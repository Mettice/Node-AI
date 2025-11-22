"""
Database operations for deployments.

This module provides CRUD operations for workflow deployments using the database.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from decimal import Decimal
import json

from backend.core.database import get_db_connection, is_database_configured
from backend.utils.logger import get_logger

logger = get_logger(__name__)


def create_deployment(
    workflow_id: str,
    user_id: str,
    version_number: int,
    workflow_snapshot: Dict[str, Any],
    description: Optional[str] = None,
    deployed_by: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Create a new deployment version.
    
    Args:
        workflow_id: Workflow ID
        user_id: User ID who owns the workflow
        version_number: Version number
        workflow_snapshot: Snapshot of workflow at deployment time
        description: Optional deployment description
        deployed_by: Optional user ID who deployed
        
    Returns:
        Created deployment dictionary
    """
    if not is_database_configured():
        raise RuntimeError("Database not configured")
    
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO deployments (workflow_id, user_id, version_number, workflow_snapshot, description, deployed_by)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id, workflow_id, user_id, version_number, workflow_snapshot, description, status,
                          deployed_at, deployed_by, total_queries, successful_queries, failed_queries,
                          avg_response_time_ms, total_cost
                """,
                (
                    workflow_id,
                    user_id,
                    version_number,
                    json.dumps(workflow_snapshot),
                    description,
                    deployed_by or user_id,
                ),
            )
            row = cur.fetchone()
            
            return {
                "id": str(row[0]),
                "workflow_id": str(row[1]),
                "user_id": str(row[2]),
                "version_number": row[3],
                "workflow_snapshot": row[4] if isinstance(row[4], dict) else json.loads(row[4]),
                "description": row[5],
                "status": row[6],
                "deployed_at": row[7].isoformat() if row[7] else None,
                "deployed_by": str(row[8]) if row[8] else None,
                "total_queries": row[9],
                "successful_queries": row[10],
                "failed_queries": row[11],
                "avg_response_time_ms": float(row[12]) if row[12] else 0.0,
                "total_cost": float(row[13]) if row[13] else 0.0,
            }


def get_deployment(deployment_id: str, user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Get a deployment by ID.
    
    Args:
        deployment_id: Deployment ID
        user_id: Optional user ID to verify ownership
        
    Returns:
        Deployment dictionary or None if not found
    """
    if not is_database_configured():
        return None
    
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            if user_id:
                cur.execute(
                    """
                    SELECT id, workflow_id, user_id, version_number, workflow_snapshot, description, status,
                           deployed_at, deployed_by, total_queries, successful_queries, failed_queries,
                           avg_response_time_ms, total_cost
                    FROM deployments
                    WHERE id = %s AND user_id = %s
                    """,
                    (deployment_id, user_id),
                )
            else:
                cur.execute(
                    """
                    SELECT id, workflow_id, user_id, version_number, workflow_snapshot, description, status,
                           deployed_at, deployed_by, total_queries, successful_queries, failed_queries,
                           avg_response_time_ms, total_cost
                    FROM deployments
                    WHERE id = %s
                    """,
                    (deployment_id,),
                )
            
            row = cur.fetchone()
            if not row:
                return None
            
            return {
                "id": str(row[0]),
                "workflow_id": str(row[1]),
                "user_id": str(row[2]),
                "version_number": row[3],
                "workflow_snapshot": row[4] if isinstance(row[4], dict) else json.loads(row[4]),
                "description": row[5],
                "status": row[6],
                "deployed_at": row[7].isoformat() if row[7] else None,
                "deployed_by": str(row[8]) if row[8] else None,
                "total_queries": row[9],
                "successful_queries": row[10],
                "failed_queries": row[11],
                "avg_response_time_ms": float(row[12]) if row[12] else 0.0,
                "total_cost": float(row[13]) if row[13] else 0.0,
            }


def list_deployments(
    workflow_id: Optional[str] = None,
    user_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
) -> List[Dict[str, Any]]:
    """
    List deployments.
    
    Args:
        workflow_id: Optional workflow ID filter
        user_id: Optional user ID filter
        status: Optional status filter
        limit: Maximum number of results
        offset: Offset for pagination
        
    Returns:
        List of deployment dictionaries
    """
    if not is_database_configured():
        return []
    
    conditions = []
    params = []
    
    if workflow_id:
        conditions.append("workflow_id = %s")
        params.append(workflow_id)
    
    if user_id:
        conditions.append("user_id = %s")
        params.append(user_id)
    
    if status:
        conditions.append("status = %s")
        params.append(status)
    
    where_clause = " AND ".join(conditions) if conditions else "1=1"
    
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT id, workflow_id, user_id, version_number, workflow_snapshot, description, status,
                       deployed_at, deployed_by, total_queries, successful_queries, failed_queries,
                       avg_response_time_ms, total_cost
                FROM deployments
                WHERE {where_clause}
                ORDER BY version_number DESC
                LIMIT %s OFFSET %s
                """,
                params + [limit, offset],
            )
            
            deployments = []
            for row in cur.fetchall():
                deployments.append({
                    "id": str(row[0]),
                    "workflow_id": str(row[1]),
                    "user_id": str(row[2]),
                    "version_number": row[3],
                    "workflow_snapshot": row[4] if isinstance(row[4], dict) else json.loads(row[4]),
                    "description": row[5],
                    "status": row[6],
                    "deployed_at": row[7].isoformat() if row[7] else None,
                    "deployed_by": str(row[8]) if row[8] else None,
                    "total_queries": row[9],
                    "successful_queries": row[10],
                    "failed_queries": row[11],
                    "avg_response_time_ms": float(row[12]) if row[12] else 0.0,
                    "total_cost": float(row[13]) if row[13] else 0.0,
                })
            
            return deployments


def get_latest_deployment(workflow_id: str, user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Get the latest deployment for a workflow.
    
    Args:
        workflow_id: Workflow ID
        user_id: Optional user ID to verify ownership
        
    Returns:
        Latest deployment dictionary or None if not found
    """
    if not is_database_configured():
        return None
    
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            if user_id:
                cur.execute(
                    """
                    SELECT id, workflow_id, user_id, version_number, workflow_snapshot, description, status,
                           deployed_at, deployed_by, total_queries, successful_queries, failed_queries,
                           avg_response_time_ms, total_cost
                    FROM deployments
                    WHERE workflow_id = %s AND user_id = %s
                    ORDER BY version_number DESC
                    LIMIT 1
                    """,
                    (workflow_id, user_id),
                )
            else:
                cur.execute(
                    """
                    SELECT id, workflow_id, user_id, version_number, workflow_snapshot, description, status,
                           deployed_at, deployed_by, total_queries, successful_queries, failed_queries,
                           avg_response_time_ms, total_cost
                    FROM deployments
                    WHERE workflow_id = %s
                    ORDER BY version_number DESC
                    LIMIT 1
                    """,
                    (workflow_id,),
                )
            
            row = cur.fetchone()
            if not row:
                return None
            
            return {
                "id": str(row[0]),
                "workflow_id": str(row[1]),
                "user_id": str(row[2]),
                "version_number": row[3],
                "workflow_snapshot": row[4] if isinstance(row[4], dict) else json.loads(row[4]),
                "description": row[5],
                "status": row[6],
                "deployed_at": row[7].isoformat() if row[7] else None,
                "deployed_by": str(row[8]) if row[8] else None,
                "total_queries": row[9],
                "successful_queries": row[10],
                "failed_queries": row[11],
                "avg_response_time_ms": float(row[12]) if row[12] else 0.0,
                "total_cost": float(row[13]) if row[13] else 0.0,
            }


def update_deployment_metrics(
    deployment_id: str,
    total_queries: Optional[int] = None,
    successful_queries: Optional[int] = None,
    failed_queries: Optional[int] = None,
    avg_response_time_ms: Optional[float] = None,
    total_cost: Optional[float] = None,
) -> None:
    """
    Update deployment metrics.
    
    Args:
        deployment_id: Deployment ID
        total_queries: Optional total queries count
        successful_queries: Optional successful queries count
        failed_queries: Optional failed queries count
        avg_response_time_ms: Optional average response time
        total_cost: Optional total cost
    """
    if not is_database_configured():
        return
    
    updates = []
    params = []
    
    if total_queries is not None:
        updates.append("total_queries = %s")
        params.append(total_queries)
    
    if successful_queries is not None:
        updates.append("successful_queries = %s")
        params.append(successful_queries)
    
    if failed_queries is not None:
        updates.append("failed_queries = %s")
        params.append(failed_queries)
    
    if avg_response_time_ms is not None:
        updates.append("avg_response_time_ms = %s")
        params.append(Decimal(str(avg_response_time_ms)))
    
    if total_cost is not None:
        updates.append("total_cost = %s")
        params.append(Decimal(str(total_cost)))
    
    if not updates:
        return
    
    params.append(deployment_id)
    
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                UPDATE deployments
                SET {', '.join(updates)}
                WHERE id = %s
                """,
                params,
            )


def update_deployment_status(deployment_id: str, status: str) -> None:
    """
    Update deployment status.
    
    Args:
        deployment_id: Deployment ID
        status: New status (active, inactive, rolled_back)
    """
    if not is_database_configured():
        return
    
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE deployments SET status = %s WHERE id = %s",
                (status, deployment_id),
            )

