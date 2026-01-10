"""
OAuth provider implementations.
Currently supports Google OAuth 2.0.
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


def get_oauth_provider(provider: str):
    """
    Get OAuth provider instance by name.

    Args:
        provider: Provider name (google, github, microsoft)

    Returns:
        OAuth provider instance

    Raises:
        ValueError: If provider is not supported
    """
    providers = {
        "google": GoogleOAuth,
    }

    if provider not in providers:
        supported = ", ".join(providers.keys())
        raise ValueError(f"Unsupported OAuth provider: {provider}. Supported: {supported}")

    return providers[provider]()
