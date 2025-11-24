"""
Database operations for user profiles.

This module provides CRUD operations for user profiles using the database.
"""

from typing import Optional, Dict, Any

from backend.core.database import get_db_connection, is_database_configured, get_supabase_client, is_supabase_configured
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
    logger.info(f"Creating profile for user {user_id}")
    
    # Try direct database connection first
    if is_database_configured():
        try:
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
                    
                    if row:
                        logger.info(f"Successfully created profile {user_id} via direct DB")
                        return {
                            "id": str(row[0]),
                            "email": row[1],
                            "name": row[2],
                            "role": row[3],
                            "avatar_url": row[4],
                            "created_at": row[5].isoformat() if row[5] else None,
                            "updated_at": row[6].isoformat() if row[6] else None,
                        }
        except Exception as e:
            logger.warning(f"Direct database connection failed for profile creation, falling back to Supabase: {e}")
    
    # Fallback to Supabase client
    supabase = get_supabase_client()
    if is_supabase_configured() and supabase:
        try:
            logger.debug(f"Using Supabase client to create profile for user {user_id}")
            
            # Prepare profile data
            profile_data = {
                "id": user_id,
                "email": email,
                "name": name,
                "role": role,
                "avatar_url": avatar_url,
            }
            
            # Use upsert to handle conflicts
            result = supabase.table("profiles").upsert(
                profile_data,
                on_conflict="id"
            ).execute()
            
            if result.data and len(result.data) > 0:
                profile = result.data[0]
                logger.info(f"Successfully created profile {profile['id']} for user {user_id} via Supabase")
                return {
                    "id": str(profile["id"]),
                    "email": profile["email"],
                    "name": profile.get("name"),
                    "role": profile.get("role", "user"),
                    "avatar_url": profile.get("avatar_url"),
                    "created_at": profile.get("created_at"),
                    "updated_at": profile.get("updated_at"),
                }
            else:
                raise RuntimeError("Supabase returned empty result")
                
        except Exception as e:
            logger.error(f"Failed to create profile via Supabase: {e}")
            raise RuntimeError(f"Failed to create profile: {str(e)}")
    
    # No database available
    error_msg = "Database not configured. "
    if not is_supabase_configured():
        error_msg += "Supabase not configured. "
    if not is_database_configured():
        error_msg += "Direct database connection not configured. "
    
    error_msg += "Please check your database configuration."
    logger.error(error_msg)
    raise RuntimeError(error_msg)


def get_profile(user_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a user profile by ID.
    
    Args:
        user_id: User ID
        
    Returns:
        Profile dictionary or None if not found
    """
    logger.debug(f"Getting profile for user {user_id}")
    
    # Try direct database connection first
    if is_database_configured():
        try:
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
                    if row:
                        logger.debug(f"Found profile for user {user_id} via direct DB")
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
                    else:
                        logger.debug(f"No profile found for user {user_id} via direct DB")
                        return None
        except Exception as e:
            logger.warning(f"Direct database connection failed for profile lookup, falling back to Supabase: {e}")
    
    # Fallback to Supabase client
    supabase = get_supabase_client()
    if is_supabase_configured() and supabase:
        try:
            logger.debug(f"Using Supabase client to get profile for user {user_id}")
            
            result = supabase.table("profiles").select("*").eq("id", user_id).execute()
            
            if result.data and len(result.data) > 0:
                profile = result.data[0]
                logger.debug(f"Found profile for user {user_id} via Supabase")
                return {
                    "id": str(profile["id"]),
                    "email": profile["email"],
                    "name": profile.get("name"),
                    "role": profile.get("role", "user"),
                    "avatar_url": profile.get("avatar_url"),
                    "settings": profile.get("settings", {}),
                    "created_at": profile.get("created_at"),
                    "updated_at": profile.get("updated_at"),
                }
            else:
                logger.debug(f"No profile found for user {user_id} via Supabase")
                return None
                
        except Exception as e:
            logger.error(f"Failed to get profile via Supabase: {e}")
            return None
    
    # No database available - return None (profile not found)
    logger.warning(f"No database connection available to get profile for user {user_id}")
    return None


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
    if name is None and email is None and avatar_url is None and role is None:
        return get_profile(user_id)
    
    # Try direct database connection first
    if is_database_configured():
        try:
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
                    if row:
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
                    else:
                        return None
        except Exception as e:
            logger.warning(f"Direct database connection failed for profile update, falling back to Supabase: {e}")
    
    # Fallback to Supabase client
    supabase = get_supabase_client()
    if is_supabase_configured() and supabase:
        try:
            # Prepare update data
            update_data = {}
            if name is not None:
                update_data["name"] = name
            if email is not None:
                update_data["email"] = email
            if avatar_url is not None:
                update_data["avatar_url"] = avatar_url
            if role is not None:
                update_data["role"] = role
            
            result = supabase.table("profiles").update(update_data).eq("id", user_id).execute()
            
            if result.data and len(result.data) > 0:
                profile = result.data[0]
                return {
                    "id": str(profile["id"]),
                    "email": profile["email"],
                    "name": profile.get("name"),
                    "role": profile.get("role", "user"),
                    "avatar_url": profile.get("avatar_url"),
                    "settings": profile.get("settings", {}),
                    "created_at": profile.get("created_at"),
                    "updated_at": profile.get("updated_at"),
                }
            else:
                return None
                
        except Exception as e:
            logger.error(f"Failed to update profile via Supabase: {e}")
            return None
    
    # No database available
    logger.warning(f"No database connection available to update profile for user {user_id}")
    return None

