"""Utility modules for Tabcorp MCP Server enhancements.

Phase 1 Enhancements (Roadmap Oct 2025):
- retry_utils: Retry logic with exponential backoff
- cache_utils: LRU caching for 60% latency reduction
- circuit_breaker: Circuit breaker pattern for resilience
- enhanced_api: Drop-in HTTP client with all enhancements

Usage:
    from tab_mcp.utils import enhanced_bearer_get, enhanced_oauth_post
    
    # Automatic retry + circuit breaker + caching
    response = await enhanced_bearer_get(url, token)
"""

from .retry_utils import (
    retry_with_backoff,
    RetryConfig,
    MaxRetriesExceededError,
    API_RETRY_CONFIG,
    QUICK_RETRY_CONFIG,
    PERSISTENT_RETRY_CONFIG,
)

from .cache_utils import (
    cached_api_call,
    clear_cache,
    get_cache_stats,
    TTLCache,
    memoize,
)

from .circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerOpenError,
    CircuitBreakerConfig,
    CircuitState,
    get_circuit_breaker,
    circuit_breaker,
    get_all_circuit_stats,
    reset_all_circuits,
)

from .enhanced_api import (
    EnhancedHTTPClient,
    enhanced_oauth_post,
    enhanced_bearer_get,
    enhanced_bearer_post,
)

__all__ = [
    # Retry utilities
    'retry_with_backoff',
    'RetryConfig',
    'MaxRetriesExceededError',
    'API_RETRY_CONFIG',
    'QUICK_RETRY_CONFIG',
    'PERSISTENT_RETRY_CONFIG',
    # Cache utilities
    'cached_api_call',
    'clear_cache',
    'get_cache_stats',
    'TTLCache',
    'memoize',
    # Circuit breaker
    'CircuitBreaker',
    'CircuitBreakerOpenError',
    'CircuitBreakerConfig',
    'CircuitState',
    'get_circuit_breaker',
    'circuit_breaker',
    'get_all_circuit_stats',
    'reset_all_circuits',
    # Enhanced API
    'EnhancedHTTPClient',
    'enhanced_oauth_post',
    'enhanced_bearer_get',
    'enhanced_bearer_post',
]
