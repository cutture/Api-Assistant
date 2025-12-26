"""
Conversation Memory Service for embedding chat history in vector store.

This module manages embedding important conversation exchanges and web search
results into the vector store for long-term context retrieval.
"""

from typing import List, Dict, Optional
from datetime import datetime, timezone

import structlog

from src.core.vector_store import VectorStore, get_vector_store
from src.config import settings

logger = structlog.get_logger(__name__)


class ConversationMemoryService:
    """
    Service for managing conversation memory in vector store.

    This service:
    - Embeds helpful web search results for future retrieval
    - Optionally embeds important conversation exchanges (long-term memory)
    - Relies on 128k context window for current session (short-term memory)
    - Provides semantic search over past conversations
    """

    def __init__(
        self,
        vector_store: Optional[VectorStore] = None,
        enable_conversation_embedding: bool = False,  # Disabled by default
        enable_web_result_embedding: bool = True,  # Enabled by default
    ):
        """
        Initialize conversation memory service.

        Args:
            vector_store: Vector store instance.
            enable_conversation_embedding: Whether to embed conversations in vector DB.
            enable_web_result_embedding: Whether to embed web search results.
        """
        self._vector_store = vector_store or get_vector_store()
        self.enable_conversation_embedding = enable_conversation_embedding
        self.enable_web_result_embedding = enable_web_result_embedding

    def embed_web_search_results(
        self,
        query: str,
        web_results: List[Dict[str, any]],
        session_id: Optional[str] = None,
    ) -> int:
        """
        Embed helpful web search results into vector store.

        This allows future queries to benefit from previously fetched web content.

        Args:
            query: The original query that triggered the web search.
            web_results: List of web search result dicts.
            session_id: Optional session identifier.

        Returns:
            Number of results embedded.
        """
        if not self.enable_web_result_embedding:
            logger.debug("Web result embedding disabled")
            return 0

        if not web_results:
            return 0

        embedded_count = 0

        for result in web_results:
            try:
                content = result.get("content", "")

                # Skip results without content
                if not content:
                    logger.warning("Skipping web result with empty content")
                    continue

                metadata = result.get("metadata", {})

                # Add embedding metadata
                metadata.update({
                    "embedded_at": datetime.now(timezone.utc).isoformat(),
                    "original_query": query,
                    "session_id": session_id or "unknown",
                    "type": "web_search_result",
                })

                # Generate unique ID
                doc_id = result.get("doc_id", f"websearch_{hash(content)}")

                # Add to vector store
                self._vector_store.add_documents(
                    documents=[content],
                    metadatas=[metadata],
                    ids=[doc_id],
                )

                embedded_count += 1

            except Exception as e:
                logger.error(
                    "Failed to embed web result",
                    error=str(e),
                    url=result.get("metadata", {}).get("url"),
                )

        logger.info(
            "Embedded web search results",
            embedded=embedded_count,
            total=len(web_results),
        )

        return embedded_count

    def embed_conversation_exchange(
        self,
        user_message: str,
        assistant_response: str,
        metadata: Optional[Dict] = None,
        session_id: Optional[str] = None,
    ) -> bool:
        """
        Embed a conversation exchange into vector store.

        This is optional and disabled by default to avoid "vector DB pollution".
        Relies on 128k context window for current session memory.

        Args:
            user_message: User's message.
            assistant_response: Assistant's response.
            metadata: Optional metadata about the exchange.
            session_id: Optional session identifier.

        Returns:
            True if embedded successfully.
        """
        if not self.enable_conversation_embedding:
            logger.debug("Conversation embedding disabled (using context window)")
            return False

        try:
            # Format as Q&A for embedding
            content = f"Question: {user_message}\n\nAnswer: {assistant_response}"

            # Prepare metadata
            meta = metadata or {}
            meta.update({
                "embedded_at": datetime.now(timezone.utc).isoformat(),
                "session_id": session_id or "unknown",
                "type": "conversation_exchange",
                "user_message": user_message[:200],  # Preview
            })

            # Generate unique ID
            doc_id = f"conv_{session_id}_{hash(content)}"

            # Add to vector store
            self._vector_store.add_documents(
                documents=[content],
                metadatas=[meta],
                ids=[doc_id],
            )

            logger.info("Embedded conversation exchange", doc_id=doc_id)
            return True

        except Exception as e:
            logger.error("Failed to embed conversation", error=str(e))
            return False

    def embed_url_content(
        self,
        url_content: Dict[str, str],
        query: str,
        session_id: Optional[str] = None,
    ) -> bool:
        """
        Embed scraped URL content into vector store.

        Args:
            url_content: Dict with 'content', 'title', 'url' keys.
            query: The query that led to scraping this URL.
            session_id: Optional session identifier.

        Returns:
            True if embedded successfully.
        """
        try:
            content = url_content.get("content", "")
            if not content:
                return False

            metadata = {
                "source": "url_scrape",
                "url": url_content.get("url", ""),
                "title": url_content.get("title", ""),
                "embedded_at": datetime.now(timezone.utc).isoformat(),
                "original_query": query,
                "session_id": session_id or "unknown",
                "type": "scraped_webpage",
            }

            # Generate unique ID based on URL
            doc_id = f"url_{hash(url_content.get('url', ''))}"

            # Add to vector store
            self._vector_store.add_documents(
                documents=[content],
                metadatas=[metadata],
                ids=[doc_id],
            )

            logger.info(
                "Embedded URL content",
                url=url_content.get("url"),
                doc_id=doc_id,
            )
            return True

        except Exception as e:
            logger.error(
                "Failed to embed URL content",
                error=str(e),
                url=url_content.get("url"),
            )
            return False

    def search_conversation_history(
        self,
        query: str,
        limit: int = 5,
    ) -> List[Dict[str, any]]:
        """
        Search embedded conversation history.

        Args:
            query: Search query.
            limit: Maximum number of results.

        Returns:
            List of relevant conversation exchanges.
        """
        try:
            # Search with filter for conversation exchanges
            results = self._vector_store.search(
                query=query,
                n_results=limit,
                where={"type": "conversation_exchange"},
            )

            return results

        except Exception as e:
            logger.error("Failed to search conversation history", error=str(e))
            return []


def get_conversation_memory_service() -> ConversationMemoryService:
    """
    Get a conversation memory service instance.

    Returns:
        Configured ConversationMemoryService instance.
    """
    return ConversationMemoryService(
        enable_conversation_embedding=False,  # Disabled: rely on 128k context
        enable_web_result_embedding=True,     # Enabled: save useful web results
    )
