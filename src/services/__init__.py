"""
Services package for API Integration Assistant.

This package contains service modules for:
- Web search (DuckDuckGo)
- URL scraping and content extraction
- Conversation memory management
"""

from src.services.web_search import WebSearchService, get_web_search_service
from src.services.url_scraper import URLScraperService, get_url_scraper_service
from src.services.conversation_memory import (
    ConversationMemoryService,
    get_conversation_memory_service,
)

__all__ = [
    "WebSearchService",
    "get_web_search_service",
    "URLScraperService",
    "get_url_scraper_service",
    "ConversationMemoryService",
    "get_conversation_memory_service",
]
