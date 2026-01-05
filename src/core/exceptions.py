"""
Custom exception hierarchy for the API Integration Assistant.

This module defines a comprehensive exception hierarchy for better error handling
and debugging throughout the application.
"""


class APIAssistantError(Exception):
    """Base exception for all API Integration Assistant errors."""

    def __init__(self, message: str, details: dict = None):
        """
        Initialize base exception.

        Args:
            message: Human-readable error message
            details: Additional context about the error
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}


# ============================================================================
# LLM-related exceptions
# ============================================================================


class LLMError(APIAssistantError):
    """Base exception for LLM-related errors."""

    pass


class LLMConnectionError(LLMError):
    """Raised when connection to LLM service fails."""

    pass


class LLMTimeoutError(LLMError):
    """Raised when LLM request times out."""

    pass


class LLMRateLimitError(LLMError):
    """Raised when LLM rate limit is exceeded."""

    pass


class LLMResponseError(LLMError):
    """Raised when LLM returns invalid or malformed response."""

    pass


class LLMCircuitBreakerOpen(LLMError):
    """Raised when circuit breaker is open and requests are blocked."""

    def __init__(self, message: str = None, retry_after: int = None):
        """
        Initialize circuit breaker exception.

        Args:
            message: Error message
            retry_after: Seconds until circuit breaker resets
        """
        super().__init__(
            message or "Circuit breaker is open - too many recent failures",
            details={"retry_after": retry_after},
        )
        self.retry_after = retry_after


# ============================================================================
# Vector Store exceptions
# ============================================================================


class VectorStoreError(APIAssistantError):
    """Base exception for vector store errors."""

    pass


class VectorStoreConnectionError(VectorStoreError):
    """Raised when connection to vector store fails."""

    pass


class VectorStoreQueryError(VectorStoreError):
    """Raised when vector store query fails."""

    pass


class EmbeddingError(VectorStoreError):
    """Raised when embedding generation fails."""

    pass


# ============================================================================
# Agent exceptions
# ============================================================================


class AgentError(APIAssistantError):
    """Base exception for agent errors."""

    pass


class AgentProcessingError(AgentError):
    """Raised when agent processing fails."""

    pass


class AgentValidationError(AgentError):
    """Raised when agent input validation fails."""

    pass


class AgentTimeoutError(AgentError):
    """Raised when agent processing times out."""

    pass


# ============================================================================
# Service exceptions
# ============================================================================


class ServiceError(APIAssistantError):
    """Base exception for service errors."""

    pass


class WebSearchError(ServiceError):
    """Raised when web search fails."""

    pass


class URLScraperError(ServiceError):
    """Raised when URL scraping fails."""

    pass


class ConversationMemoryError(ServiceError):
    """Raised when conversation memory operation fails."""

    pass


# ============================================================================
# Parser exceptions
# ============================================================================


class ParserError(APIAssistantError):
    """Base exception for parser errors."""

    pass


class InvalidAPISpecError(ParserError):
    """Raised when API specification is invalid."""

    pass


class UnsupportedFormatError(ParserError):
    """Raised when API spec format is not supported."""

    pass


# ============================================================================
# Configuration exceptions
# ============================================================================


class ConfigurationError(APIAssistantError):
    """Base exception for configuration errors."""

    pass


class MissingConfigError(ConfigurationError):
    """Raised when required configuration is missing."""

    pass


class InvalidConfigError(ConfigurationError):
    """Raised when configuration value is invalid."""

    pass


# ============================================================================
# Utility functions
# ============================================================================


def get_error_details(error: Exception) -> dict:
    """
    Extract error details from exception.

    Args:
        error: Exception to extract details from

    Returns:
        Dictionary with error type, message, and details
    """
    error_info = {
        "type": type(error).__name__,
        "message": str(error),
    }

    if isinstance(error, APIAssistantError):
        error_info["details"] = error.details

    return error_info


def is_retryable_error(error: Exception) -> bool:
    """
    Check if error is retryable.

    Args:
        error: Exception to check

    Returns:
        True if error should be retried, False otherwise
    """
    retryable_types = (
        LLMConnectionError,
        LLMTimeoutError,
        VectorStoreConnectionError,
        WebSearchError,
    )

    # Don't retry circuit breaker or rate limit errors
    non_retryable_types = (
        LLMCircuitBreakerOpen,
        LLMRateLimitError,
    )

    if isinstance(error, non_retryable_types):
        return False

    return isinstance(error, retryable_types)
