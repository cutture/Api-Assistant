"""
Performance monitoring and optimization utilities.

Features:
- Performance profiling with timing decorators
- Query response time tracking
- Cache hit/miss metrics
- Bottleneck identification
- Performance reporting
"""

import functools
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional

import structlog

logger = structlog.get_logger(__name__)


# ============================================================================
# Performance Metrics Data Classes
# ============================================================================


@dataclass
class OperationMetrics:
    """Metrics for a single operation."""

    operation_name: str
    count: int = 0
    total_time: float = 0.0
    min_time: float = float("inf")
    max_time: float = 0.0
    errors: int = 0
    last_execution: Optional[datetime] = None

    @property
    def avg_time(self) -> float:
        """Calculate average execution time."""
        return self.total_time / self.count if self.count > 0 else 0.0

    def record(self, duration: float, error: bool = False) -> None:
        """Record a single execution."""
        self.count += 1
        self.total_time += duration
        self.min_time = min(self.min_time, duration)
        self.max_time = max(self.max_time, duration)
        self.last_execution = datetime.now()

        if error:
            self.errors += 1

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for reporting."""
        return {
            "operation": self.operation_name,
            "count": self.count,
            "total_time_s": round(self.total_time, 3),
            "avg_time_ms": round(self.avg_time * 1000, 2),
            "min_time_ms": round(self.min_time * 1000, 2),
            "max_time_ms": round(self.max_time * 1000, 2),
            "errors": self.errors,
            "error_rate": round(self.errors / self.count * 100, 2) if self.count > 0 else 0,
            "last_execution": self.last_execution.isoformat() if self.last_execution else None,
        }


@dataclass
class CacheMetrics:
    """Metrics for cache performance."""

    cache_name: str
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    size: int = 0
    max_size: int = 0

    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate."""
        total = self.hits + self.misses
        return (self.hits / total * 100) if total > 0 else 0.0

    def record_hit(self) -> None:
        """Record a cache hit."""
        self.hits += 1

    def record_miss(self) -> None:
        """Record a cache miss."""
        self.misses += 1

    def record_eviction(self) -> None:
        """Record a cache eviction."""
        self.evictions += 1

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for reporting."""
        return {
            "cache": self.cache_name,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": round(self.hit_rate, 2),
            "evictions": self.evictions,
            "size": self.size,
            "max_size": self.max_size,
            "utilization": round(self.size / self.max_size * 100, 2) if self.max_size > 0 else 0,
        }


# ============================================================================
# Performance Monitor Singleton
# ============================================================================


class PerformanceMonitor:
    """
    Singleton class for tracking application performance metrics.

    Usage:
        monitor = PerformanceMonitor.get_instance()
        monitor.record_operation("llm_generate", duration=1.5)
        report = monitor.get_report()
    """

    _instance: Optional["PerformanceMonitor"] = None
    _initialized: bool = False

    def __init__(self):
        """Initialize performance monitor."""
        if not PerformanceMonitor._initialized:
            self.operations: Dict[str, OperationMetrics] = defaultdict(
                lambda: OperationMetrics(operation_name="unknown")
            )
            self.caches: Dict[str, CacheMetrics] = {}
            self.start_time = datetime.now()
            PerformanceMonitor._initialized = True

    @classmethod
    def get_instance(cls) -> "PerformanceMonitor":
        """Get singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        """Reset the singleton instance (mainly for testing)."""
        cls._instance = None
        cls._initialized = False

    def record_operation(
        self,
        operation_name: str,
        duration: float,
        error: bool = False,
    ) -> None:
        """
        Record an operation execution.

        Args:
            operation_name: Name of the operation
            duration: Execution time in seconds
            error: Whether the operation failed
        """
        if operation_name not in self.operations:
            self.operations[operation_name] = OperationMetrics(operation_name=operation_name)

        self.operations[operation_name].record(duration, error)

        # Log slow operations
        if duration > 5.0:
            logger.warning(
                "slow_operation_detected",
                operation=operation_name,
                duration_s=round(duration, 3),
            )

    def register_cache(self, cache_name: str, max_size: int = 1000) -> None:
        """
        Register a cache for metrics tracking.

        Args:
            cache_name: Name of the cache
            max_size: Maximum cache size
        """
        if cache_name not in self.caches:
            self.caches[cache_name] = CacheMetrics(
                cache_name=cache_name,
                max_size=max_size,
            )

    def record_cache_hit(self, cache_name: str) -> None:
        """Record a cache hit."""
        if cache_name in self.caches:
            self.caches[cache_name].record_hit()

    def record_cache_miss(self, cache_name: str) -> None:
        """Record a cache miss."""
        if cache_name in self.caches:
            self.caches[cache_name].record_miss()

    def record_cache_eviction(self, cache_name: str) -> None:
        """Record a cache eviction."""
        if cache_name in self.caches:
            self.caches[cache_name].record_eviction()

    def update_cache_size(self, cache_name: str, size: int) -> None:
        """Update cache size."""
        if cache_name in self.caches:
            self.caches[cache_name].size = size

    def get_report(self) -> Dict[str, Any]:
        """
        Get performance report.

        Returns:
            Dictionary with performance metrics
        """
        uptime = datetime.now() - self.start_time

        operations_report = [
            metrics.to_dict() for metrics in sorted(
                self.operations.values(),
                key=lambda x: x.total_time,
                reverse=True,
            )
        ]

        caches_report = [
            metrics.to_dict() for metrics in sorted(
                self.caches.values(),
                key=lambda x: x.hit_rate,
                reverse=True,
            )
        ]

        return {
            "uptime_seconds": uptime.total_seconds(),
            "operations": operations_report,
            "caches": caches_report,
            "summary": {
                "total_operations": sum(op.count for op in self.operations.values()),
                "total_time_s": sum(op.total_time for op in self.operations.values()),
                "total_errors": sum(op.errors for op in self.operations.values()),
                "avg_cache_hit_rate": (
                    sum(c.hit_rate for c in self.caches.values()) / len(self.caches)
                    if self.caches
                    else 0
                ),
            },
        }

    def get_slow_operations(self, threshold_ms: float = 1000) -> List[Dict[str, Any]]:
        """
        Get operations slower than threshold.

        Args:
            threshold_ms: Threshold in milliseconds

        Returns:
            List of slow operations
        """
        threshold_s = threshold_ms / 1000
        slow_ops = [
            metrics.to_dict()
            for metrics in self.operations.values()
            if metrics.avg_time > threshold_s
        ]
        return sorted(slow_ops, key=lambda x: x["avg_time_ms"], reverse=True)


# ============================================================================
# Performance Decorators
# ============================================================================


def monitor_performance(operation_name: Optional[str] = None) -> Callable:
    """
    Decorator to monitor function performance.

    Args:
        operation_name: Override operation name (default: function name)

    Returns:
        Decorated function

    Example:
        @monitor_performance("process_query")
        def process_query(query: str):
            return result
    """

    def decorator(func: Callable) -> Callable:
        op_name = operation_name or func.__name__

        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            monitor = PerformanceMonitor.get_instance()
            start_time = time.perf_counter()
            error = False

            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                error = True
                raise
            finally:
                duration = time.perf_counter() - start_time
                monitor.record_operation(op_name, duration, error)

        return wrapper

    return decorator


def monitor_performance_async(operation_name: Optional[str] = None) -> Callable:
    """
    Async version of monitor_performance decorator.

    Args:
        operation_name: Override operation name (default: function name)

    Returns:
        Decorated async function

    Example:
        @monitor_performance_async("fetch_data")
        async def fetch_data(url: str):
            return data
    """

    def decorator(func: Callable) -> Callable:
        op_name = operation_name or func.__name__

        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            monitor = PerformanceMonitor.get_instance()
            start_time = time.perf_counter()
            error = False

            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                error = True
                raise
            finally:
                duration = time.perf_counter() - start_time
                monitor.record_operation(op_name, duration, error)

        return wrapper

    return decorator


# ============================================================================
# Convenience Functions
# ============================================================================


def get_performance_report() -> Dict[str, Any]:
    """Get current performance report."""
    monitor = PerformanceMonitor.get_instance()
    return monitor.get_report()


def get_slow_operations(threshold_ms: float = 1000) -> List[Dict[str, Any]]:
    """Get operations slower than threshold."""
    monitor = PerformanceMonitor.get_instance()
    return monitor.get_slow_operations(threshold_ms)


def log_performance_report() -> None:
    """Log performance report to logger."""
    report = get_performance_report()

    logger.info(
        "performance_report",
        uptime_s=round(report["uptime_seconds"], 2),
        total_operations=report["summary"]["total_operations"],
        total_errors=report["summary"]["total_errors"],
        avg_cache_hit_rate=round(report["summary"]["avg_cache_hit_rate"], 2),
    )

    # Log slow operations
    slow_ops = get_slow_operations(threshold_ms=1000)
    if slow_ops:
        logger.warning(
            "slow_operations_detected",
            count=len(slow_ops),
            operations=[op["operation"] for op in slow_ops[:5]],
        )
