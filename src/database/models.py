"""
SQLAlchemy models for user authentication, code execution, and artifact management.
"""

import uuid
from datetime import datetime, timezone
from enum import Enum as PyEnum
from typing import Optional, List

from sqlalchemy import (
    String,
    Boolean,
    DateTime,
    ForeignKey,
    Text,
    Index,
    Integer,
    JSON,
    Enum,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
)


# Enums for code execution
class ExecutionStatus(str, PyEnum):
    """Status of a code execution."""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    PARTIAL = "partial"


class ArtifactType(str, PyEnum):
    """Type of artifact."""
    UPLOADED = "uploaded"
    GENERATED = "generated"
    OUTPUT = "output"
    SCREENSHOT = "screenshot"
    PREVIEW = "preview"


class OutputType(str, PyEnum):
    """Type of execution output delivery."""
    SNIPPET = "snippet"
    ZIP = "zip"
    PR = "pr"


def utc_now() -> datetime:
    """Get current UTC timestamp."""
    return datetime.now(timezone.utc)


def generate_uuid() -> str:
    """Generate a new UUID string."""
    return str(uuid.uuid4())


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass


class User(Base):
    """User account model."""

    __tablename__ = "users"

    # Primary key
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=generate_uuid,
    )

    # User credentials
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )
    hashed_password: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,  # Nullable for OAuth-only users
    )

    # Profile information
    name: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    avatar_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )

    # Account status
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,  # Email verification required
        nullable=False,
    )
    is_admin: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )
    last_login_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    oauth_accounts: Mapped[List["OAuthAccount"]] = relationship(
        "OAuthAccount",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    verification_tokens: Mapped[List["EmailVerificationToken"]] = relationship(
        "EmailVerificationToken",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email})>"

    def to_dict(self) -> dict:
        """Convert user to dictionary (exclude sensitive fields)."""
        return {
            "id": self.id,
            "email": self.email,
            "name": self.name,
            "avatar_url": self.avatar_url,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "is_admin": self.is_admin,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login_at": self.last_login_at.isoformat() if self.last_login_at else None,
        }


class OAuthAccount(Base):
    """OAuth provider account linked to a user."""

    __tablename__ = "oauth_accounts"

    # Primary key
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=generate_uuid,
    )

    # Foreign key to user
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # OAuth provider info
    provider: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )  # google, github, microsoft
    provider_user_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    provider_email: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )

    # OAuth tokens (encrypted in production)
    access_token: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    refresh_token: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    token_expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="oauth_accounts",
    )

    # Unique constraint: one account per provider per user
    __table_args__ = (
        Index(
            "ix_oauth_provider_user",
            "provider",
            "provider_user_id",
            unique=True,
        ),
    )

    def __repr__(self) -> str:
        return f"<OAuthAccount(provider={self.provider}, user_id={self.user_id})>"


class EmailVerificationToken(Base):
    """Email verification token for new user registration."""

    __tablename__ = "email_verification_tokens"

    # Primary key
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=generate_uuid,
    )

    # Foreign key to user
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Token data
    token: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )
    token_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="email_verification",
    )  # email_verification, password_reset

    # Expiration
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    used_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="verification_tokens",
    )

    def __repr__(self) -> str:
        return f"<EmailVerificationToken(user_id={self.user_id}, type={self.token_type})>"

    @property
    def is_expired(self) -> bool:
        """Check if token has expired."""
        return utc_now() > self.expires_at

    @property
    def is_used(self) -> bool:
        """Check if token has been used."""
        return self.used_at is not None

    @property
    def is_valid(self) -> bool:
        """Check if token is valid (not expired and not used)."""
        return not self.is_expired and not self.is_used


# =============================================================================
# Code Execution Models
# =============================================================================


class Artifact(Base):
    """
    Artifact model for uploaded and generated files.
    Stores metadata only - actual files are in filesystem/GCS.
    """

    __tablename__ = "artifacts"

    # Primary key
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=generate_uuid,
    )

    # Foreign keys
    user_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    session_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        nullable=True,  # No FK since sessions are in different system
        index=True,
    )

    # Artifact info
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )  # uploaded, generated, output, screenshot, preview
    mime_type: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    file_path: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )  # Relative path in /data/artifacts/
    size_bytes: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )
    language: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )  # For code files

    # Additional metadata (JSON)
    metadata_json: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
    )
    # Array of ChromaDB chunk IDs for this artifact
    chromadb_ids: Mapped[Optional[list]] = mapped_column(
        JSON,
        nullable=True,
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )  # For auto-cleanup

    # Relationships
    user: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[user_id],
    )

    __table_args__ = (
        Index("ix_artifacts_type", "type"),
    )

    def __repr__(self) -> str:
        return f"<Artifact(id={self.id}, name={self.name}, type={self.type})>"

    def to_dict(self) -> dict:
        """Convert artifact to dictionary."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "name": self.name,
            "type": self.type,
            "mime_type": self.mime_type,
            "file_path": self.file_path,
            "size_bytes": self.size_bytes,
            "language": self.language,
            "metadata": self.metadata_json,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
        }


class CodeExecution(Base):
    """
    Code execution model - tracks all code execution attempts.
    """

    __tablename__ = "code_executions"

    # Primary key
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=generate_uuid,
    )

    # Foreign keys
    session_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        nullable=True,
        index=True,
    )
    user_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Request details
    prompt: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    language: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    complexity_score: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )
    llm_provider: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )
    llm_model: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )

    # Generated code
    generated_code: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    generated_tests: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Execution results
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=ExecutionStatus.PENDING.value,
    )  # pending, running, passed, failed, partial
    attempt_number: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
    )
    execution_time_ms: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )

    # Multi-signal validation results
    test_passed: Mapped[Optional[bool]] = mapped_column(
        Boolean,
        nullable=True,
    )
    lint_passed: Mapped[Optional[bool]] = mapped_column(
        Boolean,
        nullable=True,
    )
    security_passed: Mapped[Optional[bool]] = mapped_column(
        Boolean,
        nullable=True,
    )

    # Output
    stdout: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    stderr: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    test_results: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
    )
    lint_results: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
    )
    security_results: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
    )

    # Delivery
    output_type: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
    )  # snippet, zip, pr
    output_artifact_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("artifacts.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Quality metrics
    quality_score: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )  # 1-10

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    user: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[user_id],
    )
    output_artifact: Mapped[Optional["Artifact"]] = relationship(
        "Artifact",
        foreign_keys=[output_artifact_id],
    )
    attempts: Mapped[List["ExecutionAttempt"]] = relationship(
        "ExecutionAttempt",
        back_populates="execution",
        cascade="all, delete-orphan",
        order_by="ExecutionAttempt.attempt_number",
    )

    __table_args__ = (
        Index("ix_executions_status", "status"),
    )

    def __repr__(self) -> str:
        return f"<CodeExecution(id={self.id}, status={self.status}, attempt={self.attempt_number})>"

    def to_dict(self) -> dict:
        """Convert execution to dictionary."""
        return {
            "id": self.id,
            "session_id": self.session_id,
            "user_id": self.user_id,
            "prompt": self.prompt,
            "language": self.language,
            "complexity_score": self.complexity_score,
            "llm_provider": self.llm_provider,
            "llm_model": self.llm_model,
            "generated_code": self.generated_code,
            "generated_tests": self.generated_tests,
            "status": self.status,
            "attempt_number": self.attempt_number,
            "execution_time_ms": self.execution_time_ms,
            "test_passed": self.test_passed,
            "lint_passed": self.lint_passed,
            "security_passed": self.security_passed,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "test_results": self.test_results,
            "lint_results": self.lint_results,
            "security_results": self.security_results,
            "output_type": self.output_type,
            "output_artifact_id": self.output_artifact_id,
            "quality_score": self.quality_score,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


class ExecutionAttempt(Base):
    """
    Execution attempt model - tracks retry history with diffs.
    """

    __tablename__ = "execution_attempts"

    # Primary key
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=generate_uuid,
    )

    # Foreign key to execution
    execution_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("code_executions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    attempt_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    # Code version for this attempt
    code_version: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    diff_from_previous: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )  # Unified diff format

    # Error information
    error_type: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    fix_applied: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )  # Description of fix

    # Per-attempt validation
    test_passed: Mapped[Optional[bool]] = mapped_column(
        Boolean,
        nullable=True,
    )
    lint_passed: Mapped[Optional[bool]] = mapped_column(
        Boolean,
        nullable=True,
    )
    security_passed: Mapped[Optional[bool]] = mapped_column(
        Boolean,
        nullable=True,
    )

    # Timestamps
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationship
    execution: Mapped["CodeExecution"] = relationship(
        "CodeExecution",
        back_populates="attempts",
    )

    def __repr__(self) -> str:
        return f"<ExecutionAttempt(execution_id={self.execution_id}, attempt={self.attempt_number})>"

    def to_dict(self) -> dict:
        """Convert attempt to dictionary."""
        return {
            "id": self.id,
            "execution_id": self.execution_id,
            "attempt_number": self.attempt_number,
            "code_version": self.code_version,
            "diff_from_previous": self.diff_from_previous,
            "error_type": self.error_type,
            "error_message": self.error_message,
            "fix_applied": self.fix_applied,
            "test_passed": self.test_passed,
            "lint_passed": self.lint_passed,
            "security_passed": self.security_passed,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }
