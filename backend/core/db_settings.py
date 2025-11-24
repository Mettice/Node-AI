"""
Database operations for user settings.

This module provides functions to get and update user settings stored in the profiles table.
"""

from typing import Optional, Dict, Any
import json

from backend.core.database import get_db_connection, is_database_configured
from backend.utils.logger import get_logger

logger = get_logger(__name__)


def get_user_settings(user_id: str) -> Dict[str, Any]:
    """
    Get user settings from profile.
    
    Args:
        user_id: User ID
        
    Returns:
        Settings dictionary (empty dict if not found or not configured)
    """
    if not is_database_configured():
        return {}
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT settings
                    FROM profiles
                    WHERE id = %s
                    """,
                    (user_id,),
                )
                
                row = cur.fetchone()
                if row and row[0]:
                    return row[0] if isinstance(row[0], dict) else json.loads(row[0])
                return {}
    except Exception as e:
        logger.warning(f"Failed to get user settings for {user_id}: {e}")
        return {}


def update_user_settings(user_id: str, settings: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update user settings in profile.
    
    This merges the provided settings with existing settings.
    
    Args:
        user_id: User ID
        settings: Settings dictionary to merge
        
    Returns:
        Updated settings dictionary
    """
    if not is_database_configured():
        raise RuntimeError("Database not configured")
    
    # Get existing settings
    existing = get_user_settings(user_id)
    
    # Merge settings
    updated = {**existing, **settings}
    
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE profiles
                SET settings = %s::jsonb, updated_at = NOW()
                WHERE id = %s
                RETURNING settings
                """,
                (json.dumps(updated), user_id),
            )
            
            row = cur.fetchone()
            if not row:
                # Profile doesn't exist, create it first
                raise ValueError(f"Profile not found for user {user_id}")
            
            return row[0] if isinstance(row[0], dict) else json.loads(row[0])


def get_observability_settings(user_id: str) -> Dict[str, Any]:
    """
    Get observability settings for a user.
    
    Args:
        user_id: User ID
        
    Returns:
        Observability settings dictionary with langsmith and langfuse keys
    """
    settings = get_user_settings(user_id)
    return settings.get("observability", {})


def update_observability_settings(user_id: str, observability_settings: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update observability settings for a user.
    
    Args:
        user_id: User ID
        observability_settings: Observability settings to update
        
    Returns:
        Updated observability settings
    """
    settings = get_user_settings(user_id)
    settings["observability"] = observability_settings
    updated = update_user_settings(user_id, settings)
    return updated.get("observability", {})

