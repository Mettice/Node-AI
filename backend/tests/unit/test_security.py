"""
Unit tests for security utilities
"""

import pytest
from backend.core.security import (
    sanitize_string,
    validate_workflow_id,
    validate_node_id,
    validate_file_name,
    sanitize_dict,
)


class TestSanitizeString:
    """Test string sanitization."""
    
    def test_sanitize_basic(self):
        """Test basic string sanitization."""
        result = sanitize_string("Hello World")
        assert result == "Hello World"
    
    def test_sanitize_html(self):
        """Test HTML escaping."""
        result = sanitize_string("<script>alert('xss')</script>")
        assert "&lt;script&gt;" in result
        assert "<script>" not in result
    
    def test_sanitize_null_bytes(self):
        """Test null byte removal."""
        result = sanitize_string("Hello\x00World")
        assert "\x00" not in result
        assert "HelloWorld" in result
    
    def test_sanitize_max_length(self):
        """Test max length truncation."""
        long_string = "a" * 200
        result = sanitize_string(long_string, max_length=100)
        assert len(result) == 100


class TestValidateWorkflowId:
    """Test workflow ID validation."""
    
    def test_valid_workflow_id(self):
        """Test valid workflow IDs."""
        assert validate_workflow_id("workflow-123") is True
        assert validate_workflow_id("test_workflow") is True
        assert validate_workflow_id("abc123") is True
    
    def test_invalid_workflow_id(self):
        """Test invalid workflow IDs."""
        assert validate_workflow_id("") is False
        assert validate_workflow_id("workflow@123") is False  # Special chars
        assert validate_workflow_id("workflow 123") is False  # Spaces
        assert validate_workflow_id("a" * 101) is False  # Too long


class TestValidateNodeId:
    """Test node ID validation."""
    
    def test_valid_node_id(self):
        """Test valid node IDs."""
        assert validate_node_id("node-123") is True
        assert validate_node_id("test_node") is True
    
    def test_invalid_node_id(self):
        """Test invalid node IDs."""
        assert validate_node_id("") is False
        assert validate_node_id("node@123") is False


class TestValidateFileName:
    """Test file name validation."""
    
    def test_valid_file_name(self):
        """Test valid file names."""
        assert validate_file_name("document.pdf") is True
        assert validate_file_name("test_file.txt") is True
    
    def test_invalid_file_name(self):
        """Test invalid file names."""
        assert validate_file_name("../../../etc/passwd") is False  # Path traversal
        assert validate_file_name("file\x00name.txt") is False  # Null bytes
        assert validate_file_name("file/name.txt") is False  # Slashes
        assert validate_file_name("file\\name.txt") is False  # Backslashes
        assert validate_file_name("a" * 256) is False  # Too long


class TestSanitizeDict:
    """Test dictionary sanitization."""
    
    def test_sanitize_simple_dict(self):
        """Test sanitizing a simple dictionary."""
        data = {
            "key1": "value1",
            "key2": "<script>alert('xss')</script>",
        }
        result = sanitize_dict(data)
        assert result["key1"] == "value1"
        assert "<script>" not in result["key2"]
    
    def test_sanitize_nested_dict(self):
        """Test sanitizing nested dictionaries."""
        data = {
            "level1": {
                "level2": "<script>alert('xss')</script>",
            }
        }
        result = sanitize_dict(data)
        assert "<script>" not in result["level1"]["level2"]
    
    def test_sanitize_list(self):
        """Test sanitizing lists in dictionaries."""
        data = {
            "items": ["item1", "<script>alert('xss')</script>", "item3"],
        }
        result = sanitize_dict(data)
        assert result["items"][0] == "item1"
        assert "<script>" not in result["items"][1]

