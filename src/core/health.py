"""
Health check system for monitoring service status.

This module provides health checks for all critical services:
- LLM providers (Ollama, Groq)
- Vector store (ChromaDB)
- Web search
- Embedding service
"""

from datetime import datetime
from enum import Enum
from typing import Dict, Optional

import structlog

from src.config import settings
from src.core.circuit_breaker import (
    llm_circuit_breaker,
    vector_store_circuit_breaker,
    web_search_circuit_breaker,
)

logger = structlog.get_logger(__name__)


class HealthStatus(Enum):
    """Health status indicators."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class HealthCheck:
    """
    Health check coordinator for all system services.

    Example:
        ```python
        health = HealthCheck()
        status = health.check_all()

        if status["status"] == HealthStatus.HEALTHY:
            print("All systems operational")
        ```
    """

    def __init__(self):
        """Initialize health checker."""
        self.last_check_time: Optional[datetime] = None
        self.cached_status: Optional[Dict] = None
        self.cache_duration = 30  # seconds

    def check_all(self, use_cache: bool = True) -> Dict:
        """
        Check health of all services.

        Args:
            use_cache: Use cached result if available

        Returns:
            Dictionary with overall status and individual service statuses
        """
        # Return cached result if recent
        if use_cache and self._is_cache_valid():
            logger.debug("health_check_using_cache")
            return self.cached_status

        logger.info("health_check_starting")
        start_time = datetime.now()

        # Check each service
        llm_health = self.check_llm()
        vector_store_health = self.check_vector_store()
        web_search_health = self.check_web_search()
        embeddings_health = self.check_embeddings()

        # Determine overall status
        overall_status = self._determine_overall_status(
            [llm_health, vector_store_health, web_search_health, embeddings_health]
        )

        # Compile results
        result = {
            "status": overall_status.value,
            "timestamp": datetime.now().isoformat(),
            "check_duration_ms": int((datetime.now() - start_time).total_seconds() * 1000),
            "services": {
                "llm": llm_health,
                "vector_store": vector_store_health,
                "web_search": web_search_health,
                "embeddings": embeddings_health,
            },
        }

        # Cache the result
        self.last_check_time = datetime.now()
        self.cached_status = result

        logger.info(
            "health_check_completed",
            status=overall_status.value,
            duration_ms=result["check_duration_ms"],
        )

        return result

    def check_llm(self) -> Dict:
        """
        Check LLM service health.

        Returns:
            Dictionary with LLM health status
        """
        try:
            circuit_state = llm_circuit_breaker.get_state()

            # Check circuit breaker state
            if circuit_state["state"] == "closed":
                status = HealthStatus.HEALTHY
                message = f"LLM available ({settings.llm_provider})"
            elif circuit_state["state"] == "half_open":
                status = HealthStatus.DEGRADED
                message = "LLM recovering from failures"
            else:  # open
                status = HealthStatus.UNHEALTHY
                message = f"LLM unavailable (circuit open, retry in {circuit_state['seconds_until_retry']}s)"

            return {
                "status": status.value,
                "message": message,
                "provider": settings.llm_provider,
                "circuit_breaker": circuit_state,
            }

        except Exception as e:
            logger.error("llm_health_check_failed", error=str(e))
            return {
                "status": HealthStatus.UNHEALTHY.value,
                "message": f"Health check failed: {str(e)}",
                "provider": settings.llm_provider,
            }

    def check_vector_store(self) -> Dict:
        """
        Check vector store health.

        Returns:
            Dictionary with vector store health status
        """
        try:
            from src.core.vector_store import get_vector_store

            vector_store = get_vector_store()
            circuit_state = vector_store_circuit_breaker.get_state()

            # Check circuit breaker state
            if circuit_state["state"] == "closed":
                # Try a simple collection operation
                try:
                    collection = vector_store._collection
                    count = collection.count()

                    status = HealthStatus.HEALTHY
                    message = f"Vector store operational ({count} documents)"
                except Exception as e:
                    status = HealthStatus.DEGRADED
                    message = f"Vector store accessible but errors occurred: {str(e)}"
            elif circuit_state["state"] == "half_open":
                status = HealthStatus.DEGRADED
                message = "Vector store recovering from failures"
            else:  # open
                status = HealthStatus.UNHEALTHY
                message = f"Vector store unavailable (circuit open, retry in {circuit_state['seconds_until_retry']}s)"

            return {
                "status": status.value,
                "message": message,
                "circuit_breaker": circuit_state,
            }

        except Exception as e:
            logger.error("vector_store_health_check_failed", error=str(e))
            return {
                "status": HealthStatus.UNHEALTHY.value,
                "message": f"Health check failed: {str(e)}",
            }

    def check_web_search(self) -> Dict:
        """
        Check web search service health.

        Returns:
            Dictionary with web search health status
        """
        try:
            circuit_state = web_search_circuit_breaker.get_state()

            # Check circuit breaker state
            if circuit_state["state"] == "closed":
                status = HealthStatus.HEALTHY
                message = "Web search available"
            elif circuit_state["state"] == "half_open":
                status = HealthStatus.DEGRADED
                message = "Web search recovering from failures"
            else:  # open
                status = HealthStatus.UNHEALTHY
                message = f"Web search unavailable (circuit open, retry in {circuit_state['seconds_until_retry']}s)"

            return {
                "status": status.value,
                "message": message,
                "enabled": settings.enable_web_search,
                "circuit_breaker": circuit_state,
            }

        except Exception as e:
            logger.error("web_search_health_check_failed", error=str(e))
            return {
                "status": HealthStatus.UNHEALTHY.value,
                "message": f"Health check failed: {str(e)}",
                "enabled": settings.enable_web_search,
            }

    def check_embeddings(self) -> Dict:
        """
        Check embedding service health.

        Returns:
            Dictionary with embeddings health status
        """
        try:
            from src.core.embeddings import EmbeddingService

            embedding_service = EmbeddingService()

            # Try a simple embedding
            try:
                test_text = "health check test"
                embedding = embedding_service.embed_text(test_text)

                if embedding and len(embedding) > 0:
                    status = HealthStatus.HEALTHY
                    message = f"Embeddings operational (dimension: {len(embedding)})"
                else:
                    status = HealthStatus.UNHEALTHY
                    message = "Embeddings returned empty result"

            except Exception as e:
                status = HealthStatus.UNHEALTHY
                message = f"Embedding generation failed: {str(e)}"

            return {
                "status": status.value,
                "message": message,
                "model": settings.embedding_model,
            }

        except Exception as e:
            logger.error("embeddings_health_check_failed", error=str(e))
            return {
                "status": HealthStatus.UNHEALTHY.value,
                "message": f"Health check failed: {str(e)}",
                "model": settings.embedding_model,
            }

    def _determine_overall_status(self, service_statuses: list[Dict]) -> HealthStatus:
        """
        Determine overall system health from individual service statuses.

        Args:
            service_statuses: List of service status dictionaries

        Returns:
            Overall health status
        """
        # Count status types
        unhealthy_count = sum(
            1 for s in service_statuses if s["status"] == HealthStatus.UNHEALTHY.value
        )
        degraded_count = sum(
            1 for s in service_statuses if s["status"] == HealthStatus.DEGRADED.value
        )

        # Determine overall status
        if unhealthy_count > 0:
            # Any unhealthy service makes the whole system unhealthy
            return HealthStatus.UNHEALTHY
        elif degraded_count > 0:
            # Any degraded service makes the whole system degraded
            return HealthStatus.DEGRADED
        else:
            # All services healthy
            return HealthStatus.HEALTHY

    def _is_cache_valid(self) -> bool:
        """
        Check if cached health status is still valid.

        Returns:
            True if cache is valid
        """
        if self.last_check_time is None or self.cached_status is None:
            return False

        elapsed = (datetime.now() - self.last_check_time).total_seconds()
        return elapsed < self.cache_duration


# ============================================================================
# Global health check instance
# ============================================================================

_health_check_instance: Optional[HealthCheck] = None


def get_health_check() -> HealthCheck:
    """
    Get or create the global health check instance.

    Returns:
        HealthCheck instance
    """
    global _health_check_instance

    if _health_check_instance is None:
        _health_check_instance = HealthCheck()

    return _health_check_instance


def check_system_health(use_cache: bool = True) -> Dict:
    """
    Convenience function to check overall system health.

    Args:
        use_cache: Use cached result if available

    Returns:
        Dictionary with system health status
    """
    health_check = get_health_check()
    return health_check.check_all(use_cache=use_cache)
