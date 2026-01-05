"""
Session Management Demonstration.

Demonstrates:
- Creating and managing sessions
- User-specific settings
- Conversation history tracking
- Session expiration and cleanup
- Multi-user scenarios

Author: API Assistant Team
Date: 2025-12-27
"""

import time
from datetime import datetime

from src.sessions import (
    SessionManager,
    UserSettings,
    get_session_manager,
)


def print_section(title: str):
    """Print section header."""
    print(f"\n{'=' * 60}")
    print(f" {title}")
    print('=' * 60)


def demo_basic_session():
    """Demonstrate basic session creation and management."""
    print_section("1. Basic Session Management")

    manager = SessionManager()

    # Create a session
    print("\n📝 Creating a new session...")
    session = manager.create_session(user_id="alice")
    print(f"✓ Session created: {session.session_id}")
    print(f"  User: {session.user_id}")
    print(f"  Status: {session.status.value}")
    print(f"  Created: {session.created_at.strftime('%Y-%m-%d %H:%M:%S')}")

    # Retrieve session
    print(f"\n🔍 Retrieving session {session.session_id[:8]}...")
    retrieved = manager.get_session(session.session_id)
    print(f"✓ Session found: {retrieved.user_id}")

    # Update session
    print("\n📝 Updating session metadata...")
    manager.update_session(
        session.session_id,
        metadata={"theme": "dark", "language": "en"}
    )
    print(f"✓ Metadata updated: {session.metadata}")


def demo_user_settings():
    """Demonstrate user-specific settings."""
    print_section("2. User-Specific Settings")

    manager = SessionManager()

    # Create custom settings
    alice_settings = UserSettings(
        default_search_mode="vector",
        default_n_results=10,
        use_reranking=True,
        show_scores=True,
        max_content_length=1000,
    )

    bob_settings = UserSettings(
        default_search_mode="hybrid",
        default_n_results=5,
        use_reranking=False,
        show_scores=False,
        max_content_length=500,
    )

    # Create sessions with different settings
    print("\n👤 Creating session for Alice...")
    alice_session = manager.create_session(
        user_id="alice",
        settings=alice_settings,
        collection_name="alice_docs"
    )
    print(f"✓ Alice's preferences:")
    print(f"  Search mode: {alice_session.settings.default_search_mode}")
    print(f"  Results limit: {alice_session.settings.default_n_results}")
    print(f"  Use reranking: {alice_session.settings.use_reranking}")

    print("\n👤 Creating session for Bob...")
    bob_session = manager.create_session(
        user_id="bob",
        settings=bob_settings,
        collection_name="bob_docs"
    )
    print(f"✓ Bob's preferences:")
    print(f"  Search mode: {bob_session.settings.default_search_mode}")
    print(f"  Results limit: {bob_session.settings.default_n_results}")
    print(f"  Use reranking: {bob_session.settings.use_reranking}")


def demo_conversation_history():
    """Demonstrate conversation history tracking."""
    print_section("3. Conversation History")

    manager = SessionManager()
    session = manager.create_session(user_id="charlie")

    print("\n💬 Simulating a conversation...")

    # Add conversation messages
    conversations = [
        ("user", "How do I parse an OpenAPI spec?"),
        ("assistant", "Use the OpenAPIParser class from src.parsers"),
        ("user", "Can you show me an example?"),
        ("assistant", "Sure! Here's how:\n\nfrom src.parsers import OpenAPIParser\nparser = OpenAPIParser()\nresult = parser.parse('spec.yaml')"),
        ("user", "Thanks! How do I search the vector store?"),
        ("assistant", "Use the VectorStore.search() method with your query"),
    ]

    for role, content in conversations:
        session.add_message(role, content, metadata={"timestamp": datetime.now().isoformat()})
        print(f"  [{role}]: {content[:50]}...")

    print(f"\n✓ Total messages: {len(session.conversation_history)}")

    # Get recent messages
    print("\n📜 Recent conversation (last 3 messages):")
    recent = session.get_recent_messages(3)
    for msg in recent:
        print(f"  [{msg.role}] {msg.timestamp.strftime('%H:%M:%S')}: {msg.content[:60]}...")

    # Get full history via manager
    history = manager.get_session_history(session.session_id)
    print(f"\n📚 Full history: {len(history)} messages")


def demo_session_expiration():
    """Demonstrate session expiration and cleanup."""
    print_section("4. Session Expiration & Cleanup")

    manager = SessionManager()

    # Create sessions with different TTLs
    print("\n⏰ Creating sessions with different expiration times...")

    session1 = manager.create_session(user_id="user1", ttl_minutes=60)
    print(f"✓ Session 1: expires in 60 minutes")

    session2 = manager.create_session(user_id="user2", ttl_minutes=120)
    print(f"✓ Session 2: expires in 120 minutes")

    # Create a session that expires immediately (for demo)
    session3 = manager.create_session(user_id="user3", ttl_minutes=0)
    print(f"✓ Session 3: expires immediately (for demo)")

    # Wait a bit
    time.sleep(0.2)

    # Check expiration
    print("\n🔍 Checking session expiration...")
    print(f"  Session 1 expired: {session1.is_expired()}")
    print(f"  Session 2 expired: {session2.is_expired()}")
    print(f"  Session 3 expired: {session3.is_expired()}")

    # Cleanup expired sessions
    print("\n🧹 Cleaning up expired sessions...")
    count = manager.cleanup_expired_sessions()
    print(f"✓ Removed {count} expired session(s)")

    # Extend session
    print(f"\n⏰ Extending session 1 by 30 minutes...")
    original_expiry = session1.expires_at
    manager.extend_session(session1.session_id, 30)
    print(f"✓ Original expiry: {original_expiry.strftime('%H:%M:%S')}")
    print(f"✓ New expiry: {session1.expires_at.strftime('%H:%M:%S')}")


def demo_multi_user_scenarios():
    """Demonstrate multi-user scenarios."""
    print_section("5. Multi-User Scenarios")

    manager = SessionManager()

    # Create multiple sessions for different users
    print("\n👥 Creating sessions for multiple users...")

    users = ["alice", "bob", "charlie", "alice", "bob"]
    for user in users:
        session = manager.create_session(user_id=user)
        print(f"✓ Created session for {user}: {session.session_id[:8]}...")

    # List all sessions
    print("\n📋 All sessions:")
    all_sessions = manager.list_sessions()
    print(f"✓ Total sessions: {len(all_sessions)}")

    # List sessions by user
    print("\n🔍 Sessions for Alice:")
    alice_sessions = manager.list_sessions(user_id="alice")
    for s in alice_sessions:
        print(f"  - {s.session_id[:8]}... (created: {s.created_at.strftime('%H:%M:%S')})")

    print("\n🔍 Sessions for Bob:")
    bob_sessions = manager.list_sessions(user_id="bob")
    for s in bob_sessions:
        print(f"  - {s.session_id[:8]}... (created: {s.created_at.strftime('%H:%M:%S')})")

    # Get statistics
    print("\n📊 Session Statistics:")
    stats = manager.get_stats()
    for key, value in stats.items():
        print(f"  {key.replace('_', ' ').title()}: {value}")


def demo_session_serialization():
    """Demonstrate session serialization."""
    print_section("6. Session Serialization")

    manager = SessionManager()
    session = manager.create_session(
        user_id="demo_user",
        collection_name="demo_collection"
    )

    # Add some conversation
    session.add_message("user", "Hello!")
    session.add_message("assistant", "Hi there!")

    # Serialize to dict
    print("\n📄 Converting session to dictionary...")
    session_dict = session.to_dict()

    print("\n✓ Session data:")
    for key, value in session_dict.items():
        if key == "settings":
            print(f"  {key}:")
            for setting_key, setting_value in value.items():
                print(f"    - {setting_key}: {setting_value}")
        else:
            print(f"  {key}: {value}")


def demo_global_manager():
    """Demonstrate global session manager."""
    print_section("7. Global Session Manager")

    print("\n🌍 Using global session manager...")

    # Get global manager (singleton)
    manager1 = get_session_manager()
    session = manager1.create_session(user_id="global_user")
    print(f"✓ Created session via manager1: {session.session_id[:8]}...")

    # Get manager again (same instance)
    manager2 = get_session_manager()
    retrieved = manager2.get_session(session.session_id)
    print(f"✓ Retrieved session via manager2: {retrieved.session_id[:8]}...")

    # Verify it's the same manager
    print(f"\n✓ Same manager instance: {manager1 is manager2}")
    print(f"✓ Session persists across manager calls")


def main():
    """Run all demonstrations."""
    print("\n" + "=" * 60)
    print(" API ASSISTANT - SESSION MANAGEMENT DEMO")
    print("=" * 60)

    demo_basic_session()
    demo_user_settings()
    demo_conversation_history()
    demo_session_expiration()
    demo_multi_user_scenarios()
    demo_session_serialization()
    demo_global_manager()

    print("\n" + "=" * 60)
    print(" ✓ DEMO COMPLETE")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
