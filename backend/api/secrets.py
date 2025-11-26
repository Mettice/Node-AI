"""
API endpoints for secrets vault management.
"""

from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field

from backend.core.user_context import require_user_context
from backend.core.security import limiter
from backend.core.db_secrets import (
    create_secret,
    get_secret,
    list_secrets,
    update_secret,
    delete_secret,
    get_secret_value,
)
from backend.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/secrets", tags=["secrets"])


# Request/Response Models
class SecretCreate(BaseModel):
    name: str = Field(..., description="Secret name")
    provider: str = Field(..., description="Provider (e.g., 'openai', 'anthropic')")
    secret_type: str = Field(..., description="Type (e.g., 'api_key', 'oauth_token')")
    value: str = Field(..., description="Secret value (plaintext)")
    description: Optional[str] = Field(None, description="Optional description")
    tags: Optional[List[str]] = Field(None, description="Optional tags")
    expires_at: Optional[datetime] = Field(None, description="Optional expiration date")


class SecretUpdate(BaseModel):
    name: Optional[str] = None
    value: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    is_active: Optional[bool] = None
    expires_at: Optional[datetime] = None


class SecretResponse(BaseModel):
    id: str
    user_id: str
    name: str
    provider: str
    secret_type: str
    description: Optional[str] = None
    tags: List[str] = []
    is_active: bool
    last_used_at: Optional[str] = None
    usage_count: int
    expires_at: Optional[str] = None
    created_at: str
    updated_at: str
    value: Optional[str] = None  # Only included when explicitly requested


@router.post("", response_model=SecretResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def create_secret_endpoint(
    secret: SecretCreate,
    request: Request,
    user_context: dict = Depends(require_user_context),
):
    """Create a new secret."""
    logger.info(f"CREATE SECRET REQUEST: user={user_context['id']}, provider={secret.provider}, type={secret.secret_type}, name={secret.name}")
    
    try:
        created = create_secret(
            user_id=user_context["id"],
            name=secret.name,
            provider=secret.provider,
            secret_type=secret.secret_type,
            secret_value=secret.value,
            description=secret.description,
            tags=secret.tags,
            expires_at=secret.expires_at,
            jwt_token=user_context.get("jwt_token"),
        )
        logger.info(f"SECRET CREATED SUCCESSFULLY: id={created['id']}")
        return SecretResponse(**created)
    except Exception as e:
        logger.error(f"Failed to create secret: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create secret: {str(e)}",
        )


@router.get("", response_model=List[SecretResponse])
@limiter.limit("30/minute")
async def list_secrets_endpoint(
    request: Request,
    provider: Optional[str] = None,
    secret_type: Optional[str] = None,
    is_active: Optional[bool] = None,
    user_context: dict = Depends(require_user_context),
):
    """List all secrets for the current user."""
    try:
        secrets = list_secrets(
            user_id=user_context["id"],
            provider=provider,
            secret_type=secret_type,
            is_active=is_active,
            jwt_token=user_context.get("jwt_token"),
        )
        return [SecretResponse(**s) for s in secrets]
    except Exception as e:
        logger.error(f"Failed to list secrets: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list secrets: {str(e)}",
        )


@router.get("/{secret_id}", response_model=SecretResponse)
@limiter.limit("30/minute")
async def get_secret_endpoint(
    secret_id: str,
    request: Request,
    decrypt: bool = False,
    user_context: dict = Depends(require_user_context),
):
    """Get a secret by ID."""
    try:
        secret = get_secret(
            secret_id=secret_id,
            user_id=user_context["id"],
            decrypt=decrypt,
            jwt_token=user_context.get("jwt_token"),
        )
        if not secret:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Secret not found",
            )
        return SecretResponse(**secret)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get secret: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get secret: {str(e)}",
        )


@router.put("/{secret_id}", response_model=SecretResponse)
@limiter.limit("10/minute")
async def update_secret_endpoint(
    secret_id: str,
    secret: SecretUpdate,
    request: Request,
    user_context: dict = Depends(require_user_context),
):
    """Update a secret."""
    try:
        updated = update_secret(
            secret_id=secret_id,
            user_id=user_context["id"],
            name=secret.name,
            secret_value=secret.value,
            description=secret.description,
            tags=secret.tags,
            is_active=secret.is_active,
            expires_at=secret.expires_at,
        )
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Secret not found",
            )
        return SecretResponse(**updated)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update secret: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update secret: {str(e)}",
        )


@router.delete("/{secret_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("10/minute")
async def delete_secret_endpoint(
    secret_id: str,
    request: Request,
    user_context: dict = Depends(require_user_context),
):
    """Delete a secret."""
    try:
        deleted = delete_secret(
            secret_id=secret_id,
            user_id=user_context["id"],
        )
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Secret not found",
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete secret: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete secret: {str(e)}",
        )

