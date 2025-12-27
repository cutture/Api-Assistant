"""
Unified Format Handler for API Specifications.

Automatically detects and parses different API specification formats:
- OpenAPI (Swagger) 2.0 and 3.x (JSON/YAML)
- GraphQL Schema (.graphql, .gql)
- Postman Collection v2.0 and v2.1 (JSON)

Provides a unified interface for parsing any supported format and
converting to vector store documents.

Author: API Assistant Team
Date: 2025-12-27
"""

import json
import re
import structlog
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from src.parsers.openapi_parser import OpenAPIParser
from src.parsers.graphql_parser import GraphQLParser
from src.parsers.postman_parser import PostmanParser

logger = structlog.get_logger(__name__)


class APIFormat(Enum):
    """Supported API specification formats."""

    OPENAPI = "openapi"
    GRAPHQL = "graphql"
    POSTMAN = "postman"
    UNKNOWN = "unknown"


class FormatDetector:
    """Detects API specification format from content or file."""

    @staticmethod
    def detect_from_content(content: str) -> APIFormat:
        """
        Detect format from content string.

        Args:
            content: API specification content

        Returns:
            Detected APIFormat
        """
        # Try to parse as JSON first
        try:
            data = json.loads(content)
            return FormatDetector._detect_from_json(data)
        except (json.JSONDecodeError, TypeError):
            pass

        # Check for GraphQL schema
        if FormatDetector._is_graphql(content):
            return APIFormat.GRAPHQL

        # Try YAML for OpenAPI
        try:
            import yaml

            data = yaml.safe_load(content)
            if isinstance(data, dict):
                json_format = FormatDetector._detect_from_json(data)
                if json_format != APIFormat.UNKNOWN:
                    return json_format
        except Exception:
            pass

        return APIFormat.UNKNOWN

    @staticmethod
    def _detect_from_json(data: dict) -> APIFormat:
        """Detect format from parsed JSON/YAML dict."""
        # Check for OpenAPI
        if "openapi" in data or "swagger" in data:
            return APIFormat.OPENAPI

        # Check for Postman
        if "info" in data and isinstance(data.get("info"), dict):
            info = data["info"]
            schema = info.get("schema", "")
            if "postman" in str(schema).lower() or "collection" in str(schema).lower():
                return APIFormat.POSTMAN

            # Also check for Postman by presence of 'item' array
            if "item" in data:
                return APIFormat.POSTMAN

        return APIFormat.UNKNOWN

    @staticmethod
    def _is_graphql(content: str) -> bool:
        """Check if content is GraphQL schema."""
        # Look for GraphQL keywords
        graphql_keywords = [
            r"\btype\s+\w+\s*\{",
            r"\binput\s+\w+\s*\{",
            r"\benum\s+\w+\s*\{",
            r"\binterface\s+\w+\s*\{",
            r"\bunion\s+\w+\s*=",
            r"\bscalar\s+\w+",
            r"\btype\s+Query\s*\{",
            r"\btype\s+Mutation\s*\{",
            r"\btype\s+Subscription\s*\{",
        ]

        # Check if at least 2 GraphQL patterns match
        matches = sum(
            1 for pattern in graphql_keywords if re.search(pattern, content)
        )

        return matches >= 2

    @staticmethod
    def detect_from_file(file_path: str) -> APIFormat:
        """
        Detect format from file extension and content.

        Args:
            file_path: Path to API specification file

        Returns:
            Detected APIFormat
        """
        path = Path(file_path)
        extension = path.suffix.lower()

        # Check by extension first
        if extension in [".graphql", ".gql"]:
            return APIFormat.GRAPHQL

        # Read and detect from content
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            return FormatDetector.detect_from_content(content)
        except Exception as e:
            logger.error("Failed to detect format from file", file_path=file_path, error=str(e))
            return APIFormat.UNKNOWN


class UnifiedFormatHandler:
    """
    Unified handler for parsing all supported API specification formats.

    Automatically detects the format and uses the appropriate parser.
    """

    def __init__(self):
        """Initialize unified format handler."""
        self.openapi_parser = OpenAPIParser()
        self.graphql_parser = GraphQLParser()
        self.postman_parser = PostmanParser()
        self.detector = FormatDetector()

    def parse(
        self,
        content: str,
        format_hint: Optional[APIFormat] = None,
        source_file: str = "",
    ) -> Dict[str, Any]:
        """
        Parse API specification content.

        Args:
            content: API specification content
            format_hint: Optional format hint to skip auto-detection
            source_file: Original file path for reference

        Returns:
            Dict with:
                - format: Detected/used format
                - data: Parsed data (format-specific)
                - documents: List of documents for vector store

        Raises:
            ValueError: If format is unsupported or parsing fails
        """
        # Detect format if not provided
        if format_hint is None:
            format_type = self.detector.detect_from_content(content)
        else:
            format_type = format_hint

        logger.info("Parsing API specification", format=format_type.value, source=source_file)

        # Route to appropriate parser
        if format_type == APIFormat.OPENAPI:
            return self._parse_openapi(content, source_file)
        elif format_type == APIFormat.GRAPHQL:
            return self._parse_graphql(content, source_file)
        elif format_type == APIFormat.POSTMAN:
            return self._parse_postman(content, source_file)
        else:
            raise ValueError(f"Unsupported or unknown API specification format")

    def _parse_openapi(self, content: str, source_file: str) -> Dict[str, Any]:
        """Parse OpenAPI specification."""
        parsed_doc = self.openapi_parser.parse(content, source_file)

        # Convert to documents
        documents = []

        # Add summary document
        documents.append(
            {
                "content": parsed_doc.get_summary_chunk(),
                "metadata": parsed_doc.get_summary_metadata(),
            }
        )

        # Add endpoint documents
        for endpoint in parsed_doc.endpoints:
            documents.append(
                {
                    "content": endpoint.to_chunk_content(),
                    "metadata": endpoint.to_metadata(),
                }
            )

        return {
            "format": APIFormat.OPENAPI.value,
            "data": parsed_doc,
            "documents": documents,
            "stats": {
                "total_endpoints": len(parsed_doc.endpoints),
                "api_title": parsed_doc.title,
                "api_version": parsed_doc.version,
            },
        }

    def _parse_graphql(self, content: str, source_file: str) -> Dict[str, Any]:
        """Parse GraphQL schema."""
        schema = self.graphql_parser.parse(content)
        documents = self.graphql_parser.to_documents()

        return {
            "format": APIFormat.GRAPHQL.value,
            "data": schema,
            "documents": documents,
            "stats": {
                "total_types": len(schema.types),
                "total_queries": len(schema.queries),
                "total_mutations": len(schema.mutations),
                "total_subscriptions": len(schema.subscriptions),
            },
        }

    def _parse_postman(self, content: str, source_file: str) -> Dict[str, Any]:
        """Parse Postman collection."""
        collection = self.postman_parser.parse(content)
        documents = self.postman_parser.to_documents()

        return {
            "format": APIFormat.POSTMAN.value,
            "data": collection,
            "documents": documents,
            "stats": {
                "total_requests": len(collection.requests),
                "collection_name": collection.name,
                "collection_version": collection.version,
            },
        }

    def parse_file(
        self, file_path: str, format_hint: Optional[APIFormat] = None
    ) -> Dict[str, Any]:
        """
        Parse API specification file.

        Args:
            file_path: Path to API specification file
            format_hint: Optional format hint

        Returns:
            Parsed result dict (same as parse())
        """
        # Detect format from file if not provided
        if format_hint is None:
            format_type = self.detector.detect_from_file(file_path)
        else:
            format_type = format_hint

        # Read file
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        return self.parse(content, format_hint=format_type, source_file=file_path)

    def parse_multiple(
        self, file_paths: List[str]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Parse multiple API specification files.

        Args:
            file_paths: List of file paths to parse

        Returns:
            Dict with:
                - results: List of successful parse results
                - errors: List of dicts with file_path and error

        """
        results = []
        errors = []

        for file_path in file_paths:
            try:
                result = self.parse_file(file_path)
                results.append(result)
                logger.info("Successfully parsed file", file_path=file_path, format=result["format"])
            except Exception as e:
                error_info = {"file_path": file_path, "error": str(e)}
                errors.append(error_info)
                logger.error("Failed to parse file", file_path=file_path, error=str(e))

        return {"results": results, "errors": errors}

    def get_all_documents(self, file_paths: List[str]) -> List[Dict[str, Any]]:
        """
        Parse multiple files and return all documents combined.

        Args:
            file_paths: List of file paths to parse

        Returns:
            Combined list of all documents from all files
        """
        all_documents = []

        parse_result = self.parse_multiple(file_paths)

        for result in parse_result["results"]:
            all_documents.extend(result["documents"])

        return all_documents

    @staticmethod
    def get_supported_formats() -> List[str]:
        """Get list of supported format names."""
        return [fmt.value for fmt in APIFormat if fmt != APIFormat.UNKNOWN]

    @staticmethod
    def get_format_info() -> Dict[str, Dict[str, Any]]:
        """Get information about supported formats."""
        return {
            "openapi": {
                "name": "OpenAPI (Swagger)",
                "versions": ["2.0", "3.0.x", "3.1.x"],
                "extensions": [".json", ".yaml", ".yml"],
                "description": "REST API specification format",
            },
            "graphql": {
                "name": "GraphQL Schema",
                "versions": ["SDL"],
                "extensions": [".graphql", ".gql"],
                "description": "GraphQL schema definition language",
            },
            "postman": {
                "name": "Postman Collection",
                "versions": ["2.0", "2.1"],
                "extensions": [".json"],
                "description": "Postman API request collections",
            },
        }
