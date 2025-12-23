"""
OpenAPI (Swagger) specification parser.
Supports OpenAPI 3.x and Swagger 2.0 formats.
"""

import json
from typing import Any, Optional

import structlog
import yaml
from prance import ResolvingParser

from src.parsers.base_parser import (
    BaseParser,
    ParsedDocument,
    ParsedEndpoint,
    ParsedParameter,
    ParsedResponse,
)

logger = structlog.get_logger(__name__)


class OpenAPIParser(BaseParser):
    """
    Parser for OpenAPI 3.x and Swagger 2.0 specifications.
    
    Uses Prance for $ref resolution, ensuring all schemas are
    fully expanded for complete context in RAG chunks.
    """

    def can_parse(self, content: str) -> bool:
        """Check if content is OpenAPI/Swagger format."""
        try:
            # Try JSON first
            try:
                data = json.loads(content)
            except json.JSONDecodeError:
                # Try YAML
                data = yaml.safe_load(content)
            
            # Check for OpenAPI markers
            return (
                "openapi" in data or  # OpenAPI 3.x
                "swagger" in data      # Swagger 2.0
            )
        except Exception:
            return False

    def parse(self, content: str, source_file: str = "") -> ParsedDocument:
        """
        Parse OpenAPI/Swagger specification.

        Args:
            content: Raw JSON or YAML content.
            source_file: Source file path for reference.

        Returns:
            ParsedDocument with all endpoints and metadata.
        """
        logger.info("Parsing OpenAPI specification", source=source_file)

        # Parse and resolve $ref references
        try:
            # Try to use Prance for full resolution
            spec = self._parse_with_prance(content, source_file)
        except Exception as e:
            logger.warning("Prance parsing failed, using basic parser", error=str(e))
            spec = self._basic_parse(content)

        # Determine version
        openapi_version = spec.get("openapi", spec.get("swagger", "unknown"))
        is_v2 = str(openapi_version).startswith("2")

        # Extract basic info
        info = spec.get("info", {})
        title = info.get("title", "Untitled API")
        version = info.get("version", "")
        description = info.get("description", "")

        # Get base URL
        base_url = self._extract_base_url(spec, is_v2)

        # Parse all endpoints
        endpoints = self._parse_endpoints(spec, is_v2, source_file, title, version)

        # Extract schemas
        schemas = self._extract_schemas(spec, is_v2)

        # Extract security schemes
        security_schemes = self._extract_security_schemes(spec, is_v2)

        logger.info(
            "OpenAPI parsing complete",
            title=title,
            endpoint_count=len(endpoints),
            schema_count=len(schemas),
        )

        return ParsedDocument(
            title=title,
            version=version,
            description=description,
            base_url=base_url,
            endpoints=endpoints,
            schemas=schemas,
            security_schemes=security_schemes,
            source_file=source_file,
            format_type="openapi" if not is_v2 else "swagger",
        )

    def _parse_with_prance(self, content: str, source_file: str) -> dict[str, Any]:
        """Parse using Prance for full $ref resolution."""
        # Write to temp file for Prance (it needs a file path)
        import tempfile
        import os

        # Determine file extension
        ext = ".yaml"
        try:
            json.loads(content)
            ext = ".json"
        except json.JSONDecodeError:
            pass

        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=ext,
            delete=False,
            encoding="utf-8"
        ) as f:
            f.write(content)
            temp_path = f.name

        try:
            parser = ResolvingParser(temp_path)
            return parser.specification
        finally:
            os.unlink(temp_path)

    def _basic_parse(self, content: str) -> dict[str, Any]:
        """Basic parsing without $ref resolution."""
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return yaml.safe_load(content)

    def _extract_base_url(self, spec: dict[str, Any], is_v2: bool) -> str:
        """Extract the base URL from the spec."""
        if is_v2:
            # Swagger 2.0
            host = spec.get("host", "")
            base_path = spec.get("basePath", "")
            schemes = spec.get("schemes", ["https"])
            if host:
                return f"{schemes[0]}://{host}{base_path}"
            return base_path
        else:
            # OpenAPI 3.x
            servers = spec.get("servers", [])
            if servers:
                return servers[0].get("url", "")
            return ""

    def _parse_endpoints(
        self,
        spec: dict[str, Any],
        is_v2: bool,
        source_file: str,
        api_title: str,
        api_version: str,
    ) -> list[ParsedEndpoint]:
        """Parse all endpoints from the spec."""
        endpoints = []
        paths = spec.get("paths", {})

        for path, path_item in paths.items():
            if not isinstance(path_item, dict):
                continue

            # Common parameters for all methods in this path
            common_params = path_item.get("parameters", [])

            for method in ["get", "post", "put", "patch", "delete", "head", "options"]:
                if method not in path_item:
                    continue

                operation = path_item[method]
                if not isinstance(operation, dict):
                    continue

                endpoint = self._parse_operation(
                    path=path,
                    method=method,
                    operation=operation,
                    common_params=common_params,
                    spec=spec,
                    is_v2=is_v2,
                    source_file=source_file,
                    api_title=api_title,
                    api_version=api_version,
                )
                endpoints.append(endpoint)

        return endpoints

    def _parse_operation(
        self,
        path: str,
        method: str,
        operation: dict[str, Any],
        common_params: list[dict[str, Any]],
        spec: dict[str, Any],
        is_v2: bool,
        source_file: str,
        api_title: str,
        api_version: str,
    ) -> ParsedEndpoint:
        """Parse a single API operation."""
        # Combine common and operation-specific parameters
        all_params = common_params + operation.get("parameters", [])

        # Parse parameters
        parameters = [
            self._parse_parameter(p, is_v2)
            for p in all_params
            if isinstance(p, dict)
        ]

        # Parse request body (OpenAPI 3.x)
        request_body = None
        if not is_v2 and "requestBody" in operation:
            request_body = self._parse_request_body(operation["requestBody"])
        elif is_v2:
            # In Swagger 2.0, body params are in parameters
            body_params = [p for p in all_params if p.get("in") == "body"]
            if body_params:
                request_body = {
                    "content_type": "application/json",
                    "schema": body_params[0].get("schema", {}),
                    "required": body_params[0].get("required", False),
                }

        # Parse responses
        responses = [
            self._parse_response(code, resp)
            for code, resp in operation.get("responses", {}).items()
            if isinstance(resp, dict)
        ]

        # Get security requirements
        security = operation.get("security", spec.get("security", []))

        return ParsedEndpoint(
            path=path,
            method=method.upper(),
            summary=operation.get("summary", ""),
            description=operation.get("description", ""),
            operation_id=operation.get("operationId", ""),
            tags=operation.get("tags", []),
            parameters=parameters,
            request_body=request_body,
            responses=responses,
            security=security,
            deprecated=operation.get("deprecated", False),
            source_file=source_file,
            api_title=api_title,
            api_version=api_version,
        )

    def _parse_parameter(
        self,
        param: dict[str, Any],
        is_v2: bool,
    ) -> ParsedParameter:
        """Parse a single parameter."""
        # Get type (location differs between v2 and v3)
        if is_v2:
            param_type = param.get("type", "string")
        else:
            schema = param.get("schema", {})
            param_type = schema.get("type", "string")

        return ParsedParameter(
            name=param.get("name", ""),
            location=param.get("in", "query"),
            required=param.get("required", False),
            param_type=param_type,
            description=param.get("description", ""),
            default=param.get("default"),
            example=param.get("example"),
        )

    def _parse_request_body(self, body: dict[str, Any]) -> dict[str, Any]:
        """Parse OpenAPI 3.x request body."""
        content = body.get("content", {})
        
        # Prefer JSON, fall back to first available
        if "application/json" in content:
            media = content["application/json"]
            content_type = "application/json"
        else:
            content_type = next(iter(content.keys()), "application/json")
            media = content.get(content_type, {})

        return {
            "content_type": content_type,
            "schema": media.get("schema", {}),
            "required": body.get("required", False),
            "description": body.get("description", ""),
        }

    def _parse_response(
        self,
        status_code: str,
        response: dict[str, Any],
    ) -> ParsedResponse:
        """Parse a response definition."""
        # Get schema/content
        content = response.get("content", {})
        schema = None
        content_type = "application/json"

        if content:
            if "application/json" in content:
                schema = content["application/json"].get("schema")
            else:
                first_type = next(iter(content.keys()), None)
                if first_type:
                    content_type = first_type
                    schema = content[first_type].get("schema")

        # Swagger 2.0 style
        if not schema and "schema" in response:
            schema = response["schema"]

        return ParsedResponse(
            status_code=str(status_code),
            description=response.get("description", ""),
            content_type=content_type,
            schema=schema,
        )

    def _extract_schemas(
        self,
        spec: dict[str, Any],
        is_v2: bool,
    ) -> dict[str, Any]:
        """Extract all schema definitions."""
        if is_v2:
            return spec.get("definitions", {})
        else:
            components = spec.get("components", {})
            return components.get("schemas", {})

    def _extract_security_schemes(
        self,
        spec: dict[str, Any],
        is_v2: bool,
    ) -> dict[str, Any]:
        """Extract security scheme definitions."""
        if is_v2:
            return spec.get("securityDefinitions", {})
        else:
            components = spec.get("components", {})
            return components.get("securitySchemes", {})
