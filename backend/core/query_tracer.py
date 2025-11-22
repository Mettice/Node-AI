"""
Query Tracer for RAG workflows.

Captures detailed execution traces for RAG queries, including:
- Query input
- Chunking details
- Embedding details
- Vector search results (chunks, scores)
- Reranking results
- LLM input/output
- Final response
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from enum import Enum

from backend.utils.logger import get_logger

logger = get_logger(__name__)


class TraceStepType(str, Enum):
    """Types of trace steps in a RAG query."""
    QUERY_INPUT = "query_input"
    CHUNKING = "chunking"
    EMBEDDING = "embedding"
    VECTOR_SEARCH = "vector_search"
    RERANKING = "reranking"
    LLM = "llm"
    FINAL_OUTPUT = "final_output"


class QueryTrace:
    """Represents a complete query trace for a RAG workflow."""
    
    def __init__(self, execution_id: str, query: str, workflow_id: str):
        self.execution_id = execution_id
        self.query = query
        self.workflow_id = workflow_id
        self.started_at = datetime.now()
        self.completed_at: Optional[datetime] = None
        self.steps: List[Dict[str, Any]] = []
        self.total_cost = 0.0
        self.total_duration_ms = 0
        
    def add_step(
        self,
        step_type: TraceStepType,
        node_id: str,
        node_type: str,
        data: Dict[str, Any],
        cost: float = 0.0,
        duration_ms: int = 0,
    ):
        """Add a step to the trace."""
        step = {
            "step_type": step_type.value,
            "node_id": node_id,
            "node_type": node_type,
            "timestamp": datetime.now().isoformat(),
            "data": data,
            "cost": cost,
            "duration_ms": duration_ms,
        }
        self.steps.append(step)
        self.total_cost += cost
        self.total_duration_ms += duration_ms
        
    def complete(self):
        """Mark trace as completed."""
        self.completed_at = datetime.now()
        if self.started_at:
            total_ms = int((self.completed_at - self.started_at).total_seconds() * 1000)
            self.total_duration_ms = total_ms
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert trace to dictionary."""
        return {
            "execution_id": self.execution_id,
            "query": self.query,
            "workflow_id": self.workflow_id,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "total_cost": self.total_cost,
            "total_duration_ms": self.total_duration_ms,
            "steps": self.steps,
        }


# In-memory storage for query traces
# In production, this should be stored in a database
_query_traces: Dict[str, QueryTrace] = {}


class QueryTracer:
    """Manages query traces for RAG workflows."""
    
    @staticmethod
    def start_trace(execution_id: str, query: str, workflow_id: str) -> QueryTrace:
        """Start a new query trace."""
        trace = QueryTrace(execution_id, query, workflow_id)
        _query_traces[execution_id] = trace
        logger.info(f"Started query trace: {execution_id} for query: {query[:50]}...")
        return trace
    
    @staticmethod
    def get_trace(execution_id: str) -> Optional[QueryTrace]:
        """Get a query trace by execution ID."""
        return _query_traces.get(execution_id)
    
    @staticmethod
    def add_step(
        execution_id: str,
        step_type: TraceStepType,
        node_id: str,
        node_type: str,
        data: Dict[str, Any],
        cost: float = 0.0,
        duration_ms: int = 0,
    ):
        """Add a step to an existing trace."""
        trace = _query_traces.get(execution_id)
        if trace:
            trace.add_step(step_type, node_id, node_type, data, cost, duration_ms)
        else:
            logger.warning(f"Trace not found for execution_id: {execution_id}")
    
    @staticmethod
    def complete_trace(execution_id: str):
        """Mark a trace as completed."""
        trace = _query_traces.get(execution_id)
        if trace:
            trace.complete()
            logger.info(f"Completed query trace: {execution_id}")
        else:
            logger.warning(f"Trace not found for execution_id: {execution_id}")
    
    @staticmethod
    def list_traces(workflow_id: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """List query traces, optionally filtered by workflow."""
        traces = list(_query_traces.values())
        
        if workflow_id:
            traces = [t for t in traces if t.workflow_id == workflow_id]
        
        # Sort by started_at (newest first)
        traces.sort(key=lambda t: t.started_at, reverse=True)
        
        # Limit results
        traces = traces[:limit]
        
        return [t.to_dict() for t in traces]
    
    @staticmethod
    def get_trace_summary(execution_id: str) -> Optional[Dict[str, Any]]:
        """Get a summary of a trace."""
        trace = _query_traces.get(execution_id)
        if not trace:
            return None
        
        # Extract key information
        vector_search_step = next((s for s in trace.steps if s["step_type"] == TraceStepType.VECTOR_SEARCH.value), None)
        rerank_step = next((s for s in trace.steps if s["step_type"] == TraceStepType.RERANKING.value), None)
        llm_step = next((s for s in trace.steps if s["step_type"] == TraceStepType.LLM.value), None)
        
        return {
            "execution_id": trace.execution_id,
            "query": trace.query,
            "workflow_id": trace.workflow_id,
            "started_at": trace.started_at.isoformat(),
            "completed_at": trace.completed_at.isoformat() if trace.completed_at else None,
            "total_cost": trace.total_cost,
            "total_duration_ms": trace.total_duration_ms,
            "chunks_retrieved": vector_search_step["data"].get("results_count", 0) if vector_search_step else 0,
            "chunks_reranked": rerank_step["data"].get("reranked_count", 0) if rerank_step else 0,
            "chunks_final": rerank_step["data"].get("final_count", 0) if rerank_step else (vector_search_step["data"].get("results_count", 0) if vector_search_step else 0),
            "llm_tokens": llm_step["data"].get("tokens_used", {}) if llm_step else {},
            "has_reranking": rerank_step is not None,
        }

