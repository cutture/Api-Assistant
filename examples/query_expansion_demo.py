#!/usr/bin/env python3
"""
Query Expansion Demo - Day 23

Demonstrates query expansion for improved search recall.

Shows how query expansion helps overcome vocabulary mismatch between
user queries and document content by:
- Adding synonyms and related technical terms
- Generating query variations
- Expanding abbreviations
- Creating multiple query perspectives

Author: API Assistant Team
Date: 2025-12-27
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core import VectorStore, QueryExpander

# Sample API documentation
API_DOCS = [
    {
        "content": "POST /api/auth/login - Authenticate user credentials and return access token. Supports OAuth2 and JWT authentication.",
        "metadata": {"endpoint": "POST /api/auth/login", "category": "authentication"},
    },
    {
        "content": "GET /api/auth/verify - Verify authentication token validity. Returns 200 if token is valid.",
        "metadata": {"endpoint": "GET /api/auth/verify", "category": "authentication"},
    },
    {
        "content": "POST /api/users - Create new user account. Requires admin permissions.",
        "metadata": {"endpoint": "POST /api/users", "category": "users"},
    },
    {
        "content": "GET /api/users/{id} - Retrieve user profile information by user ID.",
        "metadata": {"endpoint": "GET /api/users/{id}", "category": "users"},
    },
    {
        "content": "PUT /api/users/{id} - Update user profile details. Requires authentication.",
        "metadata": {"endpoint": "PUT /api/users/{id}", "category": "users"},
    },
    {
        "content": "DELETE /api/users/{id} - Remove user account. Requires admin role.",
        "metadata": {"endpoint": "DELETE /api/users/{id}", "category": "users"},
    },
    {
        "content": "POST /api/products - Add new product to catalog. Returns product ID on success.",
        "metadata": {"endpoint": "POST /api/products", "category": "products"},
    },
    {
        "content": "GET /api/products - List all products with pagination support. Filter by category.",
        "metadata": {"endpoint": "GET /api/products", "category": "products"},
    },
    {
        "content": "GET /api/analytics - Retrieve analytics data and metrics. Requires admin access.",
        "metadata": {"endpoint": "GET /api/analytics", "category": "analytics"},
    },
    {
        "content": "POST /api/webhooks - Register webhook endpoint for event notifications.",
        "metadata": {"endpoint": "POST /api/webhooks", "category": "webhooks"},
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
        print(f"\n{i}. [Score: {result['score']:.4f}]")
        print(f"   {result['content']}")
        print(f"   Category: {result['metadata'].get('category', 'N/A')}")


def print_expanded_query(expanded):
    """Print expanded query details."""
    print(f"\nOriginal Query: \"{expanded.original_query}\"")
    print(f"Expansion Method: {expanded.expansion_method}")
    print(f"Confidence: {expanded.confidence}")

    if expanded.expanded_terms:
        print(f"\nExpanded Terms ({len(expanded.expanded_terms)}):")
        for term in expanded.expanded_terms[:10]:  # Show first 10
            print(f"  - {term}")

    if expanded.query_variations:
        print(f"\nQuery Variations ({len(expanded.query_variations)}):")
        for var in expanded.query_variations:
            print(f"  - {var}")


def compare_results(original_results, expanded_results):
    """Compare original vs expanded query results."""
    print("\n" + "=" * 90)
    print("RESULTS COMPARISON")
    print("=" * 90)

    print(f"\nOriginal query found: {len(original_results)} results")
    print(f"Expanded query found: {len(expanded_results)} results")

    # Check for new results
    original_ids = {r['id'] for r in original_results}
    expanded_ids = {r['id'] for r in expanded_results}

    new_results = expanded_ids - original_ids
    if new_results:
        print(f"\n✅ Query expansion found {len(new_results)} additional results!")
    else:
        print("\nℹ️  No additional results (but may have improved ranking)")


def main():
    """Run query expansion demo."""
    print_section("QUERY EXPANSION DEMO - DAY 23")

    print("\nQuery expansion improves search recall by:")
    print("  - Adding synonyms and related terms")
    print("  - Expanding technical abbreviations")
    print("  - Generating query variations")
    print("  - Overcoming vocabulary mismatch")

    # Initialize vector store
    print("\n" + "-" * 90)
    print("Initializing vector store...")
    vector_store = VectorStore(
        collection_name="query_expansion_demo",
        enable_hybrid_search=True,
    )

    # Clear and recreate
    try:
        vector_store.clear()
    except:
        pass

    vector_store = VectorStore(
        collection_name="query_expansion_demo",
        enable_hybrid_search=True,
    )

    # Add documents
    print(f"Adding {len(API_DOCS)} API documentation entries...")
    vector_store.add_documents(API_DOCS)

    # Initialize query expander
    expander = QueryExpander()

    # Test 1: Abbreviation Expansion (auth → authentication, login, OAuth, JWT)
    print_section("TEST 1: ABBREVIATION EXPANSION - 'auth'")

    query1 = "auth"

    # Original search
    original_results = vector_store.search(query1, n_results=5)
    print_results(original_results, "Original Query: 'auth'")

    # Expand query
    expanded1 = expander.expand_query(query1, strategy="domain")
    print_expanded_query(expanded1)

    # Search with expanded terms
    expanded_query_str = expander.expand_and_format(query1)
    expanded_results = vector_store.search(expanded_query_str, n_results=5)
    print_results(expanded_results, f"Expanded Query: '{expanded_query_str[:80]}...'")

    compare_results(original_results, expanded_results)

    # Test 2: Technical Term Expansion (JWT → JSON Web Token, authentication, token)
    print_section("TEST 2: TECHNICAL TERM EXPANSION - 'JWT'")

    query2 = "JWT"

    # Original search
    original_results = vector_store.search(query2, n_results=5)
    print_results(original_results, "Original Query: 'JWT'")

    # Expand query
    expanded2 = expander.expand_query(query2, strategy="domain")
    print_expanded_query(expanded2)

    # Search with expanded terms
    expanded_query_str = expander.expand_and_format(query2)
    expanded_results = vector_store.search(expanded_query_str, n_results=5)
    print_results(expanded_results, f"Expanded Query: '{expanded_query_str[:80]}...'")

    compare_results(original_results, expanded_results)

    # Test 3: Multi-Query Expansion (question → multiple variations)
    print_section("TEST 3: MULTI-QUERY EXPANSION - 'how to authenticate'")

    query3 = "how to authenticate users"

    # Original search
    original_results = vector_store.search(query3, n_results=5)
    print_results(original_results, "Original Query: 'how to authenticate users'")

    # Expand query
    expanded3 = expander.expand_query(query3, strategy="multi_query")
    print_expanded_query(expanded3)

    # Search with each query variation and merge results
    print("\nSearching with each query variation...")
    all_results = {}
    for i, query_var in enumerate(expanded3.get_all_queries(), 1):
        print(f"  {i}. Searching: \"{query_var}\"")
        results = vector_store.search(query_var, n_results=3)
        for r in results:
            if r['id'] not in all_results or r['score'] > all_results[r['id']]['score']:
                all_results[r['id']] = r

    # Sort by score
    merged_results = sorted(all_results.values(), key=lambda x: x['score'], reverse=True)[:5]
    print_results(merged_results, "Merged Results from All Query Variations")

    compare_results(original_results, merged_results)

    # Test 4: Compound Query Expansion (multiple technical terms)
    print_section("TEST 4: COMPOUND QUERY - 'POST endpoint authentication'")

    query4 = "POST endpoint authentication"

    # Original search
    original_results = vector_store.search(query4, n_results=5)
    print_results(original_results, "Original Query: 'POST endpoint authentication'")

    # Expand query
    expanded4 = expander.expand_query(query4, strategy="domain")
    print_expanded_query(expanded4)

    # Search with expanded terms
    expanded_query_str = expander.expand_and_format(query4)
    expanded_results = vector_store.search(expanded_query_str, n_results=5)
    print_results(expanded_results, f"Expanded Query: '{expanded_query_str[:80]}...'")

    compare_results(original_results, expanded_results)

    # Test 5: Auto Strategy Selection
    print_section("TEST 5: AUTO STRATEGY SELECTION")

    test_queries = [
        ("config settings", "Technical terms → domain expansion"),
        ("what is OAuth", "Question → multi-query expansion"),
        ("api documentation", "General terms → synonym expansion"),
    ]

    for query, expected in test_queries:
        print(f"\nQuery: \"{query}\"")
        print(f"Expected: {expected}")

        expanded = expander.expand_query(query, strategy="auto")
        print(f"Selected strategy: {expanded.expansion_method}")

        if expanded.expanded_terms:
            print(f"Expanded terms: {', '.join(expanded.expanded_terms[:3])}")
        if expanded.query_variations:
            print(f"Query variations: {len(expanded.query_variations)} generated")

    # Summary
    print_section("DEMO SUMMARY")

    print("\n✅ Query Expansion Benefits:")
    print("  1. Overcomes vocabulary mismatch (user words ≠ document words)")
    print("  2. Expands abbreviations automatically (JWT → JSON Web Token)")
    print("  3. Adds domain-specific related terms (auth → authentication, login, OAuth)")
    print("  4. Generates multiple query perspectives for questions")
    print("  5. Improves recall without sacrificing precision")

    print("\n📊 Expansion Strategies:")
    print("  - Domain: Use for technical queries (auth, API, JWT)")
    print("  - Multi-query: Use for questions (how to, what is, why)")
    print("  - Synonyms: General purpose expansion")
    print("  - Auto: Automatically selects best strategy")

    print("\n💡 Usage Recommendations:")
    print("  - Use query expansion when users might use different terminology")
    print("  - Especially valuable for technical documentation search")
    print("  - Combine with hybrid search for best results")
    print("  - Consider multi-query for question-answering systems")

    print("\n⚙️  Integration Example:")
    print("""
    from src.core import QueryExpander, VectorStore

    # Initialize
    expander = QueryExpander()
    vector_store = VectorStore(enable_hybrid_search=True)

    # Expand query
    expanded = expander.expand_query("auth", strategy="domain")

    # Search with expanded terms
    expanded_query = expander.expand_and_format("auth")
    results = vector_store.search(expanded_query, n_results=10)

    # Or use query variations
    for query_var in expanded.get_all_queries():
        results = vector_store.search(query_var, n_results=5)
        # Merge results...
    """)

    # Cleanup
    print("\n" + "=" * 90)
    print("Cleaning up demo collection...")
    vector_store.clear()
    print("Demo completed!")
    print("=" * 90)


if __name__ == "__main__":
    main()
