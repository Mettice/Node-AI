"""
Database operations for secrets vault.

This module provides CRUD operations for user secrets using the database.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime

from backend.core.database import get_db_connection, is_database_configured
from backend.core.encryption import encrypt_secret, decrypt_secret
from backend.utils.logger import get_logger

logger = get_logger(__name__)


def create_secret(
    user_id: str,
    name: str,
    provider: str,
    secret_type: str,
    secret_value: str,
    description: Optional[str] = None,
    tags: Optional[List[str]] = None,
    expires_at: Optional[datetime] = None,
) -> Dict[str, Any]:
    """
    Create a new secret in the vault.
    
    Args:
        user_id: User ID
        name: Secret name
        provider: Provider (e.g., 'openai', 'anthropic')
        secret_type: Type (e.g., 'api_key', 'oauth_token')
        secret_value: Plaintext secret value
        description: Optional description
        tags: Optional tags
        expires_at: Optional expiration date
        
    Returns:
        Created secret dictionary (without decrypted value)
    """
    if not is_database_configured():
        raise RuntimeError("Database not configured")
    
    # Encrypt the secret
    encrypted_value = encrypt_secret(user_id, secret_value)
    
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO secrets_vault (
                    user_id, name, provider, secret_type, encrypted_value,
                    description, tags, expires_at, encryption_key_id
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'v1')
                ON CONFLICT (user_id, provider, secret_type) DO UPDATE
                SET name = EXCLUDED.name,
                    encrypted_value = EXCLUDED.encrypted_value,
                    description = EXCLUDED.description,
                    tags = EXCLUDED.tags,
                    expires_at = EXCLUDED.expires_at,
                    updated_at = NOW()
                RETURNING id, user_id, name, provider, secret_type, description,
                          tags, is_active, last_used_at, usage_count,
                          expires_at, created_at, updated_at
                """,
                (
                    user_id, name, provider, secret_type, encrypted_value,
                    description, tags, expires_at
                ),
            )
            row = cur.fetchone()
            
            return {
                "id": str(row[0]),
                "user_id": str(row[1]),
                "name": row[2],
                "provider": row[3],
                "secret_type": row[4],
                "description": row[5],
                "tags": row[6] if row[6] else [],
                "is_active": row[7],
                "last_used_at": row[8].isoformat() if row[8] else None,
                "usage_count": row[9],
                "expires_at": row[10].isoformat() if row[10] else None,
                "created_at": row[11].isoformat() if row[11] else None,
                "updated_at": row[12].isoformat() if row[12] else None,
            }


def get_secret(secret_id: str, user_id: str, decrypt: bool = False) -> Optional[Dict[str, Any]]:
    """
    Get a secret by ID.
    
    Args:
        secret_id: Secret ID
        user_id: User ID (for access control)
        decrypt: Whether to decrypt the secret value
        
    Returns:
        Secret dictionary (with decrypted value if decrypt=True)
    """
    if not is_database_configured():
        return None
    
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, user_id, name, provider, secret_type, encrypted_value,
                       description, tags, is_active, last_used_at, usage_count,
                       expires_at, created_at, updated_at
                FROM secrets_vault
                WHERE id = %s AND user_id = %s
                """,
                (secret_id, user_id),
            )
            
            row = cur.fetchone()
            if not row:
                return None
            
            result = {
                "id": str(row[0]),
                "user_id": str(row[1]),
                "name": row[2],
                "provider": row[3],
                "secret_type": row[4],
                "description": row[6],
                "tags": row[7] if row[7] else [],
                "is_active": row[8],
                "last_used_at": row[9].isoformat() if row[9] else None,
                "usage_count": row[10],
                "expires_at": row[11].isoformat() if row[11] else None,
                "created_at": row[12].isoformat() if row[12] else None,
                "updated_at": row[13].isoformat() if row[13] else None,
            }
            
            # Decrypt if requested
            if decrypt:
                try:
                    encrypted_value = row[5]
                    result["value"] = decrypt_secret(user_id, encrypted_value)
                except Exception as e:
                    logger.error(f"Failed to decrypt secret {secret_id}: {e}")
                    result["value"] = None
            
            return result


def list_secrets(
    user_id: str,
    provider: Optional[str] = None,
    secret_type: Optional[str] = None,
    is_active: Optional[bool] = None,
) -> List[Dict[str, Any]]:
    """
    List all secrets for a user.
    
    Args:
        user_id: User ID
        provider: Optional provider filter
        secret_type: Optional type filter
        is_active: Optional active status filter
        
    Returns:
        List of secret dictionaries (without decrypted values)
    """
    if not is_database_configured():
        return []
    
    query = """
        SELECT id, user_id, name, provider, secret_type, description,
               tags, is_active, last_used_at, usage_count,
               expires_at, created_at, updated_at
        FROM secrets_vault
        WHERE user_id = %s
    """
    params = [user_id]
    
    if provider:
        query += " AND provider = %s"
        params.append(provider)
    
    if secret_type:
        query += " AND secret_type = %s"
        params.append(secret_type)
    
    if is_active is not None:
        query += " AND is_active = %s"
        params.append(is_active)
    
    query += " ORDER BY created_at DESC"
    
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            
            results = []
            for row in cur.fetchall():
                results.append({
                    "id": str(row[0]),
                    "user_id": str(row[1]),
                    "name": row[2],
                    "provider": row[3],
                    "secret_type": row[4],
                    "description": row[5],
                    "tags": row[6] if row[6] else [],
                    "is_active": row[7],
                    "last_used_at": row[8].isoformat() if row[8] else None,
                    "usage_count": row[9],
                    "expires_at": row[10].isoformat() if row[10] else None,
                    "created_at": row[11].isoformat() if row[11] else None,
                    "updated_at": row[12].isoformat() if row[12] else None,
                })
            
            return results


def update_secret(
    secret_id: str,
    user_id: str,
    name: Optional[str] = None,
    secret_value: Optional[str] = None,
    description: Optional[str] = None,
    tags: Optional[List[str]] = None,
    is_active: Optional[bool] = None,
    expires_at: Optional[datetime] = None,
) -> Optional[Dict[str, Any]]:
    """
    Update a secret.
    
    Args:
        secret_id: Secret ID
        user_id: User ID (for access control)
        name: Optional new name
        secret_value: Optional new secret value (will be encrypted)
        description: Optional new description
        tags: Optional new tags
        is_active: Optional active status
        expires_at: Optional expiration date
        
    Returns:
        Updated secret dictionary or None if not found
    """
    if not is_database_configured():
        return None
    
    updates = []
    params = []
    
    if name is not None:
        updates.append("name = %s")
        params.append(name)
    
    if secret_value is not None:
        encrypted_value = encrypt_secret(user_id, secret_value)
        updates.append("encrypted_value = %s")
        params.append(encrypted_value)
    
    if description is not None:
        updates.append("description = %s")
        params.append(description)
    
    if tags is not None:
        updates.append("tags = %s")
        params.append(tags)
    
    if is_active is not None:
        updates.append("is_active = %s")
        params.append(is_active)
    
    if expires_at is not None:
        updates.append("expires_at = %s")
        params.append(expires_at)
    
    if not updates:
        return get_secret(secret_id, user_id)
    
    updates.append("updated_at = NOW()")
    params.extend([secret_id, user_id])
    
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                UPDATE secrets_vault
                SET {', '.join(updates)}
                WHERE id = %s AND user_id = %s
                RETURNING id, user_id, name, provider, secret_type, description,
                          tags, is_active, last_used_at, usage_count,
                          expires_at, created_at, updated_at
                """,
                params,
            )
            
            row = cur.fetchone()
            if not row:
                return None
            
            return {
                "id": str(row[0]),
                "user_id": str(row[1]),
                "name": row[2],
                "provider": row[3],
                "secret_type": row[4],
                "description": row[5],
                "tags": row[6] if row[6] else [],
                "is_active": row[7],
                "last_used_at": row[8].isoformat() if row[8] else None,
                "usage_count": row[9],
                "expires_at": row[10].isoformat() if row[10] else None,
                "created_at": row[11].isoformat() if row[11] else None,
                "updated_at": row[12].isoformat() if row[12] else None,
            }


def delete_secret(secret_id: str, user_id: str) -> bool:
    """
    Delete a secret.
    
    Args:
        secret_id: Secret ID
        user_id: User ID (for access control)
        
    Returns:
        True if deleted, False if not found
    """
    if not is_database_configured():
        return False
    
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                DELETE FROM secrets_vault
                WHERE id = %s AND user_id = %s
                RETURNING id
                """,
                (secret_id, user_id),
            )
            
            return cur.fetchone() is not None


def get_secret_value(secret_id: str, user_id: str) -> Optional[str]:
    """
    Get the decrypted value of a secret (for use in nodes).
    
    Args:
        secret_id: Secret ID
        user_id: User ID
        
    Returns:
        Decrypted secret value or None
    """
    secret = get_secret(secret_id, user_id, decrypt=True)
    if not secret:
        return None
    
    return secret.get("value")


def record_secret_usage(
    secret_id: str,
    user_id: str,
    workflow_id: Optional[str] = None,
    node_id: Optional[str] = None,
) -> None:
    """
    Record that a secret was used.
    
    Args:
        secret_id: Secret ID
        user_id: User ID
        workflow_id: Optional workflow ID
        node_id: Optional node ID
    """
    if not is_database_configured():
        return
    
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # Update usage stats
            cur.execute(
                """
                UPDATE secrets_vault
                SET last_used_at = NOW(),
                    usage_count = usage_count + 1,
                    last_used_in_workflow = %s
                WHERE id = %s AND user_id = %s
                """,
                (workflow_id, secret_id, user_id),
            )
            
            # Log access
            cur.execute(
                """
                INSERT INTO secret_access_log (secret_id, user_id, access_type, workflow_id, node_id)
                VALUES (%s, %s, 'use', %s, %s)
                """,
                (secret_id, user_id, workflow_id, node_id),
            )

