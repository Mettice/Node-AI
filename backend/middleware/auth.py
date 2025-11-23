"""
Authentication middleware for FastAPI.

This middleware extracts user information from JWT tokens and adds it to request state.
"""

from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware

from backend.core.user_context import get_user_context
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class AuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware to extract and verify user authentication.
    
    This middleware:
    1. Extracts JWT token from Authorization header
    2. Verifies token with Supabase
    3. Adds user context to request.state
    """
    
    async def dispatch(self, request: Request, call_next):
        # Skip auth for health check and public endpoints
        if request.url.path in ["/health", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)
        
        # Get user context (will be None if not authenticated)
        user_context = await get_user_context(request)
        
        # Add to request state
        request.state.user_context = user_context
        request.state.user_id = user_context["id"] if user_context else None
        
        # Continue with request
        response = await call_next(request)
        return response

