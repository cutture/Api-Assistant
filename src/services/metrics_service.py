"""
Metrics and cost tracking service.

Tracks execution metrics, LLM costs, and usage analytics
for monitoring and billing purposes.
"""

import asyncio
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional
import structlog

logger = structlog.get_logger(__name__)


class MetricType(str, Enum):
    """Types of metrics tracked."""

    EXECUTION = "execution"
    LLM_CALL = "llm_call"
    SEARCH = "search"
    ARTIFACT = "artifact"
    PREVIEW = "preview"
    API_REQUEST = "api_request"


class ExecutionStatus(str, Enum):
    """Status of code executions."""

    STARTED = "started"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


@dataclass
class LLMCost:
    """Cost information for an LLM call."""

    provider: str
    model: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    duration_ms: int
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class ExecutionMetric:
    """Metrics for a single code execution."""

    execution_id: str
    user_id: Optional[str]
    language: str
    status: ExecutionStatus
    attempt_count: int
    duration_ms: int
    llm_costs: List[LLMCost] = field(default_factory=list)
    test_passed: bool = False
    lint_passed: bool = False
    security_passed: bool = False
    quality_score: Optional[int] = None
    error_type: Optional[str] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def total_llm_cost(self) -> float:
        """Total LLM cost for this execution."""
        return sum(c.cost_usd for c in self.llm_costs)


@dataclass
class UserMetrics:
    """Aggregated metrics for a user."""

    user_id: str
    total_executions: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
    total_llm_cost: float = 0.0
    total_execution_time_ms: int = 0
    languages_used: Dict[str, int] = field(default_factory=dict)
    average_quality_score: float = 0.0
    last_activity: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class DailyMetrics:
    """Daily aggregated metrics."""

    date: str  # YYYY-MM-DD
    total_executions: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
    total_llm_cost: float = 0.0
    unique_users: int = 0
    total_api_requests: int = 0
    average_response_time_ms: float = 0.0


class MetricsService:
    """
    Service for tracking metrics and costs.

    Provides real-time tracking of executions, LLM usage,
    and cost monitoring with alerting capabilities.
    """

    # LLM cost estimates per 1K tokens (USD)
    LLM_COSTS = {
        "groq": {
            "llama-3.3-70b-versatile": {"input": 0.0008, "output": 0.0008},
            "llama-3.1-8b-instant": {"input": 0.0001, "output": 0.0001},
            "mixtral-8x7b-32768": {"input": 0.0005, "output": 0.0005},
        },
        "ollama": {
            # Local models - effectively free
            "deepseek-coder:6.7b": {"input": 0.0, "output": 0.0},
            "llama3.1:8b": {"input": 0.0, "output": 0.0},
            "codellama:13b": {"input": 0.0, "output": 0.0},
        },
        "anthropic": {
            "claude-3-5-sonnet-20241022": {"input": 0.003, "output": 0.015},
            "claude-3-5-haiku-20241022": {"input": 0.0008, "output": 0.004},
        },
        "openai": {
            "gpt-4o": {"input": 0.005, "output": 0.015},
            "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
        },
    }

    def __init__(
        self,
        cost_alert_threshold: float = 50.0,
        cost_limit_monthly: float = 200.0,
    ):
        """
        Initialize metrics service.

        Args:
            cost_alert_threshold: Cost threshold for alerts (USD)
            cost_limit_monthly: Monthly cost limit (USD)
        """
        self.cost_alert_threshold = cost_alert_threshold
        self.cost_limit_monthly = cost_limit_monthly

        # In-memory storage (could be backed by database)
        self._executions: List[ExecutionMetric] = []
        self._llm_calls: List[LLMCost] = []
        self._user_metrics: Dict[str, UserMetrics] = {}
        self._daily_metrics: Dict[str, DailyMetrics] = {}
        self._api_requests: Dict[str, int] = defaultdict(int)

        self._lock = asyncio.Lock()

    def _get_today(self) -> str:
        """Get today's date string."""
        return datetime.now(timezone.utc).strftime("%Y-%m-%d")

    def _estimate_llm_cost(
        self,
        provider: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
    ) -> float:
        """Estimate LLM cost based on token usage."""
        provider_costs = self.LLM_COSTS.get(provider, {})
        model_costs = provider_costs.get(model, {"input": 0.001, "output": 0.001})

        input_cost = (input_tokens / 1000) * model_costs["input"]
        output_cost = (output_tokens / 1000) * model_costs["output"]

        return round(input_cost + output_cost, 6)

    async def record_llm_call(
        self,
        provider: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        duration_ms: int,
        user_id: Optional[str] = None,
    ) -> LLMCost:
        """
        Record an LLM API call.

        Args:
            provider: LLM provider name
            model: Model identifier
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            duration_ms: Call duration in milliseconds
            user_id: Optional user ID

        Returns:
            LLMCost record
        """
        cost_usd = self._estimate_llm_cost(provider, model, input_tokens, output_tokens)

        llm_cost = LLMCost(
            provider=provider,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost_usd,
            duration_ms=duration_ms,
        )

        async with self._lock:
            self._llm_calls.append(llm_cost)

            # Update user metrics
            if user_id:
                if user_id not in self._user_metrics:
                    self._user_metrics[user_id] = UserMetrics(user_id=user_id)
                self._user_metrics[user_id].total_llm_cost += cost_usd
                self._user_metrics[user_id].last_activity = datetime.now(timezone.utc)

            # Update daily metrics
            today = self._get_today()
            if today not in self._daily_metrics:
                self._daily_metrics[today] = DailyMetrics(date=today)
            self._daily_metrics[today].total_llm_cost += cost_usd

        logger.debug(
            "LLM call recorded",
            provider=provider,
            model=model,
            tokens=input_tokens + output_tokens,
            cost_usd=cost_usd,
        )

        return llm_cost

    async def record_execution(
        self,
        execution_id: str,
        user_id: Optional[str],
        language: str,
        status: ExecutionStatus,
        attempt_count: int,
        duration_ms: int,
        llm_costs: Optional[List[LLMCost]] = None,
        test_passed: bool = False,
        lint_passed: bool = False,
        security_passed: bool = False,
        quality_score: Optional[int] = None,
        error_type: Optional[str] = None,
    ) -> ExecutionMetric:
        """
        Record a code execution.

        Args:
            execution_id: Unique execution identifier
            user_id: User who initiated the execution
            language: Programming language
            status: Execution status
            attempt_count: Number of validation attempts
            duration_ms: Total execution duration
            llm_costs: List of LLM costs for this execution
            test_passed: Whether tests passed
            lint_passed: Whether lint passed
            security_passed: Whether security scan passed
            quality_score: Code quality score (1-10)
            error_type: Type of error if failed

        Returns:
            ExecutionMetric record
        """
        metric = ExecutionMetric(
            execution_id=execution_id,
            user_id=user_id,
            language=language,
            status=status,
            attempt_count=attempt_count,
            duration_ms=duration_ms,
            llm_costs=llm_costs or [],
            test_passed=test_passed,
            lint_passed=lint_passed,
            security_passed=security_passed,
            quality_score=quality_score,
            error_type=error_type,
        )

        async with self._lock:
            self._executions.append(metric)

            # Update user metrics
            if user_id:
                if user_id not in self._user_metrics:
                    self._user_metrics[user_id] = UserMetrics(user_id=user_id)

                user = self._user_metrics[user_id]
                user.total_executions += 1
                user.total_execution_time_ms += duration_ms
                user.total_llm_cost += metric.total_llm_cost
                user.last_activity = datetime.now(timezone.utc)

                if status == ExecutionStatus.COMPLETED:
                    user.successful_executions += 1
                else:
                    user.failed_executions += 1

                # Track language usage
                user.languages_used[language] = user.languages_used.get(language, 0) + 1

                # Update average quality score
                if quality_score:
                    total_quality = user.average_quality_score * (user.total_executions - 1)
                    user.average_quality_score = (total_quality + quality_score) / user.total_executions

            # Update daily metrics
            today = self._get_today()
            if today not in self._daily_metrics:
                self._daily_metrics[today] = DailyMetrics(date=today)

            daily = self._daily_metrics[today]
            daily.total_executions += 1
            if status == ExecutionStatus.COMPLETED:
                daily.successful_executions += 1
            else:
                daily.failed_executions += 1
            daily.total_llm_cost += metric.total_llm_cost

            # Track unique users
            if user_id:
                # Simplistic unique user tracking
                daily.unique_users = len(self._user_metrics)

        logger.info(
            "Execution recorded",
            execution_id=execution_id,
            status=status.value,
            language=language,
            duration_ms=duration_ms,
            llm_cost=metric.total_llm_cost,
        )

        return metric

    async def record_api_request(
        self,
        endpoint: str,
        method: str,
        response_time_ms: int,
        status_code: int,
        user_id: Optional[str] = None,
    ):
        """Record an API request for analytics."""
        async with self._lock:
            key = f"{method}:{endpoint}"
            self._api_requests[key] += 1

            # Update daily metrics
            today = self._get_today()
            if today not in self._daily_metrics:
                self._daily_metrics[today] = DailyMetrics(date=today)

            daily = self._daily_metrics[today]
            daily.total_api_requests += 1

            # Update average response time
            total_time = daily.average_response_time_ms * (daily.total_api_requests - 1)
            daily.average_response_time_ms = (total_time + response_time_ms) / daily.total_api_requests

    async def get_cost_summary(
        self,
        user_id: Optional[str] = None,
        days: int = 30,
    ) -> Dict[str, Any]:
        """
        Get cost summary for a period.

        Args:
            user_id: Optional filter by user
            days: Number of days to include

        Returns:
            Cost summary dictionary
        """
        async with self._lock:
            cutoff = datetime.now(timezone.utc) - timedelta(days=days)

            if user_id:
                user = self._user_metrics.get(user_id)
                if not user:
                    return {"total_cost": 0.0, "executions": 0}

                return {
                    "user_id": user_id,
                    "total_cost": user.total_llm_cost,
                    "total_executions": user.total_executions,
                    "successful_executions": user.successful_executions,
                    "failed_executions": user.failed_executions,
                    "average_quality_score": user.average_quality_score,
                    "languages": user.languages_used,
                }

            # System-wide summary
            total_cost = sum(
                m.total_llm_cost
                for m in self._daily_metrics.values()
                if datetime.strptime(m.date, "%Y-%m-%d").replace(tzinfo=timezone.utc) > cutoff
            )

            total_executions = sum(
                m.total_executions
                for m in self._daily_metrics.values()
                if datetime.strptime(m.date, "%Y-%m-%d").replace(tzinfo=timezone.utc) > cutoff
            )

            return {
                "total_cost": total_cost,
                "total_executions": total_executions,
                "cost_limit": self.cost_limit_monthly,
                "cost_alert_threshold": self.cost_alert_threshold,
                "budget_remaining": self.cost_limit_monthly - total_cost,
                "budget_used_percent": (total_cost / self.cost_limit_monthly * 100) if self.cost_limit_monthly > 0 else 0,
            }

    async def check_cost_alerts(self) -> List[Dict[str, Any]]:
        """Check for cost-related alerts."""
        alerts = []
        summary = await self.get_cost_summary(days=30)

        if summary["total_cost"] >= self.cost_alert_threshold:
            alerts.append({
                "type": "cost_threshold",
                "severity": "warning",
                "message": f"Monthly cost (${summary['total_cost']:.2f}) has exceeded alert threshold (${self.cost_alert_threshold:.2f})",
                "current_cost": summary["total_cost"],
                "threshold": self.cost_alert_threshold,
            })

        if summary["total_cost"] >= self.cost_limit_monthly * 0.9:
            alerts.append({
                "type": "cost_limit_approaching",
                "severity": "critical",
                "message": f"Monthly cost is at {summary['budget_used_percent']:.1f}% of limit",
                "current_cost": summary["total_cost"],
                "limit": self.cost_limit_monthly,
            })

        return alerts

    async def get_dashboard_stats(self) -> Dict[str, Any]:
        """Get statistics for dashboard display."""
        async with self._lock:
            today = self._get_today()
            daily = self._daily_metrics.get(today, DailyMetrics(date=today))

            # Last 7 days trend
            trend = []
            for i in range(7):
                date = (datetime.now(timezone.utc) - timedelta(days=i)).strftime("%Y-%m-%d")
                metrics = self._daily_metrics.get(date, DailyMetrics(date=date))
                trend.append({
                    "date": date,
                    "executions": metrics.total_executions,
                    "cost": metrics.total_llm_cost,
                    "success_rate": (
                        metrics.successful_executions / metrics.total_executions * 100
                        if metrics.total_executions > 0 else 0
                    ),
                })

            return {
                "today": {
                    "executions": daily.total_executions,
                    "successful": daily.successful_executions,
                    "failed": daily.failed_executions,
                    "cost": daily.total_llm_cost,
                    "unique_users": daily.unique_users,
                    "api_requests": daily.total_api_requests,
                    "avg_response_time_ms": daily.average_response_time_ms,
                },
                "trend": list(reversed(trend)),
                "totals": {
                    "users": len(self._user_metrics),
                    "executions": len(self._executions),
                    "llm_calls": len(self._llm_calls),
                },
            }

    async def get_user_metrics(self, user_id: str) -> Optional[UserMetrics]:
        """Get metrics for a specific user."""
        async with self._lock:
            return self._user_metrics.get(user_id)

    async def get_execution_history(
        self,
        user_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[ExecutionMetric]:
        """Get execution history."""
        async with self._lock:
            executions = self._executions
            if user_id:
                executions = [e for e in executions if e.user_id == user_id]

            return list(reversed(executions[-limit:]))


# Singleton instance
_metrics_service: Optional[MetricsService] = None


def get_metrics_service() -> MetricsService:
    """Get the global metrics service instance."""
    global _metrics_service
    if _metrics_service is None:
        _metrics_service = MetricsService()
    return _metrics_service
