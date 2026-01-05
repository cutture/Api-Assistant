"""
Unit tests for Code Generator Agent.
"""

import json
from unittest.mock import Mock, patch

import pytest

from src.agents.code_agent import CodeGenerator, CodeLibrary
from src.agents.state import (
    AgentState,
    AgentType,
    RetrievedDocument,
    create_initial_state,
)
from src.core.llm_client import LLMClient


class TestCodeGenerator:
    """Test suite for Code Generator Agent."""

    @pytest.fixture
    def mock_llm_client(self):
        """Create a mock LLM client."""
        return Mock(spec=LLMClient)

    @pytest.fixture
    def code_gen(self, mock_llm_client):
        """Create CodeGenerator with mocked LLM."""
        return CodeGenerator(llm_client=mock_llm_client)

    def test_agent_properties(self, code_gen):
        """Test agent properties are correct."""
        assert code_gen.name == "code_generator"
        assert code_gen.agent_type == AgentType.CODE_GENERATOR
        assert "code" in code_gen.description.lower()

    def test_process_with_empty_query(self, code_gen):
        """Test processing with empty query returns error."""
        state = create_initial_state("")

        result = code_gen.process(state)

        assert result.get("error") is not None
        assert result["error"]["agent"] == "code_generator"
        assert result["error"]["error_type"] == "missing_input"

    def test_process_without_retrieved_docs(self, code_gen):
        """Test processing without documents returns error."""
        state = create_initial_state("Generate code for POST /users")

        result = code_gen.process(state)

        assert result.get("error") is not None
        assert result["error"]["error_type"] == "missing_context"

    def test_process_generates_code_for_get_request(self, code_gen, mock_llm_client):
        """Test code generation for GET request."""
        # Mock LLM response with endpoint details
        endpoint_details = {
            "endpoint": "/users",
            "method": "GET",
            "description": "List all users",
            "operation_id": "listUsers",
            "path_params": [],
            "query_params": [
                {
                    "name": "limit",
                    "type": "integer",
                    "required": False,
                    "description": "Maximum number of users to return",
                    "default": "10",
                    "example": "20"
                }
            ],
            "request_body": {"required": False, "example": {}},
            "auth_type": "bearer",
            "auth_details": {"header_name": "Authorization"}
        }

        mock_llm_client.generate.return_value = json.dumps(endpoint_details)

        # Create state with retrieved documents
        state = create_initial_state("Generate code for GET /users")
        state["retrieved_documents"] = [
            {
                "content": "GET /users - Returns a list of users. Supports pagination via limit parameter.",
                "metadata": {"endpoint": "/users", "method": "GET"},
                "score": 0.9,
                "doc_id": "doc1"
            }
        ]

        # Process
        result = code_gen.process(state)

        # Verify no errors
        assert result.get("error") is None

        # Verify code snippet created
        assert len(result["code_snippets"]) == 1
        snippet = result["code_snippets"][0]

        assert snippet["language"] == "python"
        assert snippet["library"] == CodeLibrary.REQUESTS
        assert snippet["endpoint"] == "/users"
        assert snippet["method"] == "GET"
        assert "def get_users(" in snippet["code"]
        assert "requests.get" in snippet["code"]
        assert "limit" in snippet["code"]

    def test_process_generates_code_for_post_request(self, code_gen, mock_llm_client):
        """Test code generation for POST request."""
        endpoint_details = {
            "endpoint": "/users",
            "method": "POST",
            "description": "Create a new user",
            "operation_id": "createUser",
            "path_params": [],
            "query_params": [],
            "request_body": {
                "required": True,
                "example": {"name": "John Doe", "email": "john@example.com"}
            },
            "auth_type": "api_key",
            "auth_details": {"header_name": "X-API-Key"}
        }

        mock_llm_client.generate.return_value = json.dumps(endpoint_details)

        state = create_initial_state("Generate code for POST /users")
        state["retrieved_documents"] = [
            {
                "content": "POST /users - Creates a new user with name and email.",
                "metadata": {"endpoint": "/users", "method": "POST"},
                "score": 0.95,
                "doc_id": "doc1"
            }
        ]

        result = code_gen.process(state)

        assert result.get("error") is None
        snippet = result["code_snippets"][0]

        assert snippet["method"] == "POST"
        assert "def post_users(" in snippet["code"]
        assert "requests.post" in snippet["code"]
        assert "data" in snippet["code"]
        assert "X-API-Key" in snippet["code"]

    def test_process_with_path_parameters(self, code_gen, mock_llm_client):
        """Test code generation with path parameters."""
        endpoint_details = {
            "endpoint": "/users/{user_id}",
            "method": "GET",
            "description": "Get user by ID",
            "operation_id": "getUser",
            "path_params": [
                {
                    "name": "user_id",
                    "type": "string",
                    "description": "User identifier",
                    "example": "'user123'"
                }
            ],
            "query_params": [],
            "request_body": {"required": False, "example": {}},
            "auth_type": "none",
            "auth_details": {}
        }

        mock_llm_client.generate.return_value = json.dumps(endpoint_details)

        state = create_initial_state("Get user by ID")
        state["retrieved_documents"] = [
            {
                "content": "GET /users/{user_id} - Returns user details.",
                "metadata": {},
                "score": 0.9,
                "doc_id": "doc1"
            }
        ]

        result = code_gen.process(state)

        assert result.get("error") is None
        snippet = result["code_snippets"][0]

        assert "user_id: str" in snippet["code"]
        assert "{user_id}" in snippet["code"]
        assert "def get_users_user_id(" in snippet["code"]

    def test_determine_library_requests(self, code_gen):
        """Test library determination defaults to requests."""
        library = code_gen._determine_library("Generate code for /users")
        assert library == CodeLibrary.REQUESTS

    def test_determine_library_httpx(self, code_gen):
        """Test library determination for httpx."""
        library = code_gen._determine_library("Generate async code using httpx")
        assert library == CodeLibrary.HTTPX

    def test_determine_library_async(self, code_gen):
        """Test library determination for async keyword."""
        library = code_gen._determine_library("Generate async code for /users")
        assert library == CodeLibrary.HTTPX

    def test_generate_function_name_simple(self, code_gen):
        """Test function name generation."""
        name = code_gen._generate_function_name("/users", "GET")
        assert name == "get_users"

    def test_generate_function_name_with_path_params(self, code_gen):
        """Test function name with path parameters."""
        name = code_gen._generate_function_name("/users/{user_id}", "GET")
        assert name == "get_users_user_id"

    def test_generate_function_name_nested_path(self, code_gen):
        """Test function name with nested path."""
        name = code_gen._generate_function_name("/users/{user_id}/posts", "GET")
        assert name == "get_users_user_id_posts"

    def test_generate_function_name_with_hyphens(self, code_gen):
        """Test function name converts hyphens to underscores."""
        name = code_gen._generate_function_name("/user-profiles", "POST")
        assert name == "post_user_profiles"

    def test_map_type_to_python_string(self, code_gen):
        """Test type mapping for string."""
        assert code_gen._map_type_to_python("string") == "str"

    def test_map_type_to_python_integer(self, code_gen):
        """Test type mapping for integer."""
        assert code_gen._map_type_to_python("integer") == "int"

    def test_map_type_to_python_number(self, code_gen):
        """Test type mapping for number."""
        assert code_gen._map_type_to_python("number") == "float"

    def test_map_type_to_python_boolean(self, code_gen):
        """Test type mapping for boolean."""
        assert code_gen._map_type_to_python("boolean") == "bool"

    def test_map_type_to_python_array(self, code_gen):
        """Test type mapping for array."""
        assert code_gen._map_type_to_python("array") == "list"

    def test_map_type_to_python_object(self, code_gen):
        """Test type mapping for object."""
        assert code_gen._map_type_to_python("object") == "dict"

    def test_select_template_requests_get(self, code_gen):
        """Test template selection for requests GET."""
        template = code_gen._select_template("GET", CodeLibrary.REQUESTS)
        assert template == "python/requests_get.py.jinja2"

    def test_select_template_requests_post(self, code_gen):
        """Test template selection for requests POST."""
        template = code_gen._select_template("POST", CodeLibrary.REQUESTS)
        assert template == "python/requests_post.py.jinja2"

    def test_select_template_httpx(self, code_gen):
        """Test template selection for httpx."""
        template = code_gen._select_template("GET", CodeLibrary.HTTPX)
        assert template == "python/httpx_async.py.jinja2"

    def test_prepare_template_vars(self, code_gen):
        """Test template variable preparation."""
        endpoint_details = {
            "endpoint": "/users",
            "method": "GET",
            "description": "List users",
            "path_params": [],
            "query_params": [
                {
                    "name": "page",
                    "type": "integer",
                    "required": False,
                    "description": "Page number",
                    "default": "1",
                    "example": "2"
                }
            ],
            "auth_type": "bearer",
            "auth_details": {"header_name": "Authorization"},
            "request_body": {"example": {}}
        }

        vars = code_gen._prepare_template_vars(endpoint_details)

        assert vars["endpoint"] == "/users"
        assert vars["method"] == "GET"
        assert vars["function_name"] == "get_users"
        assert vars["description"] == "List users"
        assert vars["auth_type"] == "bearer"
        assert len(vars["query_params"]) == 1
        assert vars["query_params"][0]["name"] == "page"
        assert vars["query_params"][0]["python_type"] == "int"

    def test_llm_extraction_fallback(self, code_gen, mock_llm_client):
        """Test error handling when LLM returns invalid JSON."""
        mock_llm_client.generate.return_value = "Not valid JSON response"

        state = create_initial_state("Generate code")
        state["retrieved_documents"] = [
            {"content": "test", "metadata": {}, "score": 0.9, "doc_id": "doc1"}
        ]

        result = code_gen.process(state)

        assert result.get("error") is not None
        assert result["error"]["error_type"] == "generation_error"

    def test_processing_path_updated(self, code_gen, mock_llm_client):
        """Test that processing path is updated."""
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

        mock_llm_client.generate.return_value = json.dumps(endpoint_details)

        state = create_initial_state("test")
        state["retrieved_documents"] = [
            {"content": "test", "metadata": {}, "score": 0.9, "doc_id": "doc1"}
        ]

        state = code_gen(state)  # Use __call__

        assert "code_generator" in state["processing_path"]
        assert state["current_agent"] == "code_generator"

    def test_custom_base_url(self):
        """Test custom base URL configuration."""
        gen = CodeGenerator(base_url="https://custom.api.com")
        assert gen.base_url == "https://custom.api.com"

    def test_custom_default_library(self):
        """Test custom default library configuration."""
        gen = CodeGenerator(default_library=CodeLibrary.HTTPX)
        assert gen.default_library == CodeLibrary.HTTPX

    def test_generated_code_includes_imports(self, code_gen, mock_llm_client):
        """Test that generated code includes necessary imports."""
        endpoint_details = {
            "endpoint": "/test",
            "method": "GET",
            "description": "Test endpoint",
            "path_params": [],
            "query_params": [],
            "request_body": {"example": {}},
            "auth_type": "bearer",
            "auth_details": {}
        }

        mock_llm_client.generate.return_value = json.dumps(endpoint_details)

        state = create_initial_state("Generate code")
        state["retrieved_documents"] = [
            {"content": "test", "metadata": {}, "score": 0.9, "doc_id": "doc1"}
        ]

        result = code_gen.process(state)

        code = result["code_snippets"][0]["code"]
        assert "import requests" in code
        assert "from typing import" in code

    def test_generated_code_includes_docstring(self, code_gen, mock_llm_client):
        """Test that generated code includes docstrings."""
        endpoint_details = {
            "endpoint": "/test",
            "method": "GET",
            "description": "Test endpoint for documentation",
            "path_params": [],
            "query_params": [],
            "request_body": {"example": {}},
            "auth_type": "none",
            "auth_details": {}
        }

        mock_llm_client.generate.return_value = json.dumps(endpoint_details)

        state = create_initial_state("Generate code")
        state["retrieved_documents"] = [
            {"content": "test", "metadata": {}, "score": 0.9, "doc_id": "doc1"}
        ]

        result = code_gen.process(state)

        code = result["code_snippets"][0]["code"]
        assert '"""' in code  # Has docstring
        assert "Test endpoint for documentation" in code

    def test_generated_code_includes_example_usage(self, code_gen, mock_llm_client):
        """Test that generated code includes example usage."""
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

        mock_llm_client.generate.return_value = json.dumps(endpoint_details)

        state = create_initial_state("Generate code")
        state["retrieved_documents"] = [
            {"content": "test", "metadata": {}, "score": 0.9, "doc_id": "doc1"}
        ]

        result = code_gen.process(state)

        code = result["code_snippets"][0]["code"]
        assert 'if __name__ == "__main__"' in code
        assert "Example usage" in code or "example" in code.lower()
