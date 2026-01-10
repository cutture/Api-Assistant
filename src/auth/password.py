"""
Password hashing and validation utilities.
Uses bcrypt for secure password hashing.
"""

import re
from typing import List

from passlib.context import CryptContext

from src.config import get_settings


# Password hashing context using bcrypt
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12,  # Cost factor for bcrypt
)


class PasswordValidationError(Exception):
    """Exception raised when password validation fails."""

    def __init__(self, errors: List[str]):
        self.errors = errors
        super().__init__("; ".join(errors))


def hash_password(password: str) -> str:
    """
    Hash a plain text password using bcrypt.

    Args:
        password: Plain text password to hash

    Returns:
        Hashed password string
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain text password against a hashed password.

    Args:
        plain_password: Plain text password to verify
        hashed_password: Hashed password to compare against

    Returns:
        True if password matches, False otherwise
    """
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        return False


def validate_password_strength(password: str) -> List[str]:
    """
    Validate password meets strength requirements.

    Requirements (configurable via settings):
    - Minimum 8 characters
    - At least 1 lowercase letter (a-z)
    - At least 1 uppercase letter (A-Z)
    - At least 1 special character (!@#$%^&*()_+-=[]{}|;:,.<>?)
    - At least 1 number (0-9)

    Args:
        password: Password to validate

    Returns:
        List of validation error messages (empty if valid)
    """
    settings = get_settings()
    errors: List[str] = []

    # Check minimum length
    if len(password) < settings.password_min_length:
        errors.append(
            f"Password must be at least {settings.password_min_length} characters long"
        )

    # Check for lowercase letter
    if settings.password_require_lowercase and not re.search(r"[a-z]", password):
        errors.append("Password must contain at least one lowercase letter (a-z)")

    # Check for uppercase letter
    if settings.password_require_uppercase and not re.search(r"[A-Z]", password):
        errors.append("Password must contain at least one uppercase letter (A-Z)")

    # Check for digit
    if settings.password_require_digit and not re.search(r"\d", password):
        errors.append("Password must contain at least one number (0-9)")

    # Check for special character
    if settings.password_require_special and not re.search(
        r"[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]", password
    ):
        errors.append(
            "Password must contain at least one special character (!@#$%^&*()_+-=[]{}|;:,.<>?)"
        )

    return errors


def ensure_password_valid(password: str) -> None:
    """
    Validate password and raise exception if invalid.

    Args:
        password: Password to validate

    Raises:
        PasswordValidationError: If password doesn't meet requirements
    """
    errors = validate_password_strength(password)
    if errors:
        raise PasswordValidationError(errors)


def get_password_requirements() -> dict:
    """
    Get the current password requirements as a dictionary.

    Returns:
        Dictionary describing password requirements
    """
    settings = get_settings()
    return {
        "min_length": settings.password_min_length,
        "require_uppercase": settings.password_require_uppercase,
        "require_lowercase": settings.password_require_lowercase,
        "require_digit": settings.password_require_digit,
        "require_special": settings.password_require_special,
        "description": (
            f"Password must be at least {settings.password_min_length} characters "
            "with at least one uppercase letter, one lowercase letter, "
            "one number, and one special character."
        ),
    }
