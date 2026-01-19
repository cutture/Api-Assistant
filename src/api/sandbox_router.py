"""
Sandbox API Router for Intelligent Coding Agent.

Provides endpoints for:
- Taking screenshots of web pages
- Running UI tests
"""

import base64
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, HttpUrl

from src.api.auth import get_current_user_optional
from src.database.models import User
from src.services.sandbox_service import (
    SandboxService,
    ViewportSize,
    get_sandbox_service,
)


router = APIRouter(prefix="/sandbox", tags=["sandbox"])


# =============================================================================
# Request/Response Models
# =============================================================================


class ViewportModel(BaseModel):
    """Viewport dimensions."""
    width: int = 1280
    height: int = 720


class ScreenshotRequest(BaseModel):
    """Request model for screenshot."""
    url: str
    viewport: Optional[ViewportModel] = None
    full_page: bool = False
    wait_for_selector: Optional[str] = None
    wait_timeout_ms: int = 5000
    save_artifact: bool = True


class ScreenshotResponse(BaseModel):
    """Response model for screenshot."""
    width: int
    height: int
    url: str
    timestamp: str
    image_base64: str
    artifact_id: Optional[str] = None


class UITestRequest(BaseModel):
    """Request model for UI tests."""
    url: str
    test_script: Optional[str] = None
    viewport: Optional[ViewportModel] = None


class UITestResponse(BaseModel):
    """Response model for UI tests."""
    passed: bool
    total_tests: int
    passed_tests: int
    failed_tests: int
    screenshots: list[ScreenshotResponse]
    errors: list[str]
    duration_ms: int


# =============================================================================
# Endpoints
# =============================================================================


@router.post("/screenshot", response_model=ScreenshotResponse)
async def take_screenshot(
    request: ScreenshotRequest,
    current_user: Optional[User] = Depends(get_current_user_optional),
    sandbox_service: SandboxService = Depends(get_sandbox_service),
):
    """
    Take a screenshot of a web page.

    - **url**: URL to screenshot
    - **viewport**: Optional viewport dimensions (width, height)
    - **full_page**: Capture full page (scrolling)
    - **wait_for_selector**: CSS selector to wait for before capture
    - **save_artifact**: Save screenshot as artifact
    """
    try:
        viewport = None
        if request.viewport:
            viewport = ViewportSize(
                width=request.viewport.width,
                height=request.viewport.height,
            )

        user_id = current_user.id if current_user else "anonymous"

        result = await sandbox_service.take_screenshot(
            url=request.url,
            viewport=viewport,
            full_page=request.full_page,
            wait_for_selector=request.wait_for_selector,
            wait_timeout_ms=request.wait_timeout_ms,
            user_id=user_id if request.save_artifact else None,
            save_artifact=request.save_artifact,
        )

        # Convert image to base64
        image_base64 = base64.b64encode(result.image_data).decode("utf-8")

        return ScreenshotResponse(
            width=result.width,
            height=result.height,
            url=result.url,
            timestamp=result.timestamp,
            image_base64=image_base64,
            artifact_id=result.artifact_id,
        )

    except ImportError as e:
        raise HTTPException(
            status_code=503,
            detail="Playwright not installed. Screenshot service unavailable.",
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Screenshot failed: {str(e)}",
        )


@router.post("/test-ui", response_model=UITestResponse)
async def run_ui_tests(
    request: UITestRequest,
    current_user: Optional[User] = Depends(get_current_user_optional),
    sandbox_service: SandboxService = Depends(get_sandbox_service),
):
    """
    Run UI tests on a web page.

    - **url**: URL to test
    - **test_script**: Optional custom JavaScript test script
    - **viewport**: Optional viewport dimensions
    """
    try:
        viewport = None
        if request.viewport:
            viewport = ViewportSize(
                width=request.viewport.width,
                height=request.viewport.height,
            )

        user_id = current_user.id if current_user else "anonymous"

        result = await sandbox_service.run_ui_tests(
            url=request.url,
            test_script=request.test_script,
            viewport=viewport,
            user_id=user_id,
        )

        # Convert screenshots to response format
        screenshots = []
        for screenshot in result.screenshots:
            image_base64 = base64.b64encode(screenshot.image_data).decode("utf-8")
            screenshots.append(ScreenshotResponse(
                width=screenshot.width,
                height=screenshot.height,
                url=screenshot.url,
                timestamp=screenshot.timestamp,
                image_base64=image_base64,
                artifact_id=screenshot.artifact_id,
            ))

        return UITestResponse(
            passed=result.passed,
            total_tests=result.total_tests,
            passed_tests=result.passed_tests,
            failed_tests=result.failed_tests,
            screenshots=screenshots,
            errors=result.errors,
            duration_ms=result.duration_ms,
        )

    except ImportError as e:
        raise HTTPException(
            status_code=503,
            detail="Playwright not installed. UI testing service unavailable.",
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"UI tests failed: {str(e)}",
        )
