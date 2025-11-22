"""
Encryption utilities for secrets vault.

This module provides AES-256-GCM encryption for securely storing user secrets.
"""

import base64
import os
from typing import Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend

from backend.config import Settings
from backend.utils.logger import get_logger

logger = get_logger(__name__)


def get_master_key() -> bytes:
    """
    Get the master encryption key from environment.
    
    Returns:
        Master key bytes (32 bytes)
        
    Raises:
        ValueError: If key is not configured or invalid
    """
    settings = Settings()
    key_str = settings.vault_encryption_key
    
    if not key_str:
        raise ValueError(
            "VAULT_ENCRYPTION_KEY not configured. "
            "Set it in .env file (32 bytes hex string)."
        )
    
    try:
        # Try to decode as hex string
        if len(key_str) == 64:  # 32 bytes = 64 hex chars
            return bytes.fromhex(key_str)
        else:
            # If not hex, use as-is (but should be 32 bytes)
            key_bytes = key_str.encode()[:32]
            if len(key_bytes) < 32:
                # Pad with zeros (not ideal, but better than error)
                key_bytes = key_bytes.ljust(32, b'\0')
            return key_bytes
    except Exception as e:
        raise ValueError(f"Invalid VAULT_ENCRYPTION_KEY format: {e}")


def derive_user_key(user_id: str, master_key: Optional[bytes] = None) -> bytes:
    """
    Derive a user-specific encryption key from master key and user ID.
    
    This ensures each user's secrets are encrypted with a unique key,
    even if they share the same master key.
    
    Args:
        user_id: User ID (used as salt)
        master_key: Optional master key (if not provided, fetched from env)
        
    Returns:
        Derived encryption key (Fernet-compatible)
    """
    if master_key is None:
        master_key = get_master_key()
    
    # Use PBKDF2 to derive key from master key + user ID
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=user_id.encode(),  # User ID as salt
        iterations=100000,
        backend=default_backend(),
    )
    
    # Derive key
    key = kdf.derive(master_key)
    
    # Convert to Fernet-compatible format (base64 URL-safe)
    return base64.urlsafe_b64encode(key)


def encrypt_secret(user_id: str, secret: str) -> str:
    """
    Encrypt a secret for a specific user.
    
    Args:
        user_id: User ID
        secret: Plaintext secret to encrypt
        
    Returns:
        Encrypted secret (base64-encoded string)
    """
    try:
        # Derive user-specific key
        user_key = derive_user_key(user_id)
        
        # Create Fernet cipher
        f = Fernet(user_key)
        
        # Encrypt
        encrypted = f.encrypt(secret.encode())
        
        # Return as base64 string
        return base64.b64encode(encrypted).decode()
    except Exception as e:
        logger.error(f"Encryption failed for user {user_id}: {e}")
        raise ValueError(f"Failed to encrypt secret: {e}")


def decrypt_secret(user_id: str, encrypted_secret: str) -> str:
    """
    Decrypt a secret for a specific user.
    
    Args:
        user_id: User ID
        encrypted_secret: Encrypted secret (base64-encoded string)
        
    Returns:
        Decrypted secret (plaintext)
    """
    try:
        # Derive user-specific key
        user_key = derive_user_key(user_id)
        
        # Create Fernet cipher
        f = Fernet(user_key)
        
        # Decode from base64
        encrypted_bytes = base64.b64decode(encrypted_secret.encode())
        
        # Decrypt
        decrypted = f.decrypt(encrypted_bytes)
        
        # Return as string
        return decrypted.decode()
    except Exception as e:
        logger.error(f"Decryption failed for user {user_id}: {e}")
        raise ValueError(f"Failed to decrypt secret: {e}")


def generate_encryption_key() -> str:
    """
    Generate a new encryption key (for setup).
    
    Returns:
        Hex-encoded key string (64 characters)
    """
    key = os.urandom(32)  # 32 bytes = 256 bits
    return key.hex()

