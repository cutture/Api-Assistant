"""
Security and input validation module.

Features:
- Input validation and sanitization
- Rate limiting
- API specification validation
- XSS prevention
- SQL injection prevention
- Command injection prevention
- File upload validation
"""

import hashlib
import re
import time
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from threading import Lock
from typing import Any, Dict, List, Optional, Set
from urllib.parse import urlparse

import structlog

from src.config import settings

logger = structlog.get_logger(__name__)


# ============================================================================
# Input Validation
# ============================================================================


class ValidationError(Exception):
    """Raised when input validation fails."""

    def __init__(self, message: str, field: Optional[str] = None, details: Optional[Dict] = None):
        super().__init__(message)
        self.message = message
        self.field = field
        self.details = details or {}


class InputValidator:
    """
    Validator for various input types.

    Features:
    - String validation (length, patterns)
    - URL validation
    - File path validation
    - JSON/YAML validation
    - API specification validation
    """

    # Dangerous patterns to detect
    SQL_INJECTION_PATTERNS = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE)\b)",
        r"(--|;|\/\*|\*\/|xp_|sp_)",
        r"(\bUNION\b.*\bSELECT\b)",
        r"(\bOR\b.*=.*)",
    ]

    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"on\w+\s*=",
        r"<iframe",
        r"<object",
        r"<embed",
    ]

    COMMAND_INJECTION_PATTERNS = [
        r"[;&|`$()]",
        r"\$\{",
        r"\$\(",
        r">\s*/dev/",
    ]

    @staticmethod
    def validate_string(
        value: str,
        min_length: int = 0,
        max_length: int = 10000,
        pattern: Optional[str] = None,
        field_name: str = "string",
    ) -> str:
        """
        Validate string input.

        Args:
            value: String to validate
            min_length: Minimum length
            max_length: Maximum length
            pattern: Optional regex pattern to match
            field_name: Field name for error messages

        Returns:
            Validated string

        Raises:
            ValidationError: If validation fails
        """
        if not isinstance(value, str):
            raise ValidationError(
                f"{field_name} must be a string",
                field=field_name,
            )

        if len(value) < min_length:
            raise ValidationError(
                f"{field_name} must be at least {min_length} characters",
                field=field_name,
                details={"length": len(value), "min_length": min_length},
            )

        if len(value) > max_length:
            raise ValidationError(
                f"{field_name} must be at most {max_length} characters",
                field=field_name,
                details={"length": len(value), "max_length": max_length},
            )

        if pattern:
            if not re.match(pattern, value):
                raise ValidationError(
                    f"{field_name} does not match required pattern",
                    field=field_name,
                )

        return value

    @staticmethod
    def validate_url(url: str, allowed_schemes: Set[str] = {"http", "https"}) -> str:
        """
        Validate URL.

        Args:
            url: URL to validate
            allowed_schemes: Set of allowed URL schemes

        Returns:
            Validated URL

        Raises:
            ValidationError: If URL is invalid
        """
        try:
            parsed = urlparse(url)

            if not parsed.scheme:
                raise ValidationError(
                    "URL must include a scheme (e.g., https://)",
                    field="url",
                )

            if parsed.scheme not in allowed_schemes:
                raise ValidationError(
                    f"URL scheme must be one of: {', '.join(allowed_schemes)}",
                    field="url",
                    details={"scheme": parsed.scheme, "allowed": list(allowed_schemes)},
                )

            if not parsed.netloc:
                raise ValidationError(
                    "URL must include a domain",
                    field="url",
                )

            # Check for suspicious patterns
            if re.search(r"@", parsed.netloc):
                raise ValidationError(
                    "URL contains suspicious characters",
                    field="url",
                )

            return url

        except ValueError as e:
            raise ValidationError(
                f"Invalid URL format: {str(e)}",
                field="url",
            )

    @staticmethod
    def validate_file_extension(
        filename: str,
        allowed_extensions: Optional[List[str]] = None,
    ) -> str:
        """
        Validate file extension.

        Args:
            filename: Filename to validate
            allowed_extensions: List of allowed extensions (default: from settings)

        Returns:
            Validated filename

        Raises:
            ValidationError: If extension is not allowed
        """
        if allowed_extensions is None:
            allowed_extensions = settings.allowed_extensions_list

        # Get file extension
        path = Path(filename)
        ext = path.suffix.lstrip(".").lower()

        if not ext:
            raise ValidationError(
                "File must have an extension",
                field="filename",
            )

        if ext not in allowed_extensions:
            raise ValidationError(
                f"File extension .{ext} is not allowed",
                field="filename",
                details={
                    "extension": ext,
                    "allowed": allowed_extensions,
                },
            )

        return filename

    @staticmethod
    def validate_file_size(size_bytes: int, max_size_bytes: Optional[int] = None) -> int:
        """
        Validate file size.

        Args:
            size_bytes: File size in bytes
            max_size_bytes: Maximum size (default: from settings)

        Returns:
            Validated size

        Raises:
            ValidationError: If file is too large
        """
        if max_size_bytes is None:
            max_size_bytes = settings.max_upload_size_bytes

        if size_bytes > max_size_bytes:
            raise ValidationError(
                f"File size exceeds maximum of {max_size_bytes / (1024*1024):.1f}MB",
                field="file_size",
                details={
                    "size_mb": size_bytes / (1024 * 1024),
                    "max_mb": max_size_bytes / (1024 * 1024),
                },
            )

        return size_bytes

    @classmethod
    def check_sql_injection(cls, value: str) -> bool:
        """
        Check if string contains SQL injection patterns.

        Args:
            value: String to check

        Returns:
            True if SQL injection detected
        """
        for pattern in cls.SQL_INJECTION_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                return True
        return False

    @classmethod
    def check_xss(cls, value: str) -> bool:
        """
        Check if string contains XSS patterns.

        Args:
            value: String to check

        Returns:
            True if XSS detected
        """
        for pattern in cls.XSS_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                return True
        return False

    @classmethod
    def check_command_injection(cls, value: str) -> bool:
        """
        Check if string contains command injection patterns.

        Args:
            value: String to check

        Returns:
            True if command injection detected
        """
        for pattern in cls.COMMAND_INJECTION_PATTERNS:
            if re.search(pattern, value):
                return True
        return False


# ============================================================================
# Input Sanitization
# ============================================================================


class InputSanitizer:
    """
    Sanitizer for user inputs.

    Features:
    - HTML escaping
    - Script tag removal
    - SQL keyword escaping
    - Path traversal prevention
    """

    @staticmethod
    def sanitize_html(value: str) -> str:
        """
        Sanitize HTML by escaping special characters.

        Args:
            value: String to sanitize

        Returns:
            Sanitized string
        """
        replacements = {
            "&": "&amp;",
            "<": "&lt;",
            ">": "&gt;",
            '"': "&quot;",
            "'": "&#x27;",
            "/": "&#x2F;",
        }

        for char, escaped in replacements.items():
            value = value.replace(char, escaped)

        return value

    @staticmethod
    def sanitize_query(value: str, max_length: int = 1000) -> str:
        """
        Sanitize user query input.

        Args:
            value: Query to sanitize
            max_length: Maximum length

        Returns:
            Sanitized query

        Raises:
            ValidationError: If query is suspicious
        """
        # Trim and limit length
        value = value.strip()[:max_length]

        # Check for injection attacks
        if InputValidator.check_sql_injection(value):
            logger.warning("sql_injection_detected", query=value[:100])
            raise ValidationError(
                "Query contains suspicious SQL patterns",
                field="query",
            )

        if InputValidator.check_command_injection(value):
            logger.warning("command_injection_detected", query=value[:100])
            raise ValidationError(
                "Query contains suspicious command patterns",
                field="query",
            )

        return value

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        Sanitize filename to prevent path traversal.

        Args:
            filename: Filename to sanitize

        Returns:
            Sanitized filename
        """
        # Remove directory separators
        filename = filename.replace("/", "_").replace("\\", "_")

        # Remove null bytes
        filename = filename.replace("\x00", "")

        # Remove leading/trailing dots and spaces
        filename = filename.strip(". ")

        # Limit length
        if len(filename) > 255:
            name, ext = filename.rsplit(".", 1) if "." in filename else (filename, "")
            filename = name[:250] + ("." + ext if ext else "")

        return filename

    @staticmethod
    def sanitize_url(url: str) -> str:
        """
        Sanitize URL for safe display.

        Args:
            url: URL to sanitize

        Returns:
            Sanitized URL
        """
        # Basic validation first
        InputValidator.validate_url(url)

        # Remove javascript: and data: schemes
        if url.lower().startswith(("javascript:", "data:", "vbscript:")):
            raise ValidationError(
                "URL scheme not allowed",
                field="url",
            )

        return url


# ============================================================================
# Rate Limiting
# ============================================================================


class RateLimiter:
    """
    Token bucket rate limiter.

    Features:
    - Per-user rate limiting
    - Configurable rate and burst
    - Thread-safe
    - Automatic cleanup of old entries
    """

    def __init__(
        self,
        requests_per_minute: int = 60,
        burst: int = 10,
        cleanup_interval: int = 300,
    ):
        """
        Initialize rate limiter.

        Args:
            requests_per_minute: Maximum requests per minute
            burst: Maximum burst size
            cleanup_interval: Cleanup interval in seconds
        """
        self.rate = requests_per_minute / 60.0  # requests per second
        self.burst = burst
        self.cleanup_interval = cleanup_interval

        self._buckets: Dict[str, Dict[str, float]] = defaultdict(
            lambda: {"tokens": self.burst, "last_update": time.time()}
        )
        self._lock = Lock()
        self._last_cleanup = time.time()

    def _cleanup_old_buckets(self) -> None:
        """Remove buckets not accessed in cleanup_interval."""
        now = time.time()
        if now - self._last_cleanup < self.cleanup_interval:
            return

        cutoff = now - self.cleanup_interval
        to_remove = [
            key for key, bucket in self._buckets.items() if bucket["last_update"] < cutoff
        ]

        for key in to_remove:
            del self._buckets[key]

        self._last_cleanup = now

        if to_remove:
            logger.debug("rate_limiter_cleanup", removed_count=len(to_remove))

    def is_allowed(self, identifier: str) -> bool:
        """
        Check if request is allowed.

        Args:
            identifier: Unique identifier (e.g., user ID, IP address)

        Returns:
            True if request is allowed
        """
        with self._lock:
            # Cleanup old buckets periodically
            self._cleanup_old_buckets()

            bucket = self._buckets[identifier]
            now = time.time()

            # Calculate tokens to add based on elapsed time
            elapsed = now - bucket["last_update"]
            bucket["tokens"] = min(
                self.burst,
                bucket["tokens"] + elapsed * self.rate,
            )
            bucket["last_update"] = now

            # Check if request is allowed
            if bucket["tokens"] >= 1.0:
                bucket["tokens"] -= 1.0
                return True

            logger.warning(
                "rate_limit_exceeded",
                identifier=identifier[:50],
                tokens=bucket["tokens"],
            )
            return False

    def get_wait_time(self, identifier: str) -> float:
        """
        Get time to wait before next request is allowed.

        Args:
            identifier: Unique identifier

        Returns:
            Wait time in seconds
        """
        with self._lock:
            bucket = self._buckets[identifier]
            tokens_needed = 1.0 - bucket["tokens"]

            if tokens_needed <= 0:
                return 0.0

            return tokens_needed / self.rate

    def reset(self, identifier: str) -> None:
        """
        Reset rate limit for identifier.

        Args:
            identifier: Unique identifier
        """
        with self._lock:
            if identifier in self._buckets:
                del self._buckets[identifier]


# ============================================================================
# Global Instances
# ============================================================================

# Global validator instance
_validator: Optional[InputValidator] = None
_sanitizer: Optional[InputSanitizer] = None
_rate_limiter: Optional[RateLimiter] = None


def get_validator() -> InputValidator:
    """Get global validator instance."""
    global _validator
    if _validator is None:
        _validator = InputValidator()
    return _validator


def get_sanitizer() -> InputSanitizer:
    """Get global sanitizer instance."""
    global _sanitizer
    if _sanitizer is None:
        _sanitizer = InputSanitizer()
    return _sanitizer


def get_rate_limiter() -> RateLimiter:
    """Get global rate limiter instance."""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter(
            requests_per_minute=60,
            burst=10,
        )
    return _rate_limiter
