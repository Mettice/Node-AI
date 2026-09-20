"""
The workflows API stores a logged-in user's workflows in the database.

Covers the wiring between the endpoints and WorkflowStore, since the endpoints previously
wrote straight to disk.
"""

import pytest
from fastapi.testclient import TestClient

import backend.api.workflows as workflows_api
import backend.core.workflow_store as store_module
import backend.middleware.auth as auth_middleware
import backend.nodes  # noqa: F401  (registers node types the validator checks against)
from backend.main import app
from backend.tests.unit.test_workflow_store import FakeSupabase

USER = {"id": "user-1", "email": "user@example.com"}

WORKFLOW = {
    "name": "Support assistant",
    "nodes": [
        {"id": "n1", "type": "text_input", "position": {"x": 0, "y": 0}, "data": {"text": "hi"}},
        {"id": "n2", "type": "chunk", "position": {"x": 200, "y": 0}, "data": {}},
    ],
    "edges": [{"id": "e1", "source": "n1", "target": "n2"}],
}


@pytest.fixture
def api(tmp_path, monkeypatch):
    """Logged-in client, a fake database, and a temporary workflows directory."""
    fake = FakeSupabase()
    import backend.core.database as database
    monkeypatch.setattr(database, "get_supabase_client", lambda: fake)
    monkeypatch.setattr(store_module, "WORKFLOWS_DIR", tmp_path)
    monkeypatch.setattr(workflows_api, "get_user_id_from_request", lambda request: USER["id"])
    monkeypatch.setattr(workflows_api, "require_user_id", lambda request: USER["id"])

    async def user(request):
        return USER
    monkeypatch.setattr(auth_middleware, "get_user_context", user)

    # Endpoints cache workflows by id; keep tests independent
    from backend.core.cache import get_cache
    get_cache().clear() if hasattr(get_cache(), "clear") else None

    return {"client": TestClient(app), "db": fake, "dir": tmp_path}


@pytest.mark.unit
class TestWorkflowApiStorage:
    def test_created_workflow_goes_to_the_database(self, api):
        response = api["client"].post("/api/v1/workflows", json=WORKFLOW)
        assert response.status_code in (200, 201), response.text

        workflow_id = response.json()["id"]
        assert [row["id"] for row in api["db"].rows] == [workflow_id]
        assert api["db"].rows[0]["user_id"] == USER["id"]
        # Nothing written to the container's disk
        assert list(api["dir"].glob("*.json")) == []

    def test_created_workflow_can_be_read_back(self, api):
        workflow_id = api["client"].post("/api/v1/workflows", json=WORKFLOW).json()["id"]

        fetched = api["client"].get(f"/api/v1/workflows/{workflow_id}")
        assert fetched.status_code == 200
        assert fetched.json()["name"] == "Support assistant"

    def test_listed_workflows_come_from_the_database(self, api):
        api["client"].post("/api/v1/workflows", json=WORKFLOW)
        listed = api["client"].get("/api/v1/workflows").json()
        assert "Support assistant" in [w["name"] for w in listed["workflows"]]

    def test_deleted_workflow_leaves_the_database(self, api):
        workflow_id = api["client"].post("/api/v1/workflows", json=WORKFLOW).json()["id"]
        assert api["client"].delete(f"/api/v1/workflows/{workflow_id}").status_code == 200
        assert api["db"].rows == []
