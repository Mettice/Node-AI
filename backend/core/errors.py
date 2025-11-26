"""
Standardized error handling and response formatting for NodeAI API.

This module provides consistent error responses across all API endpoints
with user-friendly messages, error codes, and actionable suggestions.
"""

from typing import Optional, Dict, Any, Union, List
from pydantic import BaseModel
from fastapi import HTTPException, status
import logging

logger = logging.getLogger(__name__)


class ErrorDetail(BaseModel):
    """Standardized error detail structure."""
    code: str
    message: str
    details: Optional[str] = None
    suggestions: Optional[List[str]] = None
    field: Optional[str] = None


class APIErrorResponse(BaseModel):
    """Standardized API error response format."""
    error: str
    error_code: str
    message: str
    details: Optional[str] = None
    suggestions: Optional[List[str]] = None
    timestamp: str
    request_id: Optional[str] = None
    validation_errors: Optional[List[ErrorDetail]] = None


class APIError(HTTPException):
    """Enhanced HTTPException with standardized error details."""
    
    def __init__(
        self,
        status_code: int,
        error_code: str,
        message: str,
        details: Optional[str] = None,
        suggestions: Optional[List[str]] = None,
        validation_errors: Optional[List[ErrorDetail]] = None,
        request_id: Optional[str] = None
    ):
        self.error_code = error_code
        self.details = details
        self.suggestions = suggestions
        self.validation_errors = validation_errors
        self.request_id = request_id
        
        # Create standardized detail object
        detail = {
            "error": self._get_error_name(status_code),
            "error_code": error_code,
            "message": message,
        }
        
        if details:
            detail["details"] = details
        if suggestions:
            detail["suggestions"] = suggestions
        if validation_errors:
            detail["validation_errors"] = [error.dict() for error in validation_errors]
        if request_id:
            detail["request_id"] = request_id
        
        from datetime import datetime
        detail["timestamp"] = datetime.utcnow().isoformat() + "Z"
        
        super().__init__(status_code=status_code, detail=detail)
    
    @staticmethod
    def _get_error_name(status_code: int) -> str:
        """Get human-readable error name from status code."""
        error_names = {
            400: "Bad Request",
            401: "Unauthorized", 
            403: "Forbidden",
            404: "Not Found",
            409: "Conflict",
            422: "Validation Error",
            429: "Rate Limited",
            500: "Internal Server Error",
            502: "Bad Gateway",
            503: "Service Unavailable",
            504: "Gateway Timeout"
        }
        return error_names.get(status_code, "Unknown Error")


# Pre-defined error codes for common scenarios
class ErrorCodes:
    """Standard error codes for consistent error handling."""
    
    # Authentication & Authorization
    INVALID_API_KEY = "INVALID_API_KEY"
    EXPIRED_TOKEN = "EXPIRED_TOKEN"
    INSUFFICIENT_PERMISSIONS = "INSUFFICIENT_PERMISSIONS"
    AUTHENTICATION_REQUIRED = "AUTHENTICATION_REQUIRED"
    
    # Validation Errors
    INVALID_INPUT = "INVALID_INPUT"
    MISSING_REQUIRED_FIELD = "MISSING_REQUIRED_FIELD"
    INVALID_FILE_FORMAT = "INVALID_FILE_FORMAT"
    FILE_TOO_LARGE = "FILE_TOO_LARGE"
    INVALID_WORKFLOW_STRUCTURE = "INVALID_WORKFLOW_STRUCTURE"
    
    # Resource Errors
    WORKFLOW_NOT_FOUND = "WORKFLOW_NOT_FOUND"
    EXECUTION_NOT_FOUND = "EXECUTION_NOT_FOUND"
    FILE_NOT_FOUND = "FILE_NOT_FOUND"
    MODEL_NOT_FOUND = "MODEL_NOT_FOUND"
    KNOWLEDGE_BASE_NOT_FOUND = "KNOWLEDGE_BASE_NOT_FOUND"
    
    # Rate Limiting
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    
    # External Service Errors
    OPENAI_API_ERROR = "OPENAI_API_ERROR"
    ANTHROPIC_API_ERROR = "ANTHROPIC_API_ERROR"
    DATABASE_ERROR = "DATABASE_ERROR"
    STORAGE_ERROR = "STORAGE_ERROR"
    
    # Workflow Execution
    EXECUTION_FAILED = "EXECUTION_FAILED"
    NODE_EXECUTION_ERROR = "NODE_EXECUTION_ERROR"
    WORKFLOW_TIMEOUT = "WORKFLOW_TIMEOUT"
    
    # General
    INTERNAL_ERROR = "INTERNAL_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    CONFIGURATION_ERROR = "CONFIGURATION_ERROR"


# Helper functions for common error scenarios
def validation_error(
    message: str,
    field: Optional[str] = None,
    details: Optional[str] = None,
    suggestions: Optional[List[str]] = None
) -> APIError:
    """Create a validation error."""
    validation_errors = []
    if field:
        validation_errors.append(ErrorDetail(
            code=ErrorCodes.INVALID_INPUT,
            message=message,
            field=field,
            details=details,
            suggestions=suggestions
        ))
    
    return APIError(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        error_code=ErrorCodes.INVALID_INPUT,
        message=message,
        details=details,
        suggestions=suggestions,
        validation_errors=validation_errors if validation_errors else None
    )


def not_found_error(
    resource_type: str,
    resource_id: str,
    suggestions: Optional[List[str]] = None
) -> APIError:
    """Create a not found error."""
    default_suggestions = [
        f"Check that the {resource_type} ID is correct",
        f"Ensure the {resource_type} exists and you have access to it",
        f"Use the list {resource_type}s endpoint to see available {resource_type}s"
    ]
    
    return APIError(
        status_code=status.HTTP_404_NOT_FOUND,
        error_code=f"{resource_type.upper()}_NOT_FOUND",
        message=f"{resource_type.title()} not found",
        details=f"No {resource_type} found with ID: {resource_id}",
        suggestions=suggestions or default_suggestions
    )


def authentication_error(
    message: str = "Authentication required",
    details: Optional[str] = None
) -> APIError:
    """Create an authentication error."""
    return APIError(
        status_code=status.HTTP_401_UNAUTHORIZED,
        error_code=ErrorCodes.AUTHENTICATION_REQUIRED,
        message=message,
        details=details,
        suggestions=[
            "Ensure you have a valid API key",
            "Include the Authorization header with 'Bearer <your-api-key>'",
            "Check that your API key hasn't expired",
            "Contact support if you need a new API key"
        ]
    )


def rate_limit_error(
    limit: str,
    retry_after: Optional[int] = None
) -> APIError:
    """Create a rate limit error."""
    suggestions = [
        "Wait before making another request",
        "Consider upgrading to a higher rate limit tier",
        "Implement exponential backoff in your client",
        "Batch multiple operations where possible"
    ]
    
    if retry_after:
        suggestions.insert(0, f"Retry after {retry_after} seconds")
    
    return APIError(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        error_code=ErrorCodes.RATE_LIMIT_EXCEEDED,
        message="Rate limit exceeded",
        details=f"You have exceeded the rate limit of {limit}",
        suggestions=suggestions
    )


def external_service_error(
    service_name: str,
    error_message: str,
    is_retryable: bool = True
) -> APIError:
    """Create an external service error."""
    suggestions = []
    
    if is_retryable:
        suggestions.extend([
            "Try again in a few moments",
            "Check if the service is experiencing issues",
            "Consider implementing retry logic in your application"
        ])
    else:
        suggestions.extend([
            "Check your API key configuration",
            "Verify your request parameters",
            "Contact support if the issue persists"
        ])
    
    error_code = f"{service_name.upper()}_API_ERROR"
    
    return APIError(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE if is_retryable else status.HTTP_400_BAD_REQUEST,
        error_code=error_code,
        message=f"{service_name} service error",
        details=error_message,
        suggestions=suggestions
    )


def workflow_execution_error(
    workflow_id: str,
    error_message: str,
    node_id: Optional[str] = None
) -> APIError:
    """Create a workflow execution error."""
    details = f"Workflow {workflow_id} failed to execute"
    if node_id:
        details += f" at node {node_id}"
    details += f": {error_message}"
    
    suggestions = [
        "Check the workflow configuration",
        "Verify all required inputs are provided",
        "Ensure all nodes are properly connected",
        "Check the execution logs for more details"
    ]
    
    if "API key" in error_message.lower():
        suggestions.extend([
            "Verify your LLM API keys are configured correctly",
            "Check that API keys haven't expired"
        ])
    
    return APIError(
        status_code=status.HTTP_400_BAD_REQUEST,
        error_code=ErrorCodes.EXECUTION_FAILED,
        message="Workflow execution failed",
        details=details,
        suggestions=suggestions
    )


def internal_server_error(
    message: str = "An internal error occurred",
    details: Optional[str] = None,
    error_id: Optional[str] = None
) -> APIError:
    """Create an internal server error."""
    suggestions = [
        "Try again in a few moments",
        "If the issue persists, contact support",
    ]
    
    if error_id:
        suggestions.append(f"Reference error ID: {error_id}")
    
    return APIError(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code=ErrorCodes.INTERNAL_ERROR,
        message=message,
        details=details,
        suggestions=suggestions,
        request_id=error_id
    )


def file_validation_error(
    filename: str,
    issue: str,
    max_size_mb: Optional[int] = None
) -> APIError:
    """Create a file validation error."""
    suggestions = []
    
    if "size" in issue.lower():
        suggestions.extend([
            f"Ensure file is smaller than {max_size_mb}MB" if max_size_mb else "Reduce file size",
            "Consider compressing the file",
            "Split large files into smaller chunks"
        ])
    elif "format" in issue.lower() or "type" in issue.lower():
        suggestions.extend([
            "Check that file format is supported",
            "Ensure file is not corrupted",
            "Convert file to a supported format"
        ])
    elif "name" in issue.lower():
        suggestions.extend([
            "Use alphanumeric characters and common symbols",
            "Avoid path traversal characters (../, \\, etc.)",
            "Keep filename length reasonable"
        ])
    
    return APIError(
        status_code=status.HTTP_400_BAD_REQUEST,
        error_code=ErrorCodes.INVALID_FILE_FORMAT,
        message="File validation failed",
        details=f"File '{filename}': {issue}",
        suggestions=suggestions
    )


# Middleware function to handle unexpected exceptions
def handle_unexpected_error(e: Exception, request_id: Optional[str] = None) -> APIError:
    """Handle unexpected exceptions with standardized error response."""
    logger.error(f"Unexpected error: {str(e)}", exc_info=True)
    
    return internal_server_error(
        message="An unexpected error occurred",
        details="The server encountered an unexpected condition",
        error_id=request_id
    )