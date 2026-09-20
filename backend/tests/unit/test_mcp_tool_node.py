"""
The MCP Tool node: calls a tool on a configured MCP server from a workflow.
"""

import pytest

import backend.core.mcp.client as mcp_client_module
import backend.core.mcp.server_manager as server_manager_module
from backend.core.mcp.client import MCPClient
from backend.core.mcp.server_manager import MCPServerManager
from backend.nodes.tools.mcp_tool_node import MCPToolNode
from backend.tests.unit.test_mcp_http_transport import FakeMCPServer, _patch_client

REMOTE_URL = "https://mcp.example.com/mcp"


@pytest.fixture
def mcp_env(tmp_path, monkeypatch):
    """A configured remote server, a fresh client, and a fake MCP server behind it."""
    server = FakeMCPServer()
    _patch_client(monkeypatch, server)

    client = MCPClient()
    monkeypatch.setattr(mcp_client_module, "get_mcp_client", lambda: client)
    monkeypatch.setattr(server_manager_module, "get_mcp_client", lambda: client)

    manager = MCPServerManager(config_path=str(tmp_path / "mcp_servers.json"))
    manager.add_remote_server(name="acme", display_name="Acme", url=REMOTE_URL,
                              headers={"Authorization": "Bearer tok"})
    monkeypatch.setattr(server_manager_module, "get_server_manager", lambda user_id=None: manager)

    return {"server": server, "manager": manager, "client": client}


@pytest.mark.unit
class TestMCPToolNode:
    async def test_calls_tool_and_returns_text(self, mcp_env):
        result = await MCPToolNode().execute(
            {}, {"server": "acme", "tool": "search_records", "arguments": {"query": "acme"}}
        )
        assert result["text"] == "found 2 records"
        assert result["tool"] == "search_records" and result["server"] == "acme"
        assert mcp_env["server"].bodies[-1]["params"]["arguments"] == {"query": "acme"}

    async def test_connects_on_demand(self, mcp_env):
        assert mcp_env["manager"].get_connections()[0].connected is False
        await MCPToolNode().execute({}, {"server": "acme", "tool": "search_records"})
        assert mcp_env["manager"].get_connections()[0].connected is True

    async def test_input_fills_placeholder(self, mcp_env):
        await MCPToolNode().execute(
            {"text": "quarterly report"},
            {"server": "acme", "tool": "search_records", "arguments": {"query": "{input}"}},
        )
        assert mcp_env["server"].bodies[-1]["params"]["arguments"] == {"query": "quarterly report"}

    async def test_arguments_accept_json_string(self, mcp_env):
        await MCPToolNode().execute(
            {}, {"server": "acme", "tool": "search_records", "arguments": '{"query": "from json"}'}
        )
        assert mcp_env["server"].bodies[-1]["params"]["arguments"] == {"query": "from json"}

    async def test_invalid_json_arguments_are_reported(self, mcp_env):
        with pytest.raises(ValueError, match="valid JSON"):
            await MCPToolNode().execute(
                {}, {"server": "acme", "tool": "search_records", "arguments": "{oops"}
            )

    async def test_unknown_server_is_reported(self, mcp_env):
        with pytest.raises(ValueError, match="not configured"):
            await MCPToolNode().execute({}, {"server": "nope", "tool": "search_records"})

    async def test_missing_selection_is_reported(self, mcp_env):
        with pytest.raises(ValueError, match="No MCP server selected"):
            await MCPToolNode().execute({}, {"tool": "search_records"})
        with pytest.raises(ValueError, match="No MCP tool selected"):
            await MCPToolNode().execute({}, {"server": "acme"})

    async def test_tool_error_is_reported(self, mcp_env):
        with pytest.raises(ValueError, match="failed"):
            await MCPToolNode().execute({}, {"server": "acme", "tool": "does_not_exist"})

    def test_registered_and_in_core_palette(self):
        from backend.core.node_labs import is_labs_node
        from backend.core.node_registry import NodeRegistry
        import backend.nodes  # noqa: F401

        assert NodeRegistry.is_registered("mcp_tool")
        assert not is_labs_node("mcp_tool")
