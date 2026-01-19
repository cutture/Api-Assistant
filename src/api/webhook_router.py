"""
Webhook API router.

Provides endpoints for managing webhooks for CI/CD integration
and notifications.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, HttpUrl
import structlog

from src.api.auth import get_current_user_optional, CurrentUser
from src.services.webhook_service import (
    WebhookService,
    Webhook,
    WebhookEvent,
    WebhookProvider,
    WebhookStatus,
    WebhookDelivery,
    get_webhook_service,
)

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


# Request/Response models
class CreateWebhookRequest(BaseModel):
    """Request to create a webhook."""

    name: str
    url: HttpUrl
    events: List[str]  # Event names
    provider: str = "custom"
    headers: Optional[dict] = None


class UpdateWebhookRequest(BaseModel):
    """Request to update a webhook."""

    name: Optional[str] = None
    url: Optional[HttpUrl] = None
    events: Optional[List[str]] = None
    status: Optional[str] = None
    headers: Optional[dict] = None


class WebhookResponse(BaseModel):
    """Webhook response model."""

    id: str
    user_id: str
    name: str
    url: str
    events: List[str]
    provider: str
    status: str
    secret: Optional[str] = None
    failure_count: int
    last_triggered_at: Optional[str] = None
    last_success_at: Optional[str] = None
    created_at: str


class WebhookListResponse(BaseModel):
    """List of webhooks response."""

    webhooks: List[WebhookResponse]
    total: int


class DeliveryResponse(BaseModel):
    """Webhook delivery response."""

    id: str
    webhook_id: str
    event: str
    status_code: Optional[int]
    success: bool
    error: Optional[str]
    duration_ms: int
    attempt: int
    created_at: str


class DeliveryListResponse(BaseModel):
    """List of deliveries response."""

    deliveries: List[DeliveryResponse]
    total: int


class WebhookStatsResponse(BaseModel):
    """Webhook statistics response."""

    total_webhooks: int
    active_webhooks: int
    failed_webhooks: int
    total_deliveries: int
    recent_success_rate: float


def _webhook_to_response(webhook: Webhook, include_secret: bool = False) -> WebhookResponse:
    """Convert Webhook to response model."""
    return WebhookResponse(
        id=webhook.id,
        user_id=webhook.user_id,
        name=webhook.name,
        url=webhook.url,
        events=[e.value for e in webhook.events],
        provider=webhook.provider.value,
        status=webhook.status.value,
        secret=webhook.secret if include_secret else None,
        failure_count=webhook.failure_count,
        last_triggered_at=webhook.last_triggered_at.isoformat() if webhook.last_triggered_at else None,
        last_success_at=webhook.last_success_at.isoformat() if webhook.last_success_at else None,
        created_at=webhook.created_at.isoformat(),
    )


def _delivery_to_response(delivery: WebhookDelivery) -> DeliveryResponse:
    """Convert WebhookDelivery to response model."""
    return DeliveryResponse(
        id=delivery.id,
        webhook_id=delivery.webhook_id,
        event=delivery.event.value,
        status_code=delivery.status_code,
        success=delivery.success,
        error=delivery.error,
        duration_ms=delivery.duration_ms,
        attempt=delivery.attempt,
        created_at=delivery.created_at.isoformat(),
    )


def _parse_events(event_names: List[str]) -> List[WebhookEvent]:
    """Parse event names to WebhookEvent enum."""
    events = []
    for name in event_names:
        try:
            events.append(WebhookEvent(name))
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid event type: {name}",
            )
    return events


def _parse_provider(provider_name: str) -> WebhookProvider:
    """Parse provider name to WebhookProvider enum."""
    try:
        return WebhookProvider(provider_name)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid provider: {provider_name}",
        )


def _parse_status(status_name: str) -> WebhookStatus:
    """Parse status name to WebhookStatus enum."""
    try:
        return WebhookStatus(status_name)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status: {status_name}",
        )


@router.post("", response_model=WebhookResponse, status_code=status.HTTP_201_CREATED)
async def create_webhook(
    request: CreateWebhookRequest,
    current_user: CurrentUser = Depends(get_current_user_optional),
    service: WebhookService = Depends(get_webhook_service),
):
    """
    Create a new webhook.

    Webhooks are triggered when specific events occur (e.g., execution completed).
    Supports custom webhooks, Slack, and Discord.
    """
    if not current_user.is_authenticated:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to create webhooks",
        )

    events = _parse_events(request.events)
    provider = _parse_provider(request.provider)

    webhook = await service.create_webhook(
        user_id=current_user.user_id,
        name=request.name,
        url=str(request.url),
        events=events,
        provider=provider,
        headers=request.headers,
    )

    # Include secret in creation response
    return _webhook_to_response(webhook, include_secret=True)


@router.get("", response_model=WebhookListResponse)
async def list_webhooks(
    status_filter: Optional[str] = None,
    current_user: CurrentUser = Depends(get_current_user_optional),
    service: WebhookService = Depends(get_webhook_service),
):
    """List user's webhooks."""
    if not current_user.is_authenticated:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )

    webhook_status = _parse_status(status_filter) if status_filter else None

    webhooks = await service.list_webhooks(
        user_id=current_user.user_id,
        status=webhook_status,
    )

    return WebhookListResponse(
        webhooks=[_webhook_to_response(w) for w in webhooks],
        total=len(webhooks),
    )


@router.get("/events", response_model=List[dict])
async def list_events():
    """List available webhook events."""
    return [
        {"name": e.value, "description": _get_event_description(e)}
        for e in WebhookEvent
    ]


@router.get("/providers", response_model=List[dict])
async def list_providers():
    """List supported webhook providers."""
    return [
        {"name": p.value, "description": _get_provider_description(p)}
        for p in WebhookProvider
    ]


@router.get("/stats", response_model=WebhookStatsResponse)
async def get_stats(
    service: WebhookService = Depends(get_webhook_service),
):
    """Get webhook service statistics."""
    stats = service.get_stats()
    return WebhookStatsResponse(**stats)


@router.get("/{webhook_id}", response_model=WebhookResponse)
async def get_webhook(
    webhook_id: str,
    current_user: CurrentUser = Depends(get_current_user_optional),
    service: WebhookService = Depends(get_webhook_service),
):
    """Get webhook details."""
    webhook = await service.get_webhook(webhook_id)

    if not webhook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Webhook not found",
        )

    # Check ownership
    if current_user.is_authenticated and webhook.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    return _webhook_to_response(webhook)


@router.patch("/{webhook_id}", response_model=WebhookResponse)
async def update_webhook(
    webhook_id: str,
    request: UpdateWebhookRequest,
    current_user: CurrentUser = Depends(get_current_user_optional),
    service: WebhookService = Depends(get_webhook_service),
):
    """Update webhook configuration."""
    webhook = await service.get_webhook(webhook_id)

    if not webhook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Webhook not found",
        )

    if webhook.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    events = _parse_events(request.events) if request.events else None
    webhook_status = _parse_status(request.status) if request.status else None

    updated = await service.update_webhook(
        webhook_id=webhook_id,
        name=request.name,
        url=str(request.url) if request.url else None,
        events=events,
        status=webhook_status,
        headers=request.headers,
    )

    return _webhook_to_response(updated)


@router.delete("/{webhook_id}")
async def delete_webhook(
    webhook_id: str,
    current_user: CurrentUser = Depends(get_current_user_optional),
    service: WebhookService = Depends(get_webhook_service),
):
    """Delete a webhook."""
    webhook = await service.get_webhook(webhook_id)

    if not webhook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Webhook not found",
        )

    if webhook.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    await service.delete_webhook(webhook_id)

    return {"success": True, "message": "Webhook deleted"}


@router.post("/{webhook_id}/regenerate-secret")
async def regenerate_secret(
    webhook_id: str,
    current_user: CurrentUser = Depends(get_current_user_optional),
    service: WebhookService = Depends(get_webhook_service),
):
    """Regenerate webhook secret for signature verification."""
    webhook = await service.get_webhook(webhook_id)

    if not webhook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Webhook not found",
        )

    if webhook.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    new_secret = await service.regenerate_secret(webhook_id)

    return {"secret": new_secret}


@router.post("/{webhook_id}/test", response_model=DeliveryResponse)
async def test_webhook(
    webhook_id: str,
    current_user: CurrentUser = Depends(get_current_user_optional),
    service: WebhookService = Depends(get_webhook_service),
):
    """Send a test event to the webhook."""
    webhook = await service.get_webhook(webhook_id)

    if not webhook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Webhook not found",
        )

    if webhook.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    delivery = await service.test_webhook(webhook_id)

    if not delivery:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send test webhook",
        )

    return _delivery_to_response(delivery)


@router.get("/{webhook_id}/deliveries", response_model=DeliveryListResponse)
async def list_deliveries(
    webhook_id: str,
    limit: int = 50,
    current_user: CurrentUser = Depends(get_current_user_optional),
    service: WebhookService = Depends(get_webhook_service),
):
    """Get recent delivery history for a webhook."""
    webhook = await service.get_webhook(webhook_id)

    if not webhook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Webhook not found",
        )

    if webhook.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    deliveries = await service.get_deliveries(webhook_id=webhook_id, limit=limit)

    return DeliveryListResponse(
        deliveries=[_delivery_to_response(d) for d in deliveries],
        total=len(deliveries),
    )


def _get_event_description(event: WebhookEvent) -> str:
    """Get human-readable description for an event."""
    descriptions = {
        WebhookEvent.EXECUTION_STARTED: "Triggered when code execution starts",
        WebhookEvent.EXECUTION_COMPLETED: "Triggered when code execution completes successfully",
        WebhookEvent.EXECUTION_FAILED: "Triggered when code execution fails",
        WebhookEvent.EXECUTION_RETRY: "Triggered when code execution is retried",
        WebhookEvent.ARTIFACT_CREATED: "Triggered when a new artifact is created",
        WebhookEvent.PREVIEW_STARTED: "Triggered when a preview server starts",
        WebhookEvent.PREVIEW_STOPPED: "Triggered when a preview server stops",
        WebhookEvent.SECURITY_ALERT: "Triggered when a security vulnerability is detected",
        WebhookEvent.COST_ALERT: "Triggered when cost thresholds are exceeded",
    }
    return descriptions.get(event, "No description available")


def _get_provider_description(provider: WebhookProvider) -> str:
    """Get human-readable description for a provider."""
    descriptions = {
        WebhookProvider.CUSTOM: "Custom HTTP webhook endpoint",
        WebhookProvider.SLACK: "Slack incoming webhook",
        WebhookProvider.DISCORD: "Discord webhook",
        WebhookProvider.GITHUB: "GitHub webhook",
        WebhookProvider.GITLAB: "GitLab webhook",
    }
    return descriptions.get(provider, "No description available")
