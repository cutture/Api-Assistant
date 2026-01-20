"""
Tests for FastAPI REST API.

Tests all API endpoints including:
- Health and stats
- Search (vector, hybrid, reranked)
- Filtering
- Query expansion
- Sessions

Note: Document management and faceted search endpoints were removed in Phase 1.
"""

import pytest
from fastapi.testclient import TestClient

from src.api.app import create_app
from src.api.models import (
    FilterOperatorEnum,
    FilterSpec,
    SearchMode,
    SearchRequest,
)


@pytest.fixture(scope="module")
def client():
    """Create test client."""
    app = create_app(enable_hybrid=True, enable_reranker=False, enable_cors=True)
    with TestClient(app) as test_client:
        yield test_client


class TestHealthEndpoints:
    """Test health and stats endpoints."""

    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "healthy"
        assert "version" in data
        assert "features" in data
        assert data["features"]["hybrid_search"] is True
        assert data["features"]["filtering"] is True

    def test_stats(self, client):
        """Test stats endpoint."""
        response = client.get("/stats")

        assert response.status_code == 200
        data = response.json()

        assert "collection" in data
        assert "features" in data
        assert "total_documents" in data["collection"]
        assert "collection_name" in data["collection"]


class TestSearch:
    """Test search endpoints."""

    def test_vector_search(self, client):
        """Test vector search mode returns valid response structure."""
        request = SearchRequest(
            query="user authentication",
            n_results=5,
            mode=SearchMode.VECTOR,
        )

        response = client.post("/search", json=request.model_dump())

        assert response.status_code == 200
        data = response.json()

        assert "results" in data
        assert "total" in data
        assert "query" in data
        assert "mode" in data
        assert data["query"] == "user authentication"
        assert data["mode"] == SearchMode.VECTOR
        # Results may be empty if no documents indexed
        assert isinstance(data["results"], list)

    def test_hybrid_search(self, client):
        """Test hybrid search mode returns valid response structure."""
        request = SearchRequest(
            query="create user",
            n_results=3,
            mode=SearchMode.HYBRID,
        )

        response = client.post("/search", json=request.model_dump())

        assert response.status_code == 200
        data = response.json()

        assert data["mode"] == SearchMode.HYBRID
        assert isinstance(data["results"], list)

    def test_search_with_query_expansion(self, client):
        """Test search with query expansion."""
        request = SearchRequest(
            query="auth",
            n_results=5,
            mode=SearchMode.HYBRID,
            use_query_expansion=True,
        )

        response = client.post("/search", json=request.model_dump())

        assert response.status_code == 200
        data = response.json()

        assert "expanded_query" in data
        assert data["expanded_query"] is not None
        assert isinstance(data["results"], list)

    def test_search_with_diversification(self, client):
        """Test search with result diversification."""
        request = SearchRequest(
            query="api",
            n_results=5,
            mode=SearchMode.HYBRID,
            use_diversification=True,
            diversification_lambda=0.5,
        )

        response = client.post("/search", json=request.model_dump())

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["results"], list)

    def test_search_with_filter(self, client):
        """Test search with metadata filter."""
        # Filter for GET endpoints
        filter_spec = FilterSpec(
            field="method",
            operator=FilterOperatorEnum.EQ,
            value="GET",
        )

        request = SearchRequest(
            query="api",
            n_results=10,
            mode=SearchMode.HYBRID,
            filter=filter_spec,
        )

        response = client.post("/search", json=request.model_dump())

        assert response.status_code == 200
        data = response.json()

        # All results should have method=GET (if any results)
        for result in data["results"]:
            if "method" in result["metadata"]:
                assert result["metadata"]["method"] == "GET"

    def test_search_with_complex_filter(self, client):
        """Test search with complex AND filter."""
        # Filter: method=POST AND category=users
        filter_spec = FilterSpec(
            operator=FilterOperatorEnum.AND,
            filters=[
                FilterSpec(
                    field="method",
                    operator=FilterOperatorEnum.EQ,
                    value="POST",
                ),
                FilterSpec(
                    field="category",
                    operator=FilterOperatorEnum.EQ,
                    value="users",
                ),
            ],
        )

        request = SearchRequest(
            query="api",
            n_results=10,
            mode=SearchMode.HYBRID,
            filter=filter_spec,
        )

        response = client.post("/search", json=request.model_dump())

        assert response.status_code == 200
        data = response.json()

        # All results should match filter (if any results)
        for result in data["results"]:
            if "method" in result["metadata"]:
                assert result["metadata"]["method"] == "POST"
            if "category" in result["metadata"]:
                assert result["metadata"]["category"] == "users"

    def test_search_with_or_filter(self, client):
        """Test search with OR filter."""
        # Filter: method=POST OR method=DELETE
        filter_spec = FilterSpec(
            operator=FilterOperatorEnum.OR,
            filters=[
                FilterSpec(
                    field="method",
                    operator=FilterOperatorEnum.EQ,
                    value="POST",
                ),
                FilterSpec(
                    field="method",
                    operator=FilterOperatorEnum.EQ,
                    value="DELETE",
                ),
            ],
        )

        request = SearchRequest(
            query="api",
            n_results=10,
            mode=SearchMode.HYBRID,
            filter=filter_spec,
        )

        response = client.post("/search", json=request.model_dump())

        assert response.status_code == 200
        data = response.json()

        # All results should be POST or DELETE (if any results)
        for result in data["results"]:
            if "method" in result["metadata"]:
                assert result["metadata"]["method"] in ["POST", "DELETE"]

    def test_search_with_not_filter(self, client):
        """Test search with NOT filter."""
        # Filter: NOT (method=DELETE)
        filter_spec = FilterSpec(
            operator=FilterOperatorEnum.NOT,
            filters=[
                FilterSpec(
                    field="method",
                    operator=FilterOperatorEnum.EQ,
                    value="DELETE",
                )
            ],
        )

        request = SearchRequest(
            query="api",
            n_results=10,
            mode=SearchMode.HYBRID,
            filter=filter_spec,
        )

        response = client.post("/search", json=request.model_dump())

        assert response.status_code == 200
        data = response.json()

        # No results should be DELETE (if any results)
        for result in data["results"]:
            # Only check if method exists in metadata
            if "method" in result["metadata"]:
                assert result["metadata"]["method"] != "DELETE"

    def test_search_empty_query(self, client):
        """Test search with empty query."""
        # Send raw JSON to bypass Pydantic model validation in test
        response = client.post(
            "/search",
            json={
                "query": "",
                "n_results": 5,
                "mode": "hybrid",
            },
        )

        # Should fail validation
        assert response.status_code == 422

    def test_search_invalid_n_results(self, client):
        """Test search with invalid n_results."""
        # Send raw JSON to bypass Pydantic model validation in test
        response = client.post(
            "/search",
            json={
                "query": "test",
                "n_results": 0,
                "mode": "hybrid",
            },
        )

        # Should fail validation
        assert response.status_code == 422


class TestValidation:
    """Test request validation."""

    def test_invalid_filter_operator(self, client):
        """Test invalid filter operator."""
        filter_spec = FilterSpec(
            field="method",
            operator=FilterOperatorEnum.AND,  # AND requires sub-filters
            value="GET",
        )

        request = SearchRequest(
            query="test",
            n_results=5,
            filter=filter_spec,
        )

        response = client.post("/search", json=request.model_dump())

        # Should fail validation
        assert response.status_code == 422

    def test_and_filter_requires_multiple_filters(self, client):
        """Test AND filter with insufficient sub-filters."""
        # Send raw JSON to bypass Pydantic model validation in test
        response = client.post(
            "/search",
            json={
                "query": "test",
                "n_results": 5,
                "filter": {
                    "operator": "and",
                    "filters": [
                        {
                            "field": "method",
                            "operator": "eq",
                            "value": "GET",
                        }
                    ],  # Only 1 filter
                },
            },
        )

        # Should fail validation
        assert response.status_code == 422

    def test_not_filter_requires_single_filter(self, client):
        """Test NOT filter with multiple sub-filters."""
        # Send raw JSON to bypass Pydantic model validation in test
        response = client.post(
            "/search",
            json={
                "query": "test",
                "n_results": 5,
                "filter": {
                    "operator": "not",
                    "filters": [
                        {
                            "field": "method",
                            "operator": "eq",
                            "value": "GET",
                        },
                        {
                            "field": "category",
                            "operator": "eq",
                            "value": "users",
                        },
                    ],  # 2 filters
                },
            },
        )

        # Should fail validation
        assert response.status_code == 422


class TestErrorHandling:
    """Test error handling."""

    def test_internal_error_handling(self, client):
        """Test that internal errors are handled gracefully."""
        # This should trigger an error if vector store is not initialized
        # But the error handler should catch it and return 500

        # Try to search with an invalid mode (should be caught by validation)
        response = client.post(
            "/search",
            json={
                "query": "test",
                "n_results": 5,
                "mode": "invalid_mode",  # Invalid mode
            },
        )

        # Should fail validation
        assert response.status_code == 422
