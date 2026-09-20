"""
Where workflows are saved: the database when Supabase is configured, files otherwise.

Saved workflows used to live only on the container's disk, which Railway replaces on
every deploy, so anything a user built disappeared.
"""

from typing import Any, Dict, List

import pytest

import backend.core.workflow_store as store_module
from backend.core.models import Edge, Node, Position, Workflow
from backend.core.workflow_store import WorkflowStore


class FakeTable:
    """The slice of the Supabase table API the store uses."""

    def __init__(self, rows: List[Dict[str, Any]]):
        self.rows = rows
        self._filters: Dict[str, Any] = {}
        self._op = "select"
        self._payload: Dict[str, Any] = {}

    def select(self, *_):
        self._op = "select"
        return self

    def upsert(self, payload, **_):
        self._op = "upsert"
        self._payload = payload
        return self

    def delete(self):
        self._op = "delete"
        return self

    def eq(self, field, value):
        self._filters[field] = value
        return self

    def limit(self, _):
        return self

    def _matching(self):
        return [r for r in self.rows if all(str(r.get(k)) == str(v) for k, v in self._filters.items())]

    def execute(self):
        if self._op == "upsert":
            self.rows[:] = [r for r in self.rows if r["id"] != self._payload["id"]]
            self.rows.append(self._payload)
            return type("Result", (), {"data": [self._payload]})()
        if self._op == "delete":
            matching = self._matching()
            self.rows[:] = [r for r in self.rows if r not in matching]
            return type("Result", (), {"data": matching})()
        return type("Result", (), {"data": self._matching()})()


class FakeSupabase:
    def __init__(self):
        self.rows: List[Dict[str, Any]] = []

    def table(self, _name):
        return FakeTable(self.rows)


def make_workflow(workflow_id="wf-1", name="My workflow", **kwargs) -> Workflow:
    return Workflow(
        id=workflow_id,
        name=name,
        nodes=[Node(id="n1", type="text_input", position=Position(x=0, y=0), data={"text": "hi"})],
        edges=[Edge(id="e1", source="n1", target="n2")],
        **kwargs,
    )


@pytest.fixture
def supabase(monkeypatch):
    fake = FakeSupabase()
    import backend.core.database as database
    monkeypatch.setattr(database, "get_supabase_client", lambda: fake)
    return fake


@pytest.fixture
def files_only(monkeypatch, tmp_path):
    """No Supabase, and workflows written to a temporary directory."""
    import backend.core.database as database
    monkeypatch.setattr(database, "get_supabase_client", lambda: None)
    monkeypatch.setattr(store_module, "WORKFLOWS_DIR", tmp_path)
    return tmp_path


@pytest.mark.unit
class TestDatabaseStorage:
    def test_save_writes_to_the_database_not_disk(self, supabase, tmp_path, monkeypatch):
        monkeypatch.setattr(store_module, "WORKFLOWS_DIR", tmp_path)
        WorkflowStore(user_id="user-1").save(make_workflow())

        assert len(supabase.rows) == 1
        assert supabase.rows[0]["user_id"] == "user-1"
        assert supabase.rows[0]["nodes"][0]["type"] == "text_input"
        assert list(tmp_path.glob("*.json")) == []  # nothing on the ephemeral disk

    def test_round_trip(self, supabase):
        store = WorkflowStore(user_id="user-1")
        store.save(make_workflow(name="Round trip"))

        loaded = store.load("wf-1")
        assert loaded.name == "Round trip"
        assert loaded.owner_id == "user-1"
        assert loaded.nodes[0].type == "text_input"
        assert loaded.edges[0].source == "n1"

    def test_another_user_cannot_load_it(self, supabase, tmp_path, monkeypatch):
        monkeypatch.setattr(store_module, "WORKFLOWS_DIR", tmp_path)
        WorkflowStore(user_id="user-1").save(make_workflow())
        assert WorkflowStore(user_id="user-2").load("wf-1") is None

    def test_another_users_leftover_file_is_not_served(self, supabase, tmp_path, monkeypatch):
        """Files predate the database; one owned by someone else must stay hidden."""
        monkeypatch.setattr(store_module, "WORKFLOWS_DIR", tmp_path)
        WorkflowStore()._save_file(make_workflow("wf-old", "Theirs", owner_id="user-1"))

        assert WorkflowStore(user_id="user-2").load("wf-old") is None
        assert WorkflowStore(user_id="user-1").load("wf-old").name == "Theirs"

    def test_list_returns_only_own_workflows(self, supabase, tmp_path, monkeypatch):
        monkeypatch.setattr(store_module, "WORKFLOWS_DIR", tmp_path)
        WorkflowStore(user_id="user-1").save(make_workflow("wf-1", "Mine"))
        WorkflowStore(user_id="user-2").save(make_workflow("wf-2", "Theirs"))

        assert [w.name for w in WorkflowStore(user_id="user-1").list()] == ["Mine"]

    def test_delete(self, supabase):
        store = WorkflowStore(user_id="user-1")
        store.save(make_workflow())
        assert store.delete("wf-1") is True
        assert store.load("wf-1") is None

    def test_load_any_ignores_ownership(self, supabase):
        """Deployed workflows are queried, and webhooks triggered, by other people."""
        WorkflowStore(user_id="user-1").save(make_workflow())
        assert WorkflowStore().load_any("wf-1").name == "My workflow"

    def test_templates_on_disk_stay_visible(self, supabase, tmp_path, monkeypatch):
        monkeypatch.setattr(store_module, "WORKFLOWS_DIR", tmp_path)
        WorkflowStore()._save_file(make_workflow("tpl-1", "Basic RAG", is_template=True))
        WorkflowStore(user_id="user-1").save(make_workflow("wf-1", "Mine"))

        names = {w.name for w in WorkflowStore(user_id="user-1").list()}
        assert names == {"Basic RAG", "Mine"}


@pytest.mark.unit
class TestFileStorage:
    def test_used_when_supabase_is_not_configured(self, files_only):
        store = WorkflowStore(user_id="user-1")
        assert store.uses_database is False

        store.save(make_workflow())
        assert (files_only / "wf-1.json").exists()
        assert store.load("wf-1").name == "My workflow"
        assert store.delete("wf-1") is True
        assert store.load("wf-1") is None

    def test_local_mode_without_user(self, files_only):
        store = WorkflowStore()
        store.save(make_workflow())
        assert [w.id for w in store.list()] == ["wf-1"]
