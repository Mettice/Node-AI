"""
Unit tests for retry logic utility
"""

import pytest
import asyncio
import time
from unittest.mock import AsyncMock, Mock
from backend.utils.retry import (
    retry_with_backoff,
    retry_with_backoff_sync,
    RetryableError,
    NonRetryableError,
    classify_http_error,
    classify_openai_error,
    classify_anthropic_error,
    retry,
)


class TestRetryLogic:
    """Test retry utility functions."""
    
    @pytest.mark.asyncio
    async def test_retry_with_backoff_success_on_retry(self):
        """Test that retryable errors eventually succeed."""
        call_count = 0
        
        async def failing_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise RetryableError("Temporary failure")
            return "success"
        
        result = await retry_with_backoff(
            failing_function,
            max_retries=3,
            initial_delay=0.01,  # Fast for testing
        )
        
        assert result == "success"
        assert call_count == 3
    
    @pytest.mark.asyncio
    async def test_retry_with_backoff_non_retryable_immediate_fail(self):
        """Test that non-retryable errors fail immediately."""
        call_count = 0
        
        async def non_retryable_function():
            nonlocal call_count
            call_count += 1
            raise NonRetryableError("Invalid API key")
        
        with pytest.raises(NonRetryableError, match="Invalid API key"):
            await retry_with_backoff(
                non_retryable_function,
                max_retries=3,
                initial_delay=0.01,
            )
        
        assert call_count == 1  # Should only try once
    
    @pytest.mark.asyncio
    async def test_retry_with_backoff_max_retries_exceeded(self):
        """Test that function fails after max retries."""
        call_count = 0
        
        async def always_failing_function():
            nonlocal call_count
            call_count += 1
            raise RetryableError("Always fails")
        
        with pytest.raises(RetryableError, match="Always fails"):
            await retry_with_backoff(
                always_failing_function,
                max_retries=2,  # 3 total attempts
                initial_delay=0.01,
            )
        
        assert call_count == 3  # Initial + 2 retries
    
    def test_retry_with_backoff_sync_success(self):
        """Test synchronous retry function."""
        call_count = 0
        
        def failing_sync_function():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise RetryableError("Sync failure")
            return "sync_success"
        
        result = retry_with_backoff_sync(
            failing_sync_function,
            max_retries=2,
            initial_delay=0.01,
        )
        
        assert result == "sync_success"
        assert call_count == 2
    
    @pytest.mark.asyncio
    async def test_retry_decorator_async(self):
        """Test retry decorator with async function."""
        call_count = 0
        
        @retry(max_retries=2, initial_delay=0.01)
        async def decorated_async_function():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise RetryableError("Decorator test")
            return "decorated_success"
        
        result = await decorated_async_function()
        assert result == "decorated_success"
        assert call_count == 2
    
    def test_retry_decorator_sync(self):
        """Test retry decorator with sync function."""
        call_count = 0
        
        @retry(max_retries=1, initial_delay=0.01)
        def decorated_sync_function():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise RetryableError("Sync decorator test")
            return "sync_decorated_success"
        
        result = decorated_sync_function()
        assert result == "sync_decorated_success"
        assert call_count == 2


class TestErrorClassification:
    """Test error classification functions."""
    
    def test_classify_http_error_retryable(self):
        """Test retryable HTTP errors."""
        # Rate limiting
        error = classify_http_error(429, "Too Many Requests")
        assert isinstance(error, RetryableError)
        assert "429" in str(error)
        
        # Server errors
        for status_code in [500, 502, 503, 504]:
            error = classify_http_error(status_code, "Server Error")
            assert isinstance(error, RetryableError)
            assert str(status_code) in str(error)
    
    def test_classify_http_error_non_retryable(self):
        """Test non-retryable HTTP errors."""
        # Client errors
        for status_code in [400, 401, 403, 404, 422]:
            error = classify_http_error(status_code, "Client Error")
            assert isinstance(error, NonRetryableError)
            assert str(status_code) in str(error)
    
    def test_classify_openai_error_retryable(self):
        """Test OpenAI error classification for retryable errors."""
        retryable_errors = [
            "rate limit exceeded",
            "rate_limit_exceeded",
            "connection timeout",
            "network error",
            "server error",
        ]
        
        for error_msg in retryable_errors:
            error = classify_openai_error(error_msg)
            assert isinstance(error, RetryableError)
            assert "OpenAI" in str(error)
    
    def test_classify_openai_error_non_retryable(self):
        """Test OpenAI error classification for non-retryable errors."""
        non_retryable_errors = [
            "invalid api key",
            "unauthorized",
            "invalid request",
            "bad request",
            "model not found",
        ]
        
        for error_msg in non_retryable_errors:
            error = classify_openai_error(error_msg)
            assert isinstance(error, NonRetryableError)
            assert "OpenAI" in str(error)
    
    def test_classify_anthropic_error_retryable(self):
        """Test Anthropic error classification for retryable errors."""
        retryable_errors = [
            "rate limit exceeded",
            "timeout",
            "connection error",
        ]
        
        for error_msg in retryable_errors:
            error = classify_anthropic_error(error_msg)
            assert isinstance(error, RetryableError)
            assert "Anthropic" in str(error)
    
    def test_classify_anthropic_error_non_retryable(self):
        """Test Anthropic error classification for non-retryable errors."""
        non_retryable_errors = [
            "invalid api key",
            "unauthorized",
            "bad request",
        ]
        
        for error_msg in non_retryable_errors:
            error = classify_anthropic_error(error_msg)
            assert isinstance(error, NonRetryableError)
            assert "Anthropic" in str(error)


class TestRetryTiming:
    """Test retry timing and exponential backoff."""
    
    @pytest.mark.asyncio
    async def test_exponential_backoff_timing(self):
        """Test exponential backoff timing."""
        attempt_times = []
        call_count = 0
        
        async def timing_test_function():
            nonlocal call_count
            call_count += 1
            attempt_times.append(time.time())
            raise RetryableError("Timing test")
        
        start_time = time.time()
        
        try:
            await retry_with_backoff(
                timing_test_function,
                max_retries=3,
                initial_delay=0.1,
                exponential_base=2.0,
                jitter=False,  # Disable jitter for predictable timing
            )
        except RetryableError:
            pass  # Expected
        
        # Verify timing between attempts
        if len(attempt_times) >= 3:
            delay1 = attempt_times[1] - attempt_times[0]
            delay2 = attempt_times[2] - attempt_times[1]
            
            # Allow some tolerance for timing
            assert 0.08 <= delay1 <= 0.12, f"First delay should be ~0.1s, got {delay1:.3f}s"
            assert 0.18 <= delay2 <= 0.22, f"Second delay should be ~0.2s, got {delay2:.3f}s"
    
    @pytest.mark.asyncio
    async def test_max_delay_limit(self):
        """Test that delays don't exceed max_delay."""
        attempt_times = []
        
        async def max_delay_test_function():
            attempt_times.append(time.time())
            raise RetryableError("Max delay test")
        
        try:
            await retry_with_backoff(
                max_delay_test_function,
                max_retries=3,
                initial_delay=0.1,
                max_delay=0.15,  # Very low max delay
                exponential_base=10.0,  # High exponential
                jitter=False,
            )
        except RetryableError:
            pass  # Expected
        
        # Check that no delay exceeds max_delay
        if len(attempt_times) >= 2:
            for i in range(1, len(attempt_times)):
                delay = attempt_times[i] - attempt_times[i-1]
                assert delay <= 0.17, f"Delay {delay:.3f}s exceeds max_delay + tolerance"


@pytest.mark.unit
class TestRetryEdgeCases:
    """Test edge cases and error conditions."""
    
    @pytest.mark.asyncio
    async def test_zero_retries(self):
        """Test with zero retries (only one attempt)."""
        call_count = 0
        
        async def single_attempt_function():
            nonlocal call_count
            call_count += 1
            raise RetryableError("Should not retry")
        
        with pytest.raises(RetryableError):
            await retry_with_backoff(
                single_attempt_function,
                max_retries=0,  # No retries
                initial_delay=0.01,
            )
        
        assert call_count == 1
    
    @pytest.mark.asyncio
    async def test_function_succeeds_immediately(self):
        """Test function that succeeds on first attempt."""
        call_count = 0
        
        async def immediate_success_function():
            nonlocal call_count
            call_count += 1
            return "immediate_success"
        
        result = await retry_with_backoff(
            immediate_success_function,
            max_retries=3,
            initial_delay=0.01,
        )
        
        assert result == "immediate_success"
        assert call_count == 1  # Should only call once
    
    def test_error_classification_unknown_errors(self):
        """Test that unknown errors default to retryable."""
        # Unknown HTTP status code
        error = classify_http_error(418, "I'm a teapot")
        assert isinstance(error, RetryableError)  # Default to retryable
        
        # Unknown OpenAI error
        error = classify_openai_error("unknown openai error")
        assert isinstance(error, RetryableError)  # Default to retryable
        
        # Unknown Anthropic error
        error = classify_anthropic_error("unknown anthropic error")
        assert isinstance(error, RetryableError)  # Default to retryable