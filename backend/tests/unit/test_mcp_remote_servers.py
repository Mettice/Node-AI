"""
Adding and connecting remote MCP servers (by URL or from a remote preset).
"""

import json

import httpx
import pytest
from fastapi.testclient import TestClient

import backend.api.mcp as mcp_api
from backend.core.mcp.client import MCPTransportType
from backend.core.mcp.server_manager import MCP_SERVER_PRESETS, MCPServerManager
from backend.main import app
from backend.tests.unit.test_mcp_http_transport import FakeMCPServer, _patch_client

REMOTE_URL = "https://mcp.example.com/mcp"


@pytest.fixture
def manager(tmp_path):
    return MCPServerManager(config_path=str(tmp_path / "mcp_servers.json"))


@pytest.fixture
def client(manager, monkeypatch):
    monkeypatch.setattr(mcp_api, "get_server_manager", lambda user_id=None: manager)
    return TestClient(app)


@pytest.mark.unit
class TestAddRemoteServer:
    def test_added_by_url_with_token_header(self, manager):
        connection = manager.add_remote_server(
            name="acme", display_name="Acme", url=REMOTE_URL,
            headers={"Authorization": "Bearer tok"},
        )
        assert connection.server_type == "http" and connection.is_remote
        assert connection.url == REMOTE_URL
        assert connection.env == {"Authorization": "Bearer tok"}
        assert connection.command == ""  # nothing runs locally

    def test_url_must_be_http(self, manager):
        with pytest.raises(ValueError, match="must start with http"):
            manager.add_remote_server(name="bad", display_name="Bad", url="npx -y some-server")

    def test_saved_and_reloaded_from_file(self, manager, tmp_path):
        manager.add_remote_server(name="acme", display_name="Acme", url=REMOTE_URL,
                                  headers={"Authorization": "Bearer tok"})
        saved = json.loads((tmp_path / "mcp_servers.json").read_text())
        assert saved["servers"][0]["url"] == REMOTE_URL

        reloaded = MCPServerManager(config_path=str(tmp_path / "mcp_servers.json"))
        assert reloaded.get_connections()[0].url == REMOTE_URL

    def test_remote_preset_turns_token_into_header(self, manager):
        connection = manager.add_server_from_preset("github-remote", {"GITHUB_TOKEN": "ghp_123"})
        assert connection is not None
        assert connection.url == MCP_SERVER_PRESETS["github-remote"]["url"]
        assert connection.env == {"Authorization": "Bearer ghp_123"}
        assert connection.preset == "github-remote"

    def test_remote_preset_without_token_is_rejected(self, manager):
        assert manager.add_server_from_preset("github-remote", {}) is None


@pytest.mark.unit
class TestConnectRemoteServer:
    async def test_connect_uses_http_transport_and_registers_tools(self, manager, monkeypatch):
        server = FakeMCPServer()
        _patch_client(monkeypatch, server)
        manager.add_remote_server(name="acme", display_name="Acme", url=REMOTE_URL,
                                  headers={"Authorization": "Bearer tok"})

        assert await manager.connect_server("acme") is True
        connection = manager.get_connections()[0]
        assert connection.connected and connection.tools_count == 1
        # The auth header configured for the server reached the wire
        assert server.requests[0].headers["authorization"] == "Bearer tok"

    async def test_connect_failure_reports_the_reason(self, manager, monkeypatch):
        _patch_client(monkeypatch, FakeMCPServer(fail_status=401))
        manager.add_remote_server(name="acme", display_name="Acme", url=REMOTE_URL)
        with pytest.raises(RuntimeError, match="Initialization failed"):
            await manager.connect_server("acme")


@pytest.mark.unit
class TestRemoteServerApi:
    def test_add_remote_server_endpoint(self, client, manager):
        response = client.post("/api/v1/mcp/servers/remote", json={
            "name": "acme", "display_name": "Acme", "url": REMOTE_URL, "token": "tok",
        })
        assert response.status_code == 200
        assert response.json()["server"]["url"] == REMOTE_URL
        assert manager.get_connections()[0].env == {"Authorization": "Bearer tok"}

    def test_bad_url_returns_400(self, client):
        response = client.post("/api/v1/mcp/servers/remote", json={
            "name": "bad", "display_name": "Bad", "url": "not-a-url",
        })
        assert response.status_code == 400

    def test_presets_mark_which_need_a_local_install(self, client):
        presets = {p["name"]: p for p in client.get("/api/v1/mcp/presets").json()["presets"]}
        assert presets["github-remote"]["requires_local_install"] is False
        assert presets["github-remote"]["url"]
        assert presets["slack"]["requires_local_install"] is True
