"""
MCP Server Manager - Manages MCP server configurations and connections.

Provides:
- Configuration storage for MCP servers (database for production, JSON for local)
- Connection lifecycle management
- Popular server presets (Slack, Gmail, etc.)
- Per-user multi-tenant support
"""

import json
import os
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, asdict
from pathlib import Path

from backend.core.mcp.client import (
    MCPClient,
    MCPServerConfig,
    MCPTransportType,
    get_mcp_client,
)
from backend.core.mcp.tool_registry import get_tool_registry, ToolSource
from backend.core.database import is_database_configured
from backend.utils.logger import get_logger

logger = get_logger(__name__)

# Import database operations (optional, for production)
try:
    from backend.core.db_mcp import (
        create_mcp_server as db_create_mcp_server,
        get_mcp_server as db_get_mcp_server,
        list_mcp_servers as db_list_mcp_servers,
        update_mcp_server as db_update_mcp_server,
        delete_mcp_server as db_delete_mcp_server,
        get_mcp_server_credentials,
        update_last_connected,
        log_mcp_connection,
    )
    DB_MCP_AVAILABLE = True
except ImportError:
    DB_MCP_AVAILABLE = False
    logger.warning("db_mcp module not available, using JSON file storage only")


# Popular MCP server presets
# Package names verified from npm registry and official MCP documentation
# See: https://github.com/modelcontextprotocol/servers
#
# server_type options:
#   - "npx": npm package, runs via npx (most common)
#   - "executable": custom executable path required
#   - "http": HTTP/SSE server (connect to URL)
#
# auth_type options:
#   - "api_key": Simple API key authentication
#   - "oauth": OAuth flow required (more complex setup)
#   - "none": No authentication needed
#
MCP_SERVER_PRESETS = {
    # ============================================
    # NPX-BASED SERVERS (ready to use)
    # ============================================

    # Communication
    "slack": {
        "name": "slack",
        "display_name": "Slack",
        "description": "Send messages, read channels, manage Slack workspace",
        "package": "@modelcontextprotocol/server-slack",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-slack"],
        "env_vars": ["SLACK_BOT_TOKEN", "SLACK_TEAM_ID"],
        "category": "communication",
        "server_type": "npx",
        "auth_type": "api_key",
        "setup_url": "https://api.slack.com/apps",
        "icon": "slack",
    },

    # Storage & Databases
    "google-drive": {
        "name": "google-drive",
        "display_name": "Google Drive",
        "description": "Read and search files in Google Drive",
        "package": "@modelcontextprotocol/server-gdrive",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-gdrive"],
        "env_vars": ["GDRIVE_CREDENTIALS_PATH"],
        "category": "storage",
        "server_type": "npx",
        "auth_type": "oauth",
        "setup_url": "https://console.cloud.google.com/apis/credentials",
        "icon": "googledrive",
    },
    "filesystem": {
        "name": "filesystem",
        "display_name": "Filesystem",
        "description": "Read and write local files (specify allowed directories)",
        "package": "@modelcontextprotocol/server-filesystem",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-filesystem"],
        "env_vars": ["ALLOWED_DIRECTORIES"],
        "category": "storage",
        "server_type": "npx",
        "auth_type": "none",
    },
    "postgres": {
        "name": "postgres",
        "display_name": "PostgreSQL",
        "description": "Read-only access to PostgreSQL databases",
        "package": "@modelcontextprotocol/server-postgres",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-postgres"],
        "env_vars": ["POSTGRES_CONNECTION_STRING"],
        "category": "database",
        "server_type": "npx",
        "auth_type": "api_key",
        "icon": "postgresql",
    },

    # Productivity
    "notion": {
        "name": "notion",
        "display_name": "Notion",
        "description": "Read and write Notion pages and databases",
        "package": "notion-mcp-server",
        "command": "npx",
        "args": ["-y", "notion-mcp-server"],
        "env_vars": ["NOTION_API_KEY"],
        "category": "productivity",
        "server_type": "npx",
        "auth_type": "api_key",
        "setup_url": "https://www.notion.so/my-integrations",
        "icon": "notion",
    },

    # Development
    "github": {
        "name": "github",
        "display_name": "GitHub",
        "description": "Manage repositories, issues, and pull requests",
        "package": "@modelcontextprotocol/server-github",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-github"],
        "env_vars": ["GITHUB_PERSONAL_ACCESS_TOKEN"],
        "category": "development",
        "server_type": "npx",
        "auth_type": "api_key",
        "setup_url": "https://github.com/settings/tokens",
        "icon": "github",
    },

    # Search & Web
    "brave-search": {
        "name": "brave-search",
        "display_name": "Brave Search",
        "description": "Search the web using Brave Search API",
        "package": "@modelcontextprotocol/server-brave-search",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-brave-search"],
        "env_vars": ["BRAVE_API_KEY"],
        "category": "search",
        "server_type": "npx",
        "auth_type": "api_key",
        "setup_url": "https://brave.com/search/api/",
    },

    # CRM & Business
    "airtable": {
        "name": "airtable",
        "display_name": "Airtable",
        "description": "Read and write Airtable bases",
        "package": "airtable-mcp-server",
        "command": "npx",
        "args": ["-y", "airtable-mcp-server"],
        "env_vars": ["AIRTABLE_API_KEY"],
        "category": "business",
        "server_type": "npx",
        "auth_type": "api_key",
        "setup_url": "https://airtable.com/create/tokens",
        "icon": "airtable",
    },

    # ============================================
    # EXECUTABLE-BASED SERVERS (requires build)
    # ============================================

    "gmail": {
        "name": "gmail",
        "display_name": "Gmail",
        "description": "Search emails, create drafts, manage Gmail (requires Go build)",
        "package": "github.com/kevin-turing/auto-gmail",
        "command": "",  # User must provide executable path
        "args": [],
        "env_vars": ["GMAIL_CLIENT_ID", "GMAIL_CLIENT_SECRET", "OPENAI_API_KEY"],
        "category": "communication",
        "server_type": "executable",
        "auth_type": "oauth",
        "setup_url": "https://console.cloud.google.com/apis/credentials",
        "icon": "gmail",
        "setup_instructions": """
1. Create Google Cloud Project and enable Gmail API
2. Create OAuth2 credentials (Desktop application)
3. Clone and build: git clone https://github.com/kevin-turing/auto-gmail && cd auto-gmail && go build .
4. Set GMAIL_CLIENT_ID and GMAIL_CLIENT_SECRET
5. Provide path to built executable
        """,
    },

    "google-calendar": {
        "name": "google-calendar",
        "display_name": "Google Calendar",
        "description": "Manage calendar events and schedules (requires setup)",
        "package": "mcp-server-google-calendar",
        "command": "",  # User must configure
        "args": [],
        "env_vars": ["GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET"],
        "category": "productivity",
        "server_type": "executable",
        "auth_type": "oauth",
        "setup_url": "https://console.cloud.google.com/apis/credentials",
    },
}


@dataclass
class MCPServerConnection:
    """Represents a configured MCP server connection."""
    name: str
    preset: Optional[str]  # Name of preset if using one
    display_name: str
    description: str
    command: str
    args: List[str]
    env: Dict[str, str]
    enabled: bool = True
    connected: bool = False
    tools_count: int = 0


class MCPServerManager:
    """
    Manages MCP server configurations and connections.

    Supports two storage modes:
    - Database (production): Per-user configurations stored in database
    - JSON file (local dev): Single-user configurations in local file

    Handles:
    - Storing server configurations
    - Connecting/disconnecting servers
    - Syncing tools with the registry
    """

    def __init__(self, config_path: Optional[str] = None, user_id: Optional[str] = None):
        self._config_path = config_path or self._default_config_path()
        self._connections: Dict[str, MCPServerConnection] = {}
        self._client = get_mcp_client()
        self._registry = get_tool_registry()
        self._user_id = user_id  # For database mode
        self._use_database = DB_MCP_AVAILABLE and is_database_configured() and user_id is not None

        if self._use_database:
            logger.info(f"MCPServerManager using database storage for user {user_id}")
            self._load_from_database()
        else:
            logger.info("MCPServerManager using JSON file storage (local mode)")
            self._load_config()

    def _default_config_path(self) -> str:
        """Get the default config file path."""
        # Store in backend/data/mcp_servers.json
        data_dir = Path(__file__).parent.parent.parent / "data"
        data_dir.mkdir(exist_ok=True)
        return str(data_dir / "mcp_servers.json")

    def _load_config(self) -> None:
        """Load server configurations from file (local mode)."""
        if os.path.exists(self._config_path):
            try:
                with open(self._config_path, "r") as f:
                    data = json.load(f)
                    for server_data in data.get("servers", []):
                        conn = MCPServerConnection(**server_data)
                        self._connections[conn.name] = conn
                logger.info(f"Loaded {len(self._connections)} MCP server configurations from file")
            except Exception as e:
                logger.error(f"Failed to load MCP config: {e}")

    def _load_from_database(self) -> None:
        """Load server configurations from database (production mode)."""
        if not self._user_id:
            return

        try:
            servers = db_list_mcp_servers(self._user_id, include_credentials=True)
            for server in servers:
                conn = MCPServerConnection(
                    name=server["name"],
                    preset=server.get("preset"),
                    display_name=server["display_name"],
                    description=server.get("description", ""),
                    command=server["command"],
                    args=server.get("args", []),
                    env=server.get("env", {}),
                    enabled=server.get("enabled", True),
                    connected=False,  # Always start disconnected
                    tools_count=0,
                )
                self._connections[conn.name] = conn
            logger.info(f"Loaded {len(self._connections)} MCP server configurations from database")
        except Exception as e:
            logger.error(f"Failed to load MCP config from database: {e}")

    def _save_config(self) -> None:
        """Save server configurations to file (local mode only)."""
        if self._use_database:
            # Database saves happen in individual operations
            return

        try:
            data = {
                "servers": [asdict(c) for c in self._connections.values()]
            }
            with open(self._config_path, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save MCP config: {e}")

    def get_presets(self) -> Dict[str, Dict[str, Any]]:
        """Get all available MCP server presets."""
        return MCP_SERVER_PRESETS.copy()

    def get_preset(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a specific preset by name."""
        return MCP_SERVER_PRESETS.get(name)

    def add_server_from_preset(
        self,
        preset_name: str,
        env_values: Dict[str, str],
        custom_name: Optional[str] = None,
    ) -> Optional[MCPServerConnection]:
        """
        Add a server using a preset configuration.

        Args:
            preset_name: Name of the preset to use
            env_values: Environment variable values (API keys, etc.)
            custom_name: Optional custom name for this instance

        Returns:
            The created connection, or None if failed
        """
        preset = MCP_SERVER_PRESETS.get(preset_name)
        if not preset:
            logger.error(f"Unknown preset: {preset_name}")
            return None

        # Validate required env vars (skip for executable types where command is user-provided)
        if preset.get("server_type") != "executable":
            for env_var in preset["env_vars"]:
                if env_var not in env_values:
                    logger.error(f"Missing required env var: {env_var}")
                    return None

        name = custom_name or preset_name
        command = preset["command"]
        args = preset["args"]

        # For executable type, use provided command if preset command is empty
        if preset.get("server_type") == "executable" and not command:
            if "_EXECUTABLE_PATH" in env_values:
                command = env_values.pop("_EXECUTABLE_PATH")
            else:
                logger.error("Executable type requires command path")
                return None

        connection = MCPServerConnection(
            name=name,
            preset=preset_name,
            display_name=preset["display_name"],
            description=preset["description"],
            command=command,
            args=args,
            env=env_values,
            enabled=True,
        )

        # Save to database if in database mode
        if self._use_database and self._user_id:
            try:
                db_create_mcp_server(
                    user_id=self._user_id,
                    name=name,
                    display_name=preset["display_name"],
                    command=command,
                    args=args,
                    env_vars=env_values,
                    description=preset["description"],
                    preset=preset_name,
                    server_type=preset.get("server_type", "npx"),
                    category=preset.get("category", "integration"),
                )
            except Exception as e:
                logger.error(f"Failed to save MCP server to database: {e}")
                # Continue anyway - will work for this session

        self._connections[name] = connection
        self._save_config()

        logger.info(f"Added MCP server from preset: {name}")
        return connection

    def add_custom_server(
        self,
        name: str,
        display_name: str,
        description: str,
        command: str,
        args: List[str],
        env: Dict[str, str],
    ) -> MCPServerConnection:
        """Add a custom MCP server configuration."""
        connection = MCPServerConnection(
            name=name,
            preset=None,
            display_name=display_name,
            description=description,
            command=command,
            args=args,
            env=env,
            enabled=True,
        )

        # Save to database if in database mode
        if self._use_database and self._user_id:
            try:
                db_create_mcp_server(
                    user_id=self._user_id,
                    name=name,
                    display_name=display_name,
                    command=command,
                    args=args,
                    env_vars=env,
                    description=description,
                    preset=None,
                    server_type="executable",
                    category="custom",
                )
            except Exception as e:
                logger.error(f"Failed to save custom MCP server to database: {e}")

        self._connections[name] = connection
        self._save_config()

        logger.info(f"Added custom MCP server: {name}")
        return connection

    def remove_server(self, name: str) -> bool:
        """Remove a server configuration."""
        if name in self._connections:
            # Disconnect if connected
            if self._connections[name].connected:
                import asyncio
                asyncio.create_task(self._client.disconnect_server(name))

            # Delete from database if in database mode
            if self._use_database and self._user_id:
                try:
                    db_delete_mcp_server(self._user_id, name)
                except Exception as e:
                    logger.error(f"Failed to delete MCP server from database: {e}")

            del self._connections[name]
            self._save_config()
            logger.info(f"Removed MCP server: {name}")
            return True
        return False

    async def connect_server(self, name: str) -> bool:
        """Connect to a configured server."""
        if name not in self._connections:
            logger.error(f"Unknown server: {name}")
            return False

        conn = self._connections[name]
        if not conn.enabled:
            logger.warning(f"Server {name} is disabled")
            return False

        config = MCPServerConfig(
            name=conn.name,
            command=conn.command,
            args=conn.args,
            env=conn.env,
            transport=MCPTransportType.STDIO,
        )

        try:
            success = await self._client.add_server(config)
        except ValueError as e:
            # Command not found or similar setup error
            logger.error(f"Failed to connect to MCP server {name}: {e}")
            raise RuntimeError(str(e)) from e
        except RuntimeError as e:
            # Process failed to start or initialization error
            logger.error(f"Failed to connect to MCP server {name}: {e}")
            raise RuntimeError(str(e)) from e
        except Exception as e:
            # Unexpected error
            logger.error(f"Unexpected error connecting to MCP server {name}: {e}", exc_info=True)
            raise RuntimeError(f"Connection failed: {str(e)}") from e

        if success:
            conn.connected = True
            # Sync tools to registry
            tools = self._client.get_available_tools()
            conn.tools_count = len([t for t in tools if t.server_name == name])

            # Register tools in the registry
            for tool in tools:
                if tool.server_name == name:
                    self._registry.register_mcp_tool(
                        name=tool.name,
                        description=tool.description,
                        input_schema=tool.input_schema,
                        server_name=tool.server_name,
                        category=self._get_server_category(name),
                    )

            self._save_config()
            logger.info(f"Connected to MCP server {name} with {conn.tools_count} tools")

        return success

    async def disconnect_server(self, name: str) -> bool:
        """Disconnect from a server."""
        if name not in self._connections:
            return False

        await self._client.disconnect_server(name)

        conn = self._connections[name]
        conn.connected = False
        conn.tools_count = 0
        self._save_config()

        logger.info(f"Disconnected from MCP server: {name}")
        return True

    async def connect_all_enabled(self) -> Dict[str, bool]:
        """Connect to all enabled servers."""
        results = {}
        for name, conn in self._connections.items():
            if conn.enabled:
                results[name] = await self.connect_server(name)
        return results

    async def disconnect_all(self) -> None:
        """Disconnect from all servers."""
        await self._client.disconnect_all()
        for conn in self._connections.values():
            conn.connected = False
            conn.tools_count = 0
        self._save_config()

    def _get_server_category(self, name: str) -> str:
        """Get the category for a server."""
        conn = self._connections.get(name)
        if conn and conn.preset:
            preset = MCP_SERVER_PRESETS.get(conn.preset)
            if preset:
                return preset.get("category", "integration")
        return "integration"

    def get_connections(self) -> List[MCPServerConnection]:
        """Get all configured connections."""
        return list(self._connections.values())

    def get_connection(self, name: str) -> Optional[MCPServerConnection]:
        """Get a specific connection."""
        return self._connections.get(name)

    def enable_server(self, name: str) -> bool:
        """Enable a server."""
        if name in self._connections:
            self._connections[name].enabled = True
            self._save_config()
            return True
        return False

    def disable_server(self, name: str) -> bool:
        """Disable a server."""
        if name in self._connections:
            self._connections[name].enabled = False
            self._save_config()
            return True
        return False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "connections": [asdict(c) for c in self._connections.values()],
            "presets": [
                {
                    "name": name,
                    "display_name": preset["display_name"],
                    "description": preset["description"],
                    "category": preset["category"],
                    "env_vars": preset["env_vars"],
                    "server_type": preset.get("server_type", "npx"),
                    "auth_type": preset.get("auth_type", "api_key"),
                    "setup_url": preset.get("setup_url"),
                    "setup_instructions": preset.get("setup_instructions"),
                }
                for name, preset in MCP_SERVER_PRESETS.items()
            ],
        }


# Singleton instances
# Global instance for local development (no user)
_server_manager: Optional[MCPServerManager] = None
# Per-user instances for production (keyed by user_id)
_user_server_managers: Dict[str, MCPServerManager] = {}


def get_server_manager(user_id: Optional[str] = None) -> MCPServerManager:
    """
    Get the server manager instance.

    For local development (no user_id): Returns global singleton
    For production (with user_id): Returns per-user instance

    Args:
        user_id: Optional user ID for multi-tenant mode

    Returns:
        MCPServerManager instance
    """
    global _server_manager, _user_server_managers

    if user_id:
        # Production mode: per-user instance
        if user_id not in _user_server_managers:
            _user_server_managers[user_id] = MCPServerManager(user_id=user_id)
        return _user_server_managers[user_id]
    else:
        # Local development mode: global instance
        if _server_manager is None:
            _server_manager = MCPServerManager()
        return _server_manager


def clear_user_manager(user_id: str) -> None:
    """Clear a user's server manager (e.g., on logout)."""
    global _user_server_managers
    if user_id in _user_server_managers:
        # Disconnect all servers first
        manager = _user_server_managers[user_id]
        import asyncio
        try:
            asyncio.create_task(manager.disconnect_all())
        except RuntimeError:
            # No event loop running
            pass
        del _user_server_managers[user_id]
