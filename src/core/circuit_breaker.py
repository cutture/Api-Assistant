"""
Circuit Breaker pattern implementation for resilient service calls.

This module provides a circuit breaker to prevent cascading failures when
calling external services like LLMs, vector stores, or web APIs.
"""

import time
from enum import Enum
from functools import wraps
from typing import Callable, Any, Optional
from datetime import datetime, timedelta

import structlog

from src.core.exceptions import LLMCircuitBreakerOpen

logger = structlog.get_logger(__name__)


class CircuitState(Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation, requests allowed
    OPEN = "open"  # Too many failures, requests blocked
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreaker:
    """
    Circuit breaker for protecting external service calls.

    The circuit breaker prevents cascading failures by:
    1. CLOSED: Allowing all requests, counting failures
    2. OPEN: Blocking all requests after threshold failures
    3. HALF_OPEN: Allowing test requests after timeout

    Example:
        ```python
        circuit_breaker = CircuitBreaker(
            name="llm_client",
            failure_threshold=5,
            timeout_duration=60,
        )

        @circuit_breaker
        def call_llm(prompt: str) -> str:
            # This call is protected by circuit breaker
            return llm_client.generate(prompt)
        ```
    """

    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        timeout_duration: int = 60,
        half_open_max_calls: int = 1,
    ):
        """
        Initialize circuit breaker.

        Args:
            name: Name of the circuit breaker (for logging)
            failure_threshold: Number of failures before opening circuit
            timeout_duration: Seconds to wait before attempting recovery
            half_open_max_calls: Max calls to allow in half-open state
        """
        self.name = name
        self.failure_threshold = failure_threshold
        self.timeout_duration = timeout_duration
        self.half_open_max_calls = half_open_max_calls

        # State tracking
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.opened_at: Optional[datetime] = None
        self.half_open_attempts = 0

        logger.info(
            "circuit_breaker_initialized",
            name=self.name,
            failure_threshold=self.failure_threshold,
            timeout_duration=self.timeout_duration,
        )

    def __call__(self, func: Callable) -> Callable:
        """
        Decorator to protect function with circuit breaker.

        Args:
            func: Function to protect

        Returns:
            Wrapped function with circuit breaker protection
        """

        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            return self.call(func, *args, **kwargs)

        return wrapper

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with circuit breaker protection.

        Args:
            func: Function to call
            *args: Positional arguments for func
            **kwargs: Keyword arguments for func

        Returns:
            Result of func

        Raises:
            LLMCircuitBreakerOpen: If circuit is open
            Exception: Any exception raised by func
        """
        # Check if circuit should transition from OPEN to HALF_OPEN
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self._transition_to_half_open()
            else:
                retry_after = self._seconds_until_retry()
                logger.warning(
                    "circuit_breaker_blocking_request",
                    name=self.name,
                    retry_after=retry_after,
                )
                raise LLMCircuitBreakerOpen(
                    f"Circuit breaker '{self.name}' is OPEN",
                    retry_after=retry_after,
                )

        # Check if we've exceeded half-open attempts
        if self.state == CircuitState.HALF_OPEN:
            if self.half_open_attempts >= self.half_open_max_calls:
                logger.warning(
                    "circuit_breaker_half_open_limit_reached",
                    name=self.name,
                    attempts=self.half_open_attempts,
                )
                raise LLMCircuitBreakerOpen(
                    f"Circuit breaker '{self.name}' is testing recovery - please retry later",
                    retry_after=5,
                )
            self.half_open_attempts += 1

        # Try the call
        try:
            start_time = time.time()
            result = func(*args, **kwargs)
            latency = time.time() - start_time

            self._on_success(latency)
            return result

        except Exception as e:
            self._on_failure(e)
            raise

    def _on_success(self, latency: float):
        """
        Handle successful call.

        Args:
            latency: Call latency in seconds
        """
        self.success_count += 1

        if self.state == CircuitState.HALF_OPEN:
            logger.info(
                "circuit_breaker_test_call_succeeded",
                name=self.name,
                latency=latency,
            )
            self._transition_to_closed()
        elif self.state == CircuitState.CLOSED:
            # Reset failure count on success
            if self.failure_count > 0:
                logger.debug(
                    "circuit_breaker_failure_count_reset",
                    name=self.name,
                    previous_failures=self.failure_count,
                )
                self.failure_count = 0

    def _on_failure(self, error: Exception):
        """
        Handle failed call.

        Args:
            error: Exception that was raised
        """
        self.failure_count += 1
        self.last_failure_time = datetime.now()

        logger.warning(
            "circuit_breaker_call_failed",
            name=self.name,
            state=self.state.value,
            failure_count=self.failure_count,
            error_type=type(error).__name__,
            error_message=str(error),
        )

        if self.state == CircuitState.HALF_OPEN:
            # Failed during recovery test - go back to OPEN
            logger.error(
                "circuit_breaker_recovery_test_failed",
                name=self.name,
            )
            self._transition_to_open()

        elif self.state == CircuitState.CLOSED:
            # Check if we should open the circuit
            if self.failure_count >= self.failure_threshold:
                logger.error(
                    "circuit_breaker_threshold_exceeded",
                    name=self.name,
                    failure_count=self.failure_count,
                    threshold=self.failure_threshold,
                )
                self._transition_to_open()

    def _transition_to_open(self):
        """Transition circuit to OPEN state."""
        self.state = CircuitState.OPEN
        self.opened_at = datetime.now()
        self.half_open_attempts = 0

        logger.error(
            "circuit_breaker_opened",
            name=self.name,
            failure_count=self.failure_count,
            timeout_duration=self.timeout_duration,
        )

    def _transition_to_half_open(self):
        """Transition circuit to HALF_OPEN state."""
        self.state = CircuitState.HALF_OPEN
        self.half_open_attempts = 0

        logger.info(
            "circuit_breaker_half_open",
            name=self.name,
            message="Testing if service recovered",
        )

    def _transition_to_closed(self):
        """Transition circuit to CLOSED state."""
        previous_state = self.state
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.half_open_attempts = 0
        self.opened_at = None

        logger.info(
            "circuit_breaker_closed",
            name=self.name,
            previous_state=previous_state.value,
            message="Service recovered",
        )

    def _should_attempt_reset(self) -> bool:
        """
        Check if enough time has passed to attempt reset.

        Returns:
            True if we should try HALF_OPEN state
        """
        if self.opened_at is None:
            return True

        elapsed = (datetime.now() - self.opened_at).total_seconds()
        return elapsed >= self.timeout_duration

    def _seconds_until_retry(self) -> int:
        """
        Calculate seconds until next retry attempt.

        Returns:
            Seconds until circuit attempts reset
        """
        if self.opened_at is None:
            return 0

        elapsed = (datetime.now() - self.opened_at).total_seconds()
        remaining = max(0, self.timeout_duration - elapsed)
        return int(remaining)

    def get_state(self) -> dict:
        """
        Get current circuit breaker state.

        Returns:
            Dictionary with state information
        """
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "failure_threshold": self.failure_threshold,
            "timeout_duration": self.timeout_duration,
            "opened_at": self.opened_at.isoformat() if self.opened_at else None,
            "seconds_until_retry": (
                self._seconds_until_retry() if self.state == CircuitState.OPEN else 0
            ),
        }

    def reset(self):
        """Manually reset circuit breaker to CLOSED state."""
        logger.info(
            "circuit_breaker_manual_reset",
            name=self.name,
            previous_state=self.state.value,
        )
        self._transition_to_closed()


# ============================================================================
# Global circuit breakers for common services
# ============================================================================

# LLM client circuit breaker
llm_circuit_breaker = CircuitBreaker(
    name="llm_client",
    failure_threshold=5,
    timeout_duration=60,
    half_open_max_calls=1,
)

# Vector store circuit breaker
vector_store_circuit_breaker = CircuitBreaker(
    name="vector_store",
    failure_threshold=3,
    timeout_duration=30,
    half_open_max_calls=1,
)

# Web search circuit breaker
web_search_circuit_breaker = CircuitBreaker(
    name="web_search",
    failure_threshold=3,
    timeout_duration=30,
    half_open_max_calls=2,
)
