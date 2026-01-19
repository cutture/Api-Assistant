"""
Rate limiting service for API endpoints.

Provides configurable rate limiting per user, IP, or API key
with sliding window algorithm for accurate request tracking.
"""

import asyncio
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
import structlog

logger = structlog.get_logger(__name__)


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""

    # Default limits (requests per window)
    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    requests_per_day: int = 10000

    # Execution-specific limits
    executions_per_minute: int = 10
    executions_per_hour: int = 100
    executions_per_day: int = 500

    # Per-user limits (override defaults for authenticated users)
    user_requests_per_minute: int = 120
    user_requests_per_hour: int = 2000
    user_requests_per_day: int = 20000

    # Premium user limits
    premium_requests_per_minute: int = 300
    premium_requests_per_hour: int = 5000
    premium_requests_per_day: int = 50000

    # Burst allowance (extra requests allowed in short burst)
    burst_allowance: int = 10

    # Cleanup interval for old entries
    cleanup_interval_seconds: int = 300


@dataclass
class RateLimitEntry:
    """Track request timestamps for rate limiting."""

    timestamps: List[float] = field(default_factory=list)
    last_cleanup: float = field(default_factory=time.time)

    def cleanup(self, max_age_seconds: float = 86400):
        """Remove timestamps older than max age."""
        cutoff = time.time() - max_age_seconds
        self.timestamps = [ts for ts in self.timestamps if ts > cutoff]
        self.last_cleanup = time.time()

    def count_in_window(self, window_seconds: float) -> int:
        """Count requests within a time window."""
        cutoff = time.time() - window_seconds
        return sum(1 for ts in self.timestamps if ts > cutoff)

    def add_request(self):
        """Record a new request."""
        self.timestamps.append(time.time())

        # Periodic cleanup
        if time.time() - self.last_cleanup > 300:
            self.cleanup()


@dataclass
class RateLimitResult:
    """Result of a rate limit check."""

    allowed: bool
    remaining: int
    reset_at: datetime
    limit: int
    window: str  # "minute", "hour", "day"
    retry_after_seconds: Optional[int] = None

    def to_headers(self) -> Dict[str, str]:
        """Convert to rate limit headers."""
        headers = {
            "X-RateLimit-Limit": str(self.limit),
            "X-RateLimit-Remaining": str(max(0, self.remaining)),
            "X-RateLimit-Reset": self.reset_at.isoformat(),
            "X-RateLimit-Window": self.window,
        }
        if self.retry_after_seconds:
            headers["Retry-After"] = str(self.retry_after_seconds)
        return headers


class RateLimiter:
    """
    Sliding window rate limiter.

    Supports multiple rate limit windows (minute, hour, day)
    and different limits for different user tiers.
    """

    def __init__(self, config: Optional[RateLimitConfig] = None):
        """Initialize rate limiter with configuration."""
        self.config = config or RateLimitConfig()
        self._entries: Dict[str, RateLimitEntry] = defaultdict(RateLimitEntry)
        self._lock = asyncio.Lock()
        self._last_cleanup = time.time()

    def _get_key(
        self,
        identifier: str,
        endpoint: str = "default",
        key_type: str = "ip"
    ) -> str:
        """Generate a unique key for rate limiting."""
        return f"{key_type}:{identifier}:{endpoint}"

    def _get_limits(
        self,
        user_tier: str = "anonymous"
    ) -> Tuple[int, int, int]:
        """
        Get rate limits based on user tier.

        Returns:
            Tuple of (per_minute, per_hour, per_day) limits
        """
        if user_tier == "premium":
            return (
                self.config.premium_requests_per_minute,
                self.config.premium_requests_per_hour,
                self.config.premium_requests_per_day,
            )
        elif user_tier == "registered":
            return (
                self.config.user_requests_per_minute,
                self.config.user_requests_per_hour,
                self.config.user_requests_per_day,
            )
        else:  # anonymous or guest
            return (
                self.config.requests_per_minute,
                self.config.requests_per_hour,
                self.config.requests_per_day,
            )

    def _get_execution_limits(
        self,
        user_tier: str = "anonymous"
    ) -> Tuple[int, int, int]:
        """Get execution-specific rate limits."""
        base_minute = self.config.executions_per_minute
        base_hour = self.config.executions_per_hour
        base_day = self.config.executions_per_day

        if user_tier == "premium":
            return (base_minute * 3, base_hour * 3, base_day * 3)
        elif user_tier == "registered":
            return (base_minute * 2, base_hour * 2, base_day * 2)
        else:
            return (base_minute, base_hour, base_day)

    async def check_rate_limit(
        self,
        identifier: str,
        endpoint: str = "default",
        key_type: str = "ip",
        user_tier: str = "anonymous",
        is_execution: bool = False,
    ) -> RateLimitResult:
        """
        Check if a request is allowed under rate limits.

        Args:
            identifier: User ID, IP address, or API key
            endpoint: Endpoint being accessed
            key_type: Type of identifier ("ip", "user", "api_key")
            user_tier: User tier for limit selection
            is_execution: Whether this is a code execution request

        Returns:
            RateLimitResult with allowed status and headers
        """
        async with self._lock:
            key = self._get_key(identifier, endpoint, key_type)
            entry = self._entries[key]

            # Get appropriate limits
            if is_execution:
                per_minute, per_hour, per_day = self._get_execution_limits(user_tier)
            else:
                per_minute, per_hour, per_day = self._get_limits(user_tier)

            # Check each window
            now = time.time()

            # Check per-minute limit
            minute_count = entry.count_in_window(60)
            if minute_count >= per_minute + self.config.burst_allowance:
                reset_at = datetime.fromtimestamp(now + 60, tz=timezone.utc)
                return RateLimitResult(
                    allowed=False,
                    remaining=0,
                    reset_at=reset_at,
                    limit=per_minute,
                    window="minute",
                    retry_after_seconds=60,
                )

            # Check per-hour limit
            hour_count = entry.count_in_window(3600)
            if hour_count >= per_hour:
                reset_at = datetime.fromtimestamp(now + 3600, tz=timezone.utc)
                return RateLimitResult(
                    allowed=False,
                    remaining=0,
                    reset_at=reset_at,
                    limit=per_hour,
                    window="hour",
                    retry_after_seconds=3600,
                )

            # Check per-day limit
            day_count = entry.count_in_window(86400)
            if day_count >= per_day:
                reset_at = datetime.fromtimestamp(now + 86400, tz=timezone.utc)
                return RateLimitResult(
                    allowed=False,
                    remaining=0,
                    reset_at=reset_at,
                    limit=per_day,
                    window="day",
                    retry_after_seconds=86400,
                )

            # Request is allowed, record it
            entry.add_request()

            # Return the most restrictive remaining count
            remaining_minute = per_minute - minute_count - 1
            remaining_hour = per_hour - hour_count - 1
            remaining_day = per_day - day_count - 1

            if remaining_minute <= remaining_hour and remaining_minute <= remaining_day:
                return RateLimitResult(
                    allowed=True,
                    remaining=remaining_minute,
                    reset_at=datetime.fromtimestamp(now + 60, tz=timezone.utc),
                    limit=per_minute,
                    window="minute",
                )
            elif remaining_hour <= remaining_day:
                return RateLimitResult(
                    allowed=True,
                    remaining=remaining_hour,
                    reset_at=datetime.fromtimestamp(now + 3600, tz=timezone.utc),
                    limit=per_hour,
                    window="hour",
                )
            else:
                return RateLimitResult(
                    allowed=True,
                    remaining=remaining_day,
                    reset_at=datetime.fromtimestamp(now + 86400, tz=timezone.utc),
                    limit=per_day,
                    window="day",
                )

    async def record_request(
        self,
        identifier: str,
        endpoint: str = "default",
        key_type: str = "ip",
    ):
        """Record a request without checking limits (for async tracking)."""
        async with self._lock:
            key = self._get_key(identifier, endpoint, key_type)
            self._entries[key].add_request()

    async def cleanup_old_entries(self):
        """Remove old entries to free memory."""
        async with self._lock:
            now = time.time()

            # Only cleanup periodically
            if now - self._last_cleanup < self.config.cleanup_interval_seconds:
                return

            self._last_cleanup = now

            # Cleanup each entry
            for entry in self._entries.values():
                entry.cleanup()

            # Remove empty entries
            empty_keys = [
                key for key, entry in self._entries.items()
                if not entry.timestamps
            ]
            for key in empty_keys:
                del self._entries[key]

            logger.debug(
                "Rate limiter cleanup complete",
                removed_entries=len(empty_keys),
                remaining_entries=len(self._entries),
            )

    def get_stats(self) -> Dict:
        """Get rate limiter statistics."""
        total_requests = sum(
            len(entry.timestamps) for entry in self._entries.values()
        )
        return {
            "total_tracked_identifiers": len(self._entries),
            "total_tracked_requests": total_requests,
            "config": {
                "requests_per_minute": self.config.requests_per_minute,
                "requests_per_hour": self.config.requests_per_hour,
                "requests_per_day": self.config.requests_per_day,
            },
        }


# Singleton instance
_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    """Get the global rate limiter instance."""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter
