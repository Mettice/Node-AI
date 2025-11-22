"""
Unit tests for node registry
"""

import pytest
from backend.core.node_registry import NodeRegistry
from backend.nodes.base import BaseNode


class TestNodeRegistry:
    """Test NodeRegistry."""
    
    def test_get_node_type(self):
        """Test getting a node type."""
        node_class = NodeRegistry.get("text_input")
        assert node_class is not None
        assert issubclass(node_class, BaseNode)
    
    def test_get_nonexistent_node_type(self):
        """Test getting a nonexistent node type."""
        from backend.core.exceptions import NodeNotFoundError
        with pytest.raises(NodeNotFoundError):
            NodeRegistry.get("nonexistent")
    
    def test_list_node_types(self):
        """Test listing all node types."""
        node_types = NodeRegistry.list_all()
        assert isinstance(node_types, list)
        assert len(node_types) > 0
        assert "text_input" in node_types
    
    def test_get_node_schema(self):
        """Test getting node metadata/schema."""
        metadata = NodeRegistry.get_metadata("text_input")
        # Metadata might be None if not pre-registered, so try getting it from node instance
        if metadata is None:
            node_class = NodeRegistry.get("text_input")
            node_instance = node_class()
            metadata = node_instance.get_metadata()
        assert metadata is not None
        # Check that metadata has expected structure
        assert hasattr(metadata, 'node_type') or hasattr(metadata, 'name')

