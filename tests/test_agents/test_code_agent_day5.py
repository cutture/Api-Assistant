"""
Additional tests for Day 5 Code Generator enhancements.
"""

import pytest

from src.agents.code_agent import CodeGenerator, CodeLibrary


class TestCodeGeneratorDay5:
    """Test suite for Day 5 enhancements."""

    def test_validate_code_valid_syntax(self):
        """Test code validation with valid Python code."""
        gen = CodeGenerator(validate_syntax=True)

        valid_code = """
def hello():
    return "world"
"""
        result = gen._validate_code(valid_code)

        assert result["valid"] is True
        assert len(result["errors"]) == 0

    def test_validate_code_invalid_syntax(self):
        """Test code validation with invalid Python code."""
        gen = CodeGenerator(validate_syntax=True)

        invalid_code = """
def hello()
    return "world"
"""
        result = gen._validate_code(invalid_code)

        assert result["valid"] is False
        assert len(result["errors"]) > 0

    def test_validate_code_empty_string(self):
        """Test code validation with empty string."""
        gen = CodeGenerator(validate_syntax=True)

        result = gen._validate_code("")

        assert result["valid"] is True  # Empty string is valid Python

    def test_format_code_removes_trailing_whitespace(self):
        """Test that formatting removes trailing whitespace."""
        gen = CodeGenerator()

        code_with_trailing = "def hello():    \n    return True    \n"
        formatted = gen._format_code(code_with_trailing)

        lines = formatted.split('\n')
        for line in lines[:-1]:  # Exclude last empty line
            assert not line.endswith(' '), f"Line has trailing space: '{line}'"

    def test_format_code_removes_consecutive_blank_lines(self):
        """Test that formatting removes multiple consecutive blank lines."""
        gen = CodeGenerator()

        code_with_blanks = "def hello():\n\n\n\n    return True\n"
        formatted = gen._format_code(code_with_blanks)

        # Should not have 3+ consecutive newlines
        assert '\n\n\n' not in formatted

    def test_format_code_ends_with_single_newline(self):
        """Test that formatted code ends with single newline."""
        gen = CodeGenerator()

        code = "def hello():\n    return True"
        formatted = gen._format_code(code)

        assert formatted.endswith('\n')
        assert not formatted.endswith('\n\n')

    def test_add_retry_decorator_for_get(self):
        """Test adding retry decorator for GET request."""
        gen = CodeGenerator(add_retry=True)

        original_code = """import requests

def get_users():
    return requests.get("/users")
"""
        code_with_retry = gen._add_retry_decorator(original_code, "GET")

        assert "from tenacity import" in code_with_retry
        assert "@retry" in code_with_retry
        assert "stop_after_attempt(3)" in code_with_retry

    def test_add_retry_decorator_not_for_post(self):
        """Test that retry is NOT added for non-idempotent POST."""
        gen = CodeGenerator(add_retry=True)

        original_code = """import requests

def post_users():
    return requests.post("/users")
"""
        code_with_retry = gen._add_retry_decorator(original_code, "POST")

        # POST is not idempotent, so no retry should be added
        assert "@retry" not in code_with_retry
        assert "tenacity" not in code_with_retry

    def test_add_retry_decorator_for_put(self):
        """Test that retry IS added for idempotent PUT."""
        gen = CodeGenerator(add_retry=True)

        original_code = """import requests

def put_user():
    return requests.put("/users/1")
"""
        code_with_retry = gen._add_retry_decorator(original_code, "PUT")

        assert "@retry" in code_with_retry
        assert "from tenacity import" in code_with_retry

    def test_add_retry_decorator_for_delete(self):
        """Test that retry IS added for idempotent DELETE."""
        gen = CodeGenerator(add_retry=True)

        original_code = """import requests

def delete_user():
    return requests.delete("/users/1")
"""
        code_with_retry = gen._add_retry_decorator(original_code, "DELETE")

        assert "@retry" in code_with_retry

    def test_add_retry_decorator_no_function_found(self):
        """Test retry decorator when no function definition found."""
        gen = CodeGenerator(add_retry=True)

        code_without_function = "x = 5\nprint(x)"
        result = gen._add_retry_decorator(code_without_function, "GET")

        # Should return original code unchanged
        assert result == code_without_function

    def test_generate_code_for_endpoint_simple(self):
        """Test direct code generation without LLM."""
        gen = CodeGenerator()

        code = gen.generate_code_for_endpoint(
            endpoint="/users",
            method="GET",
            description="List all users"
        )

        assert "def get_users(" in code
        assert "List all users" in code
        assert "requests.get" in code

    def test_generate_code_for_endpoint_with_path_params(self):
        """Test direct generation with path parameters."""
        gen = CodeGenerator()

        code = gen.generate_code_for_endpoint(
            endpoint="/users/{user_id}",
            method="GET",
            path_params=[
                {"name": "user_id", "type": "string", "description": "User ID", "example": "'123'"}
            ]
        )

        assert "user_id: str" in code
        assert "{user_id}" in code

    def test_generate_code_for_endpoint_with_query_params(self):
        """Test direct generation with query parameters."""
        gen = CodeGenerator()

        code = gen.generate_code_for_endpoint(
            endpoint="/users",
            method="GET",
            query_params=[
                {"name": "limit", "type": "integer", "required": False, "default": "10", "example": "20"}
            ]
        )

        assert "limit: int" in code
        assert "params" in code

    def test_generate_code_for_endpoint_with_bearer_auth(self):
        """Test direct generation with Bearer authentication."""
        gen = CodeGenerator()

        code = gen.generate_code_for_endpoint(
            endpoint="/users",
            method="GET",
            auth_type="bearer"
        )

        assert "access_token" in code
        assert "Bearer" in code
        assert "Authorization" in code

    def test_generate_code_for_endpoint_with_api_key_auth(self):
        """Test direct generation with API key authentication."""
        gen = CodeGenerator()

        code = gen.generate_code_for_endpoint(
            endpoint="/users",
            method="GET",
            auth_type="api_key"
        )

        assert "api_key" in code
        assert "X-API-Key" in code

    def test_generate_code_for_endpoint_custom_library(self):
        """Test direct generation with custom library."""
        gen = CodeGenerator()

        code = gen.generate_code_for_endpoint(
            endpoint="/users",
            method="GET",
            library=CodeLibrary.HTTPX
        )

        assert "async def" in code
        assert "httpx" in code
        assert "AsyncClient" in code

    def test_generate_code_for_endpoint_post_method(self):
        """Test direct generation for POST method."""
        gen = CodeGenerator()

        code = gen.generate_code_for_endpoint(
            endpoint="/users",
            method="POST",
            description="Create a new user"
        )

        assert "def post_users(" in code
        assert "data:" in code or "data :" in code
        assert "requests.post" in code

    def test_get_supported_libraries(self):
        """Test getting list of supported libraries."""
        gen = CodeGenerator()

        libraries = gen.get_supported_libraries()

        assert CodeLibrary.REQUESTS in libraries
        assert CodeLibrary.HTTPX in libraries
        assert CodeLibrary.AIOHTTP in libraries
        assert len(libraries) == 3

    def test_get_template_info_requests_get(self):
        """Test getting template info for requests GET."""
        gen = CodeGenerator()

        info = gen.get_template_info(CodeLibrary.REQUESTS, "GET")

        assert info["library"] == CodeLibrary.REQUESTS
        assert info["method"] == "GET"
        assert info["template_name"] == "python/requests_get.py.jinja2"
        assert "requests_get" in info["template_path"]

    def test_get_template_info_requests_post(self):
        """Test getting template info for requests POST."""
        gen = CodeGenerator()

        info = gen.get_template_info(CodeLibrary.REQUESTS, "POST")

        assert info["library"] == CodeLibrary.REQUESTS
        assert info["method"] == "POST"
        assert info["template_name"] == "python/requests_post.py.jinja2"

    def test_get_template_info_httpx(self):
        """Test getting template info for httpx."""
        gen = CodeGenerator()

        info = gen.get_template_info(CodeLibrary.HTTPX, "GET")

        assert info["library"] == CodeLibrary.HTTPX
        assert info["template_name"] == "python/httpx_async.py.jinja2"

    def test_validation_enabled_by_default(self):
        """Test that validation is enabled by default."""
        gen = CodeGenerator()
        assert gen.validate_syntax is True

    def test_validation_can_be_disabled(self):
        """Test that validation can be disabled."""
        gen = CodeGenerator(validate_syntax=False)
        assert gen.validate_syntax is False

    def test_retry_disabled_by_default(self):
        """Test that retry is disabled by default."""
        gen = CodeGenerator()
        assert gen.add_retry is False

    def test_retry_can_be_enabled(self):
        """Test that retry can be enabled."""
        gen = CodeGenerator(add_retry=True)
        assert gen.add_retry is True

    def test_code_generation_with_validation_and_retry(self):
        """Test full code generation with both validation and retry enabled."""
        gen = CodeGenerator(validate_syntax=True, add_retry=True)

        code = gen.generate_code_for_endpoint(
            endpoint="/users",
            method="GET"
        )

        # Should have retry decorator (GET is idempotent)
        assert "@retry" in code
        assert "from tenacity import" in code

        # Should be valid Python
        import ast
        try:
            ast.parse(code)
            is_valid = True
        except:
            is_valid = False

        assert is_valid

    def test_format_code_with_complex_structure(self):
        """Test code formatting with complex nested structure."""
        gen = CodeGenerator()

        complex_code = """
def outer():


    def inner():



        return True


    return inner()


"""
        formatted = gen._format_code(complex_code)

        # Should not have triple newlines
        assert '\n\n\n' not in formatted
        # Should end with single newline
        assert formatted.endswith('\n')
        assert not formatted.endswith('\n\n')

    def test_retry_decorator_preserves_existing_tenacity_import(self):
        """Test that retry decorator doesn't duplicate tenacity import."""
        gen = CodeGenerator(add_retry=True)

        code_with_import = """from tenacity import retry
import requests

def get_users():
    return requests.get("/users")
"""
        result = gen._add_retry_decorator(code_with_import, "GET")

        # Count occurrences of tenacity import
        import_count = result.count("from tenacity import")

        # Should only have one import statement
        assert import_count == 1

    def test_generate_code_for_endpoint_no_description_uses_default(self):
        """Test that missing description gets default value."""
        gen = CodeGenerator()

        code = gen.generate_code_for_endpoint(
            endpoint="/test",
            method="GET",
            description=""  # Empty description
        )

        # Should have default description format
        assert "GET /test" in code

    def test_code_snippet_includes_validation_metadata(self):
        """Test that generated code snippet includes validation info."""
        from unittest.mock import Mock
        import json

        mock_llm = Mock()
        endpoint_details = {
            "endpoint": "/test",
            "method": "GET",
            "description": "Test",
            "path_params": [],
            "query_params": [],
            "request_body": {"example": {}},
            "auth_type": "none",
            "auth_details": {}
        }
        mock_llm.generate.return_value = json.dumps(endpoint_details)

        gen = CodeGenerator(llm_client=mock_llm, validate_syntax=True)

        state = {
            "query": "test",
            "retrieved_documents": [
                {"content": "test", "metadata": {}, "score": 0.9, "doc_id": "doc1"}
            ]
        }

        result = gen.process(state)

        # Should have code snippets
        assert "code_snippets" in result
        assert len(result["code_snippets"]) > 0
