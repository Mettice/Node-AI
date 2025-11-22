"""
Integration tests for workflow API endpoints
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


class TestWorkflowAPI:
    """Test workflow API endpoints."""
    
    def test_list_workflows(self):
        """Test listing workflows."""
        response = client.get("/api/v1/workflows")
        assert response.status_code == 200
        data = response.json()
        assert "workflows" in data
        assert isinstance(data["workflows"], list)
    
    def test_create_workflow(self):
        """Test creating a workflow."""
        workflow_data = {
            "name": "Test Workflow",
            "description": "A test workflow",
            "nodes": [
                {
                    "id": "input-1",
                    "type": "text_input",
                    "position": {"x": 100, "y": 100},
                    "data": {"text": "Hello", "config": {}}
                }
            ],
            "edges": [],
            "tags": ["test"]
        }
        response = client.post("/api/v1/workflows", json=workflow_data)
        assert response.status_code in [200, 201]
        data = response.json()
        assert data["name"] == "Test Workflow"
        assert "id" in data
    
    def test_get_workflow_not_found(self):
        """Test getting a nonexistent workflow."""
        response = client.get("/api/v1/workflows/nonexistent-id")
        assert response.status_code == 404
    
    def test_health_endpoint(self):
        """Test health check endpoint."""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data

