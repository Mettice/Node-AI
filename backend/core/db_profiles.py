"""
Database operations for user profiles.

This module provides CRUD operations for user profiles using the database.
"""

from typing import Optional, Dict, Any

from backend.core.database import get_db_connection, is_database_configured
from backend.utils.logger import get_logger

logger = get_logger(__name__)


def create_profile(
    user_id: str,
    email: str,
    name: Optional[str] = None,
    role: str = "user",
    avatar_url: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Create a new user profile.
    
    Args:
        user_id: User ID (from Supabase auth)
        email: User email
        name: Optional user name
        role: User role (admin, user, viewer)
        avatar_url: Optional avatar URL
        
    Returns:
        Created profile dictionary
    """
    if not is_database_configured():
        raise RuntimeError("Database not configured")
    
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO profiles (id, email, name, role, avatar_url)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE
                SET email = EXCLUDED.email, name = EXCLUDED.name, role = EXCLUDED.role,
                    avatar_url = EXCLUDED.avatar_url, updated_at = NOW()
                RETURNING id, email, name, role, avatar_url, created_at, updated_at
                """,
                (user_id, email, name, role, avatar_url),
            )
            row = cur.fetchone()
            
            return {
                "id": str(row[0]),
                "email": row[1],
                "name": row[2],
                "role": row[3],
                "avatar_url": row[4],
                "created_at": row[5].isoformat() if row[5] else None,
                "updated_at": row[6].isoformat() if row[6] else None,
            }


def get_profile(user_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a user profile by ID.
    
    Args:
        user_id: User ID
        
    Returns:
        Profile dictionary or None if not found
    """
    if not is_database_configured():
        return None
    
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, email, name, role, avatar_url, settings, created_at, updated_at
                FROM profiles
                WHERE id = %s
                """,
                (user_id,),
            )
            
            row = cur.fetchone()
            if not row:
                return None
            
            return {
                "id": str(row[0]),
                "email": row[1],
                "name": row[2],
                "role": row[3],
                "avatar_url": row[4],
                "settings": row[5] or {},
                "created_at": row[6].isoformat() if row[6] else None,
                "updated_at": row[7].isoformat() if row[7] else None,
            }


def update_profile(
    user_id: str,
    name: Optional[str] = None,
    email: Optional[str] = None,
    avatar_url: Optional[str] = None,
    role: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    Update a user profile.
    
    Args:
        user_id: User ID
        name: Optional new name
        email: Optional new email
        avatar_url: Optional new avatar URL
        role: Optional new role (admin only)
        
    Returns:
        Updated profile dictionary or None if not found
    """
    if not is_database_configured():
        return None
    
    updates = []
    params = []
    
    if name is not None:
        updates.append("name = %s")
        params.append(name)
    
    if email is not None:
        updates.append("email = %s")
        params.append(email)
    
    if avatar_url is not None:
        updates.append("avatar_url = %s")
        params.append(avatar_url)
    
    if role is not None:
        updates.append("role = %s")
        params.append(role)
    
    if not updates:
        return get_profile(user_id)
    
    updates.append("updated_at = NOW()")
    params.append(user_id)
    
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                UPDATE profiles
                SET {', '.join(updates)}
                WHERE id = %s
                RETURNING id, email, name, role, avatar_url, settings, created_at, updated_at
                """,
                params,
            )
            
            row = cur.fetchone()
            if not row:
                return None
            
            return {
                "id": str(row[0]),
                "email": row[1],
                "name": row[2],
                "role": row[3],
                "avatar_url": row[4],
                "settings": row[5] or {},
                "created_at": row[6].isoformat() if row[6] else None,
                "updated_at": row[7].isoformat() if row[7] else None,
            }

