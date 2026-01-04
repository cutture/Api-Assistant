"""API Authentication middleware.

Provides API key-based authentication for securing endpoints.
"""
import logging
from typing import Optional

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

from src.config import get_settings

logger = logging.getLogger(__name__)

# API key header
API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)


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
