"""
FastAPI REST API Application for API Assistant.

Provides REST endpoints for:
- Document management (add, delete, get)
- Search (vector, hybrid, re-ranked)
- Advanced features (query expansion, diversification)
- Faceted search
- Health and statistics

Author: API Assistant Team
Date: 2025-12-27
"""

import structlog
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.api.models import (
    AddDocumentsRequest,
    AddDocumentsResponse,
    AddMessageRequest,
    BulkDeleteRequest,
    BulkDeleteResponse,
    CollectionStats,
    ConversationMessage,
    CreateSessionRequest,
    CreateSessionResponse,
    DeleteDocumentResponse,
    DiagramResponse,
    DiagramType,
    Document,
    DocumentResponse,
    ErrorResponse,
    FacetedSearchRequest,
    FacetedSearchResponse,
    FacetResult,
    FacetValue,
    FilterOperatorEnum,
    FilterSpec,
    GenerateAuthFlowRequest,
    GenerateSequenceDiagramRequest,
    HealthResponse,
    SearchMode,
    SearchRequest,
    SearchResponse,
    SearchResult,
    Session,
    SessionListResponse,
    SessionStatsResponse,
    SessionStatus,
    StatsResponse,
    UpdateSessionRequest,
    UserSettings,
)
from src.core import (
    CombinedFilter,
    ContentFilter,
    FilterBuilder,
    FilterOperator,
    MetadataFilter,
    QueryExpander,
    ResultDiversifier,
    VectorStore,
)
from src.sessions import get_session_manager
from src.diagrams import MermaidGenerator

logger = structlog.get_logger(__name__)

# API Version
API_VERSION = "1.0.0"


def create_app(
    enable_hybrid: bool = True,
    enable_reranker: bool = True,
    enable_cors: bool = True,
) -> FastAPI:
    """
    Create FastAPI application.

    Args:
        enable_hybrid: Enable hybrid search
        enable_reranker: Enable cross-encoder re-ranking
        enable_cors: Enable CORS middleware

    Returns:
        FastAPI application instance
    """
    app = FastAPI(
        title="API Assistant REST API",
        description="Advanced semantic search API for API documentation",
        version=API_VERSION,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Add CORS middleware
    if enable_cors:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # Configure appropriately for production
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    # Initialize services
    vector_store = VectorStore(
        enable_hybrid_search=enable_hybrid,
        enable_reranker=enable_reranker,
    )
    query_expander = QueryExpander()
    result_diversifier = ResultDiversifier()
    session_manager = get_session_manager()
    mermaid_generator = MermaidGenerator()

    # Helper functions
    def convert_filter_spec_to_filter(filter_spec: FilterSpec):
        """Convert FilterSpec to Filter object."""
        if filter_spec.operator == FilterOperatorEnum.AND:
            sub_filters = [
                convert_filter_spec_to_filter(f) for f in filter_spec.filters
            ]
            return CombinedFilter(FilterOperator.AND, sub_filters)
        elif filter_spec.operator == FilterOperatorEnum.OR:
            sub_filters = [
                convert_filter_spec_to_filter(f) for f in filter_spec.filters
            ]
            return CombinedFilter(FilterOperator.OR, sub_filters)
        elif filter_spec.operator == FilterOperatorEnum.NOT:
            sub_filter = convert_filter_spec_to_filter(filter_spec.filters[0])
            return CombinedFilter(FilterOperator.NOT, [sub_filter])
        else:
            # Map operator enum to FilterOperator
            operator_map = {
                FilterOperatorEnum.EQ: FilterOperator.EQ,
                FilterOperatorEnum.NE: FilterOperator.NE,
                FilterOperatorEnum.GT: FilterOperator.GT,
                FilterOperatorEnum.GTE: FilterOperator.GTE,
                FilterOperatorEnum.LT: FilterOperator.LT,
                FilterOperatorEnum.LTE: FilterOperator.LTE,
                FilterOperatorEnum.CONTAINS: FilterOperator.CONTAINS,
                FilterOperatorEnum.NOT_CONTAINS: FilterOperator.NOT_CONTAINS,
                FilterOperatorEnum.STARTS_WITH: FilterOperator.STARTS_WITH,
                FilterOperatorEnum.ENDS_WITH: FilterOperator.ENDS_WITH,
                FilterOperatorEnum.REGEX: FilterOperator.REGEX,
                FilterOperatorEnum.IN: FilterOperator.IN,
                FilterOperatorEnum.NOT_IN: FilterOperator.NOT_IN,
            }

            operator = operator_map.get(filter_spec.operator)
            if not operator:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Unsupported operator: {filter_spec.operator}",
                )

            # Check if it's a content filter (no field specified)
            if filter_spec.field is None:
                if operator not in [
                    FilterOperator.CONTAINS,
                    FilterOperator.NOT_CONTAINS,
                ]:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Content filters only support CONTAINS and NOT_CONTAINS",
                    )
                return ContentFilter(operator, filter_spec.value)
            else:
                return MetadataFilter(filter_spec.field, operator, filter_spec.value)

    # Exception handlers
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request, exc):
        """Handle HTTP exceptions."""
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(
                error=exc.__class__.__name__,
                message=exc.detail,
            ).model_dump(),
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request, exc):
        """Handle general exceptions."""
        logger.error("Unhandled exception", exc_info=exc)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ErrorResponse(
                error=exc.__class__.__name__,
                message="Internal server error",
                detail={"message": str(exc)},
            ).model_dump(),
        )

    # Health and Status Endpoints
    @app.get("/health", response_model=HealthResponse, tags=["Health"])
    async def health_check():
        """
        Health check endpoint.

        Returns service status and available features.
        """
        return HealthResponse(
            status="healthy",
            version=API_VERSION,
            features={
                "hybrid_search": enable_hybrid,
                "reranking": enable_reranker,
                "query_expansion": True,
                "diversification": True,
                "faceted_search": True,
                "filtering": True,
            },
        )

    @app.get("/stats", response_model=StatsResponse, tags=["Stats"])
    async def get_stats():
        """
        Get collection statistics.

        Returns document count and enabled features.
        """
        try:
            collection = vector_store.collection
            count = collection.count()

            return StatsResponse(
                collection=CollectionStats(
                    total_documents=count,
                    collection_name=vector_store.collection_name,
                ),
                features={
                    "hybrid_search": enable_hybrid,
                    "reranking": enable_reranker,
                    "query_expansion": True,
                    "diversification": True,
                    "faceted_search": True,
                    "filtering": True,
                },
            )
        except Exception as e:
            logger.error("Error getting stats", exc_info=e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error getting statistics: {str(e)}",
            )

    # Document Management Endpoints
    @app.post(
        "/documents",
        response_model=AddDocumentsResponse,
        status_code=status.HTTP_201_CREATED,
        tags=["Documents"],
    )
    async def add_documents(request: AddDocumentsRequest):
        """
        Add documents to the collection.

        Adds one or more documents with content and metadata.
        """
        try:
            docs = [
                {
                    "content": doc.content,
                    "metadata": doc.metadata,
                    "id": doc.id,
                }
                for doc in request.documents
            ]

            doc_ids = vector_store.add_documents(docs)

            logger.info("Documents added", count=len(doc_ids))

            return AddDocumentsResponse(
                document_ids=doc_ids,
                count=len(doc_ids),
            )
        except Exception as e:
            logger.error("Error adding documents", exc_info=e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error adding documents: {str(e)}",
            )

    @app.get(
        "/documents/{document_id}",
        response_model=DocumentResponse,
        tags=["Documents"],
    )
    async def get_document(document_id: str):
        """
        Get a document by ID.

        Returns document content and metadata.
        """
        try:
            doc = vector_store.get_document(document_id)

            if not doc:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Document not found: {document_id}",
                )

            return DocumentResponse(
                id=doc["id"],
                content=doc["content"],
                metadata=doc["metadata"],
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Error getting document", document_id=document_id, exc_info=e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error getting document: {str(e)}",
            )

    @app.delete(
        "/documents/{document_id}",
        response_model=DeleteDocumentResponse,
        tags=["Documents"],
    )
    async def delete_document(document_id: str):
        """
        Delete a document by ID.

        Returns success status and message.
        """
        try:
            success = vector_store.delete_document(document_id)

            if not success:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Document not found: {document_id}",
                )

            logger.info("Document deleted", document_id=document_id)

            return DeleteDocumentResponse(
                success=True,
                message=f"Document {document_id} deleted successfully",
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Error deleting document", document_id=document_id, exc_info=e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error deleting document: {str(e)}",
            )

    @app.post(
        "/documents/bulk-delete",
        response_model=BulkDeleteResponse,
        tags=["Documents"],
    )
    async def bulk_delete_documents(request: BulkDeleteRequest):
        """
        Delete multiple documents by IDs.

        Returns count of deleted and not found documents.
        """
        try:
            deleted_ids = []
            not_found_count = 0

            for doc_id in request.document_ids:
                success = vector_store.delete_document(doc_id)
                if success:
                    deleted_ids.append(doc_id)
                else:
                    not_found_count += 1

            logger.info(
                "Bulk delete completed",
                deleted=len(deleted_ids),
                not_found=not_found_count,
            )

            return BulkDeleteResponse(
                deleted_count=len(deleted_ids),
                not_found_count=not_found_count,
                document_ids=deleted_ids,
            )
        except Exception as e:
            logger.error("Error in bulk delete", exc_info=e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error in bulk delete: {str(e)}",
            )

    # Search Endpoints
    @app.post("/search", response_model=SearchResponse, tags=["Search"])
    async def search(request: SearchRequest):
        """
        Search for documents.

        Supports multiple search modes:
        - vector: Pure vector similarity search
        - hybrid: BM25 + vector with RRF fusion
        - reranked: Hybrid search + cross-encoder re-ranking

        Optional features:
        - Query expansion
        - Result diversification
        - Filtering
        """
        try:
            query = request.query
            expanded_query = None

            # Apply query expansion if requested
            if request.use_query_expansion:
                expansion = query_expander.expand_and_format(query)
                expanded_query = expansion
                query = expansion
                logger.debug("Query expanded", original=request.query, expanded=query)

            # Convert filter if provided
            filter_obj = None
            if request.filter:
                filter_obj = convert_filter_spec_to_filter(request.filter)

            # Determine search parameters based on mode
            use_hybrid = request.mode in [SearchMode.HYBRID, SearchMode.RERANKED]
            use_reranker = request.mode == SearchMode.RERANKED

            # Perform search
            results = vector_store.search(
                query=query,
                n_results=request.n_results,
                where=filter_obj,
                use_hybrid=use_hybrid,
                use_reranker=use_reranker,
            )

            # Apply diversification if requested
            if request.use_diversification and len(results) > 1:
                diversifier = ResultDiversifier(
                    lambda_param=request.diversification_lambda,
                    embedding_service=vector_store.embedding_service,
                )
                results = diversifier.diversify(results, top_k=request.n_results)
                logger.debug("Results diversified", count=len(results))

            # Convert to response format
            search_results = [
                SearchResult(
                    id=r["id"],
                    content=r["content"],
                    metadata=r["metadata"],
                    score=r["score"],
                    method=r.get("method"),
                )
                for r in results
            ]

            logger.info(
                "Search completed",
                query=request.query,
                mode=request.mode,
                results=len(search_results),
            )

            return SearchResponse(
                results=search_results,
                total=len(search_results),
                query=request.query,
                expanded_query=expanded_query,
                mode=request.mode,
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Error in search", exc_info=e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error in search: {str(e)}",
            )

    @app.post(
        "/search/faceted",
        response_model=FacetedSearchResponse,
        tags=["Search"],
    )
    async def faceted_search(request: FacetedSearchRequest):
        """
        Faceted search for documents.

        Performs search and computes facet aggregations for specified fields.
        Useful for building filter UIs with category counts.
        """
        try:
            # Convert filter if provided
            filter_obj = None
            if request.filter:
                filter_obj = convert_filter_spec_to_filter(request.filter)

            # Perform faceted search
            results, facets = vector_store.search_with_facets(
                query=request.query,
                facet_fields=request.facet_fields,
                n_results=request.n_results,
                where=filter_obj,
                use_hybrid=True,
            )

            # Convert results to response format
            search_results = [
                SearchResult(
                    id=r["id"],
                    content=r["content"],
                    metadata=r["metadata"],
                    score=r["score"],
                    method=r.get("method"),
                )
                for r in results
            ]

            # Convert facets to response format
            facet_results = {}
            for field, facet in facets.items():
                top_values = facet.get_top_values(request.top_facet_values)
                facet_values = [
                    FacetValue(
                        value=value,
                        count=count,
                        percentage=facet.get_percentage(value),
                    )
                    for value, count in top_values
                ]

                facet_results[field] = FacetResult(
                    field=field,
                    values=facet_values,
                    total_docs=facet.total_docs,
                )

            logger.info(
                "Faceted search completed",
                query=request.query,
                results=len(search_results),
                facets=list(facet_results.keys()),
            )

            return FacetedSearchResponse(
                results=search_results,
                facets=facet_results,
                total=len(search_results),
                query=request.query,
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Error in faceted search", exc_info=e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error in faceted search: {str(e)}",
            )

    # Session Management Endpoints
    @app.post(
        "/sessions",
        response_model=CreateSessionResponse,
        status_code=status.HTTP_201_CREATED,
        tags=["Sessions"],
    )
    async def create_session(request: CreateSessionRequest):
        """
        Create a new user session.

        Creates an isolated session with user-specific settings and conversation history.
        """
        try:
            # Convert Pydantic model to dataclass
            from src.sessions.session_manager import UserSettings as SessionUserSettings

            settings = None
            if request.settings:
                settings = SessionUserSettings(
                    default_search_mode=request.settings.default_search_mode,
                    default_n_results=request.settings.default_n_results,
                    use_reranking=request.settings.use_reranking,
                    use_query_expansion=request.settings.use_query_expansion,
                    use_diversification=request.settings.use_diversification,
                    show_scores=request.settings.show_scores,
                    show_metadata=request.settings.show_metadata,
                    max_content_length=request.settings.max_content_length,
                    default_collection=request.settings.default_collection,
                    custom_metadata=request.settings.custom_metadata,
                )

            session = session_manager.create_session(
                user_id=request.user_id,
                ttl_minutes=request.ttl_minutes,
                settings=settings,
                collection_name=request.collection_name,
            )

            # Convert to API model
            session_dict = session.to_dict()
            api_session = Session(**session_dict)

            logger.info("Session created via API", session_id=session.session_id)

            return CreateSessionResponse(session=api_session)
        except Exception as e:
            logger.error("Error creating session", exc_info=e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error creating session: {str(e)}",
            )

    @app.get(
        "/sessions/{session_id}",
        response_model=Session,
        tags=["Sessions"],
    )
    async def get_session(session_id: str):
        """
        Get session by ID.

        Returns session details including conversation history and settings.
        """
        try:
            session = session_manager.get_session(session_id)

            if session is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Session not found: {session_id}",
                )

            session_dict = session.to_dict()
            return Session(**session_dict)
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Error getting session", session_id=session_id, exc_info=e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error getting session: {str(e)}",
            )

    @app.get(
        "/sessions",
        response_model=SessionListResponse,
        tags=["Sessions"],
    )
    async def list_sessions(
        user_id: Optional[str] = None,
        status_filter: Optional[SessionStatus] = None,
    ):
        """
        List all sessions with optional filters.

        Filter by user_id or status to get specific sessions.
        """
        try:
            from src.sessions.session_manager import SessionStatus as BackendSessionStatus

            backend_status = None
            if status_filter:
                backend_status = BackendSessionStatus(status_filter.value)

            sessions = session_manager.list_sessions(
                user_id=user_id,
                status=backend_status,
            )

            api_sessions = [Session(**s.to_dict()) for s in sessions]

            return SessionListResponse(
                sessions=api_sessions,
                total=len(api_sessions),
            )
        except Exception as e:
            logger.error("Error listing sessions", exc_info=e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error listing sessions: {str(e)}",
            )

    @app.patch(
        "/sessions/{session_id}",
        response_model=Session,
        tags=["Sessions"],
    )
    async def update_session(session_id: str, request: UpdateSessionRequest):
        """
        Update session attributes.

        Update user_id, status, metadata, or collection_name.
        """
        try:
            update_kwargs = {}
            if request.user_id is not None:
                update_kwargs["user_id"] = request.user_id
            if request.status is not None:
                update_kwargs["status"] = request.status.value
            if request.metadata is not None:
                update_kwargs["metadata"] = request.metadata
            if request.collection_name is not None:
                update_kwargs["collection_name"] = request.collection_name

            session = session_manager.update_session(session_id, **update_kwargs)

            if session is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Session not found: {session_id}",
                )

            session_dict = session.to_dict()
            return Session(**session_dict)
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Error updating session", session_id=session_id, exc_info=e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error updating session: {str(e)}",
            )

    @app.delete(
        "/sessions/{session_id}",
        response_model=DeleteDocumentResponse,
        tags=["Sessions"],
    )
    async def delete_session(session_id: str):
        """
        Delete a session.

        Permanently removes the session and its conversation history.
        """
        try:
            success = session_manager.delete_session(session_id)

            if not success:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Session not found: {session_id}",
                )

            logger.info("Session deleted via API", session_id=session_id)

            return DeleteDocumentResponse(
                success=True,
                message=f"Session {session_id} deleted successfully",
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Error deleting session", session_id=session_id, exc_info=e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error deleting session: {str(e)}",
            )

    @app.get(
        "/sessions/stats",
        response_model=SessionStatsResponse,
        tags=["Sessions"],
    )
    async def get_session_stats():
        """
        Get session statistics.

        Returns counts of total, active, inactive, and expired sessions.
        """
        try:
            stats = session_manager.get_stats()
            return SessionStatsResponse(**stats)
        except Exception as e:
            logger.error("Error getting session stats", exc_info=e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error getting session stats: {str(e)}",
            )

    @app.post(
        "/sessions/{session_id}/messages",
        response_model=Session,
        tags=["Sessions"],
    )
    async def add_message_to_session(session_id: str, request: AddMessageRequest):
        """
        Add a message to session conversation history.

        Stores user or assistant messages in the session.
        """
        try:
            session = session_manager.get_session(session_id)

            if session is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Session not found: {session_id}",
                )

            session.add_message(
                role=request.role,
                content=request.content,
                metadata=request.metadata,
            )

            # Persist the updated session
            session_manager._save_sessions()

            session_dict = session.to_dict()
            return Session(**session_dict)
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Error adding message to session", session_id=session_id, exc_info=e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error adding message: {str(e)}",
            )

    # Diagram Generation Endpoints
    @app.post(
        "/diagrams/sequence",
        response_model=DiagramResponse,
        tags=["Diagrams"],
    )
    async def generate_sequence_diagram(request: GenerateSequenceDiagramRequest):
        """
        Generate a sequence diagram from an API endpoint.

        Creates a Mermaid sequence diagram showing the request/response flow.
        """
        try:
            # Get the endpoint document
            doc = vector_store.get_document(request.endpoint_id)

            if not doc:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Endpoint document not found: {request.endpoint_id}",
                )

            # Parse endpoint to create diagram
            # Note: This is a simplified version - full implementation would parse the document
            from src.diagrams.mermaid_generator import SequenceDiagram

            diagram = SequenceDiagram(
                title=doc["metadata"].get("endpoint", "API Endpoint"),
                participants=["Client", "API", "Backend"],
            )

            # Build basic sequence
            diagram.interactions.append({
                "from": "Client",
                "to": "API",
                "arrow": "->>",
                "message": f"{doc['metadata'].get('method', 'GET')} {doc['metadata'].get('endpoint', '/')}",
            })

            diagram.interactions.append({
                "from": "API",
                "to": "Backend",
                "arrow": "->>",
                "message": "Process request",
            })

            diagram.interactions.append({
                "from": "Backend",
                "to": "API",
                "arrow": "-->>",
                "message": "200 OK",
            })

            diagram.interactions.append({
                "from": "API",
                "to": "Client",
                "arrow": "-->>",
                "message": "Response",
            })

            mermaid_code = diagram.to_mermaid()

            logger.info("Sequence diagram generated", endpoint_id=request.endpoint_id)

            return DiagramResponse(
                diagram_type=DiagramType.SEQUENCE,
                mermaid_code=mermaid_code,
                title=diagram.title,
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Error generating sequence diagram", exc_info=e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error generating diagram: {str(e)}",
            )

    @app.post(
        "/diagrams/auth-flow",
        response_model=DiagramResponse,
        tags=["Diagrams"],
    )
    async def generate_auth_flow_diagram(request: GenerateAuthFlowRequest):
        """
        Generate an authentication flow diagram.

        Creates a flowchart showing the authentication process.
        """
        try:
            diagram = mermaid_generator.generate_auth_flow(
                auth_type=request.auth_type,
                endpoints=request.endpoints,
            )

            mermaid_code = diagram.to_mermaid()

            logger.info("Auth flow diagram generated", auth_type=request.auth_type)

            return DiagramResponse(
                diagram_type=DiagramType.FLOWCHART,
                mermaid_code=mermaid_code,
                title=diagram.title,
            )
        except Exception as e:
            logger.error("Error generating auth flow diagram", exc_info=e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error generating diagram: {str(e)}",
            )

    return app


# Create default app instance
app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
