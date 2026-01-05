"""
Tests for error handling, circuit breaker, and health check systems.
"""

import time
from unittest.mock import Mock, patch

import pytest

from src.core.exceptions import (
    APIAssistantError,
    LLMError,
    LLMConnectionError,
    LLMTimeoutError,
    LLMCircuitBreakerOpen,
    LLMResponseError,
    get_error_details,
    is_retryable_error,
)
from src.core.circuit_breaker import CircuitBreaker, CircuitState
from src.core.health import HealthCheck, HealthStatus


class TestExceptions:
    """Test custom exception hierarchy."""

    def test_base_exception_with_details(self):
        """Test base exception stores message and details."""
        error = APIAssistantError(
            "Test error",
            details={"key": "value", "code": 123},
        )

        assert str(error) == "Test error"
        assert error.message == "Test error"
        assert error.details == {"key": "value", "code": 123}

    def test_base_exception_without_details(self):
        """Test base exception works without details."""
        error = APIAssistantError("Simple error")

        assert str(error) == "Simple error"
        assert error.details == {}

    def test_llm_circuit_breaker_exception(self):
        """Test circuit breaker exception includes retry_after."""
        error = LLMCircuitBreakerOpen(
            "Circuit is open",
            retry_after=60,
        )

        assert "Circuit is open" in str(error)
        assert error.retry_after == 60
        assert error.details["retry_after"] == 60

    def test_get_error_details_custom_exception(self):
        """Test extracting details from custom exceptions."""
        error = LLMConnectionError(
            "Connection failed",
            details={"host": "localhost", "port": 11434},
        )

        details = get_error_details(error)

        assert details["type"] == "LLMConnectionError"
        assert details["message"] == "Connection failed"
        assert details["details"]["host"] == "localhost"
        assert details["details"]["port"] == 11434

    def test_get_error_details_standard_exception(self):
        """Test extracting details from standard exceptions."""
        error = ValueError("Invalid value")

        details = get_error_details(error)

        assert details["type"] == "ValueError"
        assert details["message"] == "Invalid value"
        assert "details" not in details

    def test_is_retryable_error(self):
        """Test retryable error detection."""
        # Retryable errors
        assert is_retryable_error(LLMConnectionError("Connection failed"))
        assert is_retryable_error(LLMTimeoutError("Timeout"))

        # Non-retryable errors
        assert not is_retryable_error(LLMCircuitBreakerOpen("Circuit open"))
        assert not is_retryable_error(LLMResponseError("Bad response"))
        assert not is_retryable_error(ValueError("Standard error"))


class TestCircuitBreaker:
    """Test circuit breaker functionality."""

    def test_circuit_breaker_initialization(self):
        """Test circuit breaker initializes correctly."""
        cb = CircuitBreaker(
            name="test_breaker",
            failure_threshold=3,
            timeout_duration=30,
        )

        assert cb.name == "test_breaker"
        assert cb.failure_threshold == 3
        assert cb.timeout_duration == 30
        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0

    def test_circuit_closed_allows_requests(self):
        """Test circuit breaker allows requests when closed."""
        cb = CircuitBreaker(name="test", failure_threshold=3)

        @cb
        def successful_operation():
            return "success"

        result = successful_operation()
        assert result == "success"
        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0

    def test_circuit_opens_after_threshold_failures(self):
        """Test circuit opens after reaching failure threshold."""
        cb = CircuitBreaker(name="test", failure_threshold=3, timeout_duration=1)

        @cb
        def failing_operation():
            raise Exception("Simulated failure")

        # First 3 failures should go through
        for i in range(3):
            with pytest.raises(Exception, match="Simulated failure"):
                failing_operation()

        # Circuit should now be OPEN
        assert cb.state == CircuitState.OPEN
        assert cb.failure_count == 3

        # Next call should be blocked by circuit breaker
        with pytest.raises(LLMCircuitBreakerOpen):
            failing_operation()

    def test_circuit_half_open_after_timeout(self):
        """Test circuit transitions to HALF_OPEN after timeout."""
        cb = CircuitBreaker(
            name="test",
            failure_threshold=2,
            timeout_duration=1,  # 1 second
            half_open_max_calls=1,
        )

        @cb
        def failing_operation():
            raise Exception("Failure")

        # Open the circuit
        for i in range(2):
            with pytest.raises(Exception):
                failing_operation()

        assert cb.state == CircuitState.OPEN

        # Wait for timeout
        time.sleep(1.1)

        # Next call should attempt recovery (HALF_OPEN)
        # This will fail and go back to OPEN
        with pytest.raises(Exception):
            failing_operation()

        # Should be back to OPEN
        assert cb.state == CircuitState.OPEN

    def test_circuit_closes_after_successful_recovery(self):
        """Test circuit closes after successful recovery test."""
        cb = CircuitBreaker(
            name="test",
            failure_threshold=2,
            timeout_duration=1,
            half_open_max_calls=1,
        )

        # Track whether to fail
        should_fail = [True]

        @cb
        def conditional_operation():
            if should_fail[0]:
                raise Exception("Failure")
            return "success"

        # Open the circuit
        for i in range(2):
            with pytest.raises(Exception):
                conditional_operation()

        assert cb.state == CircuitState.OPEN

        # Wait for timeout
        time.sleep(1.1)

        # Fix the issue
        should_fail[0] = False

        # Recovery should succeed
        result = conditional_operation()
        assert result == "success"
        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0

    def test_circuit_breaker_get_state(self):
        """Test getting circuit breaker state information."""
        cb = CircuitBreaker(name="test", failure_threshold=5)

        state = cb.get_state()

        assert state["name"] == "test"
        assert state["state"] == "closed"
        assert state["failure_count"] == 0
        assert state["success_count"] == 0
        assert state["failure_threshold"] == 5

    def test_circuit_breaker_manual_reset(self):
        """Test manually resetting circuit breaker."""
        cb = CircuitBreaker(name="test", failure_threshold=1)

        @cb
        def failing_operation():
            raise Exception("Failure")

        # Open the circuit
        with pytest.raises(Exception):
            failing_operation()

        assert cb.state == CircuitState.OPEN

        # Manual reset
        cb.reset()

        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0

    def test_circuit_success_resets_failure_count(self):
        """Test successful calls reset failure count."""
        cb = CircuitBreaker(name="test", failure_threshold=5)

        call_count = [0]

        @cb
        def intermittent_operation():
            call_count[0] += 1
            if call_count[0] % 2 == 0:
                raise Exception("Failure")
            return "success"

        # Success, failure, success pattern
        result1 = intermittent_operation()
        assert result1 == "success"
        assert cb.failure_count == 0

        with pytest.raises(Exception):
            intermittent_operation()
        assert cb.failure_count == 1

        result2 = intermittent_operation()
        assert result2 == "success"
        assert cb.failure_count == 0  # Reset after success


class TestHealthCheck:
    """Test health check system."""

    def test_health_check_initialization(self):
        """Test health check initializes correctly."""
        health = HealthCheck()

        assert health.last_check_time is None
        assert health.cached_status is None
        assert health.cache_duration == 30

    @patch("src.core.health.llm_circuit_breaker")
    def test_check_llm_healthy(self, mock_circuit):
        """Test LLM health check when healthy."""
        mock_circuit.get_state.return_value = {
            "state": "closed",
            "failure_count": 0,
            "seconds_until_retry": 0,
        }

        health = HealthCheck()
        result = health.check_llm()

        assert result["status"] == HealthStatus.HEALTHY.value
        assert "available" in result["message"].lower()

    @patch("src.core.health.llm_circuit_breaker")
    def test_check_llm_degraded(self, mock_circuit):
        """Test LLM health check when degraded."""
        mock_circuit.get_state.return_value = {
            "state": "half_open",
            "failure_count": 3,
            "seconds_until_retry": 0,
        }

        health = HealthCheck()
        result = health.check_llm()

        assert result["status"] == HealthStatus.DEGRADED.value
        assert "recovering" in result["message"].lower()

    @patch("src.core.health.llm_circuit_breaker")
    def test_check_llm_unhealthy(self, mock_circuit):
        """Test LLM health check when unhealthy."""
        mock_circuit.get_state.return_value = {
            "state": "open",
            "failure_count": 5,
            "seconds_until_retry": 45,
        }

        health = HealthCheck()
        result = health.check_llm()

        assert result["status"] == HealthStatus.UNHEALTHY.value
        assert "unavailable" in result["message"].lower()
        assert "45" in result["message"]  # Retry time mentioned

    @patch("src.core.health.vector_store_circuit_breaker")
    @patch("src.core.vector_store.get_vector_store")
    def test_check_vector_store_healthy(self, mock_get_vs, mock_circuit):
        """Test vector store health check when healthy."""
        mock_circuit.get_state.return_value = {
            "state": "closed",
            "failure_count": 0,
        }

        mock_collection = Mock()
        mock_collection.count.return_value = 100

        mock_vs = Mock()
        mock_vs._collection = mock_collection
        mock_get_vs.return_value = mock_vs

        health = HealthCheck()
        result = health.check_vector_store()

        assert result["status"] == HealthStatus.HEALTHY.value
        assert "100" in result["message"]

    @patch("src.core.embeddings.EmbeddingService")
    def test_check_embeddings_healthy(self, mock_embedding_class):
        """Test embeddings health check when healthy."""
        mock_service = Mock()
        mock_service.embed_text.return_value = [0.1] * 384  # 384-dim vector
        mock_embedding_class.return_value = mock_service

        health = HealthCheck()
        result = health.check_embeddings()

        assert result["status"] == HealthStatus.HEALTHY.value
        assert "384" in result["message"]

    @patch("src.core.embeddings.EmbeddingService")
    def test_check_embeddings_unhealthy(self, mock_embedding_class):
        """Test embeddings health check when unhealthy."""
        mock_service = Mock()
        mock_service.embed_text.side_effect = Exception("Model loading failed")
        mock_embedding_class.return_value = mock_service

        health = HealthCheck()
        result = health.check_embeddings()

        assert result["status"] == HealthStatus.UNHEALTHY.value
        assert "failed" in result["message"].lower()

    @patch("src.core.health.HealthCheck.check_llm")
    @patch("src.core.health.HealthCheck.check_vector_store")
    @patch("src.core.health.HealthCheck.check_web_search")
    @patch("src.core.health.HealthCheck.check_embeddings")
    def test_check_all_services_healthy(
        self,
        mock_embeddings,
        mock_web,
        mock_vs,
        mock_llm,
    ):
        """Test overall health check when all services healthy."""
        # All services healthy
        for mock in [mock_embeddings, mock_web, mock_vs, mock_llm]:
            mock.return_value = {
                "status": HealthStatus.HEALTHY.value,
                "message": "OK",
            }

        health = HealthCheck()
        result = health.check_all(use_cache=False)

        assert result["status"] == HealthStatus.HEALTHY.value
        assert "llm" in result["services"]
        assert "vector_store" in result["services"]
        assert "web_search" in result["services"]
        assert "embeddings" in result["services"]

    @patch("src.core.health.HealthCheck.check_llm")
    @patch("src.core.health.HealthCheck.check_vector_store")
    @patch("src.core.health.HealthCheck.check_web_search")
    @patch("src.core.health.HealthCheck.check_embeddings")
    def test_check_all_services_degraded(
        self,
        mock_embeddings,
        mock_web,
        mock_vs,
        mock_llm,
    ):
        """Test overall health when one service degraded."""
        mock_llm.return_value = {
            "status": HealthStatus.DEGRADED.value,
            "message": "Recovering",
        }

        for mock in [mock_embeddings, mock_web, mock_vs]:
            mock.return_value = {
                "status": HealthStatus.HEALTHY.value,
                "message": "OK",
            }

        health = HealthCheck()
        result = health.check_all(use_cache=False)

        assert result["status"] == HealthStatus.DEGRADED.value

    @patch("src.core.health.HealthCheck.check_llm")
    @patch("src.core.health.HealthCheck.check_vector_store")
    @patch("src.core.health.HealthCheck.check_web_search")
    @patch("src.core.health.HealthCheck.check_embeddings")
    def test_check_all_services_unhealthy(
        self,
        mock_embeddings,
        mock_web,
        mock_vs,
        mock_llm,
    ):
        """Test overall health when service is unhealthy."""
        mock_llm.return_value = {
            "status": HealthStatus.UNHEALTHY.value,
            "message": "Down",
        }

        for mock in [mock_embeddings, mock_web, mock_vs]:
            mock.return_value = {
                "status": HealthStatus.HEALTHY.value,
                "message": "OK",
            }

        health = HealthCheck()
        result = health.check_all(use_cache=False)

        assert result["status"] == HealthStatus.UNHEALTHY.value

    @patch("src.core.health.HealthCheck.check_llm")
    @patch("src.core.health.HealthCheck.check_vector_store")
    @patch("src.core.health.HealthCheck.check_web_search")
    @patch("src.core.health.HealthCheck.check_embeddings")
    def test_health_check_caching(
        self,
        mock_embeddings,
        mock_web,
        mock_vs,
        mock_llm,
    ):
        """Test health check result caching."""
        for mock in [mock_embeddings, mock_web, mock_vs, mock_llm]:
            mock.return_value = {
                "status": HealthStatus.HEALTHY.value,
                "message": "OK",
            }

        health = HealthCheck()

        # First call
        result1 = health.check_all(use_cache=False)
        assert mock_llm.call_count == 1

        # Second call should use cache
        result2 = health.check_all(use_cache=True)
        assert mock_llm.call_count == 1  # Not called again

        assert result1["timestamp"] == result2["timestamp"]
