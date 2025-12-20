"""
Node execution module.

This module handles:
- Executing individual nodes
- Handling node execution errors
- Extracting costs and tokens
- Adding display metadata
"""

import time
import traceback
from datetime import datetime
from typing import Any, Dict, Optional

from backend.core.models import Execution, ExecutionStep, Node, NodeResult, NodeStatus
from backend.core.node_registry import NodeRegistry
from backend.core.observability import get_observability_manager
from backend.core.streaming import StreamEventType
from backend.core.engine.tracing import Tracing
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class NodeExecutor:
    """Executes individual workflow nodes."""

    @staticmethod
    async def execute_node(
        node: Node,
        inputs: Dict[str, Any],
        execution: Execution,
        execution_id: str,
        user_id: Optional[str] = None,
        span: Optional[Any] = None,
    ) -> NodeResult:
        """
        Execute a single node.
        
        Args:
            node: The node to execute
            inputs: Input data from previous nodes
            execution: Current execution object (for trace)
            execution_id: Execution ID for streaming
            user_id: Optional user ID for vault access
            span: Optional observability span
            
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
            if user_id:
                node_config["_user_id"] = user_id

            # Publish node_started event for streaming (so UI shows node is working)
            # This ensures all nodes show progress, not just chat nodes
            if hasattr(node_instance, 'stream_event'):
                await node_instance.stream_event(
                    StreamEventType.NODE_STARTED,
                    node.id,
                    {"type": node.type, "provider": node_config.get("provider", "")},
                )

            # Execute node
            start_time = time.time()
            try:
                logger.info(f"Executing node {node.type} with inputs: {list(inputs.keys()) if inputs else 'no inputs'}")
                output = await node_instance.execute_safe(inputs, node_config)
                duration_ms = int((time.time() - start_time) * 1000)
                logger.info(f"Node {node.type} produced output with keys: {list(output.keys()) if isinstance(output, dict) else 'non-dict output'}")
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
                
                # Add standardized display metadata using formatter registry
                try:
                    from backend.core.output_formatters import get_formatter_registry
                    formatter_registry = get_formatter_registry()
                    # Create a safe copy of output without circular references for formatting
                    # IMPORTANT: Use a deep copy to avoid modifying the original output
                    import copy
                    safe_output = copy.deepcopy(output)
                    display_metadata = formatter_registry.format_for_display(node.type, safe_output)
                    
                    # Only include metadata and actions, not the full primary_content to avoid circular refs
                    output["_display_metadata"] = {
                        "display_type": display_metadata.get("display_type", "data"),
                        "metadata": display_metadata.get("metadata", {}),
                        "actions": display_metadata.get("actions", []),
                        "attachments": display_metadata.get("attachments", [])
                        # Exclude primary_content to prevent circular reference
                    }
                    logger.debug(f"Added display metadata for {node.type}: {display_metadata.get('display_type', 'unknown')}")
                except Exception as formatter_error:
                    logger.warning(f"Failed to generate display metadata for {node.type}: {formatter_error}")
                    # Add basic display metadata as fallback
                    output["_display_metadata"] = {
                        "display_type": "data",
                        "metadata": {"node_type": node.type},
                        "actions": ["copy"],
                        "attachments": []
                    }
            else:
                # No cost in output, estimate
                cost = node_instance.estimate_cost(inputs, node.data)
                # Convert to dict and add metadata
                output = {"output": output, "_node_type": node.type, "_node_config": node.data}
                
                # Add standardized display metadata using formatter registry
                try:
                    from backend.core.output_formatters import get_formatter_registry
                    formatter_registry = get_formatter_registry()
                    # Create a safe copy of output without circular references for formatting
                    safe_output = Tracing.create_safe_output_copy(output)
                    display_metadata = formatter_registry.format_for_display(node.type, safe_output)
                    
                    # Only include metadata and actions, not the full primary_content to avoid circular refs
                    output["_display_metadata"] = {
                        "display_type": display_metadata.get("display_type", "data"),
                        "metadata": display_metadata.get("metadata", {}),
                        "actions": display_metadata.get("actions", []),
                        "attachments": display_metadata.get("attachments", [])
                        # Exclude primary_content to prevent circular reference
                    }
                    logger.debug(f"Added display metadata for {node.type}: {display_metadata.get('display_type', 'unknown')}")
                except Exception as formatter_error:
                    logger.warning(f"Failed to generate display metadata for {node.type}: {formatter_error}")
                    # Add basic display metadata as fallback
                    output["_display_metadata"] = {
                        "display_type": "data",
                        "metadata": {"node_type": node.type},
                        "actions": ["copy"],
                        "attachments": []
                    }

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

