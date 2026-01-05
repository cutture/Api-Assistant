#!/usr/bin/env python3
"""
Cross-Encoder Re-ranking Demo - Day 22

Demonstrates the cross-encoder re-ranking feature for improved search accuracy.

Shows three search modes:
1. Vector-only search (baseline)
2. Hybrid search (BM25 + Vector)
3. Re-ranked search (Cross-encoder re-ranking)

The demo compares results to show how cross-encoder re-ranking provides
the most accurate relevance scoring.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core import VectorStore

# Sample API documentation with varying relevance
API_DOCS = [
    {
        "content": "POST /api/auth/login - Authenticate user with OAuth2. Supports OAuth2 authorization code flow and client credentials flow.",
        "metadata": {"endpoint": "POST /api/auth/login", "category": "authentication"},
    },
    {
        "content": "OAuth2 - A protocol for authorization. Used for secure API access.",
        "metadata": {"endpoint": "N/A", "category": "concepts"},
    },
    {
        "content": "POST /api/users - Create a new user account. Returns user ID and profile.",
        "metadata": {"endpoint": "POST /api/users", "category": "users"},
    },
    {
        "content": "GET /api/auth/oauth2/authorize - OAuth2 authorization endpoint. Initiates OAuth2 authorization code flow.",
        "metadata": {"endpoint": "GET /api/auth/oauth2/authorize", "category": "authentication"},
    },
    {
        "content": "POST /api/auth/token - Exchange authorization code for access token in OAuth2 flow.",
        "metadata": {"endpoint": "POST /api/auth/token", "category": "authentication"},
    },
    {
        "content": "GET /api/products - List all products. Supports filtering and pagination.",
        "metadata": {"endpoint": "GET /api/products", "category": "products"},
    },
    {
        "content": "PUT /api/users/{id} - Update user profile. Requires authentication.",
        "metadata": {"endpoint": "PUT /api/users/{id}", "category": "users"},
    },
    {
        "content": "Authentication: The process of verifying identity. Can use various methods including OAuth2, JWT, Basic Auth.",
        "metadata": {"endpoint": "N/A", "category": "concepts"},
    },
    {
        "content": "GET /api/analytics - Retrieve analytics data. Requires admin permissions.",
        "metadata": {"endpoint": "GET /api/analytics", "category": "analytics"},
    },
    {
        "content": "POST /api/webhooks - Register a webhook for event notifications. Supports OAuth2 authenticated callbacks.",
        "metadata": {"endpoint": "POST /api/webhooks", "category": "webhooks"},
    },
]


def print_results(results, mode_name, show_scores=True):
    """Print search results in a formatted way."""
    print(f"\n{'=' * 90}")
    print(f"{mode_name.upper()}")
    print(f"{'=' * 90}")

    if not results:
        print("No results found.")
        return

    for i, result in enumerate(results, 1):
        score_str = f"{result['score']:.4f}" if show_scores else "N/A"
        print(f"\n{i}. [Score: {score_str}]")
        print(f"   {result['content'][:85]}...")
        print(f"   Category: {result['metadata'].get('category', 'N/A')}")
        if 'original_rank' in result:
            print(f"   Original Rank: {result['original_rank']} → Re-ranked: {i}")


def compare_rankings(vector_results, hybrid_results, reranked_results, query):
    """Compare rankings across different search modes."""
    print(f"\n{'=' * 90}")
    print("RANKING COMPARISON")
    print(f"{'=' * 90}")
    print(f"\nQuery: '{query}'")
    print(f"\n{'Doc ID':<12} | {'Vector Rank':<12} | {'Hybrid Rank':<12} | {'Reranked Rank':<14}")
    print("-" * 90)

    # Get all unique doc IDs
    all_docs = set()
    for r in vector_results[:3] + hybrid_results[:3] + reranked_results[:3]:
        all_docs.add(r['id'])

    # Create rank maps
    vector_map = {r['id']: (idx + 1, r['score']) for idx, r in enumerate(vector_results)}
    hybrid_map = {r['id']: (idx + 1, r['score']) for idx, r in enumerate(hybrid_results)}
    reranked_map = {r['id']: (idx + 1, r['score']) for idx, r in enumerate(reranked_results)}

    for doc_id in sorted(all_docs):
        v_rank, v_score = vector_map.get(doc_id, ("-", 0))
        h_rank, h_score = hybrid_map.get(doc_id, ("-", 0))
        r_rank, r_score = reranked_map.get(doc_id, ("-", 0))

        doc_id_short = doc_id[:10] + ".." if len(doc_id) > 12 else doc_id
        print(f"{doc_id_short:<12} | {str(v_rank):<12} | {str(h_rank):<12} | {str(r_rank):<14}")


def main():
    """Run cross-encoder re-ranking demo."""
    print("=" * 90)
    print("CROSS-ENCODER RE-RANKING DEMO - DAY 22")
    print("=" * 90)
    print("\nDemonstrating three search modes:")
    print("1. Vector-only search (baseline - semantic similarity)")
    print("2. Hybrid search (BM25 + Vector with RRF fusion)")
    print("3. Re-ranked search (Cross-encoder for maximum accuracy)")

    # Create vector store with hybrid search AND re-ranking enabled
    print("\n" + "-" * 90)
    print("Initializing vector store...")
    vector_store = VectorStore(
        collection_name="reranking_demo",
        enable_hybrid_search=True,
        enable_reranker=True,  # Enable cross-encoder re-ranking
        reranker_model="ms-marco-mini-lm-6",  # Fast model for demo
    )

    # Clear any existing data
    try:
        vector_store.clear()
    except:
        pass

    # Recreate collection
    vector_store = VectorStore(
        collection_name="reranking_demo",
        enable_hybrid_search=True,
        enable_reranker=True,
    )

    # Add API documentation
    print(f"Adding {len(API_DOCS)} API documentation entries...")
    vector_store.add_documents(API_DOCS)

    stats = vector_store.get_stats()
    print(f"\nVector Store Stats:")
    print(f"  - Documents: {stats['document_count']}")
    print(f"  - Hybrid Search: {'Enabled' if stats['hybrid_search_enabled'] else 'Disabled'}")
    print(f"  - Re-ranker: {'Enabled' if stats['reranker_enabled'] else 'Disabled'}")
    if 'reranker_model' in stats:
        print(f"  - Re-ranker Model: {stats['reranker_model']}")

    # Test 1: OAuth2 authentication query
    print("\n" + "=" * 90)
    print("TEST 1: SPECIFIC QUERY - 'OAuth2 authorization flow'")
    print("=" * 90)
    print("\nExpected: Cross-encoder should rank OAuth2 authorization endpoint highest")
    print("because it understands the full context, not just keyword matches.")

    query = "OAuth2 authorization flow"
    n_results = 5

    # Vector-only search
    vector_results = vector_store.search(
        query, n_results=n_results, use_hybrid=False, use_reranker=False
    )
    print_results(vector_results, "1. Vector-only Search (Baseline)")

    # Hybrid search
    hybrid_results = vector_store.search(
        query, n_results=n_results, use_hybrid=True, use_reranker=False
    )
    print_results(hybrid_results, "2. Hybrid Search (BM25 + Vector)")

    # Re-ranked search
    reranked_results = vector_store.search(
        query, n_results=n_results, use_hybrid=True, use_reranker=True
    )
    print_results(reranked_results, "3. Cross-Encoder Re-ranked (Most Accurate)")

    # Compare rankings
    compare_rankings(vector_results, hybrid_results, reranked_results, query)

    # Test 2: Ambiguous query
    print("\n" + "=" * 90)
    print("TEST 2: AMBIGUOUS QUERY - 'authentication methods'")
    print("=" * 90)
    print("\nExpected: Cross-encoder should better understand which docs are about")
    print("authentication methods vs just mentioning 'authentication'")

    query = "authentication methods"
    n_results = 5

    # Vector-only search
    vector_results = vector_store.search(
        query, n_results=n_results, use_hybrid=False, use_reranker=False
    )
    print_results(vector_results, "1. Vector-only Search")

    # Hybrid search
    hybrid_results = vector_store.search(
        query, n_results=n_results, use_hybrid=True, use_reranker=False
    )
    print_results(hybrid_results, "2. Hybrid Search")

    # Re-ranked search
    reranked_results = vector_store.search(
        query, n_results=n_results, use_hybrid=True, use_reranker=True
    )
    print_results(reranked_results, "3. Cross-Encoder Re-ranked")

    # Test 3: Keyword vs semantic
    print("\n" + "=" * 90)
    print("TEST 3: KEYWORD vs SEMANTIC - 'how to get access token'")
    print("=" * 90)
    print("\nExpected: Cross-encoder should find the token exchange endpoint")
    print("even though query uses different words ('get' vs 'exchange')")

    query = "how to get access token"
    n_results = 5

    # Vector-only search
    vector_results = vector_store.search(
        query, n_results=n_results, use_hybrid=False, use_reranker=False
    )
    print_results(vector_results, "1. Vector-only Search")

    # Hybrid search
    hybrid_results = vector_store.search(
        query, n_results=n_results, use_hybrid=True, use_reranker=False
    )
    print_results(hybrid_results, "2. Hybrid Search")

    # Re-ranked search
    reranked_results = vector_store.search(
        query, n_results=n_results, use_hybrid=True, use_reranker=True
    )
    print_results(reranked_results, "3. Cross-Encoder Re-ranked")

    # Summary
    print("\n" + "=" * 90)
    print("DEMO SUMMARY - SEARCH MODE COMPARISON")
    print("=" * 90)

    print("\n1. VECTOR-ONLY SEARCH (Baseline)")
    print("   - Fast semantic similarity using bi-encoder embeddings")
    print("   - Good for general semantic matching")
    print("   - May miss exact keyword matches")
    print("   - Speed: ⚡⚡⚡ (Fastest)")
    print("   - Accuracy: ⭐⭐⭐ (Good)")

    print("\n2. HYBRID SEARCH (BM25 + Vector with RRF)")
    print("   - Combines BM25 keyword matching with vector search")
    print("   - Better for queries with important keywords")
    print("   - Reciprocal Rank Fusion merges results")
    print("   - Speed: ⚡⚡ (Fast)")
    print("   - Accuracy: ⭐⭐⭐⭐ (Very Good)")

    print("\n3. CROSS-ENCODER RE-RANKING (Most Accurate)")
    print("   - Retrieves candidates with hybrid search")
    print("   - Re-ranks with cross-encoder (processes query+doc together)")
    print("   - Captures fine-grained relevance signals")
    print("   - Best for high-stakes queries requiring maximum accuracy")
    print("   - Speed: ⚡ (Slower, but still fast for top-k)")
    print("   - Accuracy: ⭐⭐⭐⭐⭐ (Excellent)")

    print("\n" + "=" * 90)
    print("RECOMMENDATION")
    print("=" * 90)
    print("\nFor production systems:")
    print("  - Use HYBRID SEARCH for most queries (good balance)")
    print("  - Use CROSS-ENCODER RE-RANKING for:")
    print("    * High-stakes queries where accuracy is critical")
    print("    * User-facing search where quality matters most")
    print("    * Queries where you can afford 50-100ms extra latency")
    print("  - Use VECTOR-ONLY for:")
    print("    * Extremely high-throughput scenarios")
    print("    * When sub-10ms latency is required")

    # Cleanup
    print("\n" + "=" * 90)
    print("Cleaning up demo collection...")
    vector_store.clear()
    print("Demo completed!")
    print("=" * 90)


if __name__ == "__main__":
    main()
