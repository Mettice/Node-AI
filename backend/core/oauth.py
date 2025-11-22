"""
OAuth management system for NodeAI.

This module provides OAuth 2.0 flow management for integrations like Slack, Google Drive, etc.
"""

import secrets
import hashlib
import base64
from typing import Dict, Optional, Any
from datetime import datetime, timedelta
import json

from backend.utils.logger import get_logger

logger = get_logger(__name__)

# In-memory storage for OAuth state and tokens
# In production, this should be stored in a database
_oauth_states: Dict[str, Dict[str, Any]] = {}
_oauth_tokens: Dict[str, Dict[str, Any]] = {}


class OAuthManager:
    """
    OAuth 2.0 flow manager.
    
    Handles OAuth authorization flows, token storage, and refresh.
    """
    
    @staticmethod
    def generate_state(user_id: Optional[str] = None) -> str:
        """
        Generate a secure random state for OAuth flow.
        
        Args:
            user_id: Optional user identifier
            
        Returns:
            Base64-encoded state string
        """
        random_bytes = secrets.token_bytes(32)
        state = base64.urlsafe_b64encode(random_bytes).decode('utf-8').rstrip('=')
        
        # Store state with metadata
        _oauth_states[state] = {
            "created_at": datetime.utcnow(),
            "user_id": user_id,
            "used": False,
        }
        
        return state
    
    @staticmethod
    def validate_state(state: str) -> bool:
        """
        Validate and consume an OAuth state.
        
        Args:
            state: The state string to validate
            
        Returns:
            True if valid and not used, False otherwise
        """
        if state not in _oauth_states:
            return False
        
        state_data = _oauth_states[state]
        
        # Check if already used
        if state_data.get("used", False):
            return False
        
        # Check if expired (10 minutes)
        created_at = state_data.get("created_at")
        if created_at and datetime.utcnow() - created_at > timedelta(minutes=10):
            return False
        
        # Mark as used
        state_data["used"] = True
        
        return True
    
    @staticmethod
    def get_authorization_url(
        service: str,
        client_id: str,
        redirect_uri: str,
        scopes: list,
        user_id: Optional[str] = None,
        additional_params: Optional[Dict[str, str]] = None,
    ) -> Dict[str, str]:
        """
        Generate OAuth authorization URL.
        
        Args:
            service: Service name (e.g., 'slack', 'google')
            client_id: OAuth client ID
            redirect_uri: OAuth redirect URI
            scopes: List of OAuth scopes
            user_id: Optional user identifier
            additional_params: Additional query parameters
            
        Returns:
            Dictionary with 'url' and 'state'
        """
        state = OAuthManager.generate_state(user_id)
        
        # Service-specific OAuth URLs
        oauth_urls = {
            "slack": "https://slack.com/oauth/v2/authorize",
            "google": "https://accounts.google.com/o/oauth2/v2/auth",
            "reddit": "https://www.reddit.com/api/v1/authorize",
        }
        
        if service not in oauth_urls:
            raise ValueError(f"Unsupported OAuth service: {service}")
        
        base_url = oauth_urls[service]
        scope_string = " ".join(scopes) if isinstance(scopes, list) else scopes
        
        params = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "scope": scope_string,
            "state": state,
            "response_type": "code",
        }
        
        # Add service-specific parameters
        if service == "slack":
            params["user_scope"] = scope_string  # Slack uses user_scope for user tokens
        elif service == "google":
            params["access_type"] = "offline"  # Get refresh token
            params["prompt"] = "consent"
        elif service == "reddit":
            params["duration"] = "permanent"  # Permanent token
            params["redirect_uri"] = redirect_uri
        
        # Add additional parameters
        if additional_params:
            params.update(additional_params)
        
        # Build URL
        from urllib.parse import urlencode
        url = f"{base_url}?{urlencode(params)}"
        
        return {
            "url": url,
            "state": state,
        }
    
    @staticmethod
    def store_token(
        service: str,
        user_id: Optional[str],
        access_token: str,
        refresh_token: Optional[str] = None,
        expires_in: Optional[int] = None,
        token_type: str = "Bearer",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Store OAuth token.
        
        Args:
            service: Service name
            user_id: User identifier (or None for global)
            access_token: OAuth access token
            refresh_token: Optional refresh token
            expires_in: Token expiration in seconds
            token_type: Token type (usually 'Bearer')
            metadata: Additional metadata
            
        Returns:
            Token ID
        """
        token_id = f"{service}_{user_id or 'global'}_{secrets.token_hex(8)}"
        
        expires_at = None
        if expires_in:
            expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
        
        _oauth_tokens[token_id] = {
            "service": service,
            "user_id": user_id,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": token_type,
            "expires_at": expires_at,
            "created_at": datetime.utcnow(),
            "metadata": metadata or {},
        }
        
        logger.info(f"Stored OAuth token for {service} (user: {user_id or 'global'})")
        
        return token_id
    
    @staticmethod
    def get_token(token_id: str) -> Optional[Dict[str, Any]]:
        """
        Get stored OAuth token.
        
        Args:
            token_id: Token identifier
            
        Returns:
            Token data or None if not found
        """
        return _oauth_tokens.get(token_id)
    
    @staticmethod
    def get_token_by_service(
        service: str,
        user_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Get token by service and user.
        
        Args:
            service: Service name
            user_id: User identifier (or None for global)
            
        Returns:
            Most recent token for the service/user, or None
        """
        matching_tokens = [
            token for token_id, token in _oauth_tokens.items()
            if token["service"] == service and token.get("user_id") == user_id
        ]
        
        if not matching_tokens:
            return None
        
        # Return most recent token
        return max(matching_tokens, key=lambda t: t.get("created_at", datetime.min))
    
    @staticmethod
    def is_token_valid(token_data: Dict[str, Any]) -> bool:
        """
        Check if token is still valid.
        
        Args:
            token_data: Token data dictionary
            
        Returns:
            True if valid, False if expired
        """
        expires_at = token_data.get("expires_at")
        if not expires_at:
            return True  # No expiration
        
        return datetime.utcnow() < expires_at
    
    @staticmethod
    def delete_token(token_id: str) -> bool:
        """
        Delete a stored token.
        
        Args:
            token_id: Token identifier
            
        Returns:
            True if deleted, False if not found
        """
        if token_id in _oauth_tokens:
            del _oauth_tokens[token_id]
            logger.info(f"Deleted OAuth token: {token_id}")
            return True
        return False
    
    @staticmethod
    def list_tokens(service: Optional[str] = None, user_id: Optional[str] = None) -> list:
        """
        List stored tokens.
        
        Args:
            service: Optional service filter
            user_id: Optional user filter
            
        Returns:
            List of token IDs and metadata
        """
        tokens = []
        for token_id, token_data in _oauth_tokens.items():
            if service and token_data.get("service") != service:
                continue
            if user_id is not None and token_data.get("user_id") != user_id:
                continue
            
            tokens.append({
                "token_id": token_id,
                "service": token_data.get("service"),
                "user_id": token_data.get("user_id"),
                "created_at": token_data.get("created_at").isoformat() if token_data.get("created_at") else None,
                "expires_at": token_data.get("expires_at").isoformat() if token_data.get("expires_at") else None,
                "is_valid": OAuthManager.is_token_valid(token_data),
            })
        
        return tokens

