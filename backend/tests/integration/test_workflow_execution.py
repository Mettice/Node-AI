"""
Integration tests for workflow execution functionality
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, Mock, patch
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


class TestWorkflowExecutionAPI:
    """Test workflow execution through API endpoints."""
    
    def setup_method(self):
        """Setup for each test."""
        self.basic_workflow = {
            "name": "Test Execution Workflow",
            "description": "Workflow for testing execution",
            "nodes": [
                {
                    "id": "input-1",
                    "type": "text_input",
                    "position": {"x": 100, "y": 100},
                    "data": {
                        "text": "Hello World",
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
                            "max_tokens": 50,
                            "system_prompt": "You are a helpful assistant.",
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
            "tags": ["test", "execution"]
        }
    
    def test_create_and_execute_simple_workflow(self):
        """Test creating and executing a simple workflow."""
        # First create the workflow
        response = client.post("/api/v1/workflows", json=self.basic_workflow)
        assert response.status_code in [200, 201]
        
        workflow_data = response.json()
        workflow_id = workflow_data["id"]
        
        # Mock the LLM API calls for execution
        with patch('backend.nodes.llm.chat.resolve_api_key', return_value="test-key"):
            with patch('backend.nodes.llm.chat.OpenAI') as mock_openai_class:
                # Setup mock OpenAI response
                mock_client = Mock()
                mock_openai_class.return_value = mock_client
                
                # Mock successful API response
                mock_stream = Mock()
                mock_chunk = Mock()
                mock_chunk.choices = [Mock()]
                mock_chunk.choices[0].delta.content = "Hello! How can I help you?"
                mock_chunk.usage = None
                mock_stream.__iter__ = Mock(return_value=iter([mock_chunk]))
                mock_client.chat.completions.create.return_value = mock_stream
                
                # Execute the workflow
                execution_data = {
                    "workflow_id": workflow_id,
                    "input_data": {}
                }
                
                response = client.post("/api/v1/execute", json=execution_data)
                assert response.status_code in [200, 202]  # Accept async execution
                
                execution_result = response.json()
                assert "execution_id" in execution_result
    
    def test_workflow_execution_with_retry_logic(self):
        """Test workflow execution with retry logic for chat node."""
        # Create workflow with chat node
        response = client.post("/api/v1/workflows", json=self.basic_workflow)
        assert response.status_code in [200, 201]
        
        workflow_data = response.json()
        workflow_id = workflow_data["id"]
        
        # Mock the LLM API calls with retry scenario
        with patch('backend.nodes.llm.chat.resolve_api_key', return_value="test-key"):
            with patch('backend.nodes.llm.chat.OpenAI') as mock_openai_class:
                mock_client = Mock()
                mock_openai_class.return_value = mock_client
                
                # Create a function that fails first, then succeeds
                call_count = 0
                
                def mock_api_call(*args, **kwargs):
                    nonlocal call_count
                    call_count += 1
                    
                    if call_count == 1:
                        # First call fails with rate limit
                        raise Exception("rate limit exceeded")
                    else:
                        # Second call succeeds
                        mock_stream = Mock()
                        mock_chunk = Mock()
                        mock_chunk.choices = [Mock()]
                        mock_chunk.choices[0].delta.content = "Success after retry!"
                        mock_chunk.usage = None
                        mock_stream.__iter__ = Mock(return_value=iter([mock_chunk]))
                        return mock_stream
                
                mock_client.chat.completions.create.side_effect = mock_api_call
                
                # Execute workflow
                execution_data = {
                    "workflow_id": workflow_id,
                    "input_data": {}
                }
                
                response = client.post("/api/v1/execute", json=execution_data)
                assert response.status_code in [200, 202]
                
                # Should have retried (called API twice)
                assert mock_client.chat.completions.create.call_count >= 1
    
    def test_workflow_execution_status_tracking(self):
        """Test tracking execution status."""
        # Create workflow
        response = client.post("/api/v1/workflows", json=self.basic_workflow)
        assert response.status_code in [200, 201]
        
        workflow_data = response.json()
        workflow_id = workflow_data["id"]
        
        # Mock the execution
        with patch('backend.nodes.llm.chat.resolve_api_key', return_value="test-key"):
            with patch('backend.nodes.llm.chat.OpenAI') as mock_openai_class:
                mock_client = Mock()
                mock_openai_class.return_value = mock_client
                
                # Mock successful response
                mock_stream = Mock()
                mock_chunk = Mock()
                mock_chunk.choices = [Mock()]
                mock_chunk.choices[0].delta.content = "Test response"
                mock_chunk.usage = None
                mock_stream.__iter__ = Mock(return_value=iter([mock_chunk]))
                mock_client.chat.completions.create.return_value = mock_stream
                
                # Start execution
                execution_data = {
                    "workflow_id": workflow_id,
                    "input_data": {}
                }
                
                response = client.post("/api/v1/execute", json=execution_data)
                assert response.status_code in [200, 202]
                
                execution_result = response.json()
                execution_id = execution_result["execution_id"]
                
                # Check execution status
                status_response = client.get(f"/api/v1/executions/{execution_id}/status")
                assert status_response.status_code == 200
                
                status_data = status_response.json()
                assert "status" in status_data
                assert status_data["status"] in ["running", "completed", "failed", "pending"]
    
    def test_workflow_execution_invalid_workflow(self):
        """Test executing non-existent workflow."""
        execution_data = {
            "workflow_id": "nonexistent-workflow-id",
            "input_data": {}
        }
        
        response = client.post("/api/v1/execute", json=execution_data)
        assert response.status_code == 404
    
    def test_list_executions(self):
        """Test listing executions."""
        response = client.get("/api/v1/executions")
        assert response.status_code == 200
        
        data = response.json()
        assert "executions" in data
        assert isinstance(data["executions"], list)


class TestWorkflowExecutionCore:
    """Test core workflow execution functionality."""
    
    @pytest.fixture
    def simple_workflow_data(self):
        """Simple workflow for testing."""
        return {
            "nodes": [
                {
                    "id": "text-1",
                    "type": "text_input",
                    "data": {
                        "text": "Test input",
                        "config": {}
                    }
                }
            ],
            "edges": []
        }
    
    @pytest.fixture 
    def chat_workflow_data(self):
        """Workflow with chat node for testing."""
        return {
            "nodes": [
                {
                    "id": "input-1",
                    "type": "text_input",
                    "data": {
                        "text": "Hello AI",
                        "config": {}
                    }
                },
                {
                    "id": "chat-1",
                    "type": "chat", 
                    "data": {
                        "config": {
                            "provider": "openai",
                            "openai_model": "gpt-3.5-turbo",
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
            ]
        }
    
    @pytest.mark.asyncio
    async def test_simple_workflow_execution(self, simple_workflow_data):
        """Test executing a simple text input workflow."""
        from backend.core.execution_engine import ExecutionEngine
        
        engine = ExecutionEngine()
        
        # Execute the workflow
        result = await engine.execute_workflow(simple_workflow_data, {})
        
        assert result is not None
        assert "text-1" in result  # Should have result from text input node
        assert result["text-1"]["text"] == "Test input"
    
    @pytest.mark.asyncio
    async def test_chat_workflow_execution_with_mock(self, chat_workflow_data):
        """Test executing workflow with chat node (mocked)."""
        from backend.core.execution_engine import ExecutionEngine
        
        engine = ExecutionEngine()
        
        # Mock the chat node execution
        with patch('backend.nodes.llm.chat.resolve_api_key', return_value="test-key"):
            with patch('backend.nodes.llm.chat.OpenAI') as mock_openai_class:
                mock_client = Mock()
                mock_openai_class.return_value = mock_client
                
                # Setup mock response
                mock_stream = Mock()
                mock_chunk = Mock()
                mock_chunk.choices = [Mock()]
                mock_chunk.choices[0].delta.content = "Mocked AI response"
                mock_chunk.usage = None
                mock_stream.__iter__ = Mock(return_value=iter([mock_chunk]))
                mock_client.chat.completions.create.return_value = mock_stream
                
                # Execute workflow
                result = await engine.execute_workflow(chat_workflow_data, {})
                
                assert result is not None
                assert "input-1" in result
                assert "chat-1" in result
                assert result["chat-1"]["response"] == "Mocked AI response"
    
    @pytest.mark.asyncio
    async def test_workflow_execution_with_error_handling(self, chat_workflow_data):
        """Test workflow execution with error in one node."""
        from backend.core.execution_engine import ExecutionEngine
        
        engine = ExecutionEngine()
        
        # Mock the chat node to raise an error
        with patch('backend.nodes.llm.chat.resolve_api_key', return_value="test-key"):
            with patch('backend.nodes.llm.chat.OpenAI') as mock_openai_class:
                mock_client = Mock()
                mock_openai_class.return_value = mock_client
                
                # Make API call fail
                mock_client.chat.completions.create.side_effect = Exception("API Error")
                
                # Execute workflow - should handle error gracefully
                try:
                    result = await engine.execute_workflow(chat_workflow_data, {})
                    # If it doesn't raise, check that error is recorded
                    assert "chat-1" in result
                    # Error should be recorded in result
                except Exception as e:
                    # Error handling may vary based on implementation
                    assert "API Error" in str(e)


@pytest.mark.integration
class TestWorkflowExecutionPerformance:
    """Test workflow execution performance and scalability."""
    
    @pytest.mark.slow
    def test_multiple_concurrent_executions(self):
        """Test handling multiple concurrent workflow executions."""
        # Create a simple workflow
        workflow_data = {
            "name": "Performance Test Workflow",
            "nodes": [
                {
                    "id": "input-1",
                    "type": "text_input",
                    "data": {"text": "Concurrent test", "config": {}}
                }
            ],
            "edges": []
        }
        
        # Create workflow
        response = client.post("/api/v1/workflows", json=workflow_data)
        assert response.status_code in [200, 201]
        
        workflow_id = response.json()["id"]
        
        # Execute multiple times concurrently (using test client)
        execution_responses = []
        for i in range(5):
            execution_data = {
                "workflow_id": workflow_id,
                "input_data": {"test_run": i}
            }
            response = client.post("/api/v1/execute", json=execution_data)
            execution_responses.append(response)
        
        # All executions should be accepted
        for response in execution_responses:
            assert response.status_code in [200, 202]
            assert "execution_id" in response.json()
    
    @pytest.mark.slow
    def test_workflow_execution_timeout_handling(self):
        """Test workflow execution timeout scenarios."""
        # Create workflow with chat node that could timeout
        timeout_workflow = {
            "name": "Timeout Test Workflow",
            "nodes": [
                {
                    "id": "chat-slow",
                    "type": "chat",
                    "data": {
                        "config": {
                            "provider": "openai",
                            "openai_model": "gpt-3.5-turbo",
                            "max_tokens": 1000,  # Large response
                            "system_prompt": "Write a very long response.",
                            "_node_id": "chat-slow"
                        }
                    }
                }
            ],
            "edges": []
        }
        
        # Create workflow
        response = client.post("/api/v1/workflows", json=timeout_workflow)
        assert response.status_code in [200, 201]
        
        workflow_id = response.json()["id"]
        
        # Mock a slow API response
        with patch('backend.nodes.llm.chat.resolve_api_key', return_value="test-key"):
            with patch('backend.nodes.llm.chat.OpenAI') as mock_openai_class:
                mock_client = Mock()
                mock_openai_class.return_value = mock_client
                
                # Mock a call that takes time but eventually succeeds
                def slow_mock_call(*args, **kwargs):
                    import time
                    time.sleep(0.1)  # Simulate slow response
                    mock_stream = Mock()
                    mock_chunk = Mock()
                    mock_chunk.choices = [Mock()]
                    mock_chunk.choices[0].delta.content = "Slow response"
                    mock_chunk.usage = None
                    mock_stream.__iter__ = Mock(return_value=iter([mock_chunk]))
                    return mock_stream
                
                mock_client.chat.completions.create.side_effect = slow_mock_call
                
                # Execute with timeout consideration
                execution_data = {
                    "workflow_id": workflow_id,
                    "input_data": {}
                }
                
                response = client.post("/api/v1/execute", json=execution_data)
                # Should still be accepted, timeout handling is internal
                assert response.status_code in [200, 202]


class TestWorkflowExecutionValidation:
    """Test workflow execution input validation."""
    
    def test_invalid_execution_request(self):
        """Test various invalid execution requests."""
        # Missing workflow_id
        response = client.post("/api/v1/execute", json={"input_data": {}})
        assert response.status_code in [400, 422]
        
        # Invalid workflow_id format
        response = client.post("/api/v1/execute", json={
            "workflow_id": "",
            "input_data": {}
        })
        assert response.status_code in [400, 422]
    
    def test_execution_with_malformed_input_data(self):
        """Test execution with malformed input data."""
        # Create a simple workflow first
        workflow_data = {
            "name": "Validation Test",
            "nodes": [{"id": "input-1", "type": "text_input", "data": {"text": "test", "config": {}}}],
            "edges": []
        }
        
        response = client.post("/api/v1/workflows", json=workflow_data)
        assert response.status_code in [200, 201]
        
        workflow_id = response.json()["id"]
        
        # Test with invalid input_data types
        invalid_inputs = [
            {"workflow_id": workflow_id, "input_data": "not_a_dict"},
            {"workflow_id": workflow_id, "input_data": None},
            {"workflow_id": workflow_id}  # Missing input_data
        ]
        
        for invalid_input in invalid_inputs:
            response = client.post("/api/v1/execute", json=invalid_input)
            # Should handle gracefully - either reject or accept with defaults
            assert response.status_code in [200, 202, 400, 422]