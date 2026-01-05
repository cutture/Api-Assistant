"""
Unit tests for RAG Agent.
"""

from unittest.mock import Mock, patch

import pytest

from src.agents.rag_agent import RAGAgent
from src.agents.state import (
    AgentState,
    AgentType,
    IntentAnalysis,
    QueryIntent,
    RetrievedDocument,
    SourceCitation,
    create_initial_state,
)
from src.core.llm_client import LLMClient
from src.core.vector_store import VectorStore


class TestRAGAgent:
    """Test suite for RAG Agent."""

    @pytest.fixture
    def mock_vector_store(self):
        """Create a mock vector store."""
        return Mock(spec=VectorStore)

    @pytest.fixture
    def mock_llm_client(self):
        """Create a mock LLM client."""
        return Mock(spec=LLMClient)

    @pytest.fixture
    def mock_web_search(self):
        """Create a mock web search service."""
        mock = Mock()
        mock.search.return_value = []  # Default to no web results
        return mock

    @pytest.fixture
    def rag_agent(self, mock_vector_store, mock_llm_client, mock_web_search):
        """Create RAG agent with mocked dependencies."""
        return RAGAgent(
            vector_store=mock_vector_store,
            llm_client=mock_llm_client,
            web_search=mock_web_search,
            top_k=5,
            min_relevance_score=0.3,
        )

    def test_agent_properties(self, rag_agent):
        """Test agent properties are correct."""
        assert rag_agent.name == "rag_agent"
        assert rag_agent.agent_type == AgentType.RAG_AGENT
        assert "retriev" in rag_agent.description.lower()

    def test_process_with_empty_query(self, rag_agent):
        """Test processing with empty query returns error."""
        state = create_initial_state("")

        result = rag_agent.process(state)

        assert result.get("error") is not None
        assert result["error"]["agent"] == "rag_agent"
        assert result["error"]["error_type"] == "missing_input"

    def test_process_successful_retrieval(self, rag_agent, mock_vector_store, mock_llm_client):
        """Test successful document retrieval and answer generation."""
        # Mock vector store search results
        mock_search_results = [
            {
                "id": "doc1",
                "content": "The API uses Bearer token authentication. Include the token in the Authorization header.",
                "metadata": {"endpoint": "/auth", "method": "POST"},
                "score": 0.9,
            },
            {
                "id": "doc2",
                "content": "To get a token, send your credentials to POST /auth/login.",
                "metadata": {"endpoint": "/auth/login", "method": "POST"},
                "score": 0.85,
            },
        ]
        mock_vector_store.search.return_value = mock_search_results

        # Mock LLM responses
        mock_llm_client.generate.side_effect = [
            # First call: query expansion
            "How to get authentication token\nAPI authentication methods",
            # Second call: answer generation
            "To authenticate with the API, use Bearer token authentication by including your token in the Authorization header. You can obtain a token by sending your credentials to POST /auth/login.",
        ]

        # Create state
        state = create_initial_state("How do I authenticate with the API?")

        # Process
        result = rag_agent.process(state)

        # Verify no errors
        assert result.get("error") is None

        # Verify retrieved documents
        assert len(result["retrieved_documents"]) == 2
        doc1 = RetrievedDocument(**result["retrieved_documents"][0])
        assert doc1.score == 0.9
        assert "Bearer token" in doc1.content

        # Verify response generated
        assert result["response"]
        assert "Bearer token" in result["response"]
        assert "POST /auth/login" in result["response"]

        # Verify citations created
        assert len(result["sources"]) == 2
        citation1 = SourceCitation(**result["sources"][0])
        assert citation1.endpoint_path == "/auth"
        assert citation1.method == "POST"
        assert citation1.relevance_score == 0.9

        # Verify context formatted
        assert result["context_text"]
        assert "Bearer token" in result["context_text"]

    def test_process_no_documents_found(self, rag_agent, mock_vector_store, mock_llm_client):
        """Test handling when no documents are found."""
        # Mock empty search results
        mock_vector_store.search.return_value = []
        mock_llm_client.generate.return_value = "query variations"

        state = create_initial_state("Unknown query")
        result = rag_agent.process(state)

        # Should return helpful message
        assert result["retrieved_documents"] == []
        assert result["sources"] == []
        assert "couldn't find" in result["response"].lower()

    def test_query_expansion(self, rag_agent, mock_vector_store, mock_llm_client):
        """Test query expansion generates multiple variations."""
        # Mock LLM expansion response
        mock_llm_client.generate.return_value = """API authentication process
Get API access token
Bearer token authentication"""

        mock_vector_store.search.return_value = []

        state = create_initial_state("How to authenticate?")
        result = rag_agent.process(state)

        # Verify search was called multiple times (once per query variation)
        assert mock_vector_store.search.call_count > 1

    def test_query_expansion_with_intent_keywords(self, rag_agent, mock_vector_store, mock_llm_client):
        """Test query expansion uses intent keywords."""
        mock_vector_store.search.return_value = []
        mock_llm_client.generate.return_value = "variation"

        # Create state with intent analysis
        state = create_initial_state("How to auth?")
        intent = IntentAnalysis.from_confidence(
            intent=QueryIntent.AUTHENTICATION,
            score=0.9,
            keywords=["authenticate", "api", "token", "bearer"],
        )
        state["intent_analysis"] = intent.model_dump()

        result = rag_agent.process(state)

        # Should have used keywords in query expansion
        search_calls = mock_vector_store.search.call_args_list
        assert len(search_calls) > 1

    def test_relevance_score_filtering(self, rag_agent, mock_vector_store, mock_llm_client):
        """Test that low-relevance documents are filtered out."""
        # Mock results with varying scores
        mock_search_results = [
            {"id": "doc1", "content": "Relevant content", "metadata": {}, "score": 0.8},
            {"id": "doc2", "content": "Low relevance", "metadata": {}, "score": 0.2},
            {"id": "doc3", "content": "Also relevant", "metadata": {}, "score": 0.5},
        ]
        mock_vector_store.search.return_value = mock_search_results
        mock_llm_client.generate.side_effect = ["variations", "answer"]

        state = create_initial_state("test query")
        result = rag_agent.process(state)

        # Should only have docs with score >= 0.3
        retrieved = result["retrieved_documents"]
        assert len(retrieved) == 2  # doc1 and doc3
        assert all(RetrievedDocument(**doc).score >= 0.3 for doc in retrieved)

    def test_document_deduplication(self, rag_agent, mock_vector_store, mock_llm_client):
        """Test that duplicate documents are deduplicated with highest score kept."""
        # Mock searches returning duplicate doc_id with different scores
        search_call_count = [0]

        def search_side_effect(*args, **kwargs):
            search_call_count[0] += 1
            if search_call_count[0] == 1:
                return [
                    {"id": "doc1", "content": "Content A", "metadata": {}, "score": 0.7},
                ]
            else:
                return [
                    {"id": "doc1", "content": "Content A", "metadata": {}, "score": 0.9},
                ]

        mock_vector_store.search.side_effect = search_side_effect
        mock_llm_client.generate.side_effect = ["variation1\nvariation2", "answer"]

        state = create_initial_state("test")
        result = rag_agent.process(state)

        # Should have only one instance of doc1 with highest score
        retrieved = result["retrieved_documents"]
        assert len(retrieved) == 1
        assert RetrievedDocument(**retrieved[0]).score == 0.9

    def test_context_formatting(self, rag_agent):
        """Test context string formatting."""
        docs = [
            RetrievedDocument(
                content="Auth documentation",
                metadata={"endpoint": "/auth", "method": "POST", "operation_id": "authenticate"},
                score=0.9,
                doc_id="doc1",
            ),
            RetrievedDocument(
                content="User endpoint docs",
                metadata={"endpoint": "/users", "method": "GET"},
                score=0.8,
                doc_id="doc2",
            ),
        ]

        context = rag_agent._format_context(docs)

        assert "[Source 1]" in context
        assert "[Source 2]" in context
        assert "Endpoint: /auth" in context
        assert "Method: POST" in context
        assert "Operation: authenticate" in context
        assert "Auth documentation" in context
        assert "User endpoint docs" in context
        assert "---" in context  # Separator

    def test_context_formatting_empty(self, rag_agent):
        """Test context formatting with empty document list."""
        context = rag_agent._format_context([])
        assert context == ""

    def test_citation_creation(self, rag_agent):
        """Test source citation creation."""
        docs = [
            RetrievedDocument(
                content="Content",
                metadata={
                    "endpoint": "/users",
                    "method": "GET",
                    "operation_id": "list_users",
                    "summary": "List all users",
                },
                score=0.9,
                doc_id="doc1",
            ),
            RetrievedDocument(
                content="Content 2",
                metadata={"endpoint": "/auth", "method": "POST"},
                score=0.8,
                doc_id="doc2",
            ),
        ]

        citations = rag_agent._create_citations(docs)

        assert len(citations) == 2

        # First citation
        assert citations[0].endpoint_path == "/users"
        assert citations[0].method == "GET"
        assert citations[0].description == "list_users"
        assert citations[0].relevance_score == 0.9

        # Second citation
        assert citations[1].endpoint_path == "/auth"
        assert citations[1].method == "POST"
        assert citations[1].relevance_score == 0.8

    def test_citation_display_string(self, rag_agent):
        """Test citation display string formatting."""
        citation = SourceCitation(
            endpoint_path="/users",
            method="GET",
            description="List all users",
            relevance_score=0.9,
        )

        display = citation.to_display_string()
        assert "`GET /users`" in display
        assert "List all users" in display

    def test_search_by_metadata_method_filter(self, rag_agent, mock_vector_store):
        """Test metadata-based search with method filter."""
        mock_vector_store.search.return_value = [
            {"id": "doc1", "content": "POST endpoint", "metadata": {"method": "POST"}, "score": 0.9}
        ]

        results = rag_agent.search_by_metadata(
            query="create user",
            method="POST",
        )

        # Verify where filter was used
        call_kwargs = mock_vector_store.search.call_args.kwargs
        assert call_kwargs["where"] == {"method": "POST"}
        assert len(results) == 1

    def test_search_by_metadata_endpoint_filter(self, rag_agent, mock_vector_store):
        """Test metadata-based search with endpoint filter."""
        mock_vector_store.search.return_value = []

        rag_agent.search_by_metadata(
            query="users",
            endpoint="/users",
        )

        call_kwargs = mock_vector_store.search.call_args.kwargs
        assert call_kwargs["where"] == {"endpoint": "/users"}

    def test_search_by_metadata_tags_filter(self, rag_agent, mock_vector_store):
        """Test metadata-based search with tags filter."""
        mock_vector_store.search.return_value = []

        rag_agent.search_by_metadata(
            query="authentication",
            tags=["auth", "security"],
        )

        call_kwargs = mock_vector_store.search.call_args.kwargs
        assert call_kwargs["where"]["tags"] == {"$in": ["auth", "security"]}

    def test_search_by_metadata_combined_filters(self, rag_agent, mock_vector_store):
        """Test metadata-based search with combined filters."""
        mock_vector_store.search.return_value = []

        rag_agent.search_by_metadata(
            query="create",
            method="POST",
            endpoint="/users",
        )

        call_kwargs = mock_vector_store.search.call_args.kwargs
        where = call_kwargs["where"]
        assert where["method"] == "POST"
        assert where["endpoint"] == "/users"

    def test_query_expansion_fallback(self, rag_agent, mock_vector_store, mock_llm_client):
        """Test query expansion falls back gracefully when LLM fails."""
        # Mock LLM to raise exception
        mock_llm_client.generate.side_effect = [
            Exception("LLM error"),  # First call fails
            "Generated answer",  # Second call succeeds
        ]
        mock_vector_store.search.return_value = [
            {"id": "doc1", "content": "Content", "metadata": {}, "score": 0.8}
        ]

        state = create_initial_state("test query")
        result = rag_agent.process(state)

        # Should still work with just the original query
        assert result.get("error") is None
        assert result["response"] == "Generated answer"

    def test_llm_generation_error_handling(self, rag_agent, mock_vector_store, mock_llm_client):
        """Test error handling when LLM generation fails."""
        mock_vector_store.search.return_value = [
            {"id": "doc1", "content": "Content", "metadata": {}, "score": 0.8}
        ]
        # All LLM calls fail
        mock_llm_client.generate.side_effect = Exception("LLM connection error")

        state = create_initial_state("test query")
        result = rag_agent.process(state)

        # Should set error in state
        assert result.get("error") is not None
        assert result["error"]["error_type"] == "retrieval_error"
        assert "LLM connection error" in result["error"]["message"]

    def test_processing_path_updated(self, rag_agent, mock_vector_store, mock_llm_client):
        """Test that processing path is updated."""
        mock_vector_store.search.return_value = []
        mock_llm_client.generate.return_value = "variations"

        state = create_initial_state("test")
        state = rag_agent(state)  # Use __call__ to update path

        assert "rag_agent" in state["processing_path"]
        assert state["current_agent"] == "rag_agent"

    def test_top_k_limiting(self, rag_agent, mock_vector_store, mock_llm_client):
        """Test that results are limited to top_k."""
        # Return more documents than top_k
        mock_search_results = [
            {"id": f"doc{i}", "content": f"Content {i}", "metadata": {}, "score": 0.9 - (i * 0.05)}
            for i in range(10)
        ]
        mock_vector_store.search.return_value = mock_search_results
        mock_llm_client.generate.side_effect = ["variations", "answer"]

        state = create_initial_state("test")
        result = rag_agent.process(state)

        # Should be limited to top_k (5)
        assert len(result["retrieved_documents"]) <= 5

    def test_documents_sorted_by_score(self, rag_agent, mock_vector_store, mock_llm_client):
        """Test that retrieved documents are sorted by relevance score."""
        mock_search_results = [
            {"id": "doc1", "content": "Low", "metadata": {}, "score": 0.5},
            {"id": "doc2", "content": "High", "metadata": {}, "score": 0.9},
            {"id": "doc3", "content": "Medium", "metadata": {}, "score": 0.7},
        ]
        mock_vector_store.search.return_value = mock_search_results
        mock_llm_client.generate.side_effect = ["variations", "answer"]

        state = create_initial_state("test")
        result = rag_agent.process(state)

        # Verify sorted by score (highest first)
        docs = result["retrieved_documents"]
        scores = [RetrievedDocument(**doc).score for doc in docs]
        assert scores == sorted(scores, reverse=True)
        assert RetrievedDocument(**docs[0]).score == 0.9

    def test_answer_generation_uses_context(self, rag_agent, mock_vector_store, mock_llm_client):
        """Test that answer generation receives proper context."""
        mock_search_results = [
            {
                "id": "doc1",
                "content": "Authentication uses Bearer tokens.",
                "metadata": {"endpoint": "/auth"},
                "score": 0.9,
            }
        ]
        mock_vector_store.search.return_value = mock_search_results
        mock_llm_client.generate.side_effect = ["variations", "Generated answer"]

        state = create_initial_state("How to authenticate?")
        result = rag_agent.process(state)

        # Check that second LLM call (answer generation) included context
        answer_gen_call = mock_llm_client.generate.call_args_list[1]
        prompt = answer_gen_call.kwargs["prompt"]
        assert "Authentication uses Bearer tokens" in prompt
        assert "How to authenticate?" in prompt

    def test_min_relevance_score_configuration(self):
        """Test that min_relevance_score is configurable."""
        agent1 = RAGAgent(min_relevance_score=0.5)
        agent2 = RAGAgent(min_relevance_score=0.7)

        assert agent1.min_relevance_score == 0.5
        assert agent2.min_relevance_score == 0.7

    def test_top_k_configuration(self):
        """Test that top_k is configurable."""
        agent1 = RAGAgent(top_k=3)
        agent2 = RAGAgent(top_k=10)

        assert agent1.top_k == 3
        assert agent2.top_k == 10
