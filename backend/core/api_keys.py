"""
API Key Management System

Handles generation, validation, and tracking of API keys for workflow access.
"""

import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from pathlib import Path
import json

from backend.utils.logger import get_logger

logger = get_logger(__name__)

# Storage for API keys (file-based for now, can be migrated to DB later)
API_KEYS_DIR = Path("backend/data/api_keys")
API_KEYS_DIR.mkdir(parents=True, exist_ok=True)


class APIKey:
    """Represents an API key with metadata."""
    
    def __init__(
        self,
        key_id: str,
        key_hash: str,
        workflow_id: Optional[str] = None,
        name: str = "Untitled Key",
        created_at: Optional[datetime] = None,
        last_used_at: Optional[datetime] = None,
        is_active: bool = True,
        rate_limit: Optional[int] = None,  # Requests per hour
        cost_limit: Optional[float] = None,  # Max cost per month
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.key_id = key_id
        self.key_hash = key_hash
        self.workflow_id = workflow_id
        self.name = name
        self.created_at = created_at or datetime.now()
        self.last_used_at = last_used_at
        self.is_active = is_active
        self.rate_limit = rate_limit
        self.cost_limit = cost_limit
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "key_id": self.key_id,
            "key_hash": self.key_hash,
            "workflow_id": self.workflow_id,
            "name": self.name,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None,
            "is_active": self.is_active,
            "rate_limit": self.rate_limit,
            "cost_limit": self.cost_limit,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "APIKey":
        """Create from dictionary."""
        return cls(
            key_id=data["key_id"],
            key_hash=data["key_hash"],
            workflow_id=data.get("workflow_id"),
            name=data.get("name", "Untitled Key"),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None,
            last_used_at=datetime.fromisoformat(data["last_used_at"]) if data.get("last_used_at") else None,
            is_active=data.get("is_active", True),
            rate_limit=data.get("rate_limit"),
            cost_limit=data.get("cost_limit"),
            metadata=data.get("metadata", {}),
        )


def generate_api_key(prefix: str = "nk") -> str:
    """
    Generate a secure API key.
    
    Format: nk_<random_32_char_hex>
    Example: nk_a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6
    
    Args:
        prefix: Prefix for the key (default: "nk" for Nodeflow Key)
        
    Returns:
        API key string
    """
    # Generate 32 bytes of random data (256 bits)
    random_bytes = secrets.token_bytes(32)
    # Convert to hex string (64 characters)
    random_hex = random_bytes.hex()
    # Format as prefix_random
    return f"{prefix}_{random_hex}"


def hash_api_key(api_key: str) -> str:
    """
    Hash an API key for secure storage.
    
    Uses SHA-256 for hashing. We store the hash, not the plain key.
    
    Args:
        api_key: The plain API key
        
    Returns:
        SHA-256 hash of the key
    """
    return hashlib.sha256(api_key.encode()).hexdigest()


def save_api_key(api_key: APIKey) -> None:
    """Save an API key to disk."""
    key_file = API_KEYS_DIR / f"{api_key.key_id}.json"
    with open(key_file, "w", encoding="utf-8") as f:
        json.dump(api_key.to_dict(), f, indent=2, ensure_ascii=False)
    logger.info(f"Saved API key {api_key.key_id}")


def load_api_key(key_id: str) -> Optional[APIKey]:
    """Load an API key by ID."""
    key_file = API_KEYS_DIR / f"{key_id}.json"
    if not key_file.exists():
        return None
    
    try:
        with open(key_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        return APIKey.from_dict(data)
    except Exception as e:
        logger.error(f"Error loading API key {key_id}: {e}")
        return None


def load_all_api_keys() -> list[APIKey]:
    """Load all API keys."""
    keys = []
    for key_file in API_KEYS_DIR.glob("*.json"):
        try:
            with open(key_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            keys.append(APIKey.from_dict(data))
        except Exception as e:
            logger.error(f"Error loading API key from {key_file}: {e}")
    return keys


def find_api_key_by_hash(key_hash: str) -> Optional[APIKey]:
    """Find an API key by its hash."""
    for key_file in API_KEYS_DIR.glob("*.json"):
        try:
            with open(key_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            if data.get("key_hash") == key_hash:
                return APIKey.from_dict(data)
        except Exception as e:
            logger.error(f"Error loading API key from {key_file}: {e}")
    return None


def delete_api_key(key_id: str) -> bool:
    """Delete an API key."""
    key_file = API_KEYS_DIR / f"{key_id}.json"
    if key_file.exists():
        key_file.unlink()
        logger.info(f"Deleted API key {key_id}")
        return True
    return False


def create_api_key(
    workflow_id: Optional[str] = None,
    name: str = "Untitled Key",
    rate_limit: Optional[int] = None,
    cost_limit: Optional[float] = None,
) -> tuple[str, APIKey]:
    """
    Create a new API key.
    
    Args:
        workflow_id: Optional workflow ID to associate with this key
        name: Human-readable name for the key
        rate_limit: Optional rate limit (requests per hour)
        cost_limit: Optional cost limit (dollars per month)
        
    Returns:
        Tuple of (plain_api_key, APIKey object)
        The plain key is only returned once and should be stored securely.
    """
    # Generate key
    plain_key = generate_api_key()
    key_hash = hash_api_key(plain_key)
    
    # Create API key object
    key_id = secrets.token_urlsafe(16)  # Unique ID for the key
    api_key = APIKey(
        key_id=key_id,
        key_hash=key_hash,
        workflow_id=workflow_id,
        name=name,
        rate_limit=rate_limit,
        cost_limit=cost_limit,
    )
    
    # Save to disk
    save_api_key(api_key)
    
    logger.info(f"Created API key {key_id} for workflow {workflow_id}")
    return plain_key, api_key


def validate_api_key(api_key: str) -> Optional[APIKey]:
    """
    Validate an API key.
    
    Args:
        api_key: The plain API key to validate
        
    Returns:
        APIKey object if valid, None otherwise
    """
    key_hash = hash_api_key(api_key)
    stored_key = find_api_key_by_hash(key_hash)
    
    if not stored_key:
        return None
    
    if not stored_key.is_active:
        logger.warning(f"Inactive API key attempted: {stored_key.key_id}")
        return None
    
    # Update last used timestamp
    stored_key.last_used_at = datetime.now()
    save_api_key(stored_key)
    
    return stored_key

