"""
Tests for Gap Analysis Agent.

Tests cover:
- Missing information detection
- Question generation
- Context analysis
- Error handling
"""

import pytest
from unittest.mock import Mock, patch

from src.agents.gap_analysis_agent import GapAnalysisAgent
from src.agents.state import IntentAnalysis, QueryIntent


@pytest.fixture
def gap_agent():
    """Create gap analysis agent with mocked LLM."""
    with patch('src.agents.gap_analysis_agent.create_reasoning_client') as mock_client_factory:
        mock_llm = Mock()
        mock_client_factory.return_value = mock_llm
        agent = GapAnalysisAgent(llm_client=mock_llm)
        agent._llm_client = mock_llm
        yield agent


@pytest.fixture
def state_with_intent():
    """Create state with intent analysis."""
    return {
        "query": "Generate code to create a user",
        "intent_analysis": {
            "primary_intent": QueryIntent.CODE_GENERATION.value,
            "confidence": 0.9,
            "keywords": ["create", "user", "code"],
            "reasoning": "User wants to generate code",
        },
        "retrieved_documents": [],
    }


class TestGapAnalysisAgent:
    """Test suite for Gap Analysis Agent."""

    def test_agent_properties(self, gap_agent):
        """Test agent basic properties."""
        assert gap_agent.name == "gap_analysis_agent"
        assert gap_agent.description == "Analyzes context to identify missing information and generate clarifying questions"

    def test_sufficient_info_detection(self, gap_agent, state_with_intent):
        """Test detection when sufficient info is available."""
        # Mock LLM response - sufficient info
        gap_agent._llm_client.generate = Mock(return_value="""
        {
            "has_sufficient_info": true,
            "confidence": 0.9,
            "missing_aspects": [],
            "questions_for_user": [],
            "reasoning": "Query provides endpoint, method, and parameters"
        }
        """)

        # Add documents to state
        state_with_intent["retrieved_documents"] = [
            {
                "content": "POST /api/users endpoint documentation",
                "metadata": {"endpoint": "/api/users", "method": "POST"},
                "score": 0.9,
            }
        ]

        result = gap_agent.process(state_with_intent)

        assert result["has_sufficient_info"] is True
        assert result["missing_info"] is False
        assert len(result["questions_for_user"]) == 0

    def test_missing_info_detection(self, gap_agent, state_with_intent):
        """Test detection when information is missing."""
        # Mock LLM response - missing info
        gap_agent._llm_client.generate = Mock(return_value="""
        {
            "has_sufficient_info": false,
            "confidence": 0.8,
            "missing_aspects": ["endpoint_path", "request_parameters", "authentication"],
            "questions_for_user": [
                "Which endpoint should I use to create a user (e.g., POST /api/users)?",
                "What parameters are required (e.g., username, email, password)?",
                "What authentication method does the API use?"
            ],
            "reasoning": "Query lacks specific endpoint, parameters, and auth details"
        }
        """)

        result = gap_agent.process(state_with_intent)

        assert result["has_sufficient_info"] is False
        assert result["missing_info"] is True
        assert len(result["questions_for_user"]) == 3
        assert "endpoint" in result["questions_for_user"][0].lower()
        assert "parameters" in result["questions_for_user"][1].lower()
        assert "authentication" in result["questions_for_user"][2].lower()

    def test_question_quality(self, gap_agent, state_with_intent):
        """Test that generated questions are specific and actionable."""
        gap_agent._llm_client.generate = Mock(return_value="""
        {
            "has_sufficient_info": false,
            "confidence": 0.7,
            "missing_aspects": ["http_method"],
            "questions_for_user": [
                "What HTTP method should be used (GET, POST, PUT, DELETE)?"
            ],
            "reasoning": "HTTP method not specified"
        }
        """)

        result = gap_agent.process(state_with_intent)

        questions = result["questions_for_user"]
        assert len(questions) > 0
        # Questions should be complete sentences ending with ?
        for question in questions:
            assert question.strip().endswith("?")
            assert len(question) > 10  # Substantive questions

    def test_context_summarization(self, gap_agent):
        """Test context summarization from state."""
        state = {
            "query": "Test query",
            "retrieved_documents": [
                {
                    "content": "Document content",
                    "metadata": {"endpoint": "/api/test", "method": "GET"},
                    "score": 0.8,
                }
            ],
            "conversation_history": [
                {"role": "user", "content": "Previous message"},
                {"role": "assistant", "content": "Previous response"},
            ],
        }

        summary = gap_agent._summarize_context(state)

        assert "1 relevant documents retrieved" in summary
        assert "endpoint: /api/test" in summary
        assert "2 messages in conversation history" in summary

    def test_context_summarization_with_web_results(self, gap_agent):
        """Test context summary includes web search results."""
        state = {
            "query": "Test query",
            "retrieved_documents": [
                {
                    "content": "Web content",
                    "metadata": {"source": "web_search", "url": "https://example.com"},
                    "score": 0.7,
                }
            ],
        }

        summary = gap_agent._summarize_context(state)

        assert "web search" in summary.lower()

    def test_empty_state_handling(self, gap_agent):
        """Test handling of empty or minimal state."""
        state = {"query": "Generate code"}

        gap_agent._llm_client.generate = Mock(return_value="""
        {
            "has_sufficient_info": false,
            "confidence": 0.3,
            "missing_aspects": ["everything"],
            "questions_for_user": ["Could you provide more details about what you want to generate?"],
            "reasoning": "Very minimal information provided"
        }
        """)

        result = gap_agent.process(state)

        assert result["has_sufficient_info"] is False
        assert len(result["questions_for_user"]) > 0

    def test_no_query_error(self, gap_agent):
        """Test handling when no query is provided."""
        state = {}

        result = gap_agent.process(state)

        # Should default to having sufficient info (don't block)
        assert "has_sufficient_info" in result or "gap_analysis" in result

    def test_llm_error_handling(self, gap_agent, state_with_intent):
        """Test graceful handling of LLM errors."""
        # Mock LLM to raise exception
        gap_agent._llm_client.generate = Mock(side_effect=Exception("LLM Error"))

        result = gap_agent.process(state_with_intent)

        # Should default to sufficient info (don't block on errors)
        assert result["has_sufficient_info"] is True
        assert result["missing_info"] is False

    def test_json_parsing_error_handling(self, gap_agent, state_with_intent):
        """Test handling of malformed JSON responses."""
        # Mock LLM to return invalid JSON
        gap_agent._llm_client.generate = Mock(return_value="This is not JSON")

        result = gap_agent.process(state_with_intent)

        # Should default to sufficient info
        assert result["has_sufficient_info"] is True

    def test_markdown_json_extraction(self, gap_agent, state_with_intent):
        """Test extraction of JSON from markdown code blocks."""
        # Mock LLM response with markdown code block
        gap_agent._llm_client.generate = Mock(return_value="""
        ```json
        {
            "has_sufficient_info": true,
            "confidence": 0.9,
            "missing_aspects": [],
            "questions_for_user": [],
            "reasoning": "All information available"
        }
        ```
        """)

        result = gap_agent.process(state_with_intent)

        assert result["has_sufficient_info"] is True

    def test_confidence_scoring(self, gap_agent, state_with_intent):
        """Test that confidence scores are included in analysis."""
        gap_agent._llm_client.generate = Mock(return_value="""
        {
            "has_sufficient_info": false,
            "confidence": 0.75,
            "missing_aspects": ["auth"],
            "questions_for_user": ["What auth method?"],
            "reasoning": "Auth method unclear"
        }
        """)

        result = gap_agent.process(state_with_intent)

        assert "gap_analysis" in result
        assert result["gap_analysis"]["confidence"] == 0.75

    def test_intent_based_analysis(self, gap_agent):
        """Test that analysis varies based on intent."""
        # Code generation intent
        code_state = {
            "query": "Generate code",
            "intent_analysis": {
                "primary_intent": QueryIntent.CODE_GENERATION.value,
                "confidence": 0.9,
            },
        }

        gap_agent._llm_client.generate = Mock(return_value="""
        {
            "has_sufficient_info": false,
            "confidence": 0.8,
            "missing_aspects": ["endpoint", "method", "params"],
            "questions_for_user": ["Need endpoint, method, and params"],
            "reasoning": "Code gen requires specific details"
        }
        """)

        result = gap_agent.process(code_state)

        # Code generation should be more strict
        assert result["has_sufficient_info"] is False

    def test_reasoning_inclusion(self, gap_agent, state_with_intent):
        """Test that reasoning is included in gap analysis."""
        gap_agent._llm_client.generate = Mock(return_value="""
        {
            "has_sufficient_info": false,
            "confidence": 0.7,
            "missing_aspects": ["details"],
            "questions_for_user": ["Need details"],
            "reasoning": "This is the reasoning for the analysis"
        }
        """)

        result = gap_agent.process(state_with_intent)

        assert "gap_analysis" in result
        assert "reasoning" in result["gap_analysis"]
        assert len(result["gap_analysis"]["reasoning"]) > 0


class TestGapAnalysisIntegration:
    """Integration tests for gap analysis."""

    def test_gap_analysis_workflow(self, gap_agent):
        """Test complete gap analysis workflow."""
        state = {
            "query": "Generate Python code to create a new user",
            "intent_analysis": {
                "primary_intent": QueryIntent.CODE_GENERATION.value,
                "confidence": 0.95,
                "keywords": ["python", "create", "user"],
            },
            "retrieved_documents": [],
            "conversation_history": [],
        }

        gap_agent._llm_client.generate = Mock(return_value="""
        {
            "has_sufficient_info": false,
            "confidence": 0.85,
            "missing_aspects": ["api_endpoint", "request_body", "auth_method"],
            "questions_for_user": [
                "Which API endpoint should I use for user creation?",
                "What fields are required in the request body?",
                "How should the API authenticate requests?"
            ],
            "reasoning": "Need endpoint, request structure, and auth details for code generation"
        }
        """)

        result = gap_agent.process(state)

        # Verify complete workflow
        assert "gap_analysis" in result
        assert "has_sufficient_info" in result
        assert "missing_info" in result
        assert "questions_for_user" in result

        # Verify state updates
        assert result["has_sufficient_info"] is False
        assert result["missing_info"] is True
        assert len(result["questions_for_user"]) == 3

    def test_gap_analysis_with_documents(self, gap_agent):
        """Test gap analysis with retrieved documents."""
        state = {
            "query": "Create user code",
            "intent_analysis": {
                "primary_intent": QueryIntent.CODE_GENERATION.value,
                "confidence": 0.9,
            },
            "retrieved_documents": [
                {
                    "content": "POST /api/users - Creates a new user. Requires: username, email, password",
                    "metadata": {
                        "endpoint": "/api/users",
                        "method": "POST",
                    },
                    "score": 0.95,
                }
            ],
        }

        gap_agent._llm_client.generate = Mock(return_value="""
        {
            "has_sufficient_info": true,
            "confidence": 0.95,
            "missing_aspects": [],
            "questions_for_user": [],
            "reasoning": "Documentation provides endpoint, method, and required parameters"
        }
        """)

        result = gap_agent.process(state)

        # With good documentation, should have sufficient info
        assert result["has_sufficient_info"] is True
        assert len(result["questions_for_user"]) == 0
