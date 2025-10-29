"""Caching utilities for performance optimization.

Provides in-memory LRU cache with TTL support for API responses.
Target: 60% latency reduction and 75% cache hit rate.
"""

import asyncio
import logging
import time
from typing import Any, Callable, Optional, TypeVar, Dict, Tuple
from functools import wraps, lru_cache
from collections import OrderedDict
import hashlib
import json

logger = logging.getLogger(__name__)

T = TypeVar('T')


class TTLCache:
    """Thread-safe LRU cache with Time-To-Live (TTL) support."""
    
    def __init__(self, maxsize: int = 128, ttl_seconds: float = 300.0):
        """Initialize cache.
        
        Args:
            maxsize: Maximum number of items to cache
            ttl_seconds: Time-to-live for cached items in seconds
        """
        self.maxsize = maxsize
        self.ttl_seconds = ttl_seconds
        self._cache: OrderedDict[str, Tuple[Any, float]] = OrderedDict()
        self._hits = 0
        self._misses = 0
        self._lock = asyncio.Lock()
        
    async def get(self, key: str) -> Optional[Any]:
        """Get item from cache if exists and not expired."""
        async with self._lock:
            if key in self._cache:
                value, timestamp = self._cache[key]
                
                # Check if expired
                if time.time() - timestamp > self.ttl_seconds:
                    del self._cache[key]
                    self._misses += 1
                    logger.debug(f"Cache expired for key: {key}")
                    return None
                
                # Move to end (most recently used)
                self._cache.move_to_end(key)
                self._hits += 1
                logger.debug(f"Cache hit for key: {key}")
                return value
            
            self._misses += 1
            logger.debug(f"Cache miss for key: {key}")
            return None
    
    async def set(self, key: str, value: Any) -> None:
        """Set item in cache with current timestamp."""
        async with self._lock:
            # Remove oldest item if at capacity
            if len(self._cache) >= self.maxsize and key not in self._cache:
                oldest_key = next(iter(self._cache))
                del self._cache[oldest_key]
                logger.debug(f"Cache full, evicted: {oldest_key}")
            
            self._cache[key] = (value, time.time())
            self._cache.move_to_end(key)
            logger.debug(f"Cache set for key: {key}")
    
    async def clear(self) -> None:
        """Clear all cached items."""
        async with self._lock:
            self._cache.clear()
            logger.info("Cache cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_requests = self._hits + self._misses
        hit_rate = (self._hits / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'size': len(self._cache),
            'maxsize': self.maxsize,
            'hits': self._hits,
            'misses': self._misses,
            'hit_rate': f"{hit_rate:.2f}%",
            'ttl_seconds': self.ttl_seconds
        }


# Global cache instances for different use cases
_api_cache = TTLCache(maxsize=256, ttl_seconds=300.0)  # 5 minutes
_token_cache = TTLCache(maxsize=10, ttl_seconds=1800.0)  # 30 minutes
_race_cache = TTLCache(maxsize=512, ttl_seconds=60.0)  # 1 minute (racing data changes frequently)


def _generate_cache_key(func_name: str, args: tuple, kwargs: dict) -> str:
    """Generate unique cache key from function name and arguments."""
    # Create deterministic string from args and kwargs
    key_parts = [func_name]
    
    # Add args
    for arg in args:
        if isinstance(arg, (str, int, float, bool)):
            key_parts.append(str(arg))
        else:
            # For complex objects, use their string representation
            key_parts.append(str(arg))
    
    # Add kwargs in sorted order for consistency
    for k in sorted(kwargs.keys()):
        v = kwargs[k]
        if isinstance(v, (str, int, float, bool)):
            key_parts.append(f"{k}={v}")
        else:
            key_parts.append(f"{k}={str(v)}")
    
    # Generate hash for compact key
    key_string = "|".join(key_parts)
    key_hash = hashlib.md5(key_string.encode()).hexdigest()
    
    return f"{func_name}:{key_hash}"


def cached_api_call(
    cache_type: str = 'api',
    ttl_seconds: Optional[float] = None,
    maxsize: Optional[int] = None
):
    """Decorator to cache API call results.
    
    Args:
        cache_type: Type of cache to use ('api', 'token', 'race')
        ttl_seconds: Override default TTL for this cached function
        maxsize: Override default maxsize for this cached function
        
    Example:
        @cached_api_call(cache_type='race', ttl_seconds=30)
        async def get_race_results(race_id: str):
            return await api.fetch_results(race_id)
    """
    # Select cache based on type
    cache_map = {
        'api': _api_cache,
        'token': _token_cache,
        'race': _race_cache
    }
    
    cache = cache_map.get(cache_type, _api_cache)
    
    # Create custom cache if parameters specified
    if ttl_seconds is not None or maxsize is not None:
        cache = TTLCache(
            maxsize=maxsize or cache.maxsize,
            ttl_seconds=ttl_seconds or cache.ttl_seconds
        )
    
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            # Generate cache key
            cache_key = _generate_cache_key(func.__name__, args, kwargs)
            
            # Try to get from cache
            cached_value = await cache.get(cache_key)
            if cached_value is not None:
                logger.info(f"Cache hit for {func.__name__}")
                return cached_value
            
            # Cache miss - execute function
            logger.info(f"Cache miss for {func.__name__} - executing")
            result = await func(*args, **kwargs)
            
            # Store in cache
            await cache.set(cache_key, result)
            
            return result
        
        return wrapper
    
    return decorator


async def clear_cache(cache_type: Optional[str] = None) -> None:
    """Clear cache(s).
    
    Args:
        cache_type: Specific cache to clear ('api', 'token', 'race'), or None for all
    """
    if cache_type is None:
        # Clear all caches
        await _api_cache.clear()
        await _token_cache.clear()
        await _race_cache.clear()
        logger.info("All caches cleared")
    else:
        cache_map = {
            'api': _api_cache,
            'token': _token_cache,
            'race': _race_cache
        }
        
        if cache_type in cache_map:
            await cache_map[cache_type].clear()
            logger.info(f"{cache_type} cache cleared")


def get_cache_stats(cache_type: Optional[str] = None) -> Dict[str, Any]:
    """Get cache statistics.
    
    Args:
        cache_type: Specific cache stats ('api', 'token', 'race'), or None for all
        
    Returns:
        Dictionary with cache statistics
    """
    if cache_type is None:
        # Return stats for all caches
        return {
            'api': _api_cache.get_stats(),
            'token': _token_cache.get_stats(),
            'race': _race_cache.get_stats()
        }
    
    cache_map = {
        'api': _api_cache,
        'token': _token_cache,
        'race': _race_cache
    }
    
    if cache_type in cache_map:
        return cache_map[cache_type].get_stats()
    
    return {}


# Convenience function for simple memoization
def memoize(func: Callable[..., T]) -> Callable[..., T]:
    """Simple memoization decorator using functools.lru_cache.
    
    Use for pure functions without I/O.
    """
    return lru_cache(maxsize=128)(func)
