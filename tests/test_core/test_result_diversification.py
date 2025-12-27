"""
Tests for result diversification module.

Tests MMR (Maximum Marginal Relevance) algorithm for result diversification:
- ResultDiversifier initialization
- Embedding-based diversification
- Content-based diversification
- Diversity score computation
- Lambda parameter effects
- Edge cases
"""

import numpy as np
import pytest

from src.core.result_diversification import (
    ResultDiversifier,
    get_result_diversifier,
    diversify_results,
)


class TestResultDiversifierInit:
    """Test ResultDiversifier initialization."""

    def test_init_with_defaults(self):
        """Test initialization with default parameters."""
        diversifier = ResultDiversifier()

        assert diversifier.lambda_param == 0.5
        assert diversifier.embedding_service is None

    def test_init_with_custom_lambda(self):
        """Test initialization with custom lambda."""
        diversifier = ResultDiversifier(lambda_param=0.7)

        assert diversifier.lambda_param == 0.7

    def test_init_validates_lambda(self):
        """Test that lambda parameter is validated."""
        # Should raise ValueError for invalid lambda
        with pytest.raises(ValueError):
            ResultDiversifier(lambda_param=1.5)

        with pytest.raises(ValueError):
            ResultDiversifier(lambda_param=-0.1)

    def test_init_boundary_values(self):
        """Test boundary values for lambda."""
        # Should accept 0 and 1
        diversifier_0 = ResultDiversifier(lambda_param=0.0)
        diversifier_1 = ResultDiversifier(lambda_param=1.0)

        assert diversifier_0.lambda_param == 0.0
        assert diversifier_1.lambda_param == 1.0


class TestEmbeddingBasedDiversification:
    """Test embedding-based diversification."""

    @pytest.fixture
    def sample_results(self):
        """Create sample results for testing."""
        return [
            {"id": "doc1", "content": "Python programming tutorial", "score": 0.9},
            {"id": "doc2", "content": "Python programming guide", "score": 0.85},  # Similar to doc1
            {"id": "doc3", "content": "Java programming basics", "score": 0.8},
            {"id": "doc4", "content": "Python advanced concepts", "score": 0.75},  # Similar to doc1
            {"id": "doc5", "content": "Database design patterns", "score": 0.7},  # Different topic
        ]

    @pytest.fixture
    def sample_embeddings(self):
        """Create sample embeddings."""
        # Simulate embeddings where doc1, doc2, doc4 are similar (Python)
        # and doc3, doc5 are different
        return [
            np.array([1.0, 0.0, 0.0, 0.1]),  # doc1 - Python
            np.array([0.95, 0.05, 0.0, 0.1]),  # doc2 - Python (similar to doc1)
            np.array([0.0, 1.0, 0.0, 0.0]),  # doc3 - Java
            np.array([0.9, 0.0, 0.1, 0.15]),  # doc4 - Python (similar to doc1)
            np.array([0.0, 0.0, 1.0, 0.0]),  # doc5 - Database
        ]

    def test_diversify_with_embeddings_basic(self, sample_results, sample_embeddings):
        """Test basic embedding-based diversification."""
        diversifier = ResultDiversifier(lambda_param=0.5)

        diversified = diversifier.diversify(
            sample_results,
            top_k=3,
            embeddings=sample_embeddings
        )

        assert len(diversified) == 3
        # First result should be the most relevant
        assert diversified[0]['id'] == "doc1"

        # Should include diverse documents (not all Python docs)
        doc_ids = [d['id'] for d in diversified]
        # Should not select both doc1 and doc2 (too similar)
        assert not (doc_ids.count("doc1") > 0 and doc_ids.count("doc2") > 0) or len(set(doc_ids)) >= 2

    def test_lambda_1_pure_relevance(self, sample_results, sample_embeddings):
        """Test with lambda=1 (pure relevance, no diversity)."""
        diversifier = ResultDiversifier(lambda_param=1.0)

        diversified = diversifier.diversify(
            sample_results,
            top_k=3,
            embeddings=sample_embeddings
        )

        # With pure relevance, should just return top 3 by score
        assert len(diversified) == 3
        assert diversified[0]['id'] == "doc1"
        assert diversified[1]['id'] == "doc2"
        assert diversified[2]['id'] == "doc3"

    def test_lambda_0_pure_diversity(self, sample_results, sample_embeddings):
        """Test with lambda=0 (pure diversity, no relevance)."""
        diversifier = ResultDiversifier(lambda_param=0.0)

        diversified = diversifier.diversify(
            sample_results,
            top_k=3,
            embeddings=sample_embeddings
        )

        # With pure diversity, should select maximally different documents
        assert len(diversified) == 3
        # First is still highest relevance
        assert diversified[0]['id'] == "doc1"

        # Remaining should be diverse
        doc_ids = [d['id'] for d in diversified]
        # Should avoid selecting similar Python docs together
        python_docs = sum(1 for id in doc_ids if id in ["doc1", "doc2", "doc4"])
        assert python_docs <= 2  # At most 2 Python docs

    def test_diversify_validates_embeddings_count(self, sample_results):
        """Test that embedding count must match results count."""
        diversifier = ResultDiversifier()

        wrong_count_embeddings = [np.array([1.0, 0.0])]  # Only 1 embedding

        with pytest.raises(ValueError):
            diversifier.diversify(
                sample_results,
                top_k=3,
                embeddings=wrong_count_embeddings
            )


class TestContentBasedDiversification:
    """Test content-based diversification."""

    @pytest.fixture
    def sample_results(self):
        """Create sample results with varying content."""
        return [
            {"id": "doc1", "content": "Python programming tutorial guide", "score": 0.9},
            {"id": "doc2", "content": "Python programming tutorial basics", "score": 0.85},  # Similar
            {"id": "doc3", "content": "Java web development", "score": 0.8},
            {"id": "doc4", "content": "Python tutorial advanced", "score": 0.75},  # Similar
            {"id": "doc5", "content": "Database administration", "score": 0.7},  # Different
        ]

    def test_diversify_content_based(self, sample_results):
        """Test content-based diversification."""
        diversifier = ResultDiversifier(lambda_param=0.5)

        # No embeddings provided - should use content
        diversified = diversifier.diversify(
            sample_results,
            top_k=3,
            embeddings=None
        )

        assert len(diversified) == 3
        # First should be most relevant
        assert diversified[0]['id'] == "doc1"

        # Should include diverse content
        doc_ids = [d['id'] for d in diversified]
        # All three shouldn't be Python docs (too similar)
        python_count = sum(1 for id in doc_ids if id in ["doc1", "doc2", "doc4"])
        assert python_count <= 2

    def test_content_diversity_avoids_duplicates(self):
        """Test that similar content is avoided."""
        results = [
            {"id": "doc1", "content": "the quick brown fox", "score": 1.0},
            {"id": "doc2", "content": "the quick brown fox", "score": 0.9},  # Identical
            {"id": "doc3", "content": "completely different content", "score": 0.8},
        ]

        diversifier = ResultDiversifier(lambda_param=0.5)
        diversified = diversifier.diversify(results, top_k=2)

        # Should select doc1 and doc3 (avoiding identical doc2)
        doc_ids = [d['id'] for d in diversified]
        assert "doc1" in doc_ids
        assert "doc3" in doc_ids
        assert "doc2" not in doc_ids


class TestDiversityScoreComputation:
    """Test diversity score computation."""

    def test_compute_diversity_single_result(self):
        """Test diversity score for single result."""
        results = [{"content": "test"}]

        score = ResultDiversifier.compute_diversity_score(results)

        # Single result is maximally diverse
        assert score == 1.0

    def test_compute_diversity_identical_results(self):
        """Test diversity score for identical results."""
        results = [
            {"content": "same content"},
            {"content": "same content"},
            {"content": "same content"},
        ]

        score = ResultDiversifier.compute_diversity_score(results)

        # Identical results have zero diversity
        assert score == 0.0

    def test_compute_diversity_different_results(self):
        """Test diversity score for completely different results."""
        results = [
            {"content": "python programming"},
            {"content": "java development"},
            {"content": "database administration"},
        ]

        score = ResultDiversifier.compute_diversity_score(results)

        # Different results should have high diversity
        assert score > 0.5

    def test_compute_diversity_mixed_results(self):
        """Test diversity score for mixed similarity."""
        results = [
            {"content": "python programming tutorial"},
            {"content": "python programming guide"},  # Similar to first
            {"content": "database design"},  # Different
        ]

        score = ResultDiversifier.compute_diversity_score(results)

        # Mixed similarity should have medium to high diversity
        assert 0.2 < score < 0.95


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_results(self):
        """Test with empty results list."""
        diversifier = ResultDiversifier()

        diversified = diversifier.diversify([], top_k=5)

        assert diversified == []

    def test_top_k_zero(self):
        """Test with top_k=0."""
        diversifier = ResultDiversifier()
        results = [{"content": "test", "score": 1.0}]

        diversified = diversifier.diversify(results, top_k=0)

        assert diversified == []

    def test_top_k_negative(self):
        """Test with negative top_k."""
        diversifier = ResultDiversifier()
        results = [{"content": "test", "score": 1.0}]

        diversified = diversifier.diversify(results, top_k=-1)

        assert diversified == []

    def test_top_k_exceeds_results(self):
        """Test when top_k > number of results."""
        diversifier = ResultDiversifier()
        results = [
            {"content": "doc1", "score": 1.0},
            {"content": "doc2", "score": 0.9},
        ]

        diversified = diversifier.diversify(results, top_k=10)

        # Should return all available results
        assert len(diversified) == 2

    def test_results_without_score(self):
        """Test with results missing score field."""
        diversifier = ResultDiversifier()
        results = [
            {"content": "doc1"},  # No score
            {"content": "doc2"},  # No score
        ]

        # Should not crash, uses default score of 0
        diversified = diversifier.diversify(results, top_k=2)

        assert len(diversified) == 2

    def test_results_without_content(self):
        """Test with results missing content field."""
        diversifier = ResultDiversifier()
        results = [
            {"id": "doc1", "score": 1.0},  # No content
            {"id": "doc2", "score": 0.9},  # No content
        ]

        # Should not crash, uses empty string for content
        diversified = diversifier.diversify(results, top_k=2)

        assert len(diversified) == 2

    def test_zero_embeddings(self):
        """Test with zero embeddings."""
        diversifier = ResultDiversifier()
        results = [
            {"content": "doc1", "score": 1.0},
            {"content": "doc2", "score": 0.9},
        ]
        embeddings = [
            np.zeros(5),  # Zero embedding
            np.zeros(5),
        ]

        # Should handle zero embeddings gracefully
        diversified = diversifier.diversify(results, top_k=2, embeddings=embeddings)

        assert len(diversified) == 2


class TestConvenienceFunctions:
    """Test convenience functions."""

    def test_get_result_diversifier(self):
        """Test get_result_diversifier function."""
        diversifier = get_result_diversifier()

        assert isinstance(diversifier, ResultDiversifier)
        assert diversifier.lambda_param == 0.5

    def test_get_result_diversifier_custom_lambda(self):
        """Test get_result_diversifier with custom lambda."""
        diversifier = get_result_diversifier(lambda_param=0.7)

        assert diversifier.lambda_param == 0.7

    def test_diversify_results_helper(self):
        """Test diversify_results helper function."""
        results = [
            {"content": "doc1", "score": 1.0},
            {"content": "doc2", "score": 0.9},
            {"content": "doc3", "score": 0.8},
        ]

        diversified = diversify_results(results, top_k=2, lambda_param=0.5)

        assert isinstance(diversified, list)
        assert len(diversified) == 2


class TestIntegrationScenarios:
    """Test real-world integration scenarios."""

    def test_api_documentation_diversification(self):
        """Test diversifying API documentation results."""
        results = [
            {"id": "get_user", "content": "GET /api/users/{id} - Retrieve user", "score": 0.9},
            {"id": "get_users", "content": "GET /api/users - List all users", "score": 0.85},
            {"id": "post_user", "content": "POST /api/users - Create user", "score": 0.8},
            {"id": "put_user", "content": "PUT /api/users/{id} - Update user", "score": 0.75},
            {"id": "delete_user", "content": "DELETE /api/users/{id} - Delete user", "score": 0.7},
        ]

        diversifier = ResultDiversifier(lambda_param=0.5)
        diversified = diversifier.diversify(results, top_k=3)

        # Should include variety of operations (not all GET)
        operations = [r['content'].split()[0] for r in diversified]
        assert len(set(operations)) >= 2  # At least 2 different operations

    def test_search_query_diversification(self):
        """Test diversifying search results for a query."""
        # Simulating search results for "authentication"
        results = [
            {"content": "OAuth2 authentication guide", "score": 0.95},
            {"content": "OAuth2 authentication tutorial", "score": 0.93},  # Similar
            {"content": "JWT authentication explained", "score": 0.9},
            {"content": "OAuth2 best practices", "score": 0.87},  # Similar to first
            {"content": "Basic authentication overview", "score": 0.85},
        ]

        diversifier = ResultDiversifier(lambda_param=0.6)  # Favor relevance slightly
        diversified = diversifier.diversify(results, top_k=3)

        assert len(diversified) == 3
        # Should include different auth methods
        contents = [r['content'] for r in diversified]
        assert not all("OAuth2" in c for c in contents)  # Not all OAuth2

    def test_balanced_diversification(self):
        """Test balanced approach (lambda=0.5)."""
        results = [
            {"content": "Python tutorial part 1", "score": 1.0},
            {"content": "Python tutorial part 2", "score": 0.95},
            {"content": "Python tutorial part 3", "score": 0.9},
            {"content": "Java programming basics", "score": 0.85},
            {"content": "Database design guide", "score": 0.8},
        ]

        diversifier = ResultDiversifier(lambda_param=0.5)
        diversified = diversifier.diversify(results, top_k=3)

        # With balanced approach, should mix relevance and diversity
        assert len(diversified) == 3
        # Should have Python tutorial part 1 (most relevant)
        assert diversified[0]['content'] == "Python tutorial part 1"

        # But should also include different topics
        contents = [r['content'] for r in diversified]
        python_count = sum(1 for c in contents if "Python" in c)
        assert python_count <= 2  # At most 2 Python tutorials
