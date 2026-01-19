"""
Unified Git Provider abstraction for GitHub, GitLab, and Bitbucket.

This module provides:
- Abstract GitProvider interface
- GitLab implementation
- Bitbucket implementation
- Provider factory
"""

import base64
import secrets
import structlog
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional, Any
from urllib.parse import urlencode

import httpx

from src.config import get_settings

logger = structlog.get_logger(__name__)


class GitProviderType(str, Enum):
    """Supported Git providers."""
    GITHUB = "github"
    GITLAB = "gitlab"
    BITBUCKET = "bitbucket"


@dataclass
class GitUser:
    """Git provider user info."""
    id: str
    username: str
    email: Optional[str]
    display_name: str
    avatar_url: Optional[str]
    provider: GitProviderType


@dataclass
class GitRepository:
    """Repository info from Git provider."""
    id: str
    name: str
    full_name: str
    description: Optional[str]
    default_branch: str
    private: bool
    clone_url: str
    web_url: str
    provider: GitProviderType


@dataclass
class GitBranch:
    """Branch info."""
    name: str
    sha: str
    protected: bool


@dataclass
class GitFile:
    """File content from repository."""
    path: str
    content: str
    sha: str
    encoding: str


@dataclass
class GitPullRequest:
    """Pull/Merge request info."""
    id: int
    number: int
    title: str
    description: Optional[str]
    state: str
    source_branch: str
    target_branch: str
    web_url: str
    created_at: datetime
    author: str


@dataclass
class GitConflict:
    """Merge conflict info."""
    file_path: str
    conflict_type: str  # 'content', 'deleted', 'renamed'
    details: Optional[str]


class GitProvider(ABC):
    """Abstract base class for Git providers."""

    @property
    @abstractmethod
    def provider_type(self) -> GitProviderType:
        """Get the provider type."""
        pass

    @abstractmethod
    def get_auth_url(self, state: str, redirect_uri: str) -> str:
        """Get OAuth authorization URL."""
        pass

    @abstractmethod
    async def exchange_code(self, code: str, redirect_uri: str) -> Dict[str, Any]:
        """Exchange authorization code for access token."""
        pass

    @abstractmethod
    async def get_user(self, access_token: str) -> GitUser:
        """Get authenticated user info."""
        pass

    @abstractmethod
    async def list_repositories(
        self,
        access_token: str,
        page: int = 1,
        per_page: int = 30,
    ) -> List[GitRepository]:
        """List user's repositories."""
        pass

    @abstractmethod
    async def get_repository(
        self,
        access_token: str,
        owner: str,
        repo: str,
    ) -> Optional[GitRepository]:
        """Get repository details."""
        pass

    @abstractmethod
    async def list_branches(
        self,
        access_token: str,
        owner: str,
        repo: str,
    ) -> List[GitBranch]:
        """List repository branches."""
        pass

    @abstractmethod
    async def get_file(
        self,
        access_token: str,
        owner: str,
        repo: str,
        path: str,
        ref: Optional[str] = None,
    ) -> Optional[GitFile]:
        """Get file content from repository."""
        pass

    @abstractmethod
    async def create_branch(
        self,
        access_token: str,
        owner: str,
        repo: str,
        branch_name: str,
        from_ref: str,
    ) -> Optional[GitBranch]:
        """Create a new branch."""
        pass

    @abstractmethod
    async def create_or_update_file(
        self,
        access_token: str,
        owner: str,
        repo: str,
        path: str,
        content: str,
        message: str,
        branch: str,
        sha: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create or update a file in repository."""
        pass

    @abstractmethod
    async def create_pull_request(
        self,
        access_token: str,
        owner: str,
        repo: str,
        title: str,
        body: str,
        source_branch: str,
        target_branch: str,
        draft: bool = False,
    ) -> Optional[GitPullRequest]:
        """Create a pull/merge request."""
        pass

    @abstractmethod
    async def check_conflicts(
        self,
        access_token: str,
        owner: str,
        repo: str,
        source_branch: str,
        target_branch: str,
    ) -> List[GitConflict]:
        """Check for merge conflicts between branches."""
        pass


class GitLabProvider(GitProvider):
    """GitLab implementation of GitProvider."""

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        base_url: str = "https://gitlab.com",
    ):
        settings = get_settings()
        self.client_id = client_id or getattr(settings, 'gitlab_client_id', '')
        self.client_secret = client_secret or getattr(settings, 'gitlab_client_secret', '')
        self.base_url = base_url.rstrip('/')
        self.api_url = f"{self.base_url}/api/v4"

    @property
    def provider_type(self) -> GitProviderType:
        return GitProviderType.GITLAB

    def get_auth_url(self, state: str, redirect_uri: str) -> str:
        params = {
            "client_id": self.client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "state": state,
            "scope": "read_user read_api read_repository write_repository api",
        }
        return f"{self.base_url}/oauth/authorize?{urlencode(params)}"

    async def exchange_code(self, code: str, redirect_uri: str) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/oauth/token",
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": redirect_uri,
                },
            )
            response.raise_for_status()
            return response.json()

    async def get_user(self, access_token: str) -> GitUser:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.api_url}/user",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            response.raise_for_status()
            data = response.json()

            return GitUser(
                id=str(data["id"]),
                username=data["username"],
                email=data.get("email"),
                display_name=data.get("name", data["username"]),
                avatar_url=data.get("avatar_url"),
                provider=GitProviderType.GITLAB,
            )

    async def list_repositories(
        self,
        access_token: str,
        page: int = 1,
        per_page: int = 30,
    ) -> List[GitRepository]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.api_url}/projects",
                headers={"Authorization": f"Bearer {access_token}"},
                params={
                    "membership": "true",
                    "page": page,
                    "per_page": per_page,
                    "order_by": "updated_at",
                    "sort": "desc",
                },
            )
            response.raise_for_status()

            repos = []
            for data in response.json():
                repos.append(GitRepository(
                    id=str(data["id"]),
                    name=data["name"],
                    full_name=data["path_with_namespace"],
                    description=data.get("description"),
                    default_branch=data.get("default_branch", "main"),
                    private=data.get("visibility") == "private",
                    clone_url=data.get("http_url_to_repo", ""),
                    web_url=data.get("web_url", ""),
                    provider=GitProviderType.GITLAB,
                ))
            return repos

    async def get_repository(
        self,
        access_token: str,
        owner: str,
        repo: str,
    ) -> Optional[GitRepository]:
        project_path = f"{owner}/{repo}".replace("/", "%2F")
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.api_url}/projects/{project_path}",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            if response.status_code == 404:
                return None
            response.raise_for_status()
            data = response.json()

            return GitRepository(
                id=str(data["id"]),
                name=data["name"],
                full_name=data["path_with_namespace"],
                description=data.get("description"),
                default_branch=data.get("default_branch", "main"),
                private=data.get("visibility") == "private",
                clone_url=data.get("http_url_to_repo", ""),
                web_url=data.get("web_url", ""),
                provider=GitProviderType.GITLAB,
            )

    async def list_branches(
        self,
        access_token: str,
        owner: str,
        repo: str,
    ) -> List[GitBranch]:
        project_path = f"{owner}/{repo}".replace("/", "%2F")
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.api_url}/projects/{project_path}/repository/branches",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            response.raise_for_status()

            branches = []
            for data in response.json():
                branches.append(GitBranch(
                    name=data["name"],
                    sha=data["commit"]["id"],
                    protected=data.get("protected", False),
                ))
            return branches

    async def get_file(
        self,
        access_token: str,
        owner: str,
        repo: str,
        path: str,
        ref: Optional[str] = None,
    ) -> Optional[GitFile]:
        project_path = f"{owner}/{repo}".replace("/", "%2F")
        file_path = path.replace("/", "%2F")
        params = {"ref": ref} if ref else {}

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.api_url}/projects/{project_path}/repository/files/{file_path}",
                headers={"Authorization": f"Bearer {access_token}"},
                params=params,
            )
            if response.status_code == 404:
                return None
            response.raise_for_status()
            data = response.json()

            content = data.get("content", "")
            if data.get("encoding") == "base64":
                content = base64.b64decode(content).decode("utf-8")

            return GitFile(
                path=data["file_path"],
                content=content,
                sha=data.get("blob_id", ""),
                encoding=data.get("encoding", "base64"),
            )

    async def create_branch(
        self,
        access_token: str,
        owner: str,
        repo: str,
        branch_name: str,
        from_ref: str,
    ) -> Optional[GitBranch]:
        project_path = f"{owner}/{repo}".replace("/", "%2F")
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_url}/projects/{project_path}/repository/branches",
                headers={"Authorization": f"Bearer {access_token}"},
                json={
                    "branch": branch_name,
                    "ref": from_ref,
                },
            )
            if response.status_code in [400, 409]:  # Already exists
                return None
            response.raise_for_status()
            data = response.json()

            return GitBranch(
                name=data["name"],
                sha=data["commit"]["id"],
                protected=data.get("protected", False),
            )

    async def create_or_update_file(
        self,
        access_token: str,
        owner: str,
        repo: str,
        path: str,
        content: str,
        message: str,
        branch: str,
        sha: Optional[str] = None,
    ) -> Dict[str, Any]:
        project_path = f"{owner}/{repo}".replace("/", "%2F")
        file_path = path.replace("/", "%2F")

        # Check if file exists
        existing = await self.get_file(access_token, owner, repo, path, branch)
        method = "PUT" if existing else "POST"

        async with httpx.AsyncClient() as client:
            response = await client.request(
                method,
                f"{self.api_url}/projects/{project_path}/repository/files/{file_path}",
                headers={"Authorization": f"Bearer {access_token}"},
                json={
                    "branch": branch,
                    "content": content,
                    "commit_message": message,
                },
            )
            response.raise_for_status()
            return response.json()

    async def create_pull_request(
        self,
        access_token: str,
        owner: str,
        repo: str,
        title: str,
        body: str,
        source_branch: str,
        target_branch: str,
        draft: bool = False,
    ) -> Optional[GitPullRequest]:
        project_path = f"{owner}/{repo}".replace("/", "%2F")
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_url}/projects/{project_path}/merge_requests",
                headers={"Authorization": f"Bearer {access_token}"},
                json={
                    "source_branch": source_branch,
                    "target_branch": target_branch,
                    "title": f"Draft: {title}" if draft else title,
                    "description": body,
                },
            )
            response.raise_for_status()
            data = response.json()

            return GitPullRequest(
                id=data["id"],
                number=data["iid"],
                title=data["title"],
                description=data.get("description"),
                state=data["state"],
                source_branch=data["source_branch"],
                target_branch=data["target_branch"],
                web_url=data["web_url"],
                created_at=datetime.fromisoformat(data["created_at"].replace("Z", "+00:00")),
                author=data["author"]["username"],
            )

    async def check_conflicts(
        self,
        access_token: str,
        owner: str,
        repo: str,
        source_branch: str,
        target_branch: str,
    ) -> List[GitConflict]:
        """Check for merge conflicts using GitLab's compare API."""
        project_path = f"{owner}/{repo}".replace("/", "%2F")
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.api_url}/projects/{project_path}/repository/compare",
                headers={"Authorization": f"Bearer {access_token}"},
                params={
                    "from": target_branch,
                    "to": source_branch,
                },
            )
            response.raise_for_status()
            data = response.json()

            conflicts = []
            # GitLab compare doesn't directly show conflicts, but we can detect
            # if there are changes that might conflict
            for diff in data.get("diffs", []):
                if diff.get("renamed_file") or diff.get("deleted_file"):
                    conflicts.append(GitConflict(
                        file_path=diff.get("new_path") or diff.get("old_path"),
                        conflict_type="renamed" if diff.get("renamed_file") else "deleted",
                        details=None,
                    ))

            return conflicts


class BitbucketProvider(GitProvider):
    """Bitbucket implementation of GitProvider."""

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
    ):
        settings = get_settings()
        self.client_id = client_id or getattr(settings, 'bitbucket_client_id', '')
        self.client_secret = client_secret or getattr(settings, 'bitbucket_client_secret', '')
        self.base_url = "https://bitbucket.org"
        self.api_url = "https://api.bitbucket.org/2.0"

    @property
    def provider_type(self) -> GitProviderType:
        return GitProviderType.BITBUCKET

    def get_auth_url(self, state: str, redirect_uri: str) -> str:
        params = {
            "client_id": self.client_id,
            "response_type": "code",
            "state": state,
        }
        return f"{self.base_url}/site/oauth2/authorize?{urlencode(params)}"

    async def exchange_code(self, code: str, redirect_uri: str) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/site/oauth2/access_token",
                auth=(self.client_id, self.client_secret),
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                },
            )
            response.raise_for_status()
            return response.json()

    async def get_user(self, access_token: str) -> GitUser:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.api_url}/user",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            response.raise_for_status()
            data = response.json()

            # Get email separately
            email = None
            email_response = await client.get(
                f"{self.api_url}/user/emails",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            if email_response.status_code == 200:
                emails = email_response.json().get("values", [])
                primary = next((e for e in emails if e.get("is_primary")), None)
                if primary:
                    email = primary.get("email")

            return GitUser(
                id=data["uuid"],
                username=data["username"],
                email=email,
                display_name=data.get("display_name", data["username"]),
                avatar_url=data.get("links", {}).get("avatar", {}).get("href"),
                provider=GitProviderType.BITBUCKET,
            )

    async def list_repositories(
        self,
        access_token: str,
        page: int = 1,
        per_page: int = 30,
    ) -> List[GitRepository]:
        async with httpx.AsyncClient() as client:
            # Get user first
            user_response = await client.get(
                f"{self.api_url}/user",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            user_response.raise_for_status()
            username = user_response.json()["username"]

            response = await client.get(
                f"{self.api_url}/repositories/{username}",
                headers={"Authorization": f"Bearer {access_token}"},
                params={
                    "page": page,
                    "pagelen": per_page,
                    "sort": "-updated_on",
                },
            )
            response.raise_for_status()

            repos = []
            for data in response.json().get("values", []):
                clone_url = ""
                for link in data.get("links", {}).get("clone", []):
                    if link.get("name") == "https":
                        clone_url = link.get("href", "")
                        break

                repos.append(GitRepository(
                    id=data["uuid"],
                    name=data["name"],
                    full_name=data["full_name"],
                    description=data.get("description"),
                    default_branch=data.get("mainbranch", {}).get("name", "main"),
                    private=data.get("is_private", False),
                    clone_url=clone_url,
                    web_url=data.get("links", {}).get("html", {}).get("href", ""),
                    provider=GitProviderType.BITBUCKET,
                ))
            return repos

    async def get_repository(
        self,
        access_token: str,
        owner: str,
        repo: str,
    ) -> Optional[GitRepository]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.api_url}/repositories/{owner}/{repo}",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            if response.status_code == 404:
                return None
            response.raise_for_status()
            data = response.json()

            clone_url = ""
            for link in data.get("links", {}).get("clone", []):
                if link.get("name") == "https":
                    clone_url = link.get("href", "")
                    break

            return GitRepository(
                id=data["uuid"],
                name=data["name"],
                full_name=data["full_name"],
                description=data.get("description"),
                default_branch=data.get("mainbranch", {}).get("name", "main"),
                private=data.get("is_private", False),
                clone_url=clone_url,
                web_url=data.get("links", {}).get("html", {}).get("href", ""),
                provider=GitProviderType.BITBUCKET,
            )

    async def list_branches(
        self,
        access_token: str,
        owner: str,
        repo: str,
    ) -> List[GitBranch]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.api_url}/repositories/{owner}/{repo}/refs/branches",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            response.raise_for_status()

            branches = []
            for data in response.json().get("values", []):
                branches.append(GitBranch(
                    name=data["name"],
                    sha=data["target"]["hash"],
                    protected=False,  # Bitbucket handles this differently
                ))
            return branches

    async def get_file(
        self,
        access_token: str,
        owner: str,
        repo: str,
        path: str,
        ref: Optional[str] = None,
    ) -> Optional[GitFile]:
        ref = ref or "main"
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.api_url}/repositories/{owner}/{repo}/src/{ref}/{path}",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            if response.status_code == 404:
                return None
            response.raise_for_status()

            return GitFile(
                path=path,
                content=response.text,
                sha=ref,
                encoding="utf-8",
            )

    async def create_branch(
        self,
        access_token: str,
        owner: str,
        repo: str,
        branch_name: str,
        from_ref: str,
    ) -> Optional[GitBranch]:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_url}/repositories/{owner}/{repo}/refs/branches",
                headers={"Authorization": f"Bearer {access_token}"},
                json={
                    "name": branch_name,
                    "target": {"hash": from_ref},
                },
            )
            if response.status_code in [400, 409]:
                return None
            response.raise_for_status()
            data = response.json()

            return GitBranch(
                name=data["name"],
                sha=data["target"]["hash"],
                protected=False,
            )

    async def create_or_update_file(
        self,
        access_token: str,
        owner: str,
        repo: str,
        path: str,
        content: str,
        message: str,
        branch: str,
        sha: Optional[str] = None,
    ) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            # Bitbucket uses multipart form for file uploads
            response = await client.post(
                f"{self.api_url}/repositories/{owner}/{repo}/src",
                headers={"Authorization": f"Bearer {access_token}"},
                data={
                    "message": message,
                    "branch": branch,
                    path: content,
                },
            )
            response.raise_for_status()
            return {"status": "success", "branch": branch}

    async def create_pull_request(
        self,
        access_token: str,
        owner: str,
        repo: str,
        title: str,
        body: str,
        source_branch: str,
        target_branch: str,
        draft: bool = False,
    ) -> Optional[GitPullRequest]:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_url}/repositories/{owner}/{repo}/pullrequests",
                headers={"Authorization": f"Bearer {access_token}"},
                json={
                    "title": title,
                    "description": body,
                    "source": {"branch": {"name": source_branch}},
                    "destination": {"branch": {"name": target_branch}},
                },
            )
            response.raise_for_status()
            data = response.json()

            return GitPullRequest(
                id=data["id"],
                number=data["id"],
                title=data["title"],
                description=data.get("description"),
                state=data["state"],
                source_branch=data["source"]["branch"]["name"],
                target_branch=data["destination"]["branch"]["name"],
                web_url=data["links"]["html"]["href"],
                created_at=datetime.fromisoformat(data["created_on"].replace("Z", "+00:00")),
                author=data["author"]["username"],
            )

    async def check_conflicts(
        self,
        access_token: str,
        owner: str,
        repo: str,
        source_branch: str,
        target_branch: str,
    ) -> List[GitConflict]:
        """Check for merge conflicts using Bitbucket's diff API."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.api_url}/repositories/{owner}/{repo}/diff/{target_branch}..{source_branch}",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            if response.status_code != 200:
                return []

            # Parse diff to find potential conflicts
            conflicts = []
            diff_text = response.text
            # Simple conflict detection - in practice, would need more sophisticated parsing
            if "<<<<<<" in diff_text or "======" in diff_text:
                conflicts.append(GitConflict(
                    file_path="unknown",
                    conflict_type="content",
                    details="Potential merge conflicts detected",
                ))

            return conflicts


def get_git_provider(provider_type: GitProviderType) -> GitProvider:
    """Factory function to get a Git provider instance."""
    providers = {
        GitProviderType.GITLAB: GitLabProvider,
        GitProviderType.BITBUCKET: BitbucketProvider,
    }

    provider_class = providers.get(provider_type)
    if not provider_class:
        raise ValueError(f"Unsupported provider: {provider_type}")

    return provider_class()
