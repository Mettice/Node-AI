"""
Caching utilities for performance optimization.

Provides in-memory caching for frequently accessed data.
In production, this should be replaced with Redis or similar.
"""

from typing import Any, Optional, Callable
from datetime import datetime, timedelta
from functools import wraps
import hashlib
import json

from backend.utils.logger import get_logger

logger = get_logger(__name__)


class CacheEntry:
    """A cache entry with expiration."""
    
    def __init__(self, value: Any, ttl_seconds: int = 300):
        self.value = value
        self.created_at = datetime.now()
        self.ttl_seconds = ttl_seconds
    
    def is_expired(self) -> bool:
        """Check if cache entry is expired."""
        age = (datetime.now() - self.created_at).total_seconds()
        return age > self.ttl_seconds


class SimpleCache:
    """Simple in-memory cache with TTL."""
    
    def __init__(self):
        self._cache: dict[str, CacheEntry] = {}
        self._max_size = 1000  # Maximum number of entries
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get a value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value if found and not expired, None otherwise
        """
        entry = self._cache.get(key)
        if entry is None:
            return None
        
        if entry.is_expired():
            del self._cache[key]
            return None
        
        return entry.value
    
    def set(self, key: str, value: Any, ttl_seconds: int = 300):
        """
        Set a value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl_seconds: Time to live in seconds (default: 5 minutes)
        """
        # Evict oldest entries if cache is full
        if len(self._cache) >= self._max_size:
            # Remove expired entries first
            expired_keys = [
                k for k, v in self._cache.items()
                if v.is_expired()
            ]
            for k in expired_keys:
                del self._cache[k]
            
            # If still full, remove oldest 10% of entries
            if len(self._cache) >= self._max_size:
                sorted_entries = sorted(
                    self._cache.items(),
                    key=lambda x: x[1].created_at
                )
                to_remove = int(self._max_size * 0.1)
                for k, _ in sorted_entries[:to_remove]:
                    del self._cache[k]
        
        self._cache[key] = CacheEntry(value, ttl_seconds)
    
    def delete(self, key: str):
        """Delete a key from cache."""
        self._cache.pop(key, None)
    
    def clear(self):
        """Clear all cache entries."""
        self._cache.clear()
    
    def size(self) -> int:
        """Get current cache size."""
        return len(self._cache)


# Global cache instance
_cache = SimpleCache()


def cache_key(*args, **kwargs) -> str:
    """
    Generate a cache key from function arguments.
    
    Args:
        *args: Positional arguments
        **kwargs: Keyword arguments
        
    Returns:
        Cache key string
    """
    # Create a hash of the arguments
    key_data = {
        "args": args,
        "kwargs": sorted(kwargs.items()),
    }
    key_str = json.dumps(key_data, sort_keys=True, default=str)
    return hashlib.md5(key_str.encode()).hexdigest()


def cached(ttl_seconds: int = 300, key_prefix: str = ""):
    """
    Decorator to cache function results.
    
    Args:
        ttl_seconds: Time to live in seconds
        key_prefix: Prefix for cache key
        
    Example:
        @cached(ttl_seconds=600)
        def expensive_function(arg1, arg2):
            # ... expensive computation
            return result
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            key = f"{key_prefix}:{func.__name__}:{cache_key(*args, **kwargs)}"
            cached_value = _cache.get(key)
            if cached_value is not None:
                logger.debug(f"Cache hit: {key}")
                return cached_value
            
            result = await func(*args, **kwargs)
            _cache.set(key, result, ttl_seconds)
            logger.debug(f"Cache miss: {key}")
            return result
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            key = f"{key_prefix}:{func.__name__}:{cache_key(*args, **kwargs)}"
            cached_value = _cache.get(key)
            if cached_value is not None:
                logger.debug(f"Cache hit: {key}")
                return cached_value
            
            result = func(*args, **kwargs)
            _cache.set(key, result, ttl_seconds)
            logger.debug(f"Cache miss: {key}")
            return result
        
        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


def get_cache() -> SimpleCache:
    """Get the global cache instance."""
    return _cache

