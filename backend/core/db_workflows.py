"""
Database operations for workflows.

This module provides CRUD operations for workflows using the database.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID
import json

from backend.core.database import get_db_connection, is_database_configured
from backend.utils.logger import get_logger

logger = get_logger(__name__)


def create_workflow(
    user_id: str,
    name: str,
    nodes: List[Dict[str, Any]],
    edges: List[Dict[str, Any]],
    description: Optional[str] = None,
    tags: Optional[List[str]] = None,
    is_template: bool = False,
) -> Dict[str, Any]:
    """
    Create a new workflow in the database.
    
    Args:
        user_id: User ID who owns the workflow
        name: Workflow name
        nodes: List of workflow nodes
        edges: List of workflow edges
        description: Optional workflow description
        tags: Optional list of tags
        is_template: Whether this is a template workflow
        
    Returns:
        Created workflow dictionary
    """
    if not is_database_configured():
        raise RuntimeError("Database not configured")
    
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO workflows (user_id, name, description, nodes, edges, tags, is_template)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id, user_id, name, description, nodes, edges, tags, is_template,
                          is_deployed, deployed_at, created_at, updated_at
                """,
                (
                    user_id,
                    name,
                    description,
                    json.dumps(nodes),
                    json.dumps(edges),
                    tags or [],
                    is_template,
                ),
            )
            row = cur.fetchone()
            
            return {
                "id": str(row[0]),
                "user_id": str(row[1]),
                "name": row[2],
                "description": row[3],
                "nodes": row[4] if isinstance(row[4], list) else json.loads(row[4]),
                "edges": row[5] if isinstance(row[5], list) else json.loads(row[5]),
                "tags": row[6] or [],
                "is_template": row[7],
                "is_deployed": row[8],
                "deployed_at": row[9].isoformat() if row[9] else None,
                "created_at": row[10].isoformat() if row[10] else None,
                "updated_at": row[11].isoformat() if row[11] else None,
            }


def get_workflow(workflow_id: str, user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Get a workflow by ID.
    
    Args:
        workflow_id: Workflow ID
        user_id: Optional user ID to verify ownership
        
    Returns:
        Workflow dictionary or None if not found
    """
    if not is_database_configured():
        return None
    
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            if user_id:
                cur.execute(
                    """
                    SELECT id, user_id, name, description, nodes, edges, tags, is_template,
                           is_deployed, deployed_at, created_at, updated_at
                    FROM workflows
                    WHERE id = %s AND user_id = %s
                    """,
                    (workflow_id, user_id),
                )
            else:
                cur.execute(
                    """
                    SELECT id, user_id, name, description, nodes, edges, tags, is_template,
                           is_deployed, deployed_at, created_at, updated_at
                    FROM workflows
                    WHERE id = %s
                    """,
                    (workflow_id,),
                )
            
            row = cur.fetchone()
            if not row:
                return None
            
            return {
                "id": str(row[0]),
                "user_id": str(row[1]),
                "name": row[2],
                "description": row[3],
                "nodes": row[4] if isinstance(row[4], list) else json.loads(row[4]),
                "edges": row[5] if isinstance(row[5], list) else json.loads(row[5]),
                "tags": row[6] or [],
                "is_template": row[7],
                "is_deployed": row[8],
                "deployed_at": row[9].isoformat() if row[9] else None,
                "created_at": row[10].isoformat() if row[10] else None,
                "updated_at": row[11].isoformat() if row[11] else None,
            }


def list_workflows(
    user_id: str,
    is_template: Optional[bool] = None,
    is_deployed: Optional[bool] = None,
    limit: int = 100,
    offset: int = 0,
) -> List[Dict[str, Any]]:
    """
    List workflows for a user.
    
    Args:
        user_id: User ID
        is_template: Filter by template status
        is_deployed: Filter by deployment status
        limit: Maximum number of results
        offset: Offset for pagination
        
    Returns:
        List of workflow dictionaries
    """
    if not is_database_configured():
        return []
    
    conditions = ["user_id = %s"]
    params = [user_id]
    
    if is_template is not None:
        conditions.append("is_template = %s")
        params.append(is_template)
    
    if is_deployed is not None:
        conditions.append("is_deployed = %s")
        params.append(is_deployed)
    
    where_clause = " AND ".join(conditions)
    
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT id, user_id, name, description, nodes, edges, tags, is_template,
                       is_deployed, deployed_at, created_at, updated_at
                FROM workflows
                WHERE {where_clause}
                ORDER BY updated_at DESC
                LIMIT %s OFFSET %s
                """,
                params + [limit, offset],
            )
            
            workflows = []
            for row in cur.fetchall():
                workflows.append({
                    "id": str(row[0]),
                    "user_id": str(row[1]),
                    "name": row[2],
                    "description": row[3],
                    "nodes": row[4] if isinstance(row[4], list) else json.loads(row[4]),
                    "edges": row[5] if isinstance(row[5], list) else json.loads(row[5]),
                    "tags": row[6] or [],
                    "is_template": row[7],
                    "is_deployed": row[8],
                    "deployed_at": row[9].isoformat() if row[9] else None,
                    "created_at": row[10].isoformat() if row[10] else None,
                    "updated_at": row[11].isoformat() if row[11] else None,
                })
            
            return workflows


def update_workflow(
    workflow_id: str,
    user_id: str,
    name: Optional[str] = None,
    description: Optional[str] = None,
    nodes: Optional[List[Dict[str, Any]]] = None,
    edges: Optional[List[Dict[str, Any]]] = None,
    tags: Optional[List[str]] = None,
    is_template: Optional[bool] = None,
    is_deployed: Optional[bool] = None,
) -> Optional[Dict[str, Any]]:
    """
    Update a workflow.
    
    Args:
        workflow_id: Workflow ID
        user_id: User ID (for ownership verification)
        name: Optional new name
        description: Optional new description
        nodes: Optional new nodes
        edges: Optional new edges
        tags: Optional new tags
        is_template: Optional template status
        is_deployed: Optional deployment status
        
    Returns:
        Updated workflow dictionary or None if not found
    """
    if not is_database_configured():
        return None
    
    updates = []
    params = []
    
    if name is not None:
        updates.append("name = %s")
        params.append(name)
    
    if description is not None:
        updates.append("description = %s")
        params.append(description)
    
    if nodes is not None:
        updates.append("nodes = %s")
        params.append(json.dumps(nodes))
    
    if edges is not None:
        updates.append("edges = %s")
        params.append(edges)
    
    if tags is not None:
        updates.append("tags = %s")
        params.append(tags)
    
    if is_template is not None:
        updates.append("is_template = %s")
        params.append(is_template)
    
    if is_deployed is not None:
        updates.append("is_deployed = %s")
        params.append(is_deployed)
        if is_deployed:
            updates.append("deployed_at = %s")
            params.append(datetime.now())
        else:
            updates.append("deployed_at = NULL")
    
    if not updates:
        return get_workflow(workflow_id, user_id)
    
    updates.append("updated_at = %s")
    params.append(datetime.now())
    
    params.extend([workflow_id, user_id])
    
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                UPDATE workflows
                SET {', '.join(updates)}
                WHERE id = %s AND user_id = %s
                RETURNING id, user_id, name, description, nodes, edges, tags, is_template,
                          is_deployed, deployed_at, created_at, updated_at
                """,
                params,
            )
            
            row = cur.fetchone()
            if not row:
                return None
            
            return {
                "id": str(row[0]),
                "user_id": str(row[1]),
                "name": row[2],
                "description": row[3],
                "nodes": row[4] if isinstance(row[4], list) else json.loads(row[4]),
                "edges": row[5] if isinstance(row[5], list) else json.loads(row[5]),
                "tags": row[6] or [],
                "is_template": row[7],
                "is_deployed": row[8],
                "deployed_at": row[9].isoformat() if row[9] else None,
                "created_at": row[10].isoformat() if row[10] else None,
                "updated_at": row[11].isoformat() if row[11] else None,
            }


def delete_workflow(workflow_id: str, user_id: str) -> bool:
    """
    Delete a workflow.
    
    Args:
        workflow_id: Workflow ID
        user_id: User ID (for ownership verification)
        
    Returns:
        True if deleted, False if not found
    """
    if not is_database_configured():
        return False
    
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM workflows WHERE id = %s AND user_id = %s",
                (workflow_id, user_id),
            )
            return cur.rowcount > 0

