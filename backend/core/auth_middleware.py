"""
Authentication middleware for FastAPI.

This module provides JWT token verification and user context extraction
for Supabase Auth tokens.
"""

from typing import Optional
from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from backend.core.database import get_supabase_client
from backend.utils.logger import get_logger

logger = get_logger(__name__)

security = HTTPBearer(auto_error=False)


async def get_current_user(request: Request) -> Optional[dict]:
    """
    Extract and verify the current user from the JWT token.
    
    This function:
    1. Extracts the JWT token from the Authorization header
    2. Verifies the token with Supabase
    3. Returns the user information
    
    Args:
        request: FastAPI request object
        
    Returns:
        User dictionary with id, email, etc., or None if not authenticated
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    # Get Supabase client
    supabase = get_supabase_client()
    if not supabase:
        # If Supabase is not configured, allow unauthenticated access
        # (for backward compatibility during migration)
        logger.warning("Supabase not configured. Allowing unauthenticated access.")
        return None
    
    # Extract token from Authorization header
    authorization: Optional[str] = request.headers.get("Authorization")
    if not authorization:
        return None
    
    # Extract Bearer token
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            return None
    except ValueError:
        return None
    
    # Verify token with Supabase
    try:
        # Use Supabase client to verify the token
        # The Supabase client automatically verifies JWT tokens
        response = supabase.auth.get_user(token)
        
        if response.user:
            return {
                "id": response.user.id,
                "email": response.user.email,
                "user_metadata": response.user.user_metadata or {},
            }
        else:
            return None
            
    except Exception as e:
        logger.warning(f"Token verification failed: {e}")
        return None


async def require_auth(request: Request) -> dict:
    """
    Require authentication and return user information.
    
    This is a stricter version of get_current_user that raises an exception
    if the user is not authenticated.
    
    Args:
        request: FastAPI request object
        
    Returns:
        User dictionary with id, email, etc.
        
    Raises:
        HTTPException: If user is not authenticated
    """
    user = await get_current_user(request)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


def get_user_id(request: Request) -> Optional[str]:
    """
    Get user ID from request state (set by middleware).
    
    Args:
        request: FastAPI request object
        
    Returns:
        User ID or None
    """
    return getattr(request.state, "user_id", None)


def set_user_id(request: Request, user_id: str) -> None:
    """
    Set user ID in request state.
    
    Args:
        request: FastAPI request object
        user_id: User ID to set
    """
    request.state.user_id = user_id

