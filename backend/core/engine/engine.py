"""
Workflow execution engine for NodeAI.

This module contains the core engine that executes workflows by:
1. Parsing workflow structure
2. Building execution graph
3. Executing nodes in correct order
4. Passing data between nodes
5. Tracking execution results and costs
"""

from datetime import datetime
from typing import Any, Dict, Optional

from backend.core.exceptions import WorkflowExecutionError
from backend.core.models import Execution, ExecutionStatus, ExecutionStep, NodeResult, NodeStatus, Workflow
from backend.core.streaming import StreamEventType, stream_manager
from backend.core.query_tracer import QueryTracer
from backend.core.observability import get_observability_manager
from backend.core.observability_adapter import get_observability_adapter
from backend.core.engine.workflow_validator import WorkflowValidator
from backend.core.engine.data_collector import DataCollector
from backend.core.engine.node_executor import NodeExecutor
from backend.core.engine.tracing import Tracing
from backend.core.engine.cost_tracker import CostTracker
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
        user_id: str | None = None,
        use_intelligent_routing: Optional[bool] = None,
    ) -> Execution:
        """
        Execute a workflow.
        
        Args:
            workflow: The workflow to execute
            execution_id: Optional execution ID (generated if not provided)
            user_id: Optional user ID for authentication
            use_intelligent_routing: Whether to use intelligent routing
            
        Returns:
            Execution object with results and trace
            
        Raises:
            WorkflowValidationError: If workflow is invalid
            WorkflowExecutionError: If execution fails
        """
        import uuid

        execution_id = execution_id or str(uuid.uuid4())
        started_at = datetime.now()
        
        # Store user_id and intelligent routing preference for node execution
        self._user_id = user_id
        self._use_intelligent_routing = use_intelligent_routing

        logger.info(f"Starting workflow execution: {execution_id}")

        try:
            # Validate workflow
            WorkflowValidator.validate_workflow(workflow)

            # Build execution graph
            execution_order = WorkflowValidator.build_execution_order(workflow)

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

            logger.info(f"Execution order: {execution_order}")
            for node_id in execution_order:
                node = WorkflowValidator.get_node_by_id(workflow, node_id)
                
                logger.info(f"Executing node: {node_id} ({node.type}) - {node.data.get('label', '')}")
                
                try:
                    # Stream node started event
                    await stream_manager.publish(StreamEvent(
                        event_type=StreamEventType.NODE_STARTED,
                        node_id=node_id,
                        execution_id=execution_id,
                        data={"node_type": node.type, "node_name": node.data.get("name", node_id)},
                    ))

                    # Collect inputs from previous nodes
                    inputs = await DataCollector.collect_node_inputs(
                        workflow,
                        node_id,
                        node_outputs,
                        use_intelligent_routing=self._use_intelligent_routing,
                    )
                    logger.info(f"Collected inputs for {node_id}: {list(inputs.keys()) if inputs else 'no inputs'}")

                    # Start observability span for this node
                    span = None
                    if trace:
                        span_type = Tracing.map_node_type_to_span_type(node.type)
                        span = observability_manager.start_span(
                            trace_id=trace.trace_id,
                            span_type=span_type,
                            name=f"{node.type}:{node.id}",
                            inputs=Tracing.sanitize_inputs_for_trace(inputs),
                        )
                    
                    # Execute node
                    node_result = await NodeExecutor.execute_node(
                        node,
                        inputs,
                        execution,
                        execution_id,
                        user_id=self._user_id,
                        span=span,
                    )
                except Exception as node_error:
                    logger.error(f"Node {node_id} ({node.type}) execution failed: {node_error}", exc_info=True)
                    # Create failed node result
                    node_result = NodeResult(
                        status=NodeStatus.FAILED,
                        output={},
                        error=str(node_error),
                        cost=0.0,
                        duration_ms=0,
                        completed_at=datetime.now(),
                    )
                    # Stream node failure event
                    await stream_manager.publish(StreamEvent(
                        event_type=StreamEventType.NODE_FAILED,
                        node_id=node_id,
                        execution_id=execution_id,
                        data={
                            "status": "failed",
                            "error": str(node_error),
                        },
                    ))

                # Store result (even if failed)
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
                    Tracing.complete_observability_span(
                        span=span,
                        node=node,
                        node_result=node_result,
                        inputs=inputs,
                    )
                
                # Add to query tracer if this is a RAG-relevant node (legacy)
                Tracing.add_to_query_trace(
                    execution_id=execution_id,
                    node=node,
                    node_result=node_result,
                    inputs=inputs,
                )
                
                # Stream node completion event with output data
                event_type = StreamEventType.NODE_COMPLETED if node_result.status == NodeStatus.COMPLETED else StreamEventType.NODE_FAILED
                
                # Include output in completion event (but sanitize large outputs)
                output_data = node_result.output
                if output_data:
                    # Don't truncate outputs for nodes that need full data (like auto_chart_generator)
                    # These nodes will have their full output available via polling/GET endpoint
                    node_type = node.node_type if hasattr(node, 'node_type') else None
                    should_preserve_full_output = node_type in ['auto_chart_generator', 'chart_generator']
                    
                    if not should_preserve_full_output:
                        # For large outputs, send a summary instead of full data
                        output_size = len(str(output_data))
                        if output_size > 10000:  # If output is larger than 10KB, send summary
                            # Create a summary of the output
                            if isinstance(output_data, dict):
                                summary = {k: f"<{type(v).__name__}>" if not isinstance(v, (str, int, float, bool, type(None))) else v 
                                         for k, v in list(output_data.items())[:5]}  # First 5 keys
                                if len(output_data) > 5:
                                    summary["_truncated"] = f"... and {len(output_data) - 5} more keys"
                                output_data = summary
                            else:
                                output_data = f"<{type(output_data).__name__} with {output_size} bytes>"
                
                await stream_manager.publish(StreamEvent(
                    event_type=event_type,
                    node_id=node_id,
                    execution_id=execution_id,
                    data={
                        "status": node_result.status.value,
                        "cost": node_result.cost,
                        "duration_ms": node_result.duration_ms,
                        "output": output_data,  # Include output in completion event
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
            
            # Clean up stream after completion
            await stream_manager.remove_stream(execution_id)

            # Record all costs for intelligence system (only if completed successfully)
            if execution.status == ExecutionStatus.COMPLETED:
                await CostTracker.record_execution_costs(
                    execution_id,
                    workflow.id or "unknown",
                    execution.results,
                    user_id=self._user_id,
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
            
            # Clean up stream on failure
            try:
                await stream_manager.remove_stream(execution_id)
            except Exception as cleanup_error:
                logger.warning(f"Failed to cleanup stream on execution failure: {cleanup_error}")
            
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


# Global engine instance
engine = WorkflowEngine()

