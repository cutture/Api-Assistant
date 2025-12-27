"""
Pydantic models for API request and response schemas.

Provides type-safe models for:
- Document operations (add, update, delete)
- Search requests and responses
- Filter specifications
- Faceted search
- Error responses

Author: API Assistant Team
Date: 2025-12-27
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, validator


# Enums
class SearchMode(str, Enum):
    """Search mode selection."""

    VECTOR = "vector"
    HYBRID = "hybrid"
    RERANKED = "reranked"


class FilterOperatorEnum(str, Enum):
    """Filter operators for API."""

    EQ = "eq"
    NE = "ne"
    GT = "gt"
    GTE = "gte"
    LT = "lt"
    LTE = "lte"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"
    REGEX = "regex"
    IN = "in"
    NOT_IN = "not_in"
    AND = "and"
    OR = "or"
    NOT = "not"


# Base Models
class HealthResponse(BaseModel):
    """Health check response."""

    status: str = Field(..., description="Service status")
    version: str = Field(..., description="API version")
    features: Dict[str, bool] = Field(..., description="Available features")


class ErrorResponse(BaseModel):
    """Error response."""

    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    detail: Optional[Dict[str, Any]] = Field(None, description="Additional error details")


# Document Models
class DocumentMetadata(BaseModel):
    """Document metadata."""

    class Config:
        extra = "allow"  # Allow additional fields


class Document(BaseModel):
    """Document with content and metadata."""

    content: str = Field(..., description="Document content", min_length=1)
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Document metadata"
    )
    id: Optional[str] = Field(None, description="Document ID (auto-generated if not provided)")


class DocumentResponse(BaseModel):
    """Document response."""

    id: str = Field(..., description="Document ID")
    content: str = Field(..., description="Document content")
    metadata: Dict[str, Any] = Field(..., description="Document metadata")


class AddDocumentsRequest(BaseModel):
    """Request to add multiple documents."""

    documents: List[Document] = Field(..., description="Documents to add", min_items=1)


class AddDocumentsResponse(BaseModel):
    """Response after adding documents."""

    document_ids: List[str] = Field(..., description="IDs of added documents")
    count: int = Field(..., description="Number of documents added")


class DeleteDocumentResponse(BaseModel):
    """Response after deleting a document."""

    success: bool = Field(..., description="Whether deletion was successful")
    message: str = Field(..., description="Status message")


# Filter Models
class FilterSpec(BaseModel):
    """Filter specification for API."""

    field: Optional[str] = Field(None, description="Field to filter on (for metadata filters)")
    operator: FilterOperatorEnum = Field(..., description="Filter operator")
    value: Optional[Any] = Field(None, description="Value to compare against")
    filters: Optional[List["FilterSpec"]] = Field(
        None, description="Sub-filters (for AND/OR/NOT operators)"
    )

    @validator("filters")
    def validate_filters(cls, v, values):
        """Validate filters based on operator."""
        operator = values.get("operator")

        if operator in [FilterOperatorEnum.AND, FilterOperatorEnum.OR]:
            if not v or len(v) < 2:
                raise ValueError(f"{operator.value} operator requires at least 2 filters")
        elif operator == FilterOperatorEnum.NOT:
            if not v or len(v) != 1:
                raise ValueError("NOT operator requires exactly 1 filter")
        elif operator in [
            FilterOperatorEnum.EQ,
            FilterOperatorEnum.NE,
            FilterOperatorEnum.GT,
            FilterOperatorEnum.GTE,
            FilterOperatorEnum.LT,
            FilterOperatorEnum.LTE,
            FilterOperatorEnum.CONTAINS,
            FilterOperatorEnum.NOT_CONTAINS,
            FilterOperatorEnum.STARTS_WITH,
            FilterOperatorEnum.ENDS_WITH,
            FilterOperatorEnum.REGEX,
            FilterOperatorEnum.IN,
            FilterOperatorEnum.NOT_IN,
        ]:
            if v is not None:
                raise ValueError(f"{operator.value} operator should not have sub-filters")

        return v


# Circular reference fix
FilterSpec.model_rebuild()


# Search Models
class SearchRequest(BaseModel):
    """Search request."""

    query: str = Field(..., description="Search query", min_length=1)
    n_results: int = Field(5, description="Number of results to return", ge=1, le=100)
    mode: SearchMode = Field(SearchMode.HYBRID, description="Search mode")
    filter: Optional[FilterSpec] = Field(None, description="Filter specification")
    use_query_expansion: bool = Field(False, description="Use query expansion")
    use_diversification: bool = Field(False, description="Use result diversification")
    diversification_lambda: float = Field(
        0.5, description="Diversification lambda (0=diversity, 1=relevance)", ge=0.0, le=1.0
    )


class SearchResult(BaseModel):
    """Single search result."""

    id: str = Field(..., description="Document ID")
    content: str = Field(..., description="Document content")
    metadata: Dict[str, Any] = Field(..., description="Document metadata")
    score: float = Field(..., description="Relevance score")
    method: Optional[str] = Field(None, description="Search method used")


class SearchResponse(BaseModel):
    """Search response."""

    results: List[SearchResult] = Field(..., description="Search results")
    total: int = Field(..., description="Total number of results")
    query: str = Field(..., description="Original query")
    expanded_query: Optional[str] = Field(None, description="Expanded query (if used)")
    mode: SearchMode = Field(..., description="Search mode used")


# Faceted Search Models
class FacetValue(BaseModel):
    """Facet value with count."""

    value: Any = Field(..., description="Field value")
    count: int = Field(..., description="Number of documents")
    percentage: float = Field(..., description="Percentage of total documents")


class FacetResult(BaseModel):
    """Facet result for a field."""

    field: str = Field(..., description="Field name")
    values: List[FacetValue] = Field(..., description="Top values and counts")
    total_docs: int = Field(..., description="Total documents")


class FacetedSearchRequest(BaseModel):
    """Faceted search request."""

    query: str = Field(..., description="Search query", min_length=1)
    facet_fields: List[str] = Field(..., description="Fields to facet on", min_items=1)
    n_results: int = Field(20, description="Number of results to return", ge=1, le=100)
    filter: Optional[FilterSpec] = Field(None, description="Filter specification")
    top_facet_values: int = Field(10, description="Number of top facet values to return", ge=1, le=50)


class FacetedSearchResponse(BaseModel):
    """Faceted search response."""

    results: List[SearchResult] = Field(..., description="Search results")
    facets: Dict[str, FacetResult] = Field(..., description="Facet results by field")
    total: int = Field(..., description="Total number of results")
    query: str = Field(..., description="Original query")


# Stats Models
class CollectionStats(BaseModel):
    """Collection statistics."""

    total_documents: int = Field(..., description="Total number of documents")
    collection_name: str = Field(..., description="Collection name")


class StatsResponse(BaseModel):
    """Statistics response."""

    collection: CollectionStats = Field(..., description="Collection statistics")
    features: Dict[str, bool] = Field(..., description="Enabled features")


# Batch Operations
class BulkDeleteRequest(BaseModel):
    """Request to delete multiple documents."""

    document_ids: List[str] = Field(..., description="Document IDs to delete", min_items=1)


class BulkDeleteResponse(BaseModel):
    """Response after bulk delete."""

    deleted_count: int = Field(..., description="Number of documents deleted")
    not_found_count: int = Field(..., description="Number of documents not found")
    document_ids: List[str] = Field(..., description="IDs of deleted documents")
