"""
Authentication middleware for FastAPI.

This middleware extracts user information from JWT tokens and adds it to request state.
"""

import re

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from backend.core.database import get_supabase_client
from backend.core.user_context import get_user_context
from backend.utils.logger import get_logger

logger = get_logger(__name__)

# Paths that skip authentication entirely
PUBLIC_PATHS = {"/", "/health", "/api/v1/health", "/docs", "/redoc", "/openapi.json"}

# Paths that are reachable without a logged-in user: (methods, pattern)
UNAUTHENTICATED_ROUTES = [
    # OAuth provider redirects back here without our token
    ({"GET"}, re.compile(r"^/api/v1/oauth/callback$")),
    # Deployed workflow API / embeddable widget: only serves deployed workflows, checks X-API-Key itself
    ({"POST"}, re.compile(r"^/api/v1/workflows/[^/]+/query$")),
    # External webhook callers: the endpoint verifies enabled state and signature itself
    ({"POST"}, re.compile(r"^/api/v1/webhooks/[^/]+/trigger$")),
    # The frontend reads these via EventSource / plain fetch, which send no token.
    # Execution IDs are random UUIDs.
    ({"GET"}, re.compile(r"^/api/v1/executions/[^/]+(/stream)?$")),
]


def _allows_unauthenticated(request: Request) -> bool:
    if request.method == "OPTIONS":  # CORS preflight never carries credentials
        return True
    path = request.url.path
    if not path.startswith("/api/"):
        return True
    return any(request.method in methods and pattern.match(path) for methods, pattern in UNAUTHENTICATED_ROUTES)


class AuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware to extract and verify user authentication.
    
    This middleware:
    1. Extracts JWT token from Authorization header
    2. Verifies token with Supabase
    3. Adds user context to request.state
    4. Rejects unauthenticated API requests when Supabase is configured
    """

    async def dispatch(self, request: Request, call_next):
        # Skip auth for health check and public endpoints
        if request.url.path in PUBLIC_PATHS:
            return await call_next(request)

        # Get user context (will be None if not authenticated)
        user_context = await get_user_context(request)

        # Without Supabase (local development) there is no auth to enforce
        if user_context is None and get_supabase_client() and not _allows_unauthenticated(request):
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Authentication required"},
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Add to request state
        request.state.user_context = user_context
        request.state.user_id = user_context["id"] if user_context else None
        
        # Continue with request
        response = await call_next(request)
        return response

