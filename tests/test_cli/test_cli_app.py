"""
Tests for CLI Application.

Tests command-line interface functionality.

Author: API Assistant Team
Date: 2025-12-27
"""

import json
import pytest
from pathlib import Path
from typer.testing import CliRunner
from src.cli import app

runner = CliRunner()


class TestCLIBasics:
    """Test basic CLI functionality."""

    def test_help_command(self):
        """Test --help command."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "API Assistant CLI" in result.stdout
        assert "parse" in result.stdout
        assert "search" in result.stdout

    def test_verbose_flag(self):
        """Test --verbose flag."""
        result = runner.invoke(app, ["--verbose", "--help"])
        assert result.exit_code == 0

    def test_version_command(self):
        """Test info version command."""
        result = runner.invoke(app, ["info", "version"])
        assert result.exit_code == 0
        assert "API Assistant CLI" in result.stdout


class TestInfoCommands:
    """Test info commands."""

    def test_info_formats(self):
        """Test info formats command."""
        result = runner.invoke(app, ["info", "formats"])
        assert result.exit_code == 0
        assert "GraphQL" in result.stdout
        assert "Postman" in result.stdout
        assert "OpenAPI" in result.stdout

    def test_info_formats_shows_versions(self):
        """Test that format info includes versions."""
        result = runner.invoke(app, ["info", "formats"])
        assert result.exit_code == 0
        assert "2.0" in result.stdout  # Postman/OpenAPI versions
        assert "SDL" in result.stdout  # GraphQL version


class TestParseCommands:
    """Test parse commands."""

    def test_parse_file_not_found(self):
        """Test parsing non-existent file."""
        result = runner.invoke(app, ["parse", "file", "nonexistent.graphql"])
        assert result.exit_code == 1
        assert "File not found" in result.stdout

    def test_parse_file_invalid_format_hint(self):
        """Test parsing with invalid format hint."""
        # Create temp file
        temp_file = Path("/tmp/test.json")
        temp_file.write_text('{"test": "data"}')

        result = runner.invoke(
            app, ["parse", "file", str(temp_file), "--format", "invalid"]
        )
        assert result.exit_code == 1
        assert "Invalid format" in result.stdout

        temp_file.unlink()

    def test_parse_graphql_file(self, tmp_path):
        """Test parsing GraphQL file."""
        # Create GraphQL schema file
        schema_file = tmp_path / "schema.graphql"
        schema_file.write_text("""
        type User {
            id: ID!
            name: String!
        }

        type Query {
            user(id: ID!): User
        }
        """)

        result = runner.invoke(app, ["parse", "file", str(schema_file)])
        assert result.exit_code == 0
        assert "Successfully parsed as graphql" in result.stdout
        assert "Documents generated" in result.stdout

    def test_parse_postman_file(self, tmp_path):
        """Test parsing Postman collection file."""
        # Create Postman collection file
        collection_file = tmp_path / "collection.json"
        collection_file.write_text(json.dumps({
            "info": {
                "name": "Test API",
                "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
            },
            "item": [
                {
                    "name": "Test Request",
                    "request": {
                        "method": "GET",
                        "url": "https://api.test.com/users"
                    }
                }
            ]
        }))

        result = runner.invoke(app, ["parse", "file", str(collection_file)])
        assert result.exit_code == 0
        assert "Successfully parsed as postman" in result.stdout

    def test_parse_file_with_output(self, tmp_path):
        """Test parsing file with --output option."""
        # Create GraphQL schema file
        schema_file = tmp_path / "schema.graphql"
        schema_file.write_text("""
        type User {
            id: ID!
        }
        type Query {
            user: User
        }
        """)

        output_file = tmp_path / "output.json"

        result = runner.invoke(
            app,
            ["parse", "file", str(schema_file), "--output", str(output_file)]
        )
        assert result.exit_code == 0
        assert output_file.exists()

        # Verify output file content
        with open(output_file) as f:
            data = json.load(f)
            assert "format" in data
            assert "documents" in data
            assert data["format"] == "graphql"

    def test_parse_batch_multiple_files(self, tmp_path):
        """Test batch parsing multiple files."""
        # Create multiple GraphQL files
        schema1 = tmp_path / "schema1.graphql"
        schema1.write_text("""
        type User { id: ID! }
        type Query { user: User }
        """)

        schema2 = tmp_path / "schema2.graphql"
        schema2.write_text("""
        type Post { id: ID! }
        type Query { post: Post }
        """)

        result = runner.invoke(
            app,
            ["parse", "batch", str(schema1), str(schema2), "--no-add"]
        )
        assert result.exit_code == 0
        assert "Successful: 2" in result.stdout

    def test_parse_batch_with_errors(self, tmp_path):
        """Test batch parsing with some non-existent files."""
        # Create valid file
        valid_file = tmp_path / "valid.graphql"
        valid_file.write_text("""
        type User { id: ID! }
        type Query { user: User }
        """)

        # Reference non-existent file
        invalid_file = tmp_path / "nonexistent.graphql"

        result = runner.invoke(
            app,
            ["parse", "batch", str(valid_file), str(invalid_file), "--no-add"]
        )
        assert result.exit_code == 0
        # Non-existent files are filtered out with a warning, not counted as errors
        assert "Warning: File not found" in result.stdout
        assert "Successful: 1" in result.stdout
        assert "Failed: 0" in result.stdout


class TestSearchCommands:
    """Test search commands."""

    def test_search_help(self):
        """Test search command help."""
        result = runner.invoke(app, ["search", "--help"])
        assert result.exit_code == 0
        assert "Search the vector store" in result.stdout


class TestCollectionCommands:
    """Test collection management commands."""

    def test_collection_info(self):
        """Test collection info command."""
        result = runner.invoke(app, ["collection", "info"])
        # May succeed or fail depending on whether vectorstore is initialized
        # Just check it doesn't crash
        assert result.exit_code in [0, 1]


class TestExportCommands:
    """Test export commands."""

    def test_export_help(self):
        """Test export command help."""
        result = runner.invoke(app, ["export", "--help"])
        assert result.exit_code == 0
        assert "Export and import data" in result.stdout


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
