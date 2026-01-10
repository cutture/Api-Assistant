"""
Authentication API endpoints.
Handles user registration, login, OAuth, and token management.
"""

import logging
import secrets
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import get_settings
from src.database.connection import get_db, init_db
from src.database.models import User
from src.auth.password import (
    validate_password_strength,
    get_password_requirements,
    PasswordValidationError,
)
from src.auth.jwt import (
    create_access_token,
    create_refresh_token,
    verify_token,
    TokenError,
)
from src.auth.user_service import UserService
from src.auth.oauth import GoogleOAuth, OAuthError


logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/auth", tags=["Authentication"])


# ============================================================================
# Pydantic Models for Auth Endpoints
# ============================================================================


class RegisterRequest(BaseModel):
    """User registration request."""

    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password", min_length=8)
    name: Optional[str] = Field(None, description="User display name")


class RegisterResponse(BaseModel):
    """User registration response."""

    success: bool = Field(..., description="Registration success status")
    message: str = Field(..., description="Status message")
    user_id: str = Field(..., description="Created user ID")
    email: str = Field(..., description="User email")
    requires_verification: bool = Field(..., description="Whether email verification is required")


class LoginRequest(BaseModel):
    """User login request."""

    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")


class TokenResponse(BaseModel):
    """Token response for login/refresh."""

    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Access token expiration in seconds")
    user: dict = Field(..., description="User information")


class RefreshTokenRequest(BaseModel):
    """Token refresh request."""

    refresh_token: str = Field(..., description="Refresh token")


class UserResponse(BaseModel):
    """User profile response."""

    id: str = Field(..., description="User ID")
    email: str = Field(..., description="User email")
    name: Optional[str] = Field(None, description="User name")
    avatar_url: Optional[str] = Field(None, description="User avatar URL")
    is_verified: bool = Field(..., description="Email verification status")
    is_admin: bool = Field(..., description="Admin status")
    created_at: str = Field(..., description="Account creation timestamp")
    last_login_at: Optional[str] = Field(None, description="Last login timestamp")


class PasswordRequirementsResponse(BaseModel):
    """Password requirements response."""

    min_length: int = Field(..., description="Minimum password length")
    require_uppercase: bool = Field(..., description="Require uppercase letter")
    require_lowercase: bool = Field(..., description="Require lowercase letter")
    require_digit: bool = Field(..., description="Require number")
    require_special: bool = Field(..., description="Require special character")
    description: str = Field(..., description="Human-readable requirements")


class VerifyEmailRequest(BaseModel):
    """Email verification request."""

    token: str = Field(..., description="Verification token from email")


class VerifyEmailResponse(BaseModel):
    """Email verification response."""

    success: bool = Field(..., description="Verification success status")
    message: str = Field(..., description="Status message")


class ResendVerificationRequest(BaseModel):
    """Request to resend verification email."""

    email: EmailStr = Field(..., description="User email address")


class OAuthLoginResponse(BaseModel):
    """OAuth login initiation response."""

    authorization_url: str = Field(..., description="URL to redirect user for OAuth")
    state: str = Field(..., description="State parameter for CSRF protection")


# ============================================================================
# Authentication Endpoints
# ============================================================================


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: RegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Register a new user account.

    - Email must be unique
    - Password must meet strength requirements
    - Email verification is required before login
    """
    # Validate password strength
    errors = validate_password_strength(request.password)
    if errors:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "Password does not meet requirements", "errors": errors},
        )

    user_service = UserService(db)
    settings = get_settings()

    try:
        # Auto-verify if skip_email_verification is enabled (for local dev)
        auto_verify = settings.skip_email_verification

        # Create user
        user = await user_service.create_user(
            email=request.email,
            password=request.password,
            name=request.name,
            is_verified=auto_verify,
        )

        requires_verification = not auto_verify
        message = "Registration successful."

        if requires_verification:
            # Create verification token
            verification_token = await user_service.create_verification_token(
                user_id=user.id,
                token_type="email_verification",
            )
            # TODO: Send verification email
            # In production, send email with verification link containing token
            logger.info(f"User registered: {user.email}, verification token: {verification_token.token}")
            message = "Registration successful. Please check your email to verify your account."
        else:
            logger.info(f"User registered and auto-verified: {user.email}")
            message = "Registration successful. You can now log in."

        return RegisterResponse(
            success=True,
            message=message,
            user_id=user.id,
            email=user.email,
            requires_verification=requires_verification,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except PasswordValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "Password validation failed", "errors": e.errors},
        )


@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Login with email and password.

    Returns JWT tokens for authentication.
    """
    user_service = UserService(db)
    settings = get_settings()

    # Authenticate user
    user = await user_service.authenticate_user(
        email=request.email,
        password=request.password,
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    # Check if email is verified (skip if skip_email_verification is enabled)
    if not user.is_verified and not settings.skip_email_verification:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified. Please check your email for verification link.",
        )

    # Create tokens
    access_token = create_access_token(user_id=user.id, email=user.email)
    refresh_token = create_refresh_token(user_id=user.id)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.jwt_access_token_expire_minutes * 60,
        user=user.to_dict(),
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Refresh access token using refresh token.
    """
    try:
        # Verify refresh token
        payload = verify_token(request.refresh_token, token_type="refresh")
    except TokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid refresh token: {e.message}",
        )

    user_service = UserService(db)
    user = await user_service.get_user_by_id(payload.sub)

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    settings = get_settings()

    # Create new tokens
    access_token = create_access_token(user_id=user.id, email=user.email)
    new_refresh_token = create_refresh_token(user_id=user.id)

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        expires_in=settings.jwt_access_token_expire_minutes * 60,
        user=user.to_dict(),
    )


@router.post("/logout")
async def logout():
    """
    Logout user.

    Note: Since we use JWTs, logout is handled client-side by deleting tokens.
    This endpoint is provided for API completeness.
    """
    return {"success": True, "message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    user: User = Depends(lambda: None),  # Will be replaced with proper dependency
    db: AsyncSession = Depends(get_db),
):
    """
    Get current authenticated user profile.

    Requires valid JWT token in Authorization header.
    """
    # This endpoint needs the get_current_user dependency from auth.py
    # For now, return a placeholder that will be properly implemented
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="This endpoint requires JWT authentication middleware",
    )


@router.get("/password-requirements", response_model=PasswordRequirementsResponse)
async def get_password_requirements_endpoint():
    """
    Get password strength requirements.

    Returns the rules that passwords must follow.
    """
    return PasswordRequirementsResponse(**get_password_requirements())


# ============================================================================
# Email Verification Endpoints
# ============================================================================


@router.post("/verify-email", response_model=VerifyEmailResponse)
async def verify_email(
    request: VerifyEmailRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Verify email address using token from email.
    """
    user_service = UserService(db)

    user = await user_service.verify_token(
        token=request.token,
        token_type="email_verification",
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token",
        )

    return VerifyEmailResponse(
        success=True,
        message="Email verified successfully. You can now log in.",
    )


@router.post("/resend-verification", response_model=VerifyEmailResponse)
async def resend_verification(
    request: ResendVerificationRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Resend email verification link.
    """
    user_service = UserService(db)
    user = await user_service.get_user_by_email(request.email)

    if not user:
        # Don't reveal if email exists
        return VerifyEmailResponse(
            success=True,
            message="If an account exists with this email, a verification link has been sent.",
        )

    if user.is_verified:
        return VerifyEmailResponse(
            success=True,
            message="Email is already verified.",
        )

    # Create new verification token
    verification_token = await user_service.create_verification_token(
        user_id=user.id,
        token_type="email_verification",
    )

    # TODO: Send verification email
    logger.info(f"Resent verification for {user.email}, token: {verification_token.token}")

    return VerifyEmailResponse(
        success=True,
        message="If an account exists with this email, a verification link has been sent.",
    )


# ============================================================================
# OAuth Endpoints
# ============================================================================


@router.get("/oauth/google")
async def oauth_google_login(
    redirect_uri: str = Query(..., description="Frontend callback URL"),
):
    """
    Initiate Google OAuth login flow.

    Returns URL to redirect user to Google for authentication.
    """
    settings = get_settings()

    if not settings.google_client_id:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Google OAuth is not configured",
        )

    # Generate state for CSRF protection
    state = secrets.token_urlsafe(32)

    # Build backend callback URL
    # The frontend will receive the tokens after backend processes the callback
    oauth = GoogleOAuth()

    try:
        auth_url = oauth.get_authorization_url(
            redirect_uri=redirect_uri,
            state=state,
        )
    except OAuthError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"OAuth configuration error: {e.message}",
        )

    return OAuthLoginResponse(
        authorization_url=auth_url,
        state=state,
    )


@router.get("/oauth/google/callback")
async def oauth_google_callback(
    code: str = Query(..., description="Authorization code from Google"),
    state: Optional[str] = Query(None, description="State parameter"),
    redirect_uri: str = Query(..., description="Original redirect URI"),
    db: AsyncSession = Depends(get_db),
):
    """
    Handle Google OAuth callback.

    Exchanges authorization code for tokens and creates/updates user.
    Returns JWT tokens for the authenticated user.
    """
    settings = get_settings()

    if not settings.google_client_id:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Google OAuth is not configured",
        )

    oauth = GoogleOAuth()

    try:
        # Exchange code for user info
        user_info = await oauth.authenticate(code, redirect_uri)
    except OAuthError as e:
        logger.error(f"OAuth error: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"OAuth authentication failed: {e.message}",
        )

    # Create or update user
    user_service = UserService(db)

    try:
        user = await user_service.create_oauth_user(
            email=user_info.email,
            name=user_info.name,
            avatar_url=user_info.avatar_url,
            provider=user_info.provider,
            provider_user_id=user_info.provider_user_id,
            provider_email=user_info.email,
            access_token=user_info.access_token,
            refresh_token=user_info.refresh_token,
        )
    except Exception as e:
        logger.error(f"Error creating OAuth user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user account",
        )

    # Create JWT tokens
    access_token = create_access_token(user_id=user.id, email=user.email)
    refresh_token = create_refresh_token(user_id=user.id)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.jwt_access_token_expire_minutes * 60,
        user=user.to_dict(),
    )


# ============================================================================
# Guest Access
# ============================================================================


@router.post("/guest", response_model=TokenResponse)
async def guest_login(
    db: AsyncSession = Depends(get_db),
):
    """
    Create a guest session.

    Returns limited-access tokens for unauthenticated users.
    Guest users can use most API features but data is not persisted across sessions.
    """
    settings = get_settings()

    # Create a temporary guest user ID
    guest_id = f"guest_{secrets.token_hex(16)}"

    # Create tokens with guest flag
    access_token = create_access_token(
        user_id=guest_id,
        email=None,
    )
    refresh_token = create_refresh_token(user_id=guest_id)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.jwt_access_token_expire_minutes * 60,
        user={
            "id": guest_id,
            "email": None,
            "name": "Guest User",
            "is_guest": True,
            "is_verified": False,
            "is_admin": False,
        },
    )


# ============================================================================
# Database Initialization (called on startup)
# ============================================================================


async def init_auth_db():
    """Initialize authentication database tables."""
    await init_db()
    logger.info("Authentication database initialized")
