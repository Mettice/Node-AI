"""
Global pytest configuration and fixtures
"""

import pytest
import asyncio
import os
from unittest.mock import AsyncMock, Mock
from fastapi.testclient import TestClient


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_client():
    """Create test client for API testing."""
    from backend.main import app
    with TestClient(app) as client:
        yield client


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for testing."""
    with Mock() as mock_client:
        # Setup default successful response
        mock_stream = Mock()
        mock_chunk = Mock()
        mock_chunk.choices = [Mock()]
        mock_chunk.choices[0].delta.content = "Test AI response"
        mock_chunk.usage = None
        mock_stream.__iter__ = Mock(return_value=iter([mock_chunk]))
        mock_client.chat.completions.create.return_value = mock_stream
        yield mock_client


@pytest.fixture
def mock_anthropic_client():
    """Mock Anthropic client for testing."""
    with Mock() as mock_client:
        # Setup default successful response
        mock_stream_context = Mock()
        mock_stream = Mock()
        mock_stream.text_stream = ["Test ", "Anthropic ", "response"]
        
        mock_message = Mock()
        mock_usage = Mock()
        mock_usage.input_tokens = 10
        mock_usage.output_tokens = 15
        mock_message.usage = mock_usage
        mock_stream.get_final_message.return_value = mock_message
        
        mock_stream_context.__enter__ = Mock(return_value=mock_stream)
        mock_stream_context.__exit__ = Mock(return_value=None)
        mock_client.messages.stream.return_value = mock_stream_context
        yield mock_client


@pytest.fixture
def sample_workflow():
    """Sample workflow data for testing."""
    return {
        "name": "Test Workflow",
        "description": "A workflow for testing",
        "nodes": [
            {
                "id": "input-1",
                "type": "text_input",
                "position": {"x": 100, "y": 100},
                "data": {
                    "text": "Test input",
                    "config": {}
                }
            },
            {
                "id": "chat-1",
                "type": "chat",
                "position": {"x": 300, "y": 100},
                "data": {
                    "config": {
                        "provider": "openai",
                        "openai_model": "gpt-3.5-turbo",
                        "temperature": 0.7,
                        "system_prompt": "You are helpful.",
                        "user_prompt_template": "{input_text}",
                        "_node_id": "chat-1"
                    }
                }
            }
        ],
        "edges": [
            {
                "id": "edge-1",
                "source": "input-1",
                "target": "chat-1",
                "sourceHandle": "text",
                "targetHandle": "input_text"
            }
        ],
        "tags": ["test"]
    }


@pytest.fixture
def mock_database_pool():
    """Mock database connection pool."""
    with Mock() as mock_pool:
        mock_pool.get_pool_stats.return_value = {
            "status": "active",
            "min_connections": 5,
            "max_connections": 20,
            "current_connections": 8,
            "available_connections": 12
        }
        yield mock_pool


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Setup test environment variables."""
    # Set test environment variables
    os.environ["TESTING"] = "true"
    os.environ["LOG_LEVEL"] = "WARNING"  # Reduce noise in tests
    
    yield
    
    # Cleanup
    if "TESTING" in os.environ:
        del os.environ["TESTING"]


@pytest.fixture
def mock_api_keys():
    """Mock API key resolution for tests."""
    with Mock() as mock_resolver:
        mock_resolver.return_value = "test-api-key"
        yield mock_resolver


# Pytest hooks for better test organization
def pytest_configure(config):
    """Configure pytest with custom markers and settings."""
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests (deselect with '-m \"not unit\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests (deselect with '-m \"not integration\"')"
    )
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "requires_api_key: marks tests that require real API keys"
    )
    config.addinivalue_line(
        "markers", "requires_network: marks tests that require network access"
    )


def pytest_collection_modifyitems(config, items):
    """Automatically mark tests based on their location."""
    for item in items:
        # Auto-mark unit tests
        if "tests/unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        
        # Auto-mark integration tests
        if "tests/integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        
        # Auto-mark slow tests
        if hasattr(item, 'pytestmark'):
            for mark in item.pytestmark:
                if mark.name == 'slow':
                    item.add_marker(pytest.mark.slow)


# Performance testing helpers
@pytest.fixture
def benchmark_settings():
    """Settings for performance benchmarks."""
    return {
        "rounds": 5,
        "warmup_rounds": 1,
        "timer": "time.perf_counter"
    }