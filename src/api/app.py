"""
FastAPI REST API Application for Intelligent Coding Agent.

Provides REST endpoints for:
- Search (vector, hybrid, re-ranked)
- Session management
- AI Chat with code generation
- Health and statistics

Author: API Assistant Team
Date: 2025-12-27
"""

import structlog
from typing import List, Optional
from fastapi import Depends, FastAPI, File, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.api.auth import verify_api_key, get_current_user_optional, CurrentUser
from src.api.auth_router import router as auth_router, init_auth_db
from src.api.execute_router import router as execute_router
from src.api.artifact_router import router as artifact_router
from src.api.sandbox_router import router as sandbox_router
from src.api.preview_router import router as preview_router
from src.api.security_router import router as security_router
from src.api.mock_router import router as mock_router
from src.api.template_router import router as template_router
from src.api.database_router import router as database_router

from src.api.models import (
    AddMessageRequest,
    ChatMessage,
    ChatRequest,
    ChatResponse,
    ChatSource,
    CollectionStats,
    ConversationMessage,
    CreateSessionRequest,
    CreateSessionResponse,
    ErrorResponse,
    FilterOperatorEnum,
    FilterSpec,
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
from src.config import get_settings
from src.core import (
    CombinedFilter,
    ContentFilter,
    FilterBuilder,
    FilterOperator,
    MetadataFilter,
    QueryExpander,
    VectorStore,
)
from src.sessions import get_session_manager

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

    # Add CORS middleware with secure configuration
    if enable_cors:
        settings = get_settings()
        cors_origins = settings.cors_origins
        logger.info(f"CORS enabled for origins: {cors_origins}")

        app.add_middleware(
            CORSMiddleware,
            allow_origins=cors_origins,  # From environment variable
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    # Include authentication router
    app.include_router(auth_router)

    # Include execute router for code generation
    app.include_router(execute_router)

    # Include artifact router for file management
    app.include_router(artifact_router)

    # Include sandbox router for screenshots and UI testing
    app.include_router(sandbox_router)

    # Include preview router for live previews
    app.include_router(preview_router)

    # Include security router for vulnerability scanning
    app.include_router(security_router)

    # Include mock router for API mocking
    app.include_router(mock_router)

    # Include template router for code templates
    app.include_router(template_router)

    # Include database router for query generation
    app.include_router(database_router)

    # Add startup event for database initialization
    @app.on_event("startup")
    async def startup_event():
        """Initialize services on application startup."""
        logger.info("Initializing authentication database...")
        await init_auth_db()
        logger.info("Application startup complete")

    # Initialize services
    vector_store = VectorStore(
        enable_hybrid_search=enable_hybrid,
        enable_reranker=enable_reranker,
    )
    query_expander = QueryExpander()
    session_manager = get_session_manager()

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
                    "filtering": True,
                },
            )
        except Exception as e:
            logger.error("Error getting stats", exc_info=e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error getting statistics: {str(e)}",
            )

    # Search Endpoints
    @app.post("/search", response_model=SearchResponse, tags=["Search"])
    async def search(
        request: SearchRequest,
        api_key: str = Depends(verify_api_key),
    ):
        """
        Search for documents.

        Supports multiple search modes:
        - vector: Pure vector similarity search
        - hybrid: BM25 + vector with RRF fusion
        - reranked: Hybrid search + cross-encoder re-ranking

        Optional features:
        - Query expansion
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
                logger.info("Filter received", filter=request.filter.model_dump())
                filter_obj = convert_filter_spec_to_filter(request.filter)
                logger.info("Filter converted", filter_obj=str(filter_obj))

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
                min_score=request.min_score,
            )

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

    # Session Management Endpoints
    @app.post(
        "/sessions",
        response_model=CreateSessionResponse,
        status_code=status.HTTP_201_CREATED,
        tags=["Sessions"],
    )
    async def create_session(
        request: CreateSessionRequest,
        current_user: CurrentUser = Depends(get_current_user_optional),
    ):
        """
        Create a new user session.

        Creates an isolated session with user-specific settings and conversation history.
        If authenticated, the session is automatically linked to the user.
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

            # Use authenticated user_id if available, otherwise use request.user_id
            user_id = current_user.user_id if current_user.is_authenticated else request.user_id

            session = session_manager.create_session(
                user_id=user_id,
                ttl_minutes=request.ttl_minutes,
                settings=settings,
                collection_name=request.collection_name,
            )

            # Convert to API model
            session_dict = session.to_dict()
            api_session = Session(**session_dict)

            logger.info("Session created via API", session_id=session.session_id, user_id=user_id)

            return CreateSessionResponse(session=api_session)
        except Exception as e:
            logger.error("Error creating session", exc_info=e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error creating session: {str(e)}",
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

    @app.get(
        "/sessions/{session_id}",
        response_model=Session,
        tags=["Sessions"],
    )
    async def get_session(session_id: str):
        """
        Get session by ID.

        Returns session details including conversation history and settings.
        This endpoint allows viewing expired sessions for historical reference.
        """
        try:
            # Allow viewing expired sessions (include_expired=True)
            session = session_manager.get_session_by_id(session_id, include_expired=True)

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
        current_user: CurrentUser = Depends(get_current_user_optional),
    ):
        """
        List sessions with optional filters.

        If authenticated, only returns the user's own sessions.
        Admins or API key users can filter by any user_id.
        Guests see only their current guest sessions.
        """
        try:
            from src.sessions.session_manager import SessionStatus as BackendSessionStatus

            backend_status = None
            if status_filter:
                backend_status = BackendSessionStatus(status_filter.value)

            # Determine which user_id to filter by
            effective_user_id = user_id
            if current_user.is_authenticated and current_user.auth_method == "jwt":
                # JWT authenticated users can only see their own sessions
                # unless they provided a specific user_id and it matches theirs
                if user_id is None or user_id == current_user.user_id:
                    effective_user_id = current_user.user_id
                elif not current_user.is_guest:
                    # Non-guest authenticated user trying to access other user's sessions
                    effective_user_id = current_user.user_id  # Force to own sessions

            sessions = session_manager.list_sessions(
                user_id=effective_user_id,
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

    @app.post(
        "/sessions/{session_id}/activate",
        response_model=Session,
        tags=["Sessions"],
    )
    async def activate_session(session_id: str, ttl_minutes: Optional[int] = None):
        """
        Activate an expired or inactive session.

        Resets the expiration time and sets the status to ACTIVE.
        This allows users to continue using previously expired sessions.

        Args:
            session_id: The session ID to activate
            ttl_minutes: Optional new TTL in minutes (uses default if not provided)
        """
        try:
            session = session_manager.activate_session(session_id, ttl_minutes)

            if session is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Session not found: {session_id}",
                )

            logger.info("Session activated via API", session_id=session_id)

            session_dict = session.to_dict()
            return Session(**session_dict)
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Error activating session", session_id=session_id, exc_info=e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error activating session: {str(e)}",
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

    @app.delete(
        "/sessions/{session_id}/messages",
        response_model=Session,
        tags=["Sessions"],
    )
    async def clear_session_history(session_id: str):
        """
        Clear all conversation history from a session.

        Permanently deletes all messages from the session's conversation history
        while preserving the session itself and its metadata.
        This action cannot be undone.
        """
        try:
            session = session_manager.clear_session_history(session_id)

            if session is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Session not found: {session_id}",
                )

            logger.info("Session history cleared via API", session_id=session_id)

            session_dict = session.to_dict()
            return Session(**session_dict)
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Error clearing session history", session_id=session_id, exc_info=e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error clearing session history: {str(e)}",
            )

    # AI Chat Endpoint
    @app.post(
        "/chat",
        response_model=ChatResponse,
        tags=["Chat"],
    )
    async def chat_generate(
        message: str = Form(...),
        session_id: Optional[str] = Form(None),
        conversation_history: Optional[str] = Form(None),  # JSON string
        enable_url_scraping: bool = Form(True),
        enable_auto_indexing: bool = Form(True),
        agent_type: str = Form("general"),
        files: Optional[List[UploadFile]] = File(None),
        api_key: str = Depends(verify_api_key),
    ):
        """
        Generate AI-powered chat response with dynamic URL fetching, indexing, and file upload support.

        This endpoint:
        - Accepts optional file uploads (PDF, TXT, MD, JSON, etc.) for contextual analysis
        - Extracts URLs from the user message and scrapes their content
        - Dynamically indexes scraped content and uploaded files into the vector store
        - Searches for relevant context from existing documents
        - Generates intelligent responses using LLM (Groq/Ollama)
        - Supports code generation and API documentation assistance
        - Maintains conversation history if session_id provided

        Example:
            POST /chat (multipart/form-data)
            - message: "Explain this API specification"
            - session_id: "abc123"
            - files: [openapi.yaml]
        """
        try:
            import json
            from datetime import datetime, timezone
            from src.services.chat_service import get_chat_service
            from src.parsers.format_handler import UnifiedFormatHandler

            logger.info(
                "chat_request_received",
                message_length=len(message),
                has_files=files is not None and len(files) > 0,
            )

            # Parse conversation history if provided
            history_list = []
            if conversation_history:
                try:
                    history_data = json.loads(conversation_history)
                    history_list = [
                        {"role": msg.get("role", "user"), "content": msg.get("content", "")}
                        for msg in history_data
                    ]
                except json.JSONDecodeError:
                    logger.warning("Failed to parse conversation history JSON")

            # Process uploaded files if any
            uploaded_file_count = 0
            uploaded_file_names = []
            if files and len(files) > 0:
                logger.info("processing_uploaded_files", file_count=len(files))
                handler = UnifiedFormatHandler()

                for file in files:
                    try:
                        # Read file content
                        content = await file.read()

                        # Try UTF-8, fallback to latin-1, keep as bytes for binary files
                        try:
                            content_str = content.decode("utf-8")
                        except UnicodeDecodeError:
                            try:
                                content_str = content.decode("latin-1")
                            except:
                                # Keep as bytes for binary files (PDFs)
                                content_str = content

                        # Parse the document
                        logger.info("parsing_uploaded_file", filename=file.filename)
                        result = handler.parse_document(content_str, filename=file.filename or "")

                        # Add to vector store with session-specific metadata
                        docs = []
                        for doc in result.get("documents", []):
                            metadata = doc.get("metadata", {})
                            # Tag with session for potential cleanup
                            metadata["uploaded_via_chat"] = True
                            if session_id:
                                metadata["chat_session_id"] = session_id
                            metadata["upload_timestamp"] = datetime.now(timezone.utc).isoformat()
                            metadata["source_file"] = file.filename

                            docs.append({
                                "content": doc["content"],
                                "metadata": metadata,
                            })

                        if docs:
                            add_result = vector_store.add_documents(docs)
                            uploaded_file_count += add_result["new_count"]
                            uploaded_file_names.append(file.filename or "unknown")
                            logger.info(
                                "uploaded_file_indexed",
                                filename=file.filename,
                                chunks=len(docs),
                                new_count=add_result["new_count"],
                            )

                    except Exception as e:
                        logger.error(
                            "file_upload_processing_failed",
                            filename=file.filename,
                            error=str(e),
                        )
                        # Continue with other files
                        continue

            # Get chat service
            chat_service = get_chat_service(
                agent_type=agent_type,
                enable_url_scraping=enable_url_scraping,
                enable_auto_indexing=enable_auto_indexing,
            )

            # Generate response
            result = await chat_service.generate_response(
                user_message=message,
                conversation_history=history_list if history_list else None,
                session_id=session_id,
            )

            # Convert sources to ChatSource models
            sources = [ChatSource(**source) for source in result["sources"]]

            # Build response - include uploaded file count in indexed_docs
            total_indexed = result["indexed_docs"] + uploaded_file_count

            response = ChatResponse(
                response=result["response"],
                sources=sources,
                scraped_urls=result["scraped_urls"],
                failed_urls=result.get("failed_urls", []),
                indexed_docs=total_indexed,
                context_results=result["context_results"],
                session_id=session_id,
                timestamp=datetime.now(timezone.utc).isoformat(),
            )

            # If session provided, add messages to session history
            if session_id:
                logger.info(
                    "chat_attempting_to_save_history",
                    session_id=session_id,
                    total_sessions_in_manager=len(session_manager.sessions),
                )
                try:
                    session = session_manager.get_session(session_id)
                    if session:
                        logger.info(
                            "chat_session_found",
                            session_id=session_id,
                            current_message_count=len(session.conversation_history),
                        )
                        # Add user message
                        session.add_message(
                            role="user",
                            content=message,
                            metadata={
                                "scraped_urls": result["scraped_urls"],
                                "indexed_docs": total_indexed,
                                "uploaded_files": uploaded_file_names,
                            },
                        )
                        # Add assistant response
                        session.add_message(
                            role="assistant",
                            content=result["response"],
                            metadata={
                                "context_results": result["context_results"],
                                "sources_count": len(sources),
                            },
                        )
                        session_manager._save_sessions()
                        logger.info(
                            "chat_history_saved_successfully",
                            session_id=session_id,
                            new_message_count=len(session.conversation_history),
                        )
                    else:
                        # Log all existing session IDs to help debug
                        existing_ids = list(session_manager.sessions.keys())
                        logger.warning(
                            "chat_session_not_found_or_expired",
                            session_id=session_id,
                            existing_session_ids=existing_ids[:5],  # Log first 5 IDs
                            total_sessions=len(existing_ids),
                            message="Session not found or expired - messages not saved",
                        )
                except Exception as e:
                    logger.warning(
                        "chat_history_save_failed",
                        session_id=session_id,
                        error=str(e),
                    )
                    # Don't fail the request if history save fails

            logger.info(
                "chat_response_generated",
                scraped_urls=len(result["scraped_urls"]),
                indexed_docs=total_indexed,
                uploaded_files=len(uploaded_file_names),
                context_results=result["context_results"],
            )

            return response

        except Exception as e:
            logger.error("chat_generation_failed", error=str(e), exc_info=e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Chat generation failed: {str(e)}",
            )

    return app


# Create default app instance
app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
