"""Retry utilities with exponential backoff for resilient API calls.

Provides configurable retry logic to handle transient failures gracefully.
"""

import asyncio
import logging
from typing import TypeVar, Callable, Any, Optional
from dataclasses import dataclass
from functools import wraps

logger = logging.getLogger(__name__)

T = TypeVar('T')


@dataclass
class RetryConfig:
    """Configuration for retry behavior."""
    max_attempts: int = 3
    initial_delay: float = 1.0  # seconds
    max_delay: float = 10.0     # seconds
    exponential_base: float = 2.0
    retry_on: tuple = (Exception,)
    

class MaxRetriesExceededError(Exception):
    """Raised when maximum retry attempts are exhausted."""
    pass


def retry_with_backoff(config: Optional[RetryConfig] = None):
    """Decorator that retries a function with exponential backoff.
    
    Args:
        config: RetryConfig instance with retry parameters
        
    Returns:
        Decorated function with retry logic
        
    Example:
        @retry_with_backoff(RetryConfig(max_attempts=3))
        async def fetch_data():
            return await api_call()
    """
    if config is None:
        config = RetryConfig()
    
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> T:
            last_exception = None
            delay = config.initial_delay
            
            for attempt in range(1, config.max_attempts + 1):
                try:
                    logger.debug(
                        f"Attempt {attempt}/{config.max_attempts} for {func.__name__}"
                    )
                    return await func(*args, **kwargs)
                    
                except config.retry_on as e:
                    last_exception = e
                    
                    if attempt == config.max_attempts:
                        logger.error(
                            f"Max retries ({config.max_attempts}) exceeded for {func.__name__}: {str(e)}"
                        )
                        raise MaxRetriesExceededError(
                            f"Failed after {config.max_attempts} attempts: {str(e)}"
                        ) from e
                    
                    # Calculate next delay with exponential backoff
                    logger.warning(
                        f"Attempt {attempt} failed for {func.__name__}: {str(e)}. "
                        f"Retrying in {delay:.1f}s..."
                    )
                    
                    await asyncio.sleep(delay)
                    delay = min(delay * config.exponential_base, config.max_delay)
                    
            # Should never reach here, but for type safety
            if last_exception:
                raise last_exception
                
        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> T:
            last_exception = None
            delay = config.initial_delay
            
            for attempt in range(1, config.max_attempts + 1):
                try:
                    logger.debug(
                        f"Attempt {attempt}/{config.max_attempts} for {func.__name__}"
                    )
                    return func(*args, **kwargs)
                    
                except config.retry_on as e:
                    last_exception = e
                    
                    if attempt == config.max_attempts:
                        logger.error(
                            f"Max retries ({config.max_attempts}) exceeded for {func.__name__}: {str(e)}"
                        )
                        raise MaxRetriesExceededError(
                            f"Failed after {config.max_attempts} attempts: {str(e)}"
                        ) from e
                    
                    logger.warning(
                        f"Attempt {attempt} failed for {func.__name__}: {str(e)}. "
                        f"Retrying in {delay:.1f}s..."
                    )
                    
                    import time
                    time.sleep(delay)
                    delay = min(delay * config.exponential_base, config.max_delay)
                    
            if last_exception:
                raise last_exception
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
            
    return decorator


# Convenience configurations for common use cases
API_RETRY_CONFIG = RetryConfig(
    max_attempts=3,
    initial_delay=1.0,
    max_delay=4.0,
    exponential_base=2.0,
    retry_on=(ConnectionError, TimeoutError, Exception)
)

QUICK_RETRY_CONFIG = RetryConfig(
    max_attempts=2,
    initial_delay=0.5,
    max_delay=2.0,
    exponential_base=2.0,
)

PERSISTENT_RETRY_CONFIG = RetryConfig(
    max_attempts=5,
    initial_delay=2.0,
    max_delay=30.0,
    exponential_base=2.0,
)
