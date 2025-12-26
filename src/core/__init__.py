"""Core business logic for API Integration Assistant."""

from src.core.embeddings import EmbeddingService
from src.core.vector_store import VectorStore
from src.core.llm_client import LLMClient
from src.core.exceptions import (
    APIAssistantError,
    LLMError,
    LLMConnectionError,
    LLMTimeoutError,
    LLMRateLimitError,
    LLMResponseError,
    LLMCircuitBreakerOpen,
)
from src.core.circuit_breaker import CircuitBreaker, CircuitState
from src.core.health import HealthCheck, HealthStatus, check_system_health
from src.core.logging_config import (
    configure_logging,
    configure_production_logging,
    configure_development_logging,
    get_logger,
    set_request_id,
    get_request_id,
    clear_request_id,
    log_performance,
    log_performance_async,
    LogContext,
)

__all__ = [
    "EmbeddingService",
    "VectorStore",
    "LLMClient",
    "APIAssistantError",
    "LLMError",
    "LLMConnectionError",
    "LLMTimeoutError",
    "LLMRateLimitError",
    "LLMResponseError",
    "LLMCircuitBreakerOpen",
    "CircuitBreaker",
    "CircuitState",
    "HealthCheck",
    "HealthStatus",
    "check_system_health",
    "configure_logging",
    "configure_production_logging",
    "configure_development_logging",
    "get_logger",
    "set_request_id",
    "get_request_id",
    "clear_request_id",
    "log_performance",
    "log_performance_async",
    "LogContext",
]
