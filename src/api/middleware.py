"""
FastAPI middleware for rate limiting, metrics, and error tracking.

Provides request-level tracking and protection.
"""

import time
from typing import Callable, Optional
import structlog
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from src.services.rate_limiter import get_rate_limiter, RateLimitResult
from src.services.metrics_service import get_metrics_service

logger = structlog.get_logger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware.

    Applies rate limits based on IP address or user ID.
    """

    # Endpoints exempt from rate limiting
    EXEMPT_PATHS = {
        "/health",
        "/docs",
        "/redoc",
        "/openapi.json",
    }

    # Endpoints with execution-specific limits
    EXECUTION_PATHS = {
        "/execute",
        "/execute/",
    }

    def __init__(self, app, enabled: bool = True):
        """
        Initialize rate limit middleware.

        Args:
            app: FastAPI application
            enabled: Whether rate limiting is enabled
        """
        super().__init__(app)
        self.enabled = enabled
        self.rate_limiter = get_rate_limiter()

    def _get_client_identifier(self, request: Request) -> tuple[str, str]:
        """
        Get client identifier for rate limiting.

        Returns:
            Tuple of (identifier, key_type)
        """
        # Check for user ID from auth
        user_id = getattr(request.state, "user_id", None)
        if user_id:
            return (user_id, "user")

        # Check for API key
        api_key = request.headers.get("X-API-Key")
        if api_key:
            return (api_key[:16], "api_key")  # Only use first 16 chars

        # Fall back to IP address
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Get the first IP in the chain
            client_ip = forwarded_for.split(",")[0].strip()
        else:
            client_ip = request.client.host if request.client else "unknown"

        return (client_ip, "ip")

    def _get_user_tier(self, request: Request) -> str:
        """Get user tier for rate limit selection."""
        # Check if user is premium (would come from auth)
        is_premium = getattr(request.state, "is_premium", False)
        if is_premium:
            return "premium"

        # Check if user is authenticated
        user_id = getattr(request.state, "user_id", None)
        if user_id:
            return "registered"

        return "anonymous"

    async def dispatch(
        self,
        request: Request,
        call_next: Callable,
    ) -> Response:
        """Process request through rate limiter."""
        # Skip if disabled or exempt path
        if not self.enabled or request.url.path in self.EXEMPT_PATHS:
            return await call_next(request)

        # Get client identifier
        identifier, key_type = self._get_client_identifier(request)
        user_tier = self._get_user_tier(request)

        # Check if this is an execution endpoint
        is_execution = any(
            request.url.path.startswith(path)
            for path in self.EXECUTION_PATHS
        )

        # Check rate limit
        result = await self.rate_limiter.check_rate_limit(
            identifier=identifier,
            endpoint=request.url.path,
            key_type=key_type,
            user_tier=user_tier,
            is_execution=is_execution,
        )

        # Add rate limit headers to response
        if not result.allowed:
            logger.warning(
                "Rate limit exceeded",
                identifier=identifier[:8] + "...",
                endpoint=request.url.path,
                window=result.window,
            )

            return JSONResponse(
                status_code=429,
                content={
                    "error": "TooManyRequests",
                    "message": f"Rate limit exceeded. Retry after {result.retry_after_seconds} seconds.",
                    "retry_after": result.retry_after_seconds,
                    "limit": result.limit,
                    "window": result.window,
                },
                headers=result.to_headers(),
            )

        # Process request
        response = await call_next(request)

        # Add rate limit headers to successful response
        for key, value in result.to_headers().items():
            response.headers[key] = value

        return response


class MetricsMiddleware(BaseHTTPMiddleware):
    """
    Metrics collection middleware.

    Tracks request timing and endpoint usage.
    """

    # Endpoints exempt from metrics
    EXEMPT_PATHS = {
        "/health",
        "/docs",
        "/redoc",
        "/openapi.json",
    }

    def __init__(self, app, enabled: bool = True):
        """
        Initialize metrics middleware.

        Args:
            app: FastAPI application
            enabled: Whether metrics collection is enabled
        """
        super().__init__(app)
        self.enabled = enabled
        self.metrics_service = get_metrics_service()

    async def dispatch(
        self,
        request: Request,
        call_next: Callable,
    ) -> Response:
        """Process request and collect metrics."""
        # Skip if disabled or exempt path
        if not self.enabled or request.url.path in self.EXEMPT_PATHS:
            return await call_next(request)

        # Record start time
        start_time = time.perf_counter()

        # Process request
        response = await call_next(request)

        # Calculate duration
        duration_ms = int((time.perf_counter() - start_time) * 1000)

        # Get user ID if available
        user_id = getattr(request.state, "user_id", None)

        # Record metrics
        try:
            await self.metrics_service.record_api_request(
                endpoint=request.url.path,
                method=request.method,
                response_time_ms=duration_ms,
                status_code=response.status_code,
                user_id=user_id,
            )
        except Exception as e:
            logger.warning("Failed to record metrics", error=str(e))

        # Add timing header
        response.headers["X-Response-Time-Ms"] = str(duration_ms)

        return response


class ErrorTrackingMiddleware(BaseHTTPMiddleware):
    """
    Error tracking middleware.

    Captures and reports errors for monitoring.
    Integrates with Sentry when configured.
    """

    def __init__(self, app, sentry_dsn: Optional[str] = None):
        """
        Initialize error tracking middleware.

        Args:
            app: FastAPI application
            sentry_dsn: Optional Sentry DSN for error reporting
        """
        super().__init__(app)
        self.sentry_initialized = False

        if sentry_dsn:
            try:
                import sentry_sdk
                from sentry_sdk.integrations.fastapi import FastApiIntegration
                from sentry_sdk.integrations.starlette import StarletteIntegration

                sentry_sdk.init(
                    dsn=sentry_dsn,
                    integrations=[
                        StarletteIntegration(),
                        FastApiIntegration(),
                    ],
                    traces_sample_rate=0.1,
                    profiles_sample_rate=0.1,
                )
                self.sentry_initialized = True
                logger.info("Sentry error tracking initialized")
            except ImportError:
                logger.warning("sentry-sdk not installed, error tracking disabled")
            except Exception as e:
                logger.error("Failed to initialize Sentry", error=str(e))

    async def dispatch(
        self,
        request: Request,
        call_next: Callable,
    ) -> Response:
        """Process request with error tracking."""
        try:
            response = await call_next(request)
            return response
        except Exception as exc:
            # Log the error
            logger.error(
                "Unhandled exception in request",
                path=request.url.path,
                method=request.method,
                error=str(exc),
                exc_info=exc,
            )

            # Report to Sentry if available
            if self.sentry_initialized:
                try:
                    import sentry_sdk
                    sentry_sdk.capture_exception(exc)
                except Exception:
                    pass

            # Re-raise to let FastAPI handle it
            raise


def setup_middleware(app, config: dict = None):
    """
    Set up all middleware on a FastAPI app.

    Args:
        app: FastAPI application
        config: Optional configuration dictionary
    """
    config = config or {}

    # Add error tracking first (outermost)
    sentry_dsn = config.get("sentry_dsn")
    if sentry_dsn:
        app.add_middleware(ErrorTrackingMiddleware, sentry_dsn=sentry_dsn)

    # Add metrics collection
    enable_metrics = config.get("enable_metrics", True)
    app.add_middleware(MetricsMiddleware, enabled=enable_metrics)

    # Add rate limiting
    enable_rate_limiting = config.get("enable_rate_limiting", True)
    app.add_middleware(RateLimitMiddleware, enabled=enable_rate_limiting)

    logger.info(
        "Middleware configured",
        rate_limiting=enable_rate_limiting,
        metrics=enable_metrics,
        sentry=bool(sentry_dsn),
    )
