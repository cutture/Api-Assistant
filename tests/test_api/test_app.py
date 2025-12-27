"""
Tests for FastAPI REST API.

Tests all API endpoints including:
- Health and stats
- Document management
- Search (vector, hybrid, reranked)
- Faceted search
- Filtering
- Query expansion
- Result diversification
"""

import pytest
from fastapi.testclient import TestClient

from src.api.app import create_app
from src.api.models import (
    AddDocumentsRequest,
    BulkDeleteRequest,
    Document,
    FacetedSearchRequest,
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


@pytest.fixture(scope="module")
def sample_documents():
    """Sample documents for testing."""
    return [
        Document(
            content="GET /api/users - Retrieve user information",
            metadata={"method": "GET", "category": "users", "version": "v1"},
        ),
        Document(
            content="POST /api/users - Create new user account",
            metadata={"method": "POST", "category": "users", "version": "v1"},
        ),
        Document(
            content="POST /api/auth/login - Authenticate user",
            metadata={"method": "POST", "category": "auth", "version": "v1"},
        ),
        Document(
            content="GET /api/auth/verify - Verify authentication token",
            metadata={"method": "GET", "category": "auth", "version": "v1"},
        ),
        Document(
            content="DELETE /api/users/{id} - Delete user account",
            metadata={"method": "DELETE", "category": "users", "version": "v2"},
        ),
    ]


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


class TestDocumentManagement:
    """Test document management endpoints."""

    def test_add_documents(self, client, sample_documents):
        """Test adding documents."""
        request = AddDocumentsRequest(documents=sample_documents)

        response = client.post("/documents", json=request.model_dump())

        assert response.status_code == 201
        data = response.json()

        assert "document_ids" in data
        assert "count" in data
        assert data["count"] == len(sample_documents)
        assert len(data["document_ids"]) == len(sample_documents)

    def test_get_document(self, client, sample_documents):
        """Test getting a document."""
        # First add a document
        request = AddDocumentsRequest(documents=[sample_documents[0]])
        add_response = client.post("/documents", json=request.model_dump())
        doc_id = add_response.json()["document_ids"][0]

        # Get the document
        response = client.get(f"/documents/{doc_id}")

        assert response.status_code == 200
        data = response.json()

        assert data["id"] == doc_id
        assert data["content"] == sample_documents[0].content
        assert data["metadata"] == sample_documents[0].metadata

    def test_get_nonexistent_document(self, client):
        """Test getting a nonexistent document."""
        response = client.get("/documents/nonexistent-id")

        assert response.status_code == 404
        data = response.json()
        assert "error" in data
        assert "message" in data

    def test_delete_document(self, client, sample_documents):
        """Test deleting a document."""
        # First add a document
        request = AddDocumentsRequest(documents=[sample_documents[0]])
        add_response = client.post("/documents", json=request.model_dump())
        doc_id = add_response.json()["document_ids"][0]

        # Delete the document
        response = client.delete(f"/documents/{doc_id}")

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert doc_id in data["message"]

        # Verify it's deleted
        get_response = client.get(f"/documents/{doc_id}")
        assert get_response.status_code == 404

    def test_delete_nonexistent_document(self, client):
        """Test deleting a nonexistent document."""
        response = client.delete("/documents/nonexistent-id")

        assert response.status_code == 404

    def test_bulk_delete(self, client, sample_documents):
        """Test bulk delete."""
        # Add documents
        request = AddDocumentsRequest(documents=sample_documents[:3])
        add_response = client.post("/documents", json=request.model_dump())
        doc_ids = add_response.json()["document_ids"]

        # Bulk delete (including one non-existent)
        delete_request = BulkDeleteRequest(
            document_ids=doc_ids + ["nonexistent-id"]
        )
        response = client.post(
            "/documents/bulk-delete", json=delete_request.model_dump()
        )

        assert response.status_code == 200
        data = response.json()

        assert data["deleted_count"] == 3
        assert data["not_found_count"] == 1
        assert len(data["document_ids"]) == 3


class TestSearch:
    """Test search endpoints."""

    @pytest.fixture(autouse=True)
    def setup_documents(self, client, sample_documents):
        """Add sample documents before each test."""
        request = AddDocumentsRequest(documents=sample_documents)
        client.post("/documents", json=request.model_dump())

    def test_vector_search(self, client):
        """Test vector search mode."""
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
        assert len(data["results"]) > 0

        # Check result structure
        result = data["results"][0]
        assert "id" in result
        assert "content" in result
        assert "metadata" in result
        assert "score" in result

    def test_hybrid_search(self, client):
        """Test hybrid search mode."""
        request = SearchRequest(
            query="create user",
            n_results=3,
            mode=SearchMode.HYBRID,
        )

        response = client.post("/search", json=request.model_dump())

        assert response.status_code == 200
        data = response.json()

        assert data["mode"] == SearchMode.HYBRID
        assert len(data["results"]) > 0

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
        assert len(data["results"]) > 0

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

        assert len(data["results"]) > 0

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

        # All results should have method=GET
        for result in data["results"]:
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

        # All results should match filter
        for result in data["results"]:
            assert result["metadata"]["method"] == "POST"
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

        # All results should be POST or DELETE
        for result in data["results"]:
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

        # No results should be DELETE
        for result in data["results"]:
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


class TestFacetedSearch:
    """Test faceted search endpoint."""

    @pytest.fixture(autouse=True)
    def setup_documents(self, client, sample_documents):
        """Add sample documents before each test."""
        request = AddDocumentsRequest(documents=sample_documents)
        client.post("/documents", json=request.model_dump())

    def test_faceted_search(self, client):
        """Test basic faceted search."""
        request = FacetedSearchRequest(
            query="api",
            facet_fields=["method", "category"],
            n_results=10,
        )

        response = client.post("/search/faceted", json=request.model_dump())

        assert response.status_code == 200
        data = response.json()

        assert "results" in data
        assert "facets" in data
        assert "total" in data
        assert "query" in data

        # Check facets structure
        assert "method" in data["facets"]
        assert "category" in data["facets"]

        method_facet = data["facets"]["method"]
        assert "field" in method_facet
        assert "values" in method_facet
        assert "total_docs" in method_facet
        assert method_facet["field"] == "method"

        # Check facet values
        assert len(method_facet["values"]) > 0
        facet_value = method_facet["values"][0]
        assert "value" in facet_value
        assert "count" in facet_value
        assert "percentage" in facet_value

    def test_faceted_search_with_filter(self, client):
        """Test faceted search with filter."""
        filter_spec = FilterSpec(
            field="category",
            operator=FilterOperatorEnum.EQ,
            value="users",
        )

        request = FacetedSearchRequest(
            query="api",
            facet_fields=["method", "version"],
            n_results=10,
            filter=filter_spec,
        )

        response = client.post("/search/faceted", json=request.model_dump())

        assert response.status_code == 200
        data = response.json()

        # All results should be in users category
        for result in data["results"]:
            assert result["metadata"]["category"] == "users"

        # Facets should only include users data
        assert "method" in data["facets"]
        assert "version" in data["facets"]

    def test_faceted_search_top_values(self, client):
        """Test faceted search with custom top_facet_values."""
        request = FacetedSearchRequest(
            query="api",
            facet_fields=["method"],
            n_results=10,
            top_facet_values=2,
        )

        response = client.post("/search/faceted", json=request.model_dump())

        assert response.status_code == 200
        data = response.json()

        # Should return at most 2 facet values
        method_facet = data["facets"]["method"]
        assert len(method_facet["values"]) <= 2

    def test_faceted_search_empty_facets(self, client):
        """Test faceted search with no facet fields."""
        # Send raw JSON to bypass Pydantic model validation in test
        response = client.post(
            "/search/faceted",
            json={
                "query": "api",
                "facet_fields": [],
                "n_results": 10,
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
