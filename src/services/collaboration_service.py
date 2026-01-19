"""
Collaboration Service for real-time session sharing and team workspaces.

This module provides:
- Team/workspace management
- Session sharing with permissions
- Real-time collaboration tracking
- Permission-based access control
"""

import asyncio
import secrets
import structlog
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional, Set, Callable, Any

logger = structlog.get_logger(__name__)


class Permission(str, Enum):
    """Permission levels for collaboration."""
    OWNER = "owner"      # Full control, can delete
    EDITOR = "editor"    # Can edit code, run executions
    VIEWER = "viewer"    # Read-only access


class CollaborationEvent(str, Enum):
    """Events for real-time collaboration."""
    USER_JOINED = "user.joined"
    USER_LEFT = "user.left"
    CODE_UPDATED = "code.updated"
    EXECUTION_STARTED = "execution.started"
    EXECUTION_COMPLETED = "execution.completed"
    CHAT_MESSAGE = "chat.message"
    CURSOR_MOVED = "cursor.moved"
    SELECTION_CHANGED = "selection.changed"
    SESSION_SETTINGS_CHANGED = "session.settings_changed"


@dataclass
class TeamMember:
    """A member of a team."""
    user_id: str
    email: str
    display_name: str
    role: Permission
    joined_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_active: Optional[datetime] = None


@dataclass
class Team:
    """A team/workspace for collaboration."""
    id: str
    name: str
    description: str
    owner_id: str
    members: Dict[str, TeamMember] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    settings: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "owner_id": self.owner_id,
            "members": [
                {
                    "user_id": m.user_id,
                    "email": m.email,
                    "display_name": m.display_name,
                    "role": m.role.value,
                    "joined_at": m.joined_at.isoformat(),
                    "last_active": m.last_active.isoformat() if m.last_active else None,
                }
                for m in self.members.values()
            ],
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "settings": self.settings,
        }


@dataclass
class SharedSession:
    """A shared coding session."""
    id: str
    session_id: str  # Original session ID
    team_id: Optional[str]  # If shared with a team
    owner_id: str
    name: str
    permissions: Dict[str, Permission] = field(default_factory=dict)  # user_id -> permission
    active_users: Set[str] = field(default_factory=set)  # Currently connected users
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = None
    share_link: Optional[str] = None
    is_public: bool = False

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "session_id": self.session_id,
            "team_id": self.team_id,
            "owner_id": self.owner_id,
            "name": self.name,
            "permissions": {uid: p.value for uid, p in self.permissions.items()},
            "active_users": list(self.active_users),
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "share_link": self.share_link,
            "is_public": self.is_public,
        }


@dataclass
class CollaborationMessage:
    """A message in a collaboration session."""
    id: str
    shared_session_id: str
    user_id: str
    event: CollaborationEvent
    data: Dict[str, Any]
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "shared_session_id": self.shared_session_id,
            "user_id": self.user_id,
            "event": self.event.value,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
        }


class CollaborationService:
    """Service for managing real-time collaboration."""

    def __init__(self):
        self.teams: Dict[str, Team] = {}
        self.shared_sessions: Dict[str, SharedSession] = {}
        self.user_teams: Dict[str, Set[str]] = {}  # user_id -> team_ids
        self.session_subscribers: Dict[str, Set[Callable]] = {}  # session_id -> callbacks
        self._lock = asyncio.Lock()
        logger.info("CollaborationService initialized")

    # ============ Team Management ============

    async def create_team(
        self,
        name: str,
        description: str,
        owner_id: str,
        owner_email: str,
        owner_name: str,
    ) -> Team:
        """Create a new team."""
        async with self._lock:
            team_id = f"team_{secrets.token_urlsafe(12)}"

            owner_member = TeamMember(
                user_id=owner_id,
                email=owner_email,
                display_name=owner_name,
                role=Permission.OWNER,
            )

            team = Team(
                id=team_id,
                name=name,
                description=description,
                owner_id=owner_id,
                members={owner_id: owner_member},
            )

            self.teams[team_id] = team

            if owner_id not in self.user_teams:
                self.user_teams[owner_id] = set()
            self.user_teams[owner_id].add(team_id)

            logger.info("Team created", team_id=team_id, owner_id=owner_id)
            return team

    async def get_team(self, team_id: str) -> Optional[Team]:
        """Get a team by ID."""
        return self.teams.get(team_id)

    async def list_user_teams(self, user_id: str) -> List[Team]:
        """List all teams a user belongs to."""
        team_ids = self.user_teams.get(user_id, set())
        return [self.teams[tid] for tid in team_ids if tid in self.teams]

    async def add_team_member(
        self,
        team_id: str,
        user_id: str,
        email: str,
        display_name: str,
        role: Permission,
        requester_id: str,
    ) -> Optional[TeamMember]:
        """Add a member to a team."""
        async with self._lock:
            team = self.teams.get(team_id)
            if not team:
                return None

            # Check requester permissions
            requester = team.members.get(requester_id)
            if not requester or requester.role not in [Permission.OWNER, Permission.EDITOR]:
                logger.warning("Unauthorized team member add attempt",
                             team_id=team_id, requester_id=requester_id)
                return None

            # Only owner can add editors/owners
            if role in [Permission.OWNER, Permission.EDITOR] and requester.role != Permission.OWNER:
                logger.warning("Non-owner tried to add editor/owner")
                return None

            member = TeamMember(
                user_id=user_id,
                email=email,
                display_name=display_name,
                role=role,
            )

            team.members[user_id] = member
            team.updated_at = datetime.now(timezone.utc)

            if user_id not in self.user_teams:
                self.user_teams[user_id] = set()
            self.user_teams[user_id].add(team_id)

            logger.info("Team member added", team_id=team_id, user_id=user_id, role=role)
            return member

    async def remove_team_member(
        self,
        team_id: str,
        user_id: str,
        requester_id: str,
    ) -> bool:
        """Remove a member from a team."""
        async with self._lock:
            team = self.teams.get(team_id)
            if not team:
                return False

            # Can't remove owner
            if user_id == team.owner_id:
                return False

            # Check requester permissions
            requester = team.members.get(requester_id)
            if not requester or requester.role != Permission.OWNER:
                # Users can remove themselves
                if requester_id != user_id:
                    return False

            if user_id in team.members:
                del team.members[user_id]
                team.updated_at = datetime.now(timezone.utc)

                if user_id in self.user_teams:
                    self.user_teams[user_id].discard(team_id)

                logger.info("Team member removed", team_id=team_id, user_id=user_id)
                return True

            return False

    async def update_member_role(
        self,
        team_id: str,
        user_id: str,
        new_role: Permission,
        requester_id: str,
    ) -> bool:
        """Update a member's role."""
        async with self._lock:
            team = self.teams.get(team_id)
            if not team:
                return False

            # Only owner can change roles
            requester = team.members.get(requester_id)
            if not requester or requester.role != Permission.OWNER:
                return False

            # Can't change owner's role
            if user_id == team.owner_id:
                return False

            member = team.members.get(user_id)
            if member:
                member.role = new_role
                team.updated_at = datetime.now(timezone.utc)
                logger.info("Member role updated", team_id=team_id, user_id=user_id, role=new_role)
                return True

            return False

    async def delete_team(self, team_id: str, requester_id: str) -> bool:
        """Delete a team."""
        async with self._lock:
            team = self.teams.get(team_id)
            if not team:
                return False

            # Only owner can delete
            if requester_id != team.owner_id:
                return False

            # Remove team from all members
            for user_id in team.members:
                if user_id in self.user_teams:
                    self.user_teams[user_id].discard(team_id)

            # Delete shared sessions for this team
            sessions_to_delete = [
                sid for sid, s in self.shared_sessions.items()
                if s.team_id == team_id
            ]
            for sid in sessions_to_delete:
                del self.shared_sessions[sid]

            del self.teams[team_id]
            logger.info("Team deleted", team_id=team_id)
            return True

    # ============ Session Sharing ============

    async def share_session(
        self,
        session_id: str,
        owner_id: str,
        name: str,
        team_id: Optional[str] = None,
        is_public: bool = False,
        expires_hours: Optional[int] = None,
    ) -> SharedSession:
        """Share a session for collaboration."""
        async with self._lock:
            share_id = f"share_{secrets.token_urlsafe(12)}"
            share_link = secrets.token_urlsafe(24) if is_public else None

            expires_at = None
            if expires_hours:
                from datetime import timedelta
                expires_at = datetime.now(timezone.utc) + timedelta(hours=expires_hours)

            shared = SharedSession(
                id=share_id,
                session_id=session_id,
                team_id=team_id,
                owner_id=owner_id,
                name=name,
                permissions={owner_id: Permission.OWNER},
                share_link=share_link,
                is_public=is_public,
                expires_at=expires_at,
            )

            # If sharing with a team, add all team members
            if team_id:
                team = self.teams.get(team_id)
                if team:
                    for user_id, member in team.members.items():
                        if user_id != owner_id:
                            shared.permissions[user_id] = member.role

            self.shared_sessions[share_id] = shared
            logger.info("Session shared", share_id=share_id, session_id=session_id)
            return shared

    async def get_shared_session(self, share_id: str) -> Optional[SharedSession]:
        """Get a shared session by ID."""
        shared = self.shared_sessions.get(share_id)
        if shared and shared.expires_at and datetime.now(timezone.utc) > shared.expires_at:
            # Session expired
            del self.shared_sessions[share_id]
            return None
        return shared

    async def get_shared_session_by_link(self, share_link: str) -> Optional[SharedSession]:
        """Get a shared session by public link."""
        for shared in self.shared_sessions.values():
            if shared.share_link == share_link and shared.is_public:
                if shared.expires_at and datetime.now(timezone.utc) > shared.expires_at:
                    continue
                return shared
        return None

    async def list_user_shared_sessions(self, user_id: str) -> List[SharedSession]:
        """List all shared sessions a user has access to."""
        sessions = []
        now = datetime.now(timezone.utc)

        for shared in self.shared_sessions.values():
            if shared.expires_at and now > shared.expires_at:
                continue
            if user_id in shared.permissions:
                sessions.append(shared)

        return sessions

    async def grant_session_access(
        self,
        share_id: str,
        user_id: str,
        permission: Permission,
        requester_id: str,
    ) -> bool:
        """Grant a user access to a shared session."""
        async with self._lock:
            shared = self.shared_sessions.get(share_id)
            if not shared:
                return False

            # Check requester has permission
            requester_perm = shared.permissions.get(requester_id)
            if not requester_perm or requester_perm not in [Permission.OWNER, Permission.EDITOR]:
                return False

            # Only owner can grant editor/owner
            if permission in [Permission.OWNER, Permission.EDITOR]:
                if requester_perm != Permission.OWNER:
                    return False

            shared.permissions[user_id] = permission
            logger.info("Session access granted", share_id=share_id, user_id=user_id, permission=permission)
            return True

    async def revoke_session_access(
        self,
        share_id: str,
        user_id: str,
        requester_id: str,
    ) -> bool:
        """Revoke a user's access to a shared session."""
        async with self._lock:
            shared = self.shared_sessions.get(share_id)
            if not shared:
                return False

            # Can't revoke owner
            if user_id == shared.owner_id:
                return False

            # Check requester has permission
            requester_perm = shared.permissions.get(requester_id)
            if not requester_perm or requester_perm != Permission.OWNER:
                # Users can revoke themselves
                if requester_id != user_id:
                    return False

            if user_id in shared.permissions:
                del shared.permissions[user_id]
                shared.active_users.discard(user_id)
                logger.info("Session access revoked", share_id=share_id, user_id=user_id)
                return True

            return False

    async def unshare_session(self, share_id: str, requester_id: str) -> bool:
        """Stop sharing a session."""
        async with self._lock:
            shared = self.shared_sessions.get(share_id)
            if not shared:
                return False

            if requester_id != shared.owner_id:
                return False

            # Notify all subscribers
            await self._broadcast_event(
                share_id,
                CollaborationEvent.USER_LEFT,
                {"reason": "session_unshared"},
                "system"
            )

            del self.shared_sessions[share_id]
            logger.info("Session unshared", share_id=share_id)
            return True

    # ============ Real-time Collaboration ============

    async def join_session(
        self,
        share_id: str,
        user_id: str,
    ) -> Optional[Permission]:
        """Join a shared session."""
        shared = self.shared_sessions.get(share_id)
        if not shared:
            return None

        # Check if expired
        if shared.expires_at and datetime.now(timezone.utc) > shared.expires_at:
            return None

        # Check permission
        permission = shared.permissions.get(user_id)
        if not permission and not shared.is_public:
            return None

        if shared.is_public and not permission:
            permission = Permission.VIEWER
            shared.permissions[user_id] = permission

        shared.active_users.add(user_id)

        # Broadcast join event
        await self._broadcast_event(
            share_id,
            CollaborationEvent.USER_JOINED,
            {"user_id": user_id},
            user_id
        )

        logger.info("User joined session", share_id=share_id, user_id=user_id)
        return permission

    async def leave_session(self, share_id: str, user_id: str) -> bool:
        """Leave a shared session."""
        shared = self.shared_sessions.get(share_id)
        if not shared:
            return False

        shared.active_users.discard(user_id)

        # Broadcast leave event
        await self._broadcast_event(
            share_id,
            CollaborationEvent.USER_LEFT,
            {"user_id": user_id},
            user_id
        )

        logger.info("User left session", share_id=share_id, user_id=user_id)
        return True

    async def broadcast_event(
        self,
        share_id: str,
        event: CollaborationEvent,
        data: Dict[str, Any],
        sender_id: str,
    ) -> bool:
        """Broadcast an event to all session participants."""
        shared = self.shared_sessions.get(share_id)
        if not shared:
            return False

        # Check sender has permission
        permission = shared.permissions.get(sender_id)
        if not permission:
            return False

        # Viewers can only send cursor/selection events
        viewer_events = [CollaborationEvent.CURSOR_MOVED, CollaborationEvent.SELECTION_CHANGED]
        if permission == Permission.VIEWER and event not in viewer_events:
            return False

        await self._broadcast_event(share_id, event, data, sender_id)
        return True

    async def _broadcast_event(
        self,
        share_id: str,
        event: CollaborationEvent,
        data: Dict[str, Any],
        sender_id: str,
    ):
        """Internal broadcast to all subscribers."""
        message = CollaborationMessage(
            id=f"msg_{secrets.token_urlsafe(8)}",
            shared_session_id=share_id,
            user_id=sender_id,
            event=event,
            data=data,
        )

        callbacks = self.session_subscribers.get(share_id, set())
        for callback in callbacks:
            try:
                await callback(message)
            except Exception as e:
                logger.error("Broadcast callback failed", error=str(e))

    def subscribe(self, share_id: str, callback: Callable) -> Callable:
        """Subscribe to session events. Returns unsubscribe function."""
        if share_id not in self.session_subscribers:
            self.session_subscribers[share_id] = set()
        self.session_subscribers[share_id].add(callback)

        def unsubscribe():
            self.session_subscribers[share_id].discard(callback)
            if not self.session_subscribers[share_id]:
                del self.session_subscribers[share_id]

        return unsubscribe

    async def get_active_users(self, share_id: str) -> List[Dict[str, Any]]:
        """Get list of active users in a session."""
        shared = self.shared_sessions.get(share_id)
        if not shared:
            return []

        users = []
        for user_id in shared.active_users:
            permission = shared.permissions.get(user_id, Permission.VIEWER)
            users.append({
                "user_id": user_id,
                "permission": permission.value,
            })

        return users

    # ============ Statistics ============

    async def get_stats(self) -> Dict[str, Any]:
        """Get collaboration statistics."""
        total_active_users = sum(
            len(s.active_users) for s in self.shared_sessions.values()
        )

        return {
            "total_teams": len(self.teams),
            "total_shared_sessions": len(self.shared_sessions),
            "total_active_collaborations": total_active_users,
            "active_sessions": sum(
                1 for s in self.shared_sessions.values() if s.active_users
            ),
        }


# Singleton instance
_collaboration_service: Optional[CollaborationService] = None


def get_collaboration_service() -> CollaborationService:
    """Get the collaboration service singleton."""
    global _collaboration_service
    if _collaboration_service is None:
        _collaboration_service = CollaborationService()
    return _collaboration_service
