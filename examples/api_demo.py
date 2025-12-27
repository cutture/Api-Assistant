#!/usr/bin/env python3
"""
REST API Demo - Day 26

Demonstrates the API Assistant REST API capabilities.

Shows how to:
- Add and manage documents
- Perform different types of searches
- Use filters
- Use faceted search
- Use query expansion and diversification

Author: API Assistant Team
Date: 2025-12-27
"""

import requests
import time
from typing import Dict, List, Any

# API Base URL
BASE_URL = "http://localhost:8000"


def print_section(title: str):
    """Print section header."""
    print(f"\n{'=' * 90}")
    print(f"{title}")
    print(f"{'=' * 90}")


def print_results(results: List[Dict[str, Any]], title: str):
    """Print search results."""
    print(f"\n{title}")
    print("-" * 90)
    if not results:
        print("No results found.")
        return

    for i, result in enumerate(results, 1):
        metadata = result.get("metadata", {})
        print(f"\n{i}. {result.get('content', 'N/A')[:80]}")
        print(f"   ID: {result.get('id', 'N/A')}")
        print(f"   Score: {result.get('score', 0):.4f}")
        print(f"   Method: {result.get('method', 'N/A')}")
        if metadata:
            print(f"   Metadata: {metadata}")


def main():
    """Run API demo."""
    print_section("REST API DEMO - DAY 26")

    print("\nAPI Assistant REST API demonstrates:")
    print("  - Document management (add, get, delete)")
    print("  - Multiple search modes (vector, hybrid, re-ranked)")
    print("  - Advanced filtering")
    print("  - Faceted search")
    print("  - Query expansion")
    print("  - Result diversification")

    # Test 1: Health Check
    print_section("TEST 1: HEALTH CHECK")

    response = requests.get(f"{BASE_URL}/health")
    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        health = response.json()
        print(f"\nAPI Status: {health['status']}")
        print(f"Version: {health['version']}")
        print("\nAvailable Features:")
        for feature, enabled in health['features'].items():
            status = "✓" if enabled else "✗"
            print(f"  {status} {feature}")
    else:
        print("ERROR: Health check failed!")
        return

    # Test 2: Add Documents
    print_section("TEST 2: ADD DOCUMENTS")

    documents = [
        {
            "content": "GET /api/users - Retrieve user information",
            "metadata": {"method": "GET", "category": "users", "version": "v1", "priority": 1},
        },
        {
            "content": "POST /api/users - Create new user account",
            "metadata": {"method": "POST", "category": "users", "version": "v1", "priority": 2},
        },
        {
            "content": "PUT /api/users/{id} - Update user information",
            "metadata": {"method": "PUT", "category": "users", "version": "v1", "priority": 2},
        },
        {
            "content": "DELETE /api/users/{id} - Delete user account",
            "metadata": {"method": "DELETE", "category": "users", "version": "v2", "priority": 3},
        },
        {
            "content": "POST /api/auth/login - Authenticate user with credentials",
            "metadata": {"method": "POST", "category": "auth", "version": "v1", "priority": 1},
        },
        {
            "content": "GET /api/auth/verify - Verify authentication token",
            "metadata": {"method": "GET", "category": "auth", "version": "v1", "priority": 2},
        },
        {
            "content": "POST /api/auth/oauth - OAuth authentication",
            "metadata": {"method": "POST", "category": "auth", "version": "v2", "priority": 1},
        },
        {
            "content": "POST /api/webhooks - Register webhook for events",
            "metadata": {"method": "POST", "category": "webhooks", "version": "v2", "priority": 3},
        },
        {
            "content": "GET /api/webhooks - List all registered webhooks",
            "metadata": {"method": "GET", "category": "webhooks", "version": "v2", "priority": 2},
        },
        {
            "content": "GET /api/analytics - Retrieve analytics and metrics",
            "metadata": {"method": "GET", "category": "analytics", "version": "v1", "priority": 4},
        },
    ]

    response = requests.post(
        f"{BASE_URL}/documents",
        json={"documents": documents},
    )

    if response.status_code == 201:
        data = response.json()
        print(f"✓ Added {data['count']} documents")
        print(f"Document IDs: {data['document_ids'][:3]}... (showing first 3)")
        doc_ids = data['document_ids']
    else:
        print(f"ERROR: Failed to add documents: {response.text}")
        return

    # Test 3: Get Document
    print_section("TEST 3: GET DOCUMENT")

    doc_id = doc_ids[0]
    response = requests.get(f"{BASE_URL}/documents/{doc_id}")

    if response.status_code == 200:
        doc = response.json()
        print(f"✓ Retrieved document {doc_id}")
        print(f"Content: {doc['content']}")
        print(f"Metadata: {doc['metadata']}")
    else:
        print(f"ERROR: Failed to get document: {response.text}")

    # Test 4: Vector Search
    print_section("TEST 4: VECTOR SEARCH")

    response = requests.post(
        f"{BASE_URL}/search",
        json={
            "query": "user authentication",
            "n_results": 5,
            "mode": "vector",
        },
    )

    if response.status_code == 200:
        data = response.json()
        print(f"✓ Found {data['total']} results")
        print(f"Search Mode: {data['mode']}")
        print_results(data['results'], "Vector Search Results")
    else:
        print(f"ERROR: Search failed: {response.text}")

    # Test 5: Hybrid Search
    print_section("TEST 5: HYBRID SEARCH")

    response = requests.post(
        f"{BASE_URL}/search",
        json={
            "query": "create user account",
            "n_results": 5,
            "mode": "hybrid",
        },
    )

    if response.status_code == 200:
        data = response.json()
        print(f"✓ Found {data['total']} results")
        print(f"Search Mode: {data['mode']}")
        print_results(data['results'], "Hybrid Search Results")
    else:
        print(f"ERROR: Search failed: {response.text}")

    # Test 6: Search with Filter
    print_section("TEST 6: SEARCH WITH FILTER - method='GET'")

    response = requests.post(
        f"{BASE_URL}/search",
        json={
            "query": "api endpoints",
            "n_results": 10,
            "mode": "hybrid",
            "filter": {
                "field": "method",
                "operator": "eq",
                "value": "GET",
            },
        },
    )

    if response.status_code == 200:
        data = response.json()
        print(f"✓ Found {data['total']} GET endpoints")
        print_results(data['results'], "GET Endpoints Only")
    else:
        print(f"ERROR: Search failed: {response.text}")

    # Test 7: Search with Complex Filter
    print_section("TEST 7: COMPLEX FILTER - (POST OR PUT) AND category='users'")

    response = requests.post(
        f"{BASE_URL}/search",
        json={
            "query": "user operations",
            "n_results": 10,
            "mode": "hybrid",
            "filter": {
                "operator": "and",
                "filters": [
                    {
                        "operator": "or",
                        "filters": [
                            {
                                "field": "method",
                                "operator": "eq",
                                "value": "POST",
                            },
                            {
                                "field": "method",
                                "operator": "eq",
                                "value": "PUT",
                            },
                        ],
                    },
                    {
                        "field": "category",
                        "operator": "eq",
                        "value": "users",
                    },
                ],
            },
        },
    )

    if response.status_code == 200:
        data = response.json()
        print(f"✓ Found {data['total']} results matching complex filter")
        print_results(data['results'], "POST/PUT User Endpoints")
    else:
        print(f"ERROR: Search failed: {response.text}")

    # Test 8: Search with Query Expansion
    print_section("TEST 8: SEARCH WITH QUERY EXPANSION")

    response = requests.post(
        f"{BASE_URL}/search",
        json={
            "query": "auth",
            "n_results": 5,
            "mode": "hybrid",
            "use_query_expansion": True,
        },
    )

    if response.status_code == 200:
        data = response.json()
        print(f"✓ Found {data['total']} results")
        print(f"Original Query: {data['query']}")
        print(f"Expanded Query: {data.get('expanded_query', 'N/A')}")
        print_results(data['results'], "Results with Query Expansion")
    else:
        print(f"ERROR: Search failed: {response.text}")

    # Test 9: Search with Diversification
    print_section("TEST 9: SEARCH WITH DIVERSIFICATION")

    response = requests.post(
        f"{BASE_URL}/search",
        json={
            "query": "api",
            "n_results": 8,
            "mode": "hybrid",
            "use_diversification": True,
            "diversification_lambda": 0.5,
        },
    )

    if response.status_code == 200:
        data = response.json()
        print(f"✓ Found {data['total']} diversified results")
        print(f"Diversification Lambda: 0.5 (balanced relevance-diversity)")
        print_results(data['results'], "Diversified Results")
    else:
        print(f"ERROR: Search failed: {response.text}")

    # Test 10: Faceted Search
    print_section("TEST 10: FACETED SEARCH")

    response = requests.post(
        f"{BASE_URL}/search/faceted",
        json={
            "query": "api",
            "facet_fields": ["method", "category", "version"],
            "n_results": 20,
            "top_facet_values": 10,
        },
    )

    if response.status_code == 200:
        data = response.json()
        print(f"✓ Found {data['total']} results")

        print("\nFacet Aggregations:")
        for field_name, facet in data['facets'].items():
            print(f"\n{field_name.upper()} (total: {facet['total_docs']}):")
            for facet_value in facet['values']:
                print(
                    f"  - {facet_value['value']}: {facet_value['count']} "
                    f"({facet_value['percentage']:.1f}%)"
                )

        print_results(data['results'][:5], "Search Results (first 5)")
    else:
        print(f"ERROR: Faceted search failed: {response.text}")

    # Test 11: Faceted Search with Filter
    print_section("TEST 11: FACETED SEARCH + FILTER - category='auth'")

    response = requests.post(
        f"{BASE_URL}/search/faceted",
        json={
            "query": "api",
            "facet_fields": ["method", "version"],
            "n_results": 20,
            "filter": {
                "field": "category",
                "operator": "eq",
                "value": "auth",
            },
        },
    )

    if response.status_code == 200:
        data = response.json()
        print(f"✓ Found {data['total']} auth endpoints")

        print("\nFacet Aggregations (filtered to category='auth'):")
        for field_name, facet in data['facets'].items():
            print(f"\n{field_name.upper()}:")
            for facet_value in facet['values']:
                print(
                    f"  - {facet_value['value']}: {facet_value['count']} "
                    f"({facet_value['percentage']:.1f}%)"
                )

        print_results(data['results'], "Auth Endpoints")
    else:
        print(f"ERROR: Faceted search failed: {response.text}")

    # Test 12: Get Statistics
    print_section("TEST 12: GET STATISTICS")

    response = requests.get(f"{BASE_URL}/stats")

    if response.status_code == 200:
        stats = response.json()
        print(f"✓ Collection: {stats['collection']['collection_name']}")
        print(f"Total Documents: {stats['collection']['total_documents']}")
        print("\nFeatures:")
        for feature, enabled in stats['features'].items():
            status = "✓" if enabled else "✗"
            print(f"  {status} {feature}")
    else:
        print(f"ERROR: Failed to get stats: {response.text}")

    # Test 13: Delete Document
    print_section("TEST 13: DELETE DOCUMENT")

    response = requests.delete(f"{BASE_URL}/documents/{doc_ids[0]}")

    if response.status_code == 200:
        data = response.json()
        print(f"✓ {data['message']}")
    else:
        print(f"ERROR: Failed to delete document: {response.text}")

    # Test 14: Bulk Delete
    print_section("TEST 14: BULK DELETE")

    response = requests.post(
        f"{BASE_URL}/documents/bulk-delete",
        json={"document_ids": doc_ids[1:4]},
    )

    if response.status_code == 200:
        data = response.json()
        print(f"✓ Deleted {data['deleted_count']} documents")
        print(f"Not found: {data['not_found_count']}")
    else:
        print(f"ERROR: Bulk delete failed: {response.text}")

    # Summary
    print_section("DEMO SUMMARY")

    print("\n✅ REST API Features Demonstrated:")
    print("  1. Health check and statistics")
    print("  2. Document management (add, get, delete, bulk delete)")
    print("  3. Vector search")
    print("  4. Hybrid search (BM25 + Vector)")
    print("  5. Simple metadata filtering")
    print("  6. Complex filter combinations (AND, OR)")
    print("  7. Query expansion")
    print("  8. Result diversification")
    print("  9. Faceted search")
    print("  10. Faceted search with filters")

    print("\n📚 API Documentation:")
    print(f"  - Swagger UI: {BASE_URL}/docs")
    print(f"  - ReDoc: {BASE_URL}/redoc")

    print("\n🔗 Example cURL Commands:")
    print(f"""
# Health check
curl {BASE_URL}/health

# Add documents
curl -X POST {BASE_URL}/documents \\
  -H "Content-Type: application/json" \\
  -d '{{"documents": [{{"content": "example", "metadata": {{}}}}'

# Search
curl -X POST {BASE_URL}/search \\
  -H "Content-Type: application/json" \\
  -d '{{"query": "test", "n_results": 5, "mode": "hybrid"}}'

# Faceted search
curl -X POST {BASE_URL}/search/faceted \\
  -H "Content-Type: application/json" \\
  -d '{{"query": "api", "facet_fields": ["category", "method"]}}'
    """)

    print("\n" + "=" * 90)
    print("Demo completed!")
    print("=" * 90)


if __name__ == "__main__":
    print("\nNOTE: This demo requires the API server to be running.")
    print("Start the server with: uvicorn src.api.app:app --reload")
    print("Or: python -m src.api.app\n")

    try:
        main()
    except requests.exceptions.ConnectionError:
        print("\nERROR: Cannot connect to API server!")
        print("Please start the server first:")
        print("  uvicorn src.api.app:app --reload")
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
