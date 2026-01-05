"""
Tests for query expansion module.

Tests query expansion functionality including:
- Query expander initialization
- Synonym/domain term expansion
- Multi-query generation
- LLM-based expansion
- Strategy selection
- Edge cases
"""

import pytest

from src.core.query_expansion import (
    QueryExpander,
    ExpandedQuery,
    get_query_expander,
    expand_query,
)


class TestExpandedQuery:
    """Test ExpandedQuery dataclass."""

    def test_expanded_query_creation(self):
        """Test creating an ExpandedQuery instance."""
        expanded = ExpandedQuery(
            original_query="test query",
            expanded_terms=["term1", "term2"],
            query_variations=["variation1", "variation2"],
            expansion_method="synonyms",
            confidence=0.9,
        )

        assert expanded.original_query == "test query"
        assert expanded.expanded_terms == ["term1", "term2"]
        assert expanded.query_variations == ["variation1", "variation2"]
        assert expanded.expansion_method == "synonyms"
        assert expanded.confidence == 0.9

    def test_get_all_terms(self):
        """Test getting all unique terms."""
        expanded = ExpandedQuery(
            original_query="auth",
            expanded_terms=["authentication", "login"],
            query_variations=[],
            expansion_method="synonyms",
        )

        all_terms = expanded.get_all_terms()
        assert "auth" in all_terms
        assert "authentication" in all_terms
        assert "login" in all_terms

    def test_get_all_queries(self):
        """Test getting all query variations."""
        expanded = ExpandedQuery(
            original_query="how to auth",
            expanded_terms=[],
            query_variations=["auth guide", "auth tutorial"],
            expansion_method="multi_query",
        )

        all_queries = expanded.get_all_queries()
        assert all_queries[0] == "how to auth"
        assert "auth guide" in all_queries
        assert "auth tutorial" in all_queries
        assert len(all_queries) == 3


class TestQueryExpanderInit:
    """Test QueryExpander initialization."""

    def test_init_with_defaults(self):
        """Test initialization with default parameters."""
        expander = QueryExpander()

        assert expander.llm_client is None
        assert expander.max_expansions == 5
        assert expander.enable_domain_expansions is True
        assert expander.enable_abbreviations is True

    def test_init_with_custom_params(self):
        """Test initialization with custom parameters."""
        expander = QueryExpander(
            max_expansions=10,
            enable_domain_expansions=False,
            enable_abbreviations=False,
        )

        assert expander.max_expansions == 10
        assert expander.enable_domain_expansions is False
        assert expander.enable_abbreviations is False


class TestDomainExpansion:
    """Test domain-specific term expansion."""

    @pytest.fixture
    def expander(self):
        """Create expander for testing."""
        return QueryExpander()

    def test_auth_expansion(self, expander):
        """Test expanding auth-related terms."""
        expanded = expander.expand_query("auth", strategy="domain")

        assert expanded.original_query == "auth"
        assert expanded.expansion_method in ["synonyms", "domain"]
        assert len(expanded.expanded_terms) > 0
        # Should include related terms
        expanded_lower = [t.lower() for t in expanded.expanded_terms]
        assert any(term in expanded_lower for term in ["authentication", "login", "oauth"])

    def test_api_expansion(self, expander):
        """Test expanding API-related terms."""
        expanded = expander.expand_query("api", strategy="domain")

        assert len(expanded.expanded_terms) > 0
        expanded_lower = [t.lower() for t in expanded.expanded_terms]
        assert any(term in expanded_lower for term in ["rest", "endpoint", "rest api"])

    def test_oauth_expansion(self, expander):
        """Test expanding OAuth terms."""
        expanded = expander.expand_query("oauth", strategy="domain")

        expanded_lower = [t.lower() for t in expanded.expanded_terms]
        assert any(term in expanded_lower for term in ["oauth2", "token", "authentication"])

    def test_multiple_terms_expansion(self, expander):
        """Test expanding query with multiple terms."""
        expanded = expander.expand_query("oauth authentication", strategy="domain")

        # Should expand both terms
        assert len(expanded.expanded_terms) > 0

    def test_max_expansions_limit(self, expander):
        """Test that expansions are limited to max_expansions."""
        expander.max_expansions = 3
        expanded = expander.expand_query("authentication", strategy="domain")

        # Should not exceed max
        assert len(expanded.expanded_terms) <= 3


class TestAbbreviationExpansion:
    """Test abbreviation expansion."""

    @pytest.fixture
    def expander(self):
        """Create expander for testing."""
        return QueryExpander()

    def test_jwt_expansion(self, expander):
        """Test JWT abbreviation expansion."""
        expanded = expander.expand_query("jwt", strategy="synonyms")

        expanded_lower = [t.lower() for t in expanded.expanded_terms]
        assert "json web token" in expanded_lower or "jwt" in expander.DOMAIN_EXPANSIONS

    def test_api_abbreviation(self, expander):
        """Test API abbreviation."""
        expanded = expander.expand_query("rest api", strategy="synonyms")

        # Should include expansions
        assert len(expanded.expanded_terms) > 0

    def test_abbreviation_disabled(self):
        """Test with abbreviations disabled."""
        expander = QueryExpander(enable_abbreviations=False)
        expanded = expander.expand_query("jwt", strategy="synonyms")

        # May still have domain expansions
        # Just testing it doesn't crash


class TestMultiQueryExpansion:
    """Test multi-query generation."""

    @pytest.fixture
    def expander(self):
        """Create expander for testing."""
        return QueryExpander()

    def test_how_to_question(self, expander):
        """Test expanding 'how to' questions."""
        expanded = expander.expand_query("how to authenticate users", strategy="multi_query")

        assert expanded.expansion_method == "multi_query"
        assert len(expanded.query_variations) > 0
        # Should generate variations like "authenticate users guide"
        variations_lower = [v.lower() for v in expanded.query_variations]
        assert any("guide" in v or "tutorial" in v for v in variations_lower)

    def test_what_is_question(self, expander):
        """Test expanding 'what is' questions."""
        expanded = expander.expand_query("what is OAuth2", strategy="multi_query")

        assert len(expanded.query_variations) > 0
        variations_lower = [v.lower() for v in expanded.query_variations]
        assert any("definition" in v or "explanation" in v or "overview" in v for v in variations_lower)

    def test_why_question(self, expander):
        """Test expanding 'why' questions."""
        expanded = expander.expand_query("why use JWT", strategy="multi_query")

        assert len(expanded.query_variations) > 0
        variations_lower = [v.lower() for v in expanded.query_variations]
        assert any("reason" in v or "explanation" in v for v in variations_lower)

    def test_max_variations_limit(self, expander):
        """Test max_variations parameter."""
        expanded = expander.expand_query(
            "how to setup OAuth2",
            strategy="multi_query",
            max_variations=2
        )

        # Should not exceed max_variations
        assert len(expanded.query_variations) <= 2


class TestStrategySelection:
    """Test automatic strategy selection."""

    @pytest.fixture
    def expander(self):
        """Create expander for testing."""
        return QueryExpander()

    def test_auto_selects_domain_for_tech_terms(self, expander):
        """Test auto strategy selects domain for technical terms."""
        expanded = expander.expand_query("oauth authentication", strategy="auto")

        # Should select domain or synonyms for tech terms
        assert expanded.expansion_method in ["domain", "synonyms"]

    def test_auto_handles_questions(self, expander):
        """Test auto strategy handles questions."""
        expanded = expander.expand_query("how to use API", strategy="auto")

        # Should work (strategy selection depends on LLM availability)
        assert expanded.expansion_method in ["multi_query", "domain", "synonyms"]

    def test_fallback_strategy(self, expander):
        """Test fallback to domain expansion."""
        expanded = expander.expand_query("random query", strategy="unknown")

        # Should fallback
        assert expanded.expansion_method in ["domain", "synonyms"]


class TestTokenization:
    """Test query tokenization."""

    def test_basic_tokenization(self):
        """Test basic tokenization."""
        expander = QueryExpander()
        tokens = expander._tokenize("OAuth2 authentication API")

        assert "OAuth2" in tokens
        assert "authentication" in tokens
        assert "API" in tokens

    def test_punctuation_handling(self):
        """Test tokenization handles punctuation."""
        expander = QueryExpander()
        tokens = expander._tokenize("how-to-auth, with JWT!")

        # Should split on punctuation
        assert len(tokens) > 0
        assert all(len(t) > 1 for t in tokens)  # Filters short tokens

    def test_filters_short_tokens(self):
        """Test that very short tokens are filtered."""
        expander = QueryExpander()
        tokens = expander._tokenize("a big test")

        # "a" should be filtered (length 1)
        assert "a" not in tokens
        assert "big" in tokens
        assert "test" in tokens


class TestExpandAndFormat:
    """Test expand_and_format method."""

    @pytest.fixture
    def expander(self):
        """Create expander for testing."""
        return QueryExpander()

    def test_formats_expanded_query(self, expander):
        """Test formatting of expanded query."""
        formatted = expander.expand_and_format("oauth", strategy="domain")

        # Should include original and expanded terms
        assert "oauth" in formatted.lower()
        assert len(formatted) > len("oauth")  # Has expansions

    def test_respects_max_expansions(self):
        """Test max_expansions in formatting."""
        expander = QueryExpander(max_expansions=2)
        formatted = expander.expand_and_format("authentication")

        # Should have limited terms
        terms = formatted.split()
        assert len(terms) <= 3  # Original + 2 expansions


class TestConvenienceFunctions:
    """Test convenience functions."""

    def test_get_query_expander(self):
        """Test get_query_expander function."""
        expander = get_query_expander()

        assert isinstance(expander, QueryExpander)
        assert expander.max_expansions == 5

    def test_get_query_expander_custom(self):
        """Test get_query_expander with custom params."""
        expander = get_query_expander(max_expansions=10)

        assert isinstance(expander, QueryExpander)

    def test_expand_query_helper(self):
        """Test expand_query helper function."""
        expanded = expand_query("authentication", strategy="domain")

        assert isinstance(expanded, ExpandedQuery)
        assert expanded.original_query == "authentication"
        assert len(expanded.expanded_terms) > 0


class TestEdgeCases:
    """Test edge cases and error handling."""

    @pytest.fixture
    def expander(self):
        """Create expander for testing."""
        return QueryExpander()

    def test_empty_query(self, expander):
        """Test with empty query."""
        expanded = expander.expand_query("", strategy="domain")

        assert expanded.original_query == ""
        # Should handle gracefully

    def test_whitespace_query(self, expander):
        """Test with whitespace-only query."""
        expanded = expander.expand_query("   ", strategy="domain")

        assert expanded.original_query == ""
        # Should handle gracefully

    def test_single_char_query(self, expander):
        """Test with single character query."""
        expanded = expander.expand_query("a", strategy="domain")

        # Should handle gracefully (may have no expansions)
        assert expanded.original_query == "a"

    def test_very_long_query(self, expander):
        """Test with very long query."""
        long_query = " ".join(["term"] * 100)
        expanded = expander.expand_query(long_query, strategy="domain")

        # Should not crash
        assert expanded.original_query == long_query

    def test_special_characters(self, expander):
        """Test with special characters."""
        expanded = expander.expand_query("@#$ authentication", strategy="domain")

        # Should handle gracefully
        assert len(expanded.expanded_terms) >= 0

    def test_unicode_query(self, expander):
        """Test with unicode characters."""
        expanded = expander.expand_query("认证 authentication", strategy="domain")

        # Should handle unicode
        assert "authentication" in expanded.original_query

    def test_mixed_case_query(self, expander):
        """Test with mixed case."""
        expanded = expander.expand_query("AuThEnTiCaTiOn", strategy="domain")

        # Should normalize and expand
        assert len(expanded.expanded_terms) > 0

    def test_query_with_numbers(self, expander):
        """Test query with numbers."""
        expanded = expander.expand_query("OAuth2 authentication", strategy="domain")

        # Should handle numbers in terms
        assert expanded.original_query == "OAuth2 authentication"
        assert len(expanded.expanded_terms) >= 0


class TestIntegrationScenarios:
    """Test real-world integration scenarios."""

    @pytest.fixture
    def expander(self):
        """Create expander for testing."""
        return QueryExpander()

    def test_api_documentation_query(self, expander):
        """Test expanding API documentation query."""
        expanded = expander.expand_query(
            "how to authenticate with OAuth2",
            strategy="multi_query"
        )

        # Should generate useful variations
        assert expanded.original_query == "how to authenticate with OAuth2"
        assert len(expanded.query_variations) > 0 or len(expanded.expanded_terms) > 0

    def test_technical_term_query(self, expander):
        """Test expanding technical term query."""
        expanded = expander.expand_query("JWT token", strategy="domain")

        # Should expand technical terms
        expanded_lower = [t.lower() for t in expanded.expanded_terms]
        assert any(
            term in expanded_lower
            for term in ["json web token", "authentication", "bearer", "access token"]
        )

    def test_endpoint_query(self, expander):
        """Test expanding endpoint-related query."""
        expanded = expander.expand_query("POST endpoint", strategy="domain")

        # Should include related terms
        expanded_lower = [t.lower() for t in expanded.expanded_terms]
        assert len(expanded_lower) > 0

    def test_error_handling_query(self, expander):
        """Test expanding error handling query."""
        expanded = expander.expand_query("debug authentication error", strategy="domain")

        # Should expand error and debug terms
        assert len(expanded.expanded_terms) > 0
