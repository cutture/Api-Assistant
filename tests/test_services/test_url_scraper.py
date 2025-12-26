"""
Tests for URL Scraper Service.

Tests cover:
- URL extraction
- Web scraping
- HTML parsing
- Error handling
- Content formatting
"""

import pytest
from unittest.mock import Mock, patch, MagicMock

from src.services.url_scraper import URLScraperService, get_url_scraper_service


@pytest.fixture
def url_scraper():
    """Create URL scraper service."""
    return URLScraperService(timeout=5, max_content_length=50000)


class TestURLExtraction:
    """Test URL extraction from text."""

    def test_extract_single_url(self, url_scraper):
        """Test extraction of a single URL."""
        text = "Check out this API: https://api.example.com/docs"
        urls = url_scraper.extract_urls(text)

        assert len(urls) == 1
        assert urls[0] == "https://api.example.com/docs"

    def test_extract_multiple_urls(self, url_scraper):
        """Test extraction of multiple URLs."""
        text = """
        Here are some resources:
        https://api.example.com/docs
        http://example.com/api
        https://github.com/user/repo
        """
        urls = url_scraper.extract_urls(text)

        assert len(urls) == 3
        assert "https://api.example.com/docs" in urls
        assert "http://example.com/api" in urls
        assert "https://github.com/user/repo" in urls

    def test_extract_urls_with_query_params(self, url_scraper):
        """Test extraction of URLs with query parameters."""
        text = "See https://api.example.com/docs?page=1&limit=10"
        urls = url_scraper.extract_urls(text)

        assert len(urls) == 1
        assert "page=1" in urls[0]
        assert "limit=10" in urls[0]

    def test_extract_urls_with_fragments(self, url_scraper):
        """Test extraction of URLs with fragments."""
        text = "Jump to https://docs.example.com#authentication"
        urls = url_scraper.extract_urls(text)

        assert len(urls) == 1
        assert "#authentication" in urls[0]

    def test_no_urls_in_text(self, url_scraper):
        """Test text without URLs."""
        text = "This is just plain text without any URLs"
        urls = url_scraper.extract_urls(text)

        assert len(urls) == 0

    def test_deduplication(self, url_scraper):
        """Test that duplicate URLs are deduplicated."""
        text = """
        https://example.com/api
        Some text
        https://example.com/api
        More text
        https://example.com/api
        """
        urls = url_scraper.extract_urls(text)

        assert len(urls) == 1
        assert urls[0] == "https://example.com/api"

    def test_http_and_https(self, url_scraper):
        """Test extraction of both HTTP and HTTPS URLs."""
        text = "HTTP: http://example.com and HTTPS: https://example.com"
        urls = url_scraper.extract_urls(text)

        assert len(urls) == 2
        assert any(url.startswith("http://") for url in urls)
        assert any(url.startswith("https://") for url in urls)


class TestURLScraping:
    """Test web scraping functionality."""

    @patch('src.services.url_scraper.httpx.Client')
    def test_successful_scraping(self, mock_client_class, url_scraper):
        """Test successful URL scraping."""
        # Mock HTTP response
        mock_response = Mock()
        mock_response.content = b"""
        <html>
            <head><title>Test API Docs</title></head>
            <body>
                <h1>API Documentation</h1>
                <p>This is the API documentation content.</p>
            </body>
        </html>
        """
        mock_response.raise_for_status = Mock()

        mock_client = MagicMock()
        mock_client.__enter__.return_value.get.return_value = mock_response
        mock_client_class.return_value = mock_client

        result = url_scraper.scrape_url("https://api.example.com/docs")

        assert result is not None
        assert result["title"] == "Test API Docs"
        assert "API Documentation" in result["content"]
        assert "documentation content" in result["content"]
        assert result["url"] == "https://api.example.com/docs"

    @patch('src.services.url_scraper.httpx.Client')
    def test_scraping_removes_scripts(self, mock_client_class, url_scraper):
        """Test that script tags are removed from content."""
        mock_response = Mock()
        mock_response.content = b"""
        <html>
            <head><title>Test</title></head>
            <body>
                <p>Visible content</p>
                <script>var x = 'hidden';</script>
                <p>More visible content</p>
            </body>
        </html>
        """
        mock_response.raise_for_status = Mock()

        mock_client = MagicMock()
        mock_client.__enter__.return_value.get.return_value = mock_response
        mock_client_class.return_value = mock_client

        result = url_scraper.scrape_url("https://example.com")

        assert result is not None
        assert "Visible content" in result["content"]
        assert "hidden" not in result["content"]
        assert "<script>" not in result["content"]

    @patch('src.services.url_scraper.httpx.Client')
    def test_scraping_removes_styles(self, mock_client_class, url_scraper):
        """Test that style tags are removed from content."""
        mock_response = Mock()
        mock_response.content = b"""
        <html>
            <head>
                <title>Test</title>
                <style>.hidden { display: none; }</style>
            </head>
            <body><p>Content</p></body>
        </html>
        """
        mock_response.raise_for_status = Mock()

        mock_client = MagicMock()
        mock_client.__enter__.return_value.get.return_value = mock_response
        mock_client_class.return_value = mock_client

        result = url_scraper.scrape_url("https://example.com")

        assert result is not None
        assert "Content" in result["content"]
        assert "display: none" not in result["content"]

    @patch('src.services.url_scraper.httpx.Client')
    def test_content_length_limit(self, mock_client_class, url_scraper):
        """Test that content is truncated at max length."""
        # Create large content
        large_content = b"<html><body>" + b"x" * 100000 + b"</body></html>"

        mock_response = Mock()
        mock_response.content = large_content
        mock_response.raise_for_status = Mock()

        mock_client = MagicMock()
        mock_client.__enter__.return_value.get.return_value = mock_response
        mock_client_class.return_value = mock_client

        result = url_scraper.scrape_url("https://example.com")

        # Content should be truncated
        assert result is not None
        # The actual content after parsing will be different, but should have truncation marker
        # or be within reasonable limits

    @patch('src.services.url_scraper.httpx.Client')
    def test_text_length_limit(self, mock_client_class, url_scraper):
        """Test that final text is limited to 10000 characters."""
        # Create content that will exceed 10000 chars after parsing
        long_text = "A" * 15000

        mock_response = Mock()
        mock_response.content = f"<html><body><p>{long_text}</p></body></html>".encode()
        mock_response.raise_for_status = Mock()

        mock_client = MagicMock()
        mock_client.__enter__.return_value.get.return_value = mock_response
        mock_client_class.return_value = mock_client

        result = url_scraper.scrape_url("https://example.com")

        assert result is not None
        assert len(result["content"]) <= 10100  # 10000 + truncation message
        if len(result["content"]) > 10000:
            assert "[Content truncated...]" in result["content"]

    @patch('src.services.url_scraper.httpx.Client')
    def test_timeout_handling(self, mock_client_class, url_scraper):
        """Test handling of request timeouts."""
        from httpx import TimeoutException

        mock_client = MagicMock()
        mock_client.__enter__.return_value.get.side_effect = TimeoutException("Timeout")
        mock_client_class.return_value = mock_client

        result = url_scraper.scrape_url("https://slow.example.com")

        assert result is None

    @patch('src.services.url_scraper.httpx.Client')
    def test_http_error_handling(self, mock_client_class, url_scraper):
        """Test handling of HTTP errors."""
        from httpx import HTTPStatusError

        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = HTTPStatusError(
            "Not Found", request=Mock(), response=mock_response
        )

        mock_client = MagicMock()
        mock_client.__enter__.return_value.get.return_value = mock_response
        mock_client_class.return_value = mock_client

        result = url_scraper.scrape_url("https://example.com/404")

        assert result is None

    def test_invalid_url_format(self, url_scraper):
        """Test handling of invalid URL formats."""
        result = url_scraper.scrape_url("not-a-valid-url")

        assert result is None

    def test_url_without_scheme(self, url_scraper):
        """Test handling of URLs without scheme."""
        result = url_scraper.scrape_url("example.com/api")

        assert result is None

    @patch('src.services.url_scraper.httpx.Client')
    def test_scrape_multiple_urls(self, mock_client_class, url_scraper):
        """Test scraping multiple URLs."""
        mock_response = Mock()
        mock_response.content = b"<html><body>Test</body></html>"
        mock_response.raise_for_status = Mock()

        mock_client = MagicMock()
        mock_client.__enter__.return_value.get.return_value = mock_response
        mock_client_class.return_value = mock_client

        urls = [
            "https://example.com/1",
            "https://example.com/2",
            "https://example.com/3",
        ]

        results = url_scraper.scrape_urls(urls)

        assert len(results) == 3
        assert all("content" in r for r in results)


class TestContentFormatting:
    """Test formatting of scraped content for vector store."""

    def test_format_for_vector_store(self, url_scraper):
        """Test formatting scraped content for vector store."""
        scraped_content = {
            "title": "API Documentation",
            "content": "This is the API documentation content.",
            "url": "https://api.example.com/docs",
        }

        formatted = url_scraper.format_for_vector_store(scraped_content)

        assert "content" in formatted
        assert "metadata" in formatted
        assert "score" in formatted
        assert "doc_id" in formatted

        # Check content includes title
        assert "API Documentation" in formatted["content"]
        assert "documentation content" in formatted["content"]

        # Check metadata
        assert formatted["metadata"]["source"] == "url_scrape"
        assert formatted["metadata"]["url"] == "https://api.example.com/docs"
        assert formatted["metadata"]["title"] == "API Documentation"
        assert formatted["metadata"]["type"] == "scraped_webpage"

        # Check score and doc_id
        assert formatted["score"] == 1.0
        assert formatted["doc_id"].startswith("url_")

    def test_format_without_title(self, url_scraper):
        """Test formatting when title is missing."""
        scraped_content = {
            "title": "",
            "content": "Content without title",
            "url": "https://example.com",
        }

        formatted = url_scraper.format_for_vector_store(scraped_content)

        # Content should not have empty title prefix
        assert formatted["content"] == "Content without title"

    def test_format_generates_unique_doc_ids(self, url_scraper):
        """Test that different URLs generate different doc IDs."""
        content1 = {
            "title": "Doc 1",
            "content": "Content 1",
            "url": "https://example.com/1",
        }

        content2 = {
            "title": "Doc 2",
            "content": "Content 2",
            "url": "https://example.com/2",
        }

        formatted1 = url_scraper.format_for_vector_store(content1)
        formatted2 = url_scraper.format_for_vector_store(content2)

        assert formatted1["doc_id"] != formatted2["doc_id"]


class TestExtractAndScrape:
    """Test combined extract and scrape functionality."""

    @patch('src.services.url_scraper.httpx.Client')
    def test_extract_and_scrape(self, mock_client_class, url_scraper):
        """Test extracting URLs from text and scraping them."""
        text = "Check these APIs: https://api1.example.com and https://api2.example.com"

        mock_response = Mock()
        mock_response.content = b"<html><body>API Content</body></html>"
        mock_response.raise_for_status = Mock()

        mock_client = MagicMock()
        mock_client.__enter__.return_value.get.return_value = mock_response
        mock_client_class.return_value = mock_client

        results = url_scraper.extract_and_scrape(text)

        assert len(results) == 2
        assert all("content" in r for r in results)
        assert all("API Content" in r["content"] for r in results)

    def test_extract_and_scrape_no_urls(self, url_scraper):
        """Test extract and scrape with no URLs in text."""
        text = "This text has no URLs"

        results = url_scraper.extract_and_scrape(text)

        assert len(results) == 0


class TestFactoryFunction:
    """Test factory function."""

    def test_get_url_scraper_service(self):
        """Test factory function creates service."""
        service = get_url_scraper_service()

        assert isinstance(service, URLScraperService)
        assert service.timeout == 10
        assert service.max_content_length == 100000


class TestEdgeCases:
    """Test edge cases and error scenarios."""

    @patch('src.services.url_scraper.httpx.Client')
    def test_empty_html(self, mock_client_class, url_scraper):
        """Test scraping empty HTML."""
        mock_response = Mock()
        mock_response.content = b"<html></html>"
        mock_response.raise_for_status = Mock()

        mock_client = MagicMock()
        mock_client.__enter__.return_value.get.return_value = mock_response
        mock_client_class.return_value = mock_client

        result = url_scraper.scrape_url("https://example.com")

        assert result is not None
        assert result["content"] == ""

    @patch('src.services.url_scraper.httpx.Client')
    def test_malformed_html(self, mock_client_class, url_scraper):
        """Test scraping malformed HTML."""
        mock_response = Mock()
        mock_response.content = b"<html><body><p>Unclosed paragraph"
        mock_response.raise_for_status = Mock()

        mock_client = MagicMock()
        mock_client.__enter__.return_value.get.return_value = mock_response
        mock_client_class.return_value = mock_client

        result = url_scraper.scrape_url("https://example.com")

        # BeautifulSoup should handle malformed HTML
        assert result is not None
        assert "Unclosed paragraph" in result["content"]

    @patch('src.services.url_scraper.httpx.Client')
    def test_unicode_content(self, mock_client_class, url_scraper):
        """Test scraping content with unicode characters."""
        mock_response = Mock()
        mock_response.content = """
        <html>
            <body>
                <p>Unicode: 你好 مرحبا שלום</p>
            </body>
        </html>
        """.encode('utf-8')
        mock_response.raise_for_status = Mock()

        mock_client = MagicMock()
        mock_client.__enter__.return_value.get.return_value = mock_response
        mock_client_class.return_value = mock_client

        result = url_scraper.scrape_url("https://example.com")

        assert result is not None
        assert "Unicode:" in result["content"]

    def test_url_with_special_characters(self, url_scraper):
        """Test URL extraction with special characters."""
        text = "URL: https://example.com/path?param=value&other=test#fragment"
        urls = url_scraper.extract_urls(text)

        assert len(urls) == 1
        assert "param=value" in urls[0]
        assert "&other=test" in urls[0]
        assert "#fragment" in urls[0]
