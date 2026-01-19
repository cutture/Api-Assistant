"""
GitHub API Router.

Provides endpoints for GitHub OAuth connection and repository operations.
"""

import secrets
from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field
from typing import Optional

from src.api.auth import get_current_user_optional, CurrentUser
from src.services.github_service import get_github_service
from src.config import get_settings

router = APIRouter(prefix="/github", tags=["github"])

# Store OAuth states for CSRF protection (in production, use Redis/database)
_oauth_states: dict[str, str] = {}


# Request/Response Models

class GitHubConnectionStatus(BaseModel):
    """GitHub connection status response."""
    connected: bool
    username: Optional[str] = None
    avatar_url: Optional[str] = None
    scopes: list[str] = []
    connected_at: Optional[str] = None


class RepositoryResponse(BaseModel):
    """Repository information response."""
    id: int
    full_name: str
    name: str
    owner: str
    description: Optional[str]
    private: bool
    default_branch: str
    language: Optional[str]
    html_url: str
    size: int
    stargazers_count: int


class RepositoryListResponse(BaseModel):
    """List of repositories response."""
    repositories: list[RepositoryResponse]
    total: int
    page: int
    per_page: int


class RepositoryContextResponse(BaseModel):
    """Repository context analysis response."""
    repo_full_name: str
    default_branch: str
    languages: dict[str, int]
    primary_language: Optional[str]
    framework_detected: Optional[str]
    package_manager: Optional[str]
    structure_summary: str
    key_files: list[str]
    patterns: list[str]
    indexed_files: int
    last_analyzed_at: Optional[str]


class FileContentResponse(BaseModel):
    """File content response."""
    path: str
    name: str
    content: str
    size: int
    language: Optional[str]
    sha: str


class AuthorizationUrlResponse(BaseModel):
    """Authorization URL response."""
    authorization_url: str
    state: str


class DisconnectResponse(BaseModel):
    """Disconnect response."""
    success: bool
    message: str


# Helper functions

def _get_user_id(current_user: CurrentUser) -> str:
    """Get user ID from current user, requiring authentication."""
    if not current_user.is_authenticated:
        raise HTTPException(
            status_code=401,
            detail="Authentication required for GitHub integration"
        )
    return current_user.user_id


# Endpoints

@router.get("/connect", response_model=AuthorizationUrlResponse)
async def initiate_github_oauth(
    current_user: CurrentUser = Depends(get_current_user_optional),
):
    """
    Initiate GitHub OAuth flow.

    Returns an authorization URL to redirect the user to GitHub for authentication.
    The state parameter should be stored and verified in the callback.
    """
    user_id = _get_user_id(current_user)

    settings = get_settings()
    service = get_github_service()

    # Generate state for CSRF protection
    state = secrets.token_urlsafe(32)
    _oauth_states[state] = user_id

    # Build callback URL
    callback_url = getattr(settings, 'github_callback_url', None)
    if not callback_url:
        # Default to the API callback endpoint
        base_url = getattr(settings, 'api_base_url', 'http://localhost:8000')
        callback_url = f"{base_url}/github/callback"

    try:
        auth_url = service.get_authorization_url(callback_url, state)
        return AuthorizationUrlResponse(
            authorization_url=auth_url,
            state=state,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate authorization URL: {str(e)}"
        )


@router.get("/callback")
async def github_oauth_callback(
    code: str = Query(..., description="Authorization code from GitHub"),
    state: str = Query(..., description="State parameter for CSRF verification"),
):
    """
    GitHub OAuth callback endpoint.

    Exchanges the authorization code for an access token and stores the connection.
    Redirects to the frontend settings page on success.
    """
    # Verify state
    user_id = _oauth_states.pop(state, None)
    if not user_id:
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired state parameter"
        )

    settings = get_settings()
    service = get_github_service()

    # Build callback URL (must match the one used in authorization)
    callback_url = getattr(settings, 'github_callback_url', None)
    if not callback_url:
        base_url = getattr(settings, 'api_base_url', 'http://localhost:8000')
        callback_url = f"{base_url}/github/callback"

    try:
        connection = await service.authenticate(code, callback_url, user_id)

        # Redirect to frontend settings page with success
        frontend_url = getattr(settings, 'frontend_url', 'http://localhost:3000')
        return RedirectResponse(
            url=f"{frontend_url}/settings/github?connected=true&username={connection.github_username}",
            status_code=302,
        )
    except Exception as e:
        # Redirect with error
        frontend_url = getattr(settings, 'frontend_url', 'http://localhost:3000')
        return RedirectResponse(
            url=f"{frontend_url}/settings/github?error={str(e)}",
            status_code=302,
        )


@router.get("/status", response_model=GitHubConnectionStatus)
async def get_github_status(
    current_user: CurrentUser = Depends(get_current_user_optional),
):
    """
    Check GitHub connection status for the current user.

    Returns whether the user is connected, their GitHub username, and granted scopes.
    """
    user_id = _get_user_id(current_user)
    service = get_github_service()

    connection = service.get_connection(user_id)

    if connection:
        return GitHubConnectionStatus(
            connected=True,
            username=connection.github_username,
            avatar_url=connection.avatar_url,
            scopes=connection.scopes,
            connected_at=connection.connected_at.isoformat(),
        )
    else:
        return GitHubConnectionStatus(connected=False)


@router.delete("/disconnect", response_model=DisconnectResponse)
async def disconnect_github(
    current_user: CurrentUser = Depends(get_current_user_optional),
):
    """
    Disconnect GitHub for the current user.

    Removes the GitHub connection and clears any cached repository contexts.
    """
    user_id = _get_user_id(current_user)
    service = get_github_service()

    success = service.disconnect(user_id)

    if success:
        return DisconnectResponse(
            success=True,
            message="GitHub disconnected successfully"
        )
    else:
        return DisconnectResponse(
            success=False,
            message="No GitHub connection found"
        )


@router.get("/repos", response_model=RepositoryListResponse)
async def list_repositories(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(30, ge=1, le=100, description="Results per page"),
    current_user: CurrentUser = Depends(get_current_user_optional),
):
    """
    List user's accessible GitHub repositories.

    Returns repositories the user owns, collaborates on, or has access to through organizations.
    """
    user_id = _get_user_id(current_user)
    service = get_github_service()

    try:
        repos = await service.list_repos(user_id, page=page, per_page=per_page)

        return RepositoryListResponse(
            repositories=[
                RepositoryResponse(
                    id=r.id,
                    full_name=r.full_name,
                    name=r.name,
                    owner=r.owner,
                    description=r.description,
                    private=r.private,
                    default_branch=r.default_branch,
                    language=r.language,
                    html_url=r.html_url,
                    size=r.size,
                    stargazers_count=r.stargazers_count,
                )
                for r in repos
            ],
            total=len(repos),
            page=page,
            per_page=per_page,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list repositories: {str(e)}"
        )


@router.post("/repos/{owner}/{repo}/analyze", response_model=RepositoryContextResponse)
async def analyze_repository(
    owner: str,
    repo: str,
    current_user: CurrentUser = Depends(get_current_user_optional),
):
    """
    Analyze a repository and build context for code generation.

    Detects:
    - Programming languages used
    - Frameworks (React, FastAPI, Spring, etc.)
    - Package managers
    - Project structure
    - Key configuration files
    """
    user_id = _get_user_id(current_user)
    service = get_github_service()

    try:
        context = await service.analyze_repository(user_id, owner, repo)

        return RepositoryContextResponse(
            repo_full_name=context.repo_full_name,
            default_branch=context.default_branch,
            languages=context.languages,
            primary_language=context.primary_language,
            framework_detected=context.framework_detected,
            package_manager=context.package_manager,
            structure_summary=context.structure_summary,
            key_files=context.key_files,
            patterns=context.patterns,
            indexed_files=context.indexed_files,
            last_analyzed_at=context.last_analyzed_at.isoformat() if context.last_analyzed_at else None,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze repository: {str(e)}"
        )


@router.get("/repos/{owner}/{repo}/context", response_model=RepositoryContextResponse)
async def get_repository_context(
    owner: str,
    repo: str,
    current_user: CurrentUser = Depends(get_current_user_optional),
):
    """
    Get cached repository context.

    Returns the previously analyzed context for a repository.
    Use /analyze to refresh the context.
    """
    user_id = _get_user_id(current_user)
    service = get_github_service()

    full_name = f"{owner}/{repo}"
    context = service.get_cached_context(user_id, full_name)

    if not context:
        raise HTTPException(
            status_code=404,
            detail=f"No context found for {full_name}. Use /analyze first."
        )

    return RepositoryContextResponse(
        repo_full_name=context.repo_full_name,
        default_branch=context.default_branch,
        languages=context.languages,
        primary_language=context.primary_language,
        framework_detected=context.framework_detected,
        package_manager=context.package_manager,
        structure_summary=context.structure_summary,
        key_files=context.key_files,
        patterns=context.patterns,
        indexed_files=context.indexed_files,
        last_analyzed_at=context.last_analyzed_at.isoformat() if context.last_analyzed_at else None,
    )


@router.get("/repos/{owner}/{repo}/file", response_model=FileContentResponse)
async def get_file_content(
    owner: str,
    repo: str,
    path: str = Query(..., description="File path in repository"),
    current_user: CurrentUser = Depends(get_current_user_optional),
):
    """
    Get file content from a repository.

    Returns the raw content of a file along with metadata.
    """
    user_id = _get_user_id(current_user)
    service = get_github_service()

    try:
        file = await service.get_file_content(user_id, owner, repo, path)

        return FileContentResponse(
            path=file.path,
            name=file.name,
            content=file.content,
            size=file.size,
            language=file.language,
            sha=file.sha,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get file content: {str(e)}"
        )


@router.delete("/repos/{owner}/{repo}/context")
async def clear_repository_context(
    owner: str,
    repo: str,
    current_user: CurrentUser = Depends(get_current_user_optional),
):
    """
    Clear cached repository context.

    Removes the cached context for a repository, forcing re-analysis on next use.
    """
    user_id = _get_user_id(current_user)
    service = get_github_service()

    full_name = f"{owner}/{repo}"
    service.clear_context_cache(user_id, full_name)

    return {"success": True, "message": f"Context cleared for {full_name}"}
