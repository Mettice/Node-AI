"""
API Key Management API endpoints.

Provides CRUD operations for API keys, usage tracking, and validation.
"""

from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Header, Request
from pydantic import BaseModel, Field

from backend.core.security import limiter
from backend.core.api_keys import (
    create_api_key,
    load_api_key,
    load_all_api_keys,
    delete_api_key,
    validate_api_key,
    APIKey,
)
from backend.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1", tags=["API Keys"])


# ============================================
# Request/Response Models
# ============================================

class APIKeyCreateRequest(BaseModel):
    workflow_id: Optional[str] = Field(None, description="Workflow ID to associate with this key")
    name: str = Field("Untitled Key", description="Human-readable name for the key")
    rate_limit: Optional[int] = Field(None, description="Rate limit (requests per hour)")
    cost_limit: Optional[float] = Field(None, description="Cost limit (dollars per month)")


class APIKeyResponse(BaseModel):
    key_id: str
    workflow_id: Optional[str]
    name: str
    created_at: str
    last_used_at: Optional[str]
    is_active: bool
    rate_limit: Optional[int]
    cost_limit: Optional[float]
    # Note: We never return the actual key or hash for security


class APIKeyCreateResponse(BaseModel):
    api_key: str  # Only returned once on creation
    key_id: str
    workflow_id: Optional[str]
    name: str
    created_at: str
    rate_limit: Optional[int]
    cost_limit: Optional[float]
    message: str = "Store this API key securely. It will not be shown again."


class APIKeyUpdateRequest(BaseModel):
    name: Optional[str] = None
    is_active: Optional[bool] = None
    rate_limit: Optional[int] = None
    cost_limit: Optional[float] = None


class UsageStats(BaseModel):
    key_id: str
    total_requests: int
    total_cost: float
    last_used_at: Optional[str]
    requests_today: int
    cost_today: float


# ============================================
# Helper Functions
# ============================================

def api_key_to_response(api_key: APIKey) -> APIKeyResponse:
    """Convert APIKey to response model."""
    return APIKeyResponse(
        key_id=api_key.key_id,
        workflow_id=api_key.workflow_id,
        name=api_key.name,
        created_at=api_key.created_at.isoformat(),
        last_used_at=api_key.last_used_at.isoformat() if api_key.last_used_at else None,
        is_active=api_key.is_active,
        rate_limit=api_key.rate_limit,
        cost_limit=api_key.cost_limit,
    )


# ============================================
# API Endpoints
# ============================================

@router.post("/api-keys", response_model=APIKeyCreateResponse)
@limiter.limit("5/minute")
async def create_new_api_key(request_body: APIKeyCreateRequest, request: Request) -> APIKeyCreateResponse:
    """
    Create a new API key.
    
    The plain API key is only returned once. Store it securely.
    """
    try:
        plain_key, api_key = create_api_key(
            workflow_id=request_body.workflow_id,
            name=request_body.name,
            rate_limit=request_body.rate_limit,
            cost_limit=request_body.cost_limit,
        )
        
        return APIKeyCreateResponse(
            api_key=plain_key,
            key_id=api_key.key_id,
            workflow_id=api_key.workflow_id,
            name=api_key.name,
            created_at=api_key.created_at.isoformat(),
            rate_limit=api_key.rate_limit,
            cost_limit=api_key.cost_limit,
        )
    except Exception as e:
        logger.error(f"Error creating API key: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"error": "Failed to create API key", "message": str(e)},
        )


@router.get("/api-keys", response_model=List[APIKeyResponse])
@limiter.limit("30/minute")
async def list_api_keys(request: Request, workflow_id: Optional[str] = None) -> List[APIKeyResponse]:
    """List all API keys, optionally filtered by workflow_id."""
    try:
        all_keys = load_all_api_keys()
        
        # Filter by workflow_id if provided
        if workflow_id:
            all_keys = [k for k in all_keys if k.workflow_id == workflow_id]
        
        return [api_key_to_response(key) for key in all_keys]
    except Exception as e:
        logger.error(f"Error listing API keys: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"error": "Failed to list API keys", "message": str(e)},
        )


@router.get("/api-keys/{key_id}", response_model=APIKeyResponse)
@limiter.limit("30/minute")
async def get_api_key(key_id: str, request: Request) -> APIKeyResponse:
    """Get an API key by ID."""
    api_key = load_api_key(key_id)
    if not api_key:
        raise HTTPException(
            status_code=404,
            detail=f"API key {key_id} not found",
        )
    return api_key_to_response(api_key)


@router.put("/api-keys/{key_id}", response_model=APIKeyResponse)
@limiter.limit("20/minute")
async def update_api_key(key_id: str, request_body: APIKeyUpdateRequest, request: Request) -> APIKeyResponse:
    """Update an API key (name, active status, limits)."""
    api_key = load_api_key(key_id)
    if not api_key:
        raise HTTPException(
            status_code=404,
            detail=f"API key {key_id} not found",
        )
    
    try:
        # Update fields
        if request_body.name is not None:
            api_key.name = request_body.name
        if request_body.is_active is not None:
            api_key.is_active = request_body.is_active
        if request_body.rate_limit is not None:
            api_key.rate_limit = request_body.rate_limit
        if request_body.cost_limit is not None:
            api_key.cost_limit = request_body.cost_limit
        
        # Save updated key
        from backend.core.api_keys import save_api_key
        save_api_key(api_key)
        
        return api_key_to_response(api_key)
    except Exception as e:
        logger.error(f"Error updating API key {key_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"error": "Failed to update API key", "message": str(e)},
        )


@router.delete("/api-keys/{key_id}")
@limiter.limit("10/minute")
async def delete_api_key_endpoint(key_id: str, request: Request) -> dict:
    """Delete an API key."""
    if not delete_api_key(key_id):
        raise HTTPException(
            status_code=404,
            detail=f"API key {key_id} not found",
        )
    return {"message": f"API key {key_id} deleted successfully"}


@router.get("/api-keys/{key_id}/usage", response_model=UsageStats)
@limiter.limit("30/minute")
async def get_api_key_usage(key_id: str, request: Request) -> UsageStats:
    """Get usage statistics for an API key."""
    api_key = load_api_key(key_id)
    if not api_key:
        raise HTTPException(
            status_code=404,
            detail=f"API key {key_id} not found",
        )
    
    # Get actual usage statistics
    from backend.core.usage_tracking import get_usage_stats
    stats = get_usage_stats(key_id)
    
    return UsageStats(
        key_id=api_key.key_id,
        total_requests=stats["total_requests"],
        total_cost=stats["total_cost"],
        last_used_at=stats["last_used_at"] or (api_key.last_used_at.isoformat() if api_key.last_used_at else None),
        requests_today=stats["requests_today"],
        cost_today=stats["cost_today"],
    )


# ============================================
# API Key Validation Dependency
# ============================================

async def get_api_key_from_header(x_api_key: Optional[str] = Header(None)) -> Optional[APIKey]:
    """
    Dependency to extract and validate API key from request header.
    
    Usage:
        @router.post("/endpoint")
        async def my_endpoint(api_key: APIKey = Depends(get_api_key_from_header)):
            if not api_key:
                raise HTTPException(401, "API key required")
            # Use api_key.workflow_id, etc.
    """
    if not x_api_key:
        return None
    
    return validate_api_key(x_api_key)

