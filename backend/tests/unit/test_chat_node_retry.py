"""
Unit tests for Chat node with retry functionality
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from backend.nodes.llm.chat import ChatNode
from backend.utils.retry import RetryableError, NonRetryableError


class TestChatNodeRetryLogic:
    """Test Chat node retry integration."""
    
    @pytest.fixture
    def chat_node(self):
        """Create a ChatNode instance for testing."""
        return ChatNode()
    
    @pytest.fixture
    def basic_config(self):
        """Basic chat node configuration."""
        return {
            "provider": "openai",
            "openai_model": "gpt-3.5-turbo",
            "temperature": 0.7,
            "max_tokens": 100,
            "system_prompt": "You are a helpful assistant.",
            "user_prompt_template": "{query}",
            "query": "Hello, how are you?",
            "_node_id": "test-chat-1",
        }
    
    @pytest.fixture
    def basic_inputs(self):
        """Basic inputs for chat node."""
        return {
            "query": "Test question"
        }
    
    @pytest.mark.asyncio
    async def test_openai_retry_on_rate_limit(self, chat_node, basic_config, basic_inputs):
        """Test that OpenAI API calls retry on rate limits."""
        
        with patch('backend.nodes.llm.chat.resolve_api_key', return_value="test-key"):
            with patch('backend.nodes.llm.chat.OpenAI') as mock_openai_class:
                # Create mock client and stream
                mock_client = Mock()
                mock_openai_class.return_value = mock_client
                
                # Create mock stream that raises rate limit error first, then succeeds
                call_count = 0
                
                def mock_stream_create(*args, **kwargs):
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
                        mock_chunk.choices[0].delta.content = "Hello! I'm doing well."
                        mock_chunk.usage = None
                        mock_stream.__iter__ = Mock(return_value=iter([mock_chunk]))
                        return mock_stream
                
                mock_client.chat.completions.create.side_effect = mock_stream_create
                
                # Mock the stream_* methods
                chat_node.stream_event = AsyncMock()
                chat_node.stream_progress = AsyncMock()
                chat_node.stream_output = AsyncMock()
                
                # Execute the chat node
                result = await chat_node.execute(basic_inputs, basic_config)
                
                # Verify retry occurred (should call API twice)
                assert mock_client.chat.completions.create.call_count == 2
                
                # Verify result is successful
                assert result["response"] == "Hello! I'm doing well."
                assert result["provider"] == "openai"
    
    @pytest.mark.asyncio
    async def test_openai_no_retry_on_auth_error(self, chat_node, basic_config, basic_inputs):
        """Test that OpenAI API calls don't retry on auth errors."""
        
        with patch('backend.nodes.llm.chat.resolve_api_key', return_value="test-key"):
            with patch('backend.nodes.llm.chat.OpenAI') as mock_openai_class:
                # Create mock client
                mock_client = Mock()
                mock_openai_class.return_value = mock_client
                
                # Mock API call that fails with auth error
                mock_client.chat.completions.create.side_effect = Exception("invalid api key")
                
                # Mock the stream_* methods
                chat_node.stream_event = AsyncMock()
                chat_node.stream_progress = AsyncMock()
                chat_node.stream_output = AsyncMock()
                
                # Execute should fail with non-retryable error
                with pytest.raises(NonRetryableError, match="invalid api key"):
                    await chat_node.execute(basic_inputs, basic_config)
                
                # Verify API was only called once (no retry)
                assert mock_client.chat.completions.create.call_count == 1
    
    @pytest.mark.asyncio
    async def test_anthropic_retry_on_rate_limit(self, chat_node, basic_config, basic_inputs):
        """Test that Anthropic API calls retry on rate limits."""
        # Update config for Anthropic
        anthropic_config = basic_config.copy()
        anthropic_config["provider"] = "anthropic"
        anthropic_config["anthropic_model"] = "claude-3-5-sonnet-20241022"
        
        with patch('backend.nodes.llm.chat.resolve_api_key', return_value="test-key"):
            with patch('backend.nodes.llm.chat.Anthropic') as mock_anthropic_class:
                # Create mock client
                mock_client = Mock()
                mock_anthropic_class.return_value = mock_client
                
                call_count = 0
                
                def mock_stream_create(*args, **kwargs):
                    nonlocal call_count
                    call_count += 1
                    
                    if call_count == 1:
                        # First call fails with rate limit
                        raise Exception("rate limit exceeded")
                    else:
                        # Second call succeeds
                        mock_stream_context = Mock()
                        mock_stream = Mock()
                        mock_stream.text_stream = ["Hello! ", "I'm doing well."]
                        
                        # Mock get_final_message
                        mock_message = Mock()
                        mock_usage = Mock()
                        mock_usage.input_tokens = 10
                        mock_usage.output_tokens = 15
                        mock_message.usage = mock_usage
                        mock_stream.get_final_message.return_value = mock_message
                        
                        mock_stream_context.__enter__ = Mock(return_value=mock_stream)
                        mock_stream_context.__exit__ = Mock(return_value=None)
                        return mock_stream_context
                
                mock_client.messages.stream.side_effect = mock_stream_create
                
                # Mock the stream_* methods
                chat_node.stream_event = AsyncMock()
                chat_node.stream_progress = AsyncMock()
                chat_node.stream_output = AsyncMock()
                
                # Execute the chat node
                result = await chat_node.execute(basic_inputs, anthropic_config)
                
                # Verify retry occurred (should call API twice)
                assert mock_client.messages.stream.call_count == 2
                
                # Verify result is successful
                assert result["response"] == "Hello! I'm doing well."
                assert result["provider"] == "anthropic"
    
    @pytest.mark.asyncio 
    async def test_anthropic_no_retry_on_auth_error(self, chat_node, basic_config, basic_inputs):
        """Test that Anthropic API calls don't retry on auth errors."""
        # Update config for Anthropic
        anthropic_config = basic_config.copy()
        anthropic_config["provider"] = "anthropic"
        
        with patch('backend.nodes.llm.chat.resolve_api_key', return_value="test-key"):
            with patch('backend.nodes.llm.chat.Anthropic') as mock_anthropic_class:
                # Create mock client
                mock_client = Mock()
                mock_anthropic_class.return_value = mock_client
                
                # Mock API call that fails with auth error
                mock_client.messages.stream.side_effect = Exception("unauthorized")
                
                # Mock the stream_* methods
                chat_node.stream_event = AsyncMock()
                chat_node.stream_progress = AsyncMock()
                chat_node.stream_output = AsyncMock()
                
                # Execute should fail with non-retryable error
                with pytest.raises(NonRetryableError, match="unauthorized"):
                    await chat_node.execute(basic_inputs, anthropic_config)
                
                # Verify API was only called once (no retry)
                assert mock_client.messages.stream.call_count == 1


class TestChatNodeBasicFunctionality:
    """Test basic Chat node functionality."""
    
    @pytest.fixture
    def chat_node(self):
        """Create a ChatNode instance for testing."""
        return ChatNode()
    
    @pytest.mark.asyncio
    async def test_template_rendering(self, chat_node):
        """Test template rendering with variables."""
        template = "Context: {context}\n\nQuestion: {query}\nAnswer:"
        inputs = {
            "context": "Test context information",
            "query": "What is this about?"
        }
        
        rendered = chat_node._render_template(template, inputs)
        
        expected = "Context: Test context information\n\nQuestion: What is this about?\nAnswer:"
        assert rendered == expected
    
    @pytest.mark.asyncio
    async def test_template_rendering_with_list_context(self, chat_node):
        """Test template rendering with list-based context."""
        template = "Context: {context}\n\nQuestion: {query}"
        inputs = {
            "context": [
                {"text": "First piece of info"},
                {"text": "Second piece of info"}
            ],
            "query": "What do you know?"
        }
        
        rendered = chat_node._render_template(template, inputs)
        
        assert "[1] First piece of info" in rendered
        assert "[2] Second piece of info" in rendered
        assert "What do you know?" in rendered
    
    @pytest.mark.asyncio
    async def test_template_rendering_with_results_input(self, chat_node):
        """Test template rendering with search results."""
        template = "Context: {context}\n\nQuestion: {query}"
        inputs = {
            "results": [
                {"text": "Result one"},
                {"text": "Result two"}
            ],
            "query": "What did you find?"
        }
        
        rendered = chat_node._render_template(template, inputs)
        
        # Should auto-format results as context
        assert "[1] Result one" in rendered
        assert "[2] Result two" in rendered
        assert "What did you find?" in rendered
    
    def test_node_metadata(self, chat_node):
        """Test chat node metadata."""
        assert chat_node.node_type == "chat"
        assert chat_node.name == "Chat"
        assert chat_node.category == "llm"
        assert "LLM providers" in chat_node.description
    
    @pytest.mark.asyncio
    async def test_unsupported_provider(self, chat_node):
        """Test error handling for unsupported provider."""
        config = {
            "provider": "unsupported_provider",
            "query": "Test"
        }
        inputs = {}
        
        with pytest.raises(ValueError, match="Unsupported LLM provider"):
            await chat_node.execute(inputs, config)


@pytest.mark.integration
class TestChatNodeIntegrationWithRetry:
    """Integration tests for Chat node with retry logic."""
    
    @pytest.fixture
    def chat_node(self):
        """Create a ChatNode instance for testing."""
        return ChatNode()
    
    @pytest.mark.asyncio
    async def test_retry_integration_with_logging(self, chat_node):
        """Test that retry logic integrates properly with logging."""
        config = {
            "provider": "openai",
            "openai_model": "gpt-3.5-turbo",
            "query": "Test query",
            "_node_id": "test-chat-1",
        }
        inputs = {"query": "Test"}
        
        with patch('backend.nodes.llm.chat.resolve_api_key', return_value="test-key"):
            with patch('backend.nodes.llm.chat.OpenAI') as mock_openai_class:
                mock_client = Mock()
                mock_openai_class.return_value = mock_client
                
                # Create a function that fails twice, then succeeds
                call_count = 0
                
                def mock_api_call(*args, **kwargs):
                    nonlocal call_count
                    call_count += 1
                    
                    if call_count <= 2:
                        raise Exception("rate limit exceeded")
                    else:
                        # Success case
                        mock_stream = Mock()
                        mock_chunk = Mock()
                        mock_chunk.choices = [Mock()]
                        mock_chunk.choices[0].delta.content = "Success after retry"
                        mock_chunk.usage = None
                        mock_stream.__iter__ = Mock(return_value=iter([mock_chunk]))
                        return mock_stream
                
                mock_client.chat.completions.create.side_effect = mock_api_call
                
                # Mock streaming methods
                chat_node.stream_event = AsyncMock()
                chat_node.stream_progress = AsyncMock()
                chat_node.stream_output = AsyncMock()
                
                # Execute and verify retry worked
                result = await chat_node.execute(inputs, config)
                
                # Should have retried 3 times total
                assert mock_client.chat.completions.create.call_count == 3
                assert result["response"] == "Success after retry"
    
    @pytest.mark.slow
    @pytest.mark.requires_api_key
    async def test_real_api_with_invalid_key(self, chat_node):
        """Test with real API but invalid key (should not retry)."""
        config = {
            "provider": "openai",
            "openai_model": "gpt-3.5-turbo",
            "openai_api_key": "invalid-key-12345",
            "query": "Test query",
            "_node_id": "test-chat-1",
        }
        inputs = {"query": "Test"}
        
        # Mock streaming methods
        chat_node.stream_event = AsyncMock()
        chat_node.stream_progress = AsyncMock()
        chat_node.stream_output = AsyncMock()
        
        # Should fail quickly without retries
        with pytest.raises(NonRetryableError):
            await chat_node.execute(inputs, config)