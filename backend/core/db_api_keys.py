"""
Database operations for API keys.

This module provides CRUD operations for API keys using the database.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from decimal import Decimal

from backend.core.database import get_db_connection, is_database_configured
from backend.utils.logger import get_logger

logger = get_logger(__name__)


def create_api_key(
    user_id: str,
    key_id: str,
    key_hash: str,
    name: str,
    rate_limit: Optional[int] = None,
    cost_limit: Optional[float] = None,
    expires_at: Optional[datetime] = None,
) -> Dict[str, Any]:
    """
    Create a new API key in the database.
    
    Args:
        user_id: User ID who owns the API key
        key_id: Unique key identifier
        key_hash: Hashed API key value
        name: API key name
        rate_limit: Optional rate limit (requests per hour)
        cost_limit: Optional cost limit (per month)
        expires_at: Optional expiration date
        
    Returns:
        Created API key dictionary
    """
    if not is_database_configured():
        raise RuntimeError("Database not configured")
    
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO api_keys (user_id, key_id, key_hash, name, rate_limit, cost_limit, expires_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id, user_id, key_id, key_hash, name, rate_limit, cost_limit, enabled,
                          last_used_at, created_at, expires_at
                """,
                (
                    user_id,
                    key_id,
                    key_hash,
                    name,
                    rate_limit,
                    Decimal(str(cost_limit)) if cost_limit else None,
                    expires_at,
                ),
            )
            row = cur.fetchone()
            
            return {
                "id": str(row[0]),
                "user_id": str(row[1]),
                "key_id": row[2],
                "key_hash": row[3],
                "name": row[4],
                "rate_limit": row[5],
                "cost_limit": float(row[6]) if row[6] else None,
                "enabled": row[7],
                "last_used_at": row[8].isoformat() if row[8] else None,
                "created_at": row[9].isoformat() if row[9] else None,
                "expires_at": row[10].isoformat() if row[10] else None,
            }


def get_api_key(key_id: str, user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Get an API key by key_id.
    
    Args:
        key_id: API key ID
        user_id: Optional user ID to verify ownership
        
    Returns:
        API key dictionary or None if not found
    """
    if not is_database_configured():
        return None
    
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            if user_id:
                cur.execute(
                    """
                    SELECT id, user_id, key_id, key_hash, name, rate_limit, cost_limit, enabled,
                           last_used_at, created_at, expires_at
                    FROM api_keys
                    WHERE key_id = %s AND user_id = %s
                    """,
                    (key_id, user_id),
                )
            else:
                cur.execute(
                    """
                    SELECT id, user_id, key_id, key_hash, name, rate_limit, cost_limit, enabled,
                           last_used_at, created_at, expires_at
                    FROM api_keys
                    WHERE key_id = %s
                    """,
                    (key_id,),
                )
            
            row = cur.fetchone()
            if not row:
                return None
            
            return {
                "id": str(row[0]),
                "user_id": str(row[1]),
                "key_id": row[2],
                "key_hash": row[3],
                "name": row[4],
                "rate_limit": row[5],
                "cost_limit": float(row[6]) if row[6] else None,
                "enabled": row[7],
                "last_used_at": row[8].isoformat() if row[8] else None,
                "created_at": row[9].isoformat() if row[9] else None,
                "expires_at": row[10].isoformat() if row[10] else None,
            }


def list_api_keys(
    user_id: str,
    enabled: Optional[bool] = None,
    limit: int = 100,
    offset: int = 0,
) -> List[Dict[str, Any]]:
    """
    List API keys for a user.
    
    Args:
        user_id: User ID
        enabled: Filter by enabled status
        limit: Maximum number of results
        offset: Offset for pagination
        
    Returns:
        List of API key dictionaries
    """
    if not is_database_configured():
        return []
    
    conditions = ["user_id = %s"]
    params = [user_id]
    
    if enabled is not None:
        conditions.append("enabled = %s")
        params.append(enabled)
    
    where_clause = " AND ".join(conditions)
    
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT id, user_id, key_id, key_hash, name, rate_limit, cost_limit, enabled,
                       last_used_at, created_at, expires_at
                FROM api_keys
                WHERE {where_clause}
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
                """,
                params + [limit, offset],
            )
            
            keys = []
            for row in cur.fetchall():
                keys.append({
                    "id": str(row[0]),
                    "user_id": str(row[1]),
                    "key_id": row[2],
                    "key_hash": row[3],
                    "name": row[4],
                    "rate_limit": row[5],
                    "cost_limit": float(row[6]) if row[6] else None,
                    "enabled": row[7],
                    "last_used_at": row[8].isoformat() if row[8] else None,
                    "created_at": row[9].isoformat() if row[9] else None,
                    "expires_at": row[10].isoformat() if row[10] else None,
                })
            
            return keys


def update_api_key(
    key_id: str,
    user_id: str,
    name: Optional[str] = None,
    rate_limit: Optional[int] = None,
    cost_limit: Optional[float] = None,
    enabled: Optional[bool] = None,
) -> Optional[Dict[str, Any]]:
    """
    Update an API key.
    
    Args:
        key_id: API key ID
        user_id: User ID (for ownership verification)
        name: Optional new name
        rate_limit: Optional new rate limit
        cost_limit: Optional new cost limit
        enabled: Optional enabled status
        
    Returns:
        Updated API key dictionary or None if not found
    """
    if not is_database_configured():
        return None
    
    updates = []
    params = []
    
    if name is not None:
        updates.append("name = %s")
        params.append(name)
    
    if rate_limit is not None:
        updates.append("rate_limit = %s")
        params.append(rate_limit)
    
    if cost_limit is not None:
        updates.append("cost_limit = %s")
        params.append(Decimal(str(cost_limit)))
    
    if enabled is not None:
        updates.append("enabled = %s")
        params.append(enabled)
    
    if not updates:
        return get_api_key(key_id, user_id)
    
    params.extend([key_id, user_id])
    
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                UPDATE api_keys
                SET {', '.join(updates)}
                WHERE key_id = %s AND user_id = %s
                RETURNING id, user_id, key_id, key_hash, name, rate_limit, cost_limit, enabled,
                          last_used_at, created_at, expires_at
                """,
                params,
            )
            
            row = cur.fetchone()
            if not row:
                return None
            
            return {
                "id": str(row[0]),
                "user_id": str(row[1]),
                "key_id": row[2],
                "key_hash": row[3],
                "name": row[4],
                "rate_limit": row[5],
                "cost_limit": float(row[6]) if row[6] else None,
                "enabled": row[7],
                "last_used_at": row[8].isoformat() if row[8] else None,
                "created_at": row[9].isoformat() if row[9] else None,
                "expires_at": row[10].isoformat() if row[10] else None,
            }


def update_api_key_last_used(key_id: str) -> None:
    """
    Update the last_used_at timestamp for an API key.
    
    Args:
        key_id: API key ID
    """
    if not is_database_configured():
        return
    
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE api_keys SET last_used_at = %s WHERE key_id = %s",
                (datetime.now(), key_id),
            )


def delete_api_key(key_id: str, user_id: str) -> bool:
    """
    Delete an API key.
    
    Args:
        key_id: API key ID
        user_id: User ID (for ownership verification)
        
    Returns:
        True if deleted, False if not found
    """
    if not is_database_configured():
        return False
    
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM api_keys WHERE key_id = %s AND user_id = %s",
                (key_id, user_id),
            )
            return cur.rowcount > 0

