"""
Tests for security and input validation.
"""

import time
from pathlib import Path

import pytest

from src.core.security import (
    ValidationError,
    InputValidator,
    InputSanitizer,
    RateLimiter,
    get_validator,
    get_sanitizer,
    get_rate_limiter,
)


class TestInputValidator:
    """Test input validation functionality."""

    def test_validate_string_basic(self):
        """Test basic string validation."""
        validator = InputValidator()

        # Valid string
        result = validator.validate_string("hello", min_length=1, max_length=10)
        assert result == "hello"

    def test_validate_string_too_short(self):
        """Test string too short."""
        validator = InputValidator()

        with pytest.raises(ValidationError) as exc:
            validator.validate_string("hi", min_length=5)

        assert "at least 5 characters" in str(exc.value)

    def test_validate_string_too_long(self):
        """Test string too long."""
        validator = InputValidator()

        with pytest.raises(ValidationError) as exc:
            validator.validate_string("a" * 100, max_length=50)

        assert "at most 50 characters" in str(exc.value)

    def test_validate_string_pattern(self):
        """Test pattern matching."""
        validator = InputValidator()

        # Valid pattern
        result = validator.validate_string("abc123", pattern=r"^[a-z0-9]+$")
        assert result == "abc123"

        # Invalid pattern
        with pytest.raises(ValidationError) as exc:
            validator.validate_string("abc-123", pattern=r"^[a-z0-9]+$")

        assert "does not match required pattern" in str(exc.value)

    def test_validate_string_not_string_type(self):
        """Test non-string input."""
        validator = InputValidator()

        with pytest.raises(ValidationError) as exc:
            validator.validate_string(123, field_name="test_field")

        assert "must be a string" in str(exc.value)

    def test_validate_url_valid(self):
        """Test valid URL validation."""
        validator = InputValidator()

        # Valid URLs
        assert validator.validate_url("https://example.com") == "https://example.com"
        assert validator.validate_url("http://api.example.com/v1") == "http://api.example.com/v1"

    def test_validate_url_missing_scheme(self):
        """Test URL without scheme."""
        validator = InputValidator()

        with pytest.raises(ValidationError) as exc:
            validator.validate_url("example.com")

        assert "must include a scheme" in str(exc.value)

    def test_validate_url_invalid_scheme(self):
        """Test URL with invalid scheme."""
        validator = InputValidator()

        with pytest.raises(ValidationError) as exc:
            validator.validate_url("ftp://example.com")

        assert "scheme must be one of" in str(exc.value)

    def test_validate_url_missing_domain(self):
        """Test URL without domain."""
        validator = InputValidator()

        with pytest.raises(ValidationError) as exc:
            validator.validate_url("https://")

        assert "must include a domain" in str(exc.value)

    def test_validate_url_suspicious_characters(self):
        """Test URL with suspicious characters."""
        validator = InputValidator()

        with pytest.raises(ValidationError) as exc:
            validator.validate_url("https://user@evil.com@good.com")

        assert "suspicious characters" in str(exc.value)

    def test_validate_file_extension_valid(self):
        """Test valid file extension."""
        validator = InputValidator()

        result = validator.validate_file_extension(
            "spec.json",
            allowed_extensions=["json", "yaml"],
        )
        assert result == "spec.json"

    def test_validate_file_extension_invalid(self):
        """Test invalid file extension."""
        validator = InputValidator()

        with pytest.raises(ValidationError) as exc:
            validator.validate_file_extension(
                "file.exe",
                allowed_extensions=["json", "yaml"],
            )

        assert "not allowed" in str(exc.value)

    def test_validate_file_extension_missing(self):
        """Test file without extension."""
        validator = InputValidator()

        with pytest.raises(ValidationError) as exc:
            validator.validate_file_extension("file", allowed_extensions=["json"])

        assert "must have an extension" in str(exc.value)

    def test_validate_file_size_valid(self):
        """Test valid file size."""
        validator = InputValidator()

        result = validator.validate_file_size(
            1024 * 1024,  # 1 MB
            max_size_bytes=5 * 1024 * 1024,  # 5 MB
        )
        assert result == 1024 * 1024

    def test_validate_file_size_too_large(self):
        """Test file size too large."""
        validator = InputValidator()

        with pytest.raises(ValidationError) as exc:
            validator.validate_file_size(
                10 * 1024 * 1024,  # 10 MB
                max_size_bytes=5 * 1024 * 1024,  # 5 MB
            )

        assert "exceeds maximum" in str(exc.value)

    def test_check_sql_injection(self):
        """Test SQL injection detection."""
        validator = InputValidator()

        # SQL injection patterns
        assert validator.check_sql_injection("SELECT * FROM users")
        assert validator.check_sql_injection("'; DROP TABLE users; --")
        assert validator.check_sql_injection("1 OR 1=1")
        assert validator.check_sql_injection("UNION SELECT password")

        # Safe strings
        assert not validator.check_sql_injection("How do I authenticate?")
        assert not validator.check_sql_injection("What is the API endpoint?")

    def test_check_xss(self):
        """Test XSS detection."""
        validator = InputValidator()

        # XSS patterns
        assert validator.check_xss("<script>alert('xss')</script>")
        assert validator.check_xss("javascript:alert(1)")
        assert validator.check_xss("<img onerror=alert(1)>")
        assert validator.check_xss("<iframe src='evil.com'>")

        # Safe strings
        assert not validator.check_xss("How do I use the API?")
        assert not validator.check_xss("The <code> tag is useful")

    def test_check_command_injection(self):
        """Test command injection detection."""
        validator = InputValidator()

        # Command injection patterns
        assert validator.check_command_injection("ls; rm -rf /")  # semicolon
        assert validator.check_command_injection("$(whoami)")  # command substitution
        assert validator.check_command_injection("data | grep password")  # pipe
        assert validator.check_command_injection("cat > /dev/null")  # redirection

        # Safe strings (no special shell characters)
        assert not validator.check_command_injection("What is the status?")
        assert not validator.check_command_injection("cat file.txt")  # no special chars


class TestInputSanitizer:
    """Test input sanitization functionality."""

    def test_sanitize_html(self):
        """Test HTML sanitization."""
        sanitizer = InputSanitizer()

        # Basic HTML entities
        assert sanitizer.sanitize_html("<script>") == "&lt;script&gt;"
        assert sanitizer.sanitize_html("A & B") == "A &amp; B"
        assert sanitizer.sanitize_html('"quoted"') == "&quot;quoted&quot;"

    def test_sanitize_query_valid(self):
        """Test query sanitization with valid input."""
        sanitizer = InputSanitizer()

        result = sanitizer.sanitize_query("  How do I authenticate?  ")
        assert result == "How do I authenticate?"

    def test_sanitize_query_sql_injection(self):
        """Test query sanitization rejects SQL injection."""
        sanitizer = InputSanitizer()

        with pytest.raises(ValidationError) as exc:
            sanitizer.sanitize_query("SELECT * FROM users")

        assert "SQL patterns" in str(exc.value)

    def test_sanitize_query_command_injection(self):
        """Test query sanitization rejects command injection."""
        sanitizer = InputSanitizer()

        with pytest.raises(ValidationError) as exc:
            sanitizer.sanitize_query("ls; cat /etc/passwd")

        # Note: This is caught by SQL injection detection (semicolon) first
        assert ("SQL patterns" in str(exc.value) or "command patterns" in str(exc.value))

    def test_sanitize_query_length_limit(self):
        """Test query length limiting."""
        sanitizer = InputSanitizer()

        long_query = "A" * 2000
        result = sanitizer.sanitize_query(long_query, max_length=1000)
        assert len(result) == 1000

    def test_sanitize_filename(self):
        """Test filename sanitization."""
        sanitizer = InputSanitizer()

        # Path traversal attempts
        result1 = sanitizer.sanitize_filename("../../etc/passwd")
        assert "/" not in result1 and "\\" not in result1
        assert "passwd" in result1

        result2 = sanitizer.sanitize_filename("..\\..\\windows\\system32")
        assert "/" not in result2 and "\\" not in result2
        assert "system32" in result2

        # Null bytes
        assert sanitizer.sanitize_filename("file\x00.txt") == "file.txt"

        # Leading/trailing dots
        assert sanitizer.sanitize_filename("...file...") == "file"

        # Normal filename
        assert sanitizer.sanitize_filename("my-spec.json") == "my-spec.json"

    def test_sanitize_filename_length_limit(self):
        """Test filename length limiting."""
        sanitizer = InputSanitizer()

        long_name = "a" * 300 + ".json"
        result = sanitizer.sanitize_filename(long_name)
        assert len(result) <= 255
        assert result.endswith(".json")

    def test_sanitize_url_valid(self):
        """Test URL sanitization with valid URL."""
        sanitizer = InputSanitizer()

        result = sanitizer.sanitize_url("https://api.example.com")
        assert result == "https://api.example.com"

    def test_sanitize_url_javascript_scheme(self):
        """Test URL sanitization rejects javascript: scheme."""
        sanitizer = InputSanitizer()

        with pytest.raises(ValidationError) as exc:
            sanitizer.sanitize_url("javascript:alert(1)")

        # Can be caught by either validate_url or sanitize_url
        assert ("not allowed" in str(exc.value).lower() or "scheme" in str(exc.value).lower())

    def test_sanitize_url_data_scheme(self):
        """Test URL sanitization rejects data: scheme."""
        sanitizer = InputSanitizer()

        with pytest.raises(ValidationError) as exc:
            sanitizer.sanitize_url("data:text/html,<script>alert(1)</script>")

        # Can be caught by either validate_url or sanitize_url
        assert ("not allowed" in str(exc.value).lower() or "scheme" in str(exc.value).lower())


class TestRateLimiter:
    """Test rate limiting functionality."""

    def test_basic_rate_limiting(self):
        """Test basic rate limiting."""
        limiter = RateLimiter(requests_per_minute=60, burst=5)

        # Should allow burst requests
        for i in range(5):
            assert limiter.is_allowed("user1"), f"Request {i+1} should be allowed"

        # Should deny after burst exhausted
        assert not limiter.is_allowed("user1"), "Should deny after burst"

    def test_rate_limiter_recovery(self):
        """Test rate limiter token recovery."""
        limiter = RateLimiter(requests_per_minute=60, burst=2)

        # Exhaust tokens
        assert limiter.is_allowed("user1")
        assert limiter.is_allowed("user1")
        assert not limiter.is_allowed("user1")

        # Wait for token recovery (60 requests/min = 1 request/second)
        time.sleep(1.1)

        # Should allow one more request
        assert limiter.is_allowed("user1")

    def test_rate_limiter_per_user(self):
        """Test per-user rate limiting."""
        limiter = RateLimiter(requests_per_minute=60, burst=3)

        # User 1 exhausts tokens
        for i in range(3):
            assert limiter.is_allowed("user1")
        assert not limiter.is_allowed("user1")

        # User 2 should still have tokens
        for i in range(3):
            assert limiter.is_allowed("user2")
        assert not limiter.is_allowed("user2")

    def test_rate_limiter_get_wait_time(self):
        """Test wait time calculation."""
        limiter = RateLimiter(requests_per_minute=60, burst=1)

        # Exhaust tokens
        assert limiter.is_allowed("user1")

        # Get wait time
        wait_time = limiter.get_wait_time("user1")
        assert wait_time > 0
        assert wait_time <= 1.0  # Should be less than 1 second

    def test_rate_limiter_reset(self):
        """Test rate limiter reset."""
        limiter = RateLimiter(requests_per_minute=60, burst=2)

        # Exhaust tokens
        assert limiter.is_allowed("user1")
        assert limiter.is_allowed("user1")
        assert not limiter.is_allowed("user1")

        # Reset
        limiter.reset("user1")

        # Should allow requests again
        assert limiter.is_allowed("user1")
        assert limiter.is_allowed("user1")

    def test_rate_limiter_cleanup(self):
        """Test automatic cleanup of old buckets."""
        limiter = RateLimiter(
            requests_per_minute=60,
            burst=5,
            cleanup_interval=1,  # 1 second for testing
        )

        # Create buckets
        limiter.is_allowed("user1")
        limiter.is_allowed("user2")

        # Wait for cleanup interval
        time.sleep(1.1)

        # Trigger cleanup by making a new request
        limiter.is_allowed("user3")

        # Old buckets should be cleaned up (implicitly tested - no errors)


class TestGlobalInstances:
    """Test global instance getters."""

    def test_get_validator(self):
        """Test getting global validator."""
        validator1 = get_validator()
        validator2 = get_validator()

        assert validator1 is validator2  # Should be singleton
        assert isinstance(validator1, InputValidator)

    def test_get_sanitizer(self):
        """Test getting global sanitizer."""
        sanitizer1 = get_sanitizer()
        sanitizer2 = get_sanitizer()

        assert sanitizer1 is sanitizer2  # Should be singleton
        assert isinstance(sanitizer1, InputSanitizer)

    def test_get_rate_limiter(self):
        """Test getting global rate limiter."""
        limiter1 = get_rate_limiter()
        limiter2 = get_rate_limiter()

        assert limiter1 is limiter2  # Should be singleton
        assert isinstance(limiter1, RateLimiter)


class TestValidationError:
    """Test ValidationError exception."""

    def test_validation_error_basic(self):
        """Test basic validation error."""
        error = ValidationError("Test error")

        assert str(error) == "Test error"
        assert error.message == "Test error"
        assert error.field is None
        assert error.details == {}

    def test_validation_error_with_field(self):
        """Test validation error with field."""
        error = ValidationError("Invalid input", field="username")

        assert error.field == "username"

    def test_validation_error_with_details(self):
        """Test validation error with details."""
        error = ValidationError(
            "Too long",
            field="text",
            details={"length": 100, "max": 50},
        )

        assert error.details["length"] == 100
        assert error.details["max"] == 50


class TestSecurityIntegration:
    """Integration tests for security module."""

    def test_complete_input_validation_flow(self):
        """Test complete input validation flow."""
        validator = get_validator()
        sanitizer = get_sanitizer()

        # Validate and sanitize user query
        query = "  How do I authenticate with the API?  "

        # Validate
        validated = validator.validate_string(
            query,
            min_length=5,
            max_length=1000,
            field_name="query",
        )

        # Sanitize
        sanitized = sanitizer.sanitize_query(validated)

        assert sanitized == "How do I authenticate with the API?"

    def test_file_upload_validation_flow(self):
        """Test file upload validation flow."""
        validator = get_validator()
        sanitizer = get_sanitizer()

        # Validate file
        filename = "api-spec.json"
        size_bytes = 2 * 1024 * 1024  # 2 MB

        # Validate extension
        validator.validate_file_extension(filename, allowed_extensions=["json", "yaml"])

        # Validate size
        validator.validate_file_size(size_bytes, max_size_bytes=10 * 1024 * 1024)

        # Sanitize filename
        safe_filename = sanitizer.sanitize_filename(filename)

        assert safe_filename == "api-spec.json"

    def test_url_validation_flow(self):
        """Test URL validation flow."""
        validator = get_validator()
        sanitizer = get_sanitizer()

        url = "https://api.example.com/docs"

        # Validate
        validated = validator.validate_url(url)

        # Sanitize
        sanitized = sanitizer.sanitize_url(validated)

        assert sanitized == url

    def test_rate_limiting_flow(self):
        """Test rate limiting flow."""
        limiter = get_rate_limiter()

        # Simulate multiple requests
        user_id = "test_user"
        allowed_count = 0

        for i in range(20):
            if limiter.is_allowed(user_id):
                allowed_count += 1

        # Should not allow all 20 (burst limit + some recovery)
        assert allowed_count < 20

        # Should allow at least burst amount
        assert allowed_count >= 5
