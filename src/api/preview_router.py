"""
Preview API Router for Intelligent Coding Agent.

Provides endpoints for:
- Starting live preview servers
- Managing preview sessions
- Stopping previews
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from src.api.auth import get_current_user_optional
from src.database.models import User
from src.services.preview_service import (
    PreviewService,
    PreviewSession,
    get_preview_service,
)


router = APIRouter(prefix="/preview", tags=["preview"])


# =============================================================================
# Request/Response Models
# =============================================================================


class StartPreviewRequest(BaseModel):
    """Request model for starting a preview."""
    execution_id: str
    code: str
    language: str
    framework: Optional[str] = None
    dependencies: Optional[list[str]] = None
    expiry_minutes: int = 30


class PreviewResponse(BaseModel):
    """Response model for preview session."""
    id: str
    execution_id: str
    url: str
    port: int
    status: str
    created_at: str
    expires_at: str
    time_remaining_seconds: int
    error_message: Optional[str] = None


class PreviewStatsResponse(BaseModel):
    """Response model for preview stats."""
    total_sessions: int
    running: int
    stopped: int
    error: int
    used_ports: int
    available_ports: int


# =============================================================================
# Helper Functions
# =============================================================================


def session_to_response(session: PreviewSession) -> PreviewResponse:
    """Convert PreviewSession to response model."""
    return PreviewResponse(
        id=session.id,
        execution_id=session.execution_id,
        url=session.url,
        port=session.port,
        status=session.status,
        created_at=session.created_at.isoformat(),
        expires_at=session.expires_at.isoformat(),
        time_remaining_seconds=session.time_remaining(),
        error_message=session.error_message,
    )


# =============================================================================
# Endpoints
# =============================================================================


@router.post("", response_model=PreviewResponse)
async def start_preview(
    request: StartPreviewRequest,
    current_user: Optional[User] = Depends(get_current_user_optional),
    preview_service: PreviewService = Depends(get_preview_service),
):
    """
    Start a live preview server for generated code.

    - **execution_id**: ID of the code execution
    - **code**: The code to run
    - **language**: Programming language (python, javascript)
    - **framework**: Optional framework (flask, fastapi, express)
    - **dependencies**: Optional list of dependencies
    - **expiry_minutes**: Minutes until preview expires (default 30)
    """
    user_id = current_user.id if current_user else "anonymous"

    try:
        session = await preview_service.start_preview(
            execution_id=request.execution_id,
            user_id=user_id,
            code=request.code,
            language=request.language,
            framework=request.framework,
            dependencies=request.dependencies,
            expiry_minutes=request.expiry_minutes,
        )

        return session_to_response(session)

    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start preview: {str(e)}",
        )


@router.get("/{preview_id}", response_model=PreviewResponse)
async def get_preview(
    preview_id: str,
    current_user: Optional[User] = Depends(get_current_user_optional),
    preview_service: PreviewService = Depends(get_preview_service),
):
    """
    Get preview session status.

    Returns preview URL, status, and time remaining.
    """
    session = preview_service.get_preview(preview_id)

    if not session:
        raise HTTPException(status_code=404, detail="Preview not found")

    # Check access
    user_id = current_user.id if current_user else "anonymous"
    if session.user_id != user_id and user_id != "anonymous":
        raise HTTPException(status_code=403, detail="Access denied")

    return session_to_response(session)


@router.delete("/{preview_id}")
async def stop_preview(
    preview_id: str,
    current_user: Optional[User] = Depends(get_current_user_optional),
    preview_service: PreviewService = Depends(get_preview_service),
):
    """
    Stop a preview session.

    Terminates the preview server and cleans up resources.
    """
    session = preview_service.get_preview(preview_id)

    if not session:
        raise HTTPException(status_code=404, detail="Preview not found")

    # Check access
    user_id = current_user.id if current_user else "anonymous"
    if session.user_id != user_id and user_id != "anonymous":
        raise HTTPException(status_code=403, detail="Access denied")

    success = await preview_service.stop_preview(preview_id)

    if not success:
        raise HTTPException(status_code=500, detail="Failed to stop preview")

    return {"success": True, "message": "Preview stopped"}


@router.get("", response_model=list[PreviewResponse])
async def list_user_previews(
    current_user: Optional[User] = Depends(get_current_user_optional),
    preview_service: PreviewService = Depends(get_preview_service),
):
    """
    List all preview sessions for the current user.
    """
    user_id = current_user.id if current_user else "anonymous"
    sessions = preview_service.get_user_previews(user_id)

    return [session_to_response(s) for s in sessions]


@router.get("/stats", response_model=PreviewStatsResponse)
async def get_preview_stats(
    preview_service: PreviewService = Depends(get_preview_service),
):
    """
    Get preview service statistics.

    Returns counts of active sessions and available resources.
    """
    stats = preview_service.get_stats()
    return PreviewStatsResponse(**stats)


@router.post("/cleanup")
async def cleanup_expired_previews(
    preview_service: PreviewService = Depends(get_preview_service),
):
    """
    Clean up expired preview sessions.

    This is typically called by a scheduled job.
    """
    count = await preview_service.cleanup_expired()

    return {
        "success": True,
        "cleaned_up": count,
        "message": f"Cleaned up {count} expired preview(s)",
    }
