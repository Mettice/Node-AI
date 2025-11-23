"""
Pytest configuration and fixtures
"""

import pytest
import asyncio
import os
import sys
from pathlib import Path
import tempfile
import shutil
from typing import Generator

# Add project root to path for imports
_backend_dir = Path(__file__).parent.parent
_project_root = _backend_dir.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("OPENAI_API_KEY", "test-key")
os.environ.setdefault("ANTHROPIC_API_KEY", "test-key")


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for test files."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def sample_workflow():
    """Sample workflow for testing."""
    return {
        "id": "test-workflow-1",
        "name": "Test Workflow",
        "description": "A test workflow",
        "nodes": [
            {
                "id": "input-1",
                "type": "text_input",
                "position": {"x": 100, "y": 100},
                "data": {
                    "text": "Hello, world!",
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
                        "model": "gpt-3.5-turbo",
                        "prompt": "Echo: {{input-1.text}}"
                    }
                }
            }
        ],
        "edges": [
            {
                "id": "edge-1",
                "source": "input-1",
                "target": "chat-1"
            }
        ],
        "tags": ["test"],
        "is_template": False,
        "is_deployed": False
    }


@pytest.fixture
def sample_node():
    """Sample node for testing."""
    return {
        "id": "test-node-1",
        "type": "text_input",
        "position": {"x": 100, "y": 100},
        "data": {
            "text": "Test input",
            "config": {}
        }
    }

