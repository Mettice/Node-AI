"""
MCP Tool Node for NodeAI.

Calls a tool on a configured MCP server from inside a workflow. Until now MCP tools were
only reachable by CrewAI agents; this makes them available on the canvas like any other node.
"""

import json
from typing import Any, Dict, List, Optional

from backend.core.models import NodeMetadata
from backend.core.node_registry import NodeRegistry
from backend.nodes.base import BaseNode
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class MCPToolNode(BaseNode):
    """
    MCP Tool Node.

    Runs one tool on an MCP server (remote or local) and returns its output.
    """

    node_type = "mcp_tool"
    name = "MCP Tool"
    description = "Call a tool on a connected MCP server (Slack, GitHub, Stripe, or any custom server)."
    category = "tool"

    async def execute(
        self,
        inputs: Dict[str, Any],
        config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Call the configured MCP tool and return its result."""
        from backend.core.mcp.client import get_mcp_client
        from backend.core.mcp.server_manager import get_server_manager

        node_id = config.get("_node_id", "mcp_tool")
        server_name = config.get("server")
        tool_name = config.get("tool")

        if not server_name:
            raise ValueError("No MCP server selected. Choose one in the node settings.")
        if not tool_name:
            raise ValueError("No MCP tool selected. Choose one in the node settings.")

        await self.stream_progress(node_id, 0.1, f"Preparing {tool_name}...")

        manager = get_server_manager(config.get("_user_id"))
        connection = next((c for c in manager.get_connections() if c.name == server_name), None)
        if connection is None:
            raise ValueError(
                f"MCP server '{server_name}' is not configured. Add it under Settings > MCP."
            )

        # Connect on demand: connections do not survive a restart
        if not connection.connected:
            await self.stream_progress(node_id, 0.3, f"Connecting to {connection.display_name}...")
            try:
                await manager.connect_server(server_name)
            except RuntimeError as e:
                raise ValueError(f"Could not connect to MCP server '{server_name}': {e}") from e

        arguments = self._build_arguments(config, inputs)

        await self.stream_progress(node_id, 0.6, f"Calling {tool_name}...")
        result = await get_mcp_client().call_tool(tool_name, arguments)

        if isinstance(result, dict) and "error" in result:
            raise ValueError(f"MCP tool '{tool_name}' failed: {result['error']}")

        text = self._extract_text(result)
        await self.stream_output(node_id, text, partial=False)
        await self.stream_progress(node_id, 1.0, "Done")

        return {
            "text": text,
            "result": result,
            "server": server_name,
            "tool": tool_name,
            "arguments": arguments,
        }

    def _build_arguments(self, config: Dict[str, Any], inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Tool arguments from the node's JSON, with {placeholders} filled from the node's inputs.

        A plain string input is available as {input}, so a search tool can take the text
        coming from the previous node.
        """
        raw = config.get("arguments") or {}
        if isinstance(raw, str):
            raw = raw.strip()
            if not raw:
                return {}
            try:
                raw = json.loads(raw)
            except json.JSONDecodeError as e:
                raise ValueError(f"Arguments must be valid JSON: {e}") from e
        if not isinstance(raw, dict):
            raise ValueError("Arguments must be a JSON object")

        values = dict(inputs)
        if "input" not in values:
            # "response" covers a chat node upstream, "content" the engine's merged text
            for key in ("text", "content", "response", "query", "data"):
                if inputs.get(key) is not None:
                    values["input"] = inputs[key]
                    break

        def render(value: Any) -> Any:
            if isinstance(value, str):
                try:
                    return value.format(**values)
                except (KeyError, IndexError):
                    return value  # leave unknown placeholders as written
            if isinstance(value, dict):
                return {k: render(v) for k, v in value.items()}
            if isinstance(value, list):
                return [render(v) for v in value]
            return value

        return {key: render(value) for key, value in raw.items()}

    @staticmethod
    def _extract_text(result: Any) -> str:
        """Readable text from an MCP tool result (content blocks, or the raw value)."""
        if isinstance(result, dict):
            content = result.get("content")
            if isinstance(content, list):
                parts = [
                    block.get("text", "")
                    for block in content
                    if isinstance(block, dict) and block.get("type") == "text"
                ]
                if parts:
                    return "\n".join(parts)
            if "text" in result and isinstance(result["text"], str):
                return result["text"]
        if isinstance(result, str):
            return result
        return json.dumps(result, ensure_ascii=False, default=str)

    def get_schema(self) -> Dict[str, Any]:
        """Return JSON schema for MCP tool configuration."""
        return {
            "type": "object",
            "properties": {
                "server": {
                    "type": "string",
                    "title": "MCP Server",
                    "description": "A server configured under Settings > MCP",
                },
                "tool": {
                    "type": "string",
                    "title": "Tool",
                    "description": "Tool to call on that server",
                },
                "arguments": {
                    "type": "object",
                    "title": "Arguments",
                    "description": 'Tool arguments as JSON. Use {input} for the incoming value, '
                                   'e.g. {"query": "{input}"}',
                    "default": {},
                },
            },
            "required": ["server", "tool"],
        }

    def get_input_schema(self) -> Dict[str, Any]:
        """Return schema for node inputs."""
        return {
            "input": {
                "type": "any",
                "description": "Value available to arguments as {input}",
                "required": False,
            },
        }

    def get_output_schema(self) -> Dict[str, Any]:
        """Return schema for node outputs."""
        return {
            "text": {"type": "string", "description": "Tool output as text"},
            "result": {"type": "object", "description": "Raw MCP result"},
            "server": {"type": "string", "description": "Server that ran the tool"},
            "tool": {"type": "string", "description": "Tool that was called"},
            "arguments": {"type": "object", "description": "Arguments the tool was called with"},
        }


# Register the node
NodeRegistry.register(
    "mcp_tool",
    MCPToolNode,
    MCPToolNode().get_metadata(),
)
