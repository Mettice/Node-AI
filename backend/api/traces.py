"""
API endpoints for trace management and visualization.
"""

from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, Field

from backend.core.security import limiter
from backend.core.observability import get_observability_manager
from backend.core.user_context import get_user_id_from_request
from backend.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1", tags=["Traces"])


class TraceListItem(BaseModel):
    """Trace list item model."""
    trace_id: str
    workflow_id: str
    execution_id: str
    query: Optional[str] = None
    started_at: str
    completed_at: Optional[str] = None
    status: str
    total_cost: float
    total_tokens: dict
    total_duration_ms: int
    span_count: int


class TraceDetailResponse(BaseModel):
    """Detailed trace response model."""
    trace_id: str
    workflow_id: str
    execution_id: str
    query: Optional[str] = None
    started_at: str
    completed_at: Optional[str] = None
    status: str
    error: Optional[str] = None
    total_cost: float
    total_tokens: dict
    total_duration_ms: int
    spans: List[dict]
    span_count: int


@router.get("/traces", response_model=List[TraceListItem])
@limiter.limit("30/minute")
async def list_traces(
    request: Request,
    workflow_id: Optional[str] = Query(None, description="Filter by workflow ID"),
    limit: int = Query(default=100, ge=1, le=1000, description="Maximum number of traces to return"),
    status: Optional[str] = Query(None, description="Filter by status (completed, failed, running)"),
):
    """
    List traces with optional filtering.
    
    Returns a list of traces with summary information.
    """
    user_id = get_user_id_from_request(request)
    
    try:
        manager = get_observability_manager()
        traces = manager.list_traces(workflow_id=workflow_id, limit=limit)
        
        # Filter by status if provided
        if status:
            traces = [t for t in traces if t.get("status") == status]
        
        # Convert to response model
        return [
            TraceListItem(
                trace_id=t["trace_id"],
                workflow_id=t["workflow_id"],
                execution_id=t["execution_id"],
                query=t.get("query"),
                started_at=t["started_at"],
                completed_at=t.get("completed_at"),
                status=t["status"],
                total_cost=t.get("total_cost", 0.0),
                total_tokens=t.get("total_tokens", {}),
                total_duration_ms=t.get("total_duration_ms", 0),
                span_count=t.get("span_count", 0),
            )
            for t in traces
        ]
    except Exception as e:
        logger.error(f"Failed to list traces: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to list traces")


@router.get("/traces/{trace_id}", response_model=TraceDetailResponse)
@limiter.limit("30/minute")
async def get_trace(request: Request, trace_id: str):
    """
    Get detailed trace information including all spans.
    
    Returns complete trace data with span details.
    """
    user_id = get_user_id_from_request(request)
    
    try:
        manager = get_observability_manager()
        trace = manager.get_trace(trace_id)
        
        if not trace:
            raise HTTPException(status_code=404, detail="Trace not found")
        
        trace_dict = trace.to_dict()
        
        return TraceDetailResponse(
            trace_id=trace_dict["trace_id"],
            workflow_id=trace_dict["workflow_id"],
            execution_id=trace_dict["execution_id"],
            query=trace_dict.get("query"),
            started_at=trace_dict["started_at"],
            completed_at=trace_dict.get("completed_at"),
            status=trace_dict["status"],
            error=trace_dict.get("error"),
            total_cost=trace_dict.get("total_cost", 0.0),
            total_tokens=trace_dict.get("total_tokens", {}),
            total_duration_ms=trace_dict.get("total_duration_ms", 0),
            spans=trace_dict.get("spans", []),
            span_count=trace_dict.get("span_count", 0),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get trace: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get trace")


@router.get("/workflows/{workflow_id}/traces", response_model=List[TraceListItem])
@limiter.limit("30/minute")
async def get_workflow_traces(
    request: Request,
    workflow_id: str,
    limit: int = Query(default=100, ge=1, le=1000),
):
    """
    Get all traces for a specific workflow.
    
    Returns traces ordered by most recent first.
    """
    user_id = get_user_id_from_request(request)
    
    try:
        manager = get_observability_manager()
        traces = manager.list_traces(workflow_id=workflow_id, limit=limit)
        
        return [
            TraceListItem(
                trace_id=t["trace_id"],
                workflow_id=t["workflow_id"],
                execution_id=t["execution_id"],
                query=t.get("query"),
                started_at=t["started_at"],
                completed_at=t.get("completed_at"),
                status=t["status"],
                total_cost=t.get("total_cost", 0.0),
                total_tokens=t.get("total_tokens", {}),
                total_duration_ms=t.get("total_duration_ms", 0),
                span_count=t.get("span_count", 0),
            )
            for t in traces
        ]
    except Exception as e:
        logger.error(f"Failed to get workflow traces: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get workflow traces")

