"""
Tests for Session Manager.

Tests:
- Session creation and management
- Session expiration
- User settings
- Conversation history
- Thread safety
- Statistics

Author: API Assistant Team
Date: 2025-12-27
"""

import pytest
import time
import threading
from datetime import datetime, timedelta

from src.sessions import (
    SessionManager,
    Session,
    SessionStatus,
    UserSettings,
    ConversationMessage,
    get_session_manager,
)


class TestSessionCreation:
    """Test session creation."""

    def test_create_basic_session(self):
        """Test creating a basic session."""
        manager = SessionManager()
        session = manager.create_session()

        assert session.session_id is not None
        assert session.status == SessionStatus.ACTIVE
        assert session.user_id is None
        assert session.collection_name is None
        assert len(session.conversation_history) == 0

    def test_create_session_with_user(self):
        """Test creating a session with user ID."""
        manager = SessionManager()
        session = manager.create_session(user_id="user123")

        assert session.user_id == "user123"

    def test_create_session_with_custom_ttl(self):
        """Test creating a session with custom TTL."""
        manager = SessionManager()
        session = manager.create_session(ttl_minutes=120)

        assert session.expires_at is not None
        # Should expire in approximately 120 minutes
        time_diff = (session.expires_at - session.created_at).total_seconds()
        assert 119 * 60 < time_diff < 121 * 60

    def test_create_session_with_settings(self):
        """Test creating a session with custom settings."""
        custom_settings = UserSettings(
            default_search_mode="vector",
            default_n_results=10,
            use_reranking=True,
        )

        manager = SessionManager()
        session = manager.create_session(settings=custom_settings)

        assert session.settings.default_search_mode == "vector"
        assert session.settings.default_n_results == 10
        assert session.settings.use_reranking is True

    def test_create_session_with_collection(self):
        """Test creating a session with collection name."""
        manager = SessionManager()
        session = manager.create_session(collection_name="my_api_docs")

        assert session.collection_name == "my_api_docs"


class TestSessionRetrieval:
    """Test session retrieval."""

    def test_get_existing_session(self):
        """Test retrieving an existing session."""
        manager = SessionManager()
        session = manager.create_session(user_id="user123")

        retrieved = manager.get_session(session.session_id)

        assert retrieved is not None
        assert retrieved.session_id == session.session_id
        assert retrieved.user_id == "user123"

    def test_get_nonexistent_session(self):
        """Test retrieving a nonexistent session."""
        manager = SessionManager()
        session = manager.get_session("nonexistent-id")

        assert session is None

    def test_get_expired_session(self):
        """Test retrieving an expired session."""
        manager = SessionManager()
        session = manager.create_session(ttl_minutes=0)  # Expires immediately

        # Small delay to ensure expiration
        time.sleep(0.1)

        retrieved = manager.get_session(session.session_id)

        assert retrieved is None
        # Session should be marked as expired
        assert session.status == SessionStatus.EXPIRED

    def test_session_touch_on_get(self):
        """Test that getting a session updates last_accessed."""
        manager = SessionManager()
        session = manager.create_session()

        original_time = session.last_accessed
        time.sleep(0.1)

        manager.get_session(session.session_id)

        assert session.last_accessed > original_time


class TestSessionUpdates:
    """Test session updates."""

    def test_update_user_id(self):
        """Test updating user ID."""
        manager = SessionManager()
        session = manager.create_session()

        updated = manager.update_session(session.session_id, user_id="newuser")

        assert updated is not None
        assert updated.user_id == "newuser"

    def test_update_metadata(self):
        """Test updating session metadata."""
        manager = SessionManager()
        session = manager.create_session()

        updated = manager.update_session(
            session.session_id, metadata={"key": "value", "count": 42}
        )

        assert updated is not None
        assert updated.metadata["key"] == "value"
        assert updated.metadata["count"] == 42

    def test_update_collection(self):
        """Test updating collection name."""
        manager = SessionManager()
        session = manager.create_session()

        updated = manager.update_session(session.session_id, collection_name="new_collection")

        assert updated is not None
        assert updated.collection_name == "new_collection"

    def test_update_status(self):
        """Test updating session status."""
        manager = SessionManager()
        session = manager.create_session()

        updated = manager.update_session(session.session_id, status="inactive")

        assert updated is not None
        assert updated.status == SessionStatus.INACTIVE

    def test_update_nonexistent_session(self):
        """Test updating a nonexistent session."""
        manager = SessionManager()
        updated = manager.update_session("nonexistent", user_id="user")

        assert updated is None


class TestSessionDeletion:
    """Test session deletion."""

    def test_delete_existing_session(self):
        """Test deleting an existing session."""
        manager = SessionManager()
        session = manager.create_session()

        deleted = manager.delete_session(session.session_id)

        assert deleted is True
        assert manager.get_session(session.session_id) is None

    def test_delete_nonexistent_session(self):
        """Test deleting a nonexistent session."""
        manager = SessionManager()
        deleted = manager.delete_session("nonexistent")

        assert deleted is False


class TestSessionListing:
    """Test session listing."""

    def test_list_all_sessions(self):
        """Test listing all sessions."""
        manager = SessionManager()
        manager.create_session(user_id="user1")
        manager.create_session(user_id="user2")
        manager.create_session(user_id="user3")

        sessions = manager.list_sessions()

        assert len(sessions) == 3

    def test_list_sessions_by_user(self):
        """Test listing sessions filtered by user."""
        manager = SessionManager()
        manager.create_session(user_id="user1")
        manager.create_session(user_id="user1")
        manager.create_session(user_id="user2")

        sessions = manager.list_sessions(user_id="user1")

        assert len(sessions) == 2
        assert all(s.user_id == "user1" for s in sessions)

    def test_list_sessions_by_status(self):
        """Test listing sessions filtered by status."""
        manager = SessionManager()
        session1 = manager.create_session()
        session2 = manager.create_session()
        manager.update_session(session2.session_id, status="inactive")

        active_sessions = manager.list_sessions(status=SessionStatus.ACTIVE)

        assert len(active_sessions) == 1
        assert active_sessions[0].session_id == session1.session_id


class TestSessionExpiration:
    """Test session expiration."""

    def test_session_expiration_check(self):
        """Test session expiration checking."""
        manager = SessionManager()
        session = manager.create_session(ttl_minutes=0)

        time.sleep(0.1)

        assert session.is_expired() is True

    def test_cleanup_expired_sessions(self):
        """Test cleanup of expired sessions."""
        manager = SessionManager()
        # Create expired sessions
        manager.create_session(ttl_minutes=0)
        manager.create_session(ttl_minutes=0)
        # Create active session
        manager.create_session(ttl_minutes=60)

        time.sleep(0.1)

        count = manager.cleanup_expired_sessions()

        assert count == 2
        assert len(manager.list_sessions()) == 1

    def test_extend_session(self):
        """Test extending session expiration."""
        manager = SessionManager()
        session = manager.create_session(ttl_minutes=60)

        original_expiry = session.expires_at

        extended = manager.extend_session(session.session_id, 30)

        assert extended is not None
        assert extended.expires_at > original_expiry
        # Should be extended by 30 minutes
        time_diff = (extended.expires_at - original_expiry).total_seconds()
        assert 29 * 60 < time_diff < 31 * 60


class TestConversationHistory:
    """Test conversation history management."""

    def test_add_message(self):
        """Test adding a message to conversation history."""
        manager = SessionManager()
        session = manager.create_session()

        session.add_message("user", "Hello!")

        assert len(session.conversation_history) == 1
        assert session.conversation_history[0].role == "user"
        assert session.conversation_history[0].content == "Hello!"

    def test_add_message_with_metadata(self):
        """Test adding a message with metadata."""
        manager = SessionManager()
        session = manager.create_session()

        session.add_message("user", "Search query", metadata={"query_type": "vector"})

        assert session.conversation_history[0].metadata["query_type"] == "vector"

    def test_get_recent_messages(self):
        """Test getting recent messages."""
        manager = SessionManager()
        session = manager.create_session()

        for i in range(20):
            session.add_message("user", f"Message {i}")

        recent = session.get_recent_messages(5)

        assert len(recent) == 5
        assert recent[0].content == "Message 15"
        assert recent[4].content == "Message 19"

    def test_clear_history(self):
        """Test clearing conversation history."""
        manager = SessionManager()
        session = manager.create_session()

        session.add_message("user", "Hello!")
        session.add_message("assistant", "Hi!")

        session.clear_history()

        assert len(session.conversation_history) == 0

    def test_get_session_history(self):
        """Test getting session history via manager."""
        manager = SessionManager()
        session = manager.create_session()

        session.add_message("user", "Test message 1")
        session.add_message("assistant", "Test message 2")

        history = manager.get_session_history(session.session_id)

        assert history is not None
        assert len(history) == 2

    def test_get_session_history_with_limit(self):
        """Test getting limited session history."""
        manager = SessionManager()
        session = manager.create_session()

        for i in range(10):
            session.add_message("user", f"Message {i}")

        history = manager.get_session_history(session.session_id, limit=3)

        assert len(history) == 3


class TestSessionStatistics:
    """Test session statistics."""

    def test_get_stats(self):
        """Test getting session statistics."""
        manager = SessionManager()
        manager.create_session(user_id="user1")
        manager.create_session(user_id="user2")
        session3 = manager.create_session(user_id="user1")
        manager.update_session(session3.session_id, status="inactive")

        stats = manager.get_stats()

        assert stats["total_sessions"] == 3
        assert stats["active_sessions"] == 2
        assert stats["inactive_sessions"] == 1
        assert stats["unique_users"] == 2

    def test_stats_with_expired_sessions(self):
        """Test statistics with expired sessions."""
        manager = SessionManager()
        manager.create_session(ttl_minutes=0)
        manager.create_session(ttl_minutes=60)

        time.sleep(0.1)

        stats = manager.get_stats()

        assert stats["expired_sessions"] == 1
        assert stats["active_sessions"] == 1


class TestSessionSerialization:
    """Test session serialization."""

    def test_session_to_dict(self):
        """Test converting session to dictionary."""
        manager = SessionManager()
        session = manager.create_session(user_id="user123", collection_name="test_collection")
        session.add_message("user", "Hello")

        session_dict = session.to_dict()

        assert session_dict["session_id"] == session.session_id
        assert session_dict["user_id"] == "user123"
        assert session_dict["status"] == "active"
        assert session_dict["collection_name"] == "test_collection"
        assert session_dict["message_count"] == 1
        assert "created_at" in session_dict
        assert "settings" in session_dict


class TestThreadSafety:
    """Test thread-safe operations."""

    def test_concurrent_session_creation(self):
        """Test concurrent session creation."""
        manager = SessionManager()
        sessions = []

        def create_sessions():
            for _ in range(10):
                session = manager.create_session()
                sessions.append(session)

        threads = [threading.Thread(target=create_sessions) for _ in range(5)]

        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        # Should have created 50 sessions (10 per thread × 5 threads)
        assert len(sessions) == 50
        # All session IDs should be unique
        assert len(set(s.session_id for s in sessions)) == 50

    def test_concurrent_session_access(self):
        """Test concurrent session access."""
        manager = SessionManager()
        session = manager.create_session()

        results = []

        def access_session():
            for _ in range(100):
                s = manager.get_session(session.session_id)
                if s:
                    results.append(s.session_id)

        threads = [threading.Thread(target=access_session) for _ in range(5)]

        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        # All accesses should succeed
        assert len(results) == 500


class TestGlobalSessionManager:
    """Test global session manager."""

    def test_get_session_manager_singleton(self):
        """Test that get_session_manager returns singleton."""
        manager1 = get_session_manager()
        manager2 = get_session_manager()

        assert manager1 is manager2

    def test_global_manager_persistence(self):
        """Test that sessions persist across manager calls."""
        manager1 = get_session_manager()
        session = manager1.create_session(user_id="test")

        manager2 = get_session_manager()
        retrieved = manager2.get_session(session.session_id)

        assert retrieved is not None
        assert retrieved.user_id == "test"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
