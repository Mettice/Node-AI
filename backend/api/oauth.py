"""
OAuth API endpoints for managing OAuth flows.
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from backend.core.oauth import OAuthManager
from backend.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/oauth", tags=["OAuth"])


class OAuthInitRequest(BaseModel):
    """Request to initialize OAuth flow."""
    service: str  # e.g., "slack", "google", "reddit"
    client_id: str
    redirect_uri: str
    scopes: list[str]
    user_id: Optional[str] = None
    additional_params: Optional[dict] = None


class OAuthInitResponse(BaseModel):
    """Response with OAuth authorization URL."""
    authorization_url: str
    state: str


class OAuthCallbackRequest(BaseModel):
    """OAuth callback request."""
    service: str
    code: str
    state: str
    client_id: str
    client_secret: str
    redirect_uri: str
    user_id: Optional[str] = None


class OAuthCallbackResponse(BaseModel):
    """OAuth callback response."""
    success: bool
    token_id: Optional[str] = None
    message: Optional[str] = None


@router.post("/init", response_model=OAuthInitResponse)
async def init_oauth_flow(request: OAuthInitRequest) -> OAuthInitResponse:
    """
    Initialize OAuth flow and get authorization URL.
    
    This endpoint generates an OAuth state and returns the authorization URL
    that the user should be redirected to.
    """
    try:
        result = OAuthManager.get_authorization_url(
            service=request.service,
            client_id=request.client_id,
            redirect_uri=request.redirect_uri,
            scopes=request.scopes,
            user_id=request.user_id,
            additional_params=request.additional_params,
        )
        
        return OAuthInitResponse(
            authorization_url=result["url"],
            state=result["state"],
        )
    except Exception as e:
        logger.error(f"OAuth init failed: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/callback")
async def oauth_callback(
    service: str = Query(...),
    code: str = Query(...),
    state: str = Query(...),
    error: Optional[str] = None,
):
    """
    Handle OAuth callback.
    
    This endpoint receives the OAuth callback and exchanges the code for tokens.
    In a real implementation, this would exchange the code for tokens server-side.
    """
    if error:
        logger.error(f"OAuth callback error: {error}")
        # Redirect to frontend with error
        return RedirectResponse(
            url=f"/oauth/callback?error={error}&service={service}"
        )
    
    # Validate state
    if not OAuthManager.validate_state(state):
        logger.error(f"Invalid OAuth state: {state}")
        return RedirectResponse(
            url=f"/oauth/callback?error=invalid_state&service={service}"
        )
    
    # In a real implementation, you would exchange the code for tokens here
    # For now, redirect to frontend with code and state
    return RedirectResponse(
        url=f"/oauth/callback?service={service}&code={code}&state={state}"
    )


@router.post("/exchange", response_model=OAuthCallbackResponse)
async def exchange_code_for_token(request: OAuthCallbackRequest) -> OAuthCallbackResponse:
    """
    Exchange OAuth authorization code for access token.
    
    This endpoint should be called from the backend (not frontend) to securely
    exchange the authorization code for tokens.
    """
    try:
        # Validate state
        if not OAuthManager.validate_state(request.state):
            return OAuthCallbackResponse(
                success=False,
                message="Invalid or expired OAuth state",
            )
        
        # Exchange code for token (service-specific)
        token_data = await _exchange_code_for_token(
            service=request.service,
            code=request.code,
            client_id=request.client_id,
            client_secret=request.client_secret,
            redirect_uri=request.redirect_uri,
        )
        
        # Store token
        token_id = OAuthManager.store_token(
            service=request.service,
            user_id=request.user_id,
            access_token=token_data["access_token"],
            refresh_token=token_data.get("refresh_token"),
            expires_in=token_data.get("expires_in"),
            token_type=token_data.get("token_type", "Bearer"),
            metadata=token_data.get("metadata"),
        )
        
        return OAuthCallbackResponse(
            success=True,
            token_id=token_id,
            message="OAuth token stored successfully",
        )
        
    except Exception as e:
        logger.error(f"OAuth token exchange failed: {e}", exc_info=True)
        return OAuthCallbackResponse(
            success=False,
            message=str(e),
        )


async def _exchange_code_for_token(
    service: str,
    code: str,
    client_id: str,
    client_secret: str,
    redirect_uri: str,
) -> dict:
    """
    Exchange authorization code for access token (service-specific).
    
    This is a helper function that handles the actual token exchange
    for different OAuth providers.
    """
    import httpx
    
    if service == "slack":
        # Slack OAuth v2 token exchange
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://slack.com/api/oauth.v2.access",
                data={
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "code": code,
                    "redirect_uri": redirect_uri,
                },
            )
            data = response.json()
            
            if not data.get("ok"):
                raise ValueError(f"Slack OAuth error: {data.get('error')}")
            
            return {
                "access_token": data["authed_user"]["access_token"],
                "refresh_token": data.get("refresh_token"),
                "expires_in": data.get("expires_in"),
                "token_type": "Bearer",
                "metadata": {
                    "team_id": data.get("team", {}).get("id"),
                    "team_name": data.get("team", {}).get("name"),
                    "user_id": data.get("authed_user", {}).get("id"),
                },
            }
    
    elif service == "google":
        # Google OAuth token exchange
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "code": code,
                    "redirect_uri": redirect_uri,
                    "grant_type": "authorization_code",
                },
            )
            data = response.json()
            
            if "error" in data:
                raise ValueError(f"Google OAuth error: {data.get('error_description')}")
            
            return {
                "access_token": data["access_token"],
                "refresh_token": data.get("refresh_token"),
                "expires_in": data.get("expires_in"),
                "token_type": data.get("token_type", "Bearer"),
                "metadata": {},
            }
    
    elif service == "reddit":
        # Reddit OAuth token exchange
        import base64
        
        auth_string = f"{client_id}:{client_secret}"
        auth_bytes = auth_string.encode('ascii')
        auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://www.reddit.com/api/v1/access_token",
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": redirect_uri,
                },
                headers={
                    "Authorization": f"Basic {auth_b64}",
                    "User-Agent": "NodAI/1.0",
                },
            )
            data = response.json()
            
            if "error" in data:
                raise ValueError(f"Reddit OAuth error: {data.get('error_description')}")
            
            return {
                "access_token": data["access_token"],
                "refresh_token": data.get("refresh_token"),
                "expires_in": data.get("expires_in"),
                "token_type": data.get("token_type", "Bearer"),
                "metadata": {},
            }
    
    else:
        raise ValueError(f"Unsupported OAuth service: {service}")


@router.get("/tokens")
async def list_oauth_tokens(
    service: Optional[str] = None,
    user_id: Optional[str] = None,
):
    """List stored OAuth tokens."""
    tokens = OAuthManager.list_tokens(service=service, user_id=user_id)
    return {"tokens": tokens}


@router.delete("/tokens/{token_id}")
async def delete_oauth_token(token_id: str):
    """Delete an OAuth token."""
    success = OAuthManager.delete_token(token_id)
    if not success:
        raise HTTPException(status_code=404, detail="Token not found")
    return {"success": True, "message": "Token deleted"}

