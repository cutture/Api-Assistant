"""
User service for CRUD operations and authentication.
"""

import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import get_settings
from src.database.models import User, OAuthAccount, EmailVerificationToken
from src.auth.password import hash_password, verify_password, ensure_password_valid


class UserService:
    """Service for user management operations."""

    def __init__(self, db: AsyncSession):
        """
        Initialize UserService with database session.

        Args:
            db: Async database session
        """
        self.db = db

    async def create_user(
        self,
        email: str,
        password: str,
        name: Optional[str] = None,
        is_verified: bool = False,
    ) -> User:
        """
        Create a new user with email and password.

        Args:
            email: User email (must be unique)
            password: Plain text password (will be hashed)
            name: Optional user name
            is_verified: Whether email is verified (default False)

        Returns:
            Created User object

        Raises:
            ValueError: If email already exists or password is invalid
        """
        # Validate password strength
        ensure_password_valid(password)

        # Check if email already exists
        existing = await self.get_user_by_email(email)
        if existing:
            raise ValueError("A user with this email already exists")

        # Create user with hashed password
        user = User(
            email=email.lower().strip(),
            hashed_password=hash_password(password),
            name=name,
            is_verified=is_verified,
        )

        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)

        return user

    async def create_oauth_user(
        self,
        email: str,
        name: Optional[str] = None,
        avatar_url: Optional[str] = None,
        provider: str = "google",
        provider_user_id: str = "",
        provider_email: Optional[str] = None,
        access_token: Optional[str] = None,
        refresh_token: Optional[str] = None,
    ) -> User:
        """
        Create a new user via OAuth (no password required).

        Args:
            email: User email
            name: User name from OAuth provider
            avatar_url: Avatar URL from OAuth provider
            provider: OAuth provider name (google, github, etc.)
            provider_user_id: User ID from OAuth provider
            provider_email: Email from OAuth provider
            access_token: OAuth access token
            refresh_token: OAuth refresh token

        Returns:
            Created User object
        """
        # Check if email already exists
        existing = await self.get_user_by_email(email)
        if existing:
            # Link OAuth account to existing user
            await self.link_oauth_account(
                user_id=existing.id,
                provider=provider,
                provider_user_id=provider_user_id,
                provider_email=provider_email,
                access_token=access_token,
                refresh_token=refresh_token,
            )
            # Update user info if missing
            if not existing.name and name:
                existing.name = name
            if not existing.avatar_url and avatar_url:
                existing.avatar_url = avatar_url
            if not existing.is_verified:
                existing.is_verified = True  # OAuth users are pre-verified
            await self.db.flush()
            return existing

        # Create new user (OAuth users are pre-verified)
        user = User(
            email=email.lower().strip(),
            hashed_password=None,  # No password for OAuth users
            name=name,
            avatar_url=avatar_url,
            is_verified=True,  # OAuth users are pre-verified
        )

        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)

        # Link OAuth account
        await self.link_oauth_account(
            user_id=user.id,
            provider=provider,
            provider_user_id=provider_user_id,
            provider_email=provider_email,
            access_token=access_token,
            refresh_token=refresh_token,
        )

        return user

    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """
        Get user by ID.

        Args:
            user_id: User ID

        Returns:
            User object or None if not found
        """
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Get user by email.

        Args:
            email: User email

        Returns:
            User object or None if not found
        """
        result = await self.db.execute(
            select(User).where(User.email == email.lower().strip())
        )
        return result.scalar_one_or_none()

    async def authenticate_user(
        self,
        email: str,
        password: str,
    ) -> Optional[User]:
        """
        Authenticate user with email and password.

        Args:
            email: User email
            password: Plain text password

        Returns:
            User object if authentication succeeds, None otherwise
        """
        user = await self.get_user_by_email(email)

        if not user:
            return None

        if not user.hashed_password:
            # User was created via OAuth, no password set
            return None

        if not verify_password(password, user.hashed_password):
            return None

        if not user.is_active:
            return None

        # Update last login timestamp
        user.last_login_at = datetime.now(timezone.utc)
        await self.db.flush()

        return user

    async def update_user(
        self,
        user_id: str,
        name: Optional[str] = None,
        avatar_url: Optional[str] = None,
        is_active: Optional[bool] = None,
        is_verified: Optional[bool] = None,
    ) -> Optional[User]:
        """
        Update user information.

        Args:
            user_id: User ID to update
            name: New name (if provided)
            avatar_url: New avatar URL (if provided)
            is_active: New active status (if provided)
            is_verified: New verified status (if provided)

        Returns:
            Updated User object or None if not found
        """
        user = await self.get_user_by_id(user_id)

        if not user:
            return None

        if name is not None:
            user.name = name
        if avatar_url is not None:
            user.avatar_url = avatar_url
        if is_active is not None:
            user.is_active = is_active
        if is_verified is not None:
            user.is_verified = is_verified

        await self.db.flush()
        await self.db.refresh(user)

        return user

    async def change_password(
        self,
        user_id: str,
        current_password: str,
        new_password: str,
    ) -> bool:
        """
        Change user password.

        Args:
            user_id: User ID
            current_password: Current password for verification
            new_password: New password to set

        Returns:
            True if password changed successfully, False otherwise
        """
        user = await self.get_user_by_id(user_id)

        if not user or not user.hashed_password:
            return False

        # Verify current password
        if not verify_password(current_password, user.hashed_password):
            return False

        # Validate new password
        ensure_password_valid(new_password)

        # Update password
        user.hashed_password = hash_password(new_password)
        await self.db.flush()

        return True

    async def set_password(self, user_id: str, new_password: str) -> bool:
        """
        Set password for OAuth user (who doesn't have one).

        Args:
            user_id: User ID
            new_password: New password to set

        Returns:
            True if password set successfully, False otherwise
        """
        user = await self.get_user_by_id(user_id)

        if not user:
            return False

        # Validate new password
        ensure_password_valid(new_password)

        # Set password
        user.hashed_password = hash_password(new_password)
        await self.db.flush()

        return True

    async def delete_user(self, user_id: str) -> bool:
        """
        Delete user and all related data.

        Args:
            user_id: User ID to delete

        Returns:
            True if deleted successfully, False if not found
        """
        user = await self.get_user_by_id(user_id)

        if not user:
            return False

        await self.db.delete(user)
        await self.db.flush()

        return True

    async def link_oauth_account(
        self,
        user_id: str,
        provider: str,
        provider_user_id: str,
        provider_email: Optional[str] = None,
        access_token: Optional[str] = None,
        refresh_token: Optional[str] = None,
    ) -> OAuthAccount:
        """
        Link an OAuth account to a user.

        Args:
            user_id: User ID to link to
            provider: OAuth provider name
            provider_user_id: User ID from OAuth provider
            provider_email: Email from OAuth provider
            access_token: OAuth access token
            refresh_token: OAuth refresh token

        Returns:
            Created or updated OAuthAccount
        """
        # Check if OAuth account already exists
        result = await self.db.execute(
            select(OAuthAccount).where(
                OAuthAccount.provider == provider,
                OAuthAccount.provider_user_id == provider_user_id,
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            # Update existing OAuth account
            existing.access_token = access_token
            existing.refresh_token = refresh_token
            existing.provider_email = provider_email
            await self.db.flush()
            return existing

        # Create new OAuth account
        oauth_account = OAuthAccount(
            user_id=user_id,
            provider=provider,
            provider_user_id=provider_user_id,
            provider_email=provider_email,
            access_token=access_token,
            refresh_token=refresh_token,
        )

        self.db.add(oauth_account)
        await self.db.flush()
        await self.db.refresh(oauth_account)

        return oauth_account

    async def get_oauth_account(
        self,
        provider: str,
        provider_user_id: str,
    ) -> Optional[OAuthAccount]:
        """
        Get OAuth account by provider and provider user ID.

        Args:
            provider: OAuth provider name
            provider_user_id: User ID from OAuth provider

        Returns:
            OAuthAccount or None if not found
        """
        result = await self.db.execute(
            select(OAuthAccount).where(
                OAuthAccount.provider == provider,
                OAuthAccount.provider_user_id == provider_user_id,
            )
        )
        return result.scalar_one_or_none()

    async def create_verification_token(
        self,
        user_id: str,
        token_type: str = "email_verification",
    ) -> EmailVerificationToken:
        """
        Create an email verification token.

        Args:
            user_id: User ID to create token for
            token_type: Token type (email_verification or password_reset)

        Returns:
            Created EmailVerificationToken
        """
        settings = get_settings()

        # Generate secure token
        token = secrets.token_urlsafe(32)

        # Calculate expiration
        expires_at = datetime.now(timezone.utc) + timedelta(
            hours=settings.verification_token_expire_hours
        )

        verification_token = EmailVerificationToken(
            user_id=user_id,
            token=token,
            token_type=token_type,
            expires_at=expires_at,
        )

        self.db.add(verification_token)
        await self.db.flush()
        await self.db.refresh(verification_token)

        return verification_token

    async def verify_token(
        self,
        token: str,
        token_type: str = "email_verification",
    ) -> Optional[User]:
        """
        Verify a token and return the associated user.

        Args:
            token: Token string to verify
            token_type: Expected token type

        Returns:
            User if token is valid, None otherwise
        """
        result = await self.db.execute(
            select(EmailVerificationToken).where(
                EmailVerificationToken.token == token,
                EmailVerificationToken.token_type == token_type,
            )
        )
        verification_token = result.scalar_one_or_none()

        if not verification_token or not verification_token.is_valid:
            return None

        # Mark token as used
        verification_token.used_at = datetime.now(timezone.utc)

        # Get user
        user = await self.get_user_by_id(verification_token.user_id)

        if user and token_type == "email_verification":
            user.is_verified = True

        await self.db.flush()

        return user

    async def get_user_by_oauth(
        self,
        provider: str,
        provider_user_id: str,
    ) -> Optional[User]:
        """
        Get user by OAuth provider info.

        Args:
            provider: OAuth provider name
            provider_user_id: User ID from OAuth provider

        Returns:
            User or None if not found
        """
        oauth_account = await self.get_oauth_account(provider, provider_user_id)

        if not oauth_account:
            return None

        return await self.get_user_by_id(oauth_account.user_id)
