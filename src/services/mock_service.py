"""
Mock Server Service for API mocking.

Provides functionality to create and manage mock API servers
that respond with predefined data for testing and development.
"""

import asyncio
import json
import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Optional

from src.config import settings


class MockStatus(str, Enum):
    """Status of a mock server."""
    STARTING = "starting"
    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"


class HttpMethod(str, Enum):
    """HTTP methods supported by mock endpoints."""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"


@dataclass
class MockEndpoint:
    """Definition of a mock endpoint."""
    method: HttpMethod
    path: str
    response_body: Any
    status_code: int = 200
    headers: dict[str, str] = field(default_factory=dict)
    delay_ms: int = 0  # Simulated latency
    description: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "method": self.method.value,
            "path": self.path,
            "response_body": self.response_body,
            "status_code": self.status_code,
            "headers": self.headers,
            "delay_ms": self.delay_ms,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "MockEndpoint":
        return cls(
            method=HttpMethod(data["method"]),
            path=data["path"],
            response_body=data.get("response_body", {}),
            status_code=data.get("status_code", 200),
            headers=data.get("headers", {}),
            delay_ms=data.get("delay_ms", 0),
            description=data.get("description"),
        )


@dataclass
class MockServer:
    """Represents a mock server instance."""
    id: str
    user_id: str
    name: str
    endpoints: list[MockEndpoint]
    status: MockStatus
    port: Optional[int] = None
    url: Optional[str] = None
    session_id: Optional[str] = None
    spec_type: Optional[str] = None  # 'openapi', 'custom'
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    request_count: int = 0
    last_request_at: Optional[datetime] = None
    error_message: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "endpoints": [e.to_dict() for e in self.endpoints],
            "status": self.status.value,
            "port": self.port,
            "url": self.url,
            "session_id": self.session_id,
            "spec_type": self.spec_type,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "request_count": self.request_count,
            "last_request_at": self.last_request_at.isoformat() if self.last_request_at else None,
            "error_message": self.error_message,
        }


@dataclass
class MockRequestLog:
    """Log entry for a request to a mock server."""
    mock_id: str
    timestamp: datetime
    method: str
    path: str
    query_params: dict
    headers: dict
    body: Optional[str]
    response_status: int
    response_time_ms: int

    def to_dict(self) -> dict:
        return {
            "mock_id": self.mock_id,
            "timestamp": self.timestamp.isoformat(),
            "method": self.method,
            "path": self.path,
            "query_params": self.query_params,
            "headers": self.headers,
            "body": self.body,
            "response_status": self.response_status,
            "response_time_ms": self.response_time_ms,
        }


class MockService:
    """Service for managing mock API servers."""

    def __init__(self):
        self._mocks: dict[str, MockServer] = {}
        self._request_logs: dict[str, list[MockRequestLog]] = {}
        self._processes: dict[str, asyncio.subprocess.Process] = {}
        self._port_range = range(9000, 9100)
        self._used_ports: set[int] = set()
        self._default_expiry_minutes = getattr(settings, 'MOCK_EXPIRY_MINUTES', 60)
        self._max_concurrent = getattr(settings, 'MOCK_MAX_CONCURRENT', 10)
        self._base_url = getattr(settings, 'MOCK_BASE_URL', 'http://localhost')

    async def create_mock(
        self,
        user_id: str,
        name: str,
        endpoints: list[dict],
        session_id: Optional[str] = None,
        spec_type: Optional[str] = None,
        expiry_minutes: Optional[int] = None,
    ) -> MockServer:
        """
        Create a new mock server.

        Args:
            user_id: ID of the user creating the mock
            name: Name for the mock server
            endpoints: List of endpoint definitions
            session_id: Optional session ID to link the mock to
            spec_type: Type of spec used ('openapi', 'custom')
            expiry_minutes: Minutes until the mock expires

        Returns:
            MockServer instance
        """
        # Check concurrent limit
        user_mocks = [m for m in self._mocks.values()
                      if m.user_id == user_id and m.status == MockStatus.RUNNING]
        if len(user_mocks) >= self._max_concurrent:
            raise ValueError(f"Maximum concurrent mocks ({self._max_concurrent}) reached")

        mock_id = str(uuid.uuid4())
        port = self._allocate_port()
        expiry = expiry_minutes or self._default_expiry_minutes

        mock_endpoints = [MockEndpoint.from_dict(e) for e in endpoints]

        mock = MockServer(
            id=mock_id,
            user_id=user_id,
            name=name,
            endpoints=mock_endpoints,
            status=MockStatus.STARTING,
            port=port,
            url=f"{self._base_url}:{port}",
            session_id=session_id,
            spec_type=spec_type,
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(minutes=expiry),
        )

        self._mocks[mock_id] = mock
        self._request_logs[mock_id] = []

        # Start the mock server
        try:
            await self._start_mock_server(mock)
            mock.status = MockStatus.RUNNING
        except Exception as e:
            mock.status = MockStatus.ERROR
            mock.error_message = str(e)
            self._release_port(port)

        return mock

    async def _start_mock_server(self, mock: MockServer) -> None:
        """Start the mock server process."""
        # Generate a simple Python mock server script
        server_code = self._generate_mock_server_code(mock)

        # For now, we'll just store the configuration
        # In production, this would start an actual server process
        # The mock endpoints can be served by the main FastAPI app
        # or by spawning a subprocess

        # Simulate startup time
        await asyncio.sleep(0.1)

    def _generate_mock_server_code(self, mock: MockServer) -> str:
        """Generate Python code for a mock server."""
        endpoints_json = json.dumps([e.to_dict() for e in mock.endpoints], indent=2)

        return f'''
import asyncio
from aiohttp import web

ENDPOINTS = {endpoints_json}

async def handle_request(request):
    method = request.method
    path = request.path

    for endpoint in ENDPOINTS:
        if endpoint["method"] == method and endpoint["path"] == path:
            if endpoint.get("delay_ms", 0) > 0:
                await asyncio.sleep(endpoint["delay_ms"] / 1000)

            headers = endpoint.get("headers", {{}})
            headers["Content-Type"] = headers.get("Content-Type", "application/json")

            body = endpoint["response_body"]
            if isinstance(body, dict):
                import json
                body = json.dumps(body)

            return web.Response(
                status=endpoint.get("status_code", 200),
                text=body,
                headers=headers
            )

    return web.Response(status=404, text="Not Found")

app = web.Application()
app.router.add_route("*", "/{{path:.*}}", handle_request)

if __name__ == "__main__":
    web.run_app(app, port={mock.port})
'''

    def _allocate_port(self) -> int:
        """Allocate an available port."""
        for port in self._port_range:
            if port not in self._used_ports:
                self._used_ports.add(port)
                return port
        raise ValueError("No available ports")

    def _release_port(self, port: int) -> None:
        """Release a port back to the pool."""
        self._used_ports.discard(port)

    async def get_mock(self, mock_id: str) -> Optional[MockServer]:
        """Get a mock server by ID."""
        return self._mocks.get(mock_id)

    async def get_user_mocks(self, user_id: str) -> list[MockServer]:
        """Get all mock servers for a user."""
        return [m for m in self._mocks.values() if m.user_id == user_id]

    async def update_mock(
        self,
        mock_id: str,
        endpoints: Optional[list[dict]] = None,
        name: Optional[str] = None,
    ) -> Optional[MockServer]:
        """Update a mock server's endpoints or name."""
        mock = self._mocks.get(mock_id)
        if not mock:
            return None

        if name:
            mock.name = name

        if endpoints:
            mock.endpoints = [MockEndpoint.from_dict(e) for e in endpoints]

        return mock

    async def stop_mock(self, mock_id: str) -> bool:
        """Stop a mock server."""
        mock = self._mocks.get(mock_id)
        if not mock:
            return False

        if mock_id in self._processes:
            process = self._processes[mock_id]
            process.terminate()
            await process.wait()
            del self._processes[mock_id]

        if mock.port:
            self._release_port(mock.port)

        mock.status = MockStatus.STOPPED
        return True

    async def delete_mock(self, mock_id: str) -> bool:
        """Delete a mock server."""
        await self.stop_mock(mock_id)

        if mock_id in self._mocks:
            del self._mocks[mock_id]
        if mock_id in self._request_logs:
            del self._request_logs[mock_id]

        return True

    async def get_request_logs(
        self,
        mock_id: str,
        limit: int = 100,
    ) -> list[MockRequestLog]:
        """Get request logs for a mock server."""
        logs = self._request_logs.get(mock_id, [])
        return logs[-limit:]

    async def log_request(
        self,
        mock_id: str,
        method: str,
        path: str,
        query_params: dict,
        headers: dict,
        body: Optional[str],
        response_status: int,
        response_time_ms: int,
    ) -> None:
        """Log a request to a mock server."""
        mock = self._mocks.get(mock_id)
        if not mock:
            return

        log = MockRequestLog(
            mock_id=mock_id,
            timestamp=datetime.utcnow(),
            method=method,
            path=path,
            query_params=query_params,
            headers=headers,
            body=body,
            response_status=response_status,
            response_time_ms=response_time_ms,
        )

        if mock_id not in self._request_logs:
            self._request_logs[mock_id] = []

        self._request_logs[mock_id].append(log)
        mock.request_count += 1
        mock.last_request_at = datetime.utcnow()

        # Keep only last 1000 logs per mock
        if len(self._request_logs[mock_id]) > 1000:
            self._request_logs[mock_id] = self._request_logs[mock_id][-1000:]

    async def cleanup_expired(self) -> int:
        """Clean up expired mock servers."""
        now = datetime.utcnow()
        expired = [
            mock_id for mock_id, mock in self._mocks.items()
            if mock.expires_at and mock.expires_at < now
        ]

        for mock_id in expired:
            await self.delete_mock(mock_id)

        return len(expired)

    def get_stats(self) -> dict:
        """Get mock service statistics."""
        total = len(self._mocks)
        running = sum(1 for m in self._mocks.values() if m.status == MockStatus.RUNNING)
        total_requests = sum(m.request_count for m in self._mocks.values())

        return {
            "total_mocks": total,
            "running_mocks": running,
            "stopped_mocks": total - running,
            "total_requests_served": total_requests,
            "used_ports": len(self._used_ports),
            "available_ports": len(self._port_range) - len(self._used_ports),
        }

    @staticmethod
    def generate_from_openapi(spec: dict) -> list[dict]:
        """
        Generate mock endpoints from an OpenAPI specification.

        Args:
            spec: OpenAPI specification dictionary

        Returns:
            List of endpoint definitions
        """
        endpoints = []

        paths = spec.get("paths", {})
        for path, methods in paths.items():
            for method, details in methods.items():
                if method.upper() not in [m.value for m in HttpMethod]:
                    continue

                # Get example response
                responses = details.get("responses", {})
                success_response = responses.get("200", responses.get("201", {}))

                response_body = {}
                if "content" in success_response:
                    content = success_response["content"]
                    if "application/json" in content:
                        schema = content["application/json"].get("schema", {})
                        example = content["application/json"].get("example")
                        if example:
                            response_body = example
                        else:
                            response_body = MockService._generate_example_from_schema(schema)

                endpoint = {
                    "method": method.upper(),
                    "path": path,
                    "response_body": response_body,
                    "status_code": 200,
                    "headers": {"Content-Type": "application/json"},
                    "description": details.get("summary", details.get("description", "")),
                }
                endpoints.append(endpoint)

        return endpoints

    @staticmethod
    def _generate_example_from_schema(schema: dict) -> Any:
        """Generate example data from an OpenAPI schema."""
        if "example" in schema:
            return schema["example"]

        schema_type = schema.get("type", "object")

        if schema_type == "object":
            result = {}
            properties = schema.get("properties", {})
            for prop_name, prop_schema in properties.items():
                result[prop_name] = MockService._generate_example_from_schema(prop_schema)
            return result

        elif schema_type == "array":
            items = schema.get("items", {})
            return [MockService._generate_example_from_schema(items)]

        elif schema_type == "string":
            if schema.get("format") == "email":
                return "user@example.com"
            elif schema.get("format") == "date":
                return "2024-01-01"
            elif schema.get("format") == "date-time":
                return "2024-01-01T00:00:00Z"
            elif schema.get("format") == "uuid":
                return "550e8400-e29b-41d4-a716-446655440000"
            elif schema.get("format") == "uri":
                return "https://example.com"
            elif "enum" in schema:
                return schema["enum"][0]
            return "string"

        elif schema_type == "integer":
            return schema.get("minimum", 0)

        elif schema_type == "number":
            return schema.get("minimum", 0.0)

        elif schema_type == "boolean":
            return True

        return None

    @staticmethod
    def generate_crud_endpoints(
        resource_name: str,
        resource_schema: Optional[dict] = None,
    ) -> list[dict]:
        """
        Generate CRUD endpoints for a resource.

        Args:
            resource_name: Name of the resource (e.g., "users", "products")
            resource_schema: Optional schema for the resource

        Returns:
            List of CRUD endpoint definitions
        """
        # Generate example data
        if resource_schema:
            example = MockService._generate_example_from_schema(resource_schema)
        else:
            example = {
                "id": 1,
                "name": f"Example {resource_name.rstrip('s')}",
                "created_at": "2024-01-01T00:00:00Z",
            }

        base_path = f"/{resource_name}"

        return [
            # GET all
            {
                "method": "GET",
                "path": base_path,
                "response_body": {"data": [example], "total": 1},
                "status_code": 200,
                "description": f"List all {resource_name}",
            },
            # GET one
            {
                "method": "GET",
                "path": f"{base_path}/{{id}}",
                "response_body": example,
                "status_code": 200,
                "description": f"Get a {resource_name.rstrip('s')} by ID",
            },
            # POST
            {
                "method": "POST",
                "path": base_path,
                "response_body": example,
                "status_code": 201,
                "description": f"Create a new {resource_name.rstrip('s')}",
            },
            # PUT
            {
                "method": "PUT",
                "path": f"{base_path}/{{id}}",
                "response_body": example,
                "status_code": 200,
                "description": f"Update a {resource_name.rstrip('s')}",
            },
            # DELETE
            {
                "method": "DELETE",
                "path": f"{base_path}/{{id}}",
                "response_body": {"deleted": True},
                "status_code": 200,
                "description": f"Delete a {resource_name.rstrip('s')}",
            },
        ]


# Singleton instance
_mock_service: Optional[MockService] = None


def get_mock_service() -> MockService:
    """Get or create the mock service singleton."""
    global _mock_service
    if _mock_service is None:
        _mock_service = MockService()
    return _mock_service
