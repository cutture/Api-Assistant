"""
Base parser interface and data models for API documentation parsing.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class ParsedParameter:
    """Represents an API parameter (path, query, header, body)."""
    
    name: str
    location: str  # path, query, header, body, cookie
    required: bool = False
    param_type: str = "string"
    description: str = ""
    default: Optional[Any] = None
    example: Optional[Any] = None


@dataclass
class ParsedResponse:
    """Represents an API response."""
    
    status_code: str
    description: str = ""
    content_type: str = "application/json"
    schema: Optional[dict[str, Any]] = None
    example: Optional[Any] = None


@dataclass
class ParsedEndpoint:
    """
    Represents a single API endpoint with all its details.
    This is the core unit for RAG chunking.
    """
    
    path: str
    method: str  # GET, POST, PUT, DELETE, PATCH, etc.
    summary: str = ""
    description: str = ""
    operation_id: str = ""
    tags: list[str] = field(default_factory=list)
    parameters: list[ParsedParameter] = field(default_factory=list)
    request_body: Optional[dict[str, Any]] = None
    responses: list[ParsedResponse] = field(default_factory=list)
    security: list[dict[str, Any]] = field(default_factory=list)
    deprecated: bool = False
    
    # For RAG metadata
    source_file: str = ""
    api_title: str = ""
    api_version: str = ""

    def to_chunk_content(self) -> str:
        """
        Convert endpoint to a text chunk suitable for embedding.
        Includes all relevant information in a structured format.
        """
        lines = [
            f"# {self.method.upper()} {self.path}",
            "",
        ]
        
        if self.summary:
            lines.append(f"**Summary**: {self.summary}")
        
        if self.description:
            lines.append(f"\n**Description**: {self.description}")
        
        if self.tags:
            lines.append(f"\n**Tags**: {', '.join(self.tags)}")
        
        # Parameters
        if self.parameters:
            lines.append("\n**Parameters**:")
            for param in self.parameters:
                required = " (required)" if param.required else ""
                lines.append(
                    f"- `{param.name}` ({param.location}, {param.param_type}){required}: "
                    f"{param.description}"
                )
        
        # Request body
        if self.request_body:
            lines.append("\n**Request Body**:")
            lines.append(f"Content-Type: {self.request_body.get('content_type', 'application/json')}")
            if self.request_body.get("schema"):
                lines.append(f"Schema: {self.request_body['schema']}")
        
        # Responses
        if self.responses:
            lines.append("\n**Responses**:")
            for resp in self.responses:
                lines.append(f"- `{resp.status_code}`: {resp.description}")
        
        # Security
        if self.security:
            lines.append("\n**Security**: " + ", ".join(
                list(sec.keys())[0] if sec else "none" 
                for sec in self.security
            ))
        
        if self.deprecated:
            lines.append("\n⚠️ **DEPRECATED**")
        
        return "\n".join(lines)

    def to_metadata(self) -> dict[str, Any]:
        """
        Generate metadata for vector store indexing.
        """
        return {
            "path": self.path,
            "method": self.method.upper(),
            "operation_id": self.operation_id,
            "tags": ",".join(self.tags) if self.tags else "",
            "source_file": self.source_file,
            "api_title": self.api_title,
            "api_version": self.api_version,
            "deprecated": self.deprecated,
            "has_request_body": self.request_body is not None,
            "param_count": len(self.parameters),
            "content_type": "endpoint",
        }


@dataclass
class ParsedDocument:
    """
    Represents a fully parsed API document.
    Contains general info and all endpoints.
    """
    
    title: str
    version: str = ""
    description: str = ""
    base_url: str = ""
    endpoints: list[ParsedEndpoint] = field(default_factory=list)
    schemas: dict[str, Any] = field(default_factory=dict)
    security_schemes: dict[str, Any] = field(default_factory=dict)
    source_file: str = ""
    format_type: str = ""  # openapi, graphql, etc.

    def get_summary_chunk(self) -> str:
        """
        Generate a summary chunk for the entire API.
        Useful for answering high-level questions.
        """
        lines = [
            f"# {self.title}",
            "",
        ]
        
        if self.version:
            lines.append(f"**Version**: {self.version}")
        
        if self.description:
            lines.append(f"\n**Description**: {self.description}")
        
        if self.base_url:
            lines.append(f"\n**Base URL**: {self.base_url}")
        
        # List all endpoints
        lines.append(f"\n**Endpoints** ({len(self.endpoints)} total):")
        
        # Group by tags
        tagged: dict[str, list[ParsedEndpoint]] = {}
        for ep in self.endpoints:
            tag = ep.tags[0] if ep.tags else "Other"
            tagged.setdefault(tag, []).append(ep)
        
        for tag, endpoints in sorted(tagged.items()):
            lines.append(f"\n### {tag}")
            for ep in endpoints:
                summary = f" - {ep.summary}" if ep.summary else ""
                lines.append(f"- `{ep.method.upper()} {ep.path}`{summary}")
        
        # Security schemes
        if self.security_schemes:
            lines.append("\n**Authentication**:")
            for name, scheme in self.security_schemes.items():
                scheme_type = scheme.get("type", "unknown")
                lines.append(f"- {name}: {scheme_type}")
        
        return "\n".join(lines)

    def get_summary_metadata(self) -> dict[str, Any]:
        """Generate metadata for the summary chunk."""
        return {
            "api_title": self.title,
            "api_version": self.version,
            "source_file": self.source_file,
            "format_type": self.format_type,
            "endpoint_count": len(self.endpoints),
            "content_type": "api_summary",
        }


class BaseParser(ABC):
    """
    Abstract base class for API documentation parsers.
    Implement this for different API spec formats.
    """

    @abstractmethod
    def parse(self, content: str, source_file: str = "") -> ParsedDocument:
        """
        Parse API documentation content.

        Args:
            content: Raw content string (JSON, YAML, etc.).
            source_file: Original file path/name for reference.

        Returns:
            ParsedDocument with all extracted information.
        """
        pass

    @abstractmethod
    def can_parse(self, content: str) -> bool:
        """
        Check if this parser can handle the given content.

        Args:
            content: Raw content string.

        Returns:
            True if this parser can handle the format.
        """
        pass

    def parse_file(self, file_path: str) -> ParsedDocument:
        """
        Parse an API spec file.

        Args:
            file_path: Path to the file.

        Returns:
            ParsedDocument with all extracted information.
        """
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        return self.parse(content, source_file=file_path)
