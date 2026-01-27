"""
MCP (Model Context Protocol) Integration Module.

This module provides MCP client capabilities for NodeAI agents,
allowing them to use external tools via the MCP protocol.

MCP enables agents to:
- Read/write to external services (Airtable, Google Drive, etc.)
- Execute actions (send emails, post to Slack, etc.)
- Access any MCP-compatible tool server

This replaces the need to build individual integration nodes.
"""

from backend.core.mcp.client import MCPClient
from backend.core.mcp.tool_registry import MCPToolRegistry, MCPTool
from backend.core.mcp.server_manager import MCPServerManager

__all__ = [
    "MCPClient",
    "MCPToolRegistry",
    "MCPTool",
    "MCPServerManager",
]
