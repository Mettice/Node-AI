"""
Workflow execution engine for NodeAI.

This module contains the core engine that executes workflows by:
1. Parsing workflow structure
2. Building execution graph
3. Executing nodes in correct order
4. Passing data between nodes
5. Tracking execution results and costs
"""

import time
from collections import defaultdict, deque
from datetime import datetime
from typing import Any, Dict, List, Set

from backend.core.exceptions import (
    CircularDependencyError,
    InvalidConnectionError,
    NodeExecutionError,
    WorkflowExecutionError,
    WorkflowValidationError,
)
from backend.core.models import (
    Edge,
    Execution,
    ExecutionStatus,
    ExecutionStep,
    Node,
    NodeResult,
    NodeStatus,
    Workflow,
)
from backend.core.node_registry import NodeRegistry
from backend.core.streaming import StreamEventType, stream_manager
from backend.core.query_tracer import QueryTracer, TraceStepType
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class WorkflowEngine:
    """
    Workflow execution engine.
    
    Orchestrates the execution of workflows by:
    - Validating workflow structure
    - Building dependency graph
    - Executing nodes in topological order
    - Passing data between nodes
    - Tracking execution state and costs
    """

    def __init__(self):
        """Initialize the workflow engine."""
        self.execution_cache: Dict[str, Any] = {}

    async def execute(
        self,
        workflow: Workflow,
        execution_id: str | None = None,
    ) -> Execution:
        """
        Execute a workflow.
        
        Args:
            workflow: The workflow to execute
            execution_id: Optional execution ID (generated if not provided)
            
        Returns:
            Execution object with results and trace
            
        Raises:
            WorkflowValidationError: If workflow is invalid
            WorkflowExecutionError: If execution fails
        """
        import uuid

        execution_id = execution_id or str(uuid.uuid4())
        started_at = datetime.now()

        logger.info(f"Starting workflow execution: {execution_id}")

        try:
            # Validate workflow
            self._validate_workflow(workflow)

            # Build execution graph
            execution_order = self._build_execution_order(workflow)

            # Initialize execution
            execution = Execution(
                id=execution_id,
                workflow_id=workflow.id or "unknown",
                status=ExecutionStatus.RUNNING,
                started_at=started_at,
                total_cost=0.0,
                results={},
                trace=[],
            )
            
            # Start query trace if this looks like a RAG query
            # Check if workflow has text_input or query input
            query_text = None
            for node in workflow.nodes:
                if node.type == "text_input":
                    query_text = node.data.get("text", "")
                    break
                elif node.type == "chat" and "query" in (node.data or {}):
                    query_text = node.data.get("query", "")
                    break
            
            # If we found a query, start tracing
            if query_text:
                QueryTracer.start_trace(
                    execution_id=execution_id,
                    query=query_text,
                    workflow_id=workflow.id or "unknown",
                )
            
            # Create stream for this execution
            await stream_manager.create_stream(execution_id)
            
            # Stream workflow start event
            from backend.core.streaming import StreamEvent
            await stream_manager.publish(StreamEvent(
                event_type=StreamEventType.LOG,
                node_id="workflow",
                execution_id=execution_id,
                data={"message": f"Workflow execution started: {execution_id}"},
            ))

            # Execute nodes in order
            node_outputs: Dict[str, Dict[str, Any]] = {}

            for node_id in execution_order:
                node = self._get_node_by_id(workflow, node_id)
                
                logger.info(f"Executing node: {node_id} ({node.type})")
                
                # Stream node started event
                await stream_manager.publish(StreamEvent(
                    event_type=StreamEventType.NODE_STARTED,
                    node_id=node_id,
                    execution_id=execution_id,
                    data={"node_type": node.type, "node_name": node.data.get("name", node_id)},
                ))

                # Collect inputs from previous nodes
                inputs = self._collect_node_inputs(
                    workflow,
                    node_id,
                    node_outputs,
                )

                # Execute node
                node_result = await self._execute_node(
                    node,
                    inputs,
                    execution,
                    execution_id,  # Pass execution_id for streaming
                )

                # Store result
                node_outputs[node_id] = node_result.output or {}
                execution.results[node_id] = node_result

                # Update total cost
                execution.total_cost += node_result.cost

                # Add to trace
                execution.trace.append(
                    ExecutionStep(
                        node_id=node_id,
                        timestamp=node_result.completed_at or datetime.now(),
                        action="completed",
                        data={"status": node_result.status.value},
                    )
                )
                
                # Add to query tracer if this is a RAG-relevant node
                self._add_to_query_trace(
                    execution_id=execution_id,
                    node=node,
                    node_result=node_result,
                    inputs=inputs,
                )
                
                # Stream node completion event
                event_type = StreamEventType.NODE_COMPLETED if node_result.status == NodeStatus.COMPLETED else StreamEventType.NODE_FAILED
                await stream_manager.publish(StreamEvent(
                    event_type=event_type,
                    node_id=node_id,
                    execution_id=execution_id,
                    data={
                        "status": node_result.status.value,
                        "cost": node_result.cost,
                        "duration_ms": node_result.duration_ms,
                    },
                ))

            # Mark as completed
            execution.status = ExecutionStatus.COMPLETED
            execution.completed_at = datetime.now()
            
            # Complete query trace
            QueryTracer.complete_trace(execution_id)
            
            # Stream workflow completion
            await stream_manager.publish(StreamEvent(
                event_type=StreamEventType.LOG,
                node_id="workflow",
                execution_id=execution_id,
                data={"message": f"Workflow execution completed: {execution_id}"},
            ))

            # Record all costs for intelligence system (only if completed successfully)
            if execution.status == ExecutionStatus.COMPLETED:
                await self._record_execution_costs(
                    execution_id,
                    workflow.id or "unknown",
                    execution.results,
                )
            
            logger.info(
                f"Workflow execution completed: {execution_id} "
                f"(cost: ${execution.total_cost:.4f}, duration: {execution.duration_ms}ms)"
            )

            return execution

        except Exception as e:
            logger.error(f"Workflow execution failed: {e}", exc_info=True)
            
            # Create failed execution
            execution = Execution(
                id=execution_id,
                workflow_id=workflow.id or "unknown",
                status=ExecutionStatus.FAILED,
                started_at=started_at,
                completed_at=datetime.now(),
                total_cost=0.0,
                results={},
                trace=[],
                error=str(e),
            )
            
            raise WorkflowExecutionError(
                f"Workflow execution failed: {str(e)}",
                workflow_id=workflow.id,
            ) from e

    def _validate_workflow(self, workflow: Workflow) -> None:
        """
        Validate workflow structure.
        
        Raises:
            WorkflowValidationError: If workflow is invalid
        """
        errors = []

        # Check nodes exist
        if not workflow.nodes:
            errors.append("Workflow must have at least one node")

        # Check node types are registered
        for node in workflow.nodes:
            if not NodeRegistry.is_registered(node.type):
                errors.append(f"Node type '{node.type}' is not registered")

        # Check edges reference valid nodes
        node_ids = {node.id for node in workflow.nodes}
        for edge in workflow.edges:
            if edge.source not in node_ids:
                errors.append(f"Edge source node '{edge.source}' not found")
            if edge.target not in node_ids:
                errors.append(f"Edge target node '{edge.target}' not found")

        # Check for circular dependencies
        if self._has_circular_dependency(workflow):
            cycle = self._find_cycle(workflow)
            raise CircularDependencyError(cycle)

        if errors:
            raise WorkflowValidationError(
                "Workflow validation failed",
                errors=errors,
            )

    def _build_execution_order(self, workflow: Workflow) -> List[str]:
        """
        Build execution order using topological sort.
        
        Returns:
            List of node IDs in execution order
        """
        # Build dependency graph
        graph: Dict[str, List[str]] = defaultdict(list)
        in_degree: Dict[str, int] = defaultdict(int)

        # Initialize all nodes
        for node in workflow.nodes:
            in_degree[node.id] = 0

        # Build graph from edges
        for edge in workflow.edges:
            graph[edge.source].append(edge.target)
            in_degree[edge.target] += 1

        # Topological sort using Kahn's algorithm
        queue = deque([node_id for node_id, degree in in_degree.items() if degree == 0])
        execution_order = []

        while queue:
            node_id = queue.popleft()
            execution_order.append(node_id)

            for neighbor in graph[node_id]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        # Check if all nodes were processed
        if len(execution_order) != len(workflow.nodes):
            # There's a cycle (should have been caught in validation, but double-check)
            raise CircularDependencyError(
                self._find_cycle(workflow) or ["unknown cycle"]
            )

        return execution_order

    def _has_circular_dependency(self, workflow: Workflow) -> bool:
        """Check for circular dependencies using DFS."""
        graph: Dict[str, List[str]] = defaultdict(list)
        for edge in workflow.edges:
            graph[edge.source].append(edge.target)

        visited: Set[str] = set()
        rec_stack: Set[str] = set()

        def has_cycle(node_id: str) -> bool:
            visited.add(node_id)
            rec_stack.add(node_id)

            for neighbor in graph[node_id]:
                if neighbor not in visited:
                    if has_cycle(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True

            rec_stack.remove(node_id)
            return False

        for node in workflow.nodes:
            if node.id not in visited:
                if has_cycle(node.id):
                    return True

        return False

    def _find_cycle(self, workflow: Workflow) -> List[str]:
        """Find a cycle in the workflow graph."""
        graph: Dict[str, List[str]] = defaultdict(list)
        for edge in workflow.edges:
            graph[edge.source].append(edge.target)

        visited: Set[str] = set()
        rec_stack: Set[str] = set()
        path: List[str] = []

        def find_cycle_dfs(node_id: str) -> List[str] | None:
            visited.add(node_id)
            rec_stack.add(node_id)
            path.append(node_id)

            for neighbor in graph[node_id]:
                if neighbor not in visited:
                    result = find_cycle_dfs(neighbor)
                    if result:
                        return result
                elif neighbor in rec_stack:
                    # Found cycle
                    cycle_start = path.index(neighbor)
                    return path[cycle_start:] + [neighbor]

            path.pop()
            rec_stack.remove(node_id)
            return None

        for node in workflow.nodes:
            if node.id not in visited:
                cycle = find_cycle_dfs(node.id)
                if cycle:
                    return cycle

        return []

    def _get_node_by_id(self, workflow: Workflow, node_id: str) -> Node:
        """Get node by ID."""
        for node in workflow.nodes:
            if node.id == node_id:
                return node
        raise ValueError(f"Node {node_id} not found in workflow")

    def _collect_node_inputs(
        self,
        workflow: Workflow,
        node_id: str,
        node_outputs: Dict[str, Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Collect inputs for a node from its source nodes.
        
        Args:
            workflow: The workflow
            node_id: The target node ID
            node_outputs: Outputs from previously executed nodes
            
        Returns:
            Combined inputs dictionary
        """
        inputs: Dict[str, Any] = {}

        # Find all edges that target this node
        for edge in workflow.edges:
            if edge.target == node_id:
                source_outputs = node_outputs.get(edge.source, {})

                # Merge source outputs into inputs
                # For now, we merge all outputs (can be refined later with handles)
                for key, value in source_outputs.items():
                    # If key already exists, prefer the most recent (last edge)
                    inputs[key] = value
                
                # Also pass through common fields that might be needed downstream
                # (e.g., query text, index_id)
                if "text" in source_outputs and "query" not in inputs:
                    inputs["query"] = source_outputs["text"]
                if "index_id" in source_outputs:
                    inputs["index_id"] = source_outputs["index_id"]

        return inputs

    async def _execute_node(
        self,
        node: Node,
        inputs: Dict[str, Any],
        execution: Execution,
        execution_id: str,
    ) -> NodeResult:
        """
        Execute a single node.
        
        Args:
            node: The node to execute
            inputs: Input data from previous nodes
            execution: Current execution object (for trace)
            
        Returns:
            NodeResult with output, cost, duration, etc.
        """
        started_at = datetime.now()

        # Add start step to trace
        execution.trace.append(
            ExecutionStep(
                node_id=node.id,
                timestamp=started_at,
                action="started",
                data={"type": node.type},
            )
        )

        try:
            # Get node class from registry
            node_class = NodeRegistry.get(node.type)

            # Create node instance
            node_instance = node_class()
            
            # Set execution_id for streaming (if node supports it)
            if hasattr(node_instance, 'execution_id'):
                node_instance.execution_id = execution_id
            
            # Add node_id to config for streaming (nodes may need it)
            node_config = node.data.copy() if node.data else {}
            node_config["_node_id"] = node.id
            node_config["_execution_id"] = execution_id

            # Execute node
            start_time = time.time()
            output = await node_instance.execute_safe(inputs, node_config)
            duration_ms = int((time.time() - start_time) * 1000)
            
            # Stream progress update during execution (if node supports it)
            if hasattr(node_instance, 'stream_progress'):
                await node_instance.stream_progress(node.id, 1.0, "Node execution completed")

            # Extract cost from output if available, otherwise estimate
            cost = 0.0
            if isinstance(output, dict):
                # Cost might be in the output (e.g., from CrewAI node)
                cost = output.get("cost", 0.0)
                if cost == 0.0:
                    # Fallback to estimation if not in output
                    cost = node_instance.estimate_cost(inputs, node.data)
                # Add node metadata for cost tracking
                output["_node_type"] = node.type
                output["_node_config"] = node.data
            else:
                # No cost in output, estimate
                cost = node_instance.estimate_cost(inputs, node.data)
                # Convert to dict and add metadata
                output = {"output": output, "_node_type": node.type, "_node_config": node.data}

            completed_at = datetime.now()

            return NodeResult(
                node_id=node.id,
                status=NodeStatus.COMPLETED,
                output=output,
                error=None,
                cost=cost,
                duration_ms=duration_ms,
                started_at=started_at,
                completed_at=completed_at,
            )

        except Exception as e:
            completed_at = datetime.now()
            duration_ms = int((completed_at - started_at).total_seconds() * 1000)

            logger.error(f"Node {node.id} execution failed: {e}", exc_info=True)

            # Add error step to trace
            execution.trace.append(
                ExecutionStep(
                    node_id=node.id,
                    timestamp=completed_at,
                    action="error",
                    data={"error": str(e)},
                )
            )

            return NodeResult(
                node_id=node.id,
                status=NodeStatus.FAILED,
                output=None,
                error=str(e),
                cost=0.0,
                duration_ms=duration_ms,
                started_at=started_at,
                completed_at=completed_at,
            )

    def _add_to_query_trace(
        self,
        execution_id: str,
        node: Node,
        node_result: NodeResult,
        inputs: Dict[str, Any],
    ) -> None:
        """Add node execution to query trace if it's RAG-relevant."""
        try:
            output = node_result.output or {}
            step_type = None
            trace_data = {}
            
            # Determine step type and extract trace data based on node type
            if node.type == "text_input":
                step_type = TraceStepType.QUERY_INPUT
                trace_data = {
                    "query": node.data.get("text", ""),
                }
            elif node.type == "chunk":
                step_type = TraceStepType.CHUNKING
                trace_data = {
                    "chunks_created": len(output.get("chunks", [])),
                    "chunk_size": node.data.get("chunk_size", 0),
                    "chunk_overlap": node.data.get("chunk_overlap", 0),
                }
            elif node.type == "embed":
                step_type = TraceStepType.EMBEDDING
                trace_data = {
                    "embeddings_created": len(output.get("embeddings", [])),
                    "model": node.data.get("model", ""),
                    "provider": node.data.get("provider", ""),
                }
            elif node.type == "vector_search":
                step_type = TraceStepType.VECTOR_SEARCH
                results = output.get("results", [])
                trace_data = {
                    "results_count": len(results),
                    "query": output.get("query", ""),
                    "provider": output.get("provider", ""),
                    "top_k": output.get("top_k", 0),
                    "results": [
                        {
                            "text": r.get("text", "")[:200],  # Truncate for storage
                            "score": r.get("score", 0.0),
                            "metadata": r.get("metadata", {}),
                        }
                        for r in results[:10]  # Limit to top 10 for trace
                    ],
                }
            elif node.type == "rerank":
                step_type = TraceStepType.RERANKING
                results = output.get("results", [])
                trace_data = {
                    "reranked_count": output.get("reranked_count", 0),
                    "filtered_count": output.get("filtered_count", 0),
                    "final_count": output.get("top_n", 0),
                    "method": output.get("method", ""),
                    "query": output.get("query", ""),
                    "results": [
                        {
                            "text": r.get("text", "")[:200],  # Truncate
                            "rerank_score": r.get("rerank_score", 0.0),
                            "original_score": r.get("score", 0.0),
                        }
                        for r in results[:10]  # Limit to top 10
                    ],
                }
            elif node.type == "chat":
                step_type = TraceStepType.LLM
                trace_data = {
                    "provider": node.data.get("provider", ""),
                    "model": (
                        node.data.get("openai_model") or
                        node.data.get("anthropic_model") or
                        node.data.get("gemini_model") or
                        ""
                    ),
                    "response": output.get("text", "")[:500],  # Truncate response
                    "tokens_used": output.get("tokens_used", {}),
                    "temperature": node.data.get("temperature", 0.7),
                }
            
            # Add step to trace if we identified it as RAG-relevant
            if step_type:
                QueryTracer.add_step(
                    execution_id=execution_id,
                    step_type=step_type,
                    node_id=node.id,
                    node_type=node.type,
                    data=trace_data,
                    cost=node_result.cost,
                    duration_ms=node_result.duration_ms,
                )
        except Exception as e:
            # Don't fail execution if trace capture fails
            logger.warning(f"Failed to add node to query trace: {e}", exc_info=True)
    
    async def _record_execution_costs(
        self,
        execution_id: str,
        workflow_id: str,
        results: Dict[str, NodeResult],
    ) -> None:
        """
        Record execution costs for the cost intelligence system.
        
        This method extracts cost information from node results and stores it
        in a format that can be analyzed by the cost intelligence API.
        
        Args:
            execution_id: The execution ID
            workflow_id: The workflow ID
            results: Dictionary of node results keyed by node ID
        """
        try:
            # Import here to avoid circular dependencies
            from backend.api import cost_intelligence
            
            # Build cost records for each node
            cost_records = []
            
            for node_id, node_result in results.items():
                # Skip nodes with no cost
                if node_result.cost <= 0.0:
                    continue
                
                # Extract node metadata from output if available
                output = node_result.output or {}
                node_type = output.get("_node_type", "unknown")
                node_config = output.get("_node_config", {})
                
                # Extract provider and model from config
                provider = node_config.get("provider")
                model = (
                    node_config.get("openai_model") or 
                    node_config.get("anthropic_model") or 
                    node_config.get("model") or
                    node_config.get("base_model")
                )
                
                # If provider is not directly in config, try to infer from model name
                if not provider and model:
                    model_str = str(model).lower()
                    if "gpt" in model_str or "o1" in model_str or "text-embedding" in model_str:
                        provider = "openai"
                    elif "claude" in model_str:
                        provider = "anthropic"
                    elif "cohere" in model_str:
                        provider = "cohere"
                
                # Build cost record
                cost_record = {
                    "node_id": node_id,
                    "node_type": node_type,
                    "cost": node_result.cost,
                    "tokens_used": node_result.tokens_used,
                    "model": model,
                    "provider": provider,
                    "config": node_config,
                    "duration_ms": node_result.duration_ms,
                    "timestamp": node_result.completed_at.isoformat() if node_result.completed_at else None,
                }
                
                cost_records.append(cost_record)
            
            # Store in cost intelligence module's history
            # This is in-memory storage - in production, this would be a database
            # The _cost_history dict is defined at module level in cost_intelligence
            cost_intelligence._cost_history[execution_id] = cost_records
            
            logger.debug(
                f"Recorded costs for execution {execution_id}: "
                f"{len(cost_records)} nodes, total cost: ${sum(r['cost'] for r in cost_records):.4f}"
            )
            
        except Exception as e:
            # Don't fail execution if cost recording fails
            logger.warning(f"Failed to record execution costs: {e}", exc_info=True)


# Global engine instance
engine = WorkflowEngine()

