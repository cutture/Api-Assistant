"""
Collaboration API Router for team workspaces and session sharing.

Provides endpoints for:
- Team management (CRUD, members)
- Session sharing and permissions
- Real-time collaboration status
"""

import structlog
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

from src.api.auth import get_current_user, CurrentUser
from src.services.collaboration_service import (
    CollaborationService,
    Permission,
    CollaborationEvent,
    get_collaboration_service,
)

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/collaboration", tags=["collaboration"])


# ============ Request/Response Models ============

class CreateTeamRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(default="", max_length=500)


class TeamResponse(BaseModel):
    id: str
    name: str
    description: str
    owner_id: str
    members: List[dict]
    created_at: str
    updated_at: str
    settings: dict


class AddMemberRequest(BaseModel):
    user_id: str
    email: str
    display_name: str
    role: str = Field(default="viewer")  # viewer, editor


class UpdateRoleRequest(BaseModel):
    role: str  # viewer, editor


class ShareSessionRequest(BaseModel):
    session_id: str
    name: str = Field(..., min_length=1, max_length=100)
    team_id: Optional[str] = None
    is_public: bool = False
    expires_hours: Optional[int] = Field(default=None, ge=1, le=720)  # Max 30 days


class SharedSessionResponse(BaseModel):
    id: str
    session_id: str
    team_id: Optional[str]
    owner_id: str
    name: str
    permissions: dict
    active_users: List[str]
    created_at: str
    expires_at: Optional[str]
    share_link: Optional[str]
    is_public: bool


class GrantAccessRequest(BaseModel):
    user_id: str
    permission: str = Field(default="viewer")  # viewer, editor


class CollaborationStatsResponse(BaseModel):
    total_teams: int
    total_shared_sessions: int
    total_active_collaborations: int
    active_sessions: int


# ============ Team Endpoints ============

@router.post("/teams", response_model=TeamResponse, status_code=status.HTTP_201_CREATED)
async def create_team(
    request: CreateTeamRequest,
    current_user: CurrentUser = Depends(get_current_user),
    service: CollaborationService = Depends(get_collaboration_service),
):
    """Create a new team."""
    team = await service.create_team(
        name=request.name,
        description=request.description,
        owner_id=current_user.user_id,
        owner_email=current_user.email or "",
        owner_name=current_user.email or current_user.user_id,
    )
    return TeamResponse(**team.to_dict())


@router.get("/teams", response_model=List[TeamResponse])
async def list_teams(
    current_user: CurrentUser = Depends(get_current_user),
    service: CollaborationService = Depends(get_collaboration_service),
):
    """List all teams the user belongs to."""
    teams = await service.list_user_teams(current_user.user_id)
    return [TeamResponse(**t.to_dict()) for t in teams]


@router.get("/teams/{team_id}", response_model=TeamResponse)
async def get_team(
    team_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    service: CollaborationService = Depends(get_collaboration_service),
):
    """Get team details."""
    team = await service.get_team(team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    # Check user is a member
    if current_user.user_id not in team.members:
        raise HTTPException(status_code=403, detail="Not a team member")

    return TeamResponse(**team.to_dict())


@router.post("/teams/{team_id}/members")
async def add_team_member(
    team_id: str,
    request: AddMemberRequest,
    current_user: CurrentUser = Depends(get_current_user),
    service: CollaborationService = Depends(get_collaboration_service),
):
    """Add a member to a team."""
    try:
        role = Permission(request.role)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid role")

    member = await service.add_team_member(
        team_id=team_id,
        user_id=request.user_id,
        email=request.email,
        display_name=request.display_name,
        role=role,
        requester_id=current_user.user_id,
    )

    if not member:
        raise HTTPException(status_code=403, detail="Cannot add member")

    return {
        "user_id": member.user_id,
        "role": member.role.value,
        "message": "Member added successfully",
    }


@router.delete("/teams/{team_id}/members/{user_id}")
async def remove_team_member(
    team_id: str,
    user_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    service: CollaborationService = Depends(get_collaboration_service),
):
    """Remove a member from a team."""
    success = await service.remove_team_member(
        team_id=team_id,
        user_id=user_id,
        requester_id=current_user.user_id,
    )

    if not success:
        raise HTTPException(status_code=403, detail="Cannot remove member")

    return {"message": "Member removed successfully"}


@router.patch("/teams/{team_id}/members/{user_id}")
async def update_member_role(
    team_id: str,
    user_id: str,
    request: UpdateRoleRequest,
    current_user: CurrentUser = Depends(get_current_user),
    service: CollaborationService = Depends(get_collaboration_service),
):
    """Update a member's role."""
    try:
        role = Permission(request.role)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid role")

    success = await service.update_member_role(
        team_id=team_id,
        user_id=user_id,
        new_role=role,
        requester_id=current_user.user_id,
    )

    if not success:
        raise HTTPException(status_code=403, detail="Cannot update role")

    return {"message": "Role updated successfully"}


@router.delete("/teams/{team_id}")
async def delete_team(
    team_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    service: CollaborationService = Depends(get_collaboration_service),
):
    """Delete a team."""
    success = await service.delete_team(
        team_id=team_id,
        requester_id=current_user.user_id,
    )

    if not success:
        raise HTTPException(status_code=403, detail="Cannot delete team")

    return {"message": "Team deleted successfully"}


# ============ Session Sharing Endpoints ============

@router.post("/sessions/share", response_model=SharedSessionResponse)
async def share_session(
    request: ShareSessionRequest,
    current_user: CurrentUser = Depends(get_current_user),
    service: CollaborationService = Depends(get_collaboration_service),
):
    """Share a session for collaboration."""
    shared = await service.share_session(
        session_id=request.session_id,
        owner_id=current_user.user_id,
        name=request.name,
        team_id=request.team_id,
        is_public=request.is_public,
        expires_hours=request.expires_hours,
    )
    return SharedSessionResponse(**shared.to_dict())


@router.get("/sessions/shared", response_model=List[SharedSessionResponse])
async def list_shared_sessions(
    current_user: CurrentUser = Depends(get_current_user),
    service: CollaborationService = Depends(get_collaboration_service),
):
    """List all shared sessions the user has access to."""
    sessions = await service.list_user_shared_sessions(current_user.user_id)
    return [SharedSessionResponse(**s.to_dict()) for s in sessions]


@router.get("/sessions/shared/{share_id}", response_model=SharedSessionResponse)
async def get_shared_session(
    share_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    service: CollaborationService = Depends(get_collaboration_service),
):
    """Get shared session details."""
    shared = await service.get_shared_session(share_id)
    if not shared:
        raise HTTPException(status_code=404, detail="Shared session not found")

    if current_user.user_id not in shared.permissions and not shared.is_public:
        raise HTTPException(status_code=403, detail="No access to this session")

    return SharedSessionResponse(**shared.to_dict())


@router.get("/sessions/link/{share_link}", response_model=SharedSessionResponse)
async def get_session_by_link(
    share_link: str,
    service: CollaborationService = Depends(get_collaboration_service),
):
    """Get a shared session by public link."""
    shared = await service.get_shared_session_by_link(share_link)
    if not shared:
        raise HTTPException(status_code=404, detail="Invalid or expired link")

    return SharedSessionResponse(**shared.to_dict())


@router.post("/sessions/shared/{share_id}/access")
async def grant_session_access(
    share_id: str,
    request: GrantAccessRequest,
    current_user: CurrentUser = Depends(get_current_user),
    service: CollaborationService = Depends(get_collaboration_service),
):
    """Grant a user access to a shared session."""
    try:
        permission = Permission(request.permission)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid permission")

    success = await service.grant_session_access(
        share_id=share_id,
        user_id=request.user_id,
        permission=permission,
        requester_id=current_user.user_id,
    )

    if not success:
        raise HTTPException(status_code=403, detail="Cannot grant access")

    return {"message": "Access granted successfully"}


@router.delete("/sessions/shared/{share_id}/access/{user_id}")
async def revoke_session_access(
    share_id: str,
    user_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    service: CollaborationService = Depends(get_collaboration_service),
):
    """Revoke a user's access to a shared session."""
    success = await service.revoke_session_access(
        share_id=share_id,
        user_id=user_id,
        requester_id=current_user.user_id,
    )

    if not success:
        raise HTTPException(status_code=403, detail="Cannot revoke access")

    return {"message": "Access revoked successfully"}


@router.delete("/sessions/shared/{share_id}")
async def unshare_session(
    share_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    service: CollaborationService = Depends(get_collaboration_service),
):
    """Stop sharing a session."""
    success = await service.unshare_session(
        share_id=share_id,
        requester_id=current_user.user_id,
    )

    if not success:
        raise HTTPException(status_code=403, detail="Cannot unshare session")

    return {"message": "Session unshared successfully"}


@router.post("/sessions/shared/{share_id}/join")
async def join_shared_session(
    share_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    service: CollaborationService = Depends(get_collaboration_service),
):
    """Join a shared session."""
    permission = await service.join_session(
        share_id=share_id,
        user_id=current_user.user_id,
    )

    if not permission:
        raise HTTPException(status_code=403, detail="Cannot join session")

    return {
        "message": "Joined session successfully",
        "permission": permission.value,
    }


@router.post("/sessions/shared/{share_id}/leave")
async def leave_shared_session(
    share_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    service: CollaborationService = Depends(get_collaboration_service),
):
    """Leave a shared session."""
    success = await service.leave_session(
        share_id=share_id,
        user_id=current_user.user_id,
    )

    if not success:
        raise HTTPException(status_code=404, detail="Session not found")

    return {"message": "Left session successfully"}


@router.get("/sessions/shared/{share_id}/users")
async def get_active_users(
    share_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    service: CollaborationService = Depends(get_collaboration_service),
):
    """Get list of active users in a shared session."""
    shared = await service.get_shared_session(share_id)
    if not shared:
        raise HTTPException(status_code=404, detail="Session not found")

    if current_user.user_id not in shared.permissions and not shared.is_public:
        raise HTTPException(status_code=403, detail="No access to this session")

    users = await service.get_active_users(share_id)
    return {"active_users": users}


# ============ Statistics ============

@router.get("/stats", response_model=CollaborationStatsResponse)
async def get_collaboration_stats(
    current_user: CurrentUser = Depends(get_current_user),
    service: CollaborationService = Depends(get_collaboration_service),
):
    """Get collaboration statistics."""
    stats = await service.get_stats()
    return CollaborationStatsResponse(**stats)


# ============ WebSocket for Real-time Updates ============

@router.websocket("/ws/{share_id}")
async def websocket_collaboration(
    websocket: WebSocket,
    share_id: str,
    service: CollaborationService = Depends(get_collaboration_service),
):
    """WebSocket endpoint for real-time collaboration."""
    await websocket.accept()

    # Get user from query params or headers
    user_id = websocket.query_params.get("user_id", "anonymous")

    # Join the session
    permission = await service.join_session(share_id, user_id)
    if not permission:
        await websocket.close(code=4003, reason="Access denied")
        return

    # Subscribe to events
    async def on_event(message):
        try:
            await websocket.send_json(message.to_dict())
        except Exception:
            pass

    unsubscribe = service.subscribe(share_id, on_event)

    try:
        while True:
            data = await websocket.receive_json()
            event_type = data.get("event")
            event_data = data.get("data", {})

            try:
                event = CollaborationEvent(event_type)
                await service.broadcast_event(
                    share_id=share_id,
                    event=event,
                    data=event_data,
                    sender_id=user_id,
                )
            except ValueError:
                await websocket.send_json({"error": f"Unknown event: {event_type}"})

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected", share_id=share_id, user_id=user_id)
    finally:
        unsubscribe()
        await service.leave_session(share_id, user_id)
