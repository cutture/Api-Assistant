"""
Tests for Postman Collection Parser.

Tests parsing of Postman collections including:
- Collection metadata
- Requests with various methods
- Folder structures
- Authentication configurations
- Variables
- Headers and body parsing
- Document conversion for vector store

Author: API Assistant Team
Date: 2025-12-27
"""

import json
import pytest
from src.parsers.postman_parser import (
    PostmanParser,
    PostmanCollection,
    PostmanRequest,
    PostmanVariable,
    PostmanAuth,
    PostmanHeader,
)


class TestBasicCollectionParsing:
    """Test parsing basic Postman collections."""

    def test_parse_minimal_collection(self):
        """Test parsing minimal collection."""
        collection_json = {
            "info": {
                "name": "Test API",
                "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
            },
            "item": [],
        }

        parser = PostmanParser()
        result = parser.parse(collection_json)

        assert result.name == "Test API"
        assert result.version == "2.1.0"
        assert len(result.requests) == 0

    def test_parse_collection_with_description(self):
        """Test parsing collection with description."""
        collection_json = {
            "info": {
                "name": "User API",
                "description": "API for managing users",
                "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
            },
            "item": [],
        }

        parser = PostmanParser()
        result = parser.parse(collection_json)

        assert result.name == "User API"
        assert result.description == "API for managing users"

    def test_parse_v2_0_collection(self):
        """Test parsing v2.0 collection."""
        collection_json = {
            "info": {
                "name": "Legacy API",
                "schema": "https://schema.getpostman.com/json/collection/v2.0.0/collection.json",
            },
            "item": [],
        }

        parser = PostmanParser()
        result = parser.parse(collection_json)

        assert result.version == "2.0.0"

    def test_parse_invalid_json_string(self):
        """Test parsing invalid JSON string."""
        invalid_json = "{ invalid json }"

        parser = PostmanParser()
        with pytest.raises(ValueError, match="Invalid JSON"):
            parser.parse(invalid_json)

    def test_parse_missing_info_field(self):
        """Test parsing collection without info field."""
        collection_json = {"item": []}

        parser = PostmanParser()
        with pytest.raises(ValueError, match="missing 'info' field"):
            parser.parse(collection_json)


class TestRequestParsing:
    """Test parsing requests."""

    def test_parse_simple_get_request(self):
        """Test parsing simple GET request."""
        collection_json = {
            "info": {"name": "Test", "schema": "v2.1.0"},
            "item": [
                {
                    "name": "Get Users",
                    "request": {
                        "method": "GET",
                        "url": "https://api.example.com/users",
                    },
                }
            ],
        }

        parser = PostmanParser()
        result = parser.parse(collection_json)

        assert len(result.requests) == 1
        request = result.requests[0]
        assert request.name == "Get Users"
        assert request.method == "GET"
        assert request.url == "https://api.example.com/users"

    def test_parse_post_request_with_description(self):
        """Test parsing POST request with description."""
        collection_json = {
            "info": {"name": "Test", "schema": "v2.1.0"},
            "item": [
                {
                    "name": "Create User",
                    "description": "Creates a new user account",
                    "request": {
                        "method": "POST",
                        "url": "https://api.example.com/users",
                    },
                }
            ],
        }

        parser = PostmanParser()
        result = parser.parse(collection_json)

        request = result.requests[0]
        assert request.name == "Create User"
        assert request.method == "POST"
        assert request.description == "Creates a new user account"

    def test_parse_request_with_headers(self):
        """Test parsing request with headers."""
        collection_json = {
            "info": {"name": "Test", "schema": "v2.1.0"},
            "item": [
                {
                    "name": "API Request",
                    "request": {
                        "method": "GET",
                        "url": "https://api.example.com/data",
                        "header": [
                            {"key": "Authorization", "value": "Bearer token123"},
                            {"key": "Content-Type", "value": "application/json"},
                            {
                                "key": "X-Debug",
                                "value": "true",
                                "disabled": True,
                            },
                        ],
                    },
                }
            ],
        }

        parser = PostmanParser()
        result = parser.parse(collection_json)

        request = result.requests[0]
        assert len(request.headers) == 3

        auth_header = next(h for h in request.headers if h.key == "Authorization")
        assert auth_header.value == "Bearer token123"
        assert auth_header.disabled is False

        debug_header = next(h for h in request.headers if h.key == "X-Debug")
        assert debug_header.disabled is True

    def test_parse_request_with_raw_body(self):
        """Test parsing request with raw body."""
        collection_json = {
            "info": {"name": "Test", "schema": "v2.1.0"},
            "item": [
                {
                    "name": "Create Resource",
                    "request": {
                        "method": "POST",
                        "url": "https://api.example.com/resource",
                        "body": {
                            "mode": "raw",
                            "raw": '{"name": "test", "value": 123}',
                        },
                    },
                }
            ],
        }

        parser = PostmanParser()
        result = parser.parse(collection_json)

        request = result.requests[0]
        assert request.body is not None
        assert request.body["mode"] == "raw"
        assert "name" in request.body["raw"]

    def test_parse_multiple_http_methods(self):
        """Test parsing requests with different HTTP methods."""
        collection_json = {
            "info": {"name": "Test", "schema": "v2.1.0"},
            "item": [
                {
                    "name": "Get",
                    "request": {"method": "GET", "url": "https://api.example.com/resource"},
                },
                {
                    "name": "Post",
                    "request": {"method": "POST", "url": "https://api.example.com/resource"},
                },
                {
                    "name": "Put",
                    "request": {"method": "PUT", "url": "https://api.example.com/resource"},
                },
                {
                    "name": "Delete",
                    "request": {"method": "DELETE", "url": "https://api.example.com/resource"},
                },
            ],
        }

        parser = PostmanParser()
        result = parser.parse(collection_json)

        assert len(result.requests) == 4
        methods = [r.method for r in result.requests]
        assert "GET" in methods
        assert "POST" in methods
        assert "PUT" in methods
        assert "DELETE" in methods


class TestURLParsing:
    """Test parsing of various URL formats."""

    def test_parse_string_url(self):
        """Test parsing simple string URL."""
        url = "https://api.example.com/users"
        parser = PostmanParser()
        result = parser._parse_url(url)
        assert result == url

    def test_parse_url_object_with_raw(self):
        """Test parsing URL object with raw field."""
        url_obj = {"raw": "https://api.example.com/users?page=1&limit=10"}

        parser = PostmanParser()
        result = parser._parse_url(url_obj)
        assert result == "https://api.example.com/users?page=1&limit=10"

    def test_parse_url_object_with_parts(self):
        """Test parsing URL object with separate parts."""
        url_obj = {
            "protocol": "https",
            "host": ["api", "example", "com"],
            "path": ["v1", "users"],
            "query": [
                {"key": "page", "value": "1"},
                {"key": "limit", "value": "10"},
            ],
        }

        parser = PostmanParser()
        result = parser._parse_url(url_obj)

        assert "https://api.example.com" in result
        assert "v1/users" in result
        assert "page=1" in result
        assert "limit=10" in result


class TestFolderStructure:
    """Test parsing folder structures."""

    def test_parse_nested_folders(self):
        """Test parsing requests in nested folders."""
        collection_json = {
            "info": {"name": "Test", "schema": "v2.1.0"},
            "item": [
                {
                    "name": "Users",
                    "item": [
                        {
                            "name": "Get User",
                            "request": {
                                "method": "GET",
                                "url": "https://api.example.com/users",
                            },
                        },
                        {
                            "name": "Authentication",
                            "item": [
                                {
                                    "name": "Login",
                                    "request": {
                                        "method": "POST",
                                        "url": "https://api.example.com/auth/login",
                                    },
                                }
                            ],
                        },
                    ],
                }
            ],
        }

        parser = PostmanParser()
        result = parser.parse(collection_json)

        assert len(result.requests) == 2

        # Check folder paths
        get_user = next(r for r in result.requests if r.name == "Get User")
        assert get_user.folder_path == ["Users"]

        login = next(r for r in result.requests if r.name == "Login")
        assert login.folder_path == ["Users", "Authentication"]

    def test_get_requests_by_folder(self):
        """Test filtering requests by folder."""
        collection_json = {
            "info": {"name": "Test", "schema": "v2.1.0"},
            "item": [
                {
                    "name": "Admin",
                    "item": [
                        {
                            "name": "Admin Request",
                            "request": {
                                "method": "GET",
                                "url": "https://api.example.com/admin",
                            },
                        }
                    ],
                },
                {
                    "name": "Public Request",
                    "request": {
                        "method": "GET",
                        "url": "https://api.example.com/public",
                    },
                },
            ],
        }

        parser = PostmanParser()
        result = parser.parse(collection_json)

        admin_requests = parser.get_requests_by_folder("Admin")
        assert len(admin_requests) == 1
        assert admin_requests[0].name == "Admin Request"


class TestVariables:
    """Test parsing collection variables."""

    def test_parse_variables(self):
        """Test parsing collection variables."""
        collection_json = {
            "info": {"name": "Test", "schema": "v2.1.0"},
            "item": [],
            "variable": [
                {"key": "baseUrl", "value": "https://api.example.com"},
                {"key": "apiKey", "value": "secret123", "type": "secret"},
                {
                    "key": "version",
                    "value": "v1",
                    "description": "API version",
                },
            ],
        }

        parser = PostmanParser()
        result = parser.parse(collection_json)

        assert len(result.variables) == 3

        base_url = next(v for v in result.variables if v.key == "baseUrl")
        assert base_url.value == "https://api.example.com"

        api_key = next(v for v in result.variables if v.key == "apiKey")
        assert api_key.type == "secret"

        version = next(v for v in result.variables if v.key == "version")
        assert version.description == "API version"


class TestAuthentication:
    """Test parsing authentication configurations."""

    def test_parse_collection_level_auth(self):
        """Test parsing collection-level authentication."""
        collection_json = {
            "info": {"name": "Test", "schema": "v2.1.0"},
            "item": [],
            "auth": {
                "type": "bearer",
                "bearer": [{"key": "token", "value": "{{bearerToken}}"}],
            },
        }

        parser = PostmanParser()
        result = parser.parse(collection_json)

        assert result.auth is not None
        assert result.auth.type == "bearer"
        assert "token" in result.auth.details

    def test_parse_request_level_auth(self):
        """Test parsing request-level authentication."""
        collection_json = {
            "info": {"name": "Test", "schema": "v2.1.0"},
            "item": [
                {
                    "name": "Protected Request",
                    "request": {
                        "method": "GET",
                        "url": "https://api.example.com/protected",
                        "auth": {
                            "type": "apikey",
                            "apikey": [
                                {"key": "key", "value": "X-API-Key"},
                                {"key": "value", "value": "secret"},
                            ],
                        },
                    },
                }
            ],
        }

        parser = PostmanParser()
        result = parser.parse(collection_json)

        request = result.requests[0]
        assert request.auth is not None
        assert request.auth.type == "apikey"
        assert "key" in request.auth.details

    def test_parse_basic_auth(self):
        """Test parsing basic authentication."""
        collection_json = {
            "info": {"name": "Test", "schema": "v2.1.0"},
            "item": [],
            "auth": {
                "type": "basic",
                "basic": [
                    {"key": "username", "value": "user"},
                    {"key": "password", "value": "pass"},
                ],
            },
        }

        parser = PostmanParser()
        result = parser.parse(collection_json)

        assert result.auth.type == "basic"
        assert result.auth.details["username"] == "user"
        assert result.auth.details["password"] == "pass"


class TestDocumentConversion:
    """Test conversion to vector store documents."""

    def test_convert_collection_to_documents(self):
        """Test converting collection to documents."""
        collection_json = {
            "info": {
                "name": "User API",
                "description": "API for user management",
                "schema": "v2.1.0",
            },
            "item": [
                {
                    "name": "Get Users",
                    "request": {
                        "method": "GET",
                        "url": "https://api.example.com/users",
                    },
                },
                {
                    "name": "Create User",
                    "request": {
                        "method": "POST",
                        "url": "https://api.example.com/users",
                    },
                },
            ],
        }

        parser = PostmanParser()
        parser.parse(collection_json)
        documents = parser.to_documents()

        # Should have collection info + 2 requests
        assert len(documents) >= 3

        # Check collection document
        collection_doc = next(
            d for d in documents if d["metadata"]["type"] == "collection_info"
        )
        assert "User API" in collection_doc["content"]
        assert collection_doc["metadata"]["source"] == "postman"

        # Check request documents
        request_docs = [d for d in documents if d["metadata"]["type"] == "request"]
        assert len(request_docs) == 2

        get_request = next(d for d in request_docs if d["metadata"]["method"] == "GET")
        assert "Get Users" in get_request["content"]

    def test_document_metadata_structure(self):
        """Test document metadata structure."""
        collection_json = {
            "info": {"name": "Test", "schema": "v2.1.0"},
            "item": [
                {
                    "name": "Users",
                    "item": [
                        {
                            "name": "Get User",
                            "request": {
                                "method": "GET",
                                "url": "https://api.example.com/v1/users",
                            },
                        }
                    ],
                }
            ],
        }

        parser = PostmanParser()
        parser.parse(collection_json)
        documents = parser.to_documents()

        request_doc = next(d for d in documents if d["metadata"]["type"] == "request")
        metadata = request_doc["metadata"]

        assert metadata["source"] == "postman"
        assert metadata["name"] == "Get User"
        assert metadata["method"] == "GET"
        assert metadata["collection_name"] == "Test"
        assert "folder" in metadata
        assert metadata["host"] == "api.example.com"
        assert metadata["path"] == "/v1/users"


class TestHelperMethods:
    """Test helper methods."""

    def test_get_request_by_name(self):
        """Test finding request by name."""
        collection_json = {
            "info": {"name": "Test", "schema": "v2.1.0"},
            "item": [
                {
                    "name": "Find Me",
                    "request": {
                        "method": "GET",
                        "url": "https://api.example.com/test",
                    },
                }
            ],
        }

        parser = PostmanParser()
        parser.parse(collection_json)

        request = parser.get_request_by_name("Find Me")
        assert request is not None
        assert request.name == "Find Me"

        not_found = parser.get_request_by_name("Does Not Exist")
        assert not_found is None

    def test_get_requests_by_method(self):
        """Test filtering requests by HTTP method."""
        collection_json = {
            "info": {"name": "Test", "schema": "v2.1.0"},
            "item": [
                {"name": "R1", "request": {"method": "GET", "url": "https://api.example.com"}},
                {"name": "R2", "request": {"method": "POST", "url": "https://api.example.com"}},
                {"name": "R3", "request": {"method": "GET", "url": "https://api.example.com"}},
            ],
        }

        parser = PostmanParser()
        parser.parse(collection_json)

        get_requests = parser.get_requests_by_method("GET")
        assert len(get_requests) == 2

        post_requests = parser.get_requests_by_method("post")  # Case insensitive
        assert len(post_requests) == 1


class TestRealWorldCollection:
    """Test with realistic Postman collection."""

    def test_parse_realistic_api_collection(self):
        """Test parsing a realistic API collection."""
        collection_json = {
            "info": {
                "name": "E-commerce API",
                "description": "Complete e-commerce platform API",
                "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
            },
            "variable": [
                {"key": "baseUrl", "value": "https://api.ecommerce.com"},
                {"key": "apiKey", "value": "your-api-key"},
            ],
            "auth": {
                "type": "bearer",
                "bearer": [{"key": "token", "value": "{{authToken}}"}],
            },
            "item": [
                {
                    "name": "Products",
                    "item": [
                        {
                            "name": "List Products",
                            "request": {
                                "method": "GET",
                                "url": {
                                    "raw": "{{baseUrl}}/products?page=1&limit=20",
                                    "host": ["{{baseUrl}}"],
                                    "path": ["products"],
                                    "query": [
                                        {"key": "page", "value": "1"},
                                        {"key": "limit", "value": "20"},
                                    ],
                                },
                                "header": [
                                    {"key": "Accept", "value": "application/json"}
                                ],
                            },
                        },
                        {
                            "name": "Create Product",
                            "request": {
                                "method": "POST",
                                "url": "{{baseUrl}}/products",
                                "header": [
                                    {
                                        "key": "Content-Type",
                                        "value": "application/json",
                                    }
                                ],
                                "body": {
                                    "mode": "raw",
                                    "raw": '{"name": "New Product", "price": 29.99}',
                                },
                            },
                        },
                    ],
                },
                {
                    "name": "Orders",
                    "item": [
                        {
                            "name": "Get Orders",
                            "request": {
                                "method": "GET",
                                "url": "{{baseUrl}}/orders",
                            },
                        }
                    ],
                },
            ],
        }

        parser = PostmanParser()
        result = parser.parse(collection_json)

        # Verify collection
        assert result.name == "E-commerce API"
        assert len(result.variables) == 2
        assert result.auth.type == "bearer"

        # Verify requests
        assert len(result.requests) == 3

        # Verify folder structure
        product_requests = parser.get_requests_by_folder("Products")
        assert len(product_requests) == 2

        # Verify specific request
        create_product = parser.get_request_by_name("Create Product")
        assert create_product is not None
        assert create_product.method == "POST"
        assert len(create_product.headers) > 0

        # Verify documents
        documents = parser.to_documents()
        assert len(documents) >= 4  # 1 collection + 3 requests


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
