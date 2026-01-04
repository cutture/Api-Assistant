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

from pydantic import BaseModel, ConfigDict, Field, field_validator, ValidationInfo


# Enums
class SearchMode(str, Enum):
    """Search mode selection."""

    VECTOR = "vector"
    HYBRID = "hybrid"
    RERANKED = "reranked"


class DocumentTypeEnum(str, Enum):
    """Supported document types for upload."""

    # API Specifications
    OPENAPI = "openapi"
    GRAPHQL = "graphql"
    POSTMAN = "postman"

    # General Documents
    PDF = "pdf"
    TEXT = "text"
    MARKDOWN = "markdown"
    JSON_GENERIC = "json_generic"
    CSV = "csv"
    DOCX = "docx"
    HTML = "html"


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

    model_config = ConfigDict(extra="allow")  # Allow additional fields


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

    documents: List[Document] = Field(..., description="Documents to add", min_length=1)


class AddDocumentsResponse(BaseModel):
    """Response after adding documents."""

    document_ids: List[str] = Field(..., description="IDs of all documents (new + skipped)")
    count: int = Field(..., description="Total number of documents processed")
    new_count: int = Field(..., description="Number of new documents added")
    skipped_count: int = Field(..., description="Number of duplicate documents skipped")


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

    @field_validator("filters")
    @classmethod
    def validate_filters(cls, v, info: ValidationInfo):
        """Validate filters based on operator."""
        operator = info.data.get("operator")

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
    n_results: int = Field(5, description="Number of results to return", ge=1, le=500)
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
    facet_fields: List[str] = Field(..., description="Fields to facet on", min_length=1)
    n_results: int = Field(20, description="Number of results to return", ge=1, le=500)
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

    document_ids: List[str] = Field(..., description="Document IDs to delete", min_length=1)


class BulkDeleteResponse(BaseModel):
    """Response after bulk delete."""

    deleted_count: int = Field(..., description="Number of documents deleted")
    not_found_count: int = Field(..., description="Number of documents not found")
    document_ids: List[str] = Field(..., description="IDs of deleted documents")


# Session Models
class SessionStatus(str, Enum):
    """Session status."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    EXPIRED = "expired"


class UserSettings(BaseModel):
    """User-specific settings and preferences."""

    default_search_mode: str = Field("hybrid", description="Default search mode")
    default_n_results: int = Field(5, description="Default number of results", ge=1, le=100)
    use_reranking: bool = Field(False, description="Use reranking by default")
    use_query_expansion: bool = Field(False, description="Use query expansion by default")
    use_diversification: bool = Field(False, description="Use diversification by default")
    show_scores: bool = Field(True, description="Show relevance scores")
    show_metadata: bool = Field(True, description="Show metadata in results")
    max_content_length: int = Field(500, description="Max content length to display", ge=100, le=2000)
    default_collection: Optional[str] = Field(None, description="Default collection name")
    custom_metadata: Dict[str, Any] = Field(default_factory=dict, description="Custom user metadata")


class ConversationMessage(BaseModel):
    """A single message in conversation history."""

    role: str = Field(..., description="Message role (user/assistant/system)")
    content: str = Field(..., description="Message content")
    timestamp: str = Field(..., description="ISO timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Message metadata")


class Session(BaseModel):
    """User session."""

    session_id: str = Field(..., description="Unique session ID")
    user_id: Optional[str] = Field(None, description="User ID")
    created_at: str = Field(..., description="Creation timestamp (ISO)")
    last_accessed: str = Field(..., description="Last accessed timestamp (ISO)")
    expires_at: Optional[str] = Field(None, description="Expiration timestamp (ISO)")
    status: SessionStatus = Field(SessionStatus.ACTIVE, description="Session status")
    settings: UserSettings = Field(default_factory=UserSettings, description="User settings")
    conversation_history: List[ConversationMessage] = Field(default_factory=list, description="Conversation history")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Session metadata")
    collection_name: Optional[str] = Field(None, description="Collection name for this session")


class CreateSessionRequest(BaseModel):
    """Request to create a new session."""

    user_id: Optional[str] = Field(None, description="User ID")
    ttl_minutes: Optional[int] = Field(60, description="Session TTL in minutes", ge=1, le=10080)
    settings: Optional[UserSettings] = Field(None, description="User settings")
    collection_name: Optional[str] = Field(None, description="Collection name")


class CreateSessionResponse(BaseModel):
    """Response after creating a session."""

    session: Session = Field(..., description="Created session")


class UpdateSessionRequest(BaseModel):
    """Request to update a session."""

    user_id: Optional[str] = Field(None, description="User ID")
    status: Optional[SessionStatus] = Field(None, description="Session status")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Session metadata")
    collection_name: Optional[str] = Field(None, description="Collection name")


class SessionListResponse(BaseModel):
    """Response with list of sessions."""

    sessions: List[Session] = Field(..., description="List of sessions")
    total: int = Field(..., description="Total number of sessions")


class SessionStatsResponse(BaseModel):
    """Session statistics response."""

    total_sessions: int = Field(..., description="Total sessions")
    active_sessions: int = Field(..., description="Active sessions")
    inactive_sessions: int = Field(..., description="Inactive sessions")
    expired_sessions: int = Field(..., description="Expired sessions")
    unique_users: int = Field(..., description="Unique users")


class AddMessageRequest(BaseModel):
    """Request to add a message to session."""

    role: str = Field(..., description="Message role")
    content: str = Field(..., description="Message content")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Message metadata")


# Diagram Models
class DiagramType(str, Enum):
    """Types of Mermaid diagrams."""

    SEQUENCE = "sequence"
    ER = "er"
    FLOWCHART = "flowchart"
    CLASS = "class"


class GenerateSequenceDiagramRequest(BaseModel):
    """Request to generate sequence diagram."""

    endpoint_id: str = Field(..., description="Document ID of the endpoint")


class GenerateAuthFlowRequest(BaseModel):
    """Request to generate authentication flow diagram."""

    auth_type: str = Field(..., description="Authentication type (bearer, oauth2, apikey, basic)")
    endpoints: Optional[List[str]] = Field(None, description="Optional list of endpoints")


class GenerateERDiagramRequest(BaseModel):
    """Request to generate ER diagram from GraphQL schema."""

    schema_content: str = Field(..., description="GraphQL schema content")
    include_types: Optional[List[str]] = Field(None, description="Optional list of type names to include")


class GenerateOverviewRequest(BaseModel):
    """Request to generate API overview diagram."""

    api_title: str = Field(..., description="API title")
    endpoints: List[Dict[str, Any]] = Field(..., description="List of endpoint summaries with tags")


class DiagramResponse(BaseModel):
    """Diagram generation response."""

    diagram_type: DiagramType = Field(..., description="Type of diagram")
    mermaid_code: str = Field(..., description="Mermaid diagram code")
    title: Optional[str] = Field(None, description="Diagram title")


# Chat Models
class ChatMessageRole(str, Enum):
    """Chat message roles."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ChatMessage(BaseModel):
    """A single chat message."""

    role: ChatMessageRole = Field(..., description="Message role")
    content: str = Field(..., description="Message content")
    timestamp: Optional[str] = Field(None, description="ISO timestamp")


class ChatSource(BaseModel):
    """Source reference in chat response."""

    type: str = Field(..., description="Source type (scraped_url, indexed_doc)")
    title: str = Field(..., description="Source title")
    url: Optional[str] = Field(None, description="Source URL")
    api_name: Optional[str] = Field(None, description="API name")
    method: Optional[str] = Field(None, description="HTTP method")
    score: float = Field(..., description="Relevance score")


class ChatRequest(BaseModel):
    """Request for AI chat generation."""

    message: str = Field(..., description="User message", min_length=1)
    session_id: Optional[str] = Field(None, description="Session ID for history")
    conversation_history: Optional[List[ChatMessage]] = Field(
        default_factory=list,
        description="Previous conversation messages (optional)",
    )
    enable_url_scraping: bool = Field(
        True,
        description="Enable automatic URL extraction and scraping",
    )
    enable_auto_indexing: bool = Field(
        True,
        description="Enable automatic indexing of scraped content",
    )
    agent_type: str = Field(
        "general",
        description="LLM agent type (general, code, reasoning)",
    )


class ChatResponse(BaseModel):
    """Response from AI chat generation."""

    response: str = Field(..., description="AI-generated response")
    sources: List[ChatSource] = Field(
        default_factory=list,
        description="Sources used for context",
    )
    scraped_urls: List[str] = Field(
        default_factory=list,
        description="URLs that were successfully scraped",
    )
    failed_urls: List[str] = Field(
        default_factory=list,
        description="URLs that failed to scrape (network/DNS errors)",
    )
    indexed_docs: int = Field(0, description="Number of documents indexed")
    context_results: int = Field(0, description="Number of context results used")
    session_id: Optional[str] = Field(None, description="Session ID")
    timestamp: str = Field(..., description="Response timestamp")
