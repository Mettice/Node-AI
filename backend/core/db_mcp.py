"""
Database operations for MCP server configurations.

This module provides CRUD operations for user-specific MCP server configurations.
Credentials are encrypted before storage for security.
"""

import json
from typing import Optional, List, Dict, Any
from datetime import datetime

from backend.core.database import (
    get_db_connection,
    is_database_configured,
    get_supabase_client,
    is_supabase_configured,
)
from backend.core.encryption import encrypt_secret, decrypt_secret
from backend.utils.logger import get_logger

logger = get_logger(__name__)


def _encrypt_env_vars(user_id: str, env_vars: Dict[str, str]) -> str:
    """Encrypt environment variables for storage."""
    if not env_vars:
        return ""
    env_json = json.dumps(env_vars)
    return encrypt_secret(user_id, env_json)


def _decrypt_env_vars(user_id: str, encrypted: str) -> Dict[str, str]:
    """Decrypt environment variables from storage."""
    if not encrypted:
        return {}
    try:
        decrypted = decrypt_secret(user_id, encrypted)
        return json.loads(decrypted)
    except Exception as e:
        logger.error(f"Failed to decrypt env vars: {e}")
        return {}


def create_mcp_server(
    user_id: str,
    name: str,
    display_name: str,
    command: str,
    args: List[str],
    env_vars: Dict[str, str],
    description: Optional[str] = None,
    preset: Optional[str] = None,
    server_type: str = "npx",
    category: str = "integration",
) -> Dict[str, Any]:
    """
    Create a new MCP server configuration.

    Args:
        user_id: User ID
        name: Server name (unique per user)
        display_name: Human-readable name
        command: Command to run
        args: Command arguments
        env_vars: Environment variables (will be encrypted)
        description: Optional description
        preset: Optional preset name if using a preset
        server_type: Type of server (npx, executable, http)
        category: Category for grouping

    Returns:
        Created server configuration
    """
    logger.info(f"Creating MCP server config '{name}' for user {user_id}")

    # Encrypt environment variables
    encrypted_env = _encrypt_env_vars(user_id, env_vars)

    # Try Supabase first
    supabase = get_supabase_client() if is_supabase_configured() else None

    if supabase:
        try:
            data = {
                "user_id": user_id,
                "name": name,
                "preset": preset,
                "display_name": display_name,
                "description": description,
                "command": command,
                "args": args,
                "env_encrypted": encrypted_env,
                "server_type": server_type,
                "category": category,
                "enabled": True,
            }

            result = supabase.table("mcp_server_configs").upsert(
                data,
                on_conflict="user_id,name"
            ).execute()

            if result.data and len(result.data) > 0:
                server = result.data[0]
                return _format_server_response(server, user_id)

        except Exception as e:
            logger.error(f"Failed to create MCP server via Supabase: {e}")

    # Fallback to direct database
    if is_database_configured():
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO mcp_server_configs (
                            user_id, name, preset, display_name, description,
                            command, args, env_encrypted, server_type, category, enabled
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb, %s, %s, %s, true)
                        ON CONFLICT (user_id, name) DO UPDATE
                        SET preset = EXCLUDED.preset,
                            display_name = EXCLUDED.display_name,
                            description = EXCLUDED.description,
                            command = EXCLUDED.command,
                            args = EXCLUDED.args,
                            env_encrypted = EXCLUDED.env_encrypted,
                            server_type = EXCLUDED.server_type,
                            category = EXCLUDED.category,
                            updated_at = NOW()
                        RETURNING id, user_id, name, preset, display_name, description,
                                  command, args, server_type, category, enabled,
                                  created_at, updated_at, last_connected_at
                        """,
                        (
                            user_id, name, preset, display_name, description,
                            command, json.dumps(args), encrypted_env, server_type, category
                        ),
                    )
                    row = cur.fetchone()
                    if row:
                        return _format_db_row(row, user_id)
        except Exception as e:
            logger.error(f"Failed to create MCP server via direct DB: {e}")

    raise RuntimeError("Database not configured or operation failed")


def get_mcp_server(
    user_id: str,
    server_name: str,
    include_credentials: bool = False,
) -> Optional[Dict[str, Any]]:
    """
    Get a specific MCP server configuration.

    Args:
        user_id: User ID
        server_name: Server name
        include_credentials: Whether to include decrypted credentials

    Returns:
        Server configuration or None
    """
    supabase = get_supabase_client() if is_supabase_configured() else None

    if supabase:
        try:
            result = supabase.table("mcp_server_configs").select("*").eq(
                "user_id", user_id
            ).eq("name", server_name).execute()

            if result.data and len(result.data) > 0:
                return _format_server_response(
                    result.data[0], user_id, include_credentials
                )
        except Exception as e:
            logger.error(f"Failed to get MCP server via Supabase: {e}")

    if is_database_configured():
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT id, user_id, name, preset, display_name, description,
                               command, args, env_encrypted, server_type, category, enabled,
                               created_at, updated_at, last_connected_at
                        FROM mcp_server_configs
                        WHERE user_id = %s AND name = %s
                        """,
                        (user_id, server_name),
                    )
                    row = cur.fetchone()
                    if row:
                        return _format_db_row(row, user_id, include_credentials)
        except Exception as e:
            logger.error(f"Failed to get MCP server via direct DB: {e}")

    return None


def list_mcp_servers(
    user_id: str,
    include_credentials: bool = False,
    enabled_only: bool = False,
) -> List[Dict[str, Any]]:
    """
    List all MCP server configurations for a user.

    Args:
        user_id: User ID
        include_credentials: Whether to include decrypted credentials
        enabled_only: Only return enabled servers

    Returns:
        List of server configurations
    """
    supabase = get_supabase_client() if is_supabase_configured() else None

    if supabase:
        try:
            query = supabase.table("mcp_server_configs").select("*").eq("user_id", user_id)
            if enabled_only:
                query = query.eq("enabled", True)
            query = query.order("created_at", desc=True)

            result = query.execute()

            if result.data:
                return [
                    _format_server_response(s, user_id, include_credentials)
                    for s in result.data
                ]
            return []
        except Exception as e:
            logger.error(f"Failed to list MCP servers via Supabase: {e}")

    if is_database_configured():
        try:
            query = """
                SELECT id, user_id, name, preset, display_name, description,
                       command, args, env_encrypted, server_type, category, enabled,
                       created_at, updated_at, last_connected_at
                FROM mcp_server_configs
                WHERE user_id = %s
            """
            params = [user_id]

            if enabled_only:
                query += " AND enabled = true"

            query += " ORDER BY created_at DESC"

            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query, params)
                    return [
                        _format_db_row(row, user_id, include_credentials)
                        for row in cur.fetchall()
                    ]
        except Exception as e:
            logger.error(f"Failed to list MCP servers via direct DB: {e}")

    return []


def update_mcp_server(
    user_id: str,
    server_name: str,
    display_name: Optional[str] = None,
    description: Optional[str] = None,
    command: Optional[str] = None,
    args: Optional[List[str]] = None,
    env_vars: Optional[Dict[str, str]] = None,
    enabled: Optional[bool] = None,
) -> Optional[Dict[str, Any]]:
    """
    Update an MCP server configuration.

    Args:
        user_id: User ID
        server_name: Server name
        display_name: New display name
        description: New description
        command: New command
        args: New arguments
        env_vars: New environment variables (will be encrypted)
        enabled: New enabled status

    Returns:
        Updated server configuration or None
    """
    updates = {}

    if display_name is not None:
        updates["display_name"] = display_name
    if description is not None:
        updates["description"] = description
    if command is not None:
        updates["command"] = command
    if args is not None:
        updates["args"] = args
    if env_vars is not None:
        updates["env_encrypted"] = _encrypt_env_vars(user_id, env_vars)
    if enabled is not None:
        updates["enabled"] = enabled

    if not updates:
        return get_mcp_server(user_id, server_name)

    supabase = get_supabase_client() if is_supabase_configured() else None

    if supabase:
        try:
            result = supabase.table("mcp_server_configs").update(updates).eq(
                "user_id", user_id
            ).eq("name", server_name).execute()

            if result.data and len(result.data) > 0:
                return _format_server_response(result.data[0], user_id)
        except Exception as e:
            logger.error(f"Failed to update MCP server via Supabase: {e}")

    if is_database_configured():
        try:
            set_clauses = []
            params = []

            for key, value in updates.items():
                if key == "args":
                    set_clauses.append(f"{key} = %s::jsonb")
                    params.append(json.dumps(value))
                else:
                    set_clauses.append(f"{key} = %s")
                    params.append(value)

            params.extend([user_id, server_name])

            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        f"""
                        UPDATE mcp_server_configs
                        SET {', '.join(set_clauses)}, updated_at = NOW()
                        WHERE user_id = %s AND name = %s
                        RETURNING id, user_id, name, preset, display_name, description,
                                  command, args, server_type, category, enabled,
                                  created_at, updated_at, last_connected_at
                        """,
                        params,
                    )
                    row = cur.fetchone()
                    if row:
                        return _format_db_row(row, user_id)
        except Exception as e:
            logger.error(f"Failed to update MCP server via direct DB: {e}")

    return None


def delete_mcp_server(user_id: str, server_name: str) -> bool:
    """
    Delete an MCP server configuration.

    Args:
        user_id: User ID
        server_name: Server name

    Returns:
        True if deleted, False otherwise
    """
    supabase = get_supabase_client() if is_supabase_configured() else None

    if supabase:
        try:
            result = supabase.table("mcp_server_configs").delete().eq(
                "user_id", user_id
            ).eq("name", server_name).execute()

            return result.data is not None and len(result.data) > 0
        except Exception as e:
            logger.error(f"Failed to delete MCP server via Supabase: {e}")

    if is_database_configured():
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        DELETE FROM mcp_server_configs
                        WHERE user_id = %s AND name = %s
                        RETURNING id
                        """,
                        (user_id, server_name),
                    )
                    return cur.fetchone() is not None
        except Exception as e:
            logger.error(f"Failed to delete MCP server via direct DB: {e}")

    return False


def log_mcp_connection(
    user_id: str,
    server_config_id: str,
    action: str,
    status: str,
    error_message: Optional[str] = None,
    tools_count: Optional[int] = None,
) -> None:
    """
    Log an MCP connection event.

    Args:
        user_id: User ID
        server_config_id: Server config ID
        action: Action type (connect, disconnect, error)
        status: Status (success, failure)
        error_message: Optional error message
        tools_count: Optional tools count
    """
    supabase = get_supabase_client() if is_supabase_configured() else None

    if supabase:
        try:
            supabase.table("mcp_connection_log").insert({
                "user_id": user_id,
                "server_config_id": server_config_id,
                "action": action,
                "status": status,
                "error_message": error_message,
                "tools_count": tools_count,
            }).execute()
            return
        except Exception as e:
            logger.error(f"Failed to log MCP connection via Supabase: {e}")

    if is_database_configured():
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO mcp_connection_log
                        (user_id, server_config_id, action, status, error_message, tools_count)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        """,
                        (user_id, server_config_id, action, status, error_message, tools_count),
                    )
        except Exception as e:
            logger.error(f"Failed to log MCP connection via direct DB: {e}")


def update_last_connected(user_id: str, server_name: str) -> None:
    """Update the last_connected_at timestamp for a server."""
    supabase = get_supabase_client() if is_supabase_configured() else None

    if supabase:
        try:
            supabase.table("mcp_server_configs").update({
                "last_connected_at": datetime.utcnow().isoformat()
            }).eq("user_id", user_id).eq("name", server_name).execute()
            return
        except Exception as e:
            logger.error(f"Failed to update last_connected via Supabase: {e}")

    if is_database_configured():
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        UPDATE mcp_server_configs
                        SET last_connected_at = NOW()
                        WHERE user_id = %s AND name = %s
                        """,
                        (user_id, server_name),
                    )
        except Exception as e:
            logger.error(f"Failed to update last_connected via direct DB: {e}")


def get_mcp_server_credentials(user_id: str, server_name: str) -> Dict[str, str]:
    """
    Get decrypted credentials for an MCP server.

    This is used when connecting to the server.

    Args:
        user_id: User ID
        server_name: Server name

    Returns:
        Decrypted environment variables
    """
    server = get_mcp_server(user_id, server_name, include_credentials=True)
    if server:
        return server.get("env", {})
    return {}


def _format_server_response(
    data: Dict[str, Any],
    user_id: str,
    include_credentials: bool = False,
) -> Dict[str, Any]:
    """Format Supabase response to standard format."""
    result = {
        "id": data.get("id"),
        "user_id": data.get("user_id"),
        "name": data.get("name"),
        "preset": data.get("preset"),
        "display_name": data.get("display_name"),
        "description": data.get("description"),
        "command": data.get("command"),
        "args": data.get("args", []),
        "server_type": data.get("server_type", "npx"),
        "category": data.get("category", "integration"),
        "enabled": data.get("enabled", True),
        "created_at": data.get("created_at"),
        "updated_at": data.get("updated_at"),
        "last_connected_at": data.get("last_connected_at"),
    }

    if include_credentials:
        encrypted = data.get("env_encrypted", "")
        result["env"] = _decrypt_env_vars(user_id, encrypted)

    return result


def _format_db_row(
    row: tuple,
    user_id: str,
    include_credentials: bool = False,
) -> Dict[str, Any]:
    """Format database row to standard format."""
    result = {
        "id": str(row[0]),
        "user_id": str(row[1]),
        "name": row[2],
        "preset": row[3],
        "display_name": row[4],
        "description": row[5],
        "command": row[6],
        "args": row[7] if isinstance(row[7], list) else json.loads(row[7] or "[]"),
        "server_type": row[9] if len(row) > 9 else "npx",
        "category": row[10] if len(row) > 10 else "integration",
        "enabled": row[11] if len(row) > 11 else True,
        "created_at": row[12].isoformat() if len(row) > 12 and row[12] else None,
        "updated_at": row[13].isoformat() if len(row) > 13 and row[13] else None,
        "last_connected_at": row[14].isoformat() if len(row) > 14 and row[14] else None,
    }

    if include_credentials:
        encrypted = row[8] if len(row) > 8 else ""
        result["env"] = _decrypt_env_vars(user_id, encrypted)

    return result
