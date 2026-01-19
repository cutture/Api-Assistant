"""
Mock Server API router.

Provides endpoints for creating and managing mock API servers.
"""

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from src.api.auth import get_current_user_optional
from src.services.mock_service import (
    MockService,
    MockStatus,
    get_mock_service,
)


router = APIRouter(prefix="/mocks", tags=["mocks"])


class EndpointDefinition(BaseModel):
    """Definition of a mock endpoint."""
    method: str = Field(..., description="HTTP method (GET, POST, PUT, DELETE, etc.)")
    path: str = Field(..., description="URL path for the endpoint")
    response_body: Any = Field(..., description="Response body to return")
    status_code: int = Field(200, description="HTTP status code to return")
    headers: dict[str, str] = Field(default_factory=dict, description="Response headers")
    delay_ms: int = Field(0, description="Simulated latency in milliseconds")
    description: Optional[str] = Field(None, description="Description of the endpoint")


class CreateMockRequest(BaseModel):
    """Request to create a new mock server."""
    name: str = Field(..., description="Name for the mock server")
    endpoints: list[EndpointDefinition] = Field(..., description="List of endpoints to mock")
    session_id: Optional[str] = Field(None, description="Optional session ID to link to")
    spec_url: Optional[str] = Field(None, description="OpenAPI spec URL to generate from")
    expiry_minutes: Optional[int] = Field(None, description="Minutes until mock expires")


class UpdateMockRequest(BaseModel):
    """Request to update a mock server."""
    name: Optional[str] = Field(None, description="New name for the mock")
    endpoints: Optional[list[EndpointDefinition]] = Field(None, description="New endpoints")


class GenerateCrudRequest(BaseModel):
    """Request to generate CRUD endpoints."""
    resource_name: str = Field(..., description="Name of the resource (e.g., 'users')")
    schema: Optional[dict] = Field(None, description="Optional schema for the resource")


class GenerateFromOpenApiRequest(BaseModel):
    """Request to generate endpoints from OpenAPI spec."""
    spec: dict = Field(..., description="OpenAPI specification")


class MockEndpointResponse(BaseModel):
    """Response model for an endpoint."""
    method: str
    path: str
    response_body: Any
    status_code: int
    headers: dict[str, str]
    delay_ms: int
    description: Optional[str]


class MockServerResponse(BaseModel):
    """Response model for a mock server."""
    id: str
    user_id: str
    name: str
    endpoints: list[MockEndpointResponse]
    status: str
    port: Optional[int]
    url: Optional[str]
    session_id: Optional[str]
    spec_type: Optional[str]
    created_at: str
    expires_at: Optional[str]
    request_count: int
    error_message: Optional[str]


class RequestLogResponse(BaseModel):
    """Response model for a request log entry."""
    mock_id: str
    timestamp: str
    method: str
    path: str
    query_params: dict
    response_status: int
    response_time_ms: int


class MockStatsResponse(BaseModel):
    """Response model for mock service stats."""
    total_mocks: int
    running_mocks: int
    stopped_mocks: int
    total_requests_served: int
    used_ports: int
    available_ports: int


def _mock_to_response(mock) -> MockServerResponse:
    """Convert a MockServer to response model."""
    mock_dict = mock.to_dict()
    return MockServerResponse(
        id=mock_dict["id"],
        user_id=mock_dict["user_id"],
        name=mock_dict["name"],
        endpoints=[MockEndpointResponse(**e) for e in mock_dict["endpoints"]],
        status=mock_dict["status"],
        port=mock_dict["port"],
        url=mock_dict["url"],
        session_id=mock_dict["session_id"],
        spec_type=mock_dict["spec_type"],
        created_at=mock_dict["created_at"],
        expires_at=mock_dict["expires_at"],
        request_count=mock_dict["request_count"],
        error_message=mock_dict["error_message"],
    )


@router.post("", response_model=MockServerResponse)
async def create_mock(
    request: CreateMockRequest,
    user: Optional[dict] = Depends(get_current_user_optional),
    mock_service: MockService = Depends(get_mock_service),
) -> MockServerResponse:
    """
    Create a new mock API server.

    Creates a mock server with the specified endpoints that will respond
    with predefined data. Useful for testing and development.
    """
    user_id = user.get("id", "anonymous") if user else "anonymous"

    try:
        endpoints = [e.model_dump() for e in request.endpoints]
        mock = await mock_service.create_mock(
            user_id=user_id,
            name=request.name,
            endpoints=endpoints,
            session_id=request.session_id,
            expiry_minutes=request.expiry_minutes,
        )
        return _mock_to_response(mock)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create mock: {str(e)}")


@router.get("", response_model=list[MockServerResponse])
async def list_mocks(
    user: Optional[dict] = Depends(get_current_user_optional),
    mock_service: MockService = Depends(get_mock_service),
) -> list[MockServerResponse]:
    """
    List all mock servers for the current user.
    """
    user_id = user.get("id", "anonymous") if user else "anonymous"
    mocks = await mock_service.get_user_mocks(user_id)
    return [_mock_to_response(m) for m in mocks]


@router.get("/stats", response_model=MockStatsResponse)
async def get_mock_stats(
    user: Optional[dict] = Depends(get_current_user_optional),
    mock_service: MockService = Depends(get_mock_service),
) -> MockStatsResponse:
    """
    Get mock service statistics.
    """
    stats = mock_service.get_stats()
    return MockStatsResponse(**stats)


@router.get("/{mock_id}", response_model=MockServerResponse)
async def get_mock(
    mock_id: str,
    user: Optional[dict] = Depends(get_current_user_optional),
    mock_service: MockService = Depends(get_mock_service),
) -> MockServerResponse:
    """
    Get a specific mock server by ID.
    """
    mock = await mock_service.get_mock(mock_id)
    if not mock:
        raise HTTPException(status_code=404, detail="Mock not found")

    user_id = user.get("id", "anonymous") if user else "anonymous"
    if mock.user_id != user_id and mock.user_id != "anonymous":
        raise HTTPException(status_code=403, detail="Access denied")

    return _mock_to_response(mock)


@router.patch("/{mock_id}", response_model=MockServerResponse)
async def update_mock(
    mock_id: str,
    request: UpdateMockRequest,
    user: Optional[dict] = Depends(get_current_user_optional),
    mock_service: MockService = Depends(get_mock_service),
) -> MockServerResponse:
    """
    Update a mock server's endpoints or name.
    """
    mock = await mock_service.get_mock(mock_id)
    if not mock:
        raise HTTPException(status_code=404, detail="Mock not found")

    user_id = user.get("id", "anonymous") if user else "anonymous"
    if mock.user_id != user_id and mock.user_id != "anonymous":
        raise HTTPException(status_code=403, detail="Access denied")

    endpoints = [e.model_dump() for e in request.endpoints] if request.endpoints else None
    updated = await mock_service.update_mock(
        mock_id=mock_id,
        endpoints=endpoints,
        name=request.name,
    )

    if not updated:
        raise HTTPException(status_code=500, detail="Failed to update mock")

    return _mock_to_response(updated)


@router.delete("/{mock_id}")
async def delete_mock(
    mock_id: str,
    user: Optional[dict] = Depends(get_current_user_optional),
    mock_service: MockService = Depends(get_mock_service),
) -> dict:
    """
    Stop and delete a mock server.
    """
    mock = await mock_service.get_mock(mock_id)
    if not mock:
        raise HTTPException(status_code=404, detail="Mock not found")

    user_id = user.get("id", "anonymous") if user else "anonymous"
    if mock.user_id != user_id and mock.user_id != "anonymous":
        raise HTTPException(status_code=403, detail="Access denied")

    success = await mock_service.delete_mock(mock_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete mock")

    return {"deleted": True, "mock_id": mock_id}


@router.post("/{mock_id}/stop")
async def stop_mock(
    mock_id: str,
    user: Optional[dict] = Depends(get_current_user_optional),
    mock_service: MockService = Depends(get_mock_service),
) -> dict:
    """
    Stop a running mock server.
    """
    mock = await mock_service.get_mock(mock_id)
    if not mock:
        raise HTTPException(status_code=404, detail="Mock not found")

    user_id = user.get("id", "anonymous") if user else "anonymous"
    if mock.user_id != user_id and mock.user_id != "anonymous":
        raise HTTPException(status_code=403, detail="Access denied")

    success = await mock_service.stop_mock(mock_id)
    return {"stopped": success, "mock_id": mock_id}


@router.get("/{mock_id}/logs", response_model=list[RequestLogResponse])
async def get_mock_logs(
    mock_id: str,
    limit: int = 100,
    user: Optional[dict] = Depends(get_current_user_optional),
    mock_service: MockService = Depends(get_mock_service),
) -> list[RequestLogResponse]:
    """
    Get request logs for a mock server.
    """
    mock = await mock_service.get_mock(mock_id)
    if not mock:
        raise HTTPException(status_code=404, detail="Mock not found")

    user_id = user.get("id", "anonymous") if user else "anonymous"
    if mock.user_id != user_id and mock.user_id != "anonymous":
        raise HTTPException(status_code=403, detail="Access denied")

    logs = await mock_service.get_request_logs(mock_id, limit=limit)
    return [
        RequestLogResponse(
            mock_id=log.mock_id,
            timestamp=log.timestamp.isoformat(),
            method=log.method,
            path=log.path,
            query_params=log.query_params,
            response_status=log.response_status,
            response_time_ms=log.response_time_ms,
        )
        for log in logs
    ]


@router.post("/generate/crud", response_model=list[EndpointDefinition])
async def generate_crud_endpoints(
    request: GenerateCrudRequest,
    user: Optional[dict] = Depends(get_current_user_optional),
) -> list[EndpointDefinition]:
    """
    Generate CRUD endpoints for a resource.

    Creates standard Create, Read, Update, Delete endpoints for
    the specified resource name.
    """
    endpoints = MockService.generate_crud_endpoints(
        resource_name=request.resource_name,
        resource_schema=request.schema,
    )
    return [EndpointDefinition(**e) for e in endpoints]


@router.post("/generate/openapi", response_model=list[EndpointDefinition])
async def generate_from_openapi(
    request: GenerateFromOpenApiRequest,
    user: Optional[dict] = Depends(get_current_user_optional),
) -> list[EndpointDefinition]:
    """
    Generate mock endpoints from an OpenAPI specification.

    Parses the OpenAPI spec and creates mock endpoints for each
    defined path/operation.
    """
    try:
        endpoints = MockService.generate_from_openapi(request.spec)
        return [EndpointDefinition(**e) for e in endpoints]
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse OpenAPI spec: {str(e)}")


@router.post("/cleanup")
async def cleanup_expired_mocks(
    user: Optional[dict] = Depends(get_current_user_optional),
    mock_service: MockService = Depends(get_mock_service),
) -> dict:
    """
    Clean up expired mock servers.

    Removes all mock servers that have passed their expiration time.
    """
    count = await mock_service.cleanup_expired()
    return {"cleaned_up": count}
