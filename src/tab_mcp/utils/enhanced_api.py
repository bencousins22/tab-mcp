"""Enhanced API wrapper with retry, caching, and circuit breaker.

Provides drop-in replacements for httpx calls with built-in resilience.
"""

import httpx
import logging
from typing import Any, Dict, Optional

from .retry_utils import retry_with_backoff, API_RETRY_CONFIG
from .cache_utils import cached_api_call
from .circuit_breaker import circuit_breaker, CircuitBreakerConfig

logger = logging.getLogger(__name__)

# Circuit breaker configuration for Tabcorp APIs
TABCORP_CIRCUIT_CONFIG = CircuitBreakerConfig(
    failure_threshold=5,
    success_threshold=2,
    timeout_seconds=60.0,
    half_open_max_calls=1
)


class EnhancedHTTPClient:
    """HTTP client with retry, caching, and circuit breaker."""
    
    def __init__(self, timeout: float = 30.0):
        """Initialize enhanced HTTP client.
        
        Args:
            timeout: Request timeout in seconds
        """
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None
        logger.info(f"EnhancedHTTPClient initialized with {timeout}s timeout")
    
    async def __aenter__(self):
        """Async context manager entry."""
        self._client = httpx.AsyncClient(timeout=self.timeout)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._client:
            await self._client.aclose()
    
    @retry_with_backoff(config=API_RETRY_CONFIG)
    @circuit_breaker('tabcorp_api', config=TABCORP_CIRCUIT_CONFIG)
    async def post(
        self,
        url: str,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> httpx.Response:
        """POST request with retry and circuit breaker.
        
        Args:
            url: Request URL
            data: POST data
            headers: Request headers
            **kwargs: Additional httpx arguments
            
        Returns:
            httpx.Response
        """
        if not self._client:
            raise RuntimeError("Client not initialized. Use async context manager.")
        
        logger.debug(f"Enhanced POST to {url}")
        response = await self._client.post(
            url,
            data=data,
            headers=headers,
            **kwargs
        )
        response.raise_for_status()
        return response
    
    @retry_with_backoff(config=API_RETRY_CONFIG)
    @circuit_breaker('tabcorp_api', config=TABCORP_CIRCUIT_CONFIG)
    @cached_api_call(cache_type='api', ttl_seconds=300)
    async def get(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> httpx.Response:
        """GET request with retry, circuit breaker, and caching.
        
        Args:
            url: Request URL
            headers: Request headers
            params: Query parameters
            **kwargs: Additional httpx arguments
            
        Returns:
            httpx.Response
        """
        if not self._client:
            raise RuntimeError("Client not initialized. Use async context manager.")
        
        logger.debug(f"Enhanced GET to {url}")
        response = await self._client.get(
            url,
            headers=headers,
            params=params,
            **kwargs
        )
        response.raise_for_status()
        return response


# Convenience functions for backward compatibility

@retry_with_backoff(config=API_RETRY_CONFIG)
@circuit_breaker('tabcorp_oauth', config=TABCORP_CIRCUIT_CONFIG)
async def enhanced_oauth_post(
    url: str,
    data: Dict[str, Any],
    headers: Optional[Dict[str, str]] = None,
    timeout: float = 30.0
) -> Dict[str, Any]:
    """OAuth POST with retry and circuit breaker.
    
    Args:
        url: OAuth endpoint URL
        data: Form data for OAuth request
        headers: Request headers
        timeout: Request timeout
        
    Returns:
        JSON response as dict
    """
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(url, data=data, headers=headers)
        response.raise_for_status()
        return response.json()


@retry_with_backoff(config=API_RETRY_CONFIG)
@circuit_breaker('tabcorp_api', config=TABCORP_CIRCUIT_CONFIG)
@cached_api_call(cache_type='api', ttl_seconds=300)
async def enhanced_bearer_get(
    url: str,
    token: str,
    params: Optional[Dict[str, Any]] = None,
    timeout: float = 30.0
) -> Dict[str, Any]:
    """Bearer token GET with retry, circuit breaker, and caching.
    
    Args:
        url: API endpoint URL
        token: Bearer token
        params: Query parameters
        timeout: Request timeout
        
    Returns:
        JSON response as dict
    """
    headers = {"Authorization": f"Bearer {token}"}
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()


@retry_with_backoff(config=API_RETRY_CONFIG)
@circuit_breaker('tabcorp_api', config=TABCORP_CIRCUIT_CONFIG)
async def enhanced_bearer_post(
    url: str,
    token: str,
    data: Optional[Dict[str, Any]] = None,
    timeout: float = 30.0
) -> Dict[str, Any]:
    """Bearer token POST with retry and circuit breaker.
    
    Args:
        url: API endpoint URL
        token: Bearer token
        data: POST data
        timeout: Request timeout
        
    Returns:
        JSON response as dict
    """
    headers = {"Authorization": f"Bearer {token}"}
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(url, headers=headers, json=data)
        response.raise_for_status()
        return response.json()
