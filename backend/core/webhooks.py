"""
Webhook management and execution.

Webhooks allow external systems to trigger workflows via HTTP POST requests.
"""

import uuid
import hmac
import hashlib
from datetime import datetime
from typing import Any, Dict, List, Optional
from pathlib import Path
import json

from pydantic import BaseModel, Field

from backend.utils.logger import get_logger

logger = get_logger(__name__)

# Storage directory for webhooks
WEBHOOKS_DIR = Path("backend/data/webhooks")
WEBHOOKS_DIR.mkdir(parents=True, exist_ok=True)


class Webhook(BaseModel):
    """Webhook model."""
    id: str = Field(description="Webhook ID")
    workflow_id: str = Field(description="Workflow ID this webhook triggers")
    name: Optional[str] = Field(default=None, description="Webhook name")
    webhook_id: str = Field(description="Unique webhook identifier (used in URL)")
    secret: Optional[str] = Field(default=None, description="Secret for signature verification")
    enabled: bool = Field(default=True, description="Whether webhook is enabled")
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")
    
    # Configuration
    method: str = Field(default="POST", description="HTTP method (POST, GET)")
    headers_required: Dict[str, str] = Field(default_factory=dict, description="Required headers")
    payload_mapping: Dict[str, str] = Field(
        default_factory=dict,
        description="Map webhook payload fields to workflow input fields"
    )
    
    # Statistics
    total_calls: int = Field(default=0, description="Total number of calls")
    successful_calls: int = Field(default=0, description="Successful executions")
    failed_calls: int = Field(default=0, description="Failed executions")
    last_called_at: Optional[datetime] = Field(default=None, description="Last call timestamp")


def get_webhook_path(webhook_id: str) -> Path:
    """Get file path for a webhook."""
    return WEBHOOKS_DIR / f"{webhook_id}.json"


def save_webhook(webhook: Webhook) -> None:
    """Save webhook to disk."""
    webhook_path = get_webhook_path(webhook.id)
    webhook_dict = webhook.model_dump(mode="json")
    
    # Convert datetime to ISO format
    if isinstance(webhook_dict.get("created_at"), datetime):
        webhook_dict["created_at"] = webhook.created_at.isoformat()
    if isinstance(webhook_dict.get("updated_at"), datetime):
        webhook_dict["updated_at"] = webhook.updated_at.isoformat()
    if isinstance(webhook_dict.get("last_called_at"), datetime):
        webhook_dict["last_called_at"] = webhook.last_called_at.isoformat()
    elif webhook_dict.get("last_called_at") is None:
        webhook_dict["last_called_at"] = None
    
    with open(webhook_path, "w", encoding="utf-8") as f:
        json.dump(webhook_dict, f, indent=2, ensure_ascii=False)


def load_webhook(webhook_id: str) -> Optional[Webhook]:
    """Load webhook from disk."""
    webhook_path = get_webhook_path(webhook_id)
    if not webhook_path.exists():
        return None
    
    try:
        with open(webhook_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # Parse datetime strings
        if "created_at" in data and isinstance(data["created_at"], str):
            data["created_at"] = datetime.fromisoformat(data["created_at"].replace("Z", "+00:00"))
        if "updated_at" in data and isinstance(data["updated_at"], str):
            data["updated_at"] = datetime.fromisoformat(data["updated_at"].replace("Z", "+00:00"))
        if "last_called_at" in data and data["last_called_at"]:
            if isinstance(data["last_called_at"], str):
                data["last_called_at"] = datetime.fromisoformat(data["last_called_at"].replace("Z", "+00:00"))
        
        return Webhook(**data)
    except Exception as e:
        logger.error(f"Error loading webhook {webhook_id}: {e}")
        return None


def list_webhooks(workflow_id: Optional[str] = None) -> List[Webhook]:
    """List all webhooks, optionally filtered by workflow."""
    webhooks = []
    for webhook_file in WEBHOOKS_DIR.glob("*.json"):
        try:
            webhook_id = webhook_file.stem
            webhook = load_webhook(webhook_id)
            if webhook:
                if workflow_id is None or webhook.workflow_id == workflow_id:
                    webhooks.append(webhook)
        except Exception as e:
            logger.warning(f"Error loading webhook from {webhook_file}: {e}")
    return webhooks


def delete_webhook(webhook_id: str) -> bool:
    """Delete a webhook."""
    webhook_path = get_webhook_path(webhook_id)
    if webhook_path.exists():
        webhook_path.unlink()
        return True
    return False


def generate_webhook_id() -> str:
    """Generate a unique webhook ID for URL."""
    return f"wh_{uuid.uuid4().hex[:16]}"


def generate_webhook_secret() -> str:
    """Generate a secret for webhook signature verification."""
    return uuid.uuid4().hex


def verify_webhook_signature(
    payload: bytes,
    signature: str,
    secret: str,
) -> bool:
    """
    Verify webhook signature (HMAC SHA256).
    
    Common format: sha256=hex(hmac_sha256(secret, payload))
    """
    if not secret or not signature:
        return False
    
    try:
        # Handle different signature formats
        if signature.startswith("sha256="):
            signature = signature[7:]
        
        # Calculate expected signature
        expected_signature = hmac.new(
            secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        # Constant-time comparison
        return hmac.compare_digest(expected_signature, signature)
    except Exception as e:
        logger.error(f"Error verifying webhook signature: {e}")
        return False


def map_payload_to_workflow_input(
    payload: Dict[str, Any],
    mapping: Dict[str, str],
) -> Dict[str, Any]:
    """
    Map webhook payload to workflow input using mapping configuration.
    
    Example mapping:
    {
        "query": "body.question",  # Extract from payload.body.question
        "file_id": "body.file_id"
    }
    
    If no mapping, returns payload as-is.
    """
    if not mapping:
        return payload
    
    workflow_input = {}
    
    for workflow_key, payload_path in mapping.items():
        try:
            # Navigate nested paths (e.g., "body.question")
            value = payload
            for part in payload_path.split("."):
                if isinstance(value, dict) and part in value:
                    value = value[part]
                else:
                    value = None
                    break
            
            if value is not None:
                workflow_input[workflow_key] = value
        except Exception as e:
            logger.warning(f"Error mapping {payload_path} to {workflow_key}: {e}")
    
    return workflow_input

