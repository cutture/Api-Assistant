"""
Artifacts API Router for Intelligent Coding Agent.

Provides endpoints for:
- Uploading artifacts (code, specs, context files)
- Listing user artifacts
- Downloading artifacts
- Deleting artifacts
"""

import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from src.api.auth import get_current_user_optional
from src.database.connection import get_db
from src.database.models import Artifact, ArtifactType, User
from src.services.artifact_service import ArtifactService, get_artifact_service


router = APIRouter(prefix="/artifacts", tags=["artifacts"])


# =============================================================================
# Request/Response Models
# =============================================================================


class ArtifactResponse(BaseModel):
    """Response model for artifact data."""
    id: str
    name: str
    type: str
    mime_type: Optional[str]
    size_bytes: Optional[int]
    language: Optional[str]
    download_url: str
    created_at: str
    expires_at: Optional[str]

    class Config:
        from_attributes = True


class ArtifactListResponse(BaseModel):
    """Response model for artifact list."""
    artifacts: list[ArtifactResponse]
    total: int
    page: int
    limit: int


class UploadResponse(BaseModel):
    """Response model for artifact upload."""
    artifact_id: str
    name: str
    type: str
    size_bytes: int
    chromadb_indexed: bool


class DeleteResponse(BaseModel):
    """Response model for artifact deletion."""
    success: bool
    artifact_id: str
    message: str


# =============================================================================
# Helper Functions
# =============================================================================


def artifact_to_response(
    artifact: Artifact,
    artifact_service: ArtifactService,
) -> ArtifactResponse:
    """Convert Artifact model to response."""
    return ArtifactResponse(
        id=artifact.id,
        name=artifact.name,
        type=artifact.type,
        mime_type=artifact.mime_type,
        size_bytes=artifact.size_bytes,
        language=artifact.language,
        download_url=artifact_service.get_download_url(artifact.file_path),
        created_at=artifact.created_at.isoformat() if artifact.created_at else "",
        expires_at=artifact.expires_at.isoformat() if artifact.expires_at else None,
    )


def detect_language(filename: str, mime_type: Optional[str] = None) -> Optional[str]:
    """Detect programming language from filename or mime type."""
    ext_to_lang = {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".jsx": "javascript",
        ".tsx": "typescript",
        ".java": "java",
        ".go": "go",
        ".cs": "csharp",
        ".rs": "rust",
        ".rb": "ruby",
        ".php": "php",
        ".c": "c",
        ".cpp": "cpp",
        ".h": "c",
        ".hpp": "cpp",
    }

    # Try extension first
    for ext, lang in ext_to_lang.items():
        if filename.lower().endswith(ext):
            return lang

    return None


# =============================================================================
# Endpoints
# =============================================================================


@router.post("/upload", response_model=UploadResponse)
async def upload_artifact(
    file: UploadFile = File(...),
    artifact_type: str = Form(default="uploaded"),
    session_id: Optional[str] = Form(default=None),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
    artifact_service: ArtifactService = Depends(get_artifact_service),
):
    """
    Upload an artifact (code, spec, or context file).

    - **file**: The file to upload
    - **artifact_type**: Type of artifact (uploaded, generated, output, screenshot, preview)
    - **session_id**: Optional session ID to associate with
    """
    # Validate artifact type
    valid_types = [t.value for t in ArtifactType]
    if artifact_type not in valid_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid artifact type. Must be one of: {valid_types}",
        )

    # Read file content
    content = await file.read()

    # Generate IDs
    artifact_id = str(uuid.uuid4())
    user_id = current_user.id if current_user else "anonymous"

    try:
        # Save to storage
        stored = artifact_service.save_artifact(
            user_id=user_id,
            artifact_id=artifact_id,
            filename=file.filename or "unnamed",
            content=content,
        )
    except ValueError as e:
        raise HTTPException(status_code=413, detail=str(e))

    # Detect language for code files
    language = detect_language(file.filename or "", file.content_type)

    # Create database record
    artifact = Artifact(
        id=artifact_id,
        user_id=current_user.id if current_user else None,
        session_id=session_id,
        name=file.filename or "unnamed",
        type=artifact_type,
        mime_type=stored.mime_type,
        file_path=stored.file_path,
        size_bytes=stored.size_bytes,
        language=language,
        metadata_json={
            "content_hash": stored.content_hash,
            "original_filename": file.filename,
        },
        expires_at=artifact_service.get_expiration_date(),
    )

    db.add(artifact)
    db.commit()
    db.refresh(artifact)

    # TODO: Index in ChromaDB for semantic search (Phase 3)
    chromadb_indexed = False

    return UploadResponse(
        artifact_id=artifact.id,
        name=artifact.name,
        type=artifact.type,
        size_bytes=stored.size_bytes,
        chromadb_indexed=chromadb_indexed,
    )


@router.get("", response_model=ArtifactListResponse)
async def list_artifacts(
    session_id: Optional[str] = Query(default=None),
    artifact_type: Optional[str] = Query(default=None),
    language: Optional[str] = Query(default=None),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
    artifact_service: ArtifactService = Depends(get_artifact_service),
):
    """
    List user's artifacts with optional filtering.

    - **session_id**: Filter by session
    - **artifact_type**: Filter by type (uploaded, generated, etc.)
    - **language**: Filter by programming language
    - **page**: Page number (1-indexed)
    - **limit**: Items per page (max 100)
    """
    # Build query
    query = select(Artifact)

    # Filter by user if authenticated
    if current_user:
        query = query.where(Artifact.user_id == current_user.id)
    else:
        # Anonymous users can only see their session's artifacts
        if session_id:
            query = query.where(Artifact.session_id == session_id)
        else:
            # No user and no session - return empty
            return ArtifactListResponse(
                artifacts=[],
                total=0,
                page=page,
                limit=limit,
            )

    # Apply filters
    if session_id:
        query = query.where(Artifact.session_id == session_id)
    if artifact_type:
        query = query.where(Artifact.type == artifact_type)
    if language:
        query = query.where(Artifact.language == language)

    # Get total count
    count_query = select(Artifact.id)
    if current_user:
        count_query = count_query.where(Artifact.user_id == current_user.id)
    if session_id:
        count_query = count_query.where(Artifact.session_id == session_id)
    if artifact_type:
        count_query = count_query.where(Artifact.type == artifact_type)
    if language:
        count_query = count_query.where(Artifact.language == language)

    total = len(db.execute(count_query).all())

    # Apply pagination and ordering
    offset = (page - 1) * limit
    query = query.order_by(desc(Artifact.created_at)).offset(offset).limit(limit)

    # Execute query
    artifacts = db.execute(query).scalars().all()

    return ArtifactListResponse(
        artifacts=[artifact_to_response(a, artifact_service) for a in artifacts],
        total=total,
        page=page,
        limit=limit,
    )


@router.get("/{artifact_id}", response_model=ArtifactResponse)
async def get_artifact(
    artifact_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
    artifact_service: ArtifactService = Depends(get_artifact_service),
):
    """
    Get artifact metadata by ID.
    """
    artifact = db.get(Artifact, artifact_id)

    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")

    # Check access permissions
    if current_user:
        if artifact.user_id and artifact.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
    else:
        # Anonymous users need session match
        if artifact.user_id:
            raise HTTPException(status_code=403, detail="Access denied")

    return artifact_to_response(artifact, artifact_service)


@router.get("/{artifact_id}/download")
async def download_artifact(
    artifact_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
    artifact_service: ArtifactService = Depends(get_artifact_service),
):
    """
    Download artifact file.
    """
    artifact = db.get(Artifact, artifact_id)

    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")

    # Check access permissions
    if current_user:
        if artifact.user_id and artifact.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
    else:
        if artifact.user_id:
            raise HTTPException(status_code=403, detail="Access denied")

    try:
        content = artifact_service.get_artifact(artifact.file_path)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Artifact file not found")

    return Response(
        content=content.data,
        media_type=content.mime_type or "application/octet-stream",
        headers={
            "Content-Disposition": f'attachment; filename="{artifact.name}"',
            "Content-Length": str(content.size_bytes),
        },
    )


@router.delete("/{artifact_id}", response_model=DeleteResponse)
async def delete_artifact(
    artifact_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
    artifact_service: ArtifactService = Depends(get_artifact_service),
):
    """
    Delete an artifact.

    Also removes from ChromaDB if indexed.
    """
    artifact = db.get(Artifact, artifact_id)

    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")

    # Check ownership
    if current_user:
        if artifact.user_id and artifact.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
    else:
        if artifact.user_id:
            raise HTTPException(status_code=403, detail="Access denied")

    # Delete from storage
    artifact_service.delete_artifact(artifact.file_path)

    # TODO: Remove from ChromaDB if indexed
    if artifact.chromadb_ids:
        pass  # Will be implemented in ChromaDB indexing phase

    # Delete from database
    db.delete(artifact)
    db.commit()

    return DeleteResponse(
        success=True,
        artifact_id=artifact_id,
        message="Artifact deleted successfully",
    )


# =============================================================================
# Download by path (for local storage URLs)
# =============================================================================


@router.get("/download/{file_path:path}")
async def download_by_path(
    file_path: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
    artifact_service: ArtifactService = Depends(get_artifact_service),
):
    """
    Download artifact by file path (for local storage URLs).

    This endpoint is used when storage returns relative paths
    instead of signed URLs.
    """
    # Find artifact by file path
    query = select(Artifact).where(Artifact.file_path == file_path)
    artifact = db.execute(query).scalar_one_or_none()

    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")

    # Check access permissions
    if current_user:
        if artifact.user_id and artifact.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
    else:
        if artifact.user_id:
            raise HTTPException(status_code=403, detail="Access denied")

    try:
        content = artifact_service.get_artifact(file_path)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Artifact file not found")

    return Response(
        content=content.data,
        media_type=content.mime_type or "application/octet-stream",
        headers={
            "Content-Disposition": f'attachment; filename="{artifact.name}"',
            "Content-Length": str(content.size_bytes),
        },
    )
