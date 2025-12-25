"""
Unit tests for agent state and base agent classes.
Run with: pytest tests/test_agents/test_foundation.py -v
"""

import pytest
from datetime import datetime

from src.agents.state import (
    AgentState,
    QueryIntent,
    ConfidenceLevel,
    IntentAnalysis,
    RetrievedDocument,
    SourceCitation,
    AgentMessage,
    AgentError,
    create_initial_state,
    add_to_processing_path,
    set_error,
)
from src.agents.base_agent import (
    BaseAgent,
    PassThroughAgent,
    AgentRegistry,
    get_agent_registry,
    AgentType,
)


class TestQueryIntent:
    """Tests for QueryIntent enum."""

    def test_all_intents_defined(self):
        """Verify all expected intents exist."""
        expected = [
            "general_question",
            "code_generation",
            "endpoint_lookup",
            "schema_explanation",
            "authentication",
            "documentation_gap",
        ]
        actual = [intent.value for intent in QueryIntent]
        assert sorted(actual) == sorted(expected)

    def test_intent_string_conversion(self):
        """Verify intent can be used as string."""
        intent = QueryIntent.CODE_GENERATION
        assert intent.value == "code_generation"
        assert str(intent) == "QueryIntent.CODE_GENERATION"


class TestIntentAnalysis:
    """Tests for IntentAnalysis model."""

    def test_from_confidence_high(self):
        """Test high confidence level assignment."""
        analysis = IntentAnalysis.from_confidence(
            intent=QueryIntent.CODE_GENERATION,
            score=0.95,
        )
        assert analysis.confidence_level == ConfidenceLevel.HIGH
        assert analysis.confidence == 0.95
        assert analysis.primary_intent == QueryIntent.CODE_GENERATION

    def test_from_confidence_medium(self):
        """Test medium confidence level assignment."""
        analysis = IntentAnalysis.from_confidence(
            intent=QueryIntent.GENERAL_QUESTION,
            score=0.65,
        )
        assert analysis.confidence_level == ConfidenceLevel.MEDIUM

    def test_from_confidence_low(self):
        """Test low confidence level assignment."""
        analysis = IntentAnalysis.from_confidence(
            intent=QueryIntent.AUTHENTICATION,
            score=0.3,
        )
        assert analysis.confidence_level == ConfidenceLevel.LOW

    def test_with_keywords(self):
        """Test intent analysis with keywords."""
        analysis = IntentAnalysis.from_confidence(
            intent=QueryIntent.CODE_GENERATION,
            score=0.85,
            keywords=["python", "requests", "POST"],
            requires_code=True,
        )
        assert analysis.keywords == ["python", "requests", "POST"]
        assert analysis.requires_code is True


class TestRetrievedDocument:
    """Tests for RetrievedDocument model."""

    def test_create_document(self):
        """Test creating a retrieved document."""
        doc = RetrievedDocument(
            content="GET /pets returns a list of pets",
            metadata={"path": "/pets", "method": "GET"},
            score=0.87,
            doc_id="doc123",
        )
        assert doc.content == "GET /pets returns a list of pets"
        assert doc.score == 0.87
        assert doc.metadata["path"] == "/pets"

    def test_default_values(self):
        """Test document default values."""
        doc = RetrievedDocument(content="Test content")
        assert doc.score == 0.0
        assert doc.metadata == {}
        assert doc.doc_id == ""


class TestSourceCitation:
    """Tests for SourceCitation model."""

    def test_to_display_string(self):
        """Test citation formatting."""
        citation = SourceCitation(
            endpoint_path="/pets/{id}",
            method="GET",
            description="Get pet by ID",
            relevance_score=0.9,
        )
        display = citation.to_display_string()
        assert "`GET /pets/{id}`" in display
        assert "Get pet by ID" in display

    def test_to_display_string_minimal(self):
        """Test citation with minimal data."""
        citation = SourceCitation(description="General API info")
        display = citation.to_display_string()
        assert display == "General API info"


class TestAgentState:
    """Tests for AgentState and helper functions."""

    def test_create_initial_state(self):
        """Test creating initial state."""
        state = create_initial_state("How do I authenticate?")
        
        assert state["query"] == "How do I authenticate?"
        assert state["response"] == ""
        assert state["retrieved_documents"] == []
        assert state["processing_path"] == []
        assert state["should_continue"] is True
        assert state["error"] is None
        assert "start_time" in state["metadata"]

    def test_create_initial_state_with_messages(self):
        """Test creating state with conversation history."""
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
        ]
        state = create_initial_state("Follow up question", messages=messages)
        
        assert len(state["messages"]) == 2
        assert state["messages"][0]["role"] == "user"

    def test_add_to_processing_path(self):
        """Test adding agents to processing path."""
        state = create_initial_state("Test query")
        
        state = add_to_processing_path(state, "query_analyzer")
        assert state["processing_path"] == ["query_analyzer"]
        assert state["current_agent"] == "query_analyzer"
        
        state = add_to_processing_path(state, "rag_agent")
        assert state["processing_path"] == ["query_analyzer", "rag_agent"]
        assert state["current_agent"] == "rag_agent"

    def test_set_error(self):
        """Test setting error in state."""
        state = create_initial_state("Test query")
        
        state = set_error(
            state=state,
            agent="test_agent",
            error_type="ValueError",
            message="Something went wrong",
            recoverable=False,
        )
        
        assert state["error"] is not None
        assert state["error"]["agent"] == "test_agent"
        assert state["error"]["message"] == "Something went wrong"
        assert state["should_continue"] is False


class TestPassThroughAgent:
    """Tests for PassThroughAgent."""

    def test_pass_through_properties(self):
        """Test pass through agent properties."""
        agent = PassThroughAgent()
        assert agent.name == "pass_through"
        assert agent.agent_type == AgentType.SUPERVISOR

    def test_pass_through_processing(self):
        """Test that pass through returns state unchanged."""
        agent = PassThroughAgent()
        state = create_initial_state("Test query")
        state["response"] = "Existing response"
        
        result = agent(state)
        
        assert result["query"] == "Test query"
        assert result["response"] == "Existing response"
        assert "pass_through" in result["processing_path"]


class TestAgentRegistry:
    """Tests for AgentRegistry."""

    def test_register_and_get(self):
        """Test registering and retrieving agents."""
        registry = AgentRegistry()
        agent = PassThroughAgent()
        
        registry.register(agent)
        
        retrieved = registry.get_by_name("pass_through")
        assert retrieved is agent

    def test_register_duplicate_raises(self):
        """Test that registering duplicate name raises error."""
        registry = AgentRegistry()
        agent1 = PassThroughAgent()
        agent2 = PassThroughAgent()
        
        registry.register(agent1)
        
        with pytest.raises(ValueError, match="already registered"):
            registry.register(agent2)

    def test_get_by_type(self):
        """Test getting agents by type."""
        registry = AgentRegistry()
        agent = PassThroughAgent()
        registry.register(agent)
        
        agents = registry.get_by_type(AgentType.SUPERVISOR)
        assert len(agents) == 1
        assert agents[0] is agent

    def test_list_names(self):
        """Test listing agent names."""
        registry = AgentRegistry()
        registry.register(PassThroughAgent())
        
        names = registry.list_names()
        assert "pass_through" in names

    def test_contains(self):
        """Test checking if agent is registered."""
        registry = AgentRegistry()
        registry.register(PassThroughAgent())
        
        assert "pass_through" in registry
        assert "nonexistent" not in registry


class TestCustomAgent:
    """Tests for creating custom agents."""

    def test_custom_agent_implementation(self):
        """Test implementing a custom agent."""
        
        class TestAgent(BaseAgent):
            @property
            def name(self) -> str:
                return "test_agent"
            
            @property
            def agent_type(self) -> AgentType:
                return AgentType.RAG_AGENT
            
            def process(self, state: AgentState) -> AgentState:
                return {
                    **state,
                    "response": f"Processed: {state['query']}",
                }
        
        agent = TestAgent()
        state = create_initial_state("Hello world")
        
        result = agent(state)
        
        assert result["response"] == "Processed: Hello world"
        assert "test_agent" in result["processing_path"]

    def test_agent_error_handling(self):
        """Test that agent errors are caught and recorded."""
        
        class FailingAgent(BaseAgent):
            @property
            def name(self) -> str:
                return "failing_agent"
            
            @property
            def agent_type(self) -> AgentType:
                return AgentType.RAG_AGENT
            
            def process(self, state: AgentState) -> AgentState:
                raise ValueError("Intentional failure")
        
        agent = FailingAgent()
        state = create_initial_state("Test query")
        
        result = agent(state)
        
        assert result["error"] is not None
        assert result["error"]["error_type"] == "ValueError"
        assert "Intentional failure" in result["error"]["message"]
