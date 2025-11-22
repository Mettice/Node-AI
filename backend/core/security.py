"""
Security utilities and middleware for NodeAI backend.

Includes:
- Rate limiting
- Input validation
- Security headers
- Request sanitization
"""

from typing import Optional, Callable
from fastapi import Request, HTTPException, status
from fastapi.responses import Response
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import re
import html

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)


def sanitize_string(value: str, max_length: Optional[int] = None) -> str:
    """
    Sanitize a string input to prevent injection attacks.
    
    Args:
        value: Input string to sanitize
        max_length: Maximum allowed length (None for no limit)
        
    Returns:
        Sanitized string
    """
    if not isinstance(value, str):
        return str(value)
    
    # Remove null bytes
    value = value.replace('\x00', '')
    
    # Truncate if too long
    if max_length and len(value) > max_length:
        value = value[:max_length]
    
    # Escape HTML to prevent XSS
    value = html.escape(value)
    
    return value


def validate_workflow_id(workflow_id: str) -> bool:
    """
    Validate workflow ID format.
    
    Args:
        workflow_id: Workflow ID to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not workflow_id or not isinstance(workflow_id, str):
        return False
    
    # Allow UUIDs and alphanumeric with hyphens/underscores
    pattern = r'^[a-zA-Z0-9_-]+$'
    if not re.match(pattern, workflow_id):
        return False
    
    # Reasonable length limit
    if len(workflow_id) > 100:
        return False
    
    return True


def validate_node_id(node_id: str) -> bool:
    """
    Validate node ID format.
    
    Args:
        node_id: Node ID to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not node_id or not isinstance(node_id, str):
        return False
    
    # Allow alphanumeric with hyphens/underscores
    pattern = r'^[a-zA-Z0-9_-]+$'
    if not re.match(pattern, node_id):
        return False
    
    # Reasonable length limit
    if len(node_id) > 100:
        return False
    
    return True


def validate_file_name(file_name: str) -> bool:
    """
    Validate file name to prevent path traversal attacks.
    
    Args:
        file_name: File name to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not file_name or not isinstance(file_name, str):
        return False
    
    # Prevent path traversal
    if '..' in file_name or '/' in file_name or '\\' in file_name:
        return False
    
    # Prevent null bytes
    if '\x00' in file_name:
        return False
    
    # Reasonable length limit
    if len(file_name) > 255:
        return False
    
    return True


def sanitize_dict(data: dict, max_depth: int = 10) -> dict:
    """
    Recursively sanitize dictionary values.
    
    Args:
        data: Dictionary to sanitize
        max_depth: Maximum recursion depth
        
    Returns:
        Sanitized dictionary
    """
    if max_depth <= 0:
        return {}
    
    sanitized = {}
    for key, value in data.items():
        # Sanitize key
        sanitized_key = sanitize_string(str(key), max_length=100)
        
        # Sanitize value
        if isinstance(value, str):
            sanitized[sanitized_key] = sanitize_string(value, max_length=10000)
        elif isinstance(value, dict):
            sanitized[sanitized_key] = sanitize_dict(value, max_depth - 1)
        elif isinstance(value, list):
            sanitized[sanitized_key] = [
                sanitize_dict(item, max_depth - 1) if isinstance(item, dict)
                else sanitize_string(str(item), max_length=10000) if isinstance(item, str)
                else item
                for item in value[:100]  # Limit list size
            ]
        else:
            sanitized[sanitized_key] = value
    
    return sanitized


async def add_security_headers(request: Request, call_next):
    """
    Middleware to add security headers to responses.
    
    Args:
        request: FastAPI request
        call_next: Next middleware/endpoint
        
    Returns:
        Response with security headers
    """
    response = await call_next(request)
    
    # Add security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    
    # Only add CSP in production
    from backend.config import settings
    if not settings.debug:
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self' https:;"
        )
    
    return response

