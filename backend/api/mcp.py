"""
MCP API - Endpoints for managing MCP servers and tools.

Provides:
- List available MCP server presets
- Configure MCP server connections
- Connect/disconnect servers
- List available tools

Supports both:
- Local mode (no auth): Uses JSON file storage
- Production mode (with auth): Uses database storage with per-user isolation
"""

from typing import Any, Dict, List, Optional
import sys
import subprocess
import shutil
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel

from backend.core.mcp.server_manager import get_server_manager, MCP_SERVER_PRESETS
from backend.core.mcp.tool_registry import get_tool_registry
from backend.core.user_context import get_user_context
from backend.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/mcp", tags=["MCP"])


async def get_optional_user_id(request: Request) -> Optional[str]:
    """
    Get user ID if authenticated, None otherwise.

    This allows MCP endpoints to work in both:
    - Local development (no auth, uses JSON file)
    - Production (with auth, uses database)
    """
    context = await get_user_context(request)
    return context["id"] if context else None


# Request/Response Models

class AddServerFromPresetRequest(BaseModel):
    """Request to add a server from a preset."""
    preset_name: str
    env_values: Dict[str, str]
    custom_name: Optional[str] = None


class AddCustomServerRequest(BaseModel):
    """Request to add a custom server."""
    name: str
    display_name: str
    description: str
    command: str
    args: List[str]
    env: Dict[str, str]


class ServerResponse(BaseModel):
    """Response containing server info."""
    name: str
    preset: Optional[str]
    display_name: str
    description: str
    enabled: bool
    connected: bool
    tools_count: int


class PresetResponse(BaseModel):
    """Response containing preset info."""
    name: str
    display_name: str
    description: str
    category: str
    env_vars: List[str]


class ToolResponse(BaseModel):
    """Response containing tool info."""
    name: str
    description: str
    source: str
    server_name: Optional[str]
    node_type: Optional[str]
    category: str


# Endpoints

@router.get("/presets")
async def list_presets() -> Dict[str, Any]:
    """
    List all available MCP server presets.

    Returns presets for popular services like Slack, Gmail, etc.
    """
    presets = []
    for name, preset in MCP_SERVER_PRESETS.items():
        presets.append({
            "name": name,
            "display_name": preset["display_name"],
            "description": preset["description"],
            "category": preset["category"],
            "env_vars": preset["env_vars"],
            "server_type": preset.get("server_type", "npx"),
            "auth_type": preset.get("auth_type", "api_key"),
            "setup_url": preset.get("setup_url"),
            "setup_instructions": preset.get("setup_instructions"),
            "icon": preset.get("icon"),
        })

    return {
        "presets": presets,
        "categories": list(set(p["category"] for p in MCP_SERVER_PRESETS.values())),
    }


@router.get("/servers")
async def list_servers(
    user_id: Optional[str] = Depends(get_optional_user_id),
) -> Dict[str, Any]:
    """
    List all configured MCP servers for the current user.
    """
    manager = get_server_manager(user_id)
    connections = manager.get_connections()

    return {
        "servers": [
            {
                "name": c.name,
                "preset": c.preset,
                "display_name": c.display_name,
                "description": c.description,
                "enabled": c.enabled,
                "connected": c.connected,
                "tools_count": c.tools_count,
            }
            for c in connections
        ]
    }


@router.post("/servers/preset")
async def add_server_from_preset(
    request: AddServerFromPresetRequest,
    user_id: Optional[str] = Depends(get_optional_user_id),
) -> Dict[str, Any]:
    """
    Add a new MCP server from a preset.

    Requires the environment variable values (API keys, etc.) for the preset.
    """
    manager = get_server_manager(user_id)

    connection = manager.add_server_from_preset(
        preset_name=request.preset_name,
        env_values=request.env_values,
        custom_name=request.custom_name,
    )

    if not connection:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to add server from preset: {request.preset_name}",
        )

    return {
        "success": True,
        "server": {
            "name": connection.name,
            "preset": connection.preset,
            "display_name": connection.display_name,
            "enabled": connection.enabled,
        },
        "message": f"Server {connection.name} added. Call /mcp/servers/{connection.name}/connect to connect.",
    }


@router.post("/servers/custom")
async def add_custom_server(
    request: AddCustomServerRequest,
    user_id: Optional[str] = Depends(get_optional_user_id),
) -> Dict[str, Any]:
    """
    Add a custom MCP server.
    """
    manager = get_server_manager(user_id)

    connection = manager.add_custom_server(
        name=request.name,
        display_name=request.display_name,
        description=request.description,
        command=request.command,
        args=request.args,
        env=request.env,
    )

    return {
        "success": True,
        "server": {
            "name": connection.name,
            "display_name": connection.display_name,
            "enabled": connection.enabled,
        },
    }


@router.get("/check-requirements")
async def check_requirements(
    user_id: Optional[str] = Depends(get_optional_user_id),
) -> Dict[str, Any]:
    """
    Check if system requirements for MCP servers are met.

    Returns information about Node.js, Python, and other dependencies.
    """
    requirements = {
        "nodejs": {
            "required": False,
            "installed": False,
            "version": None,
            "path": None,
            "npx_available": False,
        },
        "python": {
            "required": True,
            "installed": True,
            "version": sys.version.split()[0],
            "path": sys.executable,
        },
    }

    # Check for Node.js (required for npm/npx MCP servers)
    node_path = shutil.which("node")
    npx_path = shutil.which("npx")

    if node_path:
        requirements["nodejs"]["installed"] = True
        requirements["nodejs"]["path"] = node_path
        # Try to get version
        try:
            result = subprocess.run(
                ["node", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                requirements["nodejs"]["version"] = result.stdout.strip()
        except:
            pass

    if npx_path:
        requirements["nodejs"]["npx_available"] = True

    # Determine if Node.js is required based on configured servers
    manager = get_server_manager(user_id)
    servers = manager.get_connections()
    nodejs_required = any(
        server.command in ["node", "npx", "npm"]
        for server in servers
        if server.enabled
    )
    requirements["nodejs"]["required"] = nodejs_required

    return {
        "requirements": requirements,
        "ready": all(
            req["installed"] if req.get("required", False) else True
            for req in requirements.values()
        ),
    }


@router.post("/servers/{server_name}/connect")
async def connect_server(
    server_name: str,
    user_id: Optional[str] = Depends(get_optional_user_id),
) -> Dict[str, Any]:
    """
    Connect to an MCP server.

    This starts the server process and loads available tools.
    """
    manager = get_server_manager(user_id)

    if not manager.get_connection(server_name):
        raise HTTPException(status_code=404, detail=f"Server {server_name} not found")

    # Pre-check: Verify Node.js is available if server requires it
    connection = manager.get_connection(server_name)
    if connection and connection.command in ["node", "npx", "npm"]:
        command_path = shutil.which(connection.command)
        if not command_path:
            raise HTTPException(
                status_code=400,
                detail=f"Node.js is required for this MCP server but is not installed. Please install Node.js from https://nodejs.org/ and restart the server.",
            )

    try:
        success = await manager.connect_server(server_name)
    except RuntimeError as e:
        # Re-raise with more specific error message
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Unexpected error connecting to MCP server {server_name}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to connect to server {server_name}: {str(e)}",
        )

    if not success:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to connect to server {server_name}. Check server logs for details.",
        )

    connection = manager.get_connection(server_name)

    return {
        "success": True,
        "server": {
            "name": connection.name,
            "connected": connection.connected,
            "tools_count": connection.tools_count,
        },
    }


@router.post("/servers/{server_name}/disconnect")
async def disconnect_server(
    server_name: str,
    user_id: Optional[str] = Depends(get_optional_user_id),
) -> Dict[str, Any]:
    """
    Disconnect from an MCP server.
    """
    manager = get_server_manager(user_id)

    if not manager.get_connection(server_name):
        raise HTTPException(status_code=404, detail=f"Server {server_name} not found")

    await manager.disconnect_server(server_name)

    return {
        "success": True,
        "message": f"Disconnected from {server_name}",
    }


@router.delete("/servers/{server_name}")
async def remove_server(
    server_name: str,
    user_id: Optional[str] = Depends(get_optional_user_id),
) -> Dict[str, Any]:
    """
    Remove an MCP server configuration.
    """
    manager = get_server_manager(user_id)

    if not manager.remove_server(server_name):
        raise HTTPException(status_code=404, detail=f"Server {server_name} not found")

    return {
        "success": True,
        "message": f"Removed server {server_name}",
    }


@router.post("/servers/{server_name}/enable")
async def enable_server(
    server_name: str,
    user_id: Optional[str] = Depends(get_optional_user_id),
) -> Dict[str, Any]:
    """Enable an MCP server."""
    manager = get_server_manager(user_id)

    if not manager.enable_server(server_name):
        raise HTTPException(status_code=404, detail=f"Server {server_name} not found")

    return {"success": True}


@router.post("/servers/{server_name}/disable")
async def disable_server(
    server_name: str,
    user_id: Optional[str] = Depends(get_optional_user_id),
) -> Dict[str, Any]:
    """Disable an MCP server."""
    manager = get_server_manager(user_id)

    if not manager.disable_server(server_name):
        raise HTTPException(status_code=404, detail=f"Server {server_name} not found")

    return {"success": True}


@router.get("/tools")
async def list_tools(
    category: Optional[str] = None,
    source: Optional[str] = None,
) -> Dict[str, Any]:
    """
    List all available tools.

    Includes both MCP tools (external) and internal NodeAI tools.
    """
    registry = get_tool_registry()
    all_tools = registry.get_all_tools()

    # Filter
    if category:
        all_tools = [t for t in all_tools if t.category == category]
    if source:
        all_tools = [t for t in all_tools if t.source.value == source]

    return {
        "tools": [t.to_dict() for t in all_tools],
        "total": len(all_tools),
        "categories": list(set(t.category for t in registry.get_all_tools())),
    }


@router.get("/tools/{tool_name}")
async def get_tool(tool_name: str) -> Dict[str, Any]:
    """
    Get details for a specific tool.
    """
    registry = get_tool_registry()
    tool = registry.get_tool(tool_name)

    if not tool:
        raise HTTPException(status_code=404, detail=f"Tool {tool_name} not found")

    return {
        "tool": tool.to_dict(),
    }


@router.post("/connect-all")
async def connect_all_enabled(
    user_id: Optional[str] = Depends(get_optional_user_id),
) -> Dict[str, Any]:
    """
    Connect to all enabled MCP servers.

    Useful for initialization on startup.
    """
    manager = get_server_manager(user_id)
    results = await manager.connect_all_enabled()

    return {
        "results": results,
        "connected": sum(1 for v in results.values() if v),
        "failed": sum(1 for v in results.values() if not v),
    }


@router.post("/disconnect-all")
async def disconnect_all(
    user_id: Optional[str] = Depends(get_optional_user_id),
) -> Dict[str, Any]:
    """
    Disconnect from all MCP servers.
    """
    manager = get_server_manager(user_id)
    await manager.disconnect_all()

    return {
        "success": True,
        "message": "Disconnected from all servers",
    }


@router.get("/status")
async def get_status(
    user_id: Optional[str] = Depends(get_optional_user_id),
) -> Dict[str, Any]:
    """
    Get overall MCP status.
    """
    manager = get_server_manager(user_id)
    registry = get_tool_registry()

    connections = manager.get_connections()
    tools = registry.get_all_tools()

    return {
        "servers": {
            "total": len(connections),
            "connected": sum(1 for c in connections if c.connected),
            "enabled": sum(1 for c in connections if c.enabled),
        },
        "tools": {
            "total": len(tools),
            "mcp": len([t for t in tools if t.source.value == "mcp"]),
            "internal": len([t for t in tools if t.source.value == "internal"]),
        },
        "mode": "database" if user_id else "local",
    }
