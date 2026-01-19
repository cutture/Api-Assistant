"""
Services package for Intelligent Coding Agent.

This package contains service modules for:
- Web search (DuckDuckGo)
- URL scraping and content extraction
- Conversation memory management
- Code execution (local and Cloud Run)
- Artifact storage and management
- ZIP bundle generation
- Code diff generation
- Browser sandbox (screenshots, UI testing)
- Live preview management
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
from src.services.diff_service import (
    DiffService,
    DiffResult,
    DiffStats,
    get_diff_service,
)
from src.services.sandbox_service import (
    SandboxService,
    ScreenshotResult,
    UITestResult,
    ViewportSize,
    get_sandbox_service,
)
from src.services.preview_service import (
    PreviewService,
    PreviewSession,
    get_preview_service,
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
    # Diff
    "DiffService",
    "DiffResult",
    "DiffStats",
    "get_diff_service",
    # Sandbox
    "SandboxService",
    "ScreenshotResult",
    "UITestResult",
    "ViewportSize",
    "get_sandbox_service",
    # Preview
    "PreviewService",
    "PreviewSession",
    "get_preview_service",
]
