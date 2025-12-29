"""
AI Chat Service with LLM integration, URL scraping, and dynamic indexing.

This service provides a complete AI chat assistant that can:
- Generate intelligent responses using LLMs (Groq/Ollama)
- Extract and scrape URLs from user messages
- Dynamically index scraped content
- Search existing indexed documents for context
- Maintain conversation history
- Generate code examples
"""

from typing import List, Dict, Optional
from datetime import datetime, timezone

import structlog

from src.core.llm_client import get_llm_client
from src.core.vector_store import get_vector_store
from src.services.url_scraper import get_url_scraper_service
from src.services.conversation_memory import get_conversation_memory_service

logger = structlog.get_logger(__name__)


class ChatService:
    """
    AI Chat Service for intelligent API documentation assistance.

    Features:
    - LLM-powered response generation
    - Dynamic URL fetching and indexing
    - Context retrieval from vector store
    - Code generation capabilities
    - Conversation history management
    """

    def __init__(
        self,
        agent_type: str = "general",
        max_context_results: int = 5,
        enable_url_scraping: bool = True,
        enable_auto_indexing: bool = True,
    ):
        """
        Initialize chat service.

        Args:
            agent_type: LLM agent type ("general", "code", "reasoning")
            max_context_results: Maximum search results to include as context
            enable_url_scraping: Enable automatic URL extraction and scraping
            enable_auto_indexing: Enable automatic indexing of scraped content
        """
        self.llm_client = get_llm_client(agent_type=agent_type)
        self.vector_store = get_vector_store()
        self.url_scraper = get_url_scraper_service()
        self.memory_service = get_conversation_memory_service()

        self.max_context_results = max_context_results
        self.enable_url_scraping = enable_url_scraping
        self.enable_auto_indexing = enable_auto_indexing

        logger.info(
            "chat_service_initialized",
            agent_type=agent_type,
            url_scraping=enable_url_scraping,
            auto_indexing=enable_auto_indexing,
        )

    async def generate_response(
        self,
        user_message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        session_id: Optional[str] = None,
    ) -> Dict[str, any]:
        """
        Generate an AI response to a user message.

        This method:
        1. Extracts and scrapes any URLs in the message
        2. Dynamically indexes scraped content
        3. Searches vector store for relevant context
        4. Generates LLM response with context
        5. Returns response with metadata

        Args:
            user_message: User's message
            conversation_history: Previous conversation messages
            session_id: Optional session identifier

        Returns:
            Dict with 'response', 'sources', 'scraped_urls', 'indexed_docs'
        """
        try:
            logger.info(
                "chat_generate_request",
                message_length=len(user_message),
                session_id=session_id,
            )

            # Step 1: Extract and scrape URLs
            scraped_content = []
            indexed_count = 0

            if self.enable_url_scraping:
                urls = self.url_scraper.extract_urls(user_message)

                if urls:
                    logger.info("chat_extracting_urls", url_count=len(urls))
                    scraped_content = self.url_scraper.scrape_urls(urls)

                    # Step 2: Dynamically index scraped content
                    if self.enable_auto_indexing and scraped_content:
                        for content in scraped_content:
                            success = self.memory_service.embed_url_content(
                                url_content=content,
                                query=user_message,
                                session_id=session_id,
                            )
                            if success:
                                indexed_count += 1

                        logger.info(
                            "chat_indexed_urls",
                            indexed=indexed_count,
                            total=len(scraped_content),
                        )

            # Step 3: Search vector store for relevant context
            search_results = self.vector_store.search(
                query=user_message,
                n_results=self.max_context_results,
            )

            logger.info("chat_search_complete", results=len(search_results))

            # Step 4: Build context for LLM
            context = self._build_context(search_results, scraped_content)

            # Step 5: Generate LLM response
            system_prompt = self._build_system_prompt(context)

            # Build messages for chat
            messages = []

            # Add conversation history if provided
            if conversation_history:
                messages.extend(conversation_history[-10:])  # Last 10 messages

            # Add current message
            user_prompt = self._build_user_prompt(user_message, context)

            # Generate response
            response_text = self.llm_client.generate(
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=0.7,
                max_tokens=2048,
                timeout_seconds=120,
            )

            logger.info(
                "chat_response_generated",
                response_length=len(response_text),
                session_id=session_id,
            )

            # Step 6: Format sources
            sources = self._format_sources(search_results, scraped_content)

            return {
                "response": response_text,
                "sources": sources,
                "scraped_urls": [c["url"] for c in scraped_content],
                "indexed_docs": indexed_count,
                "context_results": len(search_results),
            }

        except Exception as e:
            logger.error("chat_generation_failed", error=str(e), exc_info=e)
            raise

    async def generate_response_stream(
        self,
        user_message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        session_id: Optional[str] = None,
    ):
        """
        Generate a streaming AI response.

        Similar to generate_response but streams chunks as they're generated.

        Yields:
            Chunks of response text
        """
        try:
            # Same URL scraping and indexing as non-streaming
            scraped_content = []
            if self.enable_url_scraping:
                urls = self.url_scraper.extract_urls(user_message)
                if urls:
                    scraped_content = self.url_scraper.scrape_urls(urls)
                    if self.enable_auto_indexing:
                        for content in scraped_content:
                            self.memory_service.embed_url_content(
                                url_content=content,
                                query=user_message,
                                session_id=session_id,
                            )

            # Search for context
            search_results = self.vector_store.search(
                query=user_message,
                n_results=self.max_context_results,
            )

            # Build prompts
            context = self._build_context(search_results, scraped_content)
            system_prompt = self._build_system_prompt(context)
            user_prompt = self._build_user_prompt(user_message, context)

            # Stream response
            for chunk in self.llm_client.generate_stream(
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=0.7,
                max_tokens=2048,
            ):
                yield chunk

        except Exception as e:
            logger.error("chat_streaming_failed", error=str(e))
            raise

    def _build_context(
        self,
        search_results: List[Dict],
        scraped_content: List[Dict],
    ) -> str:
        """
        Build context string from search results and scraped content.

        Args:
            search_results: Vector store search results
            scraped_content: Scraped URL content

        Returns:
            Formatted context string
        """
        context_parts = []

        # Add scraped content (highest priority - user provided)
        if scraped_content:
            context_parts.append("## Newly Scraped Content (User Provided URLs):\n")
            for i, content in enumerate(scraped_content, 1):
                context_parts.append(
                    f"### Source {i}: {content.get('title', 'Untitled')}\n"
                    f"URL: {content.get('url')}\n"
                    f"{content.get('content', '')[:2000]}\n"  # Limit length
                )

        # Add existing indexed content
        if search_results:
            context_parts.append("\n## Existing Indexed API Documentation:\n")
            for i, result in enumerate(search_results, 1):
                metadata = result.get("metadata", {})
                content = result.get("content", "")
                score = result.get("score", 0)

                # Format metadata
                meta_str = ""
                if metadata.get("method"):
                    meta_str += f"Method: {metadata['method']}, "
                if metadata.get("endpoint"):
                    meta_str += f"Endpoint: {metadata['endpoint']}, "
                if metadata.get("api_name"):
                    meta_str += f"API: {metadata['api_name']}"

                context_parts.append(
                    f"### Result {i} (Score: {score:.2f}):\n"
                    f"{meta_str}\n"
                    f"{content[:1000]}\n"  # Limit length
                )

        if not context_parts:
            return "No relevant context found. Please answer based on general API best practices."

        return "\n".join(context_parts)

    def _build_system_prompt(self, context: str) -> str:
        """Build system prompt with context."""
        return f"""You are an expert API documentation assistant. Your role is to help users understand and work with APIs by:

1. Analyzing API specifications and documentation
2. Explaining authentication methods and endpoints
3. Generating code examples in Python, JavaScript, cURL, etc.
4. Providing best practices for API integration
5. Answering questions about API usage

When generating code examples:
- Use clear, well-commented code
- Include error handling
- Show practical, working examples
- Specify any required dependencies

Here is the relevant context from the indexed API documentation:

{context}

Use this context to provide accurate, specific answers. If the context doesn't contain enough information, say so and provide general guidance based on API best practices."""

    def _build_user_prompt(self, user_message: str, context: str) -> str:
        """Build user prompt."""
        # Check if user is asking for code
        code_keywords = ["write", "generate", "create", "code", "script", "example", "show me"]
        asking_for_code = any(keyword in user_message.lower() for keyword in code_keywords)

        if asking_for_code:
            return f"""{user_message}

Please provide a complete, working code example with:
1. All necessary imports
2. Clear comments explaining each step
3. Error handling
4. Example usage/output

Base your example on the provided API documentation context."""
        else:
            return user_message

    def _format_sources(
        self,
        search_results: List[Dict],
        scraped_content: List[Dict],
    ) -> List[Dict]:
        """
        Format sources for response metadata.

        Args:
            search_results: Vector store search results
            scraped_content: Scraped URL content

        Returns:
            List of source dicts with type, title, url, score
        """
        sources = []

        # Add scraped sources
        for content in scraped_content:
            sources.append({
                "type": "scraped_url",
                "title": content.get("title", "Untitled"),
                "url": content.get("url", ""),
                "score": 1.0,  # User-provided URLs are highest priority
            })

        # Add indexed sources
        for result in search_results:
            metadata = result.get("metadata", {})
            sources.append({
                "type": "indexed_doc",
                "title": metadata.get("endpoint") or metadata.get("title", "API Documentation"),
                "url": metadata.get("url", ""),
                "api_name": metadata.get("api_name", ""),
                "method": metadata.get("method", ""),
                "score": result.get("score", 0),
            })

        return sources


def get_chat_service(
    agent_type: str = "general",
    enable_url_scraping: bool = True,
    enable_auto_indexing: bool = True,
) -> ChatService:
    """
    Get a configured chat service instance.

    Args:
        agent_type: LLM agent type
        enable_url_scraping: Enable URL extraction and scraping
        enable_auto_indexing: Enable automatic indexing of scraped content

    Returns:
        Configured ChatService instance
    """
    return ChatService(
        agent_type=agent_type,
        max_context_results=5,
        enable_url_scraping=enable_url_scraping,
        enable_auto_indexing=enable_auto_indexing,
    )
