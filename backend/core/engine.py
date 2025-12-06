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
import traceback
from collections import defaultdict, deque
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

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
from backend.core.observability import (
    get_observability_manager,
    SpanType,
)
from backend.core.observability_adapter import get_observability_adapter
from backend.core.span_evaluator import SpanEvaluator
from backend.utils.logger import get_logger

logger = get_logger(__name__)

# Initialize span evaluator
_span_evaluator = SpanEvaluator()


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
        user_id: str | None = None,
        use_intelligent_routing: Optional[bool] = None,
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
        
        # Store user_id for node execution
        self._user_id = user_id

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
            
            # Start observability trace
            observability_manager = get_observability_manager()
            observability_adapter = get_observability_adapter(user_id=user_id)
            
            trace = observability_manager.start_trace(
                workflow_id=workflow.id or "unknown",
                execution_id=execution_id,
                query=query_text,
            )
            
            # Also start legacy QueryTracer for backward compatibility
            if query_text:
                QueryTracer.start_trace(
                    execution_id=execution_id,
                    query=query_text,
                    workflow_id=workflow.id or "unknown",
                )
            
            # Start trace in external adapters (LangSmith/LangFuse)
            observability_adapter.start_trace(
                trace_id=trace.trace_id,
                workflow_id=workflow.id or "unknown",
                execution_id=execution_id,
                query=query_text,
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
                inputs = await self._collect_node_inputs(
                    workflow,
                    node_id,
                    node_outputs,
                    use_intelligent_routing=getattr(self, '_use_intelligent_routing', None),
                )

                # Start observability span for this node
                span = None
                if trace:
                    span_type = self._map_node_type_to_span_type(node.type)
                    span = observability_manager.start_span(
                        trace_id=trace.trace_id,
                        span_type=span_type,
                        name=f"{node.type}:{node.id}",
                        inputs=self._sanitize_inputs_for_trace(inputs),
                    )
                
                # Execute node
                node_result = await self._execute_node(
                    node,
                    inputs,
                    execution,
                    execution_id,  # Pass execution_id for streaming
                    span=span,  # Pass span for enhanced tracking
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
                
                # Complete observability span
                if span:
                    self._complete_observability_span(
                        span=span,
                        node=node,
                        node_result=node_result,
                        inputs=inputs,
                    )
                
                # Add to query tracer if this is a RAG-relevant node (legacy)
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
            
            # Complete observability trace
            observability_manager.complete_trace(trace.trace_id)
            observability_adapter.complete_trace(trace.trace_id, trace)
            
            # Complete query trace (legacy)
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
            
            # Mark trace as failed
            try:
                observability_manager = get_observability_manager()
                observability_adapter = get_observability_adapter()
                trace = observability_manager.get_trace_by_execution_id(execution_id)
                if trace:
                    trace.fail(str(e))
                    observability_adapter.complete_trace(trace.trace_id, trace)
            except Exception as obs_error:
                logger.warning(f"Failed to mark trace as failed: {obs_error}")
            
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

        # Check node types are registered with helpful error messages
        missing_nodes = []
        for node in workflow.nodes:
            if not NodeRegistry.is_registered(node.type):
                missing_nodes.append(node.type)
        
        if missing_nodes:
            # Provide helpful suggestions for common missing node types
            suggestions = []
            for node_type in missing_nodes:
                if node_type in ['crewai_agent']:
                    suggestions.append(f"'{node_type}' requires CrewAI package: pip install crewai")
                elif node_type in ['knowledge_graph']:
                    suggestions.append(f"'{node_type}' requires Neo4j package: pip install neo4j")
                elif node_type in ['rerank']:
                    suggestions.append(f"'{node_type}' requires additional packages: pip install cohere sentence-transformers")
                else:
                    suggestions.append(f"'{node_type}' may require additional dependencies")
            
            error_msg = f"Node types not available: {', '.join(missing_nodes)}"
            if suggestions:
                error_msg += f". Installation hints: {' | '.join(suggestions)}"
            errors.append(error_msg)

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

    async def _collect_node_inputs(
        self,
        workflow: Workflow,
        node_id: str,
        node_outputs: Dict[str, Dict[str, Any]],
        use_intelligent_routing: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """
        Collect inputs for a node from its source nodes.
        
        Args:
            workflow: The workflow
            node_id: The target node ID
            node_outputs: Outputs from previously executed nodes
            use_intelligent_routing: Whether to use intelligent routing (None = auto-detect from settings)
            
        Returns:
            Combined inputs dictionary
        """
        # Check if intelligent routing is enabled
        if use_intelligent_routing is None:
            # Auto-detect from settings or workflow config
            from backend.config import settings
            use_intelligent_routing = getattr(settings, 'enable_intelligent_routing', False)
            # Also check workflow-level config
            workflow_config = getattr(workflow, 'config', {})
            if isinstance(workflow_config, dict):
                use_intelligent_routing = workflow_config.get('use_intelligent_routing', use_intelligent_routing)
        
        inputs: Dict[str, Any] = {}
        
        # Collect all available data from source nodes
        available_data: Dict[str, Any] = {}
        source_node_types: List[str] = []

        # Find all edges that target this node
        for edge in workflow.edges:
            if edge.target == node_id:
                source_outputs = node_outputs.get(edge.source, {})
                source_node = self._get_node_by_id(workflow, edge.source)
                
                if source_node:
                    source_node_types.append(source_node.type)

                # Merge source outputs into available_data
                for key, value in source_outputs.items():
                    # If key already exists, prefer the most recent (last edge)
                    available_data[key] = value
                
                # For text_input nodes, also map by node ID for better placeholder support
                # This allows templates to use {node_id} or {label} placeholders
                if source_node and source_node.type == "text_input":
                    # Use node ID as a key (e.g., "text_input_brand" -> inputs["text_input_brand"])
                    if "text" in source_outputs:
                        available_data[edge.source] = source_outputs["text"]
                    
                    # Also try to infer semantic keys from node label/data
                    node_label = source_node.data.get("label", "").lower() if source_node.data else ""
                    if "brand" in node_label or "product" in node_label:
                        available_data["brand_info"] = source_outputs.get("text", "")
                    elif "content" in node_label and "type" in node_label:
                        available_data["content_type"] = source_outputs.get("text", "")
                    elif "topic" in node_label:
                        available_data["topic"] = source_outputs.get("text", "")
                    elif "tone" in node_label or "style" in node_label:
                        available_data["tone"] = source_outputs.get("text", "")
                
                # Also pass through common fields that might be needed downstream
                # (e.g., query text, index_id)
                if "text" in source_outputs and "query" not in available_data:
                    available_data["query"] = source_outputs["text"]
                if "index_id" in source_outputs:
                    available_data["index_id"] = source_outputs["index_id"]
                
                # Extract text from common output formats for text-processing nodes
                # This helps nodes like advanced_nlp, chat, etc. find text from agent outputs
                if "text" not in available_data:
                    # Check for common text output fields
                    if "output" in source_outputs and isinstance(source_outputs["output"], str):
                        available_data["text"] = source_outputs["output"]
                    elif "report" in source_outputs and isinstance(source_outputs["report"], str):
                        available_data["text"] = source_outputs["report"]
                    elif "response" in source_outputs and isinstance(source_outputs["response"], str):
                        available_data["text"] = source_outputs["response"]
                    elif "content" in source_outputs and isinstance(source_outputs["content"], str):
                        available_data["text"] = source_outputs["content"]
        
        # If intelligent routing is enabled, use it to map data semantically
        if use_intelligent_routing and available_data:
            try:
                target_node = self._get_node_by_id(workflow, node_id)
                if target_node:
                    # Get node schema for intelligent routing
                    node_class = NodeRegistry.get(target_node.type)
                    node_instance = node_class()
                    node_schema = node_instance.get_schema()
                    
                    # Get workflow context for better routing decisions
                    workflow_context = f"{workflow.name}: {workflow.description or 'No description'}"
                    
                    # Use intelligent router
                    from backend.core.intelligent_router import route_data_intelligently
                    intelligent_inputs = await route_data_intelligently(
                        target_node_type=target_node.type,
                        target_node_schema=node_schema,
                        available_data=available_data,
                        source_node_types=list(set(source_node_types)),  # Unique source types
                        workflow_context=workflow_context,
                        use_intelligent=True,
                    )
                    
                    # Merge intelligent routing results with fallback
                    # Intelligent routing may not map everything, so we merge
                    inputs = {**available_data, **intelligent_inputs}
                    logger.debug(f"Used intelligent routing for node {node_id}: mapped {len(intelligent_inputs)} fields")
                    return inputs
            except Exception as e:
                logger.warning(f"Intelligent routing failed for node {node_id}, using rule-based: {e}")
                # Fall through to rule-based routing
        
        # Rule-based routing (current behavior)
        inputs = available_data.copy()
        return inputs

    async def _execute_node(
        self,
        node: Node,
        inputs: Dict[str, Any],
        execution: Execution,
        execution_id: str,
        span: Optional[Any] = None,
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
            # Add user_id for vault access
            if hasattr(self, '_user_id') and self._user_id:
                node_config["_user_id"] = self._user_id

            # Execute node
            start_time = time.time()
            try:
                output = await node_instance.execute_safe(inputs, node_config)
                duration_ms = int((time.time() - start_time) * 1000)
            except Exception as e:
                # Track error in span if available
                if span:
                    observability_manager = get_observability_manager()
                    observability_manager.fail_span(
                        span_id=span.span_id,
                        error=str(e),
                        error_type=type(e).__name__,
                        error_stack=traceback.format_exc(),
                    )
                raise
            
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

            # Extract tokens if available
            tokens = {}
            if isinstance(output, dict):
                tokens = output.get("tokens_used", {})
            
            # Update span with metadata if available
            if span:
                observability_manager = get_observability_manager()
                observability_manager.update_span_metadata(
                    span_id=span.span_id,
                    tokens=tokens,
                    cost=cost,
                    model=node.data.get("openai_model") or node.data.get("anthropic_model") or node.data.get("gemini_model"),
                    provider=node.data.get("provider"),
                    metadata={
                        "node_type": node.type,
                        "node_id": node.id,
                    },
                )
            
            return NodeResult(
                node_id=node.id,
                status=NodeStatus.COMPLETED,
                output=output,
                error=None,
                cost=cost,
                duration_ms=duration_ms,
                started_at=started_at,
                completed_at=completed_at,
                tokens_used=tokens if tokens else None,
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
            
            # Store in cost intelligence module's history (in-memory cache)
            # The _cost_history dict is defined at module level in cost_intelligence
            cost_intelligence._cost_history[execution_id] = cost_records
            
            # Also persist to database for historical tracking
            try:
                from backend.core.cost_storage import record_cost
                
                # Get user_id if available
                user_id = getattr(self, '_user_id', None)
                
                # Convert workflow_id to UUID if needed
                # Skip if workflow_id is "unknown" or not a valid UUID
                workflow_uuid = None
                if workflow_id and workflow_id != "unknown":
                    try:
                        import uuid
                        # Only try to convert if it looks like a UUID (36 chars)
                        if len(workflow_id) == 36:
                            workflow_uuid = str(uuid.UUID(workflow_id))
                        else:
                            # Not a UUID format, skip it (set to None)
                            workflow_uuid = None
                    except (ValueError, AttributeError):
                        # Invalid UUID format, set to None
                        workflow_uuid = None
                
                # Persist each cost record to database
                for cost_record in cost_records:
                    node_id = cost_record.get("node_id")
                    node_type = cost_record.get("node_type", "unknown")
                    cost_value = cost_record.get("cost", 0.0)
                    
                    if cost_value <= 0:
                        continue
                    
                    # Determine category from node_type
                    category = "other"
                    if "embed" in node_type.lower():
                        category = "embedding"
                    elif "rerank" in node_type.lower():
                        category = "rerank"
                    elif "vector" in node_type.lower() or "search" in node_type.lower():
                        category = "vector_search"
                    elif "chat" in node_type.lower() or "llm" in node_type.lower() or "agent" in node_type.lower():
                        category = "llm"
                    
                    # Extract timestamp
                    timestamp = None
                    if cost_record.get("timestamp"):
                        try:
                            timestamp = datetime.fromisoformat(cost_record["timestamp"].replace('Z', '+00:00'))
                        except (ValueError, AttributeError):
                            pass
                    
                    # Record to database
                    record_cost(
                        execution_id=execution_id,
                        workflow_id=workflow_uuid,
                        user_id=user_id,
                        node_id=node_id or "unknown",
                        node_type=node_type,
                        cost=cost_value,
                        category=category,
                        provider=cost_record.get("provider"),
                        model=cost_record.get("model"),
                        tokens_used=cost_record.get("tokens_used"),
                        duration_ms=cost_record.get("duration_ms", 0),
                        config=cost_record.get("config"),
                        metadata=cost_record.get("metadata"),
                        timestamp=timestamp,
                    )
            except Exception as db_error:
                # Don't fail execution if database persistence fails
                logger.warning(f"Failed to persist costs to database: {db_error}", exc_info=True)
            
            logger.debug(
                f"Recorded costs for execution {execution_id}: "
                f"{len(cost_records)} nodes, total cost: ${sum(r['cost'] for r in cost_records):.4f}"
            )
            
        except Exception as e:
            # Don't fail execution if cost recording fails
            logger.warning(f"Failed to record execution costs: {e}", exc_info=True)
    
    def _map_node_type_to_span_type(self, node_type: str) -> SpanType:
        """Map node type to observability span type."""
        mapping = {
            "text_input": SpanType.QUERY_INPUT,
            "chunk": SpanType.CHUNKING,
            "embed": SpanType.EMBEDDING,
            "vector_search": SpanType.VECTOR_SEARCH,
            "rerank": SpanType.RERANKING,
            "chat": SpanType.LLM,
            "langchain_agent": SpanType.AGENT_START,
            "crewai_agent": SpanType.AGENT_START,
        }
        return mapping.get(node_type, SpanType.NODE_EXECUTION)
    
    def _sanitize_inputs_for_trace(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize inputs for trace (remove large data, keep metadata)."""
        sanitized = {}
        for key, value in inputs.items():
            if isinstance(value, str) and len(value) > 1000:
                sanitized[key] = value[:1000] + "... (truncated)"
            elif isinstance(value, (list, dict)) and len(str(value)) > 1000:
                sanitized[key] = f"{type(value).__name__} (size: {len(str(value))})"
            else:
                sanitized[key] = value
        return sanitized
    
    def _complete_observability_span(
        self,
        span: Any,
        node: Node,
        node_result: NodeResult,
        inputs: Dict[str, Any],
    ):
        """Complete an observability span with all metadata."""
        try:
            observability_manager = get_observability_manager()
            observability_adapter = get_observability_adapter()
            
            # Extract outputs (sanitize if needed)
            outputs = node_result.output or {}
            sanitized_outputs = self._sanitize_inputs_for_trace(outputs)
            
            # Complete span
            observability_manager.complete_span(
                span_id=span.span_id,
                outputs=sanitized_outputs,
                tokens=node_result.tokens_used or {},
                cost=node_result.cost,
            )
            
            # Update span with additional metadata
            observability_manager.update_span_metadata(
                span_id=span.span_id,
                model=node.data.get("openai_model") or node.data.get("anthropic_model") or node.data.get("gemini_model"),
                provider=node.data.get("provider"),
                metadata={
                    "node_type": node.type,
                    "node_id": node.id,
                    "chunk_size": node.data.get("chunk_size"),
                    "chunk_overlap": node.data.get("chunk_overlap"),
                    "top_k": node.data.get("top_k"),
                    "temperature": node.data.get("temperature"),
                },
            )
            
            # Evaluate span if evaluator available
            try:
                # Get updated span for evaluation
                updated_span = observability_manager.get_span(span.span_id)
                if updated_span:
                    evaluation = _span_evaluator.evaluate_span(updated_span)
                    observability_manager.add_span_evaluation(span.span_id, evaluation)
            except Exception as e:
                logger.debug(f"Failed to evaluate span: {e}")
            
            # Log to external adapters
            updated_span = observability_manager.get_span(span.span_id)
            if updated_span:
                observability_adapter.log_span(span.trace_id, updated_span)
            
        except Exception as e:
            # Don't fail execution if observability fails
            logger.warning(f"Failed to complete observability span: {e}", exc_info=True)


# Global engine instance
engine = WorkflowEngine()

