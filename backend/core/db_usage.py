"""
Database operations for usage tracking.

This module provides operations for recording and querying usage logs.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from decimal import Decimal

from backend.core.database import get_db_connection, is_database_configured
from backend.utils.logger import get_logger

logger = get_logger(__name__)


def record_usage(
    api_key_id: Optional[str],
    user_id: Optional[str],
    workflow_id: Optional[str],
    execution_id: str,
    cost: float,
    duration_ms: int,
    status: str = "completed",
) -> None:
    """
    Record a usage event.
    
    Args:
        api_key_id: Optional API key ID
        user_id: Optional user ID
        workflow_id: Optional workflow ID
        execution_id: Execution ID
        cost: Cost of the execution
        duration_ms: Duration in milliseconds
        status: Status (completed, failed, etc.)
    """
    if not is_database_configured():
        return
    
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO usage_logs (api_key_id, user_id, workflow_id, execution_id, cost, duration_ms, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    api_key_id,
                    user_id,
                    workflow_id,
                    execution_id,
                    Decimal(str(cost)),
                    duration_ms,
                    status,
                ),
            )


def get_usage_stats(
    user_id: Optional[str] = None,
    api_key_id: Optional[str] = None,
    workflow_id: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> Dict[str, Any]:
    """
    Get usage statistics.
    
    Args:
        user_id: Optional user ID filter
        api_key_id: Optional API key ID filter
        workflow_id: Optional workflow ID filter
        start_date: Optional start date filter
        end_date: Optional end date filter
        
    Returns:
        Dictionary with usage statistics
    """
    if not is_database_configured():
        return {
            "total_requests": 0,
            "total_cost": 0.0,
            "total_duration_ms": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "avg_duration_ms": 0.0,
            "avg_cost": 0.0,
        }
    
    conditions = []
    params = []
    
    if user_id:
        conditions.append("user_id = %s")
        params.append(user_id)
    
    if api_key_id:
        conditions.append("api_key_id = %s")
        params.append(api_key_id)
    
    if workflow_id:
        conditions.append("workflow_id = %s")
        params.append(workflow_id)
    
    if start_date:
        conditions.append("created_at >= %s")
        params.append(start_date)
    
    if end_date:
        conditions.append("created_at <= %s")
        params.append(end_date)
    
    where_clause = " AND ".join(conditions) if conditions else "1=1"
    
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT 
                    COUNT(*) as total_requests,
                    COALESCE(SUM(cost), 0) as total_cost,
                    COALESCE(SUM(duration_ms), 0) as total_duration_ms,
                    COUNT(*) FILTER (WHERE status = 'completed') as successful_requests,
                    COUNT(*) FILTER (WHERE status != 'completed') as failed_requests,
                    COALESCE(AVG(duration_ms), 0) as avg_duration_ms,
                    COALESCE(AVG(cost), 0) as avg_cost
                FROM usage_logs
                WHERE {where_clause}
                """,
                params,
            )
            
            row = cur.fetchone()
            
            return {
                "total_requests": row[0] or 0,
                "total_cost": float(row[1]) if row[1] else 0.0,
                "total_duration_ms": row[2] or 0,
                "successful_requests": row[3] or 0,
                "failed_requests": row[4] or 0,
                "avg_duration_ms": float(row[5]) if row[5] else 0.0,
                "avg_cost": float(row[6]) if row[6] else 0.0,
            }


def list_usage_logs(
    user_id: Optional[str] = None,
    api_key_id: Optional[str] = None,
    workflow_id: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
) -> List[Dict[str, Any]]:
    """
    List usage logs.
    
    Args:
        user_id: Optional user ID filter
        api_key_id: Optional API key ID filter
        workflow_id: Optional workflow ID filter
        limit: Maximum number of results
        offset: Offset for pagination
        
    Returns:
        List of usage log dictionaries
    """
    if not is_database_configured():
        return []
    
    conditions = []
    params = []
    
    if user_id:
        conditions.append("user_id = %s")
        params.append(user_id)
    
    if api_key_id:
        conditions.append("api_key_id = %s")
        params.append(api_key_id)
    
    if workflow_id:
        conditions.append("workflow_id = %s")
        params.append(workflow_id)
    
    where_clause = " AND ".join(conditions) if conditions else "1=1"
    
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT id, api_key_id, user_id, workflow_id, execution_id, cost, duration_ms, status, created_at
                FROM usage_logs
                WHERE {where_clause}
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
                """,
                params + [limit, offset],
            )
            
            logs = []
            for row in cur.fetchall():
                logs.append({
                    "id": str(row[0]),
                    "api_key_id": str(row[1]) if row[1] else None,
                    "user_id": str(row[2]) if row[2] else None,
                    "workflow_id": str(row[3]) if row[3] else None,
                    "execution_id": row[4],
                    "cost": float(row[5]) if row[5] else 0.0,
                    "duration_ms": row[6],
                    "status": row[7],
                    "created_at": row[8].isoformat() if row[8] else None,
                })
            
            return logs

