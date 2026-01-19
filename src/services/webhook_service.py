"""
Webhook service for CI/CD integration and notifications.

Provides webhook management for:
- Execution notifications (on complete, on failure)
- CI/CD pipeline triggers
- Slack/Discord notifications
- Custom HTTP callbacks
"""

import asyncio
import hashlib
import hmac
import secrets
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
import structlog
import httpx

logger = structlog.get_logger(__name__)


class WebhookEvent(str, Enum):
    """Types of events that can trigger webhooks."""

    EXECUTION_STARTED = "execution.started"
    EXECUTION_COMPLETED = "execution.completed"
    EXECUTION_FAILED = "execution.failed"
    EXECUTION_RETRY = "execution.retry"
    ARTIFACT_CREATED = "artifact.created"
    PREVIEW_STARTED = "preview.started"
    PREVIEW_STOPPED = "preview.stopped"
    SECURITY_ALERT = "security.alert"
    COST_ALERT = "cost.alert"


class WebhookStatus(str, Enum):
    """Status of a webhook."""

    ACTIVE = "active"
    PAUSED = "paused"
    FAILED = "failed"  # Too many failures
    DELETED = "deleted"


class WebhookProvider(str, Enum):
    """Built-in webhook providers."""

    CUSTOM = "custom"
    SLACK = "slack"
    DISCORD = "discord"
    GITHUB = "github"
    GITLAB = "gitlab"


@dataclass
class WebhookDelivery:
    """Record of a webhook delivery attempt."""

    id: str
    webhook_id: str
    event: WebhookEvent
    payload: Dict[str, Any]
    status_code: Optional[int] = None
    response_body: Optional[str] = None
    error: Optional[str] = None
    duration_ms: int = 0
    attempt: int = 1
    success: bool = False
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class Webhook:
    """Webhook configuration."""

    id: str
    user_id: str
    name: str
    url: str
    events: List[WebhookEvent]
    provider: WebhookProvider = WebhookProvider.CUSTOM
    secret: str = ""  # For signature verification
    headers: Dict[str, str] = field(default_factory=dict)
    status: WebhookStatus = WebhookStatus.ACTIVE
    failure_count: int = 0
    last_triggered_at: Optional[datetime] = None
    last_success_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "url": self.url,
            "events": [e.value for e in self.events],
            "provider": self.provider.value,
            "status": self.status.value,
            "failure_count": self.failure_count,
            "last_triggered_at": self.last_triggered_at.isoformat() if self.last_triggered_at else None,
            "last_success_at": self.last_success_at.isoformat() if self.last_success_at else None,
            "created_at": self.created_at.isoformat(),
        }


class WebhookService:
    """
    Service for managing and triggering webhooks.

    Supports multiple providers with automatic payload formatting
    and signature verification.
    """

    # Maximum retries for failed deliveries
    MAX_RETRIES = 3

    # Maximum failures before marking webhook as failed
    MAX_FAILURES = 10

    # Timeout for webhook requests
    TIMEOUT_SECONDS = 30

    def __init__(self):
        """Initialize webhook service."""
        self._webhooks: Dict[str, Webhook] = {}
        self._deliveries: List[WebhookDelivery] = []
        self._lock = asyncio.Lock()

    def _generate_id(self) -> str:
        """Generate a unique webhook ID."""
        return f"wh_{secrets.token_hex(12)}"

    def _generate_secret(self) -> str:
        """Generate a webhook secret for signature verification."""
        return secrets.token_hex(32)

    def _compute_signature(self, payload: str, secret: str) -> str:
        """Compute HMAC-SHA256 signature for payload."""
        return hmac.new(
            secret.encode("utf-8"),
            payload.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    def _format_payload_for_provider(
        self,
        event: WebhookEvent,
        data: Dict[str, Any],
        provider: WebhookProvider,
    ) -> Dict[str, Any]:
        """Format payload for specific provider."""
        if provider == WebhookProvider.SLACK:
            return self._format_slack_payload(event, data)
        elif provider == WebhookProvider.DISCORD:
            return self._format_discord_payload(event, data)
        else:
            return self._format_custom_payload(event, data)

    def _format_custom_payload(
        self,
        event: WebhookEvent,
        data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Format payload for custom webhooks."""
        return {
            "event": event.value,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": data,
        }

    def _format_slack_payload(
        self,
        event: WebhookEvent,
        data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Format payload for Slack webhooks."""
        # Get appropriate emoji and color
        emoji = "ℹ️"
        color = "#36a64f"  # Green

        if "failed" in event.value or "alert" in event.value:
            emoji = "🚨"
            color = "#ff0000"  # Red
        elif "completed" in event.value:
            emoji = "✅"
            color = "#36a64f"  # Green
        elif "started" in event.value:
            emoji = "🚀"
            color = "#3aa3e3"  # Blue

        # Build message
        title = event.value.replace(".", " ").replace("_", " ").title()

        fields = []
        if "execution_id" in data:
            fields.append({
                "title": "Execution ID",
                "value": data["execution_id"],
                "short": True,
            })
        if "language" in data:
            fields.append({
                "title": "Language",
                "value": data["language"],
                "short": True,
            })
        if "status" in data:
            fields.append({
                "title": "Status",
                "value": data["status"],
                "short": True,
            })
        if "quality_score" in data:
            fields.append({
                "title": "Quality Score",
                "value": str(data["quality_score"]),
                "short": True,
            })

        return {
            "attachments": [
                {
                    "color": color,
                    "title": f"{emoji} {title}",
                    "fields": fields,
                    "footer": "Intelligent Coding Agent",
                    "ts": int(time.time()),
                }
            ]
        }

    def _format_discord_payload(
        self,
        event: WebhookEvent,
        data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Format payload for Discord webhooks."""
        # Get appropriate color
        color = 0x36a64f  # Green

        if "failed" in event.value or "alert" in event.value:
            color = 0xff0000  # Red
        elif "started" in event.value:
            color = 0x3aa3e3  # Blue

        title = event.value.replace(".", " ").replace("_", " ").title()

        fields = []
        if "execution_id" in data:
            fields.append({
                "name": "Execution ID",
                "value": data["execution_id"],
                "inline": True,
            })
        if "language" in data:
            fields.append({
                "name": "Language",
                "value": data["language"],
                "inline": True,
            })
        if "status" in data:
            fields.append({
                "name": "Status",
                "value": data["status"],
                "inline": True,
            })

        return {
            "embeds": [
                {
                    "title": title,
                    "color": color,
                    "fields": fields,
                    "footer": {"text": "Intelligent Coding Agent"},
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            ]
        }

    async def create_webhook(
        self,
        user_id: str,
        name: str,
        url: str,
        events: List[WebhookEvent],
        provider: WebhookProvider = WebhookProvider.CUSTOM,
        headers: Optional[Dict[str, str]] = None,
    ) -> Webhook:
        """
        Create a new webhook.

        Args:
            user_id: Owner of the webhook
            name: Display name
            url: Webhook URL
            events: Events to trigger webhook
            provider: Webhook provider type
            headers: Custom headers to include

        Returns:
            Created webhook
        """
        async with self._lock:
            webhook = Webhook(
                id=self._generate_id(),
                user_id=user_id,
                name=name,
                url=url,
                events=events,
                provider=provider,
                secret=self._generate_secret(),
                headers=headers or {},
            )

            self._webhooks[webhook.id] = webhook

            logger.info(
                "Webhook created",
                webhook_id=webhook.id,
                user_id=user_id,
                events=[e.value for e in events],
            )

            return webhook

    async def get_webhook(self, webhook_id: str) -> Optional[Webhook]:
        """Get webhook by ID."""
        return self._webhooks.get(webhook_id)

    async def list_webhooks(
        self,
        user_id: Optional[str] = None,
        status: Optional[WebhookStatus] = None,
    ) -> List[Webhook]:
        """List webhooks with optional filters."""
        webhooks = list(self._webhooks.values())

        if user_id:
            webhooks = [w for w in webhooks if w.user_id == user_id]

        if status:
            webhooks = [w for w in webhooks if w.status == status]

        return webhooks

    async def update_webhook(
        self,
        webhook_id: str,
        name: Optional[str] = None,
        url: Optional[str] = None,
        events: Optional[List[WebhookEvent]] = None,
        status: Optional[WebhookStatus] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Optional[Webhook]:
        """Update webhook configuration."""
        async with self._lock:
            webhook = self._webhooks.get(webhook_id)
            if not webhook:
                return None

            if name:
                webhook.name = name
            if url:
                webhook.url = url
            if events:
                webhook.events = events
            if status:
                webhook.status = status
            if headers is not None:
                webhook.headers = headers

            return webhook

    async def delete_webhook(self, webhook_id: str) -> bool:
        """Delete a webhook."""
        async with self._lock:
            if webhook_id in self._webhooks:
                self._webhooks[webhook_id].status = WebhookStatus.DELETED
                del self._webhooks[webhook_id]
                return True
            return False

    async def regenerate_secret(self, webhook_id: str) -> Optional[str]:
        """Regenerate webhook secret."""
        async with self._lock:
            webhook = self._webhooks.get(webhook_id)
            if not webhook:
                return None

            webhook.secret = self._generate_secret()
            return webhook.secret

    async def trigger(
        self,
        event: WebhookEvent,
        data: Dict[str, Any],
        user_id: Optional[str] = None,
    ) -> List[WebhookDelivery]:
        """
        Trigger webhooks for an event.

        Args:
            event: Event type
            data: Event data
            user_id: Optional user ID filter

        Returns:
            List of delivery records
        """
        # Find matching webhooks
        webhooks = []
        for webhook in self._webhooks.values():
            if webhook.status != WebhookStatus.ACTIVE:
                continue
            if event not in webhook.events:
                continue
            if user_id and webhook.user_id != user_id:
                continue
            webhooks.append(webhook)

        if not webhooks:
            return []

        # Deliver to all matching webhooks concurrently
        deliveries = await asyncio.gather(
            *[self._deliver(webhook, event, data) for webhook in webhooks],
            return_exceptions=True,
        )

        # Filter out exceptions and return deliveries
        return [d for d in deliveries if isinstance(d, WebhookDelivery)]

    async def _deliver(
        self,
        webhook: Webhook,
        event: WebhookEvent,
        data: Dict[str, Any],
        attempt: int = 1,
    ) -> WebhookDelivery:
        """Deliver webhook payload."""
        delivery_id = f"del_{secrets.token_hex(8)}"
        start_time = time.perf_counter()

        # Format payload for provider
        payload = self._format_payload_for_provider(event, data, webhook.provider)

        # Build headers
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "IntelligentCodingAgent/1.0",
            "X-Webhook-Event": event.value,
            "X-Webhook-Delivery": delivery_id,
            **webhook.headers,
        }

        # Add signature if secret is set
        if webhook.secret:
            import json
            payload_str = json.dumps(payload, separators=(",", ":"))
            signature = self._compute_signature(payload_str, webhook.secret)
            headers["X-Webhook-Signature"] = f"sha256={signature}"

        delivery = WebhookDelivery(
            id=delivery_id,
            webhook_id=webhook.id,
            event=event,
            payload=payload,
            attempt=attempt,
        )

        try:
            async with httpx.AsyncClient(timeout=self.TIMEOUT_SECONDS) as client:
                response = await client.post(
                    webhook.url,
                    json=payload,
                    headers=headers,
                )

                delivery.status_code = response.status_code
                delivery.response_body = response.text[:1000]  # Truncate
                delivery.success = 200 <= response.status_code < 300

        except httpx.TimeoutException:
            delivery.error = "Request timeout"
        except httpx.RequestError as e:
            delivery.error = str(e)
        except Exception as e:
            delivery.error = f"Unexpected error: {str(e)}"

        delivery.duration_ms = int((time.perf_counter() - start_time) * 1000)

        # Update webhook stats
        async with self._lock:
            webhook.last_triggered_at = datetime.now(timezone.utc)

            if delivery.success:
                webhook.failure_count = 0
                webhook.last_success_at = datetime.now(timezone.utc)
            else:
                webhook.failure_count += 1

                # Mark as failed if too many failures
                if webhook.failure_count >= self.MAX_FAILURES:
                    webhook.status = WebhookStatus.FAILED
                    logger.warning(
                        "Webhook marked as failed",
                        webhook_id=webhook.id,
                        failure_count=webhook.failure_count,
                    )

            # Store delivery
            self._deliveries.append(delivery)

            # Cleanup old deliveries (keep last 1000)
            if len(self._deliveries) > 1000:
                self._deliveries = self._deliveries[-1000:]

        logger.info(
            "Webhook delivered",
            webhook_id=webhook.id,
            event=event.value,
            success=delivery.success,
            status_code=delivery.status_code,
            duration_ms=delivery.duration_ms,
        )

        # Retry on failure
        if not delivery.success and attempt < self.MAX_RETRIES:
            await asyncio.sleep(2 ** attempt)  # Exponential backoff
            return await self._deliver(webhook, event, data, attempt + 1)

        return delivery

    async def get_deliveries(
        self,
        webhook_id: Optional[str] = None,
        limit: int = 50,
    ) -> List[WebhookDelivery]:
        """Get recent webhook deliveries."""
        deliveries = self._deliveries

        if webhook_id:
            deliveries = [d for d in deliveries if d.webhook_id == webhook_id]

        return list(reversed(deliveries[-limit:]))

    async def test_webhook(self, webhook_id: str) -> Optional[WebhookDelivery]:
        """Send a test event to a webhook."""
        webhook = self._webhooks.get(webhook_id)
        if not webhook:
            return None

        test_data = {
            "message": "This is a test webhook delivery",
            "webhook_id": webhook_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        # Use execution.completed as test event
        return await self._deliver(
            webhook,
            WebhookEvent.EXECUTION_COMPLETED,
            test_data,
        )

    def get_stats(self) -> Dict[str, Any]:
        """Get webhook service statistics."""
        total = len(self._webhooks)
        active = sum(1 for w in self._webhooks.values() if w.status == WebhookStatus.ACTIVE)
        failed = sum(1 for w in self._webhooks.values() if w.status == WebhookStatus.FAILED)

        recent_deliveries = self._deliveries[-100:]
        success_rate = (
            sum(1 for d in recent_deliveries if d.success) / len(recent_deliveries) * 100
            if recent_deliveries else 0
        )

        return {
            "total_webhooks": total,
            "active_webhooks": active,
            "failed_webhooks": failed,
            "total_deliveries": len(self._deliveries),
            "recent_success_rate": round(success_rate, 1),
        }


# Singleton instance
_webhook_service: Optional[WebhookService] = None


def get_webhook_service() -> WebhookService:
    """Get the global webhook service instance."""
    global _webhook_service
    if _webhook_service is None:
        _webhook_service = WebhookService()
    return _webhook_service
