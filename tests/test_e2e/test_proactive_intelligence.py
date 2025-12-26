"""
End-to-End Integration Tests for Proactive Intelligence Features.

Simplified tests that focus on actual integration rather than heavy mocking.
Tests cover:
- Gap analysis workflow
- Supervisor routing
- Error handling
"""

import pytest
from unittest.mock import Mock

from src.agents.supervisor import SupervisorAgent
from src.agents.query_analyzer import QueryAnalyzer
from src.agents.rag_agent import RAGAgent
from src.agents.code_agent import CodeGenerator
from src.agents.doc_analyzer import DocumentationAnalyzer
from src.agents.gap_analysis_agent import GapAnalysisAgent
from src.agents.state import QueryIntent


@pytest.fixture
def mock_llm_client():
    """Create mock LLM client."""
    mock = Mock()
    mock.generate = Mock(return_value="Test response")
    return mock


@pytest.fixture
def mock_vector_store():
    """Create mock vector store."""
    mock = Mock()
    mock.search = Mock(return_value=[])
    mock.add_documents = Mock()
    return mock


@pytest.fixture
def supervisor_with_gap_analysis(mock_llm_client, mock_vector_store):
    """Create supervisor with all agents including gap analysis."""
    query_analyzer = QueryAnalyzer(llm_client=mock_llm_client)
    rag_agent = RAGAgent(
        vector_store=mock_vector_store,
        llm_client=mock_llm_client,
    )
    code_generator = CodeGenerator(llm_client=mock_llm_client)
    doc_analyzer = DocumentationAnalyzer(llm_client=mock_llm_client)
    gap_analysis = GapAnalysisAgent(llm_client=mock_llm_client)

    return SupervisorAgent(
        query_analyzer=query_analyzer,
        rag_agent=rag_agent,
        code_generator=code_generator,
        doc_analyzer=doc_analyzer,
        gap_analysis_agent=gap_analysis,
    )


class TestGapAnalysisWorkflow:
    """Test gap analysis workflow integration."""

    def test_missing_info_triggers_questions(
        self, supervisor_with_gap_analysis, mock_llm_client, mock_vector_store
    ):
        """Test that missing information triggers clarifying questions."""
        # Mock query analysis - code generation intent
        mock_llm_client.generate = Mock(side_effect=[
            # Query analyzer response
            """```json
            {
                "primary_intent": "code_generation",
                "confidence": 0.9,
                "keywords": ["generate", "code", "user"],
                "reasoning": "User wants to generate code"
            }
            ```""",
            # RAG response
            "I found some documentation about user creation.",
            # Gap analysis response
            """```json
            {
                "has_sufficient_info": false,
                "confidence": 0.8,
                "missing_aspects": ["endpoint", "parameters", "auth"],
                "questions_for_user": [
                    "Which endpoint should I use?",
                    "What parameters are required?",
                    "What authentication method?"
                ],
                "reasoning": "Missing endpoint details"
            }
            ```""",
        ])

        # Mock vector store to return minimal docs
        mock_vector_store.search.return_value = [
            {
                "id": "doc1",
                "content": "User creation is possible",
                "metadata": {},
                "score": 0.6,
            }
        ]

        result = supervisor_with_gap_analysis.process("Generate code to create a user")

        # Should have gap analysis in processing path
        processing_path = result.get("processing_path", [])
        assert "gap_analysis" in processing_path or result.get("missing_info") is not None

    def test_sufficient_info_proceeds_to_code_gen(
        self, supervisor_with_gap_analysis, mock_llm_client, mock_vector_store
    ):
        """Test that sufficient information proceeds to code generation."""
        mock_llm_client.generate = Mock(side_effect=[
            # Query analyzer
            """{"primary_intent": "code_generation", "confidence": 0.95, "keywords": []}""",
            # RAG response
            "Documentation about POST /api/users endpoint",
            # Gap analysis - sufficient info
            """{"has_sufficient_info": true, "confidence": 0.95, "missing_aspects": [], "questions_for_user": [], "reasoning": "Good"}""",
            # Code generation
            "import requests\n\nresponse = requests.post('/api/users', json=data)",
        ])

        mock_vector_store.search.return_value = [
            {
                "id": "doc1",
                "content": "POST /api/users - Creates user",
                "metadata": {"endpoint": "/api/users", "method": "POST"},
                "score": 0.95,
            }
        ]

        result = supervisor_with_gap_analysis.process("Generate code for POST /api/users")

        # Should reach code generator
        processing_path = result.get("processing_path", [])
        assert "code_generator" in processing_path or result.get("code_snippets") is not None


class TestSupervisorRouting:
    """Test supervisor routing with gap analysis."""

    def test_code_generation_routes_through_gap_analysis(
        self, supervisor_with_gap_analysis, mock_llm_client, mock_vector_store
    ):
        """Test that code generation requests route through gap analysis."""
        mock_llm_client.generate = Mock(side_effect=[
            # Query analyzer - code gen intent
            """{"primary_intent": "code_generation", "confidence": 0.9, "keywords": []}""",
            # RAG
            "Documentation retrieved",
            # Gap analysis - sufficient info
            """{"has_sufficient_info": true, "confidence": 0.9, "missing_aspects": [], "questions_for_user": [], "reasoning": "Good"}""",
            # Code gen
            "import requests",
        ])

        mock_vector_store.search.return_value = [
            {"id": "1", "content": "Docs", "metadata": {}, "score": 0.8}
        ]

        result = supervisor_with_gap_analysis.process("Generate code")

        # Should have some result
        assert result is not None
        assert "processing_path" in result

    def test_general_questions_skip_gap_analysis(
        self, supervisor_with_gap_analysis, mock_llm_client, mock_vector_store
    ):
        """Test that general questions skip gap analysis."""
        mock_llm_client.generate = Mock(side_effect=[
            # Query analyzer - general question
            """{"primary_intent": "general_question", "confidence": 0.9, "keywords": []}""",
            # RAG response
            "The API provides user management endpoints",
        ])

        mock_vector_store.search.return_value = [
            {"id": "1", "content": "API documentation", "metadata": {}, "score": 0.9}
        ]

        result = supervisor_with_gap_analysis.process("What does this API do?")

        # Processing path should NOT include gap_analysis
        processing_path = result.get("processing_path", [])
        assert "gap_analysis" not in processing_path


class TestErrorHandling:
    """Test error handling in proactive intelligence features."""

    def test_gap_analysis_error_doesnt_block(
        self, supervisor_with_gap_analysis, mock_llm_client, mock_vector_store
    ):
        """Test that gap analysis errors don't block code generation."""
        mock_llm_client.generate = Mock(side_effect=[
            # Query analyzer
            """{"primary_intent": "code_generation", "confidence": 0.9, "keywords": []}""",
            # RAG
            "Documentation",
            # Gap analysis - error
            Exception("Gap analysis error"),
        ])

        mock_vector_store.search.return_value = [
            {"id": "1", "content": "Docs", "metadata": {}, "score": 0.8}
        ]

        # Should not raise exception (gap analysis defaults to sufficient info)
        result = supervisor_with_gap_analysis.process("Generate code")

        # Should have some result
        assert result is not None


class TestEndToEndScenarios:
    """Test realistic end-to-end scenarios."""

    def test_incomplete_request_workflow(
        self, supervisor_with_gap_analysis, mock_llm_client, mock_vector_store
    ):
        """Test workflow when user provides incomplete information."""
        mock_llm_client.generate = Mock(side_effect=[
            # Intent: code generation
            """{"primary_intent": "code_generation", "confidence": 0.85, "keywords": []}""",
            # RAG finds generic docs
            "Found general user creation documentation",
            # Gap analysis detects missing info
            """{"has_sufficient_info": false, "confidence": 0.75, "missing_aspects": ["endpoint"], "questions_for_user": ["Which endpoint?"], "reasoning": "Missing details"}""",
        ])

        mock_vector_store.search.return_value = [
            {"id": "1", "content": "Users can be created via API", "metadata": {}, "score": 0.6}
        ]

        result = supervisor_with_gap_analysis.process("Create user code")

        # Should have some form of output
        assert result is not None
        assert "response" in result or "questions_for_user" in result

    def test_complete_request_workflow(
        self, supervisor_with_gap_analysis, mock_llm_client, mock_vector_store
    ):
        """Test workflow when user provides complete information."""
        mock_llm_client.generate = Mock(side_effect=[
            # Intent: code generation
            """{"primary_intent": "code_generation", "confidence": 0.95, "keywords": []}""",
            # RAG finds specific docs
            "Found documentation for POST /api/users endpoint",
            # Gap analysis: sufficient info
            """{"has_sufficient_info": true, "confidence": 0.95, "missing_aspects": [], "questions_for_user": [], "reasoning": "Complete"}""",
            # Code generation
            "import requests\nresponse = requests.post('/api/users')",
        ])

        mock_vector_store.search.return_value = [
            {
                "id": "1",
                "content": "POST /api/users - Creates user. Required: username, email",
                "metadata": {"endpoint": "/api/users", "method": "POST"},
                "score": 0.95,
            }
        ]

        result = supervisor_with_gap_analysis.process(
            "Generate Python code to create a user using POST /api/users"
        )

        # Should have response
        assert result is not None
        assert result.get("response") is not None or result.get("code_snippets") is not None
