"""
OAuth provider implementations.
Supports Google OAuth 2.0 and GitHub OAuth.
"""

import httpx
from typing import Optional
from urllib.parse import urlencode

from pydantic import BaseModel

from src.config import get_settings


class OAuthUserInfo(BaseModel):
    """User information from OAuth provider."""

    provider: str
    provider_user_id: str
    email: str
    name: Optional[str] = None
    avatar_url: Optional[str] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    username: Optional[str] = None  # For GitHub


class OAuthError(Exception):
    """Exception raised for OAuth errors."""

    def __init__(self, message: str, provider: str = "unknown"):
        self.message = message
        self.provider = provider
        super().__init__(f"[{provider}] {message}")


class GoogleOAuth:
    """Google OAuth 2.0 implementation."""

    AUTHORIZATION_URL = "https://accounts.google.com/o/oauth2/v2/auth"
    TOKEN_URL = "https://oauth2.googleapis.com/token"
    USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"

    # Scopes for user info
    SCOPES = [
        "openid",
        "email",
        "profile",
    ]

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        redirect_uri: Optional[str] = None,
    ):
        """
        Initialize Google OAuth client.

        Args:
            client_id: Google OAuth client ID (defaults to settings)
            client_secret: Google OAuth client secret (defaults to settings)
            redirect_uri: OAuth callback redirect URI
        """
        settings = get_settings()
        self.client_id = client_id or settings.google_client_id
        self.client_secret = client_secret or settings.google_client_secret
        self.redirect_uri = redirect_uri

    def get_authorization_url(
        self,
        redirect_uri: Optional[str] = None,
        state: Optional[str] = None,
    ) -> str:
        """
        Generate Google OAuth authorization URL.

        Args:
            redirect_uri: OAuth callback URL
            state: Optional state parameter for CSRF protection

        Returns:
            Authorization URL to redirect user to
        """
        if not self.client_id:
            raise OAuthError("Google OAuth client ID not configured", "google")

        redirect = redirect_uri or self.redirect_uri
        if not redirect:
            raise OAuthError("Redirect URI is required", "google")

        params = {
            "client_id": self.client_id,
            "redirect_uri": redirect,
            "response_type": "code",
            "scope": " ".join(self.SCOPES),
            "access_type": "offline",  # Request refresh token
            "prompt": "consent",  # Always show consent screen for refresh token
        }

        if state:
            params["state"] = state

        return f"{self.AUTHORIZATION_URL}?{urlencode(params)}"

    async def exchange_code(
        self,
        code: str,
        redirect_uri: Optional[str] = None,
    ) -> dict:
        """
        Exchange authorization code for tokens.

        Args:
            code: Authorization code from OAuth callback
            redirect_uri: OAuth callback URL (must match original)

        Returns:
            Token response dictionary

        Raises:
            OAuthError: If token exchange fails
        """
        if not self.client_id or not self.client_secret:
            raise OAuthError("Google OAuth credentials not configured", "google")

        redirect = redirect_uri or self.redirect_uri
        if not redirect:
            raise OAuthError("Redirect URI is required", "google")

        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": redirect,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.TOKEN_URL,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

            if response.status_code != 200:
                error_data = response.json() if response.content else {}
                error_msg = error_data.get("error_description", response.text)
                raise OAuthError(f"Token exchange failed: {error_msg}", "google")

            return response.json()

    async def get_user_info(self, access_token: str) -> OAuthUserInfo:
        """
        Get user information from Google.

        Args:
            access_token: OAuth access token

        Returns:
            OAuthUserInfo with user details

        Raises:
            OAuthError: If user info request fails
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.USERINFO_URL,
                headers={"Authorization": f"Bearer {access_token}"},
            )

            if response.status_code != 200:
                raise OAuthError(
                    f"Failed to get user info: {response.text}",
                    "google",
                )

            data = response.json()

            return OAuthUserInfo(
                provider="google",
                provider_user_id=data.get("id", ""),
                email=data.get("email", ""),
                name=data.get("name"),
                avatar_url=data.get("picture"),
                access_token=access_token,
            )

    async def authenticate(
        self,
        code: str,
        redirect_uri: Optional[str] = None,
    ) -> OAuthUserInfo:
        """
        Complete OAuth flow: exchange code and get user info.

        Args:
            code: Authorization code from callback
            redirect_uri: OAuth callback URL

        Returns:
            OAuthUserInfo with user details and tokens

        Raises:
            OAuthError: If authentication fails
        """
        # Exchange code for tokens
        token_data = await self.exchange_code(code, redirect_uri)

        access_token = token_data.get("access_token")
        refresh_token = token_data.get("refresh_token")

        if not access_token:
            raise OAuthError("No access token in response", "google")

        # Get user info
        user_info = await self.get_user_info(access_token)
        user_info.access_token = access_token
        user_info.refresh_token = refresh_token

        return user_info

    async def refresh_access_token(self, refresh_token: str) -> dict:
        """
        Refresh an expired access token.

        Args:
            refresh_token: OAuth refresh token

        Returns:
            New token response dictionary

        Raises:
            OAuthError: If token refresh fails
        """
        if not self.client_id or not self.client_secret:
            raise OAuthError("Google OAuth credentials not configured", "google")

        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.TOKEN_URL,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

            if response.status_code != 200:
                error_data = response.json() if response.content else {}
                error_msg = error_data.get("error_description", response.text)
                raise OAuthError(f"Token refresh failed: {error_msg}", "google")

            return response.json()


class GitHubOAuth:
    """GitHub OAuth 2.0 implementation."""

    AUTHORIZATION_URL = "https://github.com/login/oauth/authorize"
    TOKEN_URL = "https://github.com/login/oauth/access_token"
    API_BASE_URL = "https://api.github.com"
    USERINFO_URL = f"{API_BASE_URL}/user"
    USER_EMAILS_URL = f"{API_BASE_URL}/user/emails"

    # Scopes for read-only repository access
    # Using minimal scopes: read-only repo access and user info
    SCOPES = [
        "read:user",
        "user:email",
        "repo",  # For private repos - can be reduced to public_repo for public only
    ]

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        redirect_uri: Optional[str] = None,
    ):
        """
        Initialize GitHub OAuth client.

        Args:
            client_id: GitHub OAuth client ID (defaults to settings)
            client_secret: GitHub OAuth client secret (defaults to settings)
            redirect_uri: OAuth callback redirect URI
        """
        settings = get_settings()
        self.client_id = client_id or getattr(settings, 'github_client_id', None)
        self.client_secret = client_secret or getattr(settings, 'github_client_secret', None)
        self.redirect_uri = redirect_uri

    def get_authorization_url(
        self,
        redirect_uri: Optional[str] = None,
        state: Optional[str] = None,
    ) -> str:
        """
        Generate GitHub OAuth authorization URL.

        Args:
            redirect_uri: OAuth callback URL
            state: Optional state parameter for CSRF protection

        Returns:
            Authorization URL to redirect user to
        """
        if not self.client_id:
            raise OAuthError("GitHub OAuth client ID not configured", "github")

        redirect = redirect_uri or self.redirect_uri
        if not redirect:
            raise OAuthError("Redirect URI is required", "github")

        params = {
            "client_id": self.client_id,
            "redirect_uri": redirect,
            "scope": " ".join(self.SCOPES),
        }

        if state:
            params["state"] = state

        return f"{self.AUTHORIZATION_URL}?{urlencode(params)}"

    async def exchange_code(
        self,
        code: str,
        redirect_uri: Optional[str] = None,
    ) -> dict:
        """
        Exchange authorization code for tokens.

        Args:
            code: Authorization code from OAuth callback
            redirect_uri: OAuth callback URL (must match original)

        Returns:
            Token response dictionary

        Raises:
            OAuthError: If token exchange fails
        """
        if not self.client_id or not self.client_secret:
            raise OAuthError("GitHub OAuth credentials not configured", "github")

        redirect = redirect_uri or self.redirect_uri
        if not redirect:
            raise OAuthError("Redirect URI is required", "github")

        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "redirect_uri": redirect,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.TOKEN_URL,
                data=data,
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Accept": "application/json",
                },
            )

            if response.status_code != 200:
                raise OAuthError(f"Token exchange failed: {response.text}", "github")

            result = response.json()

            if "error" in result:
                error_msg = result.get("error_description", result.get("error"))
                raise OAuthError(f"Token exchange failed: {error_msg}", "github")

            return result

    async def get_user_info(self, access_token: str) -> OAuthUserInfo:
        """
        Get user information from GitHub.

        Args:
            access_token: OAuth access token

        Returns:
            OAuthUserInfo with user details

        Raises:
            OAuthError: If user info request fails
        """
        async with httpx.AsyncClient() as client:
            # Get user profile
            response = await client.get(
                self.USERINFO_URL,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/vnd.github+json",
                    "X-GitHub-Api-Version": "2022-11-28",
                },
            )

            if response.status_code != 200:
                raise OAuthError(
                    f"Failed to get user info: {response.text}",
                    "github",
                )

            data = response.json()

            # Get user email if not public
            email = data.get("email")
            if not email:
                email = await self._get_primary_email(client, access_token)

            return OAuthUserInfo(
                provider="github",
                provider_user_id=str(data.get("id", "")),
                email=email or "",
                name=data.get("name") or data.get("login"),
                avatar_url=data.get("avatar_url"),
                access_token=access_token,
                username=data.get("login"),
            )

    async def _get_primary_email(
        self,
        client: httpx.AsyncClient,
        access_token: str
    ) -> Optional[str]:
        """Get user's primary email from GitHub."""
        try:
            response = await client.get(
                self.USER_EMAILS_URL,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/vnd.github+json",
                    "X-GitHub-Api-Version": "2022-11-28",
                },
            )

            if response.status_code == 200:
                emails = response.json()
                # Find primary email
                for email in emails:
                    if email.get("primary") and email.get("verified"):
                        return email.get("email")
                # Fallback to first verified email
                for email in emails:
                    if email.get("verified"):
                        return email.get("email")
        except Exception:
            pass

        return None

    async def authenticate(
        self,
        code: str,
        redirect_uri: Optional[str] = None,
    ) -> OAuthUserInfo:
        """
        Complete OAuth flow: exchange code and get user info.

        Args:
            code: Authorization code from callback
            redirect_uri: OAuth callback URL

        Returns:
            OAuthUserInfo with user details and tokens

        Raises:
            OAuthError: If authentication fails
        """
        # Exchange code for tokens
        token_data = await self.exchange_code(code, redirect_uri)

        access_token = token_data.get("access_token")
        # GitHub doesn't provide refresh tokens by default
        refresh_token = token_data.get("refresh_token")

        if not access_token:
            raise OAuthError("No access token in response", "github")

        # Get user info
        user_info = await self.get_user_info(access_token)
        user_info.access_token = access_token
        user_info.refresh_token = refresh_token

        return user_info

    async def get_user_repos(
        self,
        access_token: str,
        page: int = 1,
        per_page: int = 30,
        sort: str = "updated",
    ) -> list[dict]:
        """
        Get user's accessible repositories.

        Args:
            access_token: OAuth access token
            page: Page number
            per_page: Results per page
            sort: Sort by (created, updated, pushed, full_name)

        Returns:
            List of repository dictionaries
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.API_BASE_URL}/user/repos",
                params={
                    "page": page,
                    "per_page": per_page,
                    "sort": sort,
                    "affiliation": "owner,collaborator,organization_member",
                },
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/vnd.github+json",
                    "X-GitHub-Api-Version": "2022-11-28",
                },
            )

            if response.status_code != 200:
                raise OAuthError(f"Failed to get repos: {response.text}", "github")

            return response.json()

    async def get_repo_contents(
        self,
        access_token: str,
        owner: str,
        repo: str,
        path: str = "",
    ) -> list[dict]:
        """
        Get repository contents at a path.

        Args:
            access_token: OAuth access token
            owner: Repository owner
            repo: Repository name
            path: Path in repository

        Returns:
            List of content items
        """
        async with httpx.AsyncClient() as client:
            url = f"{self.API_BASE_URL}/repos/{owner}/{repo}/contents/{path}"
            response = await client.get(
                url,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/vnd.github+json",
                    "X-GitHub-Api-Version": "2022-11-28",
                },
            )

            if response.status_code != 200:
                raise OAuthError(f"Failed to get contents: {response.text}", "github")

            result = response.json()
            return result if isinstance(result, list) else [result]

    async def get_file_content(
        self,
        access_token: str,
        owner: str,
        repo: str,
        path: str,
    ) -> str:
        """
        Get raw file content from repository.

        Args:
            access_token: OAuth access token
            owner: Repository owner
            repo: Repository name
            path: File path

        Returns:
            File content as string
        """
        async with httpx.AsyncClient() as client:
            url = f"{self.API_BASE_URL}/repos/{owner}/{repo}/contents/{path}"
            response = await client.get(
                url,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/vnd.github.raw+json",
                    "X-GitHub-Api-Version": "2022-11-28",
                },
            )

            if response.status_code != 200:
                raise OAuthError(f"Failed to get file: {response.text}", "github")

            return response.text

    async def get_repo_languages(
        self,
        access_token: str,
        owner: str,
        repo: str,
    ) -> dict:
        """
        Get repository languages breakdown.

        Args:
            access_token: OAuth access token
            owner: Repository owner
            repo: Repository name

        Returns:
            Dict of language -> bytes
        """
        async with httpx.AsyncClient() as client:
            url = f"{self.API_BASE_URL}/repos/{owner}/{repo}/languages"
            response = await client.get(
                url,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/vnd.github+json",
                    "X-GitHub-Api-Version": "2022-11-28",
                },
            )

            if response.status_code != 200:
                raise OAuthError(f"Failed to get languages: {response.text}", "github")

            return response.json()

    async def get_branch_ref(
        self,
        access_token: str,
        owner: str,
        repo: str,
        branch: str,
    ) -> dict:
        """
        Get branch reference (SHA).

        Args:
            access_token: OAuth access token
            owner: Repository owner
            repo: Repository name
            branch: Branch name

        Returns:
            Branch reference data
        """
        async with httpx.AsyncClient() as client:
            url = f"{self.API_BASE_URL}/repos/{owner}/{repo}/git/refs/heads/{branch}"
            response = await client.get(
                url,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/vnd.github+json",
                    "X-GitHub-Api-Version": "2022-11-28",
                },
            )

            if response.status_code != 200:
                raise OAuthError(f"Failed to get branch ref: {response.text}", "github")

            return response.json()

    async def create_branch(
        self,
        access_token: str,
        owner: str,
        repo: str,
        branch_name: str,
        from_sha: str,
    ) -> dict:
        """
        Create a new branch from a SHA.

        Args:
            access_token: OAuth access token
            owner: Repository owner
            repo: Repository name
            branch_name: New branch name
            from_sha: SHA to branch from

        Returns:
            Created branch reference
        """
        async with httpx.AsyncClient() as client:
            url = f"{self.API_BASE_URL}/repos/{owner}/{repo}/git/refs"
            response = await client.post(
                url,
                json={
                    "ref": f"refs/heads/{branch_name}",
                    "sha": from_sha,
                },
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/vnd.github+json",
                    "X-GitHub-Api-Version": "2022-11-28",
                },
            )

            if response.status_code not in (200, 201):
                raise OAuthError(f"Failed to create branch: {response.text}", "github")

            return response.json()

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
    ) -> dict:
        """
        Create or update a file in the repository.

        Args:
            access_token: OAuth access token
            owner: Repository owner
            repo: Repository name
            path: File path
            content: File content (will be base64 encoded)
            message: Commit message
            branch: Branch name
            sha: Current file SHA (required for updates)

        Returns:
            Commit and content data
        """
        import base64

        async with httpx.AsyncClient() as client:
            url = f"{self.API_BASE_URL}/repos/{owner}/{repo}/contents/{path}"

            data = {
                "message": message,
                "content": base64.b64encode(content.encode()).decode(),
                "branch": branch,
            }

            if sha:
                data["sha"] = sha

            response = await client.put(
                url,
                json=data,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/vnd.github+json",
                    "X-GitHub-Api-Version": "2022-11-28",
                },
            )

            if response.status_code not in (200, 201):
                raise OAuthError(f"Failed to create/update file: {response.text}", "github")

            return response.json()

    async def create_pull_request(
        self,
        access_token: str,
        owner: str,
        repo: str,
        title: str,
        body: str,
        head: str,
        base: str,
        draft: bool = False,
    ) -> dict:
        """
        Create a pull request.

        Args:
            access_token: OAuth access token
            owner: Repository owner
            repo: Repository name
            title: PR title
            body: PR description
            head: Head branch (with changes)
            base: Base branch (target)
            draft: Create as draft PR

        Returns:
            Created pull request data
        """
        async with httpx.AsyncClient() as client:
            url = f"{self.API_BASE_URL}/repos/{owner}/{repo}/pulls"
            response = await client.post(
                url,
                json={
                    "title": title,
                    "body": body,
                    "head": head,
                    "base": base,
                    "draft": draft,
                },
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/vnd.github+json",
                    "X-GitHub-Api-Version": "2022-11-28",
                },
            )

            if response.status_code not in (200, 201):
                raise OAuthError(f"Failed to create PR: {response.text}", "github")

            return response.json()

    async def get_pull_request(
        self,
        access_token: str,
        owner: str,
        repo: str,
        pull_number: int,
    ) -> dict:
        """
        Get pull request details.

        Args:
            access_token: OAuth access token
            owner: Repository owner
            repo: Repository name
            pull_number: PR number

        Returns:
            Pull request data
        """
        async with httpx.AsyncClient() as client:
            url = f"{self.API_BASE_URL}/repos/{owner}/{repo}/pulls/{pull_number}"
            response = await client.get(
                url,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/vnd.github+json",
                    "X-GitHub-Api-Version": "2022-11-28",
                },
            )

            if response.status_code != 200:
                raise OAuthError(f"Failed to get PR: {response.text}", "github")

            return response.json()

    async def list_pull_requests(
        self,
        access_token: str,
        owner: str,
        repo: str,
        state: str = "open",
        per_page: int = 30,
    ) -> list[dict]:
        """
        List pull requests for a repository.

        Args:
            access_token: OAuth access token
            owner: Repository owner
            repo: Repository name
            state: PR state (open, closed, all)
            per_page: Results per page

        Returns:
            List of pull requests
        """
        async with httpx.AsyncClient() as client:
            url = f"{self.API_BASE_URL}/repos/{owner}/{repo}/pulls"
            response = await client.get(
                url,
                params={"state": state, "per_page": per_page},
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/vnd.github+json",
                    "X-GitHub-Api-Version": "2022-11-28",
                },
            )

            if response.status_code != 200:
                raise OAuthError(f"Failed to list PRs: {response.text}", "github")

            return response.json()


def get_oauth_provider(provider: str):
    """
    Get OAuth provider instance by name.

    Args:
        provider: Provider name (google, github)

    Returns:
        OAuth provider instance

    Raises:
        ValueError: If provider is not supported
    """
    providers = {
        "google": GoogleOAuth,
        "github": GitHubOAuth,
    }

    if provider not in providers:
        supported = ", ".join(providers.keys())
        raise ValueError(f"Unsupported OAuth provider: {provider}. Supported: {supported}")

    return providers[provider]()
