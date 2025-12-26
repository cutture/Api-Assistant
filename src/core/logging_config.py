"""
Production-ready logging configuration for API Integration Assistant.

Features:
- Structured JSON logging for production
- Request ID tracking across all operations
- Component-specific log levels
- Performance timing decorators
- Log aggregation support

Usage:
    ```python
    # Initialize logging at application startup
    from src.core.logging_config import configure_logging
    configure_logging()

    # Use structured logger
    import structlog
    logger = structlog.get_logger(__name__)
    logger.info("user_query_received", query="How do I authenticate?")

    # Track request across operations
    from src.core.logging_config import set_request_id, get_request_id
    set_request_id("req-123")
    # All subsequent logs will include request_id

    # Performance timing
    from src.core.logging_config import log_performance
    @log_performance
    def slow_operation():
        time.sleep(1)
        return "done"
    ```
"""

import logging
import sys
import time
import uuid
from contextvars import ContextVar
from functools import wraps
from typing import Any, Callable, Dict, Optional

import structlog
from structlog.types import EventDict, Processor

from src.config import settings

# ============================================================================
# Context Variables for Request Tracking
# ============================================================================

# Thread-safe storage for request ID
_request_id: ContextVar[Optional[str]] = ContextVar("request_id", default=None)


def get_request_id() -> Optional[str]:
    """
    Get the current request ID from context.

    Returns:
        Current request ID or None
    """
    return _request_id.get()


def set_request_id(request_id: Optional[str] = None) -> str:
    """
    Set request ID in context. Generates UUID if not provided.

    Args:
        request_id: Optional request ID (generates UUID if None)

    Returns:
        The request ID that was set
    """
    if request_id is None:
        request_id = f"req-{uuid.uuid4().hex[:12]}"

    _request_id.set(request_id)
    return request_id


def clear_request_id() -> None:
    """Clear the request ID from context."""
    _request_id.set(None)


# ============================================================================
# Custom Processors
# ============================================================================


def add_request_id(logger: Any, method_name: str, event_dict: EventDict) -> EventDict:
    """
    Processor that adds request_id to all log entries.

    Args:
        logger: Logger instance
        method_name: Log method name (info, debug, etc.)
        event_dict: Event dictionary

    Returns:
        Updated event dictionary with request_id
    """
    request_id = get_request_id()
    if request_id:
        event_dict["request_id"] = request_id

    return event_dict


def add_component(logger: Any, method_name: str, event_dict: EventDict) -> EventDict:
    """
    Processor that adds component name from logger name.

    Args:
        logger: Logger instance
        method_name: Log method name
        event_dict: Event dictionary

    Returns:
        Updated event dictionary with component name
    """
    # Extract component from logger name (e.g., "src.agents.rag_agent" -> "rag_agent")
    logger_name = event_dict.get("logger", "unknown")
    if "." in logger_name:
        component = logger_name.split(".")[-1]
    else:
        component = logger_name

    event_dict["component"] = component
    return event_dict


def add_app_metadata(logger: Any, method_name: str, event_dict: EventDict) -> EventDict:
    """
    Processor that adds application metadata to log entries.

    Args:
        logger: Logger instance
        method_name: Log method name
        event_dict: Event dictionary

    Returns:
        Updated event dictionary with app metadata
    """
    event_dict["app"] = settings.app_name
    event_dict["environment"] = "development" if settings.debug else "production"

    return event_dict


# ============================================================================
# Logging Configuration
# ============================================================================


def configure_logging(
    json_format: bool = True,
    log_level: Optional[str] = None,
    component_log_levels: Optional[Dict[str, str]] = None,
) -> None:
    """
    Configure structured logging for the application.

    Args:
        json_format: Use JSON formatting (True for production, False for development)
        log_level: Override default log level from settings
        component_log_levels: Component-specific log levels
            Example: {"rag_agent": "DEBUG", "llm_client": "WARNING"}
    """
    # Determine log level
    level = log_level or settings.log_level
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=numeric_level,
    )

    # Build processor chain
    processors: list[Processor] = [
        # Add context information
        add_request_id,
        add_component,
        add_app_metadata,
        # Standard structlog processors
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    # Add renderer based on format preference
    if json_format:
        # Production: JSON output for log aggregation
        processors.append(structlog.processors.JSONRenderer())
    else:
        # Development: Pretty console output
        processors.extend(
            [
                structlog.dev.set_exc_info,
                structlog.dev.ConsoleRenderer(colors=True),
            ]
        )

    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Apply component-specific log levels
    if component_log_levels:
        for component, level_str in component_log_levels.items():
            component_level = getattr(logging, level_str.upper(), logging.INFO)
            component_logger = logging.getLogger(f"src.{component}")
            component_logger.setLevel(component_level)

    # Log configuration
    logger = structlog.get_logger(__name__)
    logger.info(
        "logging_configured",
        log_level=level,
        json_format=json_format,
        component_levels=component_log_levels or {},
    )


# ============================================================================
# Performance Logging
# ============================================================================


def log_performance(
    logger_name: Optional[str] = None,
    log_args: bool = False,
    log_result: bool = False,
) -> Callable:
    """
    Decorator to log function execution time and optionally args/result.

    Args:
        logger_name: Override logger name (default: function's module)
        log_args: Log function arguments
        log_result: Log function result

    Returns:
        Decorated function

    Example:
        ```python
        @log_performance(log_args=True)
        def process_query(query: str) -> str:
            time.sleep(1)
            return "result"
        ```
    """

    def decorator(func: Callable) -> Callable:
        # Get logger
        logger = structlog.get_logger(logger_name or func.__module__)

        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Build log context
            log_context = {
                "function": func.__name__,
            }

            if log_args:
                # Safely log args (avoid logging sensitive data)
                log_context["args_count"] = len(args)
                log_context["kwargs"] = list(kwargs.keys())

            # Start timing
            start_time = time.perf_counter()

            try:
                # Execute function
                result = func(*args, **kwargs)

                # Calculate duration
                duration_ms = (time.perf_counter() - start_time) * 1000

                # Log success
                if log_result and result is not None:
                    log_context["result_type"] = type(result).__name__

                logger.info(
                    "function_completed",
                    **log_context,
                    duration_ms=round(duration_ms, 2),
                    status="success",
                )

                return result

            except Exception as e:
                # Calculate duration
                duration_ms = (time.perf_counter() - start_time) * 1000

                # Log failure
                logger.error(
                    "function_failed",
                    **log_context,
                    duration_ms=round(duration_ms, 2),
                    status="error",
                    error_type=type(e).__name__,
                    error_message=str(e),
                )

                # Re-raise exception
                raise

        return wrapper

    return decorator


def log_performance_async(
    logger_name: Optional[str] = None,
    log_args: bool = False,
    log_result: bool = False,
) -> Callable:
    """
    Async version of log_performance decorator.

    Args:
        logger_name: Override logger name (default: function's module)
        log_args: Log function arguments
        log_result: Log function result

    Returns:
        Decorated async function

    Example:
        ```python
        @log_performance_async(log_args=True)
        async def fetch_data(url: str) -> dict:
            await asyncio.sleep(1)
            return {"data": "value"}
        ```
    """

    def decorator(func: Callable) -> Callable:
        # Get logger
        logger = structlog.get_logger(logger_name or func.__module__)

        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            # Build log context
            log_context = {
                "function": func.__name__,
            }

            if log_args:
                log_context["args_count"] = len(args)
                log_context["kwargs"] = list(kwargs.keys())

            # Start timing
            start_time = time.perf_counter()

            try:
                # Execute async function
                result = await func(*args, **kwargs)

                # Calculate duration
                duration_ms = (time.perf_counter() - start_time) * 1000

                # Log success
                if log_result and result is not None:
                    log_context["result_type"] = type(result).__name__

                logger.info(
                    "async_function_completed",
                    **log_context,
                    duration_ms=round(duration_ms, 2),
                    status="success",
                )

                return result

            except Exception as e:
                # Calculate duration
                duration_ms = (time.perf_counter() - start_time) * 1000

                # Log failure
                logger.error(
                    "async_function_failed",
                    **log_context,
                    duration_ms=round(duration_ms, 2),
                    status="error",
                    error_type=type(e).__name__,
                    error_message=str(e),
                )

                # Re-raise exception
                raise

        return wrapper

    return decorator


# ============================================================================
# Context Managers for Scoped Logging
# ============================================================================


class LogContext:
    """
    Context manager for adding temporary context to logs.

    Example:
        ```python
        with LogContext(user_id="123", operation="query"):
            logger.info("processing")  # Will include user_id and operation
        ```
    """

    def __init__(self, **context):
        """
        Initialize log context.

        Args:
            **context: Key-value pairs to add to logs
        """
        self.context = context
        self.token = None

    def __enter__(self):
        """Enter context - bind context to structlog."""
        structlog.contextvars.bind_contextvars(**self.context)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context - unbind context from structlog."""
        # Unbind all keys that were bound
        structlog.contextvars.unbind_contextvars(*self.context.keys())


# ============================================================================
# Convenience Functions
# ============================================================================


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """
    Get a configured structlog logger.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Configured structlog logger
    """
    return structlog.get_logger(name)


def configure_production_logging() -> None:
    """
    Configure logging for production environment.

    - JSON output for log aggregation
    - INFO level by default
    - Component-specific levels for noise reduction
    """
    component_levels = {
        # Reduce noise from verbose components
        "embeddings": "WARNING",
        "vector_store": "WARNING",
        # Keep important components at INFO
        "agents": "INFO",
        "llm_client": "INFO",
        "orchestrator": "INFO",
    }

    configure_logging(
        json_format=True,
        log_level="INFO",
        component_log_levels=component_levels,
    )


def configure_development_logging() -> None:
    """
    Configure logging for development environment.

    - Pretty console output with colors
    - DEBUG level for detailed information
    """
    configure_logging(
        json_format=False,
        log_level="DEBUG",
    )
