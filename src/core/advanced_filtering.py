"""
Advanced Filtering and Faceted Search Module

Provides advanced filtering capabilities and faceted search for the vector store.
Supports multiple filter types, complex combinations, and aggregations.

Features:
- Multiple filter types (equality, range, contains, regex, etc.)
- Complex filter combinations (AND, OR, NOT)
- Faceted search (count aggregations by field)
- Integration with ChromaDB metadata filters
- Type-safe filter building

Author: API Assistant Team
Date: 2025-12-27
"""

import re
import structlog
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Union

logger = structlog.get_logger(__name__)


class FilterOperator(Enum):
    """Filter operators."""

    # Comparison operators
    EQ = "eq"  # Equal
    NE = "ne"  # Not equal
    GT = "gt"  # Greater than
    GTE = "gte"  # Greater than or equal
    LT = "lt"  # Less than
    LTE = "lte"  # Less than or equal

    # String operators
    CONTAINS = "contains"  # String contains
    NOT_CONTAINS = "not_contains"  # String does not contain
    STARTS_WITH = "starts_with"  # String starts with
    ENDS_WITH = "ends_with"  # String ends with
    REGEX = "regex"  # Regular expression match

    # Collection operators
    IN = "in"  # Value in list
    NOT_IN = "not_in"  # Value not in list

    # Logical operators
    AND = "and"  # Logical AND
    OR = "or"  # Logical OR
    NOT = "not"  # Logical NOT


class Filter(ABC):
    """Base class for all filters."""

    @abstractmethod
    def to_chroma_where(self) -> Optional[Dict[str, Any]]:
        """Convert filter to ChromaDB where clause."""
        pass

    @abstractmethod
    def to_chroma_where_document(self) -> Optional[Dict[str, Any]]:
        """Convert filter to ChromaDB where_document clause."""
        pass

    @abstractmethod
    def matches(self, metadata: Dict[str, Any], content: str = "") -> bool:
        """Check if document matches filter (for client-side filtering)."""
        pass


class MetadataFilter(Filter):
    """Filter on metadata fields."""

    def __init__(
        self,
        field: str,
        operator: FilterOperator,
        value: Any,
    ):
        """
        Initialize metadata filter.

        Args:
            field: Metadata field name
            operator: Filter operator
            value: Value to compare against
        """
        self.field = field
        self.operator = operator
        self.value = value

    def to_chroma_where(self) -> Optional[Dict[str, Any]]:
        """Convert to ChromaDB where clause.

        Note: ChromaDB only supports: $eq, $ne, $gt, $gte, $lt, $lte, $in, $nin
        Operators not supported by ChromaDB will return None and use client-side filtering.
        """
        # Map operators to ChromaDB syntax (only supported operators)
        operator_map = {
            FilterOperator.EQ: "$eq",
            FilterOperator.NE: "$ne",
            FilterOperator.GT: "$gt",
            FilterOperator.GTE: "$gte",
            FilterOperator.LT: "$lt",
            FilterOperator.LTE: "$lte",
            FilterOperator.IN: "$in",
            FilterOperator.NOT_IN: "$nin",
            # Note: CONTAINS, NOT_CONTAINS, STARTS_WITH, ENDS_WITH, REGEX
            # are NOT supported by ChromaDB and will use client-side filtering
        }

        if self.operator in operator_map:
            return {self.field: {operator_map[self.operator]: self.value}}

        # For operators not supported by ChromaDB, return None
        # (will fall back to client-side filtering)
        logger.debug(
            "filter_operator_not_supported_by_chromadb",
            operator=self.operator.value,
            field=self.field,
            using_client_side_filtering=True,
        )
        return None

    def to_chroma_where_document(self) -> Optional[Dict[str, Any]]:
        """Metadata filters don't use where_document."""
        return None

    def matches(self, metadata: Dict[str, Any], content: str = "") -> bool:
        """Check if document matches filter."""
        if self.field not in metadata:
            return False

        field_value = metadata[self.field]

        if self.operator == FilterOperator.EQ:
            return field_value == self.value
        elif self.operator == FilterOperator.NE:
            return field_value != self.value
        elif self.operator == FilterOperator.GT:
            return field_value > self.value
        elif self.operator == FilterOperator.GTE:
            return field_value >= self.value
        elif self.operator == FilterOperator.LT:
            return field_value < self.value
        elif self.operator == FilterOperator.LTE:
            return field_value <= self.value
        elif self.operator == FilterOperator.IN:
            return field_value in self.value
        elif self.operator == FilterOperator.NOT_IN:
            return field_value not in self.value
        elif self.operator == FilterOperator.CONTAINS:
            return self.value in str(field_value)
        elif self.operator == FilterOperator.NOT_CONTAINS:
            return self.value not in str(field_value)
        elif self.operator == FilterOperator.STARTS_WITH:
            return str(field_value).startswith(self.value)
        elif self.operator == FilterOperator.ENDS_WITH:
            return str(field_value).endswith(self.value)
        elif self.operator == FilterOperator.REGEX:
            try:
                return bool(re.search(self.value, str(field_value)))
            except re.error:
                # Invalid regex pattern, return False
                logger.warning("Invalid regex pattern", pattern=self.value)
                return False

        return False


class ContentFilter(Filter):
    """Filter on document content."""

    def __init__(
        self,
        operator: FilterOperator,
        value: Any,
    ):
        """
        Initialize content filter.

        Args:
            operator: Filter operator
            value: Value to compare against
        """
        self.operator = operator
        self.value = value

    def to_chroma_where(self) -> Optional[Dict[str, Any]]:
        """Content filters don't use where."""
        return None

    def to_chroma_where_document(self) -> Optional[Dict[str, Any]]:
        """Convert to ChromaDB where_document clause."""
        operator_map = {
            FilterOperator.CONTAINS: "$contains",
            FilterOperator.NOT_CONTAINS: "$not_contains",
        }

        if self.operator in operator_map:
            return {operator_map[self.operator]: self.value}

        return None

    def matches(self, metadata: Dict[str, Any], content: str = "") -> bool:
        """Check if document matches filter."""
        if self.operator == FilterOperator.CONTAINS:
            return self.value in content
        elif self.operator == FilterOperator.NOT_CONTAINS:
            return self.value not in content
        elif self.operator == FilterOperator.STARTS_WITH:
            return content.startswith(self.value)
        elif self.operator == FilterOperator.ENDS_WITH:
            return content.endswith(self.value)
        elif self.operator == FilterOperator.REGEX:
            try:
                return bool(re.search(self.value, content))
            except re.error:
                # Invalid regex pattern, return False
                logger.warning("Invalid regex pattern", pattern=self.value)
                return False

        return False


class CombinedFilter(Filter):
    """Combine multiple filters with logical operators."""

    def __init__(
        self,
        operator: FilterOperator,
        filters: List[Filter],
    ):
        """
        Initialize combined filter.

        Args:
            operator: Logical operator (AND, OR, NOT)
            filters: List of filters to combine
        """
        if operator not in [FilterOperator.AND, FilterOperator.OR, FilterOperator.NOT]:
            raise ValueError(f"Invalid logical operator: {operator}")

        if operator == FilterOperator.NOT and len(filters) != 1:
            raise ValueError("NOT operator requires exactly one filter")

        if operator in [FilterOperator.AND, FilterOperator.OR] and len(filters) < 2:
            raise ValueError(f"{operator.value.upper()} operator requires at least 2 filters")

        self.operator = operator
        self.filters = filters

    def to_chroma_where(self) -> Optional[Dict[str, Any]]:
        """Convert to ChromaDB where clause."""
        where_clauses = []
        for f in self.filters:
            where = f.to_chroma_where()
            if where:
                where_clauses.append(where)

        if not where_clauses:
            return None

        # Special handling for NOT
        # ChromaDB doesn't support top-level $not, so we try to convert to $ne if possible
        if self.operator == FilterOperator.NOT:
            # Check if it's a simple equality that can be converted to $ne
            if len(where_clauses) == 1 and len(self.filters) == 1:
                filter = self.filters[0]
                if isinstance(filter, MetadataFilter) and filter.operator == FilterOperator.EQ:
                    # Convert NOT (field = value) to (field != value)
                    return {filter.field: {"$ne": filter.value}}

            # For complex NOT filters, return None to trigger client-side filtering
            return None

        if len(where_clauses) == 1:
            return where_clauses[0]

        # Combine clauses
        if self.operator == FilterOperator.AND:
            return {"$and": where_clauses}
        elif self.operator == FilterOperator.OR:
            return {"$or": where_clauses}

        return None

    def to_chroma_where_document(self) -> Optional[Dict[str, Any]]:
        """Convert to ChromaDB where_document clause."""
        doc_clauses = []
        for f in self.filters:
            doc = f.to_chroma_where_document()
            if doc:
                doc_clauses.append(doc)

        if not doc_clauses:
            return None

        if len(doc_clauses) == 1:
            return doc_clauses[0]

        # Combine clauses
        if self.operator == FilterOperator.AND:
            return {"$and": doc_clauses}
        elif self.operator == FilterOperator.OR:
            return {"$or": doc_clauses}
        elif self.operator == FilterOperator.NOT:
            return {"$not": doc_clauses[0]}

        return None

    def matches(self, metadata: Dict[str, Any], content: str = "") -> bool:
        """Check if document matches filter."""
        if self.operator == FilterOperator.AND:
            return all(f.matches(metadata, content) for f in self.filters)
        elif self.operator == FilterOperator.OR:
            return any(f.matches(metadata, content) for f in self.filters)
        elif self.operator == FilterOperator.NOT:
            return not self.filters[0].matches(metadata, content)

        return False


@dataclass
class FacetResult:
    """Result of faceted search aggregation."""

    field: str
    """Field that was faceted on."""

    values: Dict[Any, int] = field(default_factory=dict)
    """Map of field values to document counts."""

    total_docs: int = 0
    """Total number of documents."""

    def get_top_values(self, n: int = 10) -> List[tuple[Any, int]]:
        """
        Get top N values by count.

        Args:
            n: Number of top values to return

        Returns:
            List of (value, count) tuples sorted by count descending
        """
        sorted_values = sorted(
            self.values.items(),
            key=lambda x: x[1],
            reverse=True,
        )
        return sorted_values[:n]

    def get_percentage(self, value: Any) -> float:
        """
        Get percentage of documents with this value.

        Args:
            value: Field value

        Returns:
            Percentage (0-100)
        """
        if self.total_docs == 0:
            return 0.0
        count = self.values.get(value, 0)
        return (count / self.total_docs) * 100


class FilterBuilder:
    """Fluent builder for creating filters."""

    @staticmethod
    def metadata(
        field: str,
        operator: FilterOperator,
        value: Any,
    ) -> MetadataFilter:
        """Create metadata filter."""
        return MetadataFilter(field, operator, value)

    @staticmethod
    def content(
        operator: FilterOperator,
        value: Any,
    ) -> ContentFilter:
        """Create content filter."""
        return ContentFilter(operator, value)

    @staticmethod
    def eq(field: str, value: Any) -> MetadataFilter:
        """Field equals value."""
        return MetadataFilter(field, FilterOperator.EQ, value)

    @staticmethod
    def ne(field: str, value: Any) -> MetadataFilter:
        """Field not equals value."""
        return MetadataFilter(field, FilterOperator.NE, value)

    @staticmethod
    def gt(field: str, value: Any) -> MetadataFilter:
        """Field greater than value."""
        return MetadataFilter(field, FilterOperator.GT, value)

    @staticmethod
    def gte(field: str, value: Any) -> MetadataFilter:
        """Field greater than or equal to value."""
        return MetadataFilter(field, FilterOperator.GTE, value)

    @staticmethod
    def lt(field: str, value: Any) -> MetadataFilter:
        """Field less than value."""
        return MetadataFilter(field, FilterOperator.LT, value)

    @staticmethod
    def lte(field: str, value: Any) -> MetadataFilter:
        """Field less than or equal to value."""
        return MetadataFilter(field, FilterOperator.LTE, value)

    @staticmethod
    def contains(field: str, value: str) -> MetadataFilter:
        """Field contains value."""
        return MetadataFilter(field, FilterOperator.CONTAINS, value)

    @staticmethod
    def not_contains(field: str, value: str) -> MetadataFilter:
        """Field does not contain value."""
        return MetadataFilter(field, FilterOperator.NOT_CONTAINS, value)

    @staticmethod
    def in_list(field: str, values: List[Any]) -> MetadataFilter:
        """Field value in list."""
        return MetadataFilter(field, FilterOperator.IN, values)

    @staticmethod
    def not_in_list(field: str, values: List[Any]) -> MetadataFilter:
        """Field value not in list."""
        return MetadataFilter(field, FilterOperator.NOT_IN, values)

    @staticmethod
    def content_contains(value: str) -> ContentFilter:
        """Content contains value."""
        return ContentFilter(FilterOperator.CONTAINS, value)

    @staticmethod
    def content_not_contains(value: str) -> ContentFilter:
        """Content does not contain value."""
        return ContentFilter(FilterOperator.NOT_CONTAINS, value)

    @staticmethod
    def and_filters(*filters: Filter) -> CombinedFilter:
        """Combine filters with AND."""
        return CombinedFilter(FilterOperator.AND, list(filters))

    @staticmethod
    def or_filters(*filters: Filter) -> CombinedFilter:
        """Combine filters with OR."""
        return CombinedFilter(FilterOperator.OR, list(filters))

    @staticmethod
    def not_filter(filter: Filter) -> CombinedFilter:
        """Negate filter with NOT."""
        return CombinedFilter(FilterOperator.NOT, [filter])


class FacetedSearch:
    """Faceted search and aggregation."""

    @staticmethod
    def compute_facets(
        documents: List[Dict[str, Any]],
        facet_fields: List[str],
    ) -> Dict[str, FacetResult]:
        """
        Compute facets for a set of documents.

        Args:
            documents: List of documents with metadata
            facet_fields: Fields to compute facets for

        Returns:
            Map of field names to FacetResult
        """
        results = {}
        total_docs = len(documents)

        for field in facet_fields:
            facet = FacetResult(field=field, total_docs=total_docs)

            # Count values
            for doc in documents:
                metadata = doc.get("metadata", {})
                if field in metadata:
                    value = metadata[field]
                    facet.values[value] = facet.values.get(value, 0) + 1

            results[field] = facet

        logger.debug(
            "Computed facets",
            facet_fields=facet_fields,
            total_docs=total_docs,
        )

        return results

    @staticmethod
    def apply_client_side_filter(
        documents: List[Dict[str, Any]],
        filter: Filter,
    ) -> List[Dict[str, Any]]:
        """
        Apply filter to documents (client-side filtering).

        Useful when filter cannot be converted to ChromaDB syntax.

        Args:
            documents: Documents to filter
            filter: Filter to apply

        Returns:
            Filtered documents
        """
        filtered = []

        for doc in documents:
            metadata = doc.get("metadata", {})
            content = doc.get("content", "")

            if filter.matches(metadata, content):
                filtered.append(doc)

        logger.debug(
            "Applied client-side filter",
            original_count=len(documents),
            filtered_count=len(filtered),
        )

        return filtered


# Convenience functions
def create_filter(
    field: str,
    operator: FilterOperator,
    value: Any,
) -> MetadataFilter:
    """
    Create a metadata filter.

    Args:
        field: Metadata field name
        operator: Filter operator
        value: Value to compare against

    Returns:
        MetadataFilter instance
    """
    return MetadataFilter(field, operator, value)


def combine_filters(
    operator: FilterOperator,
    *filters: Filter,
) -> CombinedFilter:
    """
    Combine multiple filters.

    Args:
        operator: Logical operator (AND, OR, NOT)
        *filters: Filters to combine

    Returns:
        CombinedFilter instance
    """
    return CombinedFilter(operator, list(filters))


def compute_facets(
    documents: List[Dict[str, Any]],
    facet_fields: List[str],
) -> Dict[str, FacetResult]:
    """
    Compute facets for documents.

    Args:
        documents: Documents to facet
        facet_fields: Fields to compute facets for

    Returns:
        Map of field names to FacetResult
    """
    return FacetedSearch.compute_facets(documents, facet_fields)


__all__ = [
    "FilterOperator",
    "Filter",
    "MetadataFilter",
    "ContentFilter",
    "CombinedFilter",
    "FacetResult",
    "FilterBuilder",
    "FacetedSearch",
    "create_filter",
    "combine_filters",
    "compute_facets",
]
