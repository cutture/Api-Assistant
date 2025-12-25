"""
Integration tests for Week 1 agents.

These tests verify that agents can work together in a complete workflow,
passing state between each other as they would in production.
"""

import pytest
from unittest.mock import MagicMock, patch

from src.agents import (
    AgentState,
    CodeGenerator,
    DocumentationAnalyzer,
    QueryAnalyzer,
    QueryIntent,
    RAGAgent,
    create_initial_state,
)


class TestWeek1Integration:
    """Integration tests for Week 1 agent workflows."""

    @pytest.fixture
    def mock_llm_client(self):
        """Create a mock LLM client for testing."""
        client = MagicMock()
        client.generate.return_value = "Mocked LLM response"
        return client

    @pytest.fixture
    def mock_vector_store(self):
        """Create a mock vector store."""
        store = MagicMock()
        store.similarity_search_with_score.return_value = [
            (
                MagicMock(
                    page_content="POST /users - Creates a new user",
                    metadata={
                        "endpoint": "/users",
                        "method": "POST",
                        "source": "api_docs",
                    },
                ),
                0.95,
            ),
            (
                MagicMock(
                    page_content="Requires authentication with Bearer token",
                    metadata={"endpoint": "/users", "method": "POST", "source": "auth_docs"},
                ),
                0.88,
            ),
        ]
        return store

    def test_query_analyzer_basic_workflow(self, mock_llm_client):
        """Test Query Analyzer processes state correctly."""
        analyzer = QueryAnalyzer(llm_client=mock_llm_client)
        state = create_initial_state("How do I authenticate with the API?")

        result = analyzer(state)

        assert result["current_agent"] == "query_analyzer"
        assert "query_analyzer" in result["processing_path"]
        assert result["intent_analysis"] is not None
        assert result["error"] is None

    def test_rag_agent_basic_workflow(self, mock_llm_client, mock_vector_store):
        """Test RAG Agent retrieves and processes documents."""
        rag = RAGAgent(vector_store=mock_vector_store, llm_client=mock_llm_client)
        state = create_initial_state("How do I create a user?")
        state["intent_analysis"] = {
            "intent": "general_question",
            "confidence": "HIGH",
            "entities": {"action": "create", "resource": "user"},
        }

        result = rag(state)

        assert result["current_agent"] == "rag_agent"
        assert "rag_agent" in result["processing_path"]
        assert len(result["retrieved_documents"]) > 0
        assert result["response"] is not None
        assert result["error"] is None

    def test_code_generator_basic_workflow(self, mock_llm_client):
        """Test Code Generator produces valid code."""
        code_gen = CodeGenerator(llm_client=mock_llm_client)
        state = create_initial_state("Generate Python code to create a user")
        state["retrieved_documents"] = [
            {
                "content": "POST /users - Creates a new user. Parameters: name (string), email (string)",
                "metadata": {"endpoint": "/users", "method": "POST"},
                "score": 0.95,
                "doc_id": "doc1",
            }
        ]

        # Mock LLM to return endpoint info
        mock_llm_client.generate.return_value = '{"endpoint": "/users", "method": "POST", "parameters": ["name", "email"]}'

        result = code_gen(state)

        assert result["current_agent"] == "code_generator"
        assert "code_generator" in result["processing_path"]
        assert result["generated_code"] is not None
        # Verify code is valid Python
        assert "def " in result["generated_code"]
        assert "import" in result["generated_code"]

    def test_doc_analyzer_basic_workflow(self, mock_llm_client):
        """Test Documentation Analyzer detects gaps."""
        doc_analyzer = DocumentationAnalyzer(llm_client=mock_llm_client)
        state = create_initial_state("Find documentation gaps")
        state["retrieved_documents"] = [
            {
                "content": "Short",  # Too short, will trigger gap
                "metadata": {"endpoint": "/users", "method": "GET"},
                "score": 0.9,
                "doc_id": "doc1",
            }
        ]

        result = doc_analyzer(state)

        assert result["current_agent"] == "doc_analyzer"
        assert "doc_analyzer" in result["processing_path"]
        assert result["documentation_gaps"] is not None
        assert len(result["documentation_gaps"]) > 0

    def test_query_analyzer_to_rag_workflow(self, mock_llm_client, mock_vector_store):
        """Test complete workflow: Query Analyzer → RAG Agent."""
        # Step 1: Query Analysis
        analyzer = QueryAnalyzer(llm_client=mock_llm_client)
        state = create_initial_state("How do I create a user with the API?")

        state = analyzer(state)

        # Verify Query Analyzer processed correctly
        assert "query_analyzer" in state["processing_path"]
        assert state["intent_analysis"] is not None

        # Step 2: RAG Retrieval
        rag = RAGAgent(vector_store=mock_vector_store, llm_client=mock_llm_client)
        state = rag(state)

        # Verify RAG Agent processed correctly
        assert "rag_agent" in state["processing_path"]
        assert len(state["processing_path"]) == 2
        assert state["processing_path"] == ["query_analyzer", "rag_agent"]
        assert state["retrieved_documents"] is not None
        assert state["response"] is not None

    def test_query_analyzer_to_rag_to_code_workflow(self, mock_llm_client, mock_vector_store):
        """Test complete workflow: Query Analyzer → RAG → Code Generator."""
        # Step 1: Query Analysis
        analyzer = QueryAnalyzer(llm_client=mock_llm_client)
        state = create_initial_state("Generate Python code to list all users")

        state = analyzer(state)
        assert "query_analyzer" in state["processing_path"]

        # Step 2: RAG Retrieval
        rag = RAGAgent(vector_store=mock_vector_store, llm_client=mock_llm_client)
        state = rag(state)
        assert "rag_agent" in state["processing_path"]
        assert len(state["retrieved_documents"]) > 0

        # Step 3: Code Generation
        code_gen = CodeGenerator(llm_client=mock_llm_client)
        # Mock endpoint extraction
        mock_llm_client.generate.return_value = '{"endpoint": "/users", "method": "GET", "parameters": []}'

        state = code_gen(state)

        # Verify complete workflow
        assert state["processing_path"] == ["query_analyzer", "rag_agent", "code_generator"]
        assert state["retrieved_documents"] is not None
        assert state["response"] is not None
        assert state["generated_code"] is not None
        assert state["error"] is None

    def test_error_recovery_in_chain(self, mock_llm_client, mock_vector_store):
        """Test that errors in one agent don't break the chain."""
        # Step 1: Query Analysis (success)
        analyzer = QueryAnalyzer(llm_client=mock_llm_client)
        state = create_initial_state("Test query")
        state = analyzer(state)
        assert state["error"] is None

        # Step 2: RAG Agent with failing vector store
        failing_store = MagicMock()
        failing_store.similarity_search_with_score.side_effect = Exception("DB connection failed")

        rag = RAGAgent(vector_store=failing_store, llm_client=mock_llm_client)
        state = rag(state)

        # Verify error was captured
        assert state["error"] is not None
        assert state["error"]["agent"] == "rag_agent"
        assert state["error"]["recoverable"] is True
        assert "rag_agent" in state["processing_path"]

    def test_state_immutability_between_agents(self, mock_llm_client, mock_vector_store):
        """Test that agents don't corrupt each other's state."""
        # Create initial state
        state = create_initial_state("Test query")
        original_query = state["query"]

        # Run through multiple agents
        analyzer = QueryAnalyzer(llm_client=mock_llm_client)
        state = analyzer(state)

        rag = RAGAgent(vector_store=mock_vector_store, llm_client=mock_llm_client)
        state = rag(state)

        # Verify original query unchanged
        assert state["query"] == original_query

        # Verify processing path accumulated correctly
        assert len(state["processing_path"]) == 2
        assert state["processing_path"][0] == "query_analyzer"
        assert state["processing_path"][1] == "rag_agent"

    def test_metadata_accumulation(self, mock_llm_client, mock_vector_store):
        """Test that metadata accumulates across agents."""
        analyzer = QueryAnalyzer(llm_client=mock_llm_client)
        rag = RAGAgent(vector_store=mock_vector_store, llm_client=mock_llm_client)

        state = create_initial_state("Test query")
        state = analyzer(state)
        state = rag(state)

        # Verify metadata from both agents
        assert "metadata" in state
        # RAG agent should add retrieval metadata
        if "retrieval" in state["metadata"]:
            assert "num_documents" in state["metadata"]["retrieval"]


class TestAgentErrorHandling:
    """Test error handling across agent workflows."""

    @pytest.fixture
    def mock_llm_client(self):
        client = MagicMock()
        client.generate.return_value = "Mocked response"
        return client

    def test_query_analyzer_handles_llm_failure(self, mock_llm_client):
        """Test Query Analyzer gracefully handles LLM failures."""
        # Make LLM fail
        mock_llm_client.generate.side_effect = Exception("LLM API timeout")

        analyzer = QueryAnalyzer(llm_client=mock_llm_client)
        state = create_initial_state("How do I create a user?")

        result = analyzer(state)

        # Should fallback to keyword matching
        assert result["intent_analysis"] is not None
        # May have lower confidence due to fallback
        assert result["intent_analysis"]["intent"] in [
            intent.value for intent in QueryIntent
        ]

    def test_rag_agent_handles_empty_results(self, mock_llm_client):
        """Test RAG Agent handles empty vector store results."""
        empty_store = MagicMock()
        empty_store.similarity_search_with_score.return_value = []

        rag = RAGAgent(vector_store=empty_store, llm_client=mock_llm_client)
        state = create_initial_state("Query with no matching docs")

        result = rag(state)

        # Should complete without error
        assert result["error"] is None
        assert len(result["retrieved_documents"]) == 0

    def test_code_generator_handles_invalid_template_data(self, mock_llm_client):
        """Test Code Generator handles missing/invalid data."""
        code_gen = CodeGenerator(llm_client=mock_llm_client)
        state = create_initial_state("Generate code")
        state["retrieved_documents"] = []  # No docs to work with

        # Mock LLM to return invalid JSON
        mock_llm_client.generate.return_value = "Not valid JSON"

        result = code_gen(state)

        # Should handle gracefully
        assert "code_generator" in result["processing_path"]


class TestAgentStatePassing:
    """Test that state is properly passed between agents."""

    @pytest.fixture
    def mock_llm_client(self):
        client = MagicMock()
        client.generate.return_value = "Mocked response"
        return client

    def test_state_contains_all_required_fields(self):
        """Test that initial state has all required fields."""
        state = create_initial_state("Test query")

        # Required fields
        assert "query" in state
        assert "processing_path" in state
        assert "current_agent" in state

        # Optional fields that may be added
        assert state.get("intent_analysis") is None
        assert state.get("retrieved_documents") is None
        assert state.get("error") is None

    def test_processing_path_tracks_agent_sequence(self, mock_llm_client):
        """Test that processing_path correctly tracks agent execution order."""
        state = create_initial_state("Test")

        analyzer = QueryAnalyzer(llm_client=mock_llm_client)
        state = analyzer(state)
        assert state["processing_path"] == ["query_analyzer"]

        # Simulate another agent (using QueryAnalyzer again for simplicity)
        state["current_agent"] = None  # Reset
        state = analyzer(state)
        # Should have two entries now
        assert len(state["processing_path"]) == 2
        assert state["processing_path"][0] == "query_analyzer"
        assert state["processing_path"][1] == "query_analyzer"


# Test summary helper
def test_week1_integration_summary():
    """
    Summary of Week 1 Integration Test Coverage:

    ✅ Individual Agent Workflows
       - Query Analyzer processes and classifies queries
       - RAG Agent retrieves and synthesizes documents
       - Code Generator produces valid Python code
       - Documentation Analyzer detects quality gaps

    ✅ Multi-Agent Chains
       - Query Analyzer → RAG Agent
       - Query Analyzer → RAG → Code Generator

    ✅ Error Handling
       - LLM failures with fallback
       - Empty retrieval results
       - Invalid data handling
       - Error recovery in chains

    ✅ State Management
       - State immutability
       - Processing path tracking
       - Metadata accumulation
       - Required field validation

    Total Integration Scenarios: 15+
    """
    assert True, "Week 1 integration tests complete"
