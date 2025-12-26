"""
Tests for Conversation Memory Service.

Tests cover:
- Web search result embedding
- URL content embedding
- Conversation exchange embedding
- Memory search
- Configuration
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from src.services.conversation_memory import (
    ConversationMemoryService,
    get_conversation_memory_service,
)


@pytest.fixture
def mock_vector_store():
    """Create mock vector store."""
    mock_store = Mock()
    mock_store.add_documents = Mock()
    mock_store.search = Mock(return_value=[])
    return mock_store


@pytest.fixture
def memory_service(mock_vector_store):
    """Create conversation memory service with mock vector store."""
    return ConversationMemoryService(
        vector_store=mock_vector_store,
        enable_conversation_embedding=False,
        enable_web_result_embedding=True,
    )


@pytest.fixture
def memory_service_with_conv_embedding(mock_vector_store):
    """Create service with conversation embedding enabled."""
    return ConversationMemoryService(
        vector_store=mock_vector_store,
        enable_conversation_embedding=True,
        enable_web_result_embedding=True,
    )


class TestWebSearchResultEmbedding:
    """Test web search result embedding."""

    def test_embed_web_search_results(self, memory_service, mock_vector_store):
        """Test embedding web search results."""
        query = "How to authenticate with OAuth2"
        web_results = [
            {
                "content": "OAuth2 is a protocol for authorization...",
                "metadata": {
                    "source": "web_search",
                    "url": "https://example.com/oauth2",
                    "title": "OAuth2 Guide",
                },
                "score": 0.9,
                "doc_id": "websearch_1",
            },
            {
                "content": "OAuth2 authentication flow...",
                "metadata": {
                    "source": "web_search",
                    "url": "https://example.com/oauth2-flow",
                    "title": "OAuth2 Flow",
                },
                "score": 0.8,
                "doc_id": "websearch_2",
            },
        ]

        count = memory_service.embed_web_search_results(query, web_results)

        assert count == 2
        assert mock_vector_store.add_documents.call_count == 2

        # Check first call
        first_call = mock_vector_store.add_documents.call_args_list[0]
        docs, metadatas, ids = first_call[1]['documents'], first_call[1]['metadatas'], first_call[1]['ids']

        assert len(docs) == 1
        assert "OAuth2 is a protocol" in docs[0]
        assert metadatas[0]["original_query"] == query
        assert metadatas[0]["type"] == "web_search_result"
        assert "embedded_at" in metadatas[0]

    def test_embed_empty_web_results(self, memory_service, mock_vector_store):
        """Test embedding empty web results list."""
        count = memory_service.embed_web_search_results("query", [])

        assert count == 0
        mock_vector_store.add_documents.assert_not_called()

    def test_web_embedding_disabled(self, mock_vector_store):
        """Test that web embedding can be disabled."""
        service = ConversationMemoryService(
            vector_store=mock_vector_store,
            enable_web_result_embedding=False,
        )

        count = service.embed_web_search_results("query", [{"content": "test"}])

        assert count == 0
        mock_vector_store.add_documents.assert_not_called()

    def test_web_result_error_handling(self, memory_service, mock_vector_store):
        """Test error handling during web result embedding."""
        mock_vector_store.add_documents.side_effect = Exception("DB Error")

        web_results = [
            {
                "content": "Test content",
                "metadata": {"source": "web_search"},
                "score": 0.9,
                "doc_id": "test_1",
            }
        ]

        # Should not raise exception
        count = memory_service.embed_web_search_results("query", web_results)

        # Count should be 0 due to error
        assert count == 0

    def test_session_id_in_metadata(self, memory_service, mock_vector_store):
        """Test that session ID is included in metadata."""
        web_results = [
            {
                "content": "Test",
                "metadata": {},
                "score": 1.0,
                "doc_id": "test",
            }
        ]

        memory_service.embed_web_search_results(
            "query",
            web_results,
            session_id="session123",
        )

        call_args = mock_vector_store.add_documents.call_args_list[0]
        metadata = call_args[1]['metadatas'][0]
        assert metadata["session_id"] == "session123"


class TestURLContentEmbedding:
    """Test URL content embedding."""

    def test_embed_url_content(self, memory_service, mock_vector_store):
        """Test embedding scraped URL content."""
        url_content = {
            "content": "API Documentation content here...",
            "url": "https://api.example.com/docs",
            "title": "API Docs",
        }

        result = memory_service.embed_url_content(
            url_content=url_content,
            query="API documentation",
            session_id="session123",
        )

        assert result is True
        mock_vector_store.add_documents.assert_called_once()

        call_args = mock_vector_store.add_documents.call_args
        docs = call_args[1]['documents']
        metadatas = call_args[1]['metadatas']
        ids = call_args[1]['ids']

        assert len(docs) == 1
        assert "API Documentation content" in docs[0]
        assert metadatas[0]["source"] == "url_scrape"
        assert metadatas[0]["url"] == "https://api.example.com/docs"
        assert metadatas[0]["title"] == "API Docs"
        assert metadatas[0]["original_query"] == "API documentation"
        assert metadatas[0]["session_id"] == "session123"
        assert ids[0].startswith("url_")

    def test_embed_url_content_empty(self, memory_service, mock_vector_store):
        """Test embedding URL with empty content."""
        url_content = {
            "content": "",
            "url": "https://example.com",
            "title": "Empty",
        }

        result = memory_service.embed_url_content(url_content, "query")

        assert result is False
        mock_vector_store.add_documents.assert_not_called()

    def test_url_content_error_handling(self, memory_service, mock_vector_store):
        """Test error handling during URL content embedding."""
        mock_vector_store.add_documents.side_effect = Exception("DB Error")

        url_content = {
            "content": "Test content",
            "url": "https://example.com",
            "title": "Test",
        }

        result = memory_service.embed_url_content(url_content, "query")

        assert result is False


class TestConversationExchangeEmbedding:
    """Test conversation exchange embedding."""

    def test_embed_conversation_exchange_disabled(self, memory_service, mock_vector_store):
        """Test that conversation embedding is disabled by default."""
        result = memory_service.embed_conversation_exchange(
            user_message="How do I create a user?",
            assistant_response="You can create a user by calling POST /api/users...",
        )

        assert result is False
        mock_vector_store.add_documents.assert_not_called()

    def test_embed_conversation_exchange_enabled(
        self, memory_service_with_conv_embedding, mock_vector_store
    ):
        """Test conversation embedding when enabled."""
        result = memory_service_with_conv_embedding.embed_conversation_exchange(
            user_message="How do I authenticate?",
            assistant_response="You can authenticate using OAuth2...",
            metadata={"intent": "authentication"},
            session_id="session123",
        )

        assert result is True
        mock_vector_store.add_documents.assert_called_once()

        call_args = mock_vector_store.add_documents.call_args
        docs = call_args[1]['documents']
        metadatas = call_args[1]['metadatas']

        # Check formatted Q&A
        assert len(docs) == 1
        assert "Question: How do I authenticate?" in docs[0]
        assert "Answer: You can authenticate using OAuth2" in docs[0]

        # Check metadata
        assert metadatas[0]["type"] == "conversation_exchange"
        assert metadatas[0]["session_id"] == "session123"
        assert metadatas[0]["intent"] == "authentication"
        assert "embedded_at" in metadatas[0]

    def test_conversation_message_preview(
        self, memory_service_with_conv_embedding, mock_vector_store
    ):
        """Test that long user messages are previewed in metadata."""
        long_message = "A" * 300

        memory_service_with_conv_embedding.embed_conversation_exchange(
            user_message=long_message,
            assistant_response="Response",
        )

        call_args = mock_vector_store.add_documents.call_args
        metadata = call_args[1]['metadatas'][0]

        # Preview should be limited to 200 chars
        assert len(metadata["user_message"]) == 200

    def test_conversation_embedding_error_handling(
        self, memory_service_with_conv_embedding, mock_vector_store
    ):
        """Test error handling in conversation embedding."""
        mock_vector_store.add_documents.side_effect = Exception("DB Error")

        result = memory_service_with_conv_embedding.embed_conversation_exchange(
            user_message="Test",
            assistant_response="Response",
        )

        assert result is False


class TestConversationSearch:
    """Test conversation history search."""

    def test_search_conversation_history(self, memory_service, mock_vector_store):
        """Test searching embedded conversation history."""
        mock_vector_store.search.return_value = [
            {
                "content": "Question: How to auth?\n\nAnswer: Use OAuth2...",
                "metadata": {"type": "conversation_exchange"},
                "score": 0.9,
            }
        ]

        results = memory_service.search_conversation_history("authentication", limit=5)

        assert len(results) == 1
        mock_vector_store.search.assert_called_once_with(
            query="authentication",
            n_results=5,
            where={"type": "conversation_exchange"},
        )

    def test_search_conversation_error_handling(self, memory_service, mock_vector_store):
        """Test error handling in conversation search."""
        mock_vector_store.search.side_effect = Exception("Search Error")

        results = memory_service.search_conversation_history("query")

        assert results == []


class TestFactoryFunction:
    """Test factory function."""

    @patch('src.services.conversation_memory.get_vector_store')
    def test_get_conversation_memory_service(self, mock_get_vector_store):
        """Test factory function creates service with correct defaults."""
        mock_store = Mock()
        mock_get_vector_store.return_value = mock_store

        service = get_conversation_memory_service()

        assert isinstance(service, ConversationMemoryService)
        assert service.enable_conversation_embedding is False
        assert service.enable_web_result_embedding is True


class TestConfiguration:
    """Test service configuration."""

    def test_default_configuration(self, mock_vector_store):
        """Test default configuration."""
        service = ConversationMemoryService(vector_store=mock_vector_store)

        assert service.enable_conversation_embedding is False
        assert service.enable_web_result_embedding is True

    def test_custom_configuration(self, mock_vector_store):
        """Test custom configuration."""
        service = ConversationMemoryService(
            vector_store=mock_vector_store,
            enable_conversation_embedding=True,
            enable_web_result_embedding=False,
        )

        assert service.enable_conversation_embedding is True
        assert service.enable_web_result_embedding is False


class TestIntegration:
    """Integration tests for conversation memory."""

    def test_full_web_result_workflow(self, memory_service, mock_vector_store):
        """Test complete workflow of web result embedding."""
        query = "Python API integration"
        web_results = [
            {
                "content": "Python requests library tutorial...",
                "metadata": {
                    "source": "web_search",
                    "url": "https://example.com/python-requests",
                    "title": "Python Requests",
                },
                "score": 0.95,
                "doc_id": "web_1",
            }
        ]

        # Embed results
        count = memory_service.embed_web_search_results(
            query=query,
            web_results=web_results,
            session_id="test_session",
        )

        assert count == 1

        # Verify embedding call
        call_args = mock_vector_store.add_documents.call_args
        docs = call_args[1]['documents']
        metadatas = call_args[1]['metadatas']

        assert "Python requests" in docs[0]
        assert metadatas[0]["original_query"] == query
        assert metadatas[0]["session_id"] == "test_session"
        assert metadatas[0]["type"] == "web_search_result"

    def test_full_url_content_workflow(self, memory_service, mock_vector_store):
        """Test complete workflow of URL content embedding."""
        url_content = {
            "content": "Stripe API Documentation\n\nThe Stripe API allows you to...",
            "url": "https://stripe.com/docs/api",
            "title": "Stripe API Docs",
        }

        result = memory_service.embed_url_content(
            url_content=url_content,
            query="stripe api docs",
            session_id="stripe_session",
        )

        assert result is True

        # Verify embedding
        call_args = mock_vector_store.add_documents.call_args
        docs = call_args[1]['documents']
        metadatas = call_args[1]['metadatas']

        assert "Stripe API" in docs[0]
        assert metadatas[0]["source"] == "url_scrape"
        assert metadatas[0]["url"] == "https://stripe.com/docs/api"


class TestEdgeCases:
    """Test edge cases."""

    def test_empty_query_for_web_results(self, memory_service, mock_vector_store):
        """Test embedding with empty query."""
        web_results = [{"content": "test", "metadata": {}, "score": 1.0, "doc_id": "1"}]

        count = memory_service.embed_web_search_results("", web_results)

        # Should still embed even with empty query
        assert count == 1

    def test_malformed_web_result(self, memory_service, mock_vector_store):
        """Test handling of malformed web result."""
        web_results = [
            {
                # Missing required fields
                "score": 0.9,
            }
        ]

        # Should handle gracefully
        count = memory_service.embed_web_search_results("query", web_results)

        # Should skip malformed result
        assert count == 0

    def test_unicode_in_content(self, memory_service, mock_vector_store):
        """Test handling of unicode content."""
        url_content = {
            "content": "API文档 مستندات שָׁלוֹם",
            "url": "https://example.com",
            "title": "Unicode Title",
        }

        result = memory_service.embed_url_content(url_content, "query")

        assert result is True
