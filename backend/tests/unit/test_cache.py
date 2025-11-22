"""
Unit tests for caching utilities
"""

import pytest
import time
from backend.core.cache import SimpleCache, CacheEntry, cache_key, cached


class TestCacheEntry:
    """Test CacheEntry class."""
    
    def test_cache_entry_not_expired(self):
        """Test cache entry that is not expired."""
        entry = CacheEntry("value", ttl_seconds=60)
        assert not entry.is_expired()
        assert entry.value == "value"
    
    def test_cache_entry_expired(self):
        """Test cache entry that is expired."""
        entry = CacheEntry("value", ttl_seconds=0.1)  # Very short TTL
        time.sleep(0.2)  # Wait for expiration
        assert entry.is_expired()


class TestSimpleCache:
    """Test SimpleCache class."""
    
    def test_get_set(self):
        """Test basic get and set operations."""
        cache = SimpleCache()
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"
    
    def test_get_nonexistent(self):
        """Test getting nonexistent key."""
        cache = SimpleCache()
        assert cache.get("nonexistent") is None
    
    def test_expiration(self):
        """Test cache entry expiration."""
        cache = SimpleCache()
        cache.set("key1", "value1", ttl_seconds=0.1)
        assert cache.get("key1") == "value1"
        time.sleep(0.2)
        assert cache.get("key1") is None
    
    def test_delete(self):
        """Test deleting cache entry."""
        cache = SimpleCache()
        cache.set("key1", "value1")
        cache.delete("key1")
        assert cache.get("key1") is None
    
    def test_clear(self):
        """Test clearing all cache entries."""
        cache = SimpleCache()
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.clear()
        assert cache.get("key1") is None
        assert cache.get("key2") is None
        assert cache.size() == 0


class TestCacheKey:
    """Test cache key generation."""
    
    def test_cache_key_same_args(self):
        """Test that same arguments generate same key."""
        key1 = cache_key("arg1", "arg2", kwarg1="value1")
        key2 = cache_key("arg1", "arg2", kwarg1="value1")
        assert key1 == key2
    
    def test_cache_key_different_args(self):
        """Test that different arguments generate different keys."""
        key1 = cache_key("arg1", "arg2")
        key2 = cache_key("arg1", "arg3")
        assert key1 != key2


class TestCachedDecorator:
    """Test @cached decorator."""
    
    def test_cached_sync_function(self):
        """Test caching a synchronous function."""
        call_count = 0
        
        @cached(ttl_seconds=60)
        def test_func(x, y):
            nonlocal call_count
            call_count += 1
            return x + y
        
        # First call should execute function
        result1 = test_func(1, 2)
        assert result1 == 3
        assert call_count == 1
        
        # Second call should use cache
        result2 = test_func(1, 2)
        assert result2 == 3
        assert call_count == 1  # Should not increment
    
    def test_cached_different_args(self):
        """Test that different arguments don't use cache."""
        call_count = 0
        
        @cached(ttl_seconds=60)
        def test_func(x):
            nonlocal call_count
            call_count += 1
            return x * 2
        
        test_func(1)
        test_func(2)  # Different argument
        assert call_count == 2  # Should call twice

