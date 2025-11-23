"""
Query Tracer API endpoints.

Provides endpoints for retrieving and analyzing RAG query traces.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException

from backend.core.query_tracer import QueryTracer
from backend.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1", tags=["Query Tracer"])


@router.get("/traces/{execution_id}")
async def get_trace(execution_id: str):
    """
    Get a complete query trace by execution ID.
    
    Returns detailed trace information including all steps in the RAG pipeline.
    """
    trace = QueryTracer.get_trace(execution_id)
    if not trace:
        raise HTTPException(status_code=404, detail=f"Trace not found for execution_id: {execution_id}")
    
    return trace.to_dict()


@router.get("/traces/{execution_id}/summary")
async def get_trace_summary(execution_id: str):
    """
    Get a summary of a query trace.
    
    Returns a condensed view with key metrics and statistics.
    """
    summary = QueryTracer.get_trace_summary(execution_id)
    if not summary:
        raise HTTPException(status_code=404, detail=f"Trace not found for execution_id: {execution_id}")
    
    return summary


@router.get("/traces")
async def list_traces(workflow_id: Optional[str] = None, limit: int = 100):
    """
    List query traces.
    
    Optionally filter by workflow_id and limit the number of results.
    """
    traces = QueryTracer.list_traces(workflow_id=workflow_id, limit=limit)
    return {
        "traces": traces,
        "count": len(traces),
    }

