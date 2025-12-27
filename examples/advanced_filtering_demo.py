#!/usr/bin/env python3
"""
Advanced Filtering and Faceted Search Demo - Day 25

Demonstrates advanced filtering and faceted search capabilities.

Shows how filtering helps refine search results by:
- Metadata field filtering (equality, range, contains, etc.)
- Content filtering
- Complex filter combinations (AND, OR, NOT)
- Faceted search for building filter UIs
- Multiple filter scenarios

Author: API Assistant Team
Date: 2025-12-27
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core import VectorStore, FilterBuilder, FilterOperator

# Sample API documentation with rich metadata
API_DOCS = [
    {
        "content": "POST /api/auth/login - Authenticate user with credentials",
        "metadata": {
            "endpoint": "POST /api/auth/login",
            "method": "POST",
            "category": "authentication",
            "version": "v1",
            "status": "active",
            "requires_auth": False,
            "priority": 1,
        },
    },
    {
        "content": "GET /api/auth/verify - Verify authentication token validity",
        "metadata": {
            "endpoint": "GET /api/auth/verify",
            "method": "GET",
            "category": "authentication",
            "version": "v1",
            "status": "active",
            "requires_auth": True,
            "priority": 2,
        },
    },
    {
        "content": "POST /api/users - Create new user account",
        "metadata": {
            "endpoint": "POST /api/users",
            "method": "POST",
            "category": "users",
            "version": "v1",
            "status": "active",
            "requires_auth": True,
            "priority": 3,
        },
    },
    {
        "content": "GET /api/users/{id} - Retrieve user profile information",
        "metadata": {
            "endpoint": "GET /api/users/{id}",
            "method": "GET",
            "category": "users",
            "version": "v1",
            "status": "active",
            "requires_auth": True,
            "priority": 1,
        },
    },
    {
        "content": "PUT /api/users/{id} - Update user profile",
        "metadata": {
            "endpoint": "PUT /api/users/{id}",
            "method": "PUT",
            "category": "users",
            "version": "v1",
            "status": "active",
            "requires_auth": True,
            "priority": 2,
        },
    },
    {
        "content": "DELETE /api/users/{id} - Delete user account",
        "metadata": {
            "endpoint": "DELETE /api/users/{id}",
            "method": "DELETE",
            "category": "users",
            "version": "v2",
            "status": "deprecated",
            "requires_auth": True,
            "priority": 5,
        },
    },
    {
        "content": "POST /api/webhooks - Register webhook for events",
        "metadata": {
            "endpoint": "POST /api/webhooks",
            "method": "POST",
            "category": "webhooks",
            "version": "v2",
            "status": "active",
            "requires_auth": True,
            "priority": 3,
        },
    },
    {
        "content": "GET /api/webhooks - List all registered webhooks",
        "metadata": {
            "endpoint": "GET /api/webhooks",
            "method": "GET",
            "category": "webhooks",
            "version": "v2",
            "status": "active",
            "requires_auth": True,
            "priority": 2,
        },
    },
    {
        "content": "GET /api/analytics - Retrieve analytics and metrics",
        "metadata": {
            "endpoint": "GET /api/analytics",
            "method": "GET",
            "category": "analytics",
            "version": "v1",
            "status": "beta",
            "requires_auth": True,
            "priority": 4,
        },
    },
    {
        "content": "POST /api/auth/oauth - OAuth authentication endpoint",
        "metadata": {
            "endpoint": "POST /api/auth/oauth",
            "method": "POST",
            "category": "authentication",
            "version": "v2",
            "status": "active",
            "requires_auth": False,
            "priority": 1,
        },
    },
]


def print_section(title):
    """Print section header."""
    print(f"\n{'=' * 90}")
    print(f"{title}")
    print(f"{'=' * 90}")


def print_results(results, title):
    """Print search results."""
    print(f"\n{title}")
    print("-" * 90)
    if not results:
        print("No results found.")
        return

    for i, result in enumerate(results, 1):
        metadata = result.get("metadata", {})
        print(f"\n{i}. {metadata.get('endpoint', 'N/A')}")
        print(f"   Method: {metadata.get('method', 'N/A')}")
        print(f"   Category: {metadata.get('category', 'N/A')}")
        print(f"   Version: {metadata.get('version', 'N/A')}")
        print(f"   Status: {metadata.get('status', 'N/A')}")
        print(f"   Score: {result.get('score', 0):.4f}")


def print_facets(facets, title):
    """Print facet results."""
    print(f"\n{title}")
    print("-" * 90)

    for field, facet in facets.items():
        print(f"\n{field.upper()} ({facet.total_docs} total):")
        for value, count in facet.get_top_values(10):
            percentage = facet.get_percentage(value)
            print(f"  - {value}: {count} ({percentage:.1f}%)")


def main():
    """Run advanced filtering demo."""
    print_section("ADVANCED FILTERING AND FACETED SEARCH DEMO - DAY 25")

    print("\nAdvanced filtering enables:")
    print("  - Precise metadata filtering (equality, range, contains)")
    print("  - Content-based filtering")
    print("  - Complex filter combinations (AND, OR, NOT)")
    print("  - Faceted search for building filter UIs")

    # Initialize vector store
    print("\n" + "-" * 90)
    print("Initializing vector store...")
    vector_store = VectorStore(
        collection_name="filtering_demo",
        enable_hybrid_search=True,
    )

    # Clear and recreate
    try:
        vector_store.clear()
    except:
        pass

    vector_store = VectorStore(
        collection_name="filtering_demo",
        enable_hybrid_search=True,
    )

    # Add documents
    print(f"Adding {len(API_DOCS)} API documentation entries...")
    vector_store.add_documents(API_DOCS)

    # Test 1: Basic Equality Filter
    print_section("TEST 1: BASIC EQUALITY FILTER - method = 'GET'")

    # Filter for GET endpoints
    filter_get = FilterBuilder.eq("method", "GET")

    results = vector_store.search(
        "api documentation",
        n_results=10,
        where=filter_get,
    )

    print_results(results, "GET Endpoints Only")
    print(f"\nFound {len(results)} GET endpoints (expected: 4)")

    # Test 2: Range Filter
    print_section("TEST 2: RANGE FILTER - priority <= 2")

    # Filter for high priority endpoints
    filter_priority = FilterBuilder.lte("priority", 2)

    results = vector_store.search(
        "api",
        n_results=10,
        where=filter_priority,
    )

    print_results(results, "High Priority Endpoints (priority <= 2)")
    print(f"\nFound {len(results)} high priority endpoints")

    # Test 3: IN Filter - Multiple Categories
    print_section("TEST 3: IN FILTER - category IN ['authentication', 'users']")

    # Filter for specific categories
    filter_categories = FilterBuilder.in_list("category", ["authentication", "users"])

    results = vector_store.search(
        "api",
        n_results=10,
        where=filter_categories,
    )

    print_results(results, "Authentication and User Endpoints")
    print(f"\nFound {len(results)} results in selected categories")

    # Test 4: AND Filter - Combining Conditions
    print_section("TEST 4: AND FILTER - method = 'POST' AND category = 'authentication'")

    # POST endpoints in authentication category
    filter_post = FilterBuilder.eq("method", "POST")
    filter_auth = FilterBuilder.eq("category", "authentication")
    filter_and = FilterBuilder.and_filters(filter_post, filter_auth)

    results = vector_store.search(
        "api",
        n_results=10,
        where=filter_and,
    )

    print_results(results, "POST Endpoints in Authentication Category")
    print(f"\nFound {len(results)} matching endpoints")

    # Test 5: OR Filter - Multiple Conditions
    print_section("TEST 5: OR FILTER - method = 'POST' OR method = 'PUT'")

    # POST or PUT endpoints
    filter_post = FilterBuilder.eq("method", "POST")
    filter_put = FilterBuilder.eq("method", "PUT")
    filter_or = FilterBuilder.or_filters(filter_post, filter_put)

    results = vector_store.search(
        "api",
        n_results=10,
        where=filter_or,
    )

    print_results(results, "POST or PUT Endpoints")
    print(f"\nFound {len(results)} POST/PUT endpoints")

    # Test 6: NOT Filter - Exclusion
    print_section("TEST 6: NOT FILTER - NOT (status = 'deprecated')")

    # Exclude deprecated endpoints
    filter_deprecated = FilterBuilder.eq("status", "deprecated")
    filter_not_deprecated = FilterBuilder.not_filter(filter_deprecated)

    results = vector_store.search(
        "api",
        n_results=10,
        where=filter_not_deprecated,
    )

    print_results(results, "Active (Non-Deprecated) Endpoints")
    print(f"\nFound {len(results)} non-deprecated endpoints")

    # Test 7: Complex Nested Filter
    print_section(
        "TEST 7: COMPLEX FILTER - (method = 'GET' OR method = 'POST') AND version = 'v2'"
    )

    # Complex: (GET or POST) AND v2
    filter_get = FilterBuilder.eq("method", "GET")
    filter_post = FilterBuilder.eq("method", "POST")
    filter_method_or = FilterBuilder.or_filters(filter_get, filter_post)

    filter_v2 = FilterBuilder.eq("version", "v2")
    filter_complex = FilterBuilder.and_filters(filter_method_or, filter_v2)

    results = vector_store.search(
        "api",
        n_results=10,
        where=filter_complex,
    )

    print_results(results, "GET/POST Endpoints in Version v2")
    print(f"\nFound {len(results)} matching endpoints")

    # Test 8: Content Filter
    print_section("TEST 8: CONTENT FILTER - content contains 'OAuth'")

    # Filter by content
    filter_content = FilterBuilder.content_contains("OAuth")

    results = vector_store.search(
        "authentication",
        n_results=10,
        where=filter_content,
    )

    print_results(results, "Endpoints Mentioning OAuth")
    print(f"\nFound {len(results)} endpoints with 'OAuth' in content")

    # Test 9: Faceted Search
    print_section("TEST 9: FACETED SEARCH - Aggregate by Multiple Fields")

    # Perform faceted search
    results, facets = vector_store.search_with_facets(
        query="api",
        facet_fields=["category", "method", "version", "status"],
        n_results=20,
    )

    print(f"\nSearch Query: 'api'")
    print(f"Total Results: {len(results)}")

    print_facets(facets, "Facet Aggregations")

    # Test 10: Faceted Search with Filter
    print_section("TEST 10: FACETED SEARCH + FILTER - Active endpoints only")

    # Faceted search with active endpoints filter
    filter_active = FilterBuilder.eq("status", "active")

    results, facets = vector_store.search_with_facets(
        query="api",
        facet_fields=["category", "method", "version"],
        n_results=20,
        where=filter_active,
    )

    print(f"\nSearch Query: 'api' (filtered: status = 'active')")
    print(f"Total Results: {len(results)}")

    print_facets(facets, "Facet Aggregations (Active Endpoints Only)")

    # Test 11: Building a Filter UI
    print_section("TEST 11: SIMULATING FILTER UI - Progressive Filtering")

    print("\nStep 1: Initial search (no filters)")
    results, facets = vector_store.search_with_facets(
        query="api",
        facet_fields=["category", "method", "version"],
        n_results=20,
    )
    print(f"Results: {len(results)}")
    print(f"Categories available: {list(facets['category'].values.keys())}")

    print("\nStep 2: User selects category = 'authentication'")
    filter_cat = FilterBuilder.eq("category", "authentication")
    results, facets = vector_store.search_with_facets(
        query="api",
        facet_fields=["method", "version"],
        n_results=20,
        where=filter_cat,
    )
    print(f"Results: {len(results)}")
    print(f"Methods available: {list(facets['method'].values.keys())}")

    print("\nStep 3: User also selects method = 'POST'")
    filter_method = FilterBuilder.eq("method", "POST")
    filter_combined = FilterBuilder.and_filters(filter_cat, filter_method)
    results, facets = vector_store.search_with_facets(
        query="api",
        facet_fields=["version"],
        n_results=20,
        where=filter_combined,
    )
    print(f"Final Results: {len(results)}")
    print_results(results, "Final Filtered Results")

    # Test 12: Real-World Scenario - Find Public Endpoints
    print_section("TEST 12: REAL-WORLD - Find Public (No Auth) Endpoints")

    # requires_auth = False
    filter_public = FilterBuilder.eq("requires_auth", False)
    filter_active = FilterBuilder.eq("status", "active")
    filter_public_active = FilterBuilder.and_filters(filter_public, filter_active)

    results = vector_store.search(
        "authentication",
        n_results=10,
        where=filter_public_active,
    )

    print_results(results, "Public Endpoints (No Authentication Required)")
    print(f"\nFound {len(results)} public endpoints")

    # Summary
    print_section("DEMO SUMMARY")

    print("\n✅ Advanced Filtering Benefits:")
    print("  1. Precise result filtering by metadata fields")
    print("  2. Complex filter combinations (AND, OR, NOT)")
    print("  3. Range queries and collection operators (IN, NOT IN)")
    print("  4. Content-based filtering")
    print("  5. Integration with search for filtered semantic search")

    print("\n📊 Faceted Search Benefits:")
    print("  1. Build filter UIs with category counts")
    print("  2. Progressive filtering (drill-down)")
    print("  3. Understand result distribution")
    print("  4. Show available filter options with counts")
    print("  5. Improve user experience with filter visibility")

    print("\n💡 Filter Types:")
    print("  - Equality: eq(), ne()")
    print("  - Range: gt(), gte(), lt(), lte()")
    print("  - Collection: in_list(), not_in_list()")
    print("  - String: contains(), not_contains()")
    print("  - Content: content_contains(), content_not_contains()")
    print("  - Logical: and_filters(), or_filters(), not_filter()")

    print("\n⚙️  Integration Example:")
    print("""
    from src.core import VectorStore, FilterBuilder

    # Initialize
    vector_store = VectorStore()

    # Create complex filter
    # (method = 'GET' OR method = 'POST') AND status != 'deprecated'
    get_filter = FilterBuilder.eq("method", "GET")
    post_filter = FilterBuilder.eq("method", "POST")
    method_or = FilterBuilder.or_filters(get_filter, post_filter)

    deprecated_filter = FilterBuilder.eq("status", "deprecated")
    not_deprecated = FilterBuilder.not_filter(deprecated_filter)

    final_filter = FilterBuilder.and_filters(method_or, not_deprecated)

    # Search with filter
    results = vector_store.search(
        "authentication",
        n_results=10,
        where=final_filter
    )

    # Or use faceted search
    results, facets = vector_store.search_with_facets(
        "api documentation",
        facet_fields=["category", "method", "version"],
        n_results=20,
        where=final_filter
    )

    # Display facet counts
    for field, facet in facets.items():
        print(f"{field}:")
        for value, count in facet.get_top_values(5):
            print(f"  {value}: {count}")
    """)

    print("\n🎯 Use Cases:")
    print("  - E-commerce: Filter by price, category, brand, rating")
    print("  - Job boards: Filter by location, salary, experience, skills")
    print("  - API docs: Filter by method, version, category, status")
    print("  - Content sites: Filter by author, date, tags, type")
    print("  - Real estate: Filter by price range, bedrooms, location")

    # Cleanup
    print("\n" + "=" * 90)
    print("Cleaning up demo collection...")
    vector_store.clear()
    print("Demo completed!")
    print("=" * 90)


if __name__ == "__main__":
    main()
