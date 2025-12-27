"""
Postman Collection Parser for API Assistant.

Parses Postman Collection JSON files (v2.0 and v2.1) and extracts:
- Collection metadata (name, description)
- Request definitions (method, URL, headers, body)
- Folder structure
- Authentication details
- Variables and environments
- Response examples

Supports:
- Postman Collection v2.0
- Postman Collection v2.1

Author: API Assistant Team
Date: 2025-12-27
"""

import json
import structlog
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlparse

logger = structlog.get_logger(__name__)


@dataclass
class PostmanVariable:
    """Postman variable definition."""

    key: str
    value: str
    type: str = "default"
    description: Optional[str] = None


@dataclass
class PostmanAuth:
    """Postman authentication configuration."""

    type: str  # basic, bearer, apikey, oauth2, etc.
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PostmanHeader:
    """Postman request header."""

    key: str
    value: str
    description: Optional[str] = None
    disabled: bool = False


@dataclass
class PostmanRequest:
    """Postman request definition."""

    name: str
    method: str
    url: str
    description: Optional[str] = None
    headers: List[PostmanHeader] = field(default_factory=list)
    body: Optional[Dict[str, Any]] = None
    auth: Optional[PostmanAuth] = None
    folder_path: List[str] = field(default_factory=list)


@dataclass
class PostmanResponse:
    """Postman response example."""

    name: str
    status: str
    code: int
    headers: List[PostmanHeader] = field(default_factory=list)
    body: Optional[str] = None


@dataclass
class PostmanCollection:
    """Parsed Postman collection."""

    name: str
    description: Optional[str] = None
    version: str = "2.1.0"
    requests: List[PostmanRequest] = field(default_factory=list)
    variables: List[PostmanVariable] = field(default_factory=list)
    auth: Optional[PostmanAuth] = None


class PostmanParser:
    """Parser for Postman Collection JSON files."""

    def __init__(self):
        """Initialize Postman parser."""
        self.collection = PostmanCollection(name="")
        self.current_folder_path: List[str] = []

    def parse(self, collection_json: Union[str, dict]) -> PostmanCollection:
        """
        Parse Postman collection JSON.

        Args:
            collection_json: Collection as JSON string or dict

        Returns:
            Parsed PostmanCollection

        Raises:
            ValueError: If JSON is invalid or unsupported version
        """
        logger.info("Parsing Postman collection")

        # Parse JSON if string
        if isinstance(collection_json, str):
            try:
                data = json.loads(collection_json)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON: {e}")
        else:
            data = collection_json

        # Validate collection format
        if "info" not in data:
            raise ValueError("Invalid Postman collection: missing 'info' field")

        # Parse collection metadata
        self._parse_info(data.get("info", {}))

        # Parse variables
        if "variable" in data:
            self._parse_variables(data["variable"])

        # Parse auth
        if "auth" in data:
            self.collection.auth = self._parse_auth(data["auth"])

        # Parse items (requests and folders)
        if "item" in data:
            self._parse_items(data["item"], folder_path=[])

        logger.info(
            "Postman collection parsed",
            name=self.collection.name,
            requests=len(self.collection.requests),
            variables=len(self.collection.variables),
        )

        return self.collection

    def _parse_info(self, info: dict):
        """Parse collection info."""
        self.collection.name = info.get("name", "Unnamed Collection")
        self.collection.description = info.get("description", "")

        # Get version
        schema = info.get("schema", "")
        if "v2.1" in schema:
            self.collection.version = "2.1.0"
        elif "v2.0" in schema:
            self.collection.version = "2.0.0"
        else:
            self.collection.version = "unknown"

    def _parse_variables(self, variables: List[dict]):
        """Parse collection variables."""
        for var_data in variables:
            variable = PostmanVariable(
                key=var_data.get("key", ""),
                value=var_data.get("value", ""),
                type=var_data.get("type", "default"),
                description=var_data.get("description"),
            )
            self.collection.variables.append(variable)

    def _parse_auth(self, auth_data: dict) -> Optional[PostmanAuth]:
        """Parse authentication configuration."""
        auth_type = auth_data.get("type")
        if not auth_type:
            return None

        # Extract auth details
        details = {}
        if auth_type in auth_data:
            auth_config = auth_data[auth_type]
            if isinstance(auth_config, list):
                # v2.1 format: list of {key, value} objects
                for item in auth_config:
                    key = item.get("key")
                    value = item.get("value")
                    if key:
                        details[key] = value
            elif isinstance(auth_config, dict):
                # v2.0 format: direct dict
                details = auth_config

        return PostmanAuth(type=auth_type, details=details)

    def _parse_items(self, items: List[dict], folder_path: List[str]):
        """Parse collection items (requests and folders)."""
        for item in items:
            # Check if it's a folder or request
            if "request" in item:
                # It's a request
                request = self._parse_request(item, folder_path)
                if request:
                    self.collection.requests.append(request)
            elif "item" in item:
                # It's a folder
                folder_name = item.get("name", "Unnamed Folder")
                new_folder_path = folder_path + [folder_name]
                self._parse_items(item["item"], new_folder_path)

    def _parse_request(
        self, item: dict, folder_path: List[str]
    ) -> Optional[PostmanRequest]:
        """Parse a single request."""
        request_data = item.get("request")
        if not request_data:
            return None

        # Get request name and description
        name = item.get("name", "Unnamed Request")
        description = item.get("description")

        # Parse method
        if isinstance(request_data, str):
            # Simple string format (rare)
            method = "GET"
            url = request_data
        else:
            method = request_data.get("method", "GET").upper()
            url = self._parse_url(request_data.get("url", ""))

        # Parse headers
        headers = []
        if "header" in request_data:
            for header_data in request_data["header"]:
                header = PostmanHeader(
                    key=header_data.get("key", ""),
                    value=header_data.get("value", ""),
                    description=header_data.get("description"),
                    disabled=header_data.get("disabled", False),
                )
                headers.append(header)

        # Parse body
        body = None
        if "body" in request_data:
            body = request_data["body"]

        # Parse auth (request-level overrides collection-level)
        auth = None
        if "auth" in request_data:
            auth = self._parse_auth(request_data["auth"])

        request = PostmanRequest(
            name=name,
            method=method,
            url=url,
            description=description,
            headers=headers,
            body=body,
            auth=auth,
            folder_path=folder_path,
        )

        return request

    def _parse_url(self, url_data: Union[str, dict]) -> str:
        """Parse URL from various formats."""
        if isinstance(url_data, str):
            return url_data

        # URL object format
        raw_url = url_data.get("raw", "")
        if raw_url:
            return raw_url

        # Build URL from parts
        protocol = url_data.get("protocol", "https")
        host = url_data.get("host", [])
        if isinstance(host, list):
            host = ".".join(host)

        path = url_data.get("path", [])
        if isinstance(path, list):
            path = "/".join(path)

        # Build URL
        url = f"{protocol}://{host}/{path}"

        # Add query params
        query = url_data.get("query", [])
        if query:
            query_str = "&".join(
                f"{q.get('key')}={q.get('value', '')}" for q in query
            )
            url += f"?{query_str}"

        return url

    def to_documents(self) -> List[Dict[str, Any]]:
        """
        Convert Postman collection to vector store documents.

        Returns:
            List of documents with content and metadata
        """
        documents = []

        # Add collection overview document
        collection_content = f"""Postman Collection: {self.collection.name}

Description: {self.collection.description or 'N/A'}
Total Requests: {len(self.collection.requests)}
Version: {self.collection.version}
"""

        # Add variables info
        if self.collection.variables:
            collection_content += "\nVariables:\n"
            for var in self.collection.variables:
                collection_content += f"  - {var.key}: {var.value}\n"

        # Add auth info
        if self.collection.auth:
            collection_content += f"\nAuthentication: {self.collection.auth.type}\n"

        documents.append(
            {
                "content": collection_content,
                "metadata": {
                    "source": "postman",
                    "type": "collection_info",
                    "collection_name": self.collection.name,
                    "version": self.collection.version,
                },
            }
        )

        # Add request documents
        for request in self.collection.requests:
            content = self._format_request_content(request)
            metadata = {
                "source": "postman",
                "type": "request",
                "name": request.name,
                "method": request.method,
                "collection_name": self.collection.name,
            }

            # Add folder path
            if request.folder_path:
                metadata["folder"] = " > ".join(request.folder_path)

            # Add URL info
            parsed_url = urlparse(request.url)
            if parsed_url.netloc:
                metadata["host"] = parsed_url.netloc
            if parsed_url.path:
                metadata["path"] = parsed_url.path

            documents.append({"content": content, "metadata": metadata})

        return documents

    def _format_request_content(self, request: PostmanRequest) -> str:
        """Format request as readable content."""
        lines = []

        # Header
        lines.append(f"Request: {request.name}")
        lines.append(f"Method: {request.method}")
        lines.append(f"URL: {request.url}")

        # Folder path
        if request.folder_path:
            lines.append(f"Folder: {' > '.join(request.folder_path)}")

        # Description
        if request.description:
            lines.append(f"\nDescription:\n{request.description}")

        # Headers
        if request.headers:
            lines.append("\nHeaders:")
            for header in request.headers:
                if not header.disabled:
                    lines.append(f"  {header.key}: {header.value}")

        # Authentication
        if request.auth:
            lines.append(f"\nAuthentication: {request.auth.type}")
            if request.auth.details:
                for key, value in request.auth.details.items():
                    lines.append(f"  {key}: {value}")

        # Body
        if request.body:
            lines.append("\nRequest Body:")
            mode = request.body.get("mode", "none")
            lines.append(f"  Mode: {mode}")

            if mode == "raw":
                raw_body = request.body.get("raw", "")
                # Truncate if too long
                if len(raw_body) > 500:
                    raw_body = raw_body[:500] + "..."
                lines.append(f"  Content: {raw_body}")
            elif mode == "formdata":
                lines.append("  Form Data:")
                for item in request.body.get("formdata", []):
                    key = item.get("key", "")
                    value = item.get("value", "")
                    lines.append(f"    {key}: {value}")
            elif mode == "urlencoded":
                lines.append("  URL Encoded:")
                for item in request.body.get("urlencoded", []):
                    key = item.get("key", "")
                    value = item.get("value", "")
                    lines.append(f"    {key}: {value}")

        return "\n".join(lines)

    def get_request_by_name(self, name: str) -> Optional[PostmanRequest]:
        """Find a request by name."""
        for request in self.collection.requests:
            if request.name == name:
                return request
        return None

    def get_requests_by_method(self, method: str) -> List[PostmanRequest]:
        """Get all requests with a specific HTTP method."""
        method = method.upper()
        return [r for r in self.collection.requests if r.method == method]

    def get_requests_by_folder(self, folder_name: str) -> List[PostmanRequest]:
        """Get all requests in a specific folder."""
        return [
            r for r in self.collection.requests if folder_name in r.folder_path
        ]

    @classmethod
    def parse_file(cls, file_path: str) -> PostmanCollection:
        """
        Parse Postman collection from file.

        Args:
            file_path: Path to Postman collection JSON file

        Returns:
            Parsed PostmanCollection
        """
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        parser = cls()
        return parser.parse(content)
