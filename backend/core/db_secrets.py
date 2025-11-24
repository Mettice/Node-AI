"""
Database operations for secrets vault.

This module provides CRUD operations for user secrets using the database.
Falls back to Supabase client if direct database connection is not available.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime

from backend.core.database import get_db_connection, is_database_configured, get_supabase_client, is_supabase_configured, get_user_supabase_client
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
    jwt_token: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Create a new secret in the vault.
    
    Uses direct database connection if available, otherwise falls back to Supabase client.
    
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
    logger.info(f"Creating secret for user {user_id}, provider {provider}, type {secret_type}")
    
    # Encrypt the secret
    try:
        encrypted_value = encrypt_secret(user_id, secret_value)
        logger.debug(f"Successfully encrypted secret for user {user_id}")
    except Exception as e:
        logger.error(f"Failed to encrypt secret for user {user_id}: {e}")
        raise RuntimeError(f"Failed to encrypt secret: {str(e)}")
    
    # Try Supabase client first (more reliable for production)
    # Use service role client first since it's more reliable
    supabase = None
    if is_supabase_configured():
        supabase = get_supabase_client()
        if supabase:
            logger.debug(f"Using service role Supabase client for user {user_id}")
        else:
            logger.error("Supabase client is None even though it's configured")
    else:
        logger.error(f"Supabase not configured: url={is_supabase_configured()}")
    
    # Try user-authenticated client if service role fails
    if not supabase and jwt_token and is_supabase_configured():
        supabase = get_user_supabase_client(jwt_token)
        if supabase:
            logger.debug(f"Using user-authenticated Supabase client for user {user_id}")
    
    if supabase:
        try:
            logger.debug(f"Using Supabase client to create secret for user {user_id}")
            
            # Prepare data for Supabase
            secret_data = {
                "user_id": user_id,
                "name": name,
                "provider": provider,
                "secret_type": secret_type,
                "encrypted_value": encrypted_value,
                "description": description,
                "tags": tags or [],
                "encryption_key_id": "v1",
            }
            if expires_at:
                secret_data["expires_at"] = expires_at.isoformat()
            
            logger.debug(f"Supabase insert data (masked): {dict(secret_data, encrypted_value='***')}")
            
            # Use upsert (insert or update on conflict)
            result = supabase.table("secrets_vault").upsert(
                secret_data,
                on_conflict="user_id,provider,secret_type"
            ).execute()
            
            logger.debug(f"Supabase response: {result}")
            
            if result.data and len(result.data) > 0:
                secret = result.data[0]
                logger.info(f"Successfully created secret {secret['id']} for user {user_id}")
                return {
                    "id": str(secret["id"]),
                    "user_id": str(secret["user_id"]),
                    "name": secret["name"],
                    "provider": secret["provider"],
                    "secret_type": secret["secret_type"],
                    "description": secret.get("description"),
                    "tags": secret.get("tags", []),
                    "is_active": secret.get("is_active", True),
                    "last_used_at": secret.get("last_used_at"),
                    "usage_count": secret.get("usage_count", 0),
                    "expires_at": secret.get("expires_at"),
                    "created_at": secret.get("created_at"),
                    "updated_at": secret.get("updated_at"),
                }
            else:
                raise RuntimeError("Supabase returned empty result")
                
        except Exception as e:
            logger.error(f"Failed to create secret via Supabase: {e}")
            # Don't give up yet, try direct DB connection
    
    # Try direct database connection as backup
    if is_database_configured():
        try:
            logger.debug(f"Using direct database connection to create secret for user {user_id}")
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
                    
                    if row:
                        logger.info(f"Successfully created secret {row[0]} for user {user_id} via direct DB")
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
                    else:
                        raise RuntimeError("Direct DB insert returned no rows")
                        
        except Exception as e:
            logger.error(f"Direct database connection also failed: {e}")
    
    # Both methods failed
    error_msg = "Database connection failed. "
    if not is_supabase_configured():
        error_msg += "Supabase not configured (missing SUPABASE_URL or SUPABASE_ANON_KEY). "
    if not is_database_configured():
        error_msg += "Direct database connection not configured (missing valid DATABASE_URL). "
    
    error_msg += "Please check your database configuration."
    logger.error(error_msg)
    raise RuntimeError(error_msg)


def get_secret(secret_id: str, user_id: str, decrypt: bool = False, jwt_token: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Get a secret by ID.
    
    Uses direct database connection if available, otherwise falls back to Supabase client.
    
    Args:
        secret_id: Secret ID
        user_id: User ID (for access control)
        decrypt: Whether to decrypt the secret value
        jwt_token: Optional JWT token for user-authenticated Supabase client
        
    Returns:
        Secret dictionary (with decrypted value if decrypt=True)
    """
    # Try direct database connection first
    if is_database_configured():
        try:
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
                    if row:
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
        except Exception as e:
            logger.warning(f"Direct database connection failed for get_secret, falling back to Supabase client: {e}")
    
    # Fall back to Supabase client
    supabase = get_supabase_client()
    if supabase:
        try:
            logger.debug(f"Using Supabase client to get secret {secret_id} for user {user_id}")
            
            response = supabase.table("secrets_vault").select("*").eq("id", secret_id).eq("user_id", user_id).execute()
            
            if response.data and len(response.data) > 0:
                secret_data = response.data[0]
                result = {
                    "id": secret_data["id"],
                    "user_id": secret_data["user_id"],
                    "name": secret_data["name"],
                    "provider": secret_data["provider"],
                    "secret_type": secret_data["secret_type"],
                    "description": secret_data.get("description"),
                    "tags": secret_data.get("tags", []),
                    "is_active": secret_data.get("is_active", True),
                    "last_used_at": secret_data.get("last_used_at"),
                    "usage_count": secret_data.get("usage_count", 0),
                    "expires_at": secret_data.get("expires_at"),
                    "created_at": secret_data.get("created_at"),
                    "updated_at": secret_data.get("updated_at"),
                }
                
                # Decrypt if requested
                if decrypt:
                    try:
                        encrypted_value = secret_data.get("encrypted_value")
                        if encrypted_value:
                            result["value"] = decrypt_secret(user_id, encrypted_value)
                        else:
                            result["value"] = None
                    except Exception as e:
                        logger.error(f"Failed to decrypt secret {secret_id}: {e}")
                        result["value"] = None
                
                return result
        except Exception as e:
            logger.error(f"Failed to get secret via Supabase client: {e}")
            return None
    
    logger.warning(f"Neither direct database connection nor Supabase client available for get_secret")
    return None


def list_secrets(
    user_id: str,
    provider: Optional[str] = None,
    secret_type: Optional[str] = None,
    is_active: Optional[bool] = None,
    jwt_token: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    List all secrets for a user.
    
    Uses direct database connection if available, otherwise falls back to Supabase client.
    
    Args:
        user_id: User ID
        provider: Optional provider filter
        secret_type: Optional type filter
        is_active: Optional active status filter
        jwt_token: Optional JWT token for user-authenticated Supabase client
        
    Returns:
        List of secret dictionaries (without decrypted values)
    """
    # Try direct database connection first
    if is_database_configured():
        try:
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

