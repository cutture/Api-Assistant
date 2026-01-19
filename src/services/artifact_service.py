"""
Artifact Service for Intelligent Coding Agent.

Provides storage abstraction for artifacts with support for:
- Local filesystem storage (development)
- Google Cloud Storage (production)
"""

import hashlib
import mimetypes
import os
import shutil
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import BinaryIO, Optional

from src.config import get_settings


@dataclass
class StoredArtifact:
    """Result of storing an artifact."""
    file_path: str  # Relative path for DB storage
    size_bytes: int
    content_hash: str
    mime_type: Optional[str]


@dataclass
class ArtifactContent:
    """Content retrieved from storage."""
    data: bytes
    mime_type: Optional[str]
    size_bytes: int


class StorageBackend:
    """Abstract base class for storage backends."""

    def save(
        self,
        user_id: str,
        artifact_id: str,
        filename: str,
        content: bytes | BinaryIO,
    ) -> StoredArtifact:
        """Save artifact to storage."""
        raise NotImplementedError

    def get(self, file_path: str) -> ArtifactContent:
        """Retrieve artifact from storage."""
        raise NotImplementedError

    def delete(self, file_path: str) -> bool:
        """Delete artifact from storage."""
        raise NotImplementedError

    def exists(self, file_path: str) -> bool:
        """Check if artifact exists."""
        raise NotImplementedError

    def get_download_url(self, file_path: str, expires_in_seconds: int = 3600) -> str:
        """Get a URL for downloading the artifact."""
        raise NotImplementedError


class LocalStorageBackend(StorageBackend):
    """Local filesystem storage backend."""

    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _get_full_path(self, file_path: str) -> Path:
        """Get full filesystem path from relative path."""
        return self.base_path / file_path

    def save(
        self,
        user_id: str,
        artifact_id: str,
        filename: str,
        content: bytes | BinaryIO,
    ) -> StoredArtifact:
        """Save artifact to local filesystem."""
        # Create directory structure: {base}/{user_id}/{artifact_id}/
        artifact_dir = self.base_path / user_id / artifact_id
        artifact_dir.mkdir(parents=True, exist_ok=True)

        # Get content as bytes
        if isinstance(content, bytes):
            data = content
        else:
            data = content.read()

        # Calculate hash
        content_hash = hashlib.sha256(data).hexdigest()

        # Determine mime type
        mime_type, _ = mimetypes.guess_type(filename)

        # Write file
        file_path = artifact_dir / filename
        file_path.write_bytes(data)

        # Return relative path for DB storage
        relative_path = f"{user_id}/{artifact_id}/{filename}"

        return StoredArtifact(
            file_path=relative_path,
            size_bytes=len(data),
            content_hash=content_hash,
            mime_type=mime_type,
        )

    def get(self, file_path: str) -> ArtifactContent:
        """Retrieve artifact from local filesystem."""
        full_path = self._get_full_path(file_path)

        if not full_path.exists():
            raise FileNotFoundError(f"Artifact not found: {file_path}")

        data = full_path.read_bytes()
        mime_type, _ = mimetypes.guess_type(file_path)

        return ArtifactContent(
            data=data,
            mime_type=mime_type,
            size_bytes=len(data),
        )

    def delete(self, file_path: str) -> bool:
        """Delete artifact from local filesystem."""
        full_path = self._get_full_path(file_path)

        if not full_path.exists():
            return False

        # Delete the file
        full_path.unlink()

        # Try to clean up empty parent directories
        try:
            parent = full_path.parent
            if parent.exists() and not any(parent.iterdir()):
                parent.rmdir()
                # Also try grandparent (user_id directory)
                grandparent = parent.parent
                if grandparent.exists() and not any(grandparent.iterdir()):
                    grandparent.rmdir()
        except OSError:
            pass  # Ignore errors when cleaning up directories

        return True

    def exists(self, file_path: str) -> bool:
        """Check if artifact exists in local filesystem."""
        full_path = self._get_full_path(file_path)
        return full_path.exists()

    def get_download_url(self, file_path: str, expires_in_seconds: int = 3600) -> str:
        """Get download URL for local storage (API endpoint)."""
        # For local storage, return the API download endpoint
        # The actual file serving is handled by the API
        return f"/artifacts/download/{file_path}"


class GCSStorageBackend(StorageBackend):
    """Google Cloud Storage backend for production."""

    def __init__(self, bucket_name: str, prefix: str = "artifacts/"):
        self.bucket_name = bucket_name
        self.prefix = prefix
        self._client = None
        self._bucket = None

    @property
    def client(self):
        """Lazy initialization of GCS client."""
        if self._client is None:
            try:
                from google.cloud import storage
                self._client = storage.Client()
            except ImportError:
                raise ImportError(
                    "google-cloud-storage is required for GCS backend. "
                    "Install with: pip install google-cloud-storage"
                )
        return self._client

    @property
    def bucket(self):
        """Get the GCS bucket."""
        if self._bucket is None:
            self._bucket = self.client.bucket(self.bucket_name)
        return self._bucket

    def _get_blob_path(self, file_path: str) -> str:
        """Get full blob path with prefix."""
        return f"{self.prefix}{file_path}"

    def save(
        self,
        user_id: str,
        artifact_id: str,
        filename: str,
        content: bytes | BinaryIO,
    ) -> StoredArtifact:
        """Save artifact to GCS."""
        # Get content as bytes
        if isinstance(content, bytes):
            data = content
        else:
            data = content.read()

        # Calculate hash
        content_hash = hashlib.sha256(data).hexdigest()

        # Determine mime type
        mime_type, _ = mimetypes.guess_type(filename)

        # Create blob path
        relative_path = f"{user_id}/{artifact_id}/{filename}"
        blob_path = self._get_blob_path(relative_path)

        # Upload to GCS
        blob = self.bucket.blob(blob_path)
        blob.upload_from_string(
            data,
            content_type=mime_type or "application/octet-stream",
        )

        return StoredArtifact(
            file_path=relative_path,
            size_bytes=len(data),
            content_hash=content_hash,
            mime_type=mime_type,
        )

    def get(self, file_path: str) -> ArtifactContent:
        """Retrieve artifact from GCS."""
        blob_path = self._get_blob_path(file_path)
        blob = self.bucket.blob(blob_path)

        if not blob.exists():
            raise FileNotFoundError(f"Artifact not found: {file_path}")

        data = blob.download_as_bytes()
        mime_type, _ = mimetypes.guess_type(file_path)

        return ArtifactContent(
            data=data,
            mime_type=blob.content_type or mime_type,
            size_bytes=len(data),
        )

    def delete(self, file_path: str) -> bool:
        """Delete artifact from GCS."""
        blob_path = self._get_blob_path(file_path)
        blob = self.bucket.blob(blob_path)

        if not blob.exists():
            return False

        blob.delete()
        return True

    def exists(self, file_path: str) -> bool:
        """Check if artifact exists in GCS."""
        blob_path = self._get_blob_path(file_path)
        blob = self.bucket.blob(blob_path)
        return blob.exists()

    def get_download_url(self, file_path: str, expires_in_seconds: int = 3600) -> str:
        """Get a signed URL for downloading from GCS."""
        from datetime import timedelta

        blob_path = self._get_blob_path(file_path)
        blob = self.bucket.blob(blob_path)

        url = blob.generate_signed_url(
            version="v4",
            expiration=timedelta(seconds=expires_in_seconds),
            method="GET",
        )
        return url


class ArtifactService:
    """
    Main artifact service that handles artifact operations.

    Automatically selects storage backend based on environment:
    - local: LocalStorageBackend (filesystem)
    - production: GCSStorageBackend (Google Cloud Storage)
    """

    def __init__(self, storage_backend: Optional[StorageBackend] = None):
        """
        Initialize artifact service.

        Args:
            storage_backend: Optional storage backend. If not provided,
                           auto-selects based on environment settings.
        """
        self.settings = get_settings()

        if storage_backend:
            self.storage = storage_backend
        else:
            self.storage = self._create_storage_backend()

    def _create_storage_backend(self) -> StorageBackend:
        """Create storage backend based on environment."""
        if self.settings.environment == "production" and self.settings.gcs_bucket_name:
            return GCSStorageBackend(
                bucket_name=self.settings.gcs_bucket_name,
                prefix=self.settings.gcs_artifact_prefix,
            )
        else:
            return LocalStorageBackend(
                base_path=self.settings.artifact_storage_dir,
            )

    def validate_file_size(self, size_bytes: int) -> bool:
        """Check if file size is within limits."""
        return size_bytes <= self.settings.artifact_max_size_bytes

    def get_expiration_date(self, days: Optional[int] = None) -> datetime:
        """Calculate expiration date for artifact."""
        retention_days = days or self.settings.artifact_retention_days
        return datetime.now(timezone.utc) + timedelta(days=retention_days)

    def save_artifact(
        self,
        user_id: str,
        artifact_id: str,
        filename: str,
        content: bytes | BinaryIO,
    ) -> StoredArtifact:
        """
        Save an artifact to storage.

        Args:
            user_id: User ID (for directory organization)
            artifact_id: Unique artifact ID
            filename: Original filename
            content: File content as bytes or file-like object

        Returns:
            StoredArtifact with storage details

        Raises:
            ValueError: If file exceeds size limit
        """
        # Get content size
        if isinstance(content, bytes):
            size = len(content)
        else:
            # Seek to end to get size, then back to start
            content.seek(0, 2)
            size = content.tell()
            content.seek(0)

        # Validate size
        if not self.validate_file_size(size):
            max_mb = self.settings.artifact_max_size_mb
            raise ValueError(f"File exceeds maximum size of {max_mb}MB")

        return self.storage.save(user_id, artifact_id, filename, content)

    def get_artifact(self, file_path: str) -> ArtifactContent:
        """
        Retrieve an artifact from storage.

        Args:
            file_path: Relative file path (from DB)

        Returns:
            ArtifactContent with data and metadata

        Raises:
            FileNotFoundError: If artifact doesn't exist
        """
        return self.storage.get(file_path)

    def delete_artifact(self, file_path: str) -> bool:
        """
        Delete an artifact from storage.

        Args:
            file_path: Relative file path (from DB)

        Returns:
            True if deleted, False if not found
        """
        return self.storage.delete(file_path)

    def artifact_exists(self, file_path: str) -> bool:
        """
        Check if an artifact exists.

        Args:
            file_path: Relative file path (from DB)

        Returns:
            True if exists, False otherwise
        """
        return self.storage.exists(file_path)

    def get_download_url(
        self,
        file_path: str,
        expires_in_seconds: int = 3600,
    ) -> str:
        """
        Get a URL for downloading an artifact.

        Args:
            file_path: Relative file path (from DB)
            expires_in_seconds: URL expiration time (for signed URLs)

        Returns:
            Download URL
        """
        return self.storage.get_download_url(file_path, expires_in_seconds)

    def save_generated_code(
        self,
        user_id: str,
        artifact_id: str,
        code: str,
        filename: str,
        language: str,
    ) -> StoredArtifact:
        """
        Save generated code as an artifact.

        Args:
            user_id: User ID
            artifact_id: Unique artifact ID
            code: Generated code content
            filename: Filename for the code
            language: Programming language

        Returns:
            StoredArtifact with storage details
        """
        content = code.encode("utf-8")
        return self.save_artifact(user_id, artifact_id, filename, content)

    def save_multiple_files(
        self,
        user_id: str,
        artifact_id: str,
        files: dict[str, str | bytes],
    ) -> list[StoredArtifact]:
        """
        Save multiple files as artifacts.

        Args:
            user_id: User ID
            artifact_id: Shared artifact ID for the bundle
            files: Dict mapping filename to content (str or bytes)

        Returns:
            List of StoredArtifact objects
        """
        results = []
        for filename, content in files.items():
            if isinstance(content, str):
                content = content.encode("utf-8")
            result = self.save_artifact(user_id, artifact_id, filename, content)
            results.append(result)
        return results


# Singleton instance
_artifact_service: Optional[ArtifactService] = None


def get_artifact_service() -> ArtifactService:
    """Get the global artifact service instance."""
    global _artifact_service
    if _artifact_service is None:
        _artifact_service = ArtifactService()
    return _artifact_service
