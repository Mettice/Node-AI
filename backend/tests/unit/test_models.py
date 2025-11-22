"""
Unit tests for data models
"""

import pytest
from datetime import datetime
from backend.core.models import Workflow, Node, Edge, ExecutionStatus, NodeStatus


class TestWorkflow:
    """Test Workflow model."""
    
    def test_create_workflow(self):
        """Test creating a workflow."""
        workflow = Workflow(
            id="test-1",
            name="Test Workflow",
            nodes=[],
            edges=[]
        )
        assert workflow.id == "test-1"
        assert workflow.name == "Test Workflow"
        assert workflow.nodes == []
        assert workflow.edges == []
        assert workflow.is_deployed is False
    
    def test_workflow_with_nodes(self, sample_node):
        """Test workflow with nodes."""
        node = Node(**sample_node)
        workflow = Workflow(
            id="test-1",
            name="Test Workflow",
            nodes=[node],
            edges=[]
        )
        assert len(workflow.nodes) == 1
        assert workflow.nodes[0].id == "test-node-1"
    
    def test_workflow_with_edges(self, sample_workflow):
        """Test workflow with edges."""
        nodes = [Node(**n) for n in sample_workflow["nodes"]]
        edges = [Edge(**e) for e in sample_workflow["edges"]]
        workflow = Workflow(
            id=sample_workflow["id"],
            name=sample_workflow["name"],
            nodes=nodes,
            edges=edges
        )
        assert len(workflow.edges) == 1
        assert workflow.edges[0].source == "input-1"
        assert workflow.edges[0].target == "chat-1"


class TestNode:
    """Test Node model."""
    
    def test_create_node(self, sample_node):
        """Test creating a node."""
        node = Node(**sample_node)
        assert node.id == "test-node-1"
        assert node.type == "text_input"
        assert node.data["text"] == "Test input"
    
    def test_node_position(self):
        """Test node position."""
        from backend.core.models import Position
        node = Node(
            id="test-1",
            type="text_input",
            position=Position(x=100, y=200),
            data={}
        )
        assert node.position.x == 100
        assert node.position.y == 200


class TestEdge:
    """Test Edge model."""
    
    def test_create_edge(self):
        """Test creating an edge."""
        edge = Edge(
            id="edge-1",
            source="node-1",
            target="node-2"
        )
        assert edge.id == "edge-1"
        assert edge.source == "node-1"
        assert edge.target == "node-2"
    
    def test_edge_with_handles(self):
        """Test edge with source and target handles."""
        edge = Edge(
            id="edge-1",
            source="node-1",
            target="node-2",
            sourceHandle="output",
            targetHandle="input"
        )
        assert edge.sourceHandle == "output"
        assert edge.targetHandle == "input"


class TestEnums:
    """Test enum types."""
    
    def test_execution_status(self):
        """Test ExecutionStatus enum."""
        assert ExecutionStatus.PENDING == "pending"
        assert ExecutionStatus.COMPLETED == "completed"
        assert ExecutionStatus.FAILED == "failed"
    
    def test_node_status(self):
        """Test NodeStatus enum."""
        assert NodeStatus.PENDING == "pending"
        assert NodeStatus.RUNNING == "running"
        assert NodeStatus.COMPLETED == "completed"
        assert NodeStatus.FAILED == "failed"

