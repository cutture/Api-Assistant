"""
URL Extraction and Scraping Service.

This module provides functionality to extract URLs from user messages
and scrape their content for use in RAG retrieval.
"""

import re
from typing import List, Dict, Optional
from urllib.parse import urlparse

import structlog
import httpx
from bs4 import BeautifulSoup

logger = structlog.get_logger(__name__)


class URLScraperService:
    """
    Service for extracting and scraping URLs from user messages.

    This service:
    - Extracts URLs from text using regex
    - Fetches URL content with timeout and error handling
    - Extracts readable text from HTML
    - Formats content for vector store indexing
    """

    # Regex pattern for URL extraction
    URL_PATTERN = re.compile(
        r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    )

    def __init__(
        self,
        timeout: int = 10,
        max_content_length: int = 100000,  # 100KB max
        user_agent: str = "API-Assistant-Bot/1.0",
    ):
        """
        Initialize URL scraper service.

        Args:
            timeout: Request timeout in seconds.
            max_content_length: Maximum content length to fetch (bytes).
            user_agent: User agent string for requests.
        """
        self.timeout = timeout
        self.max_content_length = max_content_length
        self.user_agent = user_agent

    def extract_urls(self, text: str) -> List[str]:
        """
        Extract all URLs from text.

        Args:
            text: Text to extract URLs from.

        Returns:
            List of extracted URLs.
        """
        urls = self.URL_PATTERN.findall(text)
        # Deduplicate while preserving order
        seen = set()
        unique_urls = []
        for url in urls:
            if url not in seen:
                seen.add(url)
                unique_urls.append(url)

        logger.info("Extracted URLs from text", num_urls=len(unique_urls))
        return unique_urls

    def scrape_url(self, url: str) -> Optional[Dict[str, str]]:
        """
        Scrape content from a URL.

        Args:
            url: URL to scrape.

        Returns:
            Dict with 'title', 'content', 'url' keys, or None if failed.
        """
        try:
            logger.info("Scraping URL", url=url)

            # Validate URL
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                logger.warning("Invalid URL format", url=url)
                return None

            # Fetch content with timeout
            headers = {"User-Agent": self.user_agent}

            with httpx.Client(timeout=self.timeout, follow_redirects=True) as client:
                response = client.get(url, headers=headers)
                response.raise_for_status()

                # Check content length
                content_length = len(response.content)
                if content_length > self.max_content_length:
                    logger.warning(
                        "Content too large, truncating",
                        url=url,
                        size=content_length,
                    )
                    content = response.content[:self.max_content_length]
                else:
                    content = response.content

                # Parse HTML
                soup = BeautifulSoup(content, 'html.parser')

                # Extract title
                title = ""
                if soup.title:
                    title = soup.title.string.strip() if soup.title.string else ""

                # Remove script and style elements
                for script in soup(["script", "style", "nav", "footer", "header"]):
                    script.decompose()

                # Get text content
                text = soup.get_text(separator="\n", strip=True)

                # Clean up whitespace
                lines = [line.strip() for line in text.split("\n")]
                text = "\n".join(line for line in lines if line)

                # Limit final text length
                if len(text) > 10000:
                    text = text[:10000] + "\n\n[Content truncated...]"

                logger.info(
                    "Successfully scraped URL",
                    url=url,
                    title=title[:50],
                    content_length=len(text),
                )

                return {
                    "title": title,
                    "content": text,
                    "url": url,
                }

        except httpx.TimeoutException:
            logger.error("URL scraping timeout", url=url)
            return None
        except httpx.HTTPStatusError as e:
            logger.error("HTTP error scraping URL", url=url, status=e.response.status_code)
            return None
        except Exception as e:
            logger.error("Failed to scrape URL", url=url, error=str(e))
            return None

    def scrape_urls(self, urls: List[str]) -> List[Dict[str, str]]:
        """
        Scrape content from multiple URLs.

        Args:
            urls: List of URLs to scrape.

        Returns:
            List of scraped content dicts (excludes failed scrapes).
        """
        results = []
        for url in urls:
            result = self.scrape_url(url)
            if result:
                results.append(result)

        logger.info("Scraped multiple URLs", total=len(urls), successful=len(results))
        return results

    def extract_and_scrape(self, text: str) -> List[Dict[str, str]]:
        """
        Extract URLs from text and scrape their content.

        Args:
            text: Text to extract URLs from.

        Returns:
            List of scraped content dicts.
        """
        urls = self.extract_urls(text)
        if not urls:
            return []

        return self.scrape_urls(urls)

    def format_for_vector_store(
        self, scraped_content: Dict[str, str]
    ) -> Dict[str, any]:
        """
        Format scraped content for vector store insertion.

        Args:
            scraped_content: Scraped content dict with title, content, url.

        Returns:
            Formatted document dict for vector store.
        """
        title = scraped_content.get("title", "")
        content = scraped_content.get("content", "")
        url = scraped_content.get("url", "")

        # Combine title and content
        full_content = f"{title}\n\n{content}" if title else content

        return {
            "content": full_content,
            "metadata": {
                "source": "url_scrape",
                "url": url,
                "title": title,
                "type": "scraped_webpage",
            },
            "score": 1.0,  # Default high relevance for user-provided URLs
            "doc_id": f"url_{hash(url)}",
        }


def get_url_scraper_service() -> URLScraperService:
    """
    Get a URL scraper service instance.

    Returns:
        Configured URLScraperService instance.
    """
    return URLScraperService()
