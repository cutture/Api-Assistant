"""
Tests for cross-encoder re-ranking module.

Tests cross-encoder based re-ranking functionality including:
- CrossEncoderReranker initialization and configuration
- Re-ranking of search results
- Caching of re-rank scores
- Score pair computation
- Integration with different models
"""

import pytest

from src.core.cross_encoder import (
    CrossEncoderReranker,
    RerankResult,
    get_cross_encoder_reranker,
    rerank_results,
)


class TestRerankResult:
    """Test RerankResult dataclass."""

    def test_rerank_result_creation(self):
        """Test creating a RerankResult instance."""
        result = RerankResult(
            doc_id="doc1",
            content="Sample content",
            metadata={"category": "test"},
            original_score=0.8,
            rerank_score=0.9,
            original_rank=2,
            rerank_rank=1,
        )

        assert result.doc_id == "doc1"
        assert result.content == "Sample content"
        assert result.metadata == {"category": "test"}
        assert result.original_score == 0.8
        assert result.rerank_score == 0.9
        assert result.original_rank == 2
        assert result.rerank_rank == 1
        assert result.method == "cross_encoder"

    def test_rerank_result_to_dict(self):
        """Test converting RerankResult to dictionary."""
        result = RerankResult(
            doc_id="doc1",
            content="Test content",
            metadata={"key": "value"},
            original_score=0.5,
            rerank_score=0.7,
            original_rank=3,
            rerank_rank=1,
        )

        result_dict = result.to_dict()

        assert result_dict["doc_id"] == "doc1"
        assert result_dict["content"] == "Test content"
        assert result_dict["metadata"] == {"key": "value"}
        assert result_dict["score"] == 0.7  # Uses rerank_score
        assert result_dict["original_score"] == 0.5
        assert result_dict["original_rank"] == 3
        assert result_dict["rank"] == 1
        assert result_dict["method"] == "cross_encoder"


class TestCrossEncoderRerankerInit:
    """Test CrossEncoderReranker initialization."""

    def test_init_with_defaults(self):
        """Test initialization with default parameters."""
        reranker = CrossEncoderReranker()

        assert reranker.model_name == "ms-marco-mini-lm-6"
        assert reranker.max_length == 512
        assert reranker.batch_size == 32
        assert reranker.use_cache is True
        assert reranker.model is not None
        assert reranker.cache is not None

    def test_init_with_custom_params(self):
        """Test initialization with custom parameters."""
        reranker = CrossEncoderReranker(
            model_name="ms-marco-mini-lm-6",
            max_length=256,
            batch_size=16,
            use_cache=False,
        )

        assert reranker.model_name == "ms-marco-mini-lm-6"
        assert reranker.max_length == 256
        assert reranker.batch_size == 16
        assert reranker.use_cache is False
        assert reranker.cache is None

    def test_model_loading(self):
        """Test that model is loaded successfully."""
        reranker = CrossEncoderReranker(model_name="ms-marco-mini-lm-6")

        # Should have loaded the model
        assert reranker.model is not None
        # Model should be able to make predictions
        assert hasattr(reranker.model, "predict")


class TestCrossEncoderReranking:
    """Test cross-encoder re-ranking functionality."""

    @pytest.fixture
    def reranker(self):
        """Create a reranker instance for testing."""
        return CrossEncoderReranker(model_name="ms-marco-mini-lm-6", use_cache=True)

    @pytest.fixture
    def sample_results(self):
        """Sample search results for testing."""
        return [
            {
                "id": "doc1",
                "content": "Python is a programming language",
                "metadata": {"category": "programming"},
                "score": 0.5,
            },
            {
                "id": "doc2",
                "content": "Java is also a programming language",
                "metadata": {"category": "programming"},
                "score": 0.6,
            },
            {
                "id": "doc3",
                "content": "Machine learning uses Python",
                "metadata": {"category": "ml"},
                "score": 0.4,
            },
        ]

    def test_rerank_basic(self, reranker, sample_results):
        """Test basic re-ranking functionality."""
        query = "Python programming"
        reranked = reranker.rerank(query, sample_results)

        # Should return results
        assert len(reranked) == 3
        assert all(isinstance(r, RerankResult) for r in reranked)

        # Results should be sorted by rerank_score (descending)
        scores = [r.rerank_score for r in reranked]
        assert scores == sorted(scores, reverse=True)

        # Original ranks should be preserved
        assert all(r.original_rank > 0 for r in reranked)

        # Rerank ranks should be sequential
        rerank_ranks = [r.rerank_rank for r in reranked]
        assert rerank_ranks == [1, 2, 3]

    def test_rerank_with_top_k(self, reranker, sample_results):
        """Test re-ranking with top_k limit."""
        query = "Python"
        reranked = reranker.rerank(query, sample_results, top_k=2)

        assert len(reranked) == 2
        # Should return only top 2 results
        assert reranked[0].rerank_rank == 1
        assert reranked[1].rerank_rank == 2

    def test_rerank_empty_results(self, reranker):
        """Test re-ranking with empty results list."""
        query = "test"
        reranked = reranker.rerank(query, [])

        assert reranked == []

    def test_rerank_single_result(self, reranker):
        """Test re-ranking with single result."""
        query = "Python"
        results = [
            {
                "id": "doc1",
                "content": "Python programming",
                "metadata": {},
                "score": 0.5,
            }
        ]

        reranked = reranker.rerank(query, results)

        assert len(reranked) == 1
        assert reranked[0].doc_id == "doc1"
        assert reranked[0].rerank_rank == 1

    def test_rerank_relevance_scores(self, reranker):
        """Test that re-ranking produces meaningful scores."""
        query = "Python programming"

        results = [
            {
                "id": "doc1",
                "content": "Python is great for programming",
                "metadata": {},
                "score": 0.5,
            },
            {
                "id": "doc2",
                "content": "Cooking recipes for dinner",
                "metadata": {},
                "score": 0.6,  # Higher initial score
            },
        ]

        reranked = reranker.rerank(query, results)

        # doc1 should be ranked higher (more relevant to query)
        assert reranked[0].doc_id == "doc1"
        assert reranked[1].doc_id == "doc2"

    def test_rerank_to_dicts(self, reranker, sample_results):
        """Test rerank_to_dicts method."""
        query = "Python"
        reranked_dicts = reranker.rerank_to_dicts(query, sample_results, top_k=2)

        assert len(reranked_dicts) == 2
        assert all(isinstance(d, dict) for d in reranked_dicts)
        assert all("doc_id" in d and "content" in d and "score" in d for d in reranked_dicts)


class TestCrossEncoderScoring:
    """Test cross-encoder scoring functionality."""

    @pytest.fixture
    def reranker(self):
        """Create a reranker instance for testing."""
        return CrossEncoderReranker(model_name="ms-marco-mini-lm-6")

    def test_compute_scores(self, reranker):
        """Test _compute_scores method."""
        query = "Python programming"
        documents = [
            "Python is a programming language",
            "Java is also a programming language",
            "Cooking recipes",
        ]

        scores = reranker._compute_scores(query, documents)

        # Should return same number of scores as documents
        assert len(scores) == len(documents)

        # Scores should be numeric
        assert all(isinstance(s, float) for s in scores)

        # Most relevant doc should have highest score
        assert scores[0] > scores[2]  # Python doc > Cooking doc

    def test_score_pairs(self, reranker):
        """Test score_pairs method."""
        pairs = [
            ("Python", "Python is a programming language"),
            ("Java", "Java programming tutorial"),
            ("cooking", "Python programming"),  # Mismatched pair
        ]

        scores = reranker.score_pairs(pairs)

        assert len(scores) == 3
        assert all(isinstance(s, float) for s in scores)

        # Matched pairs should score higher than mismatched
        assert scores[0] > scores[2]
        assert scores[1] > scores[2]

    def test_score_pairs_empty(self, reranker):
        """Test score_pairs with empty list."""
        scores = reranker.score_pairs([])
        assert scores == []


class TestCrossEncoderCaching:
    """Test cross-encoder caching functionality."""

    def test_caching_enabled(self):
        """Test that caching works when enabled."""
        reranker = CrossEncoderReranker(use_cache=True)
        query = "test query"
        documents = ["test document 1", "test document 2"]

        # First call - should compute scores
        scores1 = reranker._compute_scores(query, documents)

        # Second call - should use cache
        scores2 = reranker._compute_scores(query, documents)

        # Scores should be identical
        assert scores1 == scores2

        # Cache should have entries
        cache_stats = reranker.get_cache_stats()
        assert cache_stats is not None
        assert cache_stats["size"] > 0

    def test_caching_disabled(self):
        """Test that caching can be disabled."""
        reranker = CrossEncoderReranker(use_cache=False)

        # Should not have cache
        assert reranker.cache is None

        # get_cache_stats should return None
        assert reranker.get_cache_stats() is None

    def test_clear_cache(self):
        """Test cache clearing."""
        reranker = CrossEncoderReranker(use_cache=True)

        # Add some entries to cache
        query = "test"
        documents = ["doc1", "doc2"]
        reranker._compute_scores(query, documents)

        # Cache should have entries
        stats_before = reranker.get_cache_stats()
        assert stats_before["size"] > 0

        # Clear cache
        reranker.clear_cache()

        # Cache should be empty
        stats_after = reranker.get_cache_stats()
        assert stats_after["size"] == 0


class TestConvenienceFunctions:
    """Test convenience functions."""

    def test_get_cross_encoder_reranker(self):
        """Test get_cross_encoder_reranker function."""
        reranker = get_cross_encoder_reranker()

        assert isinstance(reranker, CrossEncoderReranker)
        assert reranker.model_name == "ms-marco-mini-lm-6"
        assert reranker.use_cache is True

    def test_get_cross_encoder_reranker_custom(self):
        """Test get_cross_encoder_reranker with custom params."""
        reranker = get_cross_encoder_reranker(
            model_name="ms-marco-mini-lm-6",
            use_cache=False,
        )

        assert isinstance(reranker, CrossEncoderReranker)
        assert reranker.use_cache is False

    def test_rerank_results_helper(self):
        """Test rerank_results helper function."""
        query = "Python programming"
        results = [
            {
                "id": "doc1",
                "content": "Python is great",
                "metadata": {},
                "score": 0.5,
            },
            {
                "id": "doc2",
                "content": "Java tutorial",
                "metadata": {},
                "score": 0.6,
            },
        ]

        reranked = rerank_results(query, results, top_k=2)

        assert isinstance(reranked, list)
        assert len(reranked) <= 2
        assert all(isinstance(r, dict) for r in reranked)


class TestEdgeCases:
    """Test edge cases and error handling."""

    @pytest.fixture
    def reranker(self):
        """Create a reranker instance for testing."""
        return CrossEncoderReranker()

    def test_rerank_missing_content(self, reranker):
        """Test re-ranking with missing content field."""
        query = "test"
        results = [
            {
                "id": "doc1",
                # Missing "content" field
                "metadata": {},
                "score": 0.5,
            }
        ]

        reranked = reranker.rerank(query, results)

        # Should handle missing content gracefully (empty string)
        assert len(reranked) == 1
        assert reranked[0].content == ""

    def test_rerank_missing_metadata(self, reranker):
        """Test re-ranking with missing metadata."""
        query = "test"
        results = [
            {
                "id": "doc1",
                "content": "Test content",
                # Missing "metadata" field
                "score": 0.5,
            }
        ]

        reranked = reranker.rerank(query, results)

        # Should handle missing metadata gracefully (empty dict)
        assert len(reranked) == 1
        assert reranked[0].metadata == {}

    def test_rerank_very_long_content(self, reranker):
        """Test re-ranking with very long content."""
        query = "test"
        long_content = " ".join(["word"] * 1000)  # Very long document

        results = [
            {
                "id": "doc1",
                "content": long_content,
                "metadata": {},
                "score": 0.5,
            }
        ]

        # Should not crash with long content (will be truncated by model)
        reranked = reranker.rerank(query, results)
        assert len(reranked) == 1

    def test_rerank_special_characters(self, reranker):
        """Test re-ranking with special characters."""
        query = "test @#$%"
        results = [
            {
                "id": "doc1",
                "content": "Special chars: @#$% & more!",
                "metadata": {},
                "score": 0.5,
            }
        ]

        # Should handle special characters
        reranked = reranker.rerank(query, results)
        assert len(reranked) == 1

    def test_rerank_unicode_content(self, reranker):
        """Test re-ranking with unicode content."""
        query = "测试"  # Chinese characters
        results = [
            {
                "id": "doc1",
                "content": "测试内容 test content",
                "metadata": {},
                "score": 0.5,
            }
        ]

        # Should handle unicode
        reranked = reranker.rerank(query, results)
        assert len(reranked) == 1


class TestIntegrationScenarios:
    """Test real-world integration scenarios."""

    @pytest.fixture
    def reranker(self):
        """Create a reranker instance for testing."""
        return CrossEncoderReranker()

    def test_api_documentation_reranking(self, reranker):
        """Test re-ranking API documentation results."""
        query = "authentication with OAuth2"

        results = [
            {
                "id": "doc1",
                "content": "POST /api/users - Create a new user",
                "metadata": {"endpoint": "POST /api/users"},
                "score": 0.6,
            },
            {
                "id": "doc2",
                "content": "POST /api/auth/login - Authenticate using OAuth2",
                "metadata": {"endpoint": "POST /api/auth/login"},
                "score": 0.5,
            },
            {
                "id": "doc3",
                "content": "GET /api/products - List all products",
                "metadata": {"endpoint": "GET /api/products"},
                "score": 0.4,
            },
        ]

        reranked = reranker.rerank(query, results)

        # OAuth2 authentication doc should be ranked first
        assert reranked[0].doc_id == "doc2"
        # Products endpoint should be last (least relevant)
        assert reranked[-1].doc_id == "doc3"

    def test_technical_documentation_reranking(self, reranker):
        """Test re-ranking technical documentation."""
        query = "how to handle errors in Python"

        results = [
            {
                "id": "doc1",
                "content": "Python error handling uses try-except blocks",
                "metadata": {},
                "score": 0.5,
            },
            {
                "id": "doc2",
                "content": "Java exception handling tutorial",
                "metadata": {},
                "score": 0.6,  # Higher initial score
            },
            {
                "id": "doc3",
                "content": "Python best practices for exception handling",
                "metadata": {},
                "score": 0.4,
            },
        ]

        reranked = reranker.rerank(query, results)

        # Python docs should rank higher than Java doc
        assert reranked[0].doc_id in ["doc1", "doc3"]
        assert reranked[-1].doc_id == "doc2"

    def test_improves_ranking_quality(self, reranker):
        """Test that cross-encoder actually improves ranking quality."""
        query = "Python machine learning"

        results = [
            {
                "id": "doc1",
                "content": "Python",  # Short, matches keyword
                "metadata": {},
                "score": 0.8,  # High initial score
            },
            {
                "id": "doc2",
                "content": "Python is widely used for machine learning and AI",
                "metadata": {},
                "score": 0.5,  # Lower initial score
            },
        ]

        reranked = reranker.rerank(query, results)

        # More relevant doc should rank first despite lower initial score
        assert reranked[0].doc_id == "doc2"
        # Cross-encoder should recognize relevance beyond keyword matching
        assert reranked[0].rerank_score > reranked[1].rerank_score
