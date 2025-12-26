"""
End-to-End Integration Tests for Proactive Intelligence Features.

Tests cover:
- Complete gap analysis workflow
- URL extraction and usage
- Smart web search
- Proactive question asking
- Supervisor routing
"""

import pytest
from unittest.mock import Mock, patch, MagicMock

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


class TestCompleteGapAnalysisWorkflow:
    """Test complete gap analysis workflow from query to response."""

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
                    "Which endpoint should I use (e.g., POST /api/users)?",
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

        # Should ask user for clarification
        assert "questions_for_user" in result or "I need" in result.get("response", "")
        assert result.get("missing_info") is not None or "questions" in result.get("response", "").lower()

    def test_sufficient_info_generates_code(
        self, supervisor_with_gap_analysis, mock_llm_client, mock_vector_store
    ):
        """Test that sufficient information leads to code generation."""
        # Mock responses
        mock_llm_client.generate = Mock(side_effect=[
            # Query analyzer
            """```json
            {
                "primary_intent": "code_generation",
                "confidence": 0.95,
                "keywords": ["create", "user", "POST"],
                "reasoning": "Code generation request"
            }
            ```""",
            # RAG response
            "Documentation about POST /api/users endpoint",
            # Gap analysis
            """```json
            {
                "has_sufficient_info": true,
                "confidence": 0.95,
                "missing_aspects": [],
                "questions_for_user": [],
                "reasoning": "All details provided in docs"
            }
            ```""",
            # Code generation
            "import requests\n\nresponse = requests.post('/api/users', json=data)",
        ])

        # Mock comprehensive docs
        mock_vector_store.search.return_value = [
            {
                "id": "doc1",
                "content": "POST /api/users - Creates user. Params: username, email",
                "metadata": {"endpoint": "/api/users", "method": "POST"},
                "score": 0.95,
            }
        ]

        result = supervisor_with_gap_analysis.process(
            "Generate Python code to create a user via POST /api/users"
        )

        # Should have code snippets
        assert result.get("code_snippets") is not None or "import" in result.get("response", "")


class TestURLExtractionIntegration:
    """Test URL extraction in complete workflow."""

    @patch('src.agents.rag_agent.URLScraperService')
    @patch('src.agents.rag_agent.ConversationMemoryService')
    def test_url_extraction_and_usage(
        self, mock_memory_class, mock_scraper_class, supervisor_with_gap_analysis, mock_llm_client
    ):
        """Test that URLs are extracted, scraped, and used."""
        # Mock URL scraper
        mock_scraper = Mock()
        mock_scraper.extract_urls.return_value = ["https://api.example.com/docs"]
        mock_scraper.scrape_urls.return_value = [
            {
                "title": "API Documentation",
                "content": "POST /api/users endpoint documentation...",
                "url": "https://api.example.com/docs",
            }
        ]
        mock_scraper.format_for_vector_store.return_value = {
            "content": "POST /api/users endpoint documentation",
            "metadata": {
                "source": "url_scrape",
                "url": "https://api.example.com/docs",
            },
            "score": 1.0,
            "doc_id": "url_1",
        }
        mock_scraper_class.return_value = mock_scraper

        # Mock memory service
        mock_memory = Mock()
        mock_memory.embed_url_content.return_value = True
        mock_memory_class.return_value = mock_memory

        # Mock LLM responses
        mock_llm_client.generate = Mock(side_effect=[
            # Query analyzer
            """{"primary_intent": "general_question", "confidence": 0.8, "keywords": []}""",
            # RAG response
            "Based on the documentation, you can create users using POST /api/users",
        ])

        result = supervisor_with_gap_analysis.process(
            "How do I use this API? https://api.example.com/docs"
        )

        # URL should have been extracted and scraped
        mock_scraper.extract_urls.assert_called()
        mock_scraper.scrape_urls.assert_called_with(["https://api.example.com/docs"])

        # Content should have been embedded
        mock_memory.embed_url_content.assert_called()

        # Response should use scraped content
        assert result.get("response") is not None


class TestSmartWebSearch:
    """Test smart web search with intent-based query generation."""

    @patch('src.agents.rag_agent.WebSearchService')
    def test_smart_search_triggered(
        self, mock_web_search_class, supervisor_with_gap_analysis, mock_llm_client, mock_vector_store
    ):
        """Test that smart web search is triggered when relevance is low."""
        # Mock web search
        mock_web_search = Mock()
        mock_web_search.search_to_documents.return_value = [
            {
                "content": "OAuth2 authentication guide from web",
                "metadata": {
                    "source": "web_search",
                    "url": "https://example.com/oauth2",
                },
                "score": 0.9,
                "doc_id": "web_1",
            }
        ]
        mock_web_search_class.return_value = mock_web_search

        # Mock vector store with low relevance results
        mock_vector_store.search.return_value = [
            {
                "id": "doc1",
                "content": "General API info",
                "metadata": {},
                "score": 0.3,  # Low relevance
            }
        ]

        # Mock LLM responses
        mock_llm_client.generate = Mock(side_effect=[
            # Query analyzer - authentication intent
            """```json
            {
                "primary_intent": "authentication",
                "confidence": 0.9,
                "keywords": ["oauth2", "auth", "token"],
                "reasoning": "Authentication question"
            }
            ```""",
            # RAG response using web results
            "OAuth2 authentication uses access tokens...",
        ])

        result = supervisor_with_gap_analysis.process("How do I authenticate with OAuth2?")

        # Web search should have been triggered
        mock_web_search.search_to_documents.assert_called()

        # Should have response
        assert result.get("response") is not None


class TestProactiveQuestions:
    """Test proactive question asking."""

    def test_question_format_in_response(
        self, supervisor_with_gap_analysis, mock_llm_client, mock_vector_store
    ):
        """Test that clarifying questions are properly formatted."""
        # Mock responses for missing info scenario
        mock_llm_client.generate = Mock(side_effect=[
            # Query analyzer
            """{"primary_intent": "code_generation", "confidence": 0.9, "keywords": ["code"]}""",
            # RAG
            "Some documentation found",
            # Gap analysis - missing info
            """```json
            {
                "has_sufficient_info": false,
                "confidence": 0.7,
                "missing_aspects": ["endpoint"],
                "questions_for_user": [
                    "Which API endpoint should I use?",
                    "What HTTP method (GET, POST, etc.)?"
                ],
                "reasoning": "Need endpoint and method details"
            }
            ```""",
        ])

        mock_vector_store.search.return_value = [
            {"id": "1", "content": "API docs", "metadata": {}, "score": 0.5}
        ]

        result = supervisor_with_gap_analysis.process("Generate API code")

        response = result.get("response", "")

        # Questions should be numbered and clear
        assert "1." in response or "?" in response
        assert len(response) > 20  # Should have substantive content


class TestSupervisorRouting:
    """Test supervisor routing with gap analysis."""

    def test_routing_to_gap_analysis(
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

        # Processing path should include gap_analysis
        processing_path = result.get("processing_path", [])
        assert "gap_analysis" in processing_path or result.get("code_snippets") is not None

    def test_general_questions_skip_gap_analysis(
        self, supervisor_with_gap_analysis, mock_llm_client, mock_vector_store
    ):
        """Test that general questions skip gap analysis."""
        mock_llm_client.generate = Mock(side_effect=[
            # Query analyzer - general question
            """{"primary_intent": "general_question", "confidence": 0.9, "keywords": ["api"]}""",
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

        # Should not raise exception
        result = supervisor_with_gap_analysis.process("Generate code")

        # Should have some response
        assert result is not None

    @patch('src.agents.rag_agent.URLScraperService')
    def test_url_scraping_error_doesnt_block(
        self, mock_scraper_class, supervisor_with_gap_analysis, mock_llm_client, mock_vector_store
    ):
        """Test that URL scraping errors don't block processing."""
        # Mock scraper to fail
        mock_scraper = Mock()
        mock_scraper.extract_urls.return_value = ["https://example.com"]
        mock_scraper.scrape_urls.side_effect = Exception("Scraping error")
        mock_scraper_class.return_value = mock_scraper

        mock_llm_client.generate = Mock(side_effect=[
            """{"primary_intent": "general_question", "confidence": 0.8, "keywords": []}""",
            "Response based on available data",
        ])

        mock_vector_store.search.return_value = [
            {"id": "1", "content": "Data", "metadata": {}, "score": 0.7}
        ]

        # Should not raise exception
        result = supervisor_with_gap_analysis.process(
            "Tell me about https://example.com/api"
        )

        assert result is not None
        assert result.get("response") is not None


class TestContextOptimization:
    """Test session context optimization (128k window vs vector store)."""

    @patch('src.agents.rag_agent.ConversationMemoryService')
    def test_web_results_are_embedded(
        self, mock_memory_class, supervisor_with_gap_analysis, mock_llm_client, mock_vector_store
    ):
        """Test that web search results are embedded in vector store."""
        # Mock memory service
        mock_memory = Mock()
        mock_memory.embed_web_search_results.return_value = 2
        mock_memory_class.return_value = mock_memory

        # Configure for web search trigger
        mock_vector_store.search.return_value = [
            {"id": "1", "content": "Low relevance", "metadata": {}, "score": 0.3}
        ]

        # Mock web search to return results
        with patch('src.agents.rag_agent.WebSearchService') as mock_web_search_class:
            mock_web_search = Mock()
            mock_web_search.search_to_documents.return_value = [
                {
                    "content": "Web result 1",
                    "metadata": {"source": "web_search"},
                    "score": 0.9,
                    "doc_id": "web_1",
                },
                {
                    "content": "Web result 2",
                    "metadata": {"source": "web_search"},
                    "score": 0.8,
                    "doc_id": "web_2",
                },
            ]
            mock_web_search_class.return_value = mock_web_search

            mock_llm_client.generate = Mock(side_effect=[
                """{"primary_intent": "general_question", "confidence": 0.8, "keywords": []}""",
                "Answer based on web results",
            ])

            supervisor_with_gap_analysis.process("Query requiring web search")

            # Web results should be embedded
            mock_memory.embed_web_search_results.assert_called()


class TestEndToEndScenarios:
    """Test realistic end-to-end scenarios."""

    def test_incomplete_request_gets_questions(
        self, supervisor_with_gap_analysis, mock_llm_client, mock_vector_store
    ):
        """Test: User provides incomplete info → Gets clarifying questions."""
        # Scenario: User wants code but doesn't specify details
        mock_llm_client.generate = Mock(side_effect=[
            # Intent: code generation
            """{"primary_intent": "code_generation", "confidence": 0.85, "keywords": ["create", "user"]}""",
            # RAG finds generic docs
            "Found general user creation documentation",
            # Gap analysis detects missing info
            """```json
            {
                "has_sufficient_info": false,
                "confidence": 0.75,
                "missing_aspects": ["specific_endpoint", "auth_method", "parameters"],
                "questions_for_user": [
                    "Which specific endpoint should I use for user creation?",
                    "What authentication method does your API require?",
                    "What user parameters need to be provided (username, email, etc.)?"
                ],
                "reasoning": "Query lacks specific implementation details needed for code generation"
            }
            ```""",
        ])

        mock_vector_store.search.return_value = [
            {
                "id": "generic",
                "content": "Users can be created via API",
                "metadata": {},
                "score": 0.6,
            }
        ]

        result = supervisor_with_gap_analysis.process("Create user code")

        # Should get questions
        response = result.get("response", "")
        questions = result.get("questions_for_user", [])

        assert len(questions) > 0 or "?" in response
        assert "endpoint" in response.lower() or any("endpoint" in q.lower() for q in questions)

    def test_complete_request_generates_code(
        self, supervisor_with_gap_analysis, mock_llm_client, mock_vector_store
    ):
        """Test: User provides complete info → Gets code directly."""
        mock_llm_client.generate = Mock(side_effect=[
            # Intent: code generation
            """{"primary_intent": "code_generation", "confidence": 0.95, "keywords": ["python", "POST", "/api/users"]}""",
            # RAG finds specific docs
            "Found documentation for POST /api/users endpoint",
            # Gap analysis: sufficient info
            """{"has_sufficient_info": true, "confidence": 0.95, "missing_aspects": [], "questions_for_user": [], "reasoning": "All required details present"}""",
            # Code generation
            """import requests

response = requests.post(
    'https://api.example.com/users',
    json={'username': 'john', 'email': 'john@example.com'},
    headers={'Authorization': 'Bearer token'}
)""",
        ])

        mock_vector_store.search.return_value = [
            {
                "id": "specific",
                "content": "POST /api/users - Creates user. Required: username, email. Auth: Bearer token",
                "metadata": {"endpoint": "/api/users", "method": "POST"},
                "score": 0.95,
            }
        ]

        result = supervisor_with_gap_analysis.process(
            "Generate Python code to create a user using POST /api/users with username and email, using Bearer token auth"
        )

        # Should have code
        assert result.get("code_snippets") or "import requests" in result.get("response", "")
