"""
Git Provider API Router for GitLab and Bitbucket integration.

Provides unified endpoints for:
- OAuth authentication for GitLab/Bitbucket
- Repository operations
- Branch and file management
- Pull/Merge request creation
- Conflict detection
"""

import secrets
import structlog
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field

from src.api.auth import get_current_user, CurrentUser
from src.config import get_settings
from src.services.git_provider import (
    GitProvider,
    GitProviderType,
    GitUser,
    GitRepository,
    GitBranch,
    GitPullRequest,
    GitConflict,
    get_git_provider,
    GitLabProvider,
    BitbucketProvider,
)

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/git", tags=["git-providers"])

# In-memory storage for OAuth state and tokens
# In production, use Redis or database
_oauth_states: dict[str, dict] = {}
_user_tokens: dict[str, dict[str, dict]] = {}  # user_id -> provider -> {access_token, ...}


# ============ Request/Response Models ============

class ProviderInfo(BaseModel):
    type: str
    name: str
    connected: bool
    username: Optional[str] = None


class RepositoryResponse(BaseModel):
    id: str
    name: str
    full_name: str
    description: Optional[str]
    default_branch: str
    private: bool
    clone_url: str
    web_url: str
    provider: str


class BranchResponse(BaseModel):
    name: str
    sha: str
    protected: bool


class CreateBranchRequest(BaseModel):
    branch_name: str = Field(..., min_length=1, max_length=100)
    from_ref: str


class CreateFileRequest(BaseModel):
    path: str
    content: str
    message: str
    branch: str
    sha: Optional[str] = None


class CreatePRRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    body: str = Field(default="")
    source_branch: str
    target_branch: str
    draft: bool = False


class PullRequestResponse(BaseModel):
    id: int
    number: int
    title: str
    description: Optional[str]
    state: str
    source_branch: str
    target_branch: str
    web_url: str
    created_at: str
    author: str


class ConflictResponse(BaseModel):
    file_path: str
    conflict_type: str
    details: Optional[str]


class ConflictCheckRequest(BaseModel):
    source_branch: str
    target_branch: str


# ============ Helper Functions ============

def get_user_token(user_id: str, provider: GitProviderType) -> Optional[str]:
    """Get stored access token for a user and provider."""
    user_tokens = _user_tokens.get(user_id, {})
    provider_data = user_tokens.get(provider.value, {})
    return provider_data.get("access_token")


def store_user_token(user_id: str, provider: GitProviderType, token_data: dict):
    """Store access token for a user and provider."""
    if user_id not in _user_tokens:
        _user_tokens[user_id] = {}
    _user_tokens[user_id][provider.value] = token_data


def remove_user_token(user_id: str, provider: GitProviderType):
    """Remove stored access token."""
    if user_id in _user_tokens and provider.value in _user_tokens[user_id]:
        del _user_tokens[user_id][provider.value]


# ============ Provider Info Endpoints ============

@router.get("/providers", response_model=List[ProviderInfo])
async def list_providers(
    current_user: CurrentUser = Depends(get_current_user),
):
    """List available Git providers and connection status."""
    providers = []
    settings = get_settings()

    # GitLab
    gitlab_connected = bool(get_user_token(current_user.user_id, GitProviderType.GITLAB))
    gitlab_username = None
    if gitlab_connected:
        try:
            provider = GitLabProvider()
            token = get_user_token(current_user.user_id, GitProviderType.GITLAB)
            user = await provider.get_user(token)
            gitlab_username = user.username
        except Exception:
            pass

    providers.append(ProviderInfo(
        type=GitProviderType.GITLAB.value,
        name="GitLab",
        connected=gitlab_connected,
        username=gitlab_username,
    ))

    # Bitbucket
    bitbucket_connected = bool(get_user_token(current_user.user_id, GitProviderType.BITBUCKET))
    bitbucket_username = None
    if bitbucket_connected:
        try:
            provider = BitbucketProvider()
            token = get_user_token(current_user.user_id, GitProviderType.BITBUCKET)
            user = await provider.get_user(token)
            bitbucket_username = user.username
        except Exception:
            pass

    providers.append(ProviderInfo(
        type=GitProviderType.BITBUCKET.value,
        name="Bitbucket",
        connected=bitbucket_connected,
        username=bitbucket_username,
    ))

    return providers


# ============ OAuth Endpoints ============

@router.get("/{provider}/connect")
async def connect_provider(
    provider: str,
    current_user: CurrentUser = Depends(get_current_user),
):
    """Initiate OAuth flow for a Git provider."""
    try:
        provider_type = GitProviderType(provider)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Unknown provider: {provider}")

    settings = get_settings()
    git_provider = get_git_provider(provider_type)

    state = secrets.token_urlsafe(32)
    _oauth_states[state] = {
        "user_id": current_user.user_id,
        "provider": provider_type.value,
    }

    # Determine redirect URI
    redirect_uri = f"{settings.api_base_url}/git/{provider}/callback"

    auth_url = git_provider.get_auth_url(state, redirect_uri)
    return RedirectResponse(url=auth_url)


@router.get("/{provider}/callback")
async def oauth_callback(
    provider: str,
    code: str,
    state: str,
):
    """Handle OAuth callback from Git provider."""
    try:
        provider_type = GitProviderType(provider)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Unknown provider: {provider}")

    # Verify state
    state_data = _oauth_states.pop(state, None)
    if not state_data:
        raise HTTPException(status_code=400, detail="Invalid or expired state")

    if state_data["provider"] != provider:
        raise HTTPException(status_code=400, detail="Provider mismatch")

    user_id = state_data["user_id"]
    settings = get_settings()
    git_provider = get_git_provider(provider_type)
    redirect_uri = f"{settings.api_base_url}/git/{provider}/callback"

    try:
        token_data = await git_provider.exchange_code(code, redirect_uri)
        store_user_token(user_id, provider_type, token_data)

        # Redirect to frontend success page
        frontend_url = settings.cors_origins[0] if settings.cors_origins else "http://localhost:3000"
        return RedirectResponse(url=f"{frontend_url}/settings/git?connected={provider}")

    except Exception as e:
        logger.error(f"{provider} OAuth failed", error=str(e))
        frontend_url = settings.cors_origins[0] if settings.cors_origins else "http://localhost:3000"
        return RedirectResponse(url=f"{frontend_url}/settings/git?error=oauth_failed")


@router.get("/{provider}/status")
async def get_connection_status(
    provider: str,
    current_user: CurrentUser = Depends(get_current_user),
):
    """Get connection status for a Git provider."""
    try:
        provider_type = GitProviderType(provider)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Unknown provider: {provider}")

    token = get_user_token(current_user.user_id, provider_type)
    if not token:
        return {"connected": False}

    try:
        git_provider = get_git_provider(provider_type)
        user = await git_provider.get_user(token)
        return {
            "connected": True,
            "username": user.username,
            "email": user.email,
            "display_name": user.display_name,
        }
    except Exception:
        return {"connected": False}


@router.delete("/{provider}/disconnect")
async def disconnect_provider(
    provider: str,
    current_user: CurrentUser = Depends(get_current_user),
):
    """Disconnect a Git provider."""
    try:
        provider_type = GitProviderType(provider)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Unknown provider: {provider}")

    remove_user_token(current_user.user_id, provider_type)
    return {"message": f"Disconnected from {provider}"}


# ============ Repository Endpoints ============

@router.get("/{provider}/repos", response_model=List[RepositoryResponse])
async def list_repositories(
    provider: str,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=30, ge=1, le=100),
    current_user: CurrentUser = Depends(get_current_user),
):
    """List repositories for a Git provider."""
    try:
        provider_type = GitProviderType(provider)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Unknown provider: {provider}")

    token = get_user_token(current_user.user_id, provider_type)
    if not token:
        raise HTTPException(status_code=401, detail=f"Not connected to {provider}")

    git_provider = get_git_provider(provider_type)
    repos = await git_provider.list_repositories(token, page, per_page)

    return [
        RepositoryResponse(
            id=r.id,
            name=r.name,
            full_name=r.full_name,
            description=r.description,
            default_branch=r.default_branch,
            private=r.private,
            clone_url=r.clone_url,
            web_url=r.web_url,
            provider=r.provider.value,
        )
        for r in repos
    ]


@router.get("/{provider}/repos/{owner}/{repo}", response_model=RepositoryResponse)
async def get_repository(
    provider: str,
    owner: str,
    repo: str,
    current_user: CurrentUser = Depends(get_current_user),
):
    """Get repository details."""
    try:
        provider_type = GitProviderType(provider)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Unknown provider: {provider}")

    token = get_user_token(current_user.user_id, provider_type)
    if not token:
        raise HTTPException(status_code=401, detail=f"Not connected to {provider}")

    git_provider = get_git_provider(provider_type)
    repository = await git_provider.get_repository(token, owner, repo)

    if not repository:
        raise HTTPException(status_code=404, detail="Repository not found")

    return RepositoryResponse(
        id=repository.id,
        name=repository.name,
        full_name=repository.full_name,
        description=repository.description,
        default_branch=repository.default_branch,
        private=repository.private,
        clone_url=repository.clone_url,
        web_url=repository.web_url,
        provider=repository.provider.value,
    )


# ============ Branch Endpoints ============

@router.get("/{provider}/repos/{owner}/{repo}/branches", response_model=List[BranchResponse])
async def list_branches(
    provider: str,
    owner: str,
    repo: str,
    current_user: CurrentUser = Depends(get_current_user),
):
    """List repository branches."""
    try:
        provider_type = GitProviderType(provider)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Unknown provider: {provider}")

    token = get_user_token(current_user.user_id, provider_type)
    if not token:
        raise HTTPException(status_code=401, detail=f"Not connected to {provider}")

    git_provider = get_git_provider(provider_type)
    branches = await git_provider.list_branches(token, owner, repo)

    return [
        BranchResponse(name=b.name, sha=b.sha, protected=b.protected)
        for b in branches
    ]


@router.post("/{provider}/repos/{owner}/{repo}/branches", response_model=BranchResponse)
async def create_branch(
    provider: str,
    owner: str,
    repo: str,
    request: CreateBranchRequest,
    current_user: CurrentUser = Depends(get_current_user),
):
    """Create a new branch."""
    try:
        provider_type = GitProviderType(provider)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Unknown provider: {provider}")

    token = get_user_token(current_user.user_id, provider_type)
    if not token:
        raise HTTPException(status_code=401, detail=f"Not connected to {provider}")

    git_provider = get_git_provider(provider_type)
    branch = await git_provider.create_branch(
        token, owner, repo, request.branch_name, request.from_ref
    )

    if not branch:
        raise HTTPException(status_code=400, detail="Failed to create branch")

    return BranchResponse(name=branch.name, sha=branch.sha, protected=branch.protected)


# ============ File Endpoints ============

@router.get("/{provider}/repos/{owner}/{repo}/file")
async def get_file(
    provider: str,
    owner: str,
    repo: str,
    path: str,
    ref: Optional[str] = None,
    current_user: CurrentUser = Depends(get_current_user),
):
    """Get file content from repository."""
    try:
        provider_type = GitProviderType(provider)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Unknown provider: {provider}")

    token = get_user_token(current_user.user_id, provider_type)
    if not token:
        raise HTTPException(status_code=401, detail=f"Not connected to {provider}")

    git_provider = get_git_provider(provider_type)
    file = await git_provider.get_file(token, owner, repo, path, ref)

    if not file:
        raise HTTPException(status_code=404, detail="File not found")

    return {
        "path": file.path,
        "content": file.content,
        "sha": file.sha,
        "encoding": file.encoding,
    }


@router.post("/{provider}/repos/{owner}/{repo}/file")
async def create_or_update_file(
    provider: str,
    owner: str,
    repo: str,
    request: CreateFileRequest,
    current_user: CurrentUser = Depends(get_current_user),
):
    """Create or update a file in repository."""
    try:
        provider_type = GitProviderType(provider)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Unknown provider: {provider}")

    token = get_user_token(current_user.user_id, provider_type)
    if not token:
        raise HTTPException(status_code=401, detail=f"Not connected to {provider}")

    git_provider = get_git_provider(provider_type)
    result = await git_provider.create_or_update_file(
        token, owner, repo,
        request.path, request.content, request.message,
        request.branch, request.sha
    )

    return {"message": "File saved successfully", "result": result}


# ============ Pull Request Endpoints ============

@router.post("/{provider}/repos/{owner}/{repo}/pulls", response_model=PullRequestResponse)
async def create_pull_request(
    provider: str,
    owner: str,
    repo: str,
    request: CreatePRRequest,
    current_user: CurrentUser = Depends(get_current_user),
):
    """Create a pull/merge request."""
    try:
        provider_type = GitProviderType(provider)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Unknown provider: {provider}")

    token = get_user_token(current_user.user_id, provider_type)
    if not token:
        raise HTTPException(status_code=401, detail=f"Not connected to {provider}")

    git_provider = get_git_provider(provider_type)
    pr = await git_provider.create_pull_request(
        token, owner, repo,
        request.title, request.body,
        request.source_branch, request.target_branch,
        request.draft
    )

    if not pr:
        raise HTTPException(status_code=400, detail="Failed to create pull request")

    return PullRequestResponse(
        id=pr.id,
        number=pr.number,
        title=pr.title,
        description=pr.description,
        state=pr.state,
        source_branch=pr.source_branch,
        target_branch=pr.target_branch,
        web_url=pr.web_url,
        created_at=pr.created_at.isoformat(),
        author=pr.author,
    )


# ============ Conflict Detection Endpoint ============

@router.post("/{provider}/repos/{owner}/{repo}/conflicts", response_model=List[ConflictResponse])
async def check_conflicts(
    provider: str,
    owner: str,
    repo: str,
    request: ConflictCheckRequest,
    current_user: CurrentUser = Depends(get_current_user),
):
    """Check for merge conflicts between branches."""
    try:
        provider_type = GitProviderType(provider)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Unknown provider: {provider}")

    token = get_user_token(current_user.user_id, provider_type)
    if not token:
        raise HTTPException(status_code=401, detail=f"Not connected to {provider}")

    git_provider = get_git_provider(provider_type)
    conflicts = await git_provider.check_conflicts(
        token, owner, repo,
        request.source_branch, request.target_branch
    )

    return [
        ConflictResponse(
            file_path=c.file_path,
            conflict_type=c.conflict_type,
            details=c.details,
        )
        for c in conflicts
    ]
