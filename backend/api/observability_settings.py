"""
API endpoints for user observability settings.

Allows users to configure their LangSmith/LangFuse API keys through the UI.
"""

from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from backend.core.security import limiter
from backend.core.db_settings import (
    get_observability_settings,
    update_observability_settings,
)
from backend.core.user_context import get_user_id_from_request
from backend.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1", tags=["Observability"])


class ObservabilitySettingsRequest(BaseModel):
    """Request model for updating observability settings."""
    
    langsmith_api_key: Optional[str] = Field(None, description="LangSmith API key")
    langsmith_project: Optional[str] = Field(None, description="LangSmith project name")
    langfuse_public_key: Optional[str] = Field(None, description="LangFuse public key")
    langfuse_secret_key: Optional[str] = Field(None, description="LangFuse secret key")
    langfuse_host: Optional[str] = Field(None, description="LangFuse host URL")
    enabled: Optional[bool] = Field(None, description="Enable/disable observability")


class ObservabilitySettingsResponse(BaseModel):
    """Response model for observability settings."""
    
    langsmith_api_key: Optional[str] = None
    langsmith_project: Optional[str] = None
    langfuse_public_key: Optional[str] = None
    langfuse_secret_key: Optional[str] = None
    langfuse_host: Optional[str] = None
    enabled: bool = True


@router.get("/observability/settings", response_model=ObservabilitySettingsResponse)
@limiter.limit("30/minute")
async def get_settings(request: Request):
    """
    Get current user's observability settings.
    
    Returns masked API keys (only last 4 characters visible).
    """
    user_id = get_user_id_from_request(request)
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    try:
        settings = get_observability_settings(user_id)
        
        # Mask API keys for security
        def mask_key(key: Optional[str]) -> Optional[str]:
            if not key:
                return None
            if len(key) <= 4:
                return "••••"
            return "•" * (len(key) - 4) + key[-4:]
        
        return ObservabilitySettingsResponse(
            langsmith_api_key=mask_key(settings.get("langsmith_api_key")),
            langsmith_project=settings.get("langsmith_project", "nodeflow"),
            langfuse_public_key=mask_key(settings.get("langfuse_public_key")),
            langfuse_secret_key=mask_key(settings.get("langfuse_secret_key")),
            langfuse_host=settings.get("langfuse_host", "https://cloud.langfuse.com"),
            enabled=settings.get("enabled", True),
        )
    except Exception as e:
        logger.error(f"Failed to get observability settings: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get observability settings")


@router.put("/observability/settings", response_model=ObservabilitySettingsResponse)
@limiter.limit("20/minute")
async def update_settings(request: Request, settings: ObservabilitySettingsRequest):
    """
    Update current user's observability settings.
    
    Only provided fields will be updated. To clear a field, pass an empty string.
    """
    user_id = get_user_id_from_request(request)
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    try:
        # Get current settings
        current = get_observability_settings(user_id)
        
        # Build update dict (only include non-None values)
        update: Dict[str, Any] = {}
        
        if settings.langsmith_api_key is not None:
            # If empty string, clear it
            update["langsmith_api_key"] = settings.langsmith_api_key if settings.langsmith_api_key else None
        elif "langsmith_api_key" in current:
            update["langsmith_api_key"] = current["langsmith_api_key"]
        
        if settings.langsmith_project is not None:
            update["langsmith_project"] = settings.langsmith_project or "nodeflow"
        elif "langsmith_project" in current:
            update["langsmith_project"] = current["langsmith_project"]
        
        if settings.langfuse_public_key is not None:
            update["langfuse_public_key"] = settings.langfuse_public_key if settings.langfuse_public_key else None
        elif "langfuse_public_key" in current:
            update["langfuse_public_key"] = current["langfuse_public_key"]
        
        if settings.langfuse_secret_key is not None:
            update["langfuse_secret_key"] = settings.langfuse_secret_key if settings.langfuse_secret_key else None
        elif "langfuse_secret_key" in current:
            update["langfuse_secret_key"] = current["langfuse_secret_key"]
        
        if settings.langfuse_host is not None:
            update["langfuse_host"] = settings.langfuse_host or "https://cloud.langfuse.com"
        elif "langfuse_host" in current:
            update["langfuse_host"] = current["langfuse_host"]
        
        if settings.enabled is not None:
            update["enabled"] = settings.enabled
        elif "enabled" in current:
            update["enabled"] = current["enabled"]
        else:
            update["enabled"] = True
        
        # Update settings
        updated = update_observability_settings(user_id, update)
        
        # Return masked response
        def mask_key(key: Optional[str]) -> Optional[str]:
            if not key:
                return None
            if len(key) <= 4:
                return "••••"
            return "•" * (len(key) - 4) + key[-4:]
        
        return ObservabilitySettingsResponse(
            langsmith_api_key=mask_key(updated.get("langsmith_api_key")),
            langsmith_project=updated.get("langsmith_project", "nodeflow"),
            langfuse_public_key=mask_key(updated.get("langfuse_public_key")),
            langfuse_secret_key=mask_key(updated.get("langfuse_secret_key")),
            langfuse_host=updated.get("langfuse_host", "https://cloud.langfuse.com"),
            enabled=updated.get("enabled", True),
        )
    except Exception as e:
        logger.error(f"Failed to update observability settings: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to update observability settings")

