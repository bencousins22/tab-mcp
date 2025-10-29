"""Circuit breaker pattern implementation for resilience.

Prevents cascading failures by temporarily blocking calls to failing services.
"""

import asyncio
import logging
import time
from enum import Enum
from typing import Callable, Optional, TypeVar, Any
from functools import wraps
from dataclasses import dataclass

logger = logging.getLogger(__name__)

T = TypeVar('T')


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation, requests pass through
    OPEN = "open"          # Circuit broken, requests fail fast
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open and blocks request."""
    pass


@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration."""
    failure_threshold: int = 5          # Failures before opening circuit
    success_threshold: int = 2          # Successes to close circuit from half-open
    timeout_seconds: float = 60.0       # Time to wait before trying again
    half_open_max_calls: int = 1        # Max concurrent calls in half-open state


class CircuitBreaker:
    """Circuit breaker for protecting against cascading failures."""
    
    def __init__(self, name: str, config: Optional[CircuitBreakerConfig] = None):
        """Initialize circuit breaker.
        
        Args:
            name: Name of the circuit (for logging)
            config: Configuration parameters
        """
        self.name = name
        self.config = config or CircuitBreakerConfig()
        
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: Optional[float] = None
        self._half_open_calls = 0
        self._lock = asyncio.Lock()
        
        logger.info(f"Circuit breaker '{name}' initialized in CLOSED state")
    
    @property
    def state(self) -> CircuitState:
        """Get current circuit state."""
        return self._state
    
    async def call(self, func: Callable[..., T], *args, **kwargs) -> T:
        """Execute function with circuit breaker protection.
        
        Args:
            func: Function to execute
            *args, **kwargs: Arguments to pass to function
            
        Returns:
            Function result
            
        Raises:
            CircuitBreakerOpenError: If circuit is open
        """
        async with self._lock:
            # Check if we should transition from OPEN to HALF_OPEN
            if self._state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    logger.info(f"Circuit '{self.name}' transitioning OPEN -> HALF_OPEN")
                    self._state = CircuitState.HALF_OPEN
                    self._half_open_calls = 0
                else:
                    raise CircuitBreakerOpenError(
                        f"Circuit breaker '{self.name}' is OPEN. "
                        f"Service unavailable. Try again in "
                        f"{self._time_until_retry():.1f}s"
                    )
            
            # Limit concurrent calls in HALF_OPEN state
            if self._state == CircuitState.HALF_OPEN:
                if self._half_open_calls >= self.config.half_open_max_calls:
                    raise CircuitBreakerOpenError(
                        f"Circuit breaker '{self.name}' is HALF_OPEN and at capacity"
                    )
                self._half_open_calls += 1
        
        # Execute the function
        try:
            result = await func(*args, **kwargs)
            await self._on_success()
            return result
            
        except Exception as e:
            await self._on_failure(e)
            raise
            
        finally:
            if self._state == CircuitState.HALF_OPEN:
                async with self._lock:
                    self._half_open_calls -= 1
    
    async def _on_success(self) -> None:
        """Handle successful call."""
        async with self._lock:
            self._failure_count = 0
            
            if self._state == CircuitState.HALF_OPEN:
                self._success_count += 1
                logger.info(
                    f"Circuit '{self.name}' success in HALF_OPEN: "
                    f"{self._success_count}/{self.config.success_threshold}"
                )
                
                if self._success_count >= self.config.success_threshold:
                    logger.info(f"Circuit '{self.name}' transitioning HALF_OPEN -> CLOSED")
                    self._state = CircuitState.CLOSED
                    self._success_count = 0
    
    async def _on_failure(self, exception: Exception) -> None:
        """Handle failed call."""
        async with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.time()
            
            logger.warning(
                f"Circuit '{self.name}' failure: {str(exception)} "
                f"({self._failure_count}/{self.config.failure_threshold})"
            )
            
            if self._state == CircuitState.HALF_OPEN:
                # Any failure in HALF_OPEN immediately opens circuit
                logger.error(f"Circuit '{self.name}' transitioning HALF_OPEN -> OPEN")
                self._state = CircuitState.OPEN
                self._success_count = 0
                
            elif self._failure_count >= self.config.failure_threshold:
                logger.error(
                    f"Circuit '{self.name}' threshold exceeded, transitioning CLOSED -> OPEN"
                )
                self._state = CircuitState.OPEN
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset."""
        if self._last_failure_time is None:
            return True
        
        elapsed = time.time() - self._last_failure_time
        return elapsed >= self.config.timeout_seconds
    
    def _time_until_retry(self) -> float:
        """Calculate seconds until retry is allowed."""
        if self._last_failure_time is None:
            return 0.0
        
        elapsed = time.time() - self._last_failure_time
        remaining = max(0.0, self.config.timeout_seconds - elapsed)
        return remaining
    
    def get_stats(self) -> dict:
        """Get circuit breaker statistics."""
        return {
            'name': self.name,
            'state': self._state.value,
            'failure_count': self._failure_count,
            'success_count': self._success_count,
            'time_until_retry': self._time_until_retry() if self._state == CircuitState.OPEN else 0,
            'config': {
                'failure_threshold': self.config.failure_threshold,
                'success_threshold': self.config.success_threshold,
                'timeout_seconds': self.config.timeout_seconds,
            }
        }
    
    async def reset(self) -> None:
        """Manually reset circuit breaker to CLOSED state."""
        async with self._lock:
            logger.info(f"Manually resetting circuit '{self.name}' to CLOSED")
            self._state = CircuitState.CLOSED
            self._failure_count = 0
            self._success_count = 0
            self._half_open_calls = 0


# Global circuit breakers for different services
_circuit_breakers: dict[str, CircuitBreaker] = {}


def get_circuit_breaker(name: str, config: Optional[CircuitBreakerConfig] = None) -> CircuitBreaker:
    """Get or create a circuit breaker by name.
    
    Args:
        name: Circuit breaker name
        config: Configuration (only used when creating new breaker)
        
    Returns:
        CircuitBreaker instance
    """
    if name not in _circuit_breakers:
        _circuit_breakers[name] = CircuitBreaker(name, config)
    return _circuit_breakers[name]


def circuit_breaker(
    name: str,
    config: Optional[CircuitBreakerConfig] = None
):
    """Decorator to protect function with circuit breaker.
    
    Args:
        name: Circuit breaker name
        config: Optional configuration
        
    Example:
        @circuit_breaker('tabcorp_api')
        async def call_api():
            return await api.fetch()
    """
    breaker = get_circuit_breaker(name, config)
    
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            return await breaker.call(func, *args, **kwargs)
        return wrapper
    
    return decorator


def get_all_circuit_stats() -> dict[str, dict]:
    """Get statistics for all circuit breakers."""
    return {name: breaker.get_stats() for name, breaker in _circuit_breakers.items()}


async def reset_all_circuits() -> None:
    """Reset all circuit breakers to CLOSED state."""
    for breaker in _circuit_breakers.values():
        await breaker.reset()
    logger.info("All circuit breakers reset")
