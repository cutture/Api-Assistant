"""
Security scanning API router.

Provides endpoints for scanning code and dependencies for security vulnerabilities.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from src.api.auth import get_current_user_optional
from src.services.security_service import (
    SecurityService,
    get_security_service,
)


router = APIRouter(prefix="/security", tags=["security"])


class CodeScanRequest(BaseModel):
    """Request to scan code for vulnerabilities."""
    code: str = Field(..., description="Source code to scan")
    language: str = Field(..., description="Programming language (python, javascript, etc.)")
    filename: Optional[str] = Field(None, description="Optional filename for context")


class DependencyScanRequest(BaseModel):
    """Request to scan dependencies for vulnerabilities."""
    package_file: str = Field(..., description="Contents of package file (requirements.txt, package.json)")
    package_type: str = Field(..., description="Type of package manager (pip, npm, cargo)")


class VulnerabilityResponse(BaseModel):
    """A single vulnerability finding."""
    type: str
    severity: str
    message: str
    line: Optional[int] = None
    column: Optional[int] = None
    code_snippet: Optional[str] = None
    fix_suggestion: Optional[str] = None
    cwe_id: Optional[str] = None
    owasp_category: Optional[str] = None


class ScanCountsResponse(BaseModel):
    """Counts by severity level."""
    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0
    info: int = 0


class ScanResultResponse(BaseModel):
    """Response from a security scan."""
    passed: bool = Field(..., description="Whether scan passed (no high/critical issues)")
    vulnerabilities: list[VulnerabilityResponse] = Field(default_factory=list)
    risk_score: int = Field(..., description="Risk score 0-100")
    scan_duration_ms: int = Field(..., description="Scan duration in milliseconds")
    scanner_used: str = Field(..., description="Scanner that was used")
    blocked: bool = Field(..., description="Whether execution should be blocked")
    summary: str = Field(..., description="Human-readable summary")
    counts: ScanCountsResponse = Field(default_factory=ScanCountsResponse)


@router.post("/scan", response_model=ScanResultResponse)
async def scan_code(
    request: CodeScanRequest,
    user: Optional[dict] = Depends(get_current_user_optional),
    security_service: SecurityService = Depends(get_security_service),
) -> ScanResultResponse:
    """
    Scan code for security vulnerabilities.

    Performs static analysis to detect common security issues including:
    - SQL injection
    - XSS (Cross-Site Scripting)
    - Command injection
    - Hardcoded secrets
    - Insecure cryptography
    - And more...

    Returns a list of vulnerabilities with severity levels and fix suggestions.
    """
    try:
        result = await security_service.scan_code(
            code=request.code,
            language=request.language,
            filename=request.filename,
        )
        result_dict = result.to_dict()
        return ScanResultResponse(
            passed=result_dict["passed"],
            vulnerabilities=[VulnerabilityResponse(**v) for v in result_dict["vulnerabilities"]],
            risk_score=result_dict["risk_score"],
            scan_duration_ms=result_dict["scan_duration_ms"],
            scanner_used=result_dict["scanner_used"],
            blocked=result_dict["blocked"],
            summary=result_dict["summary"],
            counts=ScanCountsResponse(**result_dict["counts"]),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scan failed: {str(e)}")


@router.post("/scan/dependencies", response_model=ScanResultResponse)
async def scan_dependencies(
    request: DependencyScanRequest,
    user: Optional[dict] = Depends(get_current_user_optional),
    security_service: SecurityService = Depends(get_security_service),
) -> ScanResultResponse:
    """
    Scan dependencies for known vulnerabilities.

    Checks package files (requirements.txt, package.json) against
    vulnerability databases to find packages with known security issues.

    Supports:
    - pip (Python)
    - npm (JavaScript/TypeScript)
    """
    if request.package_type not in ("pip", "npm"):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported package type: {request.package_type}. Supported: pip, npm"
        )

    try:
        result = await security_service.scan_dependencies(
            package_file=request.package_file,
            package_type=request.package_type,
        )
        result_dict = result.to_dict()
        return ScanResultResponse(
            passed=result_dict["passed"],
            vulnerabilities=[VulnerabilityResponse(**v) for v in result_dict["vulnerabilities"]],
            risk_score=result_dict["risk_score"],
            scan_duration_ms=result_dict["scan_duration_ms"],
            scanner_used=result_dict["scanner_used"],
            blocked=result_dict["blocked"],
            summary=result_dict["summary"],
            counts=ScanCountsResponse(**result_dict["counts"]),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Dependency scan failed: {str(e)}")


@router.get("/scan/{execution_id}", response_model=ScanResultResponse)
async def get_execution_security_scan(
    execution_id: str,
    user: Optional[dict] = Depends(get_current_user_optional),
) -> ScanResultResponse:
    """
    Get security scan results for a specific code execution.

    Returns the security scan that was performed during the execution's
    validation loop.
    """
    # TODO: Implement fetching from database when execution service stores results
    raise HTTPException(
        status_code=501,
        detail="Retrieving execution security scans not yet implemented"
    )


@router.get("/supported-languages")
async def get_supported_languages() -> dict:
    """
    Get list of languages supported for security scanning.
    """
    return {
        "languages": [
            {
                "id": "python",
                "name": "Python",
                "aliases": ["py"],
                "scanners": ["pattern_matcher", "bandit"],
            },
            {
                "id": "javascript",
                "name": "JavaScript",
                "aliases": ["js", "jsx"],
                "scanners": ["pattern_matcher"],
            },
            {
                "id": "typescript",
                "name": "TypeScript",
                "aliases": ["ts", "tsx"],
                "scanners": ["pattern_matcher"],
            },
            {
                "id": "java",
                "name": "Java",
                "aliases": [],
                "scanners": ["pattern_matcher"],
            },
            {
                "id": "go",
                "name": "Go",
                "aliases": ["golang"],
                "scanners": ["pattern_matcher"],
            },
            {
                "id": "csharp",
                "name": "C#",
                "aliases": ["cs", "c#"],
                "scanners": ["pattern_matcher"],
            },
        ],
        "dependency_scanners": [
            {"type": "pip", "name": "Python pip", "file": "requirements.txt"},
            {"type": "npm", "name": "Node.js npm", "file": "package.json"},
        ],
    }
