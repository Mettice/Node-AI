"""
Tests that API routes require a logged-in user when Supabase is configured,
while the intentionally public routes stay reachable.
"""

import pytest
from fastapi.testclient import TestClient

import backend.middleware.auth as auth_middleware
from backend.main import app

ORIGIN = "https://nodai.io"


@pytest.fixture
def client():
    # No context manager: skip lifespan startup, only the middleware matters here
    return TestClient(app)


@pytest.fixture
def supabase_configured(monkeypatch):
    monkeypatch.setattr(auth_middleware, "get_supabase_client", lambda: object())


@pytest.fixture
def anonymous(monkeypatch):
    async def no_user(request):
        return None
    monkeypatch.setattr(auth_middleware, "get_user_context", no_user)


@pytest.fixture
def logged_in(monkeypatch):
    async def user(request):
        return {"id": "user-1", "email": "user@example.com"}
    monkeypatch.setattr(auth_middleware, "get_user_context", user)


@pytest.mark.unit
@pytest.mark.parametrize("method,path", [
    ("GET", "/api/v1/nodes"),
    ("GET", "/api/v1/workflows"),
    ("POST", "/api/v1/workflows/execute"),
    ("GET", "/api/v1/executions"),
    ("POST", "/api/v1/executions/abc/record"),
    ("GET", "/api/v1/secrets"),
    ("GET", "/api/v1/oauth/tokens"),
])
def test_anonymous_requests_are_rejected(client, supabase_configured, anonymous, method, path):
    response = client.request(method, path, json={})
    assert response.status_code == 401
    assert response.json() == {"detail": "Authentication required"}


@pytest.mark.unit
@pytest.mark.parametrize("method,path", [
    ("GET", "/api/v1/health"),
    ("GET", "/"),
    ("GET", "/api/v1/oauth/callback"),
    ("POST", "/api/v1/workflows/some-id/query"),
    ("POST", "/api/v1/webhooks/some-id/trigger"),
    ("GET", "/api/v1/executions/some-id"),
])
def test_public_routes_skip_auth(client, supabase_configured, anonymous, method, path):
    response = client.request(method, path, json={})
    assert response.status_code != 401


@pytest.mark.unit
def test_execution_stream_skips_auth():
    # Checked against the rule directly: calling the SSE endpoint would never return
    from starlette.requests import Request
    request = Request({"type": "http", "method": "GET", "path": "/api/v1/executions/some-id/stream",
                       "headers": [], "query_string": b""})
    assert auth_middleware._allows_unauthenticated(request)


@pytest.mark.unit
def test_cors_preflight_is_not_blocked(client, supabase_configured, anonymous):
    response = client.options(
        "/api/v1/workflows/execute",
        headers={"Origin": ORIGIN, "Access-Control-Request-Method": "POST"},
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == ORIGIN


@pytest.mark.unit
def test_rejection_carries_cors_headers(client, supabase_configured, anonymous):
    # Otherwise the browser hides the 401 from the frontend as a CORS error
    response = client.get("/api/v1/nodes", headers={"Origin": ORIGIN})
    assert response.status_code == 401
    assert response.headers["access-control-allow-origin"] == ORIGIN


@pytest.mark.unit
def test_logged_in_user_is_allowed(client, supabase_configured, logged_in):
    assert client.get("/api/v1/nodes").status_code == 200


@pytest.mark.unit
def test_no_enforcement_without_supabase(client, monkeypatch, anonymous):
    monkeypatch.setattr(auth_middleware, "get_supabase_client", lambda: None)
    assert client.get("/api/v1/nodes").status_code == 200
