"""
Unit tests for QueryAnalyzer agent.
"""

import json
from unittest.mock import MagicMock, Mock, patch

import pytest

from src.agents.query_analyzer import QueryAnalyzer
from src.agents.state import (
    AgentState,
    AgentType,
    IntentAnalysis,
    QueryIntent,
    create_initial_state,
)
from src.core.llm_client import LLMClient


class TestQueryAnalyzer:
    """Test suite for QueryAnalyzer agent."""

    @pytest.fixture
    def mock_llm_client(self):
        """Create a mock LLM client."""
        return Mock(spec=LLMClient)

    @pytest.fixture
    def analyzer(self, mock_llm_client):
        """Create QueryAnalyzer with mock LLM client."""
        return QueryAnalyzer(llm_client=mock_llm_client)

    def test_agent_properties(self, analyzer):
        """Test agent properties are correct."""
        assert analyzer.name == "query_analyzer"
        assert analyzer.agent_type == AgentType.QUERY_ANALYZER
        assert "intent" in analyzer.description.lower()

    def test_process_with_empty_query(self, analyzer):
        """Test processing with empty query returns error."""
        state = create_initial_state("")

        result = analyzer.process(state)

        assert result.get("error") is not None
        assert result["error"]["agent"] == "query_analyzer"
        assert result["error"]["error_type"] == "missing_input"
        assert result["should_continue"] is False

    def test_process_code_generation_intent(self, analyzer, mock_llm_client):
        """Test classification of code generation query."""
        # Mock LLM response
        llm_response = json.dumps({
            "primary_intent": "code_generation",
            "confidence": 0.95,
            "secondary_intents": [],
            "keywords": ["generate", "python", "code", "endpoint"],
            "requires_code": True,
            "requires_retrieval": True,
        })
        mock_llm_client.generate.return_value = llm_response

        state = create_initial_state("Generate Python code to call the /users endpoint")
        result = analyzer.process(state)

        # Verify LLM was called correctly
        mock_llm_client.generate.assert_called_once()
        call_args = mock_llm_client.generate.call_args
        assert "Generate Python code" in call_args.kwargs["prompt"]
        assert call_args.kwargs["temperature"] == 0.3

        # Verify intent analysis
        assert result.get("intent_analysis") is not None
        intent = IntentAnalysis(**result["intent_analysis"])
        assert intent.primary_intent == QueryIntent.CODE_GENERATION
        assert intent.confidence == 0.95
        assert intent.requires_code is True
        assert "generate" in intent.keywords

        # Verify routing
        assert result.get("next_agent") == "code_generator"

    def test_process_authentication_intent(self, analyzer, mock_llm_client):
        """Test classification of authentication query."""
        llm_response = json.dumps({
            "primary_intent": "authentication",
            "confidence": 0.9,
            "secondary_intents": ["general_question"],
            "keywords": ["authenticate", "api", "key"],
            "requires_code": False,
            "requires_retrieval": True,
        })
        mock_llm_client.generate.return_value = llm_response

        state = create_initial_state("How do I authenticate with the API?")
        result = analyzer.process(state)

        intent = IntentAnalysis(**result["intent_analysis"])
        assert intent.primary_intent == QueryIntent.AUTHENTICATION
        assert intent.confidence == 0.9
        assert QueryIntent.GENERAL_QUESTION in intent.secondary_intents
        assert result.get("next_agent") == "rag_agent"

    def test_process_endpoint_lookup_intent(self, analyzer, mock_llm_client):
        """Test classification of endpoint lookup query."""
        llm_response = json.dumps({
            "primary_intent": "endpoint_lookup",
            "confidence": 0.85,
            "secondary_intents": [],
            "keywords": ["endpoint", "create", "user"],
            "requires_code": False,
            "requires_retrieval": True,
        })
        mock_llm_client.generate.return_value = llm_response

        state = create_initial_state("Which endpoint creates a new user?")
        result = analyzer.process(state)

        intent = IntentAnalysis(**result["intent_analysis"])
        assert intent.primary_intent == QueryIntent.ENDPOINT_LOOKUP
        assert result.get("next_agent") == "rag_agent"

    def test_process_schema_explanation_intent(self, analyzer, mock_llm_client):
        """Test classification of schema explanation query."""
        llm_response = json.dumps({
            "primary_intent": "schema_explanation",
            "confidence": 0.8,
            "secondary_intents": [],
            "keywords": ["fields", "user", "object"],
            "requires_code": False,
            "requires_retrieval": True,
        })
        mock_llm_client.generate.return_value = llm_response

        state = create_initial_state("What fields does the User object have?")
        result = analyzer.process(state)

        intent = IntentAnalysis(**result["intent_analysis"])
        assert intent.primary_intent == QueryIntent.SCHEMA_EXPLANATION
        assert result.get("next_agent") == "rag_agent"

    def test_process_documentation_gap_intent(self, analyzer, mock_llm_client):
        """Test classification of documentation gap query."""
        llm_response = json.dumps({
            "primary_intent": "documentation_gap",
            "confidence": 0.92,
            "secondary_intents": [],
            "keywords": ["missing", "documentation", "undocumented"],
            "requires_code": False,
            "requires_retrieval": True,
        })
        mock_llm_client.generate.return_value = llm_response

        state = create_initial_state("Find undocumented endpoints in the API")
        result = analyzer.process(state)

        intent = IntentAnalysis(**result["intent_analysis"])
        assert intent.primary_intent == QueryIntent.DOCUMENTATION_GAP
        assert result.get("next_agent") == "rag_agent"  # Routes to RAG now

    def test_process_general_question_intent(self, analyzer, mock_llm_client):
        """Test classification of general question."""
        llm_response = json.dumps({
            "primary_intent": "general_question",
            "confidence": 0.75,
            "secondary_intents": [],
            "keywords": ["api", "available", "endpoints"],
            "requires_code": False,
            "requires_retrieval": True,
        })
        mock_llm_client.generate.return_value = llm_response

        state = create_initial_state("What endpoints are available?")
        result = analyzer.process(state)

        intent = IntentAnalysis(**result["intent_analysis"])
        assert intent.primary_intent == QueryIntent.GENERAL_QUESTION
        assert result.get("next_agent") == "rag_agent"

    def test_confidence_level_mapping(self, analyzer, mock_llm_client):
        """Test that confidence scores map to correct levels."""
        test_cases = [
            (0.95, "high"),
            (0.85, "high"),
            (0.75, "medium"),
            (0.65, "medium"),
            (0.45, "low"),
            (0.3, "low"),
        ]

        for confidence, expected_level in test_cases:
            llm_response = json.dumps({
                "primary_intent": "general_question",
                "confidence": confidence,
                "secondary_intents": [],
                "keywords": ["test"],
                "requires_code": False,
                "requires_retrieval": True,
            })
            mock_llm_client.generate.return_value = llm_response

            state = create_initial_state("test query")
            result = analyzer.process(state)

            intent = IntentAnalysis(**result["intent_analysis"])
            assert intent.confidence_level.value == expected_level

    def test_fallback_classification_code_generation(self, analyzer, mock_llm_client):
        """Test fallback classification for code generation queries."""
        # Simulate LLM failure
        mock_llm_client.generate.return_value = "Invalid JSON response"

        state = create_initial_state("Generate Python code for the API")
        result = analyzer.process(state)

        # Should fall back to keyword matching
        intent = IntentAnalysis(**result["intent_analysis"])
        assert intent.primary_intent == QueryIntent.CODE_GENERATION
        assert intent.requires_code is True
        assert 0.5 <= intent.confidence <= 0.7  # Fallback confidence range

    def test_fallback_classification_authentication(self, analyzer, mock_llm_client):
        """Test fallback classification for authentication queries."""
        mock_llm_client.generate.return_value = "Not valid JSON"

        state = create_initial_state("How do I get an API key for authentication?")
        result = analyzer.process(state)

        intent = IntentAnalysis(**result["intent_analysis"])
        assert intent.primary_intent == QueryIntent.AUTHENTICATION
        assert 0.5 <= intent.confidence <= 0.7

    def test_fallback_classification_endpoint_lookup(self, analyzer, mock_llm_client):
        """Test fallback classification for endpoint lookup."""
        mock_llm_client.generate.return_value = "{invalid json"

        state = create_initial_state("Which endpoint should I use to delete a user?")
        result = analyzer.process(state)

        intent = IntentAnalysis(**result["intent_analysis"])
        assert intent.primary_intent == QueryIntent.ENDPOINT_LOOKUP
        assert 0.5 <= intent.confidence <= 0.7

    def test_fallback_classification_default(self, analyzer, mock_llm_client):
        """Test fallback classification with no keyword matches."""
        mock_llm_client.generate.return_value = "Bad response"

        state = create_initial_state("Tell me about it")
        result = analyzer.process(state)

        intent = IntentAnalysis(**result["intent_analysis"])
        assert intent.primary_intent == QueryIntent.GENERAL_QUESTION
        assert intent.confidence == 0.5

    def test_llm_response_with_extra_text(self, analyzer, mock_llm_client):
        """Test parsing LLM response that includes extra text around JSON."""
        llm_response = """Here's the classification:
        {
            "primary_intent": "code_generation",
            "confidence": 0.9,
            "secondary_intents": [],
            "keywords": ["code"],
            "requires_code": true,
            "requires_retrieval": true
        }
        Hope that helps!"""

        mock_llm_client.generate.return_value = llm_response

        state = create_initial_state("Generate code")
        result = analyzer.process(state)

        intent = IntentAnalysis(**result["intent_analysis"])
        assert intent.primary_intent == QueryIntent.CODE_GENERATION
        assert intent.confidence == 0.9

    def test_processing_path_updated(self, analyzer, mock_llm_client):
        """Test that processing path includes query_analyzer."""
        llm_response = json.dumps({
            "primary_intent": "general_question",
            "confidence": 0.8,
            "secondary_intents": [],
            "keywords": [],
            "requires_code": False,
            "requires_retrieval": True,
        })
        mock_llm_client.generate.return_value = llm_response

        state = create_initial_state("test")
        state = analyzer(state)  # Use __call__ to add to processing path

        assert "query_analyzer" in state["processing_path"]
        assert state["current_agent"] == "query_analyzer"

    def test_llm_exception_handling(self, analyzer, mock_llm_client):
        """Test handling of LLM client exceptions."""
        # Simulate LLM client raising exception
        mock_llm_client.generate.side_effect = Exception("Connection error")

        state = create_initial_state("Test query")
        result = analyzer.process(state)

        # Should set error in state
        assert result.get("error") is not None
        assert result["error"]["error_type"] == "classification_error"
        assert "Connection error" in result["error"]["message"]
        assert result["should_continue"] is True  # Error is recoverable

    def test_secondary_intents_parsing(self, analyzer, mock_llm_client):
        """Test parsing of secondary intents."""
        llm_response = json.dumps({
            "primary_intent": "endpoint_lookup",
            "confidence": 0.7,
            "secondary_intents": ["code_generation", "schema_explanation"],
            "keywords": ["endpoint"],
            "requires_code": False,
            "requires_retrieval": True,
        })
        mock_llm_client.generate.return_value = llm_response

        state = create_initial_state("Find endpoint and show me how to use it")
        result = analyzer.process(state)

        intent = IntentAnalysis(**result["intent_analysis"])
        assert len(intent.secondary_intents) == 2
        assert QueryIntent.CODE_GENERATION in intent.secondary_intents
        assert QueryIntent.SCHEMA_EXPLANATION in intent.secondary_intents

    def test_invalid_secondary_intent_ignored(self, analyzer, mock_llm_client):
        """Test that invalid secondary intents are ignored."""
        llm_response = json.dumps({
            "primary_intent": "general_question",
            "confidence": 0.8,
            "secondary_intents": ["code_generation", "invalid_intent", "authentication"],
            "keywords": [],
            "requires_code": False,
            "requires_retrieval": True,
        })
        mock_llm_client.generate.return_value = llm_response

        state = create_initial_state("test")
        result = analyzer.process(state)

        intent = IntentAnalysis(**result["intent_analysis"])
        # Should only have valid intents
        assert len(intent.secondary_intents) == 2
        assert QueryIntent.CODE_GENERATION in intent.secondary_intents
        assert QueryIntent.AUTHENTICATION in intent.secondary_intents

    def test_keywords_extraction(self, analyzer, mock_llm_client):
        """Test keyword extraction from LLM response."""
        llm_response = json.dumps({
            "primary_intent": "code_generation",
            "confidence": 0.9,
            "secondary_intents": [],
            "keywords": ["python", "requests", "post", "users", "endpoint"],
            "requires_code": True,
            "requires_retrieval": True,
        })
        mock_llm_client.generate.return_value = llm_response

        state = create_initial_state("Generate Python code using requests library for POST /users")
        result = analyzer.process(state)

        intent = IntentAnalysis(**result["intent_analysis"])
        assert len(intent.keywords) == 5
        assert "python" in intent.keywords
        assert "requests" in intent.keywords
        assert "endpoint" in intent.keywords
