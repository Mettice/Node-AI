"""
Labs nodes are hidden from the node palette but still registered and runnable.
"""

import pytest
from fastapi.testclient import TestClient

from backend.core.node_labs import LABS_NODE_TYPES
from backend.core.node_registry import NodeRegistry
from backend.main import app

CORE_NODES = ["chat", "embed", "vector_search", "rerank", "chunk", "file_loader",
              "crewai_agent", "advanced_nlp", "ai_web_search", "vector_store",
              "knowledge_graph", "hybrid_retrieval", "memory", "tool"]


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def clear_node_cache():
    from backend.core.cache import get_cache
    get_cache().delete("nodes:list:core")
    get_cache().delete("nodes:list:all")
    yield


@pytest.mark.unit
def test_labs_nodes_are_registered_and_runnable():
    import backend.nodes  # noqa: F401  (registers all nodes)
    for node_type in LABS_NODE_TYPES:
        assert NodeRegistry.is_registered(node_type), f"{node_type} must stay runnable"


@pytest.mark.unit
def test_palette_hides_labs_nodes(client):
    listed = {node["type"] for node in client.get("/api/v1/nodes").json()}
    assert listed.isdisjoint(LABS_NODE_TYPES)
    for node_type in CORE_NODES:
        assert node_type in listed, f"{node_type} belongs in the core palette"


@pytest.mark.unit
def test_labs_nodes_listed_on_request(client):
    listed = {node["type"] for node in client.get("/api/v1/nodes?include_labs=true").json()}
    assert LABS_NODE_TYPES <= listed


@pytest.mark.unit
def test_labs_nodes_listed_when_enabled(client, monkeypatch):
    # The API module imported the helper by name, so patch it there
    import backend.api.nodes as nodes_api
    monkeypatch.setattr(nodes_api, "show_labs_nodes", lambda: True)
    listed = {node["type"] for node in client.get("/api/v1/nodes").json()}
    assert LABS_NODE_TYPES <= listed


@pytest.mark.unit
def test_categories_exclude_labs_nodes(client):
    body = client.get("/api/v1/nodes/categories").json()
    listed = {node for category in body.values() for node in category["nodes"]}
    assert listed.isdisjoint(LABS_NODE_TYPES)
    assert all(category["count"] == len(category["nodes"]) for category in body.values())


@pytest.mark.unit
def test_labs_node_settings_still_open(client):
    # A saved workflow using a Labs node must still show its settings
    response = client.get("/api/v1/nodes/blog_generator")
    assert response.status_code == 200
    assert response.json()["type"] == "blog_generator"
