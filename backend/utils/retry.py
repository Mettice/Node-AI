"""
Retry utility with exponential backoff.

This module provides robust retry logic for external API calls, especially useful
for LLM providers (OpenAI, Anthropic, etc.) that may have temporary failures.
"""

import asyncio
import random
import time
from typing import Callable, TypeVar, Optional, Union, Any
from functools import wraps

from backend.utils.logger import get_logger

logger = get_logger(__name__)

T = TypeVar('T')


class RetryableError(Exception):
    """Error that should trigger a retry."""
    pass


class NonRetryableError(Exception):
    """Error that should NOT trigger a retry (e.g., invalid API key, bad request)."""
    pass


async def retry_with_backoff(
    func: Callable,
    max_retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
) -> T:
    """
    Retry an async function with exponential backoff.
    
    Args:
        func: Async function to retry
        max_retries: Maximum number of retries (default: 3)
        initial_delay: Initial delay in seconds (default: 1.0)
        max_delay: Maximum delay in seconds (default: 60.0)
        exponential_base: Base for exponential backoff (default: 2.0)
        jitter: Add random jitter to delay (default: True)
    
    Returns:
        Result of function call
    
    Raises:
        Last exception if all retries fail
        NonRetryableError: Immediately if non-retryable error occurs
    
    Example:
        async def api_call():
            # Your API call here
            response = await httpx.get("https://api.example.com/data")
            if response.status_code == 429:
                raise RetryableError("Rate limited")
            elif response.status_code == 401:
                raise NonRetryableError("Invalid API key")
            return response.json()
        
        result = await retry_with_backoff(api_call, max_retries=3)
    """
    last_exception = None
    
    for attempt in range(max_retries + 1):
        try:
            logger.debug(f"Attempt {attempt + 1}/{max_retries + 1} for {func.__name__}")
            return await func()
        
        except NonRetryableError as e:
            # Don't retry non-retryable errors
            logger.warning(f"Non-retryable error in {func.__name__}: {e}")
            raise
        
        except Exception as e:
            last_exception = e
            
            # Don't retry on last attempt
            if attempt == max_retries:
                break
            
            # Calculate delay with exponential backoff
            delay = min(
                initial_delay * (exponential_base ** attempt),
                max_delay
            )
            
            # Add jitter to prevent thundering herd
            if jitter:
                delay = delay * (0.5 + random.random() * 0.5)
            
            logger.warning(
                f"Attempt {attempt + 1} failed for {func.__name__}: {e}. "
                f"Retrying in {delay:.2f}s..."
            )
            
            # Wait before retrying
            await asyncio.sleep(delay)
    
    # All retries failed
    logger.error(f"All {max_retries + 1} attempts failed for {func.__name__}: {last_exception}")
    raise last_exception


def retry_with_backoff_sync(
    func: Callable,
    max_retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
) -> T:
    """
    Retry a synchronous function with exponential backoff.
    
    Args:
        func: Synchronous function to retry
        max_retries: Maximum number of retries (default: 3)
        initial_delay: Initial delay in seconds (default: 1.0)
        max_delay: Maximum delay in seconds (default: 60.0)
        exponential_base: Base for exponential backoff (default: 2.0)
        jitter: Add random jitter to delay (default: True)
    
    Returns:
        Result of function call
    
    Raises:
        Last exception if all retries fail
        NonRetryableError: Immediately if non-retryable error occurs
    """
    last_exception = None
    
    for attempt in range(max_retries + 1):
        try:
            logger.debug(f"Attempt {attempt + 1}/{max_retries + 1} for {func.__name__}")
            return func()
        
        except NonRetryableError as e:
            # Don't retry non-retryable errors
            logger.warning(f"Non-retryable error in {func.__name__}: {e}")
            raise
        
        except Exception as e:
            last_exception = e
            
            # Don't retry on last attempt
            if attempt == max_retries:
                break
            
            # Calculate delay with exponential backoff
            delay = min(
                initial_delay * (exponential_base ** attempt),
                max_delay
            )
            
            # Add jitter to prevent thundering herd
            if jitter:
                delay = delay * (0.5 + random.random() * 0.5)
            
            logger.warning(
                f"Attempt {attempt + 1} failed for {func.__name__}: {e}. "
                f"Retrying in {delay:.2f}s..."
            )
            
            # Wait before retrying
            time.sleep(delay)
    
    # All retries failed
    logger.error(f"All {max_retries + 1} attempts failed for {func.__name__}: {last_exception}")
    raise last_exception


def retry(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
):
    """
    Decorator for adding retry logic to functions.
    
    Args:
        max_retries: Maximum number of retries (default: 3)
        initial_delay: Initial delay in seconds (default: 1.0)
        max_delay: Maximum delay in seconds (default: 60.0)
        exponential_base: Base for exponential backoff (default: 2.0)
        jitter: Add random jitter to delay (default: True)
    
    Example:
        @retry(max_retries=3, initial_delay=1.0)
        async def call_openai_api():
            # Your API call here
            pass
        
        @retry(max_retries=2, initial_delay=0.5)
        def call_sync_api():
            # Your synchronous API call here
            pass
    """
    def decorator(func: Callable) -> Callable:
        if asyncio.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                async def wrapped_func():
                    return await func(*args, **kwargs)
                
                return await retry_with_backoff(
                    wrapped_func,
                    max_retries=max_retries,
                    initial_delay=initial_delay,
                    max_delay=max_delay,
                    exponential_base=exponential_base,
                    jitter=jitter,
                )
            
            return async_wrapper
        else:
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                def wrapped_func():
                    return func(*args, **kwargs)
                
                return retry_with_backoff_sync(
                    wrapped_func,
                    max_retries=max_retries,
                    initial_delay=initial_delay,
                    max_delay=max_delay,
                    exponential_base=exponential_base,
                    jitter=jitter,
                )
            
            return sync_wrapper
    
    return decorator


def classify_http_error(status_code: int, error_message: str = "") -> Union[RetryableError, NonRetryableError]:
    """
    Classify HTTP errors as retryable or non-retryable.
    
    Args:
        status_code: HTTP status code
        error_message: Error message (optional)
    
    Returns:
        RetryableError or NonRetryableError instance
    
    Retryable errors (temporary issues):
        - 429 (Rate Limited)
        - 500 (Internal Server Error)
        - 502 (Bad Gateway)
        - 503 (Service Unavailable)
        - 504 (Gateway Timeout)
        - Network timeouts/connection errors
    
    Non-retryable errors (permanent issues):
        - 400 (Bad Request)
        - 401 (Unauthorized)
        - 403 (Forbidden)
        - 404 (Not Found)
        - 422 (Unprocessable Entity)
    """
    retryable_status_codes = {429, 500, 502, 503, 504}
    non_retryable_status_codes = {400, 401, 403, 404, 422}
    
    error_msg = f"HTTP {status_code}: {error_message}" if error_message else f"HTTP {status_code}"
    
    if status_code in retryable_status_codes:
        return RetryableError(error_msg)
    elif status_code in non_retryable_status_codes:
        return NonRetryableError(error_msg)
    else:
        # Default to retryable for unknown status codes
        return RetryableError(error_msg)


def classify_openai_error(error) -> Union[RetryableError, NonRetryableError]:
    """
    Classify OpenAI-specific errors as retryable or non-retryable.
    
    Args:
        error: OpenAI error object or exception
    
    Returns:
        RetryableError or NonRetryableError instance
    """
    error_str = str(error).lower()
    
    # Check for specific OpenAI error patterns
    if "rate limit" in error_str or "rate_limit" in error_str:
        return RetryableError(f"OpenAI rate limit: {error}")
    elif "timeout" in error_str or "connection" in error_str:
        return RetryableError(f"OpenAI connection issue: {error}")
    elif "invalid api key" in error_str or "unauthorized" in error_str:
        return NonRetryableError(f"OpenAI authentication error: {error}")
    elif "invalid request" in error_str or "bad request" in error_str:
        return NonRetryableError(f"OpenAI request error: {error}")
    elif "model not found" in error_str:
        return NonRetryableError(f"OpenAI model error: {error}")
    else:
        # Default to retryable for unknown OpenAI errors
        return RetryableError(f"OpenAI error: {error}")


def classify_anthropic_error(error) -> Union[RetryableError, NonRetryableError]:
    """
    Classify Anthropic-specific errors as retryable or non-retryable.
    
    Args:
        error: Anthropic error object or exception
    
    Returns:
        RetryableError or NonRetryableError instance
    """
    error_str = str(error).lower()
    
    # Check for specific Anthropic error patterns
    if "rate limit" in error_str or "rate_limit" in error_str:
        return RetryableError(f"Anthropic rate limit: {error}")
    elif "timeout" in error_str or "connection" in error_str:
        return RetryableError(f"Anthropic connection issue: {error}")
    elif "invalid api key" in error_str or "unauthorized" in error_str:
        return NonRetryableError(f"Anthropic authentication error: {error}")
    elif "invalid request" in error_str or "bad request" in error_str:
        return NonRetryableError(f"Anthropic request error: {error}")
    else:
        # Default to retryable for unknown Anthropic errors
        return RetryableError(f"Anthropic error: {error}")