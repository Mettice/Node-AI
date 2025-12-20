"""
Tracing and observability module.

This module handles:
- Query tracing for RAG workflows
- Observability span management
- Input/output sanitization
"""

from typing import Any, Dict

from backend.core.models import Node, NodeResult
from backend.core.observability import (
    get_observability_manager,
    SpanType,
)
from backend.core.observability_adapter import get_observability_adapter
from backend.core.query_tracer import QueryTracer, TraceStepType
from backend.core.span_evaluator import SpanEvaluator
from backend.utils.logger import get_logger

logger = get_logger(__name__)

# Initialize span evaluator
_span_evaluator = SpanEvaluator()


class Tracing:
    """Handles tracing and observability for workflow execution."""

    @staticmethod
    def add_to_query_trace(
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

    @staticmethod
    def map_node_type_to_span_type(node_type: str) -> SpanType:
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
    
    @staticmethod
    def sanitize_inputs_for_trace(inputs: Dict[str, Any]) -> Dict[str, Any]:
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
    
    @staticmethod
    def create_safe_output_copy(output: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a safe copy of output for formatting, removing potential circular references.
        """
        import copy
        
        try:
            # Create a shallow copy and remove potentially problematic keys
            safe_output = {}
            for key, value in output.items():
                # Skip keys that might cause circular references
                if key.startswith('_') and key != '_node_type' and key != '_node_config':
                    continue
                    
                # Handle different value types safely
                if isinstance(value, (str, int, float, bool, type(None))):
                    safe_output[key] = value
                elif isinstance(value, (list, tuple)):
                    # Limit list size to prevent memory issues
                    safe_output[key] = list(value)[:100] if len(value) > 100 else list(value)
                elif isinstance(value, dict):
                    # Create a shallow copy of dicts to avoid circular references
                    safe_output[key] = {k: v for k, v in value.items() if not callable(v)}
                else:
                    # Convert other objects to string representation
                    safe_output[key] = str(value)[:1000]
                    
            return safe_output
        except Exception as e:
            logger.warning(f"Failed to create safe output copy: {e}")
            # Fallback: return a minimal safe representation
            return {
                "output": output.get("output", str(output)[:1000]) if isinstance(output, dict) else str(output)[:1000],
                "node_type": output.get("_node_type", "unknown") if isinstance(output, dict) else "unknown"
            }
    
    @staticmethod
    def complete_observability_span(
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
            sanitized_outputs = Tracing.sanitize_inputs_for_trace(outputs)
            
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

