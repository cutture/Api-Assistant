"""
Tests for advanced filtering and faceted search module.

Tests filtering functionality including:
- Filter operators and types
- Metadata filtering
- Content filtering
- Combined filters (AND, OR, NOT)
- Filter builder
- Faceted search
- ChromaDB integration
- Edge cases
"""

import pytest

from src.core.advanced_filtering import (
    FilterOperator,
    Filter,
    MetadataFilter,
    ContentFilter,
    CombinedFilter,
    FacetResult,
    FilterBuilder,
    FacetedSearch,
    create_filter,
    combine_filters,
    compute_facets,
)


class TestFilterOperator:
    """Test FilterOperator enum."""

    def test_comparison_operators(self):
        """Test comparison operators exist."""
        assert FilterOperator.EQ.value == "eq"
        assert FilterOperator.NE.value == "ne"
        assert FilterOperator.GT.value == "gt"
        assert FilterOperator.GTE.value == "gte"
        assert FilterOperator.LT.value == "lt"
        assert FilterOperator.LTE.value == "lte"

    def test_string_operators(self):
        """Test string operators exist."""
        assert FilterOperator.CONTAINS.value == "contains"
        assert FilterOperator.NOT_CONTAINS.value == "not_contains"
        assert FilterOperator.STARTS_WITH.value == "starts_with"
        assert FilterOperator.ENDS_WITH.value == "ends_with"
        assert FilterOperator.REGEX.value == "regex"

    def test_collection_operators(self):
        """Test collection operators exist."""
        assert FilterOperator.IN.value == "in"
        assert FilterOperator.NOT_IN.value == "not_in"

    def test_logical_operators(self):
        """Test logical operators exist."""
        assert FilterOperator.AND.value == "and"
        assert FilterOperator.OR.value == "or"
        assert FilterOperator.NOT.value == "not"


class TestMetadataFilter:
    """Test MetadataFilter class."""

    def test_equality_filter(self):
        """Test equality filter."""
        f = MetadataFilter("status", FilterOperator.EQ, "active")

        assert f.field == "status"
        assert f.operator == FilterOperator.EQ
        assert f.value == "active"

    def test_to_chroma_where_eq(self):
        """Test converting EQ to ChromaDB where clause."""
        f = MetadataFilter("status", FilterOperator.EQ, "active")
        where = f.to_chroma_where()

        assert where == {"status": {"$eq": "active"}}

    def test_to_chroma_where_range(self):
        """Test converting range operators."""
        # Greater than
        f_gt = MetadataFilter("score", FilterOperator.GT, 0.5)
        assert f_gt.to_chroma_where() == {"score": {"$gt": 0.5}}

        # Less than or equal
        f_lte = MetadataFilter("priority", FilterOperator.LTE, 10)
        assert f_lte.to_chroma_where() == {"priority": {"$lte": 10}}

    def test_to_chroma_where_in(self):
        """Test converting IN operator."""
        f = MetadataFilter("category", FilterOperator.IN, ["api", "webhook"])
        where = f.to_chroma_where()

        assert where == {"category": {"$in": ["api", "webhook"]}}

    def test_matches_equality(self):
        """Test matches() for equality."""
        f = MetadataFilter("status", FilterOperator.EQ, "active")

        metadata = {"status": "active"}
        assert f.matches(metadata) is True

        metadata_wrong = {"status": "inactive"}
        assert f.matches(metadata_wrong) is False

    def test_matches_range(self):
        """Test matches() for range operators."""
        f_gt = MetadataFilter("score", FilterOperator.GT, 0.5)
        assert f_gt.matches({"score": 0.7}) is True
        assert f_gt.matches({"score": 0.3}) is False

        f_lte = MetadataFilter("count", FilterOperator.LTE, 100)
        assert f_lte.matches({"count": 50}) is True
        assert f_lte.matches({"count": 150}) is False

    def test_matches_in(self):
        """Test matches() for IN operator."""
        f = MetadataFilter("method", FilterOperator.IN, ["GET", "POST"])

        assert f.matches({"method": "GET"}) is True
        assert f.matches({"method": "POST"}) is True
        assert f.matches({"method": "DELETE"}) is False

    def test_matches_contains(self):
        """Test matches() for CONTAINS operator."""
        f = MetadataFilter("tags", FilterOperator.CONTAINS, "auth")

        assert f.matches({"tags": "authentication"}) is True
        assert f.matches({"tags": "database"}) is False

    def test_matches_missing_field(self):
        """Test matches() when field is missing."""
        f = MetadataFilter("nonexistent", FilterOperator.EQ, "value")

        assert f.matches({}) is False
        assert f.matches({"other": "value"}) is False


class TestContentFilter:
    """Test ContentFilter class."""

    def test_content_contains(self):
        """Test content contains filter."""
        f = ContentFilter(FilterOperator.CONTAINS, "authentication")

        assert f.operator == FilterOperator.CONTAINS
        assert f.value == "authentication"

    def test_to_chroma_where_document(self):
        """Test converting to ChromaDB where_document."""
        f = ContentFilter(FilterOperator.CONTAINS, "OAuth")
        where_doc = f.to_chroma_where_document()

        assert where_doc == {"$contains": "OAuth"}

    def test_to_chroma_where_returns_none(self):
        """Test that content filters don't use where clause."""
        f = ContentFilter(FilterOperator.CONTAINS, "test")
        assert f.to_chroma_where() is None

    def test_matches_contains(self):
        """Test matches() for contains."""
        f = ContentFilter(FilterOperator.CONTAINS, "authentication")

        content = "This document explains authentication methods"
        assert f.matches({}, content) is True

        content_no_match = "This is about databases"
        assert f.matches({}, content_no_match) is False

    def test_matches_not_contains(self):
        """Test matches() for not contains."""
        f = ContentFilter(FilterOperator.NOT_CONTAINS, "deprecated")

        assert f.matches({}, "This is a new API") is True
        assert f.matches({}, "This is deprecated") is False

    def test_matches_starts_with(self):
        """Test matches() for starts with."""
        f = ContentFilter(FilterOperator.STARTS_WITH, "GET")

        assert f.matches({}, "GET /api/users") is True
        assert f.matches({}, "POST /api/users") is False

    def test_matches_regex(self):
        """Test matches() for regex."""
        f = ContentFilter(FilterOperator.REGEX, r"v\d+\.\d+")

        assert f.matches({}, "Version v1.2 released") is True
        assert f.matches({}, "No version here") is False


class TestCombinedFilter:
    """Test CombinedFilter class."""

    def test_and_filter(self):
        """Test AND combination."""
        f1 = MetadataFilter("status", FilterOperator.EQ, "active")
        f2 = MetadataFilter("priority", FilterOperator.GT, 5)

        combined = CombinedFilter(FilterOperator.AND, [f1, f2])

        assert combined.operator == FilterOperator.AND
        assert len(combined.filters) == 2

    def test_or_filter(self):
        """Test OR combination."""
        f1 = MetadataFilter("method", FilterOperator.EQ, "GET")
        f2 = MetadataFilter("method", FilterOperator.EQ, "POST")

        combined = CombinedFilter(FilterOperator.OR, [f1, f2])

        assert combined.operator == FilterOperator.OR

    def test_not_filter(self):
        """Test NOT negation."""
        f = MetadataFilter("status", FilterOperator.EQ, "archived")
        combined = CombinedFilter(FilterOperator.NOT, [f])

        assert combined.operator == FilterOperator.NOT
        assert len(combined.filters) == 1

    def test_and_requires_multiple_filters(self):
        """Test that AND requires at least 2 filters."""
        f = MetadataFilter("status", FilterOperator.EQ, "active")

        with pytest.raises(ValueError):
            CombinedFilter(FilterOperator.AND, [f])

    def test_not_requires_single_filter(self):
        """Test that NOT requires exactly 1 filter."""
        f1 = MetadataFilter("status", FilterOperator.EQ, "active")
        f2 = MetadataFilter("priority", FilterOperator.GT, 5)

        with pytest.raises(ValueError):
            CombinedFilter(FilterOperator.NOT, [f1, f2])

    def test_invalid_operator(self):
        """Test invalid logical operator."""
        f = MetadataFilter("status", FilterOperator.EQ, "active")

        with pytest.raises(ValueError):
            CombinedFilter(FilterOperator.EQ, [f])  # EQ is not a logical operator

    def test_to_chroma_where_and(self):
        """Test converting AND to ChromaDB where."""
        f1 = MetadataFilter("status", FilterOperator.EQ, "active")
        f2 = MetadataFilter("priority", FilterOperator.GT, 5)

        combined = CombinedFilter(FilterOperator.AND, [f1, f2])
        where = combined.to_chroma_where()

        assert "$and" in where
        assert len(where["$and"]) == 2

    def test_to_chroma_where_or(self):
        """Test converting OR to ChromaDB where."""
        f1 = MetadataFilter("method", FilterOperator.EQ, "GET")
        f2 = MetadataFilter("method", FilterOperator.EQ, "POST")

        combined = CombinedFilter(FilterOperator.OR, [f1, f2])
        where = combined.to_chroma_where()

        assert "$or" in where

    def test_to_chroma_where_not(self):
        """Test converting NOT to ChromaDB where."""
        f = MetadataFilter("status", FilterOperator.EQ, "archived")
        combined = CombinedFilter(FilterOperator.NOT, [f])
        where = combined.to_chroma_where()

        # Simple NOT (field = value) is converted to (field != value) for ChromaDB compatibility
        assert where == {"status": {"$ne": "archived"}}

    def test_matches_and(self):
        """Test matches() for AND."""
        f1 = MetadataFilter("status", FilterOperator.EQ, "active")
        f2 = MetadataFilter("priority", FilterOperator.GT, 5)

        combined = CombinedFilter(FilterOperator.AND, [f1, f2])

        # Both conditions met
        assert combined.matches({"status": "active", "priority": 10}) is True

        # Only one condition met
        assert combined.matches({"status": "active", "priority": 3}) is False
        assert combined.matches({"status": "inactive", "priority": 10}) is False

    def test_matches_or(self):
        """Test matches() for OR."""
        f1 = MetadataFilter("method", FilterOperator.EQ, "GET")
        f2 = MetadataFilter("method", FilterOperator.EQ, "POST")

        combined = CombinedFilter(FilterOperator.OR, [f1, f2])

        assert combined.matches({"method": "GET"}) is True
        assert combined.matches({"method": "POST"}) is True
        assert combined.matches({"method": "DELETE"}) is False

    def test_matches_not(self):
        """Test matches() for NOT."""
        f = MetadataFilter("status", FilterOperator.EQ, "archived")
        combined = CombinedFilter(FilterOperator.NOT, [f])

        assert combined.matches({"status": "active"}) is True
        assert combined.matches({"status": "archived"}) is False


class TestFilterBuilder:
    """Test FilterBuilder helper class."""

    def test_eq_builder(self):
        """Test eq() builder."""
        f = FilterBuilder.eq("status", "active")

        assert isinstance(f, MetadataFilter)
        assert f.field == "status"
        assert f.operator == FilterOperator.EQ
        assert f.value == "active"

    def test_range_builders(self):
        """Test range filter builders."""
        f_gt = FilterBuilder.gt("score", 0.5)
        assert f_gt.operator == FilterOperator.GT

        f_gte = FilterBuilder.gte("score", 0.5)
        assert f_gte.operator == FilterOperator.GTE

        f_lt = FilterBuilder.lt("priority", 10)
        assert f_lt.operator == FilterOperator.LT

        f_lte = FilterBuilder.lte("priority", 10)
        assert f_lte.operator == FilterOperator.LTE

    def test_contains_builder(self):
        """Test contains() builder."""
        f = FilterBuilder.contains("tags", "auth")

        assert f.operator == FilterOperator.CONTAINS
        assert f.value == "auth"

    def test_in_list_builder(self):
        """Test in_list() builder."""
        f = FilterBuilder.in_list("method", ["GET", "POST"])

        assert f.operator == FilterOperator.IN
        assert f.value == ["GET", "POST"]

    def test_content_contains_builder(self):
        """Test content_contains() builder."""
        f = FilterBuilder.content_contains("authentication")

        assert isinstance(f, ContentFilter)
        assert f.operator == FilterOperator.CONTAINS

    def test_and_filters_builder(self):
        """Test and_filters() builder."""
        f1 = FilterBuilder.eq("status", "active")
        f2 = FilterBuilder.gt("priority", 5)

        combined = FilterBuilder.and_filters(f1, f2)

        assert isinstance(combined, CombinedFilter)
        assert combined.operator == FilterOperator.AND

    def test_or_filters_builder(self):
        """Test or_filters() builder."""
        f1 = FilterBuilder.eq("method", "GET")
        f2 = FilterBuilder.eq("method", "POST")

        combined = FilterBuilder.or_filters(f1, f2)

        assert combined.operator == FilterOperator.OR

    def test_not_filter_builder(self):
        """Test not_filter() builder."""
        f = FilterBuilder.eq("status", "archived")
        combined = FilterBuilder.not_filter(f)

        assert isinstance(combined, CombinedFilter)
        assert combined.operator == FilterOperator.NOT


class TestFacetResult:
    """Test FacetResult dataclass."""

    def test_facet_result_creation(self):
        """Test creating FacetResult."""
        facet = FacetResult(
            field="category",
            values={"api": 10, "webhook": 5, "auth": 3},
            total_docs=18,
        )

        assert facet.field == "category"
        assert facet.values["api"] == 10
        assert facet.total_docs == 18

    def test_get_top_values(self):
        """Test get_top_values()."""
        facet = FacetResult(
            field="category",
            values={"api": 10, "webhook": 5, "auth": 15, "database": 3},
            total_docs=33,
        )

        top_values = facet.get_top_values(2)

        assert len(top_values) == 2
        assert top_values[0] == ("auth", 15)  # Highest
        assert top_values[1] == ("api", 10)  # Second highest

    def test_get_top_values_default(self):
        """Test get_top_values() with default n."""
        values = {f"cat{i}": i for i in range(20)}
        facet = FacetResult(field="test", values=values, total_docs=190)

        top_values = facet.get_top_values()  # Default n=10

        assert len(top_values) == 10

    def test_get_percentage(self):
        """Test get_percentage()."""
        facet = FacetResult(
            field="category",
            values={"api": 25, "webhook": 50, "auth": 25},
            total_docs=100,
        )

        assert facet.get_percentage("api") == 25.0
        assert facet.get_percentage("webhook") == 50.0
        assert facet.get_percentage("auth") == 25.0

    def test_get_percentage_missing_value(self):
        """Test get_percentage() for missing value."""
        facet = FacetResult(field="category", values={"api": 10}, total_docs=10)

        assert facet.get_percentage("nonexistent") == 0.0

    def test_get_percentage_zero_docs(self):
        """Test get_percentage() with zero docs."""
        facet = FacetResult(field="category", values={}, total_docs=0)

        assert facet.get_percentage("any") == 0.0


class TestFacetedSearch:
    """Test FacetedSearch class."""

    @pytest.fixture
    def sample_documents(self):
        """Sample documents for testing."""
        return [
            {
                "id": "doc1",
                "content": "API documentation",
                "metadata": {"category": "api", "method": "GET", "priority": 1},
            },
            {
                "id": "doc2",
                "content": "Webhook guide",
                "metadata": {"category": "webhook", "method": "POST", "priority": 2},
            },
            {
                "id": "doc3",
                "content": "Auth tutorial",
                "metadata": {"category": "auth", "method": "POST", "priority": 1},
            },
            {
                "id": "doc4",
                "content": "API reference",
                "metadata": {"category": "api", "method": "GET", "priority": 3},
            },
        ]

    def test_compute_facets_single_field(self, sample_documents):
        """Test computing facets for single field."""
        facets = FacetedSearch.compute_facets(sample_documents, ["category"])

        assert "category" in facets
        assert facets["category"].values["api"] == 2
        assert facets["category"].values["webhook"] == 1
        assert facets["category"].values["auth"] == 1
        assert facets["category"].total_docs == 4

    def test_compute_facets_multiple_fields(self, sample_documents):
        """Test computing facets for multiple fields."""
        facets = FacetedSearch.compute_facets(
            sample_documents, ["category", "method"]
        )

        assert "category" in facets
        assert "method" in facets
        assert facets["method"].values["GET"] == 2
        assert facets["method"].values["POST"] == 2

    def test_compute_facets_empty_documents(self):
        """Test with empty documents list."""
        facets = FacetedSearch.compute_facets([], ["category"])

        assert "category" in facets
        assert facets["category"].total_docs == 0
        assert len(facets["category"].values) == 0

    def test_compute_facets_missing_field(self, sample_documents):
        """Test faceting on missing field."""
        facets = FacetedSearch.compute_facets(sample_documents, ["nonexistent"])

        assert "nonexistent" in facets
        # Should have no values since field doesn't exist
        assert len(facets["nonexistent"].values) == 0

    def test_apply_client_side_filter(self, sample_documents):
        """Test client-side filtering."""
        filter = MetadataFilter("category", FilterOperator.EQ, "api")

        filtered = FacetedSearch.apply_client_side_filter(sample_documents, filter)

        assert len(filtered) == 2
        assert all(d["metadata"]["category"] == "api" for d in filtered)

    def test_apply_client_side_filter_complex(self, sample_documents):
        """Test client-side filtering with complex filter."""
        f1 = MetadataFilter("method", FilterOperator.EQ, "POST")
        f2 = MetadataFilter("priority", FilterOperator.GT, 1)

        combined = CombinedFilter(FilterOperator.AND, [f1, f2])

        filtered = FacetedSearch.apply_client_side_filter(sample_documents, combined)

        assert len(filtered) == 1
        assert filtered[0]["id"] == "doc2"


class TestConvenienceFunctions:
    """Test convenience functions."""

    def test_create_filter(self):
        """Test create_filter() function."""
        f = create_filter("status", FilterOperator.EQ, "active")

        assert isinstance(f, MetadataFilter)
        assert f.field == "status"

    def test_combine_filters(self):
        """Test combine_filters() function."""
        f1 = MetadataFilter("status", FilterOperator.EQ, "active")
        f2 = MetadataFilter("priority", FilterOperator.GT, 5)

        combined = combine_filters(FilterOperator.AND, f1, f2)

        assert isinstance(combined, CombinedFilter)
        assert combined.operator == FilterOperator.AND

    def test_compute_facets(self):
        """Test compute_facets() function."""
        docs = [
            {"metadata": {"category": "api"}},
            {"metadata": {"category": "api"}},
            {"metadata": {"category": "auth"}},
        ]

        facets = compute_facets(docs, ["category"])

        assert "category" in facets
        assert facets["category"].values["api"] == 2


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_field_name(self):
        """Test filter with empty field name."""
        f = MetadataFilter("", FilterOperator.EQ, "value")

        # Should not crash
        assert f.matches({"": "value"}) is True

    def test_none_value_filter(self):
        """Test filter with None value."""
        f = MetadataFilter("field", FilterOperator.EQ, None)

        assert f.matches({"field": None}) is True
        assert f.matches({"field": "value"}) is False

    def test_unicode_in_filter(self):
        """Test Unicode characters in filter."""
        f = MetadataFilter("name", FilterOperator.EQ, "用户认证")

        assert f.matches({"name": "用户认证"}) is True

    def test_large_in_list(self):
        """Test IN filter with large list."""
        large_list = list(range(1000))
        f = MetadataFilter("id", FilterOperator.IN, large_list)

        assert f.matches({"id": 500}) is True
        assert f.matches({"id": 1500}) is False

    def test_regex_invalid(self):
        """Test invalid regex pattern."""
        f = ContentFilter(FilterOperator.REGEX, "[invalid")

        # Should handle invalid regex gracefully (return False)
        result = f.matches({}, "test content")
        assert result is False  # Invalid regex should return False, not crash

    def test_nested_combined_filters(self):
        """Test deeply nested combined filters."""
        f1 = MetadataFilter("a", FilterOperator.EQ, 1)
        f2 = MetadataFilter("b", FilterOperator.EQ, 2)
        f3 = MetadataFilter("c", FilterOperator.EQ, 3)

        # (a=1 AND b=2) OR c=3
        and_filter = CombinedFilter(FilterOperator.AND, [f1, f2])
        or_filter = CombinedFilter(FilterOperator.OR, [and_filter, f3])

        assert or_filter.matches({"a": 1, "b": 2, "c": 0}) is True
        assert or_filter.matches({"a": 0, "b": 0, "c": 3}) is True
        assert or_filter.matches({"a": 0, "b": 0, "c": 0}) is False


class TestIntegrationScenarios:
    """Test real-world integration scenarios."""

    def test_api_endpoint_filtering(self):
        """Test filtering API endpoints."""
        # Filter for GET endpoints in auth category
        method_filter = FilterBuilder.eq("method", "GET")
        category_filter = FilterBuilder.eq("category", "auth")

        combined = FilterBuilder.and_filters(method_filter, category_filter)

        metadata = {"method": "GET", "category": "auth"}
        assert combined.matches(metadata) is True

        metadata_wrong = {"method": "POST", "category": "auth"}
        assert combined.matches(metadata_wrong) is False

    def test_search_with_multiple_categories(self):
        """Test filtering by multiple categories."""
        # category IN ["api", "webhook", "auth"]
        category_filter = FilterBuilder.in_list("category", ["api", "webhook", "auth"])

        assert category_filter.matches({"category": "api"}) is True
        assert category_filter.matches({"category": "database"}) is False

    def test_priority_range_filtering(self):
        """Test filtering by priority range."""
        # priority >= 2 AND priority <= 5
        min_filter = FilterBuilder.gte("priority", 2)
        max_filter = FilterBuilder.lte("priority", 5)

        combined = FilterBuilder.and_filters(min_filter, max_filter)

        assert combined.matches({"priority": 3}) is True
        assert combined.matches({"priority": 1}) is False
        assert combined.matches({"priority": 6}) is False

    def test_exclude_deprecated_endpoints(self):
        """Test excluding deprecated endpoints."""
        # NOT (status = "deprecated")
        deprecated_filter = FilterBuilder.eq("status", "deprecated")
        not_deprecated = FilterBuilder.not_filter(deprecated_filter)

        assert not_deprecated.matches({"status": "active"}) is True
        assert not_deprecated.matches({"status": "deprecated"}) is False

    def test_complex_api_search_filter(self):
        """Test complex realistic filter."""
        # (method = "GET" OR method = "POST") AND category = "api" AND status != "deprecated"
        get_filter = FilterBuilder.eq("method", "GET")
        post_filter = FilterBuilder.eq("method", "POST")
        method_or = FilterBuilder.or_filters(get_filter, post_filter)

        category_filter = FilterBuilder.eq("category", "api")

        deprecated_filter = FilterBuilder.eq("status", "deprecated")
        not_deprecated = FilterBuilder.not_filter(deprecated_filter)

        final_filter = FilterBuilder.and_filters(
            method_or, category_filter, not_deprecated
        )

        # Should match
        assert final_filter.matches(
            {"method": "GET", "category": "api", "status": "active"}
        ) is True

        # Should not match (wrong category)
        assert final_filter.matches(
            {"method": "GET", "category": "webhook", "status": "active"}
        ) is False

        # Should not match (deprecated)
        assert final_filter.matches(
            {"method": "GET", "category": "api", "status": "deprecated"}
        ) is False

    def test_faceted_search_for_ui(self):
        """Test faceted search for building filter UI."""
        documents = [
            {"metadata": {"category": "api", "method": "GET", "version": "v1"}},
            {"metadata": {"category": "api", "method": "POST", "version": "v1"}},
            {"metadata": {"category": "webhook", "method": "POST", "version": "v2"}},
            {"metadata": {"category": "auth", "method": "GET", "version": "v1"}},
        ]

        facets = compute_facets(documents, ["category", "method", "version"])

        # Category facet
        assert facets["category"].values["api"] == 2
        top_categories = facets["category"].get_top_values(2)
        assert top_categories[0][0] == "api"

        # Method facet
        assert facets["method"].values["GET"] == 2
        assert facets["method"].values["POST"] == 2

        # Version facet
        assert facets["version"].values["v1"] == 3
        assert facets["version"].values["v2"] == 1
