"""
URL Extraction and Scraping Service.

This module provides functionality to extract URLs from user messages
and scrape their content for use in RAG retrieval.
"""

import re
import time
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
    - Retries on DNS/network errors
    - Extracts readable text from HTML
    - Formats content for vector store indexing
    """

    # Regex pattern for URL extraction
    # Matches http/https URLs including query params (?key=value) and fragments (#section)
    URL_PATTERN = re.compile(
        r'http[s]?://[^\s<>"{}|\\^`\[\]]+'
    )

    def __init__(
        self,
        timeout: int = 15,  # Increased timeout for slow networks
        max_content_length: int = 100000,  # 100KB max
        user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        max_retries: int = 3,  # Retry up to 3 times on network errors
    ):
        """
        Initialize URL scraper service.

        Args:
            timeout: Request timeout in seconds.
            max_content_length: Maximum content length to fetch (bytes).
            user_agent: User agent string for requests.
            max_retries: Maximum number of retries on network errors.
        """
        self.timeout = timeout
        self.max_content_length = max_content_length
        self.user_agent = user_agent
        self.max_retries = max_retries

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
        Scrape content from a URL with retry logic for network errors.

        Args:
            url: URL to scrape.

        Returns:
            Dict with 'title', 'content', 'url' keys, or None if failed.
        """
        # Validate URL
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            logger.warning("Invalid URL format", url=url)
            return None

        # Retry logic for DNS and network errors
        for attempt in range(self.max_retries):
            try:
                logger.info("Scraping URL", url=url, attempt=attempt + 1)

                # Fetch content with timeout
                headers = {
                    "User-Agent": self.user_agent,
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.5",
                    "Connection": "keep-alive",
                }

                # Create client with DNS resolution and connection settings
                with httpx.Client(
                    timeout=httpx.Timeout(self.timeout, connect=10.0),
                    follow_redirects=True,
                    verify=False,  # Disable SSL verification for problematic sites
                ) as client:
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
                        title=title[:50] if title else "No title",
                        content_length=len(text),
                    )

                    return {
                        "title": title,
                        "content": text,
                        "url": url,
                    }

            except httpx.TimeoutException as e:
                logger.warning(
                    "URL scraping timeout",
                    url=url,
                    attempt=attempt + 1,
                    max_retries=self.max_retries,
                    error=str(e),
                )
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff: 1s, 2s, 4s
                    continue
                else:
                    logger.error("URL scraping failed after retries (timeout)", url=url)
                    return None

            except httpx.HTTPStatusError as e:
                logger.error("HTTP error scraping URL", url=url, status=e.response.status_code)
                return None  # Don't retry on HTTP errors (404, 403, etc.)

            except (httpx.ConnectError, httpx.NetworkError) as e:
                # DNS resolution errors (getaddrinfo failed) fall under ConnectError
                logger.warning(
                    "Network/DNS error scraping URL",
                    url=url,
                    attempt=attempt + 1,
                    max_retries=self.max_retries,
                    error=str(e),
                    error_type=type(e).__name__,
                )
                if attempt < self.max_retries - 1:
                    backoff = 2 ** attempt
                    logger.info(f"Retrying in {backoff} seconds...", url=url)
                    time.sleep(backoff)  # Exponential backoff: 1s, 2s, 4s
                    continue
                else:
                    logger.error(
                        "URL scraping failed after retries (network/DNS error)",
                        url=url,
                        error=str(e),
                    )
                    return None

            except Exception as e:
                logger.error(
                    "Unexpected error scraping URL",
                    url=url,
                    error=str(e),
                    error_type=type(e).__name__,
                )
                return None

        return None  # All retries failed

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
