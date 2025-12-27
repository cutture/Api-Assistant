"""
Tests for Unified Format Handler.

Tests automatic format detection and unified parsing interface.

Author: API Assistant Team
Date: 2025-12-27
"""

import json
import pytest
from src.parsers.format_handler import (
    UnifiedFormatHandler,
    FormatDetector,
    APIFormat,
)


class TestFormatDetection:
    """Test automatic format detection."""

    def test_detect_openapi_json(self):
        """Test detecting OpenAPI from JSON."""
        openapi_content = json.dumps({
            "openapi": "3.0.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {},
        })

        detector = FormatDetector()
        format_type = detector.detect_from_content(openapi_content)
        assert format_type == APIFormat.OPENAPI

    def test_detect_swagger_json(self):
        """Test detecting Swagger 2.0 from JSON."""
        swagger_content = json.dumps({
            "swagger": "2.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {},
        })

        detector = FormatDetector()
        format_type = detector.detect_from_content(swagger_content)
        assert format_type == APIFormat.OPENAPI

    def test_detect_postman_collection(self):
        """Test detecting Postman collection."""
        postman_content = json.dumps({
            "info": {
                "name": "Test Collection",
                "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
            },
            "item": [],
        })

        detector = FormatDetector()
        format_type = detector.detect_from_content(postman_content)
        assert format_type == APIFormat.POSTMAN

    def test_detect_graphql_schema(self):
        """Test detecting GraphQL schema."""
        graphql_content = """
        type Query {
            user(id: ID!): User
        }

        type User {
            id: ID!
            name: String!
        }

        enum Role {
            ADMIN
            USER
        }
        """

        detector = FormatDetector()
        format_type = detector.detect_from_content(graphql_content)
        assert format_type == APIFormat.GRAPHQL

    def test_detect_unknown_format(self):
        """Test detecting unknown format."""
        unknown_content = "This is not a valid API specification"

        detector = FormatDetector()
        format_type = detector.detect_from_content(unknown_content)
        assert format_type == APIFormat.UNKNOWN


class TestUnifiedParsing:
    """Test unified parsing interface."""

    def test_parse_graphql_schema(self):
        """Test parsing GraphQL schema through unified handler."""
        schema = """
        type User {
            id: ID!
            name: String!
        }

        type Query {
            user(id: ID!): User
        }
        """

        handler = UnifiedFormatHandler()
        result = handler.parse(schema)

        assert result["format"] == "graphql"
        assert "data" in result
        assert "documents" in result
        assert len(result["documents"]) > 0

    def test_parse_postman_collection(self):
        """Test parsing Postman collection through unified handler."""
        collection = {
            "info": {"name": "Test API", "schema": "v2.1.0"},
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

        handler = UnifiedFormatHandler()
        result = handler.parse(json.dumps(collection))

        assert result["format"] == "postman"
        assert "data" in result
        assert "documents" in result
        assert result["stats"]["total_requests"] == 1

    def test_parse_with_format_hint(self):
        """Test parsing with explicit format hint."""
        schema = """
        type User {
            id: ID!
        }
        """

        handler = UnifiedFormatHandler()
        result = handler.parse(schema, format_hint=APIFormat.GRAPHQL)

        assert result["format"] == "graphql"

    def test_parse_unsupported_format_raises_error(self):
        """Test that unknown format raises error."""
        invalid_content = "This is not valid"

        handler = UnifiedFormatHandler()
        with pytest.raises(ValueError, match="Unsupported or unknown"):
            handler.parse(invalid_content)


class TestMultipleFileParsing:
    """Test parsing multiple files."""

    def test_parse_multiple_formats(self, tmp_path):
        """Test parsing files of different formats."""
        # Create GraphQL file
        graphql_file = tmp_path / "schema.graphql"
        graphql_file.write_text("""
        type User {
            id: ID!
        }
        type Query {
            user(id: ID!): User
        }
        """)

        # Create Postman file
        postman_file = tmp_path / "collection.json"
        postman_file.write_text(json.dumps({
            "info": {"name": "Test", "schema": "v2.1.0"},
            "item": [
                {
                    "name": "Request",
                    "request": {"method": "GET", "url": "https://example.com"},
                }
            ],
        }))

        handler = UnifiedFormatHandler()
        results = handler.parse_multiple([str(graphql_file), str(postman_file)])

        assert len(results["results"]) == 2
        assert len(results["errors"]) == 0

        formats = [r["format"] for r in results["results"]]
        assert "graphql" in formats
        assert "postman" in formats

    def test_parse_multiple_with_errors(self, tmp_path):
        """Test parsing multiple files with some errors."""
        # Create valid file
        valid_file = tmp_path / "schema.graphql"
        valid_file.write_text("type User { id: ID! }")

        # Create invalid file
        invalid_file = tmp_path / "invalid.txt"
        invalid_file.write_text("Not a valid spec")

        handler = UnifiedFormatHandler()
        results = handler.parse_multiple([str(valid_file), str(invalid_file)])

        assert len(results["results"]) == 1
        assert len(results["errors"]) == 1
        assert results["errors"][0]["file_path"] == str(invalid_file)

    def test_get_all_documents(self, tmp_path):
        """Test getting all documents from multiple files."""
        # Create multiple files
        file1 = tmp_path / "schema1.graphql"
        file1.write_text("""
        type User { id: ID! }
        type Query { user: User }
        """)

        file2 = tmp_path / "schema2.graphql"
        file2.write_text("""
        type Post { id: ID! }
        type Mutation { createPost: Post }
        """)

        handler = UnifiedFormatHandler()
        all_docs = handler.get_all_documents([str(file1), str(file2)])

        # Should have documents from both files
        assert len(all_docs) > 0

        # All should have source metadata
        for doc in all_docs:
            assert "content" in doc
            assert "metadata" in doc
            assert doc["metadata"]["source"] == "graphql"


class TestFormatInfo:
    """Test format information methods."""

    def test_get_supported_formats(self):
        """Test getting list of supported formats."""
        formats = UnifiedFormatHandler.get_supported_formats()

        assert "openapi" in formats
        assert "graphql" in formats
        assert "postman" in formats
        assert "unknown" not in formats

    def test_get_format_info(self):
        """Test getting detailed format information."""
        info = UnifiedFormatHandler.get_format_info()

        assert "openapi" in info
        assert "graphql" in info
        assert "postman" in info

        # Check OpenAPI info
        openapi_info = info["openapi"]
        assert "name" in openapi_info
        assert "versions" in openapi_info
        assert "extensions" in openapi_info
        assert ".json" in openapi_info["extensions"]


class TestDocumentStructure:
    """Test that all parsers produce consistent document structure."""

    def test_graphql_document_structure(self):
        """Test GraphQL produces valid document structure."""
        schema = """
        type User {
            id: ID!
            name: String!
        }

        type Query {
            user(id: ID!): User
        }
        """

        handler = UnifiedFormatHandler()
        result = handler.parse(schema)

        for doc in result["documents"]:
            assert "content" in doc
            assert "metadata" in doc
            assert isinstance(doc["content"], str)
            assert isinstance(doc["metadata"], dict)
            assert "source" in doc["metadata"]
            assert doc["metadata"]["source"] == "graphql"

    def test_postman_document_structure(self):
        """Test Postman produces valid document structure."""
        collection = {
            "info": {"name": "Test", "schema": "v2.1.0"},
            "item": [
                {
                    "name": "Request",
                    "request": {"method": "GET", "url": "https://example.com"},
                }
            ],
        }

        handler = UnifiedFormatHandler()
        result = handler.parse(json.dumps(collection))

        for doc in result["documents"]:
            assert "content" in doc
            assert "metadata" in doc
            assert isinstance(doc["content"], str)
            assert isinstance(doc["metadata"], dict)
            assert "source" in doc["metadata"]
            assert doc["metadata"]["source"] == "postman"


class TestStatsGeneration:
    """Test statistics generation for different formats."""

    def test_graphql_stats(self):
        """Test GraphQL statistics."""
        schema = """
        type User { id: ID! }
        type Query { user: User }
        type Mutation { createUser: User }
        enum Role { ADMIN, USER }
        """

        handler = UnifiedFormatHandler()
        result = handler.parse(schema)

        stats = result["stats"]
        assert "total_types" in stats
        assert "total_queries" in stats
        assert "total_mutations" in stats
        assert stats["total_types"] >= 2  # User + Role + maybe others

    def test_postman_stats(self):
        """Test Postman statistics."""
        collection = {
            "info": {"name": "My API", "schema": "v2.1.0"},
            "item": [
                {"name": "R1", "request": {"method": "GET", "url": "https://example.com"}},
                {"name": "R2", "request": {"method": "POST", "url": "https://example.com"}},
            ],
        }

        handler = UnifiedFormatHandler()
        result = handler.parse(json.dumps(collection))

        stats = result["stats"]
        assert stats["total_requests"] == 2
        assert stats["collection_name"] == "My API"
        assert "collection_version" in stats


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
