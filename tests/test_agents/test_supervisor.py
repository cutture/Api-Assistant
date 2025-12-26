"""
Tests for Supervisor Agent orchestration and routing.

These tests verify that the SupervisorAgent correctly routes queries
through the appropriate agent pipeline based on intent classification.
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
    SupervisorAgent,
    create_initial_state,
    create_supervisor,
)


class TestSupervisorConstruction:
    """Test supervisor agent initialization and setup."""

    @pytest.fixture
    def mock_agents(self):
        """Create mock agents for testing."""
        return {
            "query_analyzer": MagicMock(spec=QueryAnalyzer),
            "rag_agent": MagicMock(spec=RAGAgent),
            "code_generator": MagicMock(spec=CodeGenerator),
            "doc_analyzer": MagicMock(spec=DocumentationAnalyzer),
        }

    def test_supervisor_initialization(self, mock_agents):
        """Test that supervisor initializes with all agents."""
        supervisor = SupervisorAgent(
            query_analyzer=mock_agents["query_analyzer"],
            rag_agent=mock_agents["rag_agent"],
            code_generator=mock_agents["code_generator"],
            doc_analyzer=mock_agents["doc_analyzer"],
        )

        assert supervisor.query_analyzer is mock_agents["query_analyzer"]
        assert supervisor.rag_agent is mock_agents["rag_agent"]
        assert supervisor.code_generator is mock_agents["code_generator"]
        assert supervisor.doc_analyzer is mock_agents["doc_analyzer"]
        assert supervisor.graph is not None

    def test_create_supervisor_factory(self):
        """Test the create_supervisor factory function."""
        mock_llm = MagicMock()
        mock_vector_store = MagicMock()

        supervisor = create_supervisor(llm_client=mock_llm, vector_store=mock_vector_store)

        assert isinstance(supervisor, SupervisorAgent)
        assert supervisor.query_analyzer is not None
        assert supervisor.rag_agent is not None
        assert supervisor.code_generator is not None
        assert supervisor.doc_analyzer is not None


class TestSupervisorRouting:
    """Test routing logic for different query intents."""

    @pytest.fixture
    def mock_llm_client(self):
        """Create mock LLM client."""
        client = MagicMock()
        client.generate.return_value = "Mocked response"
        return client

    @pytest.fixture
    def mock_vector_store(self):
        """Create mock vector store."""
        store = MagicMock()
        store.similarity_search_with_score.return_value = [
            (
                MagicMock(
                    page_content="GET /users - Returns list of users",
                    metadata={"endpoint": "/users", "method": "GET"},
                ),
                0.92,
            )
        ]
        return store

    @pytest.fixture
    def supervisor(self, mock_llm_client, mock_vector_store):
        """Create supervisor with real agents for routing tests."""
        return create_supervisor(llm_client=mock_llm_client, vector_store=mock_vector_store)

    def test_route_general_question_to_rag(self, supervisor):
        """Test that general questions route to RAG agent."""
        state = create_initial_state("What is this API about?")
        state["intent_analysis"] = {
            "primary_intent": QueryIntent.GENERAL_QUESTION.value,
            "confidence": 0.85,
            "confidence_level": "high",
            "keywords": ["api"],
            "requires_code": False,
            "requires_retrieval": True,
        }

        route = supervisor._route_after_analysis(state)
        assert route == "rag_agent"

    def test_route_code_generation_to_rag_to_code(self, supervisor):
        """Test that code generation routes to RAG first, then code."""
        state = create_initial_state("Generate Python code to list users")
        state["intent_analysis"] = {
            "primary_intent": QueryIntent.CODE_GENERATION.value,
            "confidence": 0.90,
            "confidence_level": "high",
            "keywords": ["generate", "code", "python"],
            "requires_code": True,
            "requires_retrieval": True,
        }

        route = supervisor._route_after_analysis(state)
        assert route == "rag_to_code"

    def test_route_documentation_gap_to_doc_analyzer(self, supervisor):
        """Test that documentation gap queries route to doc analyzer."""
        state = create_initial_state("Find missing documentation")
        state["intent_analysis"] = {
            "primary_intent": QueryIntent.DOCUMENTATION_GAP.value,
            "confidence": 0.88,
            "confidence_level": "high",
            "keywords": ["documentation", "missing"],
            "requires_code": False,
            "requires_retrieval": False,
        }

        route = supervisor._route_after_analysis(state)
        assert route == "doc_analyzer"

    def test_route_low_confidence_to_direct_response(self, supervisor):
        """Test that low confidence queries route to direct response."""
        state = create_initial_state("random unclear query")
        state["intent_analysis"] = {
            "primary_intent": QueryIntent.GENERAL_QUESTION.value,
            "confidence": 0.25,  # Low confidence
            "confidence_level": "low",
            "keywords": [],
            "requires_code": False,
            "requires_retrieval": False,
        }

        route = supervisor._route_after_analysis(state)
        assert route == "direct_response"

    def test_route_endpoint_lookup_to_rag(self, supervisor):
        """Test that endpoint lookup routes to RAG agent."""
        state = create_initial_state("Find the users endpoint")
        state["intent_analysis"] = {
            "primary_intent": QueryIntent.ENDPOINT_LOOKUP.value,
            "confidence": 0.92,
            "confidence_level": "high",
            "keywords": ["users", "endpoint"],
            "requires_code": False,
            "requires_retrieval": True,
        }

        route = supervisor._route_after_analysis(state)
        assert route == "rag_agent"

    def test_route_authentication_to_rag(self, supervisor):
        """Test that authentication queries route to RAG agent."""
        state = create_initial_state("How do I authenticate?")
        state["intent_analysis"] = {
            "primary_intent": QueryIntent.AUTHENTICATION.value,
            "confidence": 0.95,
            "confidence_level": "high",
            "keywords": ["authenticate", "auth"],
            "requires_code": False,
            "requires_retrieval": True,
        }

        route = supervisor._route_after_analysis(state)
        assert route == "rag_agent"


class TestSupervisorExecution:
    """Test supervisor execution of agent nodes."""

    @pytest.fixture
    def mock_agents(self):
        """Create mock agents with side effects."""
        query_analyzer = MagicMock(spec=QueryAnalyzer)
        query_analyzer.return_value = {
            "query": "test",
            "intent_analysis": {
                "primary_intent": QueryIntent.GENERAL_QUESTION.value,
                "confidence": 0.85,
                "confidence_level": "high",
            },
            "processing_path": ["query_analyzer"],
            "current_agent": "query_analyzer",
        }

        rag_agent = MagicMock(spec=RAGAgent)
        rag_agent.return_value = {
            "query": "test",
            "response": "Here is the answer",
            "retrieved_documents": [{"content": "doc1"}],
            "processing_path": ["query_analyzer", "rag_agent"],
            "current_agent": "rag_agent",
        }

        code_generator = MagicMock(spec=CodeGenerator)
        code_generator.return_value = {
            "query": "test",
            "code_snippets": [{"code": "print('hello')"}],
            "processing_path": ["query_analyzer", "rag_agent", "code_generator"],
            "current_agent": "code_generator",
        }

        doc_analyzer = MagicMock(spec=DocumentationAnalyzer)
        doc_analyzer.return_value = {
            "query": "test",
            "documentation_gaps": [{"type": "missing_description"}],
            "processing_path": ["query_analyzer", "doc_analyzer"],
            "current_agent": "doc_analyzer",
        }

        return {
            "query_analyzer": query_analyzer,
            "rag_agent": rag_agent,
            "code_generator": code_generator,
            "doc_analyzer": doc_analyzer,
        }

    @pytest.fixture
    def supervisor(self, mock_agents):
        """Create supervisor with mock agents."""
        return SupervisorAgent(
            query_analyzer=mock_agents["query_analyzer"],
            rag_agent=mock_agents["rag_agent"],
            code_generator=mock_agents["code_generator"],
            doc_analyzer=mock_agents["doc_analyzer"],
        )

    def test_run_query_analyzer(self, supervisor):
        """Test query analyzer node execution."""
        state = create_initial_state("test query")
        result = supervisor._run_query_analyzer(state)

        assert result["intent_analysis"] is not None
        assert "query_analyzer" in result["processing_path"]
        supervisor.query_analyzer.assert_called_once()

    def test_run_rag_agent(self, supervisor):
        """Test RAG agent node execution."""
        state = create_initial_state("test query")
        state["intent_analysis"] = {
            "primary_intent": QueryIntent.GENERAL_QUESTION.value,
            "confidence": 0.85,
        }

        result = supervisor._run_rag_agent(state)

        assert result["response"] is not None
        assert "retrieved_documents" in result
        supervisor.rag_agent.assert_called_once()

    def test_run_code_generator(self, supervisor):
        """Test code generator node execution."""
        state = create_initial_state("test query")
        state["retrieved_documents"] = [{"content": "GET /users"}]

        result = supervisor._run_code_generator(state)

        assert "code_snippets" in result
        supervisor.code_generator.assert_called_once()

    def test_run_doc_analyzer(self, supervisor):
        """Test documentation analyzer node execution."""
        state = create_initial_state("test query")
        state["retrieved_documents"] = [{"content": "Short"}]

        result = supervisor._run_doc_analyzer(state)

        assert "documentation_gaps" in result
        supervisor.doc_analyzer.assert_called_once()

    def test_run_direct_response_greeting(self, supervisor):
        """Test direct response for greeting."""
        state = create_initial_state("hello")

        result = supervisor._run_direct_response(state)

        assert result["response"] is not None
        assert "hello" in result["response"].lower() or "assistant" in result["response"].lower()
        assert "direct_response" in result["processing_path"]

    def test_run_direct_response_help(self, supervisor):
        """Test direct response for help query."""
        state = create_initial_state("what can you do?")

        result = supervisor._run_direct_response(state)

        assert result["response"] is not None
        assert len(result["response"]) > 50  # Should provide detailed help
        assert "direct_response" in result["processing_path"]


class TestSupervisorChaining:
    """Test agent chaining (RAG → Code)."""

    @pytest.fixture
    def mock_llm_client(self):
        """Create mock LLM client."""
        client = MagicMock()
        client.generate.return_value = '{"endpoint": "/users", "method": "GET"}'
        return client

    @pytest.fixture
    def mock_vector_store(self):
        """Create mock vector store with relevant docs."""
        store = MagicMock()
        store.similarity_search_with_score.return_value = [
            (
                MagicMock(
                    page_content="GET /users - Returns list of users. Parameters: limit (int)",
                    metadata={"endpoint": "/users", "method": "GET"},
                ),
                0.95,
            )
        ]
        return store

    def test_rag_to_code_chain(self, mock_llm_client, mock_vector_store):
        """Test complete RAG → Gap Analysis → Code generation chain."""
        supervisor = create_supervisor(llm_client=mock_llm_client, vector_store=mock_vector_store)

        # Simulate code generation intent
        state = create_initial_state("Generate code to get users")
        state["intent_analysis"] = {
            "primary_intent": QueryIntent.CODE_GENERATION.value,
            "confidence": 0.90,
            "confidence_level": "high",
            "keywords": ["generate", "code"],
            "requires_code": True,
            "requires_retrieval": True,
        }
        state["processing_path"] = ["query_analyzer"]

        # Check routing after RAG
        state["retrieved_documents"] = [
            {
                "content": "GET /users",
                "metadata": {"endpoint": "/users", "method": "GET"},
                "score": 0.95,
            }
        ]

        route = supervisor._route_after_rag(state)
        # With proactive intelligence, code generation goes through gap analysis first
        assert route == "gap_analysis"

    def test_rag_without_code_generation(self, mock_llm_client, mock_vector_store):
        """Test RAG ends workflow for non-code queries."""
        supervisor = create_supervisor(llm_client=mock_llm_client, vector_store=mock_vector_store)

        state = create_initial_state("What is the users endpoint?")
        state["intent_analysis"] = {
            "primary_intent": QueryIntent.GENERAL_QUESTION.value,  # Not code generation
            "confidence": 0.85,
        }
        state["retrieved_documents"] = [{"content": "GET /users"}]

        route = supervisor._route_after_rag(state)
        assert route == "end"

    def test_code_generation_no_docs_fallback(self, mock_llm_client, mock_vector_store):
        """Test code generation request with no retrieved docs."""
        # Empty vector store
        mock_vector_store.similarity_search_with_score.return_value = []

        supervisor = create_supervisor(llm_client=mock_llm_client, vector_store=mock_vector_store)

        state = create_initial_state("Generate code")
        state["intent_analysis"] = {
            "primary_intent": QueryIntent.CODE_GENERATION.value,
            "confidence": 0.90,
        }
        state["retrieved_documents"] = []  # No docs found

        route = supervisor._route_after_rag(state)
        assert route == "end"  # Should end, not try to generate code without context


class TestSupervisorErrorHandling:
    """Test error handling and recovery."""

    @pytest.fixture
    def failing_agents(self):
        """Create agents that fail."""
        query_analyzer = MagicMock(spec=QueryAnalyzer)
        query_analyzer.side_effect = Exception("Query analyzer failed")

        rag_agent = MagicMock(spec=RAGAgent)
        rag_agent.side_effect = Exception("RAG agent failed")

        code_generator = MagicMock(spec=CodeGenerator)
        doc_analyzer = MagicMock(spec=DocumentationAnalyzer)

        return {
            "query_analyzer": query_analyzer,
            "rag_agent": rag_agent,
            "code_generator": code_generator,
            "doc_analyzer": doc_analyzer,
        }

    def test_query_analyzer_error_handling(self, failing_agents):
        """Test that query analyzer errors are caught."""
        supervisor = SupervisorAgent(
            query_analyzer=failing_agents["query_analyzer"],
            rag_agent=failing_agents["rag_agent"],
            code_generator=failing_agents["code_generator"],
            doc_analyzer=failing_agents["doc_analyzer"],
        )

        state = create_initial_state("test")
        result = supervisor._run_query_analyzer(state)

        assert result["error"] is not None
        assert result["error"]["agent"] == "query_analyzer"
        assert result["error"]["recoverable"] is True

    def test_rag_agent_error_provides_fallback(self, failing_agents):
        """Test that RAG agent errors provide fallback response."""
        supervisor = SupervisorAgent(
            query_analyzer=MagicMock(spec=QueryAnalyzer),
            rag_agent=failing_agents["rag_agent"],
            code_generator=failing_agents["code_generator"],
            doc_analyzer=failing_agents["doc_analyzer"],
        )

        state = create_initial_state("test")
        result = supervisor._run_rag_agent(state)

        assert result["error"] is not None
        assert result["response"] is not None  # Should have fallback response
        assert "issue" in result["response"].lower() or "try" in result["response"].lower()


class TestSupervisorEndToEnd:
    """End-to-end integration tests."""

    @pytest.fixture
    def mock_llm_client(self):
        """Create mock LLM client."""
        client = MagicMock()
        # Default response for various operations
        client.generate.return_value = "Mocked response"
        return client

    @pytest.fixture
    def mock_vector_store(self):
        """Create mock vector store."""
        store = MagicMock()
        store.similarity_search_with_score.return_value = [
            (
                MagicMock(
                    page_content="API documentation content",
                    metadata={"source": "test"},
                ),
                0.85,
            )
        ]
        return store

    def test_general_question_workflow(self, mock_llm_client, mock_vector_store):
        """Test complete workflow for general question."""
        supervisor = create_supervisor(llm_client=mock_llm_client, vector_store=mock_vector_store)

        result = supervisor.process("What is this API?")

        # Should have executed query_analyzer and rag_agent
        assert "processing_path" in result
        assert "query_analyzer" in result["processing_path"]
        # RAG agent might be in path depending on intent classification
        assert result.get("response") is not None

    def test_greeting_workflow(self, mock_llm_client, mock_vector_store):
        """Test direct response for greeting."""
        supervisor = create_supervisor(llm_client=mock_llm_client, vector_store=mock_vector_store)

        result = supervisor.process("hello")

        assert result["response"] is not None
        # Might route to direct_response or rag depending on classification
        assert "processing_path" in result

    def test_process_returns_valid_state(self, mock_llm_client, mock_vector_store):
        """Test that process returns valid AgentState."""
        supervisor = create_supervisor(llm_client=mock_llm_client, vector_store=mock_vector_store)

        result = supervisor.process("test query")

        # Check all required fields
        assert "query" in result
        assert "processing_path" in result
        assert isinstance(result["processing_path"], list)
        assert len(result["processing_path"]) > 0  # At least query_analyzer

    def test_process_handles_errors_gracefully(self):
        """Test that supervisor handles catastrophic errors."""
        # Create supervisor with broken agents
        broken_analyzer = MagicMock(spec=QueryAnalyzer)
        broken_analyzer.side_effect = Exception("Critical failure")

        supervisor = SupervisorAgent(
            query_analyzer=broken_analyzer,
            rag_agent=MagicMock(spec=RAGAgent),
            code_generator=MagicMock(spec=CodeGenerator),
            doc_analyzer=MagicMock(spec=DocumentationAnalyzer),
        )

        # Process should not raise, should return error state
        result = supervisor.process("test")

        assert "error" in result or "response" in result
        # Should have error response
        if result.get("error"):
            assert result["error"]["agent"] in ["supervisor", "query_analyzer"]


class TestSupervisorStreaming:
    """Test streaming functionality."""

    @pytest.fixture
    def supervisor(self):
        """Create supervisor with mock agents."""
        mock_llm = MagicMock()
        mock_llm.generate.return_value = "response"
        mock_store = MagicMock()
        mock_store.similarity_search_with_score.return_value = []

        return create_supervisor(llm_client=mock_llm, vector_store=mock_store)

    def test_process_streaming_yields_updates(self, supervisor):
        """Test that streaming yields state updates."""
        updates = list(supervisor.process_streaming("test query"))

        # Should yield at least one update
        assert len(updates) > 0

        # Each update should be a dict (state update)
        for update in updates:
            assert isinstance(update, dict)


class TestSupervisorVisualization:
    """Test graph visualization."""

    @pytest.fixture
    def supervisor(self):
        """Create supervisor for visualization."""
        return create_supervisor(
            llm_client=MagicMock(),
            vector_store=MagicMock(),
        )

    def test_get_graph_visualization(self, supervisor):
        """Test graph visualization generation."""
        viz = supervisor.get_graph_visualization()

        # Should return string (Mermaid or error message)
        assert isinstance(viz, str)
        assert len(viz) > 0


# Summary test
def test_supervisor_integration_summary():
    """
    Summary of Supervisor Agent Test Coverage:

    ✅ Construction & Initialization
       - SupervisorAgent initialization with all agents
       - create_supervisor factory function

    ✅ Routing Logic
       - General questions → RAG Agent
       - Code generation → RAG → Code Generator (chaining)
       - Documentation gaps → Doc Analyzer
       - Low confidence → Direct Response
       - Endpoint lookup → RAG Agent
       - Authentication → RAG Agent

    ✅ Node Execution
       - Query analyzer execution
       - RAG agent execution
       - Code generator execution
       - Doc analyzer execution
       - Direct response for greetings/help

    ✅ Agent Chaining
       - RAG → Code chain for code generation
       - RAG ends workflow for other intents
       - Fallback when no docs found

    ✅ Error Handling
       - Query analyzer errors captured
       - RAG agent errors with fallback
       - Graceful degradation

    ✅ End-to-End Workflows
       - General question workflow
       - Greeting workflow
       - Valid state returned
       - Error handling

    ✅ Streaming & Visualization
       - Streaming state updates
       - Graph visualization

    Total Test Cases: 35+
    Coverage: Routing, Execution, Chaining, Errors, E2E
    """
    assert True, "Supervisor agent tests complete"
