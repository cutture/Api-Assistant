"""
Web Search Service for fallback retrieval.

This module provides web search capabilities using DuckDuckGo
when the vector store doesn't have relevant information.
"""

from typing import List, Dict, Optional
import structlog
from duckduckgo_search import DDGS

from src.config import settings

logger = structlog.get_logger(__name__)


class WebSearchService:
    """
    Web search service using DuckDuckGo.

    Provides fallback search capabilities when vector store
    results are insufficient or irrelevant.
    """

    def __init__(self, max_results: int = 5):
        """
        Initialize web search service.

        Args:
            max_results: Maximum number of search results to return.
        """
        self.max_results = max_results
        self._ddgs = None

    @property
    def ddgs(self) -> DDGS:
        """Get or create DuckDuckGo search client."""
        if self._ddgs is None:
            self._ddgs = DDGS()
        return self._ddgs

    def search(
        self,
        query: str,
        max_results: Optional[int] = None,
        region: str = "wt-wt",  # Worldwide
        safesearch: str = "moderate",
    ) -> List[Dict[str, str]]:
        """
        Search the web using DuckDuckGo.

        Args:
            query: Search query string.
            max_results: Maximum number of results (overrides default).
            region: Search region (default: worldwide).
            safesearch: Safe search level (off, moderate, strict).

        Returns:
            List of search results with title, body, and href.

        Example:
            >>> searcher = WebSearchService()
            >>> results = searcher.search("OpenAPI specification format")
            >>> for result in results:
            ...     print(result["title"], result["href"])
        """
        if not query or not query.strip():
            logger.warning("Empty search query provided")
            return []

        max_results = max_results or self.max_results

        try:
            logger.info(
                "performing_web_search",
                query=query[:100],
                max_results=max_results,
            )

            # Perform search using DuckDuckGo
            results = []
            search_results = self.ddgs.text(
                keywords=query,
                region=region,
                safesearch=safesearch,
                max_results=max_results,
            )

            for result in search_results:
                results.append({
                    "title": result.get("title", ""),
                    "body": result.get("body", ""),
                    "href": result.get("href", ""),
                })

            logger.info(
                "web_search_complete",
                num_results=len(results),
            )

            return results

        except Exception as e:
            logger.error(
                "web_search_failed",
                error=str(e),
                query=query[:100],
            )
            # Return empty list on error - don't crash the application
            return []

    def search_to_documents(
        self,
        query: str,
        max_results: Optional[int] = None,
    ) -> List[Dict[str, any]]:
        """
        Search and format results as document-like structures.

        This formats web search results to match the structure of
        vector store documents for consistent handling.

        Args:
            query: Search query string.
            max_results: Maximum number of results.

        Returns:
            List of formatted documents with content and metadata.

        Example:
            >>> searcher = WebSearchService()
            >>> docs = searcher.search_to_documents("REST API authentication")
            >>> for doc in docs:
            ...     print(doc["content"][:100])
            ...     print(doc["metadata"]["source"])
        """
        results = self.search(query, max_results=max_results)

        documents = []
        for idx, result in enumerate(results, 1):
            # Combine title and body for content
            content = f"{result['title']}\n\n{result['body']}"

            doc = {
                "content": content,
                "metadata": {
                    "source": "web_search",
                    "url": result["href"],
                    "title": result["title"],
                    "search_rank": idx,
                    "query": query,
                },
                "score": 1.0 - (idx * 0.1),  # Decreasing relevance score
                "doc_id": f"websearch_{idx}",
            }
            documents.append(doc)

        return documents


def get_web_search_service() -> WebSearchService:
    """
    Get a web search service instance.

    Returns:
        Configured WebSearchService instance.
    """
    return WebSearchService(max_results=settings.web_search_max_results)
