"""
Remote MCP servers over Streamable HTTP.

A fake MCP server is served through httpx.MockTransport, so these tests make no
network calls and need no Node.js.
"""

import json

import httpx
import pytest

from backend.core.mcp.client import MCPClient, MCPServerConfig, MCPTransportType

SERVER_URL = "https://mcp.example.com/mcp"
SESSION_ID = "session-abc-123"


class FakeMCPServer:
    """Minimal MCP server: initialize, tools/list (as SSE) and tools/call (as JSON)."""

    def __init__(self, *, fail_status: int = 0, protocol_version: str = "2025-06-18"):
        self.requests: list[httpx.Request] = []
        self.bodies: list[dict] = []
        self.fail_status = fail_status
        self.protocol_version = protocol_version

    def handler(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        body = json.loads(request.content.decode())
        self.bodies.append(body)

        if self.fail_status:
            return httpx.Response(self.fail_status, text="nope")

        method = body.get("method")

        if method == "initialize":
            return httpx.Response(
                200,
                json={
                    "jsonrpc": "2.0",
                    "id": body["id"],
                    "result": {
                        "protocolVersion": self.protocol_version,
                        "capabilities": {"tools": {}},
                        "serverInfo": {"name": "fake", "version": "1.0"},
                    },
                },
                headers={"mcp-session-id": SESSION_ID},
            )

        if method == "notifications/initialized":
            return httpx.Response(202)

        if method == "tools/list":
            # Answer as SSE, which the transport must parse
            payload = {
                "jsonrpc": "2.0",
                "id": body["id"],
                "result": {
                    "tools": [
                        {
                            "name": "search_records",
                            "description": "Search records",
                            "inputSchema": {"type": "object", "properties": {"query": {"type": "string"}}},
                        }
                    ]
                },
            }
            sse = f"event: message\ndata: {json.dumps(payload)}\n\n"
            return httpx.Response(200, text=sse, headers={"content-type": "text/event-stream"})

        if method == "tools/call":
            return httpx.Response(
                200,
                json={
                    "jsonrpc": "2.0",
                    "id": body["id"],
                    "result": {"content": [{"type": "text", "text": "found 2 records"}]},
                },
            )

        return httpx.Response(
            200, json={"jsonrpc": "2.0", "id": body.get("id"), "error": {"code": -32601, "message": "unknown"}}
        )


def _patch_client(monkeypatch, server: "FakeMCPServer") -> None:
    """Make httpx.AsyncClient() talk to the fake server instead of the network."""
    real_async_client = httpx.AsyncClient  # capture before patching, or the factory recurses

    def client_factory(**kwargs):
        kwargs.pop("transport", None)
        return real_async_client(transport=httpx.MockTransport(server.handler), **kwargs)

    monkeypatch.setattr(httpx, "AsyncClient", client_factory)


@pytest.fixture
def fake_server(monkeypatch):
    server = FakeMCPServer()
    _patch_client(monkeypatch, server)
    return server


def http_config(**kwargs) -> MCPServerConfig:
    return MCPServerConfig(
        name="fake",
        command="",
        transport=MCPTransportType.HTTP,
        url=SERVER_URL,
        **kwargs,
    )


@pytest.mark.unit
class TestHttpTransport:
    async def test_connect_discovers_tools(self, fake_server):
        client = MCPClient()
        assert await client.add_server(http_config()) is True

        tools = client.get_available_tools()
        assert [t.name for t in tools] == ["search_records"]
        assert tools[0].server_name == "fake"
        # tools/list came back as SSE, so the parser handled it
        assert any(b.get("method") == "tools/list" for b in fake_server.bodies)

    async def test_handshake_order(self, fake_server):
        await MCPClient().add_server(http_config())
        assert [b.get("method") for b in fake_server.bodies][:3] == [
            "initialize",
            "notifications/initialized",
            "tools/list",
        ]

    async def test_session_and_protocol_headers_are_echoed(self, fake_server):
        await MCPClient().add_server(http_config())
        # The first request cannot know the session; later ones must send it back
        assert "mcp-session-id" not in {k.lower() for k in fake_server.requests[0].headers}
        later = fake_server.requests[-1].headers
        assert later["mcp-session-id"] == SESSION_ID
        assert later["mcp-protocol-version"] == "2025-06-18"

    async def test_auth_headers_are_sent(self, fake_server):
        await MCPClient().add_server(http_config(headers={"Authorization": "Bearer secret-token"}))
        assert fake_server.requests[0].headers["authorization"] == "Bearer secret-token"

    async def test_accepts_json_and_sse(self, fake_server):
        await MCPClient().add_server(http_config())
        accept = fake_server.requests[0].headers["accept"]
        assert "application/json" in accept and "text/event-stream" in accept

    async def test_call_tool(self, fake_server):
        client = MCPClient()
        await client.add_server(http_config())
        result = await client.call_tool("search_records", {"query": "acme"})
        assert result["content"][0]["text"] == "found 2 records"
        call = fake_server.bodies[-1]
        assert call["method"] == "tools/call"
        assert call["params"] == {"name": "search_records", "arguments": {"query": "acme"}}

    async def test_server_error_raises_with_status(self, monkeypatch):
        _patch_client(monkeypatch, FakeMCPServer(fail_status=401))
        with pytest.raises(RuntimeError, match="Initialization failed"):
            await MCPClient().add_server(http_config())

    async def test_missing_url_is_rejected(self, fake_server):
        config = MCPServerConfig(name="fake", command="", transport=MCPTransportType.HTTP)
        with pytest.raises(ValueError, match="no url"):
            await MCPClient().add_server(config)

    async def test_disconnect_clears_state(self, fake_server):
        client = MCPClient()
        await client.add_server(http_config())
        await client.disconnect_server("fake")
        assert client.get_available_tools() == []
        assert "fake" not in client._http_clients
        assert "fake" not in client._http_sessions
