"""
Metrics and analytics API endpoints.

This module provides REST API endpoints for tracking and analyzing
workflow execution metrics, costs, and performance.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel

from backend.core.security import limiter
from backend.core.models import Execution, ExecutionStatus
from backend.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1", tags=["Metrics"])

# Execution history storage directory
EXECUTIONS_DIR = Path("backend/data/executions")
EXECUTIONS_DIR.mkdir(parents=True, exist_ok=True)


class ExecutionRecord(BaseModel):
    """Record of a workflow execution for metrics tracking."""
    execution_id: str
    workflow_id: str
    workflow_version: Optional[str] = None
    status: str  # "completed" or "failed"
    started_at: str
    completed_at: Optional[str]
    duration_ms: int
    total_cost: float
    cost_breakdown: Dict[str, float] = {}  # e.g., {"embedding": 0.001, "llm": 0.05}
    error: Optional[str] = None
    metadata: Dict[str, Any] = {}  # Additional metadata (relevance_score, etc.)


class MetricsResponse(BaseModel):
    """Response model for workflow metrics."""
    workflow_id: str
    time_range: str  # e.g., "24h", "7d", "30d"
    total_queries: int
    success_rate: float
    avg_response_time_ms: float
    total_cost: float
    cost_per_query: float
    cost_breakdown: Dict[str, float]
    quality_metrics: Dict[str, Any] = {}
    alerts: List[Dict[str, Any]] = []
    performance_trends: List[Dict[str, Any]] = []


class VersionComparison(BaseModel):
    """Comparison between workflow versions."""
    current_version: str
    previous_version: Optional[str]
    current_metrics: Dict[str, Any]
    previous_metrics: Optional[Dict[str, Any]]
    comparison: Dict[str, Any]


def _get_execution_path(execution_id: str) -> Path:
    """Get the file path for an execution record."""
    return EXECUTIONS_DIR / f"{execution_id}.json"


def _save_execution_record(record: ExecutionRecord) -> None:
    """Save an execution record to disk."""
    execution_path = _get_execution_path(record.execution_id)
    with open(execution_path, "w", encoding="utf-8") as f:
        json.dump(record.model_dump(), f, indent=2, ensure_ascii=False)


def _load_execution_record(execution_id: str) -> Optional[ExecutionRecord]:
    """Load an execution record from disk."""
    execution_path = _get_execution_path(execution_id)
    if not execution_path.exists():
        return None
    
    try:
        with open(execution_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return ExecutionRecord(**data)
    except Exception as e:
        logger.error(f"Error loading execution record {execution_id}: {e}")
        return None


def _list_execution_records(workflow_id: Optional[str] = None, hours: int = 24) -> List[ExecutionRecord]:
    """List execution records, optionally filtered by workflow_id and time range."""
    records = []
    cutoff_time = datetime.now() - timedelta(hours=hours)
    
    for execution_file in EXECUTIONS_DIR.glob("*.json"):
        try:
            with open(execution_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            record = ExecutionRecord(**data)
            
            # Filter by workflow_id if provided
            if workflow_id and record.workflow_id != workflow_id:
                continue
            
            # Filter by time range
            started_at = datetime.fromisoformat(record.started_at.replace("Z", "+00:00"))
            if started_at < cutoff_time:
                continue
            
            records.append(record)
        except Exception as e:
            logger.error(f"Error loading execution record from {execution_file}: {e}")
    
    return records


@router.post("/executions/{execution_id}/record")
@limiter.limit("100/minute")
async def record_execution(
    execution_id: str,
    execution: Execution,
    request: Request,
    workflow_version: Optional[str] = None,
    cost_breakdown: Optional[Dict[str, float]] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, str]:
    """
    Record an execution for metrics tracking.
    
    This endpoint is called after a workflow execution completes to store
    metrics for analytics and dashboard display.
    """
    try:
        # Calculate cost breakdown from node results if not provided
        if cost_breakdown is None:
            cost_breakdown = {}
            for node_id, node_result in execution.results.items():
                node_type = node_result.node_id.split("-")[0] if "-" in node_result.node_id else "unknown"
                # Categorize costs by node type
                if "embed" in node_type.lower():
                    cost_breakdown["embedding"] = cost_breakdown.get("embedding", 0) + node_result.cost
                elif "search" in node_type.lower() or "vector" in node_type.lower():
                    cost_breakdown["vector_search"] = cost_breakdown.get("vector_search", 0) + node_result.cost
                elif "chat" in node_type.lower() or "llm" in node_type.lower():
                    cost_breakdown["llm"] = cost_breakdown.get("llm", 0) + node_result.cost
                else:
                    cost_breakdown["other"] = cost_breakdown.get("other", 0) + node_result.cost
        
        record = ExecutionRecord(
            execution_id=execution_id,
            workflow_id=execution.workflow_id,
            workflow_version=workflow_version,
            status=execution.status.value,
            started_at=execution.started_at.isoformat(),
            completed_at=execution.completed_at.isoformat() if execution.completed_at else None,
            duration_ms=execution.duration_ms,
            total_cost=execution.total_cost,
            cost_breakdown=cost_breakdown,
            error=execution.error,
            metadata=metadata or {},
        )
        
        _save_execution_record(record)
        logger.info(f"Recorded execution {execution_id} for workflow {execution.workflow_id}")
        
        return {"message": "Execution recorded", "execution_id": execution_id}
        
    except Exception as e:
        logger.error(f"Error recording execution {execution_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Failed to record execution",
                "message": str(e),
            },
        )


@router.get("/workflows/{workflow_id}/metrics", response_model=MetricsResponse)
@limiter.limit("30/minute")
async def get_workflow_metrics(
    workflow_id: str,
    request: Request,
    hours: int = Query(24, ge=1, le=720, description="Time range in hours (1-720)"),
) -> MetricsResponse:
    """
    Get metrics for a workflow.
    
    Returns aggregated metrics including:
    - Total queries, success rate, avg response time
    - Total cost and cost per query
    - Cost breakdown by component
    - Quality metrics and alerts
    - Performance trends
    """
    try:
        records = _list_execution_records(workflow_id=workflow_id, hours=hours)
        
        if not records:
            # Return empty metrics
            return MetricsResponse(
                workflow_id=workflow_id,
                time_range=f"{hours}h",
                total_queries=0,
                success_rate=0.0,
                avg_response_time_ms=0.0,
                total_cost=0.0,
                cost_per_query=0.0,
                cost_breakdown={},
                quality_metrics={},
                alerts=[],
                performance_trends=[],
            )
        
        # Calculate metrics
        total_queries = len(records)
        successful = sum(1 for r in records if r.status == "completed")
        success_rate = (successful / total_queries * 100) if total_queries > 0 else 0.0
        
        avg_response_time_ms = sum(r.duration_ms for r in records) / total_queries if total_queries > 0 else 0.0
        
        total_cost = sum(r.total_cost for r in records)
        cost_per_query = total_cost / total_queries if total_queries > 0 else 0.0
        
        # Aggregate cost breakdown
        cost_breakdown = {}
        for record in records:
            for category, cost in record.cost_breakdown.items():
                cost_breakdown[category] = cost_breakdown.get(category, 0) + cost
        
        # Calculate quality metrics
        failed_queries = total_queries - successful
        error_counts: Dict[str, int] = {}
        for record in records:
            if record.error:
                error_type = record.error.split(":")[0] if ":" in record.error else record.error
                error_counts[error_type] = error_counts.get(error_type, 0) + 1
        
        # Calculate average relevance score if available
        relevance_scores = [
            r.metadata.get("relevance_score")
            for r in records
            if r.metadata.get("relevance_score") is not None
        ]
        avg_relevance = sum(relevance_scores) / len(relevance_scores) if relevance_scores else None
        
        quality_metrics = {
            "avg_relevance_score": avg_relevance,
            "failed_queries": failed_queries,
            "failure_rate": (failed_queries / total_queries * 100) if total_queries > 0 else 0.0,
            "error_breakdown": error_counts,
        }
        
        # Generate alerts
        alerts = []
        
        # Check for performance degradation (compare last 2 hours vs previous 2 hours)
        if len(records) >= 10:
            recent_records = [r for r in records if datetime.fromisoformat(r.started_at.replace("Z", "+00:00")) > datetime.now() - timedelta(hours=2)]
            older_records = [r for r in records if datetime.fromisoformat(r.started_at.replace("Z", "+00:00")) <= datetime.now() - timedelta(hours=2)]
            
            if recent_records and older_records:
                recent_avg = sum(r.duration_ms for r in recent_records) / len(recent_records)
                older_avg = sum(r.duration_ms for r in older_records) / len(older_records)
                
                if older_avg > 0:
                    change_pct = ((recent_avg - older_avg) / older_avg) * 100
                    if abs(change_pct) > 10:  # More than 10% change
                        alerts.append({
                            "type": "warning" if change_pct > 0 else "info",
                            "message": f"Response time {'increased' if change_pct > 0 else 'decreased'} {abs(change_pct):.1f}% in last 2 hours",
                        })
        
        # Performance trends (hourly aggregation)
        performance_trends = []
        if records:
            # Group by hour
            hourly_data: Dict[str, Dict[str, Any]] = {}
            for record in records:
                started_at = datetime.fromisoformat(record.started_at.replace("Z", "+00:00"))
                hour_key = started_at.strftime("%Y-%m-%d %H:00")
                
                if hour_key not in hourly_data:
                    hourly_data[hour_key] = {
                        "timestamp": hour_key,
                        "count": 0,
                        "total_duration": 0,
                        "total_cost": 0,
                    }
                
                hourly_data[hour_key]["count"] += 1
                hourly_data[hour_key]["total_duration"] += record.duration_ms
                hourly_data[hour_key]["total_cost"] += record.total_cost
            
            # Convert to list and calculate averages
            for hour_key, data in sorted(hourly_data.items()):
                performance_trends.append({
                    "timestamp": data["timestamp"],
                    "avg_response_time_ms": data["total_duration"] / data["count"],
                    "query_count": data["count"],
                    "total_cost": data["total_cost"],
                })
        
        return MetricsResponse(
            workflow_id=workflow_id,
            time_range=f"{hours}h",
            total_queries=total_queries,
            success_rate=success_rate,
            avg_response_time_ms=avg_response_time_ms,
            total_cost=total_cost,
            cost_per_query=cost_per_query,
            cost_breakdown=cost_breakdown,
            quality_metrics=quality_metrics,
            alerts=alerts,
            performance_trends=performance_trends,
        )
        
    except Exception as e:
        logger.error(f"Error getting metrics for workflow {workflow_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Failed to get metrics",
                "message": str(e),
            },
        )


@router.get("/workflows/{workflow_id}/versions/compare", response_model=VersionComparison)
@limiter.limit("30/minute")
async def compare_workflow_versions(
    workflow_id: str,
    request: Request,
    current_version: str = Query(..., description="Current version identifier"),
    previous_version: Optional[str] = Query(None, description="Previous version identifier"),
    hours: int = Query(24, ge=1, le=720, description="Time range in hours"),
) -> VersionComparison:
    """
    Compare metrics between workflow versions.
    """
    try:
        # Get current version metrics
        current_records = [
            r for r in _list_execution_records(workflow_id=workflow_id, hours=hours)
            if r.workflow_version == current_version
        ]
        
        current_metrics = _calculate_version_metrics(current_records) if current_records else {}
        
        # Get previous version metrics if provided
        previous_metrics = None
        if previous_version:
            previous_records = [
                r for r in _list_execution_records(workflow_id=workflow_id, hours=hours * 2)  # Look back further
                if r.workflow_version == previous_version
            ]
            previous_metrics = _calculate_version_metrics(previous_records) if previous_records else {}
        
        # Calculate comparison
        comparison = {}
        if previous_metrics:
            # Response time comparison
            if "avg_response_time_ms" in current_metrics and "avg_response_time_ms" in previous_metrics:
                current_rt = current_metrics["avg_response_time_ms"]
                previous_rt = previous_metrics["avg_response_time_ms"]
                if previous_rt > 0:
                    rt_change = ((current_rt - previous_rt) / previous_rt) * 100
                    comparison["response_time_change_pct"] = rt_change
            
            # Cost comparison
            if "cost_per_query" in current_metrics and "cost_per_query" in previous_metrics:
                current_cost = current_metrics["cost_per_query"]
                previous_cost = previous_metrics["cost_per_query"]
                if previous_cost > 0:
                    cost_change = ((current_cost - previous_cost) / previous_cost) * 100
                    comparison["cost_change_pct"] = cost_change
            
            # Success rate comparison
            if "success_rate" in current_metrics and "success_rate" in previous_metrics:
                sr_change = current_metrics["success_rate"] - previous_metrics["success_rate"]
                comparison["success_rate_change_pct"] = sr_change
        
        return VersionComparison(
            current_version=current_version,
            previous_version=previous_version,
            current_metrics=current_metrics,
            previous_metrics=previous_metrics,
            comparison=comparison,
        )
        
    except Exception as e:
        logger.error(f"Error comparing versions for workflow {workflow_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Failed to compare versions",
                "message": str(e),
            },
        )


def _calculate_version_metrics(records: List[ExecutionRecord]) -> Dict[str, Any]:
    """Calculate metrics for a set of execution records."""
    if not records:
        return {}
    
    total_queries = len(records)
    successful = sum(1 for r in records if r.status == "completed")
    success_rate = (successful / total_queries * 100) if total_queries > 0 else 0.0
    avg_response_time_ms = sum(r.duration_ms for r in records) / total_queries if total_queries > 0 else 0.0
    total_cost = sum(r.total_cost for r in records)
    cost_per_query = total_cost / total_queries if total_queries > 0 else 0.0
    
    return {
        "total_queries": total_queries,
        "success_rate": success_rate,
        "avg_response_time_ms": avg_response_time_ms,
        "total_cost": total_cost,
        "cost_per_query": cost_per_query,
    }

