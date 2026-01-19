"""
Sandbox Service for Intelligent Coding Agent.

Provides browser automation functionality:
- Taking screenshots of web pages
- Running UI tests
- Capturing web page content
"""

import asyncio
import base64
import structlog
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
import uuid

from src.config import get_settings
from src.services.artifact_service import ArtifactService, get_artifact_service

logger = structlog.get_logger(__name__)


@dataclass
class ScreenshotResult:
    """Result of taking a screenshot."""
    image_data: bytes
    width: int
    height: int
    url: str
    timestamp: str
    artifact_id: Optional[str] = None
    artifact_path: Optional[str] = None


@dataclass
class UITestResult:
    """Result of running UI tests."""
    passed: bool
    total_tests: int
    passed_tests: int
    failed_tests: int
    screenshots: list[ScreenshotResult]
    errors: list[str]
    duration_ms: int


@dataclass
class ViewportSize:
    """Browser viewport dimensions."""
    width: int = 1280
    height: int = 720


class SandboxService:
    """
    Service for browser-based operations using Playwright.

    Features:
    - Screenshot capture with configurable viewport
    - Full page screenshots
    - UI test execution
    - Page interaction simulation
    """

    def __init__(
        self,
        artifact_service: Optional[ArtifactService] = None,
    ):
        self.settings = get_settings()
        self.artifact_service = artifact_service or get_artifact_service()
        self._browser = None
        self._playwright = None

    async def _ensure_browser(self):
        """Ensure browser is initialized."""
        if self._browser is None:
            try:
                from playwright.async_api import async_playwright

                self._playwright = await async_playwright().start()
                self._browser = await self._playwright.chromium.launch(
                    headless=True,
                    args=[
                        "--no-sandbox",
                        "--disable-setuid-sandbox",
                        "--disable-dev-shm-usage",
                    ],
                )
                logger.info("Browser initialized")
            except ImportError:
                raise ImportError(
                    "playwright is required for sandbox service. "
                    "Install with: pip install playwright && playwright install chromium"
                )
            except Exception as e:
                logger.error("Failed to initialize browser", error=str(e))
                raise

    async def close(self):
        """Close browser and cleanup resources."""
        if self._browser:
            await self._browser.close()
            self._browser = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None
        logger.info("Browser closed")

    async def take_screenshot(
        self,
        url: str,
        viewport: Optional[ViewportSize] = None,
        full_page: bool = False,
        wait_for_selector: Optional[str] = None,
        wait_timeout_ms: int = 5000,
        user_id: Optional[str] = None,
        save_artifact: bool = True,
    ) -> ScreenshotResult:
        """
        Take a screenshot of a web page.

        Args:
            url: URL to screenshot
            viewport: Viewport dimensions
            full_page: Capture full page scroll
            wait_for_selector: CSS selector to wait for before screenshot
            wait_timeout_ms: Timeout for waiting
            user_id: User ID for artifact storage
            save_artifact: Whether to save as artifact

        Returns:
            ScreenshotResult with image data
        """
        await self._ensure_browser()

        viewport = viewport or ViewportSize()

        logger.info(
            "Taking screenshot",
            url=url,
            viewport=f"{viewport.width}x{viewport.height}",
            full_page=full_page,
        )

        page = await self._browser.new_page(
            viewport={"width": viewport.width, "height": viewport.height}
        )

        try:
            # Navigate to URL
            await page.goto(url, wait_until="networkidle", timeout=30000)

            # Wait for specific selector if provided
            if wait_for_selector:
                try:
                    await page.wait_for_selector(
                        wait_for_selector,
                        timeout=wait_timeout_ms,
                    )
                except Exception as e:
                    logger.warning(
                        "Wait for selector timeout",
                        selector=wait_for_selector,
                        error=str(e),
                    )

            # Take screenshot
            screenshot_bytes = await page.screenshot(
                full_page=full_page,
                type="png",
            )

            timestamp = datetime.now(timezone.utc).isoformat()

            result = ScreenshotResult(
                image_data=screenshot_bytes,
                width=viewport.width,
                height=viewport.height,
                url=url,
                timestamp=timestamp,
            )

            # Save as artifact if requested
            if save_artifact and user_id:
                artifact_id = str(uuid.uuid4())
                filename = f"screenshot_{artifact_id[:8]}.png"

                stored = self.artifact_service.save_artifact(
                    user_id=user_id,
                    artifact_id=artifact_id,
                    filename=filename,
                    content=screenshot_bytes,
                )

                result.artifact_id = artifact_id
                result.artifact_path = stored.file_path

            logger.info(
                "Screenshot captured",
                url=url,
                size=len(screenshot_bytes),
                artifact_id=result.artifact_id,
            )

            return result

        finally:
            await page.close()

    async def run_ui_tests(
        self,
        url: str,
        test_script: Optional[str] = None,
        viewport: Optional[ViewportSize] = None,
        user_id: Optional[str] = None,
    ) -> UITestResult:
        """
        Run UI tests on a web page.

        Args:
            url: URL to test
            test_script: Optional custom test script (JavaScript)
            viewport: Viewport dimensions
            user_id: User ID for artifact storage

        Returns:
            UITestResult with test outcomes
        """
        await self._ensure_browser()

        viewport = viewport or ViewportSize()
        start_time = datetime.now(timezone.utc)
        screenshots = []
        errors = []
        tests_passed = 0
        tests_failed = 0

        logger.info("Running UI tests", url=url)

        page = await self._browser.new_page(
            viewport={"width": viewport.width, "height": viewport.height}
        )

        try:
            # Navigate to URL
            await page.goto(url, wait_until="networkidle", timeout=30000)

            # Take initial screenshot
            initial_screenshot = await self.take_screenshot(
                url=url,
                viewport=viewport,
                user_id=user_id,
                save_artifact=True,
            )
            screenshots.append(initial_screenshot)

            # Default tests if no custom script
            if test_script is None:
                # Basic page health checks
                test_results = await self._run_default_tests(page)
                for test in test_results:
                    if test["passed"]:
                        tests_passed += 1
                    else:
                        tests_failed += 1
                        errors.append(test["error"])
            else:
                # Run custom test script
                try:
                    result = await page.evaluate(test_script)
                    if isinstance(result, dict):
                        tests_passed = result.get("passed", 0)
                        tests_failed = result.get("failed", 0)
                        errors.extend(result.get("errors", []))
                except Exception as e:
                    errors.append(f"Test script error: {str(e)}")
                    tests_failed += 1

            # Take final screenshot if tests failed
            if tests_failed > 0:
                final_screenshot = await self.take_screenshot(
                    url=url,
                    viewport=viewport,
                    user_id=user_id,
                    save_artifact=True,
                )
                screenshots.append(final_screenshot)

        except Exception as e:
            errors.append(f"UI test execution error: {str(e)}")
            tests_failed += 1

        finally:
            await page.close()

        end_time = datetime.now(timezone.utc)
        duration_ms = int((end_time - start_time).total_seconds() * 1000)

        return UITestResult(
            passed=tests_failed == 0,
            total_tests=tests_passed + tests_failed,
            passed_tests=tests_passed,
            failed_tests=tests_failed,
            screenshots=screenshots,
            errors=errors,
            duration_ms=duration_ms,
        )

    async def _run_default_tests(self, page) -> list[dict]:
        """Run default UI health checks."""
        tests = []

        # Test 1: Page title exists
        try:
            title = await page.title()
            tests.append({
                "name": "page_has_title",
                "passed": bool(title),
                "error": None if title else "Page has no title",
            })
        except Exception as e:
            tests.append({
                "name": "page_has_title",
                "passed": False,
                "error": str(e),
            })

        # Test 2: No JavaScript errors
        js_errors = []

        def handle_console(msg):
            if msg.type == "error":
                js_errors.append(msg.text)

        page.on("console", handle_console)

        # Trigger any pending errors
        await page.evaluate("() => { /* trigger pending */ }")
        await asyncio.sleep(0.5)

        tests.append({
            "name": "no_js_errors",
            "passed": len(js_errors) == 0,
            "error": "; ".join(js_errors) if js_errors else None,
        })

        # Test 3: Page is interactive
        try:
            is_interactive = await page.evaluate(
                "() => document.readyState === 'complete'"
            )
            tests.append({
                "name": "page_interactive",
                "passed": is_interactive,
                "error": None if is_interactive else "Page not fully loaded",
            })
        except Exception as e:
            tests.append({
                "name": "page_interactive",
                "passed": False,
                "error": str(e),
            })

        # Test 4: No broken images
        try:
            broken_images = await page.evaluate("""
                () => {
                    const images = document.querySelectorAll('img');
                    const broken = [];
                    images.forEach(img => {
                        if (!img.complete || img.naturalWidth === 0) {
                            broken.push(img.src);
                        }
                    });
                    return broken;
                }
            """)
            tests.append({
                "name": "no_broken_images",
                "passed": len(broken_images) == 0,
                "error": f"Broken images: {broken_images}" if broken_images else None,
            })
        except Exception as e:
            tests.append({
                "name": "no_broken_images",
                "passed": False,
                "error": str(e),
            })

        return tests

    def screenshot_to_base64(self, result: ScreenshotResult) -> str:
        """Convert screenshot to base64 data URL."""
        b64 = base64.b64encode(result.image_data).decode("utf-8")
        return f"data:image/png;base64,{b64}"


# Singleton instance
_sandbox_service: Optional[SandboxService] = None


def get_sandbox_service() -> SandboxService:
    """Get the global sandbox service instance."""
    global _sandbox_service
    if _sandbox_service is None:
        _sandbox_service = SandboxService()
    return _sandbox_service
