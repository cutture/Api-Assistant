"""
Pytest configuration for session manager tests.

Provides fixtures for test isolation.
"""

import pytest
import tempfile
import os
from pathlib import Path


@pytest.fixture(autouse=True, scope="function")
def clear_sessions():
    """Clear sessions before each test for isolation."""
    # Get the default sessions file path
    from src.sessions import SessionManager

    # Create a temporary sessions file for this test
    fd, path = tempfile.mkstemp(suffix='.json')
    os.close(fd)

    # Monkey-patch the SessionManager __init__ to use temp file
    original_init = SessionManager.__init__

    def patched_init(self, default_ttl_minutes=60, cleanup_interval_minutes=10, sessions_file=None):
        # Force use of temp file if not explicitly provided
        if sessions_file is None:
            sessions_file = path
        original_init(self, default_ttl_minutes, cleanup_interval_minutes, sessions_file)

    SessionManager.__init__ = patched_init

    yield

    # Restore original __init__
    SessionManager.__init__ = original_init

    # Cleanup temp file
    try:
        os.unlink(path)
    except OSError:
        pass


@pytest.fixture
def temp_sessions_file():
    """Create a temporary sessions file for testing."""
    # Create a temporary file
    fd, path = tempfile.mkstemp(suffix='.json')
    os.close(fd)

    yield path

    # Cleanup after test
    try:
        os.unlink(path)
    except OSError:
        pass


@pytest.fixture
def clean_session_manager(temp_sessions_file):
    """Create a clean SessionManager instance for each test."""
    from src.sessions import SessionManager

    # Create manager with temporary sessions file
    manager = SessionManager(sessions_file=temp_sessions_file)

    return manager
