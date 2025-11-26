"""
Error handling middleware for consistent API error responses.

This middleware catches exceptions and converts them to standardized
error responses using the APIError format.
"""

import uuid
import logging
from typing import Callable
from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from backend.core.errors import (
    APIError, 
    handle_unexpected_error,
    rate_limit_error,
    ErrorCodes
)

logger = logging.getLogger(__name__)


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Middleware to handle errors consistently across all endpoints."""
    
    def __init__(self, app: ASGIApp, debug: bool = False):
        super().__init__(app)
        self.debug = debug
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate request ID for error tracking
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        try:
            response = await call_next(request)
            return response
            
        except APIError as e:
            # Our standardized errors - just return them
            logger.warning(f"API Error [{request_id}]: {e.error_code} - {e.detail}")
            return JSONResponse(
                status_code=e.status_code,
                content=e.detail
            )
            
        except HTTPException as e:
            # Convert FastAPI HTTPException to our format
            if e.status_code == 429:
                # Special handling for rate limit errors
                api_error = rate_limit_error(
                    limit="Unknown limit",
                    retry_after=None
                )
            else:
                # Generic HTTPException conversion
                api_error = APIError(
                    status_code=e.status_code,
                    error_code=self._get_error_code_from_status(e.status_code),
                    message=str(e.detail),
                    request_id=request_id
                )
            
            logger.warning(f"HTTP Exception [{request_id}]: {e.status_code} - {str(e.detail)}")
            return JSONResponse(
                status_code=api_error.status_code,
                content=api_error.detail
            )
            
        except ValueError as e:
            # Convert ValueError to validation error
            api_error = APIError(
                status_code=422,
                error_code=ErrorCodes.INVALID_INPUT,
                message="Validation error",
                details=str(e),
                suggestions=[
                    "Check your input parameters",
                    "Ensure all required fields are provided",
                    "Verify data types match expected format"
                ],
                request_id=request_id
            )
            
            logger.warning(f"Validation Error [{request_id}]: {str(e)}")
            return JSONResponse(
                status_code=api_error.status_code,
                content=api_error.detail
            )
            
        except PermissionError as e:
            # Handle permission errors
            api_error = APIError(
                status_code=403,
                error_code=ErrorCodes.INSUFFICIENT_PERMISSIONS,
                message="Access denied",
                details=str(e),
                suggestions=[
                    "Check that you have the required permissions",
                    "Verify your authentication credentials",
                    "Contact an administrator for access"
                ],
                request_id=request_id
            )
            
            logger.warning(f"Permission Error [{request_id}]: {str(e)}")
            return JSONResponse(
                status_code=api_error.status_code,
                content=api_error.detail
            )
            
        except FileNotFoundError as e:
            # Handle file not found errors
            api_error = APIError(
                status_code=404,
                error_code=ErrorCodes.FILE_NOT_FOUND,
                message="File not found",
                details=str(e),
                suggestions=[
                    "Check that the file path is correct",
                    "Ensure the file exists and is accessible",
                    "Verify you have permission to access the file"
                ],
                request_id=request_id
            )
            
            logger.warning(f"File Not Found [{request_id}]: {str(e)}")
            return JSONResponse(
                status_code=api_error.status_code,
                content=api_error.detail
            )
            
        except ConnectionError as e:
            # Handle database/external service connection errors
            api_error = APIError(
                status_code=503,
                error_code=ErrorCodes.SERVICE_UNAVAILABLE,
                message="Service temporarily unavailable",
                details=str(e),
                suggestions=[
                    "Try again in a few moments",
                    "Check your internet connection",
                    "Contact support if the issue persists"
                ],
                request_id=request_id
            )
            
            logger.error(f"Connection Error [{request_id}]: {str(e)}", exc_info=True)
            return JSONResponse(
                status_code=api_error.status_code,
                content=api_error.detail
            )
            
        except TimeoutError as e:
            # Handle timeout errors
            api_error = APIError(
                status_code=504,
                error_code=ErrorCodes.WORKFLOW_TIMEOUT,
                message="Request timeout",
                details=str(e),
                suggestions=[
                    "Try again with a simpler request",
                    "Consider breaking up large operations",
                    "Contact support if timeouts persist"
                ],
                request_id=request_id
            )
            
            logger.error(f"Timeout Error [{request_id}]: {str(e)}", exc_info=True)
            return JSONResponse(
                status_code=api_error.status_code,
                content=api_error.detail
            )
            
        except Exception as e:
            # Catch-all for unexpected errors
            api_error = handle_unexpected_error(e, request_id)
            
            logger.error(f"Unexpected Error [{request_id}]: {str(e)}", exc_info=True)
            return JSONResponse(
                status_code=api_error.status_code,
                content=api_error.detail
            )
    
    def _get_error_code_from_status(self, status_code: int) -> str:
        """Convert HTTP status code to error code."""
        error_codes = {
            400: ErrorCodes.INVALID_INPUT,
            401: ErrorCodes.AUTHENTICATION_REQUIRED,
            403: ErrorCodes.INSUFFICIENT_PERMISSIONS,
            404: ErrorCodes.WORKFLOW_NOT_FOUND,  # Generic, will be overridden by specific handlers
            409: ErrorCodes.INVALID_INPUT,
            422: ErrorCodes.INVALID_INPUT,
            429: ErrorCodes.RATE_LIMIT_EXCEEDED,
            500: ErrorCodes.INTERNAL_ERROR,
            502: ErrorCodes.SERVICE_UNAVAILABLE,
            503: ErrorCodes.SERVICE_UNAVAILABLE,
            504: ErrorCodes.WORKFLOW_TIMEOUT
        }
        return error_codes.get(status_code, ErrorCodes.INTERNAL_ERROR)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware to add request IDs to all responses."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate or extract request ID
        request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
        request.state.request_id = request_id
        
        response = await call_next(request)
        
        # Add request ID to response headers
        response.headers["x-request-id"] = request_id
        
        return response