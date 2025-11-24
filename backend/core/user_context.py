"""
User context management for requests.

This module provides utilities for managing user context throughout
the request lifecycle.
"""

from typing import Optional
from fastapi import Request

from backend.core.auth_middleware import get_current_user, get_user_id, set_user_id
from backend.core.db_profiles import get_profile, create_profile
from backend.utils.logger import get_logger

logger = get_logger(__name__)


async def get_user_context(request: Request) -> Optional[dict]:
    """
    Get full user context including profile information.
    
    This function:
    1. Gets the authenticated user from the JWT token
    2. Fetches or creates the user profile in the database
    3. Returns complete user context
    
    Args:
        request: FastAPI request object
        
    Returns:
        User context dictionary with id, email, profile, role, etc., or None
    """
    # Get authenticated user
    user = await get_current_user(request)
    if not user:
        return None
    
    user_id = user["id"]
    
    # Set user_id in request state for easy access
    set_user_id(request, user_id)
    
    # Get or create profile (handle database connection failures)
    profile = None
    try:
        profile = get_profile(user_id)
    except Exception as e:
        logger.warning(f"Failed to get profile for user {user_id}: {e}. Using basic user context.")
        # Return basic user info without profile when database is unavailable
        return {
            "id": user_id,
            "email": user.get("email"),
            "role": "user",
            "profile": None,
        }
    
    if not profile:
        # Create profile if it doesn't exist
        try:
            profile = create_profile(
                user_id=user_id,
                email=user.get("email", ""),
                name=user.get("user_metadata", {}).get("name"),
                role="user",  # Default role
            )
            logger.info(f"Created profile for user {user_id}")
        except Exception as e:
            logger.error(f"Failed to create profile for user {user_id}: {e}")
            # Return basic user info even if profile creation fails
            return {
                "id": user_id,
                "email": user.get("email"),
                "role": "user",
                "profile": None,
            }
    
    return {
        "id": user_id,
        "email": user.get("email"),
        "role": profile.get("role", "user"),
        "profile": profile,
    }


async def require_user_context(request: Request) -> dict:
    """
    Require user context and return it.
    
    This is a stricter version that raises an exception if user is not authenticated.
    
    Args:
        request: FastAPI request object
        
    Returns:
        User context dictionary
        
    Raises:
        HTTPException: If user is not authenticated
    """
    from fastapi import HTTPException, status
    
    context = await get_user_context(request)
    
    if not context:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return context


def get_user_id_from_request(request: Request) -> Optional[str]:
    """
    Get user ID from request state (set by auth middleware).
    
    This is a convenience function that extracts the user_id from the request state.
    The user_id is set by the auth middleware when a user is authenticated.
    
    Args:
        request: FastAPI request object
        
    Returns:
        User ID string or None if not authenticated
    """
    return getattr(request.state, "user_id", None)