"""API Authentication middleware.

Provides API key-based and JWT-based authentication for securing endpoints.
Supports both authenticated users and guest access.
"""
import logging
from typing import Optional, Union

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader, HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import get_settings
from src.auth.jwt import verify_token, TokenError, TokenPayload

logger = logging.getLogger(__name__)

# API key header
API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)

# JWT Bearer token
JWT_BEARER = HTTPBearer(auto_error=False)


class CurrentUser:
    """Represents the current authenticated user or guest."""

    def __init__(
        self,
        user_id: Optional[str] = None,
        email: Optional[str] = None,
        is_guest: bool = True,
        is_authenticated: bool = False,
        auth_method: str = "none",
    ):
        self.user_id = user_id
        self.email = email
        self.is_guest = is_guest
        self.is_authenticated = is_authenticated
        self.auth_method = auth_method  # "jwt", "api_key", or "none"

    def __repr__(self) -> str:
        if self.is_guest:
            return f"<CurrentUser(guest, id={self.user_id})>"
        return f"<CurrentUser(id={self.user_id}, email={self.email})>"


async def get_current_user_optional(
    api_key: Optional[str] = Security(API_KEY_HEADER),
    bearer: Optional[HTTPAuthorizationCredentials] = Security(JWT_BEARER),
) -> CurrentUser:
    """
    Get current user from JWT token or API key (optional).

    This dependency does not require authentication - it returns a guest user
    if no valid credentials are provided. Use for endpoints that support
    both authenticated and guest access.

    Priority:
    1. JWT Bearer token (if valid)
    2. API key (if valid)
    3. Guest user (fallback)

    Returns:
        CurrentUser object with authentication details
    """
    settings = get_settings()

    # Try JWT token first
    if bearer and bearer.credentials:
        try:
            payload = verify_token(bearer.credentials, token_type="access")
            is_guest = payload.sub.startswith("guest_") if payload.sub else True

            return CurrentUser(
                user_id=payload.sub,
                email=payload.email,
                is_guest=is_guest,
                is_authenticated=True,
                auth_method="jwt",
            )
        except TokenError as e:
            logger.debug(f"Invalid JWT token: {e.message}")
            # Fall through to try API key

    # Try API key
    if api_key and settings.api_keys_list:
        if api_key in settings.api_keys_list:
            return CurrentUser(
                user_id=f"apikey_{api_key[:8]}",
                email=None,
                is_guest=False,
                is_authenticated=True,
                auth_method="api_key",
            )

    # Return guest user
    return CurrentUser(
        user_id=None,
        email=None,
        is_guest=True,
        is_authenticated=False,
        auth_method="none",
    )


async def get_current_user(
    api_key: Optional[str] = Security(API_KEY_HEADER),
    bearer: Optional[HTTPAuthorizationCredentials] = Security(JWT_BEARER),
) -> CurrentUser:
    """
    Get current authenticated user (required).

    This dependency requires authentication - it raises 401 if no valid
    credentials are provided. Use for protected endpoints.

    Returns:
        CurrentUser object with authentication details

    Raises:
        HTTPException: If authentication fails
    """
    settings = get_settings()

    # Skip authentication if not required (development mode)
    if not settings.require_auth:
        return CurrentUser(
            user_id="dev_user",
            email=None,
            is_guest=True,
            is_authenticated=False,
            auth_method="none",
        )

    user = await get_current_user_optional(api_key, bearer)

    if not user.is_authenticated:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Provide JWT token or API key.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def get_verified_user(
    current_user: CurrentUser = Depends(get_current_user),
) -> CurrentUser:
    """
    Get current user and verify they are not a guest.

    Use for endpoints that require a real authenticated user account
    (not API key or guest access).

    Returns:
        CurrentUser object

    Raises:
        HTTPException: If user is guest or using API key
    """
    if current_user.is_guest or current_user.auth_method == "api_key":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint requires a verified user account. Please log in.",
        )

    return current_user


async def verify_api_key(api_key: Optional[str] = Security(API_KEY_HEADER)) -> str:
    """
    Verify API key from request header.

    Args:
        api_key: API key from X-API-Key header

    Returns:
        The validated API key

    Raises:
        HTTPException: If API key is missing or invalid
    """
    settings = get_settings()

    # Skip authentication if not required (development mode)
    if not settings.require_auth:
        logger.debug("API authentication disabled (REQUIRE_AUTH=false)")
        return "auth-disabled"

    # Check if API key is provided
    if not api_key:
        logger.warning("Request missing API key")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required. Include 'X-API-Key' header in your request.",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    # Validate against configured keys
    valid_keys = settings.api_keys_list

    if not valid_keys:
        logger.error("No API keys configured but authentication required!")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server configuration error: No API keys configured",
        )

    if api_key not in valid_keys:
        logger.warning(f"Invalid API key attempted: {api_key[:10]}...")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key",
        )

    logger.debug(f"API key authenticated: {api_key[:10]}...")
    return api_key


def get_optional_api_key(api_key: Optional[str] = Security(API_KEY_HEADER)) -> Optional[str]:
    """
    Get API key if provided, but don't require it.

    Useful for endpoints that have different behavior based on authentication
    but don't strictly require it.

    Args:
        api_key: API key from X-API-Key header

    Returns:
        The API key if valid, None otherwise
    """
    settings = get_settings()

    if not api_key or not settings.require_auth:
        return None

    valid_keys = settings.api_keys_list
    if api_key in valid_keys:
        return api_key

    return None
