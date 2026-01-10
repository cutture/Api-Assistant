"""
Authentication module for user management, JWT, OAuth, and password handling.
"""

from src.auth.password import (
    hash_password,
    verify_password,
    validate_password_strength,
    PasswordValidationError,
)
from src.auth.jwt import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_token,
    TokenPayload,
    TokenError,
)
from src.auth.user_service import UserService
from src.auth.oauth import GoogleOAuth

__all__ = [
    # Password
    "hash_password",
    "verify_password",
    "validate_password_strength",
    "PasswordValidationError",
    # JWT
    "create_access_token",
    "create_refresh_token",
    "decode_token",
    "verify_token",
    "TokenPayload",
    "TokenError",
    # User Service
    "UserService",
    # OAuth
    "GoogleOAuth",
]
