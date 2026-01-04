"""
Session Management for Multi-User Support.

Provides session management for multiple users with:
- Isolated sessions for each user
- User-specific settings and preferences
- Conversation history tracking
- Session expiration and cleanup
- Thread-safe session operations

Author: API Assistant Team
Date: 2025-12-27
"""

import time
import uuid
import threading
import structlog
import json
import os
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum

logger = structlog.get_logger(__name__)


class SessionStatus(Enum):
    """Session status."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    EXPIRED = "expired"


@dataclass
class UserSettings:
    """User-specific settings and preferences."""

    # Search preferences
    default_search_mode: str = "hybrid"  # vector, hybrid, bm25
    default_n_results: int = 5
    use_reranking: bool = False
    use_query_expansion: bool = False
    use_diversification: bool = False

    # Display preferences
    show_scores: bool = True
    show_metadata: bool = True
    max_content_length: int = 500  # Max chars to display

    # Collection preferences
    default_collection: Optional[str] = None

    # Custom metadata
    custom_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConversationMessage:
    """A single message in the conversation history."""

    role: str  # user, assistant, system
    content: str
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Session:
    """User session with isolated state."""

    session_id: str
    user_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    last_accessed: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    status: SessionStatus = SessionStatus.ACTIVE

    # User settings
    settings: UserSettings = field(default_factory=UserSettings)

    # Conversation history
    conversation_history: List[ConversationMessage] = field(default_factory=list)

    # Session-specific metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Collection name for this session (optional)
    collection_name: Optional[str] = None

    def is_expired(self) -> bool:
        """Check if session has expired."""
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at

    def touch(self):
        """Update last accessed timestamp."""
        self.last_accessed = datetime.now()
        if self.status == SessionStatus.INACTIVE:
            self.status = SessionStatus.ACTIVE

    def add_message(self, role: str, content: str, metadata: Optional[Dict] = None):
        """Add a message to conversation history."""
        message = ConversationMessage(
            role=role,
            content=content,
            timestamp=datetime.now(),
            metadata=metadata or {},
        )
        self.conversation_history.append(message)

    def get_recent_messages(self, n: int = 10) -> List[ConversationMessage]:
        """Get N most recent messages."""
        return self.conversation_history[-n:]

    def clear_history(self):
        """Clear conversation history."""
        self.conversation_history = []

    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary for serialization."""
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "created_at": self.created_at.isoformat(),
            "last_accessed": self.last_accessed.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "status": self.status.value,
            "settings": {
                "default_search_mode": self.settings.default_search_mode,
                "default_n_results": self.settings.default_n_results,
                "use_reranking": self.settings.use_reranking,
                "use_query_expansion": self.settings.use_query_expansion,
                "use_diversification": self.settings.use_diversification,
                "show_scores": self.settings.show_scores,
                "show_metadata": self.settings.show_metadata,
                "max_content_length": self.settings.max_content_length,
                "default_collection": self.settings.default_collection,
                "custom_metadata": self.settings.custom_metadata,
            },
            "conversation_history": [
                {
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat(),
                    "metadata": msg.metadata,
                }
                for msg in self.conversation_history
            ],
            "message_count": len(self.conversation_history),
            "metadata": self.metadata,
            "collection_name": self.collection_name,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Session":
        """Create session from dictionary."""
        # Parse settings
        settings_data = data.get("settings", {})
        settings = UserSettings(
            default_search_mode=settings_data.get("default_search_mode", "hybrid"),
            default_n_results=settings_data.get("default_n_results", 5),
            use_reranking=settings_data.get("use_reranking", False),
            use_query_expansion=settings_data.get("use_query_expansion", False),
            use_diversification=settings_data.get("use_diversification", False),
            show_scores=settings_data.get("show_scores", True),
            show_metadata=settings_data.get("show_metadata", True),
            max_content_length=settings_data.get("max_content_length", 500),
            default_collection=settings_data.get("default_collection"),
            custom_metadata=settings_data.get("custom_metadata", {}),
        )

        # Parse conversation history
        conversation_history = []
        for msg_data in data.get("conversation_history", []):
            msg = ConversationMessage(
                role=msg_data["role"],
                content=msg_data["content"],
                timestamp=datetime.fromisoformat(msg_data["timestamp"]),
                metadata=msg_data.get("metadata", {}),
            )
            conversation_history.append(msg)

        # Create session
        session = cls(
            session_id=data["session_id"],
            user_id=data.get("user_id"),
            created_at=datetime.fromisoformat(data["created_at"]),
            last_accessed=datetime.fromisoformat(data["last_accessed"]),
            expires_at=datetime.fromisoformat(data["expires_at"]) if data.get("expires_at") else None,
            status=SessionStatus(data["status"]),
            settings=settings,
            conversation_history=conversation_history,
            metadata=data.get("metadata", {}),
            collection_name=data.get("collection_name"),
        )

        return session


class SessionManager:
    """
    Manages user sessions for multi-user support.

    Features:
    - Create and manage isolated sessions
    - Session expiration and cleanup
    - Thread-safe operations
    - User-specific settings
    - Conversation history tracking
    """

    def __init__(
        self,
        default_ttl_minutes: int = 60,
        cleanup_interval_minutes: int = 10,
        sessions_file: Optional[str] = None,
    ):
        """
        Initialize session manager.

        Args:
            default_ttl_minutes: Default session TTL in minutes
            cleanup_interval_minutes: How often to run cleanup
            sessions_file: Path to sessions JSON file (default: data/sessions.json)
        """
        self.sessions: Dict[str, Session] = {}
        self.default_ttl = timedelta(minutes=default_ttl_minutes)
        self.cleanup_interval = timedelta(minutes=cleanup_interval_minutes)
        self.lock = threading.RLock()
        self.last_cleanup = datetime.now()

        # Set sessions file path
        if sessions_file is None:
            # Default to data/sessions.json in project root
            project_root = Path(__file__).parent.parent.parent
            sessions_file = project_root / "data" / "sessions.json"
        self.sessions_file = Path(sessions_file)

        # Load existing sessions from file
        self._load_sessions()

        logger.info(
            "Session manager initialized",
            default_ttl_minutes=default_ttl_minutes,
            cleanup_interval_minutes=cleanup_interval_minutes,
            sessions_file=str(self.sessions_file),
            loaded_sessions=len(self.sessions),
        )

    def _load_sessions(self):
        """Load sessions from JSON file."""
        try:
            if self.sessions_file.exists():
                with open(self.sessions_file, "r") as f:
                    data = json.load(f)
                    for session_data in data.get("sessions", []):
                        try:
                            session = Session.from_dict(session_data)
                            self.sessions[session.session_id] = session
                        except Exception as e:
                            logger.error(
                                "Failed to load session",
                                session_id=session_data.get("session_id"),
                                error=str(e),
                            )
                logger.info(f"Loaded {len(self.sessions)} sessions from {self.sessions_file}")
            else:
                logger.info(f"No existing sessions file found at {self.sessions_file}")
        except Exception as e:
            logger.error(f"Failed to load sessions file: {e}")

    def _save_sessions(self):
        """Save sessions to JSON file."""
        try:
            # Create directory if it doesn't exist
            self.sessions_file.parent.mkdir(parents=True, exist_ok=True)

            # Serialize all sessions
            data = {
                "sessions": [session.to_dict() for session in self.sessions.values()],
                "last_updated": datetime.now().isoformat(),
            }

            # Write to file
            with open(self.sessions_file, "w") as f:
                json.dump(data, f, indent=2)

            logger.debug(f"Saved {len(self.sessions)} sessions to {self.sessions_file}")
        except Exception as e:
            logger.error(f"Failed to save sessions file: {e}")

    def create_session(
        self,
        user_id: Optional[str] = None,
        ttl_minutes: Optional[int] = None,
        settings: Optional[UserSettings] = None,
        collection_name: Optional[str] = None,
    ) -> Session:
        """
        Create a new session.

        Args:
            user_id: Optional user identifier
            ttl_minutes: Session TTL in minutes (uses default if None)
            settings: Optional user settings
            collection_name: Optional collection name for this session

        Returns:
            Created Session
        """
        with self.lock:
            session_id = str(uuid.uuid4())
            ttl = timedelta(minutes=ttl_minutes) if ttl_minutes is not None else self.default_ttl
            expires_at = datetime.now() + ttl

            session = Session(
                session_id=session_id,
                user_id=user_id,
                expires_at=expires_at,
                settings=settings or UserSettings(),
                collection_name=collection_name,
            )

            self.sessions[session_id] = session

            logger.info(
                "Session created",
                session_id=session_id,
                user_id=user_id,
                expires_at=expires_at.isoformat(),
            )

            # Persist to file
            self._save_sessions()

            return session

    def get_session(self, session_id: str) -> Optional[Session]:
        """
        Get session by ID.

        Args:
            session_id: Session identifier

        Returns:
            Session if found and not expired, None otherwise
        """
        with self.lock:
            session = self.sessions.get(session_id)

            if session is None:
                return None

            # Check expiration
            if session.is_expired():
                session.status = SessionStatus.EXPIRED
                logger.warning("Session expired", session_id=session_id)
                return None

            # Touch session
            session.touch()

            return session

    def get_session_by_id(self, session_id: str, include_expired: bool = False) -> Optional[Session]:
        """
        Get session by ID, optionally including expired sessions.

        This method is useful for viewing session details without activating them.

        Args:
            session_id: Session identifier
            include_expired: If True, return expired sessions as well

        Returns:
            Session if found, None otherwise
        """
        with self.lock:
            session = self.sessions.get(session_id)

            if session is None:
                return None

            # Update status if expired
            if session.is_expired():
                session.status = SessionStatus.EXPIRED

            # If not including expired and session is expired, return None
            if not include_expired and session.is_expired():
                return None

            return session

    def update_session(self, session_id: str, **kwargs) -> Optional[Session]:
        """
        Update session attributes.

        Args:
            session_id: Session identifier
            **kwargs: Attributes to update

        Returns:
            Updated Session if found, None otherwise
        """
        with self.lock:
            session = self.get_session(session_id)

            if session is None:
                return None

            # Update allowed attributes
            if "user_id" in kwargs:
                session.user_id = kwargs["user_id"]
            if "metadata" in kwargs:
                session.metadata.update(kwargs["metadata"])
            if "collection_name" in kwargs:
                session.collection_name = kwargs["collection_name"]

            session.touch()

            # Update status AFTER touch to prevent reactivation
            if "status" in kwargs:
                session.status = SessionStatus(kwargs["status"])

            logger.info("Session updated", session_id=session_id)

            # Persist to file
            self._save_sessions()

            return session

    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session.

        Args:
            session_id: Session identifier

        Returns:
            True if deleted, False if not found
        """
        with self.lock:
            if session_id in self.sessions:
                del self.sessions[session_id]
                logger.info("Session deleted", session_id=session_id)

                # Persist to file
                self._save_sessions()

                return True

            return False

    def list_sessions(
        self,
        user_id: Optional[str] = None,
        status: Optional[SessionStatus] = None,
    ) -> List[Session]:
        """
        List sessions with optional filters.

        Args:
            user_id: Filter by user ID
            status: Filter by status

        Returns:
            List of matching sessions
        """
        with self.lock:
            # Update session statuses based on expiration before filtering
            for session in self.sessions.values():
                if session.is_expired() and session.status != SessionStatus.EXPIRED:
                    session.status = SessionStatus.EXPIRED

            sessions = list(self.sessions.values())

            if user_id is not None:
                sessions = [s for s in sessions if s.user_id == user_id]

            if status is not None:
                # For filtering, also consider expired sessions when filtering by status
                if status == SessionStatus.EXPIRED:
                    sessions = [s for s in sessions if s.is_expired()]
                else:
                    # For ACTIVE and INACTIVE, only include non-expired sessions
                    sessions = [s for s in sessions if s.status == status and not s.is_expired()]

            return sessions

    def cleanup_expired_sessions(self) -> int:
        """
        Remove expired sessions.

        Returns:
            Number of sessions cleaned up
        """
        with self.lock:
            expired_ids = [
                sid for sid, session in self.sessions.items()
                if session.is_expired()
            ]

            for sid in expired_ids:
                del self.sessions[sid]

            if expired_ids:
                logger.info("Cleaned up expired sessions", count=len(expired_ids))

                # Persist to file
                self._save_sessions()

            self.last_cleanup = datetime.now()

            return len(expired_ids)

    def auto_cleanup(self):
        """Automatically cleanup if interval has passed."""
        if datetime.now() - self.last_cleanup > self.cleanup_interval:
            self.cleanup_expired_sessions()

    def get_stats(self) -> Dict[str, Any]:
        """
        Get session statistics.

        Returns:
            Statistics dictionary
        """
        with self.lock:
            active_count = sum(
                1 for s in self.sessions.values()
                if s.status == SessionStatus.ACTIVE and not s.is_expired()
            )
            inactive_count = sum(
                1 for s in self.sessions.values()
                if s.status == SessionStatus.INACTIVE
            )
            expired_count = sum(
                1 for s in self.sessions.values()
                if s.is_expired()
            )

            return {
                "total_sessions": len(self.sessions),
                "active_sessions": active_count,
                "inactive_sessions": inactive_count,
                "expired_sessions": expired_count,
                "unique_users": len(set(s.user_id for s in self.sessions.values() if s.user_id)),
            }

    def extend_session(self, session_id: str, minutes: int) -> Optional[Session]:
        """
        Extend session expiration.

        Args:
            session_id: Session identifier
            minutes: Minutes to add to expiration

        Returns:
            Updated Session if found, None otherwise
        """
        with self.lock:
            session = self.get_session(session_id)

            if session is None:
                return None

            if session.expires_at:
                session.expires_at += timedelta(minutes=minutes)

            logger.info("Session extended", session_id=session_id, minutes=minutes)

            # Persist to file
            self._save_sessions()

            return session

    def activate_session(self, session_id: str, ttl_minutes: Optional[int] = None) -> Optional[Session]:
        """
        Activate an expired or inactive session.

        This resets the expiration time and sets the status to ACTIVE.

        Args:
            session_id: Session identifier
            ttl_minutes: New TTL in minutes (uses default if None)

        Returns:
            Activated Session if found, None otherwise
        """
        with self.lock:
            # Get session regardless of expiration status
            session = self.get_session_by_id(session_id, include_expired=True)

            if session is None:
                return None

            # Set new expiration time
            ttl = timedelta(minutes=ttl_minutes) if ttl_minutes is not None else self.default_ttl
            session.expires_at = datetime.now() + ttl

            # Activate the session
            session.status = SessionStatus.ACTIVE
            session.last_accessed = datetime.now()

            logger.info(
                "Session activated",
                session_id=session_id,
                new_expires_at=session.expires_at.isoformat(),
            )

            # Persist to file
            self._save_sessions()

            return session

    def get_session_history(
        self, session_id: str, limit: Optional[int] = None
    ) -> Optional[List[ConversationMessage]]:
        """
        Get conversation history for a session.

        Args:
            session_id: Session identifier
            limit: Maximum number of messages to return

        Returns:
            List of messages if session found, None otherwise
        """
        session = self.get_session(session_id)

        if session is None:
            return None

        if limit is None:
            return session.conversation_history

        return session.get_recent_messages(limit)


# Global session manager instance
_session_manager: Optional[SessionManager] = None


def get_session_manager() -> SessionManager:
    """Get or create global session manager instance."""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager
