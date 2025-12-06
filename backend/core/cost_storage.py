"""
Persistent cost storage for historical cost tracking.

This module provides functions for storing and retrieving cost data from the database,
enabling historical cost analysis (daily, weekly, monthly stats).
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from decimal import Decimal

from backend.core.database import get_db_connection, is_database_configured
from backend.utils.logger import get_logger

logger = get_logger(__name__)


def record_cost(
    execution_id: str,
    workflow_id: Optional[str],
    user_id: Optional[str],
    node_id: str,
    node_type: str,
    cost: float,
    category: str,  # 'llm', 'embedding', 'rerank', 'vector_search', 'other'
    provider: Optional[str] = None,
    model: Optional[str] = None,
    tokens_used: Optional[Dict[str, int]] = None,
    duration_ms: int = 0,
    config: Optional[Dict[str, Any]] = None,
    metadata: Optional[Dict[str, Any]] = None,
    timestamp: Optional[datetime] = None,
) -> None:
    """
    Record a cost entry in the database.
    
    Args:
        execution_id: Execution ID
        workflow_id: Workflow ID (UUID)
        user_id: User ID (UUID)
        node_id: Node ID
        node_type: Node type (e.g., 'chat', 'embed', 'rerank')
        cost: Cost in USD
        category: Cost category ('llm', 'embedding', 'rerank', 'vector_search', 'other')
        provider: Provider name (e.g., 'openai', 'anthropic')
        model: Model name (e.g., 'gpt-4o-mini', 'claude-sonnet-4')
        tokens_used: Token usage dictionary {input: int, output: int, total: int}
        duration_ms: Duration in milliseconds
        config: Node configuration
        metadata: Additional metadata
        timestamp: Timestamp (defaults to now)
    """
    if not is_database_configured():
        logger.debug("Database not configured, skipping cost record persistence")
        return
    
    if cost <= 0:
        return  # Don't store zero-cost records
    
    import json
    
    timestamp = timestamp or datetime.now()
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO cost_records (
                        execution_id, workflow_id, user_id, node_id, node_type,
                        cost, tokens_used, duration_ms, provider, model, category,
                        config, metadata, created_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        execution_id,
                        workflow_id,
                        user_id,
                        node_id,
                        node_type,
                        Decimal(str(cost)),
                        json.dumps(tokens_used) if tokens_used else '{}',
                        duration_ms,
                        provider,
                        model,
                        category,
                        json.dumps(config) if config else '{}',
                        json.dumps(metadata) if metadata else '{}',
                        timestamp,
                    ),
                )
            # Explicit commit to ensure data is persisted immediately
            conn.commit()
        logger.info(f"✅ Recorded cost: ${cost:.6f} for node {node_id} in execution {execution_id} (workflow_id: {workflow_id}, user_id: {user_id})")
    except Exception as e:
        logger.error(f"Failed to record cost to database: {e}", exc_info=True)


def get_cost_stats(
    user_id: Optional[str] = None,
    workflow_id: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    period: str = "daily",  # 'daily', 'weekly', 'monthly'
) -> Dict[str, Any]:
    """
    Get cost statistics for a time period.
    
    Args:
        user_id: Optional user ID filter
        workflow_id: Optional workflow ID filter
        start_date: Start date (defaults to 30 days ago)
        end_date: End date (defaults to now)
        period: Aggregation period ('daily', 'weekly', 'monthly')
        
    Returns:
        Dictionary with cost statistics and breakdowns
    """
    if not is_database_configured():
        return {
            "total_cost": 0.0,
            "total_executions": 0,
            "total_records": 0,
            "period": period,
            "start_date": start_date.isoformat() if start_date else datetime.now().isoformat(),
            "end_date": end_date.isoformat() if end_date else datetime.now().isoformat(),
            "breakdown_by_category": {},
            "breakdown_by_provider": {},
            "breakdown_by_model": {},
            "period_data": [],
        }
    
    end_date = end_date or datetime.now()
    start_date = start_date or (end_date - timedelta(days=30))
    
    conditions = []
    params = []
    
    if user_id:
        conditions.append("user_id = %s")
        params.append(user_id)
    
    # Note: If workflow_id is provided, we only match that workflow_id
    # Template executions (workflow_id = NULL) won't be included unless workflow_id is None
    # This is intentional - saved workflows have IDs, templates don't
    if workflow_id:
        conditions.append("workflow_id = %s")
        params.append(workflow_id)
    
    conditions.append("created_at >= %s")
    params.append(start_date)
    
    conditions.append("created_at <= %s")
    params.append(end_date)
    
    where_clause = " AND ".join(conditions)
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Get total stats
                cur.execute(
                    f"""
                    SELECT 
                        COALESCE(SUM(cost), 0) as total_cost,
                        COUNT(DISTINCT execution_id) as total_executions,
                        COUNT(*) as total_records
                    FROM cost_records
                    WHERE {where_clause}
                    """,
                    params,
                )
                total_row = cur.fetchone()
                total_cost = float(total_row[0]) if total_row[0] else 0.0
                total_executions = total_row[1] or 0
                total_records = total_row[2] or 0
                
                # Get breakdown by category
                cur.execute(
                    f"""
                    SELECT 
                        category,
                        SUM(cost) as total_cost,
                        COUNT(*) as count
                    FROM cost_records
                    WHERE {where_clause}
                    GROUP BY category
                    ORDER BY total_cost DESC
                    """,
                    params,
                )
                breakdown_by_category = {
                    row[0]: {"cost": float(row[1]), "count": row[2]}
                    for row in cur.fetchall()
                }
                
                # Get breakdown by provider
                cur.execute(
                    f"""
                    SELECT 
                        provider,
                        SUM(cost) as total_cost,
                        COUNT(*) as count
                    FROM cost_records
                    WHERE {where_clause} AND provider IS NOT NULL
                    GROUP BY provider
                    ORDER BY total_cost DESC
                    """,
                    params,
                )
                breakdown_by_provider = {
                    row[0]: {"cost": float(row[1]), "count": row[2]}
                    for row in cur.fetchall()
                }
                
                # Get breakdown by model
                cur.execute(
                    f"""
                    SELECT 
                        model,
                        SUM(cost) as total_cost,
                        COUNT(*) as count
                    FROM cost_records
                    WHERE {where_clause} AND model IS NOT NULL
                    GROUP BY model
                    ORDER BY total_cost DESC
                    LIMIT 20
                    """,
                    params,
                )
                breakdown_by_model = {
                    row[0]: {"cost": float(row[1]), "count": row[2]}
                    for row in cur.fetchall()
                }
                
                # Get daily/weekly/monthly data
                if period == "daily":
                    date_trunc = "DATE_TRUNC('day', created_at)"
                elif period == "weekly":
                    date_trunc = "DATE_TRUNC('week', created_at)"
                else:  # monthly
                    date_trunc = "DATE_TRUNC('month', created_at)"
                
                cur.execute(
                    f"""
                    SELECT 
                        {date_trunc} as period,
                        SUM(cost) as total_cost,
                        COUNT(DISTINCT execution_id) as executions,
                        COUNT(*) as records
                    FROM cost_records
                    WHERE {where_clause}
                    GROUP BY period
                    ORDER BY period ASC
                    """,
                    params,
                )
                period_data = [
                    {
                        "period": row[0].isoformat() if isinstance(row[0], datetime) else str(row[0]),
                        "total_cost": float(row[1]),
                        "executions": row[2],
                        "records": row[3],
                    }
                    for row in cur.fetchall()
                ]
                
                return {
                    "total_cost": total_cost,
                    "total_executions": total_executions,
                    "total_records": total_records,
                    "period": period,
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "breakdown_by_category": breakdown_by_category,
                    "breakdown_by_provider": breakdown_by_provider,
                    "breakdown_by_model": breakdown_by_model,
                    "period_data": period_data,
                }
    except Exception as e:
        logger.error(f"Failed to get cost stats: {e}", exc_info=True)
        return {
            "total_cost": 0.0,
            "total_executions": 0,
            "total_records": 0,
            "period": period,
            "start_date": start_date.isoformat() if start_date else datetime.now().isoformat(),
            "end_date": end_date.isoformat() if end_date else datetime.now().isoformat(),
            "breakdown_by_category": {},
            "breakdown_by_provider": {},
            "breakdown_by_model": {},
            "period_data": [],
        }


def get_cost_history(
    user_id: Optional[str] = None,
    workflow_id: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> List[Dict[str, Any]]:
    """
    Get cost history records.
    
    Args:
        user_id: Optional user ID filter
        workflow_id: Optional workflow ID filter
        limit: Maximum number of results
        offset: Offset for pagination
        start_date: Optional start date filter
        end_date: Optional end date filter
        
    Returns:
        List of cost record dictionaries
    """
    if not is_database_configured():
        return []
    
    conditions = []
    params = []
    
    if user_id:
        conditions.append("user_id = %s")
        params.append(user_id)
    
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
    
    try:
        import json
        
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    SELECT 
                        id, execution_id, workflow_id, user_id, node_id, node_type,
                        cost, tokens_used, duration_ms, provider, model, category,
                        config, metadata, created_at
                    FROM cost_records
                    WHERE {where_clause}
                    ORDER BY created_at DESC
                    LIMIT %s OFFSET %s
                    """,
                    params + [limit, offset],
                )
                
                records = []
                for row in cur.fetchall():
                    records.append({
                        "id": str(row[0]),
                        "execution_id": row[1],
                        "workflow_id": str(row[2]) if row[2] else None,
                        "user_id": str(row[3]) if row[3] else None,
                        "node_id": row[4],
                        "node_type": row[5],
                        "cost": float(row[6]) if row[6] else 0.0,
                        "tokens_used": json.loads(row[7]) if row[7] else {},
                        "duration_ms": row[8] or 0,
                        "provider": row[9],
                        "model": row[10],
                        "category": row[11],
                        "config": json.loads(row[12]) if row[12] else {},
                        "metadata": json.loads(row[13]) if row[13] else {},
                        "created_at": row[14].isoformat() if row[14] else None,
                    })
                
                return records
    except Exception as e:
        logger.error(f"Failed to get cost history: {e}", exc_info=True)
        return []

