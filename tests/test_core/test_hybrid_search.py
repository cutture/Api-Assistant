"""
Comprehensive tests for hybrid search (BM25 + Vector).

Tests cover:
- BM25 tokenization and scoring
- Reciprocal Rank Fusion (RRF)
- Weighted Score Fusion
- Hybrid search integration
- Edge cases and error handling
"""

import pytest
from src.core.hybrid_search import (
    BM25,
    HybridSearch,
    SearchResult,
    create_bm25_index,
    get_bm25,
    get_hybrid_search,
)


class TestBM25Tokenization:
    """Test BM25 tokenization functionality."""

    def test_basic_tokenization(self):
        """Test basic tokenization."""
        tokens = BM25.tokenize("Hello World")
        assert tokens == ["hello", "world"]

    def test_tokenization_lowercase(self):
        """Test that tokenization converts to lowercase."""
        tokens = BM25.tokenize("OAuth2 Authentication REST API")
        assert "oauth2" in tokens
        assert "authentication" in tokens
        assert "rest" in tokens
        assert "api" in tokens

    def test_tokenization_filters_short_tokens(self):
        """Test that single character tokens are filtered."""
        tokens = BM25.tokenize("a b cd efg")
        assert "a" not in tokens
        assert "b" not in tokens
        assert "cd" in tokens
        assert "efg" in tokens

    def test_tokenization_handles_punctuation(self):
        """Test tokenization with punctuation."""
        tokens = BM25.tokenize("POST /api/users - Create user")
        assert "post" in tokens
        assert "api" in tokens
        assert "users" in tokens
        assert "create" in tokens
        assert "user" in tokens

    def test_tokenization_handles_underscores(self):
        """Test that underscores are preserved in tokens."""
        tokens = BM25.tokenize("user_id auth_token")
        assert "user_id" in tokens
        assert "auth_token" in tokens

    def test_tokenization_empty_string(self):
        """Test tokenization with empty string."""
        tokens = BM25.tokenize("")
        assert tokens == []

    def test_tokenization_special_characters(self):
        """Test tokenization with special characters."""
        tokens = BM25.tokenize("@#$%^&*()")
        assert tokens == []


class TestBM25Indexing:
    """Test BM25 indexing and fitting."""

    def test_fit_basic_corpus(self):
        """Test fitting BM25 on a basic corpus."""
        bm25 = BM25()
        corpus = [
            "The quick brown fox",
            "jumps over the lazy dog",
            "The dog is lazy",
        ]
        doc_ids = ["doc1", "doc2", "doc3"]

        bm25.fit(corpus, doc_ids)

        assert bm25.num_docs == 3
        assert bm25.doc_ids == doc_ids
        assert len(bm25.doc_freqs) == 3
        assert bm25.avgdl > 0
        assert len(bm25.idf) > 0

    def test_fit_auto_generates_doc_ids(self):
        """Test that doc IDs are auto-generated if not provided."""
        bm25 = BM25()
        corpus = ["document one", "document two"]

        bm25.fit(corpus)

        assert bm25.doc_ids == ["doc_0", "doc_1"]

    def test_fit_calculates_idf(self):
        """Test that IDF is calculated correctly."""
        bm25 = BM25()
        corpus = [
            "the cat sat",
            "the dog sat",
            "the bird flew",
        ]

        bm25.fit(corpus)

        # "the" appears in all documents, should have lower IDF
        # "cat" appears in only one document, should have higher IDF
        assert "the" in bm25.idf
        assert "cat" in bm25.idf
        assert bm25.idf["cat"] > bm25.idf["the"]

    def test_fit_calculates_average_doc_length(self):
        """Test that average document length is calculated."""
        bm25 = BM25()
        corpus = [
            "short doc",
            "this is a much longer document",
        ]

        bm25.fit(corpus)

        # Average should be between 2 and 6
        assert 2 < bm25.avgdl < 7

    def test_fit_raises_error_on_mismatched_doc_ids(self):
        """Test that fit raises error if doc_ids length doesn't match corpus."""
        bm25 = BM25()
        corpus = ["doc1", "doc2"]
        doc_ids = ["id1"]  # Wrong length

        with pytest.raises(ValueError, match="doc_ids length must match corpus length"):
            bm25.fit(corpus, doc_ids)


class TestBM25Scoring:
    """Test BM25 scoring functionality."""

    def test_score_exact_match(self):
        """Test scoring for exact match query."""
        bm25 = BM25()
        corpus = [
            "OAuth2 authentication",
            "JWT token validation",
            "Basic authentication",
        ]
        bm25.fit(corpus)

        # Query that exactly matches first document
        score_0 = bm25.score("OAuth2 authentication", 0)
        score_1 = bm25.score("OAuth2 authentication", 1)

        # First document should score higher
        assert score_0 > score_1

    def test_score_partial_match(self):
        """Test scoring for partial match."""
        bm25 = BM25()
        corpus = [
            "REST API authentication",
            "GraphQL API",
            "SOAP web service",
        ]
        bm25.fit(corpus)

        # Query with "API" should match first two documents
        score_0 = bm25.score("API", 0)
        score_1 = bm25.score("API", 1)
        score_2 = bm25.score("API", 2)

        assert score_0 > 0
        assert score_1 > 0
        assert score_2 == 0  # No "API" in third document

    def test_score_no_match(self):
        """Test scoring when query doesn't match."""
        bm25 = BM25()
        corpus = ["document about cats", "document about dogs"]
        bm25.fit(corpus)

        # Query for "birds" should score 0
        score = bm25.score("birds", 0)
        assert score == 0

    def test_score_with_k1_parameter(self):
        """Test that k1 parameter affects scoring."""
        corpus = ["test document with repeated word word word"]

        # Lower k1 should saturate faster
        bm25_low = BM25(k1=0.5)
        bm25_low.fit(corpus)
        score_low = bm25_low.score("word", 0)

        # Higher k1 should allow higher scores for repeated terms
        bm25_high = BM25(k1=2.0)
        bm25_high.fit(corpus)
        score_high = bm25_high.score("word", 0)

        # With higher k1, repeated terms should score higher
        assert score_high > score_low

    def test_score_with_b_parameter(self):
        """Test that b parameter affects length normalization."""
        # Short and long documents
        corpus = [
            "short",
            "this is a much longer document with many words",
        ]

        # No length normalization (b=0)
        bm25_no_norm = BM25(b=0.0)
        bm25_no_norm.fit(corpus)

        # Full length normalization (b=1)
        bm25_full_norm = BM25(b=1.0)
        bm25_full_norm.fit(corpus)

        # Scores should differ based on normalization
        # (exact values depend on IDF, but they should be different)
        score_no_norm = bm25_no_norm.score("document", 1)
        score_full_norm = bm25_full_norm.score("document", 1)

        assert score_no_norm != score_full_norm


class TestBM25Search:
    """Test BM25 search functionality."""

    def test_search_returns_top_k(self):
        """Test that search returns correct number of results."""
        bm25 = BM25()
        corpus = [f"document {i}" for i in range(10)]
        bm25.fit(corpus)

        results = bm25.search("document", top_k=5)

        assert len(results) == 5

    def test_search_returns_ranked_results(self):
        """Test that search returns results in descending score order."""
        bm25 = BM25()
        corpus = [
            "OAuth2 authentication flow",
            "OAuth2 is a protocol",
            "JWT token",
        ]
        doc_ids = ["doc1", "doc2", "doc3"]
        bm25.fit(corpus, doc_ids)

        results = bm25.search("OAuth2", top_k=3)

        # Should return 2 results (only first two have "OAuth2")
        assert len(results) == 2

        # Check that results are tuples of (doc_id, score)
        assert all(isinstance(r, tuple) and len(r) == 2 for r in results)

        # Scores should be in descending order
        scores = [score for _, score in results]
        assert scores == sorted(scores, reverse=True)

    def test_search_filters_zero_scores(self):
        """Test that search filters out zero-score results."""
        bm25 = BM25()
        corpus = [
            "cat document",
            "dog document",
            "bird document",
        ]
        bm25.fit(corpus)

        # Search for "cat" should only return one result
        results = bm25.search("cat", top_k=10)

        assert len(results) == 1
        assert results[0][0] == "doc_0"

    def test_search_empty_corpus(self):
        """Test search on empty corpus."""
        bm25 = BM25()
        results = bm25.search("query", top_k=5)

        assert results == []

    def test_search_returns_doc_ids_and_scores(self):
        """Test that search returns correct doc IDs and scores."""
        bm25 = BM25()
        corpus = ["authentication method", "authorization header"]
        doc_ids = ["auth1", "auth2"]
        bm25.fit(corpus, doc_ids)

        results = bm25.search("authentication", top_k=10)

        assert len(results) == 1
        doc_id, score = results[0]
        assert doc_id == "auth1"
        assert score > 0


class TestSearchResult:
    """Test SearchResult dataclass."""

    def test_search_result_creation(self):
        """Test creating SearchResult."""
        result = SearchResult(
            doc_id="doc1",
            content="test content",
            metadata={"key": "value"},
            score=0.95,
            method="vector",
        )

        assert result.doc_id == "doc1"
        assert result.content == "test content"
        assert result.metadata == {"key": "value"}
        assert result.score == 0.95
        assert result.method == "vector"
        assert result.rank == 0

    def test_search_result_with_rank(self):
        """Test SearchResult with rank."""
        result = SearchResult(
            doc_id="doc1",
            content="content",
            metadata={},
            score=0.8,
            method="bm25",
            rank=5,
        )

        assert result.rank == 5


class TestReciprocalRankFusion:
    """Test Reciprocal Rank Fusion (RRF)."""

    def test_rrf_merges_results(self):
        """Test that RRF merges results from both methods."""
        bm25_results = [("doc1", 10.0), ("doc2", 5.0)]
        vector_results = [
            SearchResult("doc2", "content2", {}, 0.9, "vector"),
            SearchResult("doc3", "content3", {}, 0.8, "vector"),
        ]

        merged = HybridSearch.reciprocal_rank_fusion(bm25_results, vector_results, k=60)

        # Should have 3 unique documents
        doc_ids = [doc_id for doc_id, _ in merged]
        assert len(doc_ids) == 3
        assert "doc1" in doc_ids
        assert "doc2" in doc_ids
        assert "doc3" in doc_ids

    def test_rrf_scores_descending(self):
        """Test that RRF returns results in descending score order."""
        bm25_results = [("doc1", 10.0), ("doc2", 5.0)]
        vector_results = [
            SearchResult("doc3", "content3", {}, 0.9, "vector"),
        ]

        merged = HybridSearch.reciprocal_rank_fusion(bm25_results, vector_results)

        scores = [score for _, score in merged]
        assert scores == sorted(scores, reverse=True)

    def test_rrf_handles_empty_bm25(self):
        """Test RRF with empty BM25 results."""
        bm25_results = []
        vector_results = [
            SearchResult("doc1", "content1", {}, 0.9, "vector"),
        ]

        merged = HybridSearch.reciprocal_rank_fusion(bm25_results, vector_results)

        assert len(merged) == 1
        assert merged[0][0] == "doc1"

    def test_rrf_handles_empty_vector(self):
        """Test RRF with empty vector results."""
        bm25_results = [("doc1", 10.0)]
        vector_results = []

        merged = HybridSearch.reciprocal_rank_fusion(bm25_results, vector_results)

        assert len(merged) == 1
        assert merged[0][0] == "doc1"

    def test_rrf_handles_both_empty(self):
        """Test RRF with both empty."""
        merged = HybridSearch.reciprocal_rank_fusion([], [])

        assert merged == []

    def test_rrf_k_parameter_affects_scores(self):
        """Test that k parameter affects RRF scores."""
        bm25_results = [("doc1", 10.0)]
        vector_results = [SearchResult("doc1", "content", {}, 0.9, "vector")]

        # Lower k gives more weight to rank differences
        merged_low_k = HybridSearch.reciprocal_rank_fusion(
            bm25_results, vector_results, k=10
        )

        # Higher k reduces impact of rank differences
        merged_high_k = HybridSearch.reciprocal_rank_fusion(
            bm25_results, vector_results, k=100
        )

        # Scores should be different
        score_low_k = merged_low_k[0][1]
        score_high_k = merged_high_k[0][1]

        assert score_low_k != score_high_k


class TestWeightedScoreFusion:
    """Test Weighted Score Fusion."""

    def test_weighted_fusion_combines_scores(self):
        """Test that weighted fusion combines scores."""
        bm25_results = [("doc1", 10.0), ("doc2", 5.0)]
        vector_results = [
            SearchResult("doc2", "content2", {}, 0.9, "vector"),
            SearchResult("doc3", "content3", {}, 0.8, "vector"),
        ]

        merged = HybridSearch.weighted_score_fusion(
            bm25_results, vector_results, bm25_weight=0.5, vector_weight=0.5
        )

        # Should have 3 unique documents
        assert len(merged) == 3

    def test_weighted_fusion_normalizes_bm25_scores(self):
        """Test that BM25 scores are normalized."""
        bm25_results = [("doc1", 100.0), ("doc2", 50.0)]
        vector_results = []

        merged = HybridSearch.weighted_score_fusion(
            bm25_results, vector_results, bm25_weight=1.0, vector_weight=0.0
        )

        # After normalization, scores should be relative to max (100.0)
        scores = [score for _, score in merged]
        assert max(scores) <= 1.0

    def test_weighted_fusion_respects_weights(self):
        """Test that weights affect final scores."""
        # Use different documents with different scores
        bm25_results = [("doc1", 10.0), ("doc2", 5.0)]
        vector_results = [
            SearchResult("doc1", "content", {}, 0.5, "vector"),
            SearchResult("doc2", "content", {}, 0.9, "vector"),
        ]

        # More weight to BM25
        merged_bm25_heavy = HybridSearch.weighted_score_fusion(
            bm25_results, vector_results, bm25_weight=0.8, vector_weight=0.2
        )

        # More weight to vector
        merged_vector_heavy = HybridSearch.weighted_score_fusion(
            bm25_results, vector_results, bm25_weight=0.2, vector_weight=0.8
        )

        # Get scores for doc1
        score_bm25_heavy = next(s for d, s in merged_bm25_heavy if d == "doc1")
        score_vector_heavy = next(s for d, s in merged_vector_heavy if d == "doc1")

        # BM25-heavy should favor doc1 (higher BM25 score=10.0, lower vector=0.5)
        # Vector-heavy should penalize doc1 (lower vector score)
        assert score_bm25_heavy > score_vector_heavy


class TestHybridSearch:
    """Test HybridSearch class."""

    def test_hybrid_search_initialization(self):
        """Test HybridSearch initialization."""
        hybrid = HybridSearch(bm25_weight=0.6, vector_weight=0.4, rrf_k=50)

        assert hybrid.bm25_weight == 0.6
        assert hybrid.vector_weight == 0.4
        assert hybrid.rrf_k == 50

    def test_hybrid_search_normalizes_weights(self):
        """Test that weights are normalized to sum to 1.0."""
        hybrid = HybridSearch(bm25_weight=0.6, vector_weight=0.6)

        # Weights should be normalized to sum to 1.0
        assert abs((hybrid.bm25_weight + hybrid.vector_weight) - 1.0) < 0.01


class TestHelperFunctions:
    """Test helper functions."""

    def test_create_bm25_index(self):
        """Test create_bm25_index helper."""
        documents = [
            {"id": "doc1", "content": "first document"},
            {"id": "doc2", "content": "second document"},
        ]

        bm25 = create_bm25_index(documents)

        assert bm25.num_docs == 2
        assert bm25.doc_ids == ["doc1", "doc2"]

    def test_create_bm25_index_custom_fields(self):
        """Test create_bm25_index with custom field names."""
        documents = [
            {"my_id": "id1", "my_text": "text 1"},
            {"my_id": "id2", "my_text": "text 2"},
        ]

        bm25 = create_bm25_index(
            documents, content_field="my_text", id_field="my_id"
        )

        assert bm25.doc_ids == ["id1", "id2"]

    def test_create_bm25_index_custom_parameters(self):
        """Test create_bm25_index with custom k1 and b."""
        documents = [{"id": "doc1", "content": "document"}]

        bm25 = create_bm25_index(documents, k1=2.0, b=0.5)

        assert bm25.k1 == 2.0
        assert bm25.b == 0.5

    def test_get_bm25(self):
        """Test get_bm25 convenience function."""
        bm25 = get_bm25(k1=1.2, b=0.8)

        assert isinstance(bm25, BM25)
        assert bm25.k1 == 1.2
        assert bm25.b == 0.8

    def test_get_hybrid_search(self):
        """Test get_hybrid_search convenience function."""
        hybrid = get_hybrid_search(
            bm25_weight=0.7, vector_weight=0.3, rrf_k=70
        )

        assert isinstance(hybrid, HybridSearch)
        assert hybrid.bm25_weight == 0.7
        assert hybrid.vector_weight == 0.3
        assert hybrid.rrf_k == 70


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_bm25_with_single_document(self):
        """Test BM25 with single document corpus."""
        bm25 = BM25()
        bm25.fit(["single document"])

        results = bm25.search("document", top_k=5)

        assert len(results) == 1

    def test_bm25_with_very_long_document(self):
        """Test BM25 with very long document."""
        bm25 = BM25()
        long_doc = " ".join(["word"] * 1000)
        short_doc = "word appears once"
        bm25.fit([long_doc, short_doc])

        # Should not crash and return both documents
        results = bm25.search("word", top_k=2)
        assert len(results) == 2

    def test_bm25_with_duplicate_documents(self):
        """Test BM25 with duplicate documents."""
        bm25 = BM25()
        corpus = ["same document", "same document", "different"]
        bm25.fit(corpus)

        results = bm25.search("same", top_k=10)

        # Should return all matching documents
        assert len(results) == 2

    def test_search_with_very_long_query(self):
        """Test search with very long query."""
        bm25 = BM25()
        bm25.fit(["normal document"])

        long_query = " ".join(["word"] * 100)
        results = bm25.search(long_query, top_k=5)

        # Should not crash
        assert isinstance(results, list)

    def test_search_with_special_characters_in_query(self):
        """Test search with special characters."""
        bm25 = BM25()
        bm25.fit(["normal document"])

        results = bm25.search("@#$%^&*()", top_k=5)

        # Should return empty results (no matching tokens)
        assert results == []


class TestIntegrationScenarios:
    """Test realistic integration scenarios."""

    def test_api_documentation_search(self):
        """Test BM25 on API documentation."""
        bm25 = BM25()
        corpus = [
            "POST /api/users - Create a new user with OAuth2 authentication",
            "GET /api/users/{id} - Retrieve user details using JWT token",
            "DELETE /api/users/{id} - Delete user account",
            "PUT /api/users/{id} - Update user information",
        ]
        doc_ids = ["create_user", "get_user", "delete_user", "update_user"]
        bm25.fit(corpus, doc_ids)

        # Search for OAuth2
        results = bm25.search("OAuth2", top_k=5)
        assert len(results) >= 1
        assert results[0][0] == "create_user"

        # Search for DELETE
        results = bm25.search("DELETE", top_k=5)
        assert len(results) >= 1
        assert results[0][0] == "delete_user"

    def test_acronym_search(self):
        """Test BM25 with acronyms."""
        bm25 = BM25()
        corpus = [
            "REST API authentication",
            "GraphQL API endpoint",
            "SOAP web service",
            "JWT token validation",
        ]
        bm25.fit(corpus)

        # Search for "API"
        results = bm25.search("API", top_k=10)

        # Should find first two documents
        assert len(results) == 2

    def test_technical_terms_search(self):
        """Test BM25 with technical terms."""
        bm25 = BM25()
        corpus = [
            "OAuth2 authorization code flow",
            "OAuth2 client credentials grant",
            "Basic authentication header",
            "Bearer token authorization",
        ]
        bm25.fit(corpus)

        # Search for "OAuth2"
        results = bm25.search("OAuth2", top_k=10)

        # Should find first two documents
        assert len(results) == 2
        scores = [score for _, score in results]
        # Both should have similar scores (both have "OAuth2")
        assert abs(scores[0] - scores[1]) < scores[0] * 0.5  # Within 50%
