"""
LangFuse integration for observability.

LangFuse is an open-source observability platform for LLM applications.
"""

from typing import Any, Dict, Optional
from datetime import datetime

from backend.utils.logger import get_logger
from backend.core.observability import Span, Trace

logger = get_logger(__name__)

# Try to import LangFuse
try:
    from langfuse import Langfuse
    from langfuse.decorators import observe
    LANGFUSE_AVAILABLE = True
except ImportError:
    LANGFUSE_AVAILABLE = False
    logger.warning("LangFuse not available. Install with: pip install langfuse")


class LangFuseAdapter:
    """Adapter for LangFuse observability platform."""
    
    def __init__(
        self,
        public_key: str,
        secret_key: str,
        host: str = "https://cloud.langfuse.com",
    ):
        if not LANGFUSE_AVAILABLE:
            raise ImportError("LangFuse is not installed. Install with: pip install langfuse")
        
        self.langfuse = Langfuse(
            public_key=public_key,
            secret_key=secret_key,
            host=host,
        )
        self._traces: Dict[str, Any] = {}  # Map trace_id to LangFuse trace
    
    def start_trace(
        self,
        trace_id: str,
        workflow_id: str,
        execution_id: str,
        query: Optional[str] = None,
    ) -> Any:
        """Start a LangFuse trace."""
        try:
            trace = self.langfuse.trace(
                name=f"workflow-{workflow_id}",
                id=trace_id,
                input=query or "",
                metadata={
                    "workflow_id": workflow_id,
                    "execution_id": execution_id,
                    "trace_id": trace_id,
                },
            )
            self._traces[trace_id] = trace
            logger.debug(f"Started LangFuse trace: {trace_id}")
            return trace
        except Exception as e:
            logger.warning(f"Failed to start LangFuse trace: {e}")
            return None
    
    def log_span(
        self,
        trace_id: str,
        span: Span,
    ):
        """Log a span to LangFuse."""
        try:
            trace = self._traces.get(trace_id)
            if not trace:
                logger.warning(f"LangFuse trace not found: {trace_id}")
                return
            
            # Determine observation type based on span type
            observation_type_map = {
                "embedding": "GENERATION",
                "llm": "GENERATION",
                "vector_search": "SPAN",
                "reranking": "SPAN",
                "chunking": "SPAN",
                "query_input": "SPAN",
                "final_output": "SPAN",
            }
            observation_type = observation_type_map.get(span.span_type.value, "SPAN")
            
            # Create span/observation
            if observation_type == "GENERATION":
                observation = trace.generation(
                    name=span.name,
                    id=span.span_id,
                    model=span.model or "unknown",
                    model_parameters={
                        "provider": span.provider,
                        "temperature": span.metadata.get("temperature"),
                    },
                    input=span.inputs,
                    output=span.outputs if span.status.value == "completed" else None,
                    usage={
                        "input": span.tokens.get("input_tokens", 0),
                        "output": span.tokens.get("output_tokens", 0),
                        "total": span.tokens.get("total_tokens", 0),
                    },
                    metadata={
                        "span_type": span.span_type.value,
                        "cost": span.cost,
                        "duration_ms": span.duration_ms,
                        "api_limits": span.api_limits,
                        "retry_count": span.retry_count,
                        "evaluation": span.evaluation,
                    },
                    start_time=span.started_at,
                    end_time=span.completed_at,
                    level="ERROR" if span.status.value == "failed" else "DEFAULT",
                )
            else:
                observation = trace.span(
                    name=span.name,
                    id=span.span_id,
                    input=span.inputs,
                    output=span.outputs if span.status.value == "completed" else None,
                    metadata={
                        "span_type": span.span_type.value,
                        "tokens": span.tokens,
                        "cost": span.cost,
                        "model": span.model,
                        "provider": span.provider,
                        "duration_ms": span.duration_ms,
                        "api_limits": span.api_limits,
                        "retry_count": span.retry_count,
                        "evaluation": span.evaluation,
                    },
                    start_time=span.started_at,
                    end_time=span.completed_at,
                    level="ERROR" if span.status.value == "failed" else "DEFAULT",
                )
            
            logger.debug(f"Logged span to LangFuse: {span.span_id}")
        except Exception as e:
            logger.warning(f"Failed to log span to LangFuse: {e}")
    
    def complete_trace(self, trace_id: str, trace: Trace):
        """Complete a LangFuse trace."""
        try:
            langfuse_trace = self._traces.get(trace_id)
            if not langfuse_trace:
                return
            
            # Update trace with final outputs
            langfuse_trace.update(
                output={
                    "result": trace.query,
                    "total_cost": trace.total_cost,
                    "total_tokens": trace.total_tokens,
                    "total_duration_ms": trace.total_duration_ms,
                },
                metadata={
                    "status": trace.status,
                    "error": trace.error,
                },
            )
            
            logger.debug(f"Completed LangFuse trace: {trace_id}")
        except Exception as e:
            logger.warning(f"Failed to complete LangFuse trace: {e}")

