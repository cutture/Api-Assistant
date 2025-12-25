"""
Observability and monitoring integration using Langfuse.

This module provides comprehensive tracing and monitoring capabilities
for all agent operations, including:
- Query latency tracking
- Token usage monitoring
- Agent routing decisions
- Retrieval quality scores
- Error tracking and debugging
"""

import functools
import os
import time
from contextlib import contextmanager
from typing import Any, Callable, Dict, List, Optional

import structlog

logger = structlog.get_logger(__name__)

# Langfuse integration (optional dependency)
try:
    from langfuse import Langfuse
    from langfuse.decorators import langfuse_context, observe

    LANGFUSE_AVAILABLE = True
except ImportError:
    LANGFUSE_AVAILABLE = False
    logger.warning("langfuse_not_installed", message="Langfuse monitoring disabled. Install with: pip install langfuse")


class MonitoringConfig:
    """Configuration for monitoring and observability."""

    def __init__(
        self,
        enabled: bool = True,
        langfuse_public_key: Optional[str] = None,
        langfuse_secret_key: Optional[str] = None,
        langfuse_host: Optional[str] = None,
        track_tokens: bool = True,
        track_latency: bool = True,
        track_routing: bool = True,
        track_quality: bool = True,
    ):
        """
        Initialize monitoring configuration.

        Args:
            enabled: Whether monitoring is enabled globally
            langfuse_public_key: Langfuse public API key (or use LANGFUSE_PUBLIC_KEY env var)
            langfuse_secret_key: Langfuse secret API key (or use LANGFUSE_SECRET_KEY env var)
            langfuse_host: Langfuse host URL (or use LANGFUSE_HOST env var)
            track_tokens: Track token usage
            track_latency: Track operation latency
            track_routing: Track agent routing decisions
            track_quality: Track retrieval quality scores
        """
        self.enabled = enabled and LANGFUSE_AVAILABLE
        self.track_tokens = track_tokens
        self.track_latency = track_latency
        self.track_routing = track_routing
        self.track_quality = track_quality

        # Langfuse configuration from env vars or params
        self.langfuse_public_key = langfuse_public_key or os.getenv("LANGFUSE_PUBLIC_KEY")
        self.langfuse_secret_key = langfuse_secret_key or os.getenv("LANGFUSE_SECRET_KEY")
        self.langfuse_host = langfuse_host or os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")

        if not self.enabled:
            logger.info("monitoring_disabled", reason="Langfuse not available or monitoring disabled")
        elif not self.langfuse_public_key or not self.langfuse_secret_key:
            logger.warning(
                "langfuse_not_configured",
                message="Langfuse credentials not found. Set LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY env vars.",
            )
            self.enabled = False


# Global monitoring configuration
_monitoring_config: Optional[MonitoringConfig] = None
_langfuse_client: Optional[Any] = None


def initialize_monitoring(config: Optional[MonitoringConfig] = None) -> None:
    """
    Initialize the monitoring system.

    Args:
        config: Monitoring configuration. If None, uses defaults from env vars.

    Example:
        >>> from src.core.monitoring import initialize_monitoring, MonitoringConfig
        >>> config = MonitoringConfig(
        ...     enabled=True,
        ...     langfuse_public_key="pk-...",
        ...     langfuse_secret_key="sk-...",
        ... )
        >>> initialize_monitoring(config)
    """
    global _monitoring_config, _langfuse_client

    if config is None:
        config = MonitoringConfig()

    _monitoring_config = config

    if config.enabled and LANGFUSE_AVAILABLE:
        try:
            _langfuse_client = Langfuse(
                public_key=config.langfuse_public_key,
                secret_key=config.langfuse_secret_key,
                host=config.langfuse_host,
            )
            logger.info(
                "monitoring_initialized",
                host=config.langfuse_host,
                track_tokens=config.track_tokens,
                track_latency=config.track_latency,
            )
        except Exception as e:
            logger.error("monitoring_initialization_failed", error=str(e))
            config.enabled = False
    else:
        logger.info("monitoring_disabled")


def is_monitoring_enabled() -> bool:
    """Check if monitoring is enabled."""
    return _monitoring_config is not None and _monitoring_config.enabled


def get_langfuse_client() -> Optional[Any]:
    """Get the Langfuse client instance."""
    return _langfuse_client


def trace_agent(name: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None):
    """
    Decorator to trace agent method execution.

    This decorator wraps agent methods with Langfuse observability,
    tracking execution time, inputs, outputs, and any errors.

    Args:
        name: Optional custom name for the trace (defaults to function name)
        metadata: Optional metadata to attach to the trace

    Example:
        >>> @trace_agent(name="query_analyzer", metadata={"version": "1.0"})
        >>> def analyze_query(self, state):
        ...     return result
    """

    def decorator(func: Callable) -> Callable:
        # If monitoring is disabled, return original function
        if not LANGFUSE_AVAILABLE or not is_monitoring_enabled():
            return func

        # Use Langfuse's @observe decorator
        trace_name = name or func.__name__
        observed_func = observe(name=trace_name)(func)

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Add metadata if provided
            if metadata and LANGFUSE_AVAILABLE:
                try:
                    langfuse_context.update_current_observation(metadata=metadata)
                except Exception as e:
                    logger.warning("failed_to_add_metadata", error=str(e))

            # Execute the function
            start_time = time.time()
            try:
                result = observed_func(*args, **kwargs)
                latency_ms = (time.time() - start_time) * 1000

                # Track latency
                if _monitoring_config and _monitoring_config.track_latency:
                    track_metric("latency_ms", latency_ms, metadata={"function": trace_name})

                return result

            except Exception as e:
                latency_ms = (time.time() - start_time) * 1000
                logger.error(
                    "agent_execution_error",
                    function=trace_name,
                    error=str(e),
                    latency_ms=latency_ms,
                )
                raise

        return wrapper

    return decorator


def track_metric(name: str, value: Any, metadata: Optional[Dict[str, Any]] = None) -> None:
    """
    Track a custom metric.

    Args:
        name: Metric name
        value: Metric value
        metadata: Optional metadata

    Example:
        >>> track_metric("retrieval_quality", 0.92, metadata={"query": "auth"})
    """
    if not is_monitoring_enabled():
        return

    try:
        if LANGFUSE_AVAILABLE and _langfuse_client:
            # Log metric via Langfuse
            langfuse_context.update_current_observation(
                metadata={
                    **({} if metadata is None else metadata),
                    f"metric_{name}": value,
                }
            )
        logger.info("metric_tracked", name=name, value=value, metadata=metadata)
    except Exception as e:
        logger.warning("metric_tracking_failed", name=name, error=str(e))


def track_routing_decision(
    query: str,
    intent: str,
    confidence: float,
    selected_agent: str,
    metadata: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Track an agent routing decision.

    Args:
        query: User query
        intent: Classified intent
        confidence: Confidence score
        selected_agent: Agent selected for execution
        metadata: Optional additional metadata

    Example:
        >>> track_routing_decision(
        ...     query="How to auth?",
        ...     intent="authentication",
        ...     confidence=0.95,
        ...     selected_agent="rag_agent"
        ... )
    """
    if not is_monitoring_enabled() or not _monitoring_config.track_routing:
        return

    routing_metadata = {
        "query_preview": query[:100],
        "intent": intent,
        "confidence": confidence,
        "selected_agent": selected_agent,
        **(metadata or {}),
    }

    track_metric("routing_decision", selected_agent, metadata=routing_metadata)
    logger.info(
        "routing_decision_tracked",
        intent=intent,
        confidence=confidence,
        agent=selected_agent,
    )


def track_retrieval_quality(
    query: str,
    num_docs: int,
    avg_score: float,
    top_score: float,
    metadata: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Track retrieval quality metrics.

    Args:
        query: Search query
        num_docs: Number of documents retrieved
        avg_score: Average similarity score
        top_score: Highest similarity score
        metadata: Optional additional metadata

    Example:
        >>> track_retrieval_quality(
        ...     query="user authentication",
        ...     num_docs=5,
        ...     avg_score=0.82,
        ...     top_score=0.95
        ... )
    """
    if not is_monitoring_enabled() or not _monitoring_config.track_quality:
        return

    quality_metadata = {
        "query_preview": query[:100],
        "num_docs": num_docs,
        "avg_score": avg_score,
        "top_score": top_score,
        **(metadata or {}),
    }

    track_metric("retrieval_quality", avg_score, metadata=quality_metadata)
    logger.info(
        "retrieval_quality_tracked",
        num_docs=num_docs,
        avg_score=avg_score,
        top_score=top_score,
    )


def track_token_usage(
    operation: str,
    prompt_tokens: int,
    completion_tokens: int,
    total_tokens: int,
    model: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Track LLM token usage.

    Args:
        operation: Operation name (e.g., "query_analysis", "code_generation")
        prompt_tokens: Number of prompt tokens
        completion_tokens: Number of completion tokens
        total_tokens: Total tokens used
        model: Model name
        metadata: Optional additional metadata

    Example:
        >>> track_token_usage(
        ...     operation="query_analysis",
        ...     prompt_tokens=150,
        ...     completion_tokens=50,
        ...     total_tokens=200,
        ...     model="deepseek-coder:6.7b"
        ... )
    """
    if not is_monitoring_enabled() or not _monitoring_config.track_tokens:
        return

    token_metadata = {
        "operation": operation,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
        "model": model,
        **(metadata or {}),
    }

    track_metric("token_usage", total_tokens, metadata=token_metadata)
    logger.info(
        "token_usage_tracked",
        operation=operation,
        total_tokens=total_tokens,
        model=model,
    )


@contextmanager
def trace_operation(name: str, metadata: Optional[Dict[str, Any]] = None):
    """
    Context manager for tracing operations.

    Args:
        name: Operation name
        metadata: Optional metadata

    Example:
        >>> with trace_operation("document_indexing", metadata={"file": "api.yaml"}):
        ...     # Your operation code here
        ...     index_document(doc)
    """
    start_time = time.time()
    operation_metadata = {"operation": name, **(metadata or {})}

    logger.info("operation_started", name=name, metadata=metadata)

    try:
        yield
        latency_ms = (time.time() - start_time) * 1000

        if is_monitoring_enabled() and _monitoring_config.track_latency:
            track_metric(f"{name}_latency_ms", latency_ms, metadata=operation_metadata)

        logger.info("operation_completed", name=name, latency_ms=latency_ms)

    except Exception as e:
        latency_ms = (time.time() - start_time) * 1000
        logger.error(
            "operation_failed",
            name=name,
            error=str(e),
            latency_ms=latency_ms,
        )
        raise


def flush_monitoring() -> None:
    """
    Flush all pending monitoring data.

    Call this before application shutdown to ensure all
    metrics are sent to Langfuse.

    Example:
        >>> flush_monitoring()
    """
    if is_monitoring_enabled() and _langfuse_client:
        try:
            _langfuse_client.flush()
            logger.info("monitoring_flushed")
        except Exception as e:
            logger.error("monitoring_flush_failed", error=str(e))


# Auto-initialize with defaults if env vars are set
if os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY"):
    initialize_monitoring()
else:
    logger.info(
        "monitoring_not_auto_initialized",
        message="Set LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY to enable monitoring",
    )
