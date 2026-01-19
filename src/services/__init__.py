"""
Services package for Intelligent Coding Agent.

This package contains service modules for:
- Web search (DuckDuckGo)
- URL scraping and content extraction
- Conversation memory management
- Code execution (local and Cloud Run)
- Artifact storage and management
- ZIP bundle generation
"""

from src.services.web_search import WebSearchService, get_web_search_service
from src.services.url_scraper import URLScraperService, get_url_scraper_service
from src.services.conversation_memory import (
    ConversationMemoryService,
    get_conversation_memory_service,
)
from src.services.execution_service import (
    ExecutionService,
    ExecutionResult,
    LocalExecutor,
    get_execution_service,
    create_executor_callback,
)
from src.services.artifact_service import (
    ArtifactService,
    StorageBackend,
    LocalStorageBackend,
    GCSStorageBackend,
    StoredArtifact,
    ArtifactContent,
    get_artifact_service,
)
from src.services.zip_service import (
    ZipService,
    ZipEntry,
    ZipBundle,
    get_zip_service,
)
from src.services.cleanup_service import (
    CleanupService,
    get_cleanup_service,
    run_cleanup,
)

__all__ = [
    "WebSearchService",
    "get_web_search_service",
    "URLScraperService",
    "get_url_scraper_service",
    "ConversationMemoryService",
    "get_conversation_memory_service",
    # Execution
    "ExecutionService",
    "ExecutionResult",
    "LocalExecutor",
    "get_execution_service",
    "create_executor_callback",
    # Artifacts
    "ArtifactService",
    "StorageBackend",
    "LocalStorageBackend",
    "GCSStorageBackend",
    "StoredArtifact",
    "ArtifactContent",
    "get_artifact_service",
    # ZIP
    "ZipService",
    "ZipEntry",
    "ZipBundle",
    "get_zip_service",
    # Cleanup
    "CleanupService",
    "get_cleanup_service",
    "run_cleanup",
]
