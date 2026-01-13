"""
JWT token creation and validation.
Uses python-jose for JWT handling.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from pydantic import BaseModel

from src.config import get_settings


class TokenError(Exception):
    """Exception raised for JWT token errors."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class TokenPayload(BaseModel):
    """JWT token payload structure."""

    sub: str  # Subject (user_id)
    email: Optional[str] = None
    type: str = "access"  # access or refresh
    exp: Optional[datetime] = None
    iat: Optional[datetime] = None

    class Config:
        from_attributes = True


def create_access_token(
    user_id: str,
    email: Optional[str] = None,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create a JWT access token.

    Args:
        user_id: User ID to encode in token
        email: Optional user email
        expires_delta: Optional custom expiration time

    Returns:
        Encoded JWT token string
    """
    settings = get_settings()

    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.jwt_access_token_expire_minutes)

    now = datetime.now(timezone.utc)
    expire = now + expires_delta

    payload = {
        "sub": user_id,
        "email": email,
        "type": "access",
        "exp": expire,
        "iat": now,
    }

    token = jwt.encode(
        payload,
        settings.effective_jwt_secret,
        algorithm=settings.jwt_algorithm,
    )
    return token


def create_refresh_token(
    user_id: str,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create a JWT refresh token.

    Args:
        user_id: User ID to encode in token
        expires_delta: Optional custom expiration time

    Returns:
        Encoded JWT refresh token string
    """
    settings = get_settings()

    if expires_delta is None:
        expires_delta = timedelta(days=settings.jwt_refresh_token_expire_days)

    now = datetime.now(timezone.utc)
    expire = now + expires_delta

    payload = {
        "sub": user_id,
        "type": "refresh",
        "exp": expire,
        "iat": now,
    }

    token = jwt.encode(
        payload,
        settings.effective_jwt_secret,
        algorithm=settings.jwt_algorithm,
    )
    return token


def decode_token(token: str) -> TokenPayload:
    """
    Decode and validate a JWT token.

    Args:
        token: JWT token string to decode

    Returns:
        TokenPayload with decoded data

    Raises:
        TokenError: If token is invalid or expired
    """
    settings = get_settings()

    try:
        payload = jwt.decode(
            token,
            settings.effective_jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
        return TokenPayload(**payload)
    except JWTError as e:
        raise TokenError(f"Invalid token: {str(e)}")


def verify_token(token: str, token_type: str = "access") -> TokenPayload:
    """
    Verify a JWT token and check its type.

    Args:
        token: JWT token string to verify
        token_type: Expected token type ("access" or "refresh")

    Returns:
        TokenPayload with decoded data

    Raises:
        TokenError: If token is invalid, expired, or wrong type
    """
    payload = decode_token(token)

    if payload.type != token_type:
        raise TokenError(f"Invalid token type. Expected {token_type}, got {payload.type}")

    return payload


def extract_token_from_header(authorization: str) -> str:
    """
    Extract JWT token from Authorization header.

    Args:
        authorization: Authorization header value (e.g., "Bearer <token>")

    Returns:
        Extracted token string

    Raises:
        TokenError: If header format is invalid
    """
    if not authorization:
        raise TokenError("Authorization header is missing")

    parts = authorization.split()

    if len(parts) != 2:
        raise TokenError("Invalid authorization header format")

    scheme, token = parts

    if scheme.lower() != "bearer":
        raise TokenError("Invalid authentication scheme. Use 'Bearer'")

    return token


def get_token_expiry(token: str) -> Optional[datetime]:
    """
    Get the expiration time of a token without full validation.

    Args:
        token: JWT token string

    Returns:
        Expiration datetime or None if not available
    """
    try:
        payload = decode_token(token)
        return payload.exp
    except TokenError:
        return None
