#!/usr/bin/env python3
"""
Result Diversification Demo - Day 24

Demonstrates Maximum Marginal Relevance (MMR) for result diversification.

Shows how MMR helps avoid redundant results by balancing relevance and diversity,
ensuring users get a broader view of the topic rather than seeing many similar results.

Author: API Assistant Team
Date: 2025-12-27
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core import VectorStore, ResultDiversifier

# Sample API documentation with some similar/redundant entries
API_DOCS = [
    {
        "content": "POST /api/auth/login - Authenticate user with username and password. Returns JWT access token.",
        "metadata": {"endpoint": "POST /api/auth/login", "category": "authentication"},
    },
    {
        "content": "POST /api/auth/signin - User login endpoint. Accepts credentials and returns authentication token.",
        "metadata": {"endpoint": "POST /api/auth/signin", "category": "authentication"},
    },
    {
        "content": "POST /api/auth/authenticate - Authentication endpoint for user login. Returns JWT token on success.",
        "metadata": {"endpoint": "POST /api/auth/authenticate", "category": "authentication"},
    },
    {
        "content": "POST /api/auth/logout - Logout user and invalidate session token.",
        "metadata": {"endpoint": "POST /api/auth/logout", "category": "authentication"},
    },
    {
        "content": "POST /api/auth/refresh - Refresh expired access token using refresh token.",
        "metadata": {"endpoint": "POST /api/auth/refresh", "category": "authentication"},
    },
    {
        "content": "GET /api/auth/verify - Verify authentication token validity.",
        "metadata": {"endpoint": "GET /api/auth/verify", "category": "authentication"},
    },
    {
        "content": "GET /api/users - List all users with pagination support.",
        "metadata": {"endpoint": "GET /api/users", "category": "users"},
    },
    {
        "content": "POST /api/users - Create new user account with email and profile data.",
        "metadata": {"endpoint": "POST /api/users", "category": "users"},
    },
    {
        "content": "GET /api/users/{id} - Retrieve user profile information by user ID.",
        "metadata": {"endpoint": "GET /api/users/{id}", "category": "users"},
    },
    {
        "content": "PUT /api/users/{id} - Update user profile details.",
        "metadata": {"endpoint": "PUT /api/users/{id}", "category": "users"},
    },
    {
        "content": "DELETE /api/users/{id} - Remove user account from system.",
        "metadata": {"endpoint": "DELETE /api/users/{id}", "category": "users"},
    },
    {
        "content": "POST /api/products - Add new product to catalog.",
        "metadata": {"endpoint": "POST /api/products", "category": "products"},
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
        score_str = f"{result['score']:.4f}" if 'score' in result else "N/A"
        print(f"\n{i}. [Score: {score_str}]")
        print(f"   {result['content'][:80]}...")
        print(f"   Endpoint: {result['metadata'].get('endpoint', 'N/A')}")


def compare_results(original, diversified):
    """Compare original vs diversified results."""
    print("\n" + "="*90)
    print("COMPARISON: Original vs Diversified")
    print("="*90)

    print("\nOriginal Results (By Relevance Only):")
    for i, r in enumerate(original, 1):
        endpoint = r['metadata'].get('endpoint', 'N/A')
        print(f"  {i}. {endpoint}")

    print("\nDiversified Results (Relevance + Diversity):")
    for i, r in enumerate(diversified, 1):
        endpoint = r['metadata'].get('endpoint', 'N/A')
        print(f"  {i}. {endpoint}")

    # Compute diversity scores
    diversifier = ResultDiversifier()
    orig_diversity = diversifier.compute_diversity_score(original)
    div_diversity = diversifier.compute_diversity_score(diversified)

    print(f"\nDiversity Scores (0-1, higher = more diverse):")
    print(f"  Original: {orig_diversity:.3f}")
    print(f"  Diversified: {div_diversity:.3f}")
    print(f"  Improvement: {(div_diversity - orig_diversity):.3f} ({((div_diversity - orig_diversity) / max(orig_diversity, 0.001) * 100):.1f}%)")


def main():
    """Run result diversification demo."""
    print_section("RESULT DIVERSIFICATION DEMO - DAY 24")

    print("\nMaximum Marginal Relevance (MMR) balances:")
    print("  - Relevance: How well results match the query")
    print("  - Diversity: How different results are from each other")
    print("\nThis prevents redundant results and provides better topic coverage.")

    # Initialize vector store
    print("\n" + "-" * 90)
    print("Initializing vector store...")
    vector_store = VectorStore(
        collection_name="diversification_demo",
        enable_hybrid_search=True,
    )

    # Clear and recreate
    try:
        vector_store.clear()
    except:
        pass

    vector_store = VectorStore(
        collection_name="diversification_demo",
        enable_hybrid_search=True,
    )

    # Add documents
    print(f"Adding {len(API_DOCS)} API documentation entries...")
    vector_store.add_documents(API_DOCS)

    # Initialize diversifier
    diversifier = ResultDiversifier(lambda_param=0.5)  # Balanced

    # Test 1: Authentication query (many similar results)
    print_section("TEST 1: AUTHENTICATION QUERY - 'user login authentication'")
    print("\nProblem: Query returns many similar login/authentication endpoints")
    print("Solution: MMR selects diverse authentication-related endpoints\n")

    query1 = "user login authentication"

    # Original search (no diversification)
    original_results = vector_store.search(query1, n_results=5)
    print_results(original_results, "Original Results (No Diversification):")

    # Diversified search
    candidates = vector_store.search(query1, n_results=10)
    diversified_results = diversifier.diversify(candidates, top_k=5)
    print_results(diversified_results, "Diversified Results (MMR with λ=0.5):")

    compare_results(original_results, diversified_results)

    # Test 2: Different lambda values
    print_section("TEST 2: LAMBDA PARAMETER EFFECTS")
    print("\nλ (lambda) controls the relevance-diversity tradeoff:")
    print("  λ = 1.0: Pure relevance (no diversity)")
    print("  λ = 0.5: Balanced (default)")
    print("  λ = 0.0: Pure diversity (no relevance weighting)\n")

    query2 = "authentication"
    candidates2 = vector_store.search(query2, n_results=10)

    # Pure relevance (lambda=1.0)
    diversifier_pure_relevance = ResultDiversifier(lambda_param=1.0)
    pure_relevance = diversifier_pure_relevance.diversify(candidates2, top_k=5)
    print_results(pure_relevance, "λ=1.0 (Pure Relevance):")

    # Balanced (lambda=0.5)
    diversifier_balanced = ResultDiversifier(lambda_param=0.5)
    balanced = diversifier_balanced.diversify(candidates2, top_k=5)
    print_results(balanced, "λ=0.5 (Balanced):")

    # Pure diversity (lambda=0.0)
    diversifier_pure_diversity = ResultDiversifier(lambda_param=0.0)
    pure_diversity = diversifier_pure_diversity.diversify(candidates2, top_k=5)
    print_results(pure_diversity, "λ=0.0 (Pure Diversity):")

    # Compute diversity scores for each
    print("\nDiversity Score Comparison:")
    print(f"  λ=1.0: {diversifier_balanced.compute_diversity_score(pure_relevance):.3f}")
    print(f"  λ=0.5: {diversifier_balanced.compute_diversity_score(balanced):.3f}")
    print(f"  λ=0.0: {diversifier_balanced.compute_diversity_score(pure_diversity):.3f}")

    # Test 3: CRUD operations diversification
    print_section("TEST 3: CRUD OPERATIONS - 'user management'")
    print("\nProblem: All results might be GET endpoints (most common)")
    print("Solution: MMR ensures variety of operations (GET, POST, PUT, DELETE)\n")

    query3 = "user management"

    original_results3 = vector_store.search(query3, n_results=5)
    print_results(original_results3, "Original Results:")

    candidates3 = vector_store.search(query3, n_results=10)
    diversified_results3 = diversifier.diversify(candidates3, top_k=5)
    print_results(diversified_results3, "Diversified Results:")

    # Count HTTP methods
    def count_methods(results):
        methods = {}
        for r in results:
            method = r['content'].split()[0]
            methods[method] = methods.get(method, 0) + 1
        return methods

    orig_methods = count_methods(original_results3)
    div_methods = count_methods(diversified_results3)

    print("\nHTTP Method Distribution:")
    print(f"  Original: {orig_methods}")
    print(f"  Diversified: {div_methods}")
    print(f"  Unique methods: Original={len(orig_methods)}, Diversified={len(div_methods)}")

    compare_results(original_results3, diversified_results3)

    # Summary
    print_section("DEMO SUMMARY")

    print("\n✅ Benefits of Result Diversification (MMR):")
    print("  1. Avoids redundant results (similar login endpoints)")
    print("  2. Provides broader topic coverage")
    print("  3. Better user experience (less scrolling through similar results)")
    print("  4. Configurable relevance-diversity tradeoff (lambda parameter)")
    print("  5. Works with any search backend (content or embedding-based)")

    print("\n📊 When to Use:")
    print("  - Search results tend to be similar/redundant")
    print("  - User needs overview of a topic (not just best match)")
    print("  - Displaying multiple results to users")
    print("  - Topic exploration and discovery")

    print("\n⚙️  Lambda Parameter Guide:")
    print("  λ=0.9-1.0: When precision is critical (exact match needed)")
    print("  λ=0.5-0.7: Balanced (most use cases) ← RECOMMENDED")
    print("  λ=0.0-0.3: When diversity is critical (topic exploration)")

    print("\n💡 Integration Example:")
    print("""
    from src.core import VectorStore, ResultDiversifier

    # Initialize
    vector_store = VectorStore()
    diversifier = ResultDiversifier(lambda_param=0.5)

    # Search + diversify
    candidates = vector_store.search(query, n_results=20)  # Retrieve 20
    diverse_results = diversifier.diversify(candidates, top_k=5)  # Return 5 diverse

    # Or use helper
    from src.core import diversify_results
    diverse = diversify_results(candidates, top_k=5, lambda_param=0.5)
    """)

    # Cleanup
    print("\n" + "=" * 90)
    print("Cleaning up demo collection...")
    vector_store.clear()
    print("Demo completed!")
    print("=" * 90)


if __name__ == "__main__":
    main()
