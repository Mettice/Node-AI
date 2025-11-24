"""
LangSmith integration for observability.

LangSmith is LangChain's observability platform for tracing and monitoring.
"""

from typing import Any, Dict, Optional
from datetime import datetime

from backend.utils.logger import get_logger
from backend.core.observability import Span, Trace

logger = get_logger(__name__)

# Try to import LangSmith
try:
    from langsmith import Client
    from langsmith.run_helpers import tracing_context
    LANGSMITH_AVAILABLE = True
except ImportError:
    LANGSMITH_AVAILABLE = False
    logger.warning("LangSmith not available. Install with: pip install langsmith")


class LangSmithAdapter:
    """Adapter for LangSmith observability platform."""
    
    def __init__(self, api_key: str, project: str = "nodeflow"):
        if not LANGSMITH_AVAILABLE:
            raise ImportError("LangSmith is not installed. Install with: pip install langsmith")
        
        self.client = Client(api_key=api_key)
        self.project = project
        self._traces: Dict[str, Any] = {}  # Map trace_id to LangSmith run
    
    def start_trace(
        self,
        trace_id: str,
        workflow_id: str,
        execution_id: str,
        query: Optional[str] = None,
    ) -> Any:
        """Start a LangSmith trace."""
        try:
            # Create a run in LangSmith
            run = self.client.create_run(
                name=f"workflow-{workflow_id}",
                run_type="chain",
                inputs={"query": query or "", "workflow_id": workflow_id},
                project_name=self.project,
                extra={
                    "trace_id": trace_id,
                    "execution_id": execution_id,
                    "workflow_id": workflow_id,
                },
            )
            self._traces[trace_id] = run
            logger.debug(f"Started LangSmith trace: {trace_id}")
            return run
        except Exception as e:
            logger.warning(f"Failed to start LangSmith trace: {e}")
            return None
    
    def log_span(
        self,
        trace_id: str,
        span: Span,
    ):
        """Log a span to LangSmith."""
        try:
            run = self._traces.get(trace_id)
            if not run:
                logger.warning(f"LangSmith trace not found: {trace_id}")
                return
            
            # Determine run type based on span type
            run_type_map = {
                "embedding": "embedding",
                "llm": "llm",
                "vector_search": "retriever",
                "reranking": "reranker",
                "chunking": "transformer",
                "query_input": "input",
                "final_output": "output",
            }
            run_type = run_type_map.get(span.span_type.value, "tool")
            
            # Create child run
            child_run = self.client.create_run(
                name=span.name,
                run_type=run_type,
                parent_run_id=run.id,
                inputs=span.inputs,
                outputs=span.outputs if span.status.value == "completed" else None,
                error=span.error,
                start_time=span.started_at,
                end_time=span.completed_at,
                extra={
                    "span_id": span.span_id,
                    "span_type": span.span_type.value,
                    "tokens": span.tokens,
                    "cost": span.cost,
                    "model": span.model,
                    "provider": span.provider,
                    "duration_ms": span.duration_ms,
                    "api_limits": span.api_limits,
                    "retry_count": span.retry_count,
                    "evaluation": span.evaluation,
                    "metadata": span.metadata,
                },
            )
            
            logger.debug(f"Logged span to LangSmith: {span.span_id}")
        except Exception as e:
            logger.warning(f"Failed to log span to LangSmith: {e}")
    
    def complete_trace(self, trace_id: str, trace: Trace):
        """Complete a LangSmith trace."""
        try:
            run = self._traces.get(trace_id)
            if not run:
                return
            
            # Update run with final outputs
            self.client.update_run(
                run.id,
                outputs={
                    "result": trace.query,
                    "total_cost": trace.total_cost,
                    "total_tokens": trace.total_tokens,
                    "total_duration_ms": trace.total_duration_ms,
                },
                end_time=trace.completed_at,
                error=trace.error,
            )
            
            logger.debug(f"Completed LangSmith trace: {trace_id}")
        except Exception as e:
            logger.warning(f"Failed to complete LangSmith trace: {e}")

