"""
Database connection and session management.
Uses SQLAlchemy async for non-blocking database operations.
"""

import os
from pathlib import Path
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool

from src.database.models import Base


# Get database URL from environment or use default
def get_database_url() -> str:
    """Get the database URL, creating directory if needed."""
    # Check for cloud storage path first (GCS FUSE mount)
    cloud_path = os.getenv("CHROMA_PERSIST_DIR", "")
    if cloud_path and cloud_path.startswith("/mnt/"):
        # Use cloud storage for persistence
        db_dir = Path(cloud_path).parent
        db_path = db_dir / "users.db"
    else:
        # Use local data directory
        db_dir = Path("./data")
        db_path = db_dir / "users.db"

    # Ensure directory exists
    db_dir.mkdir(parents=True, exist_ok=True)

    # Return async SQLite URL
    return f"sqlite+aiosqlite:///{db_path}"


# Create async engine
DATABASE_URL = get_database_url()

engine = create_async_engine(
    DATABASE_URL,
    echo=os.getenv("DEBUG", "false").lower() == "true",
    connect_args={"check_same_thread": False},  # Required for SQLite
    poolclass=StaticPool,  # Use static pool for SQLite
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def init_db() -> None:
    """Initialize database and create all tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Get an async database session.
    Use as dependency injection in FastAPI routes.

    Example:
        @app.get("/users")
        async def get_users(db: AsyncSession = Depends(get_async_session)):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Alias for get_async_session for convenience."""
    async for session in get_async_session():
        yield session


# For testing - allows using in-memory database
def get_test_engine(database_url: str = "sqlite+aiosqlite:///:memory:"):
    """Create a test engine with in-memory database."""
    return create_async_engine(
        database_url,
        echo=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )


def get_test_session_factory(test_engine):
    """Create a test session factory."""
    return async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )
