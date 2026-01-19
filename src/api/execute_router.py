"""
Execute API Router - Code generation and execution endpoints.

Provides endpoints for:
- Generating and executing code
- Retrieving execution status and results
- Getting diffs between attempts
- Retrying failed executions
"""

from datetime import datetime
from typing import Optional

import structlog
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.auth import get_current_user_optional
from src.database.connection import get_db
from src.database.models import (
    CodeExecution,
    ExecutionAttempt,
    ExecutionStatus,
    OutputType,
    User,
)
from src.agents.validator import ValidationLoop, ValidationStatus, create_validation_loop
from src.core.llm_router import get_llm_router

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/execute", tags=["execute"])


# Request/Response Models
class ExecuteRequest(BaseModel):
    """Request to generate and execute code."""
    prompt: str = Field(..., description="Natural language description of code to generate")
    language: Optional[str] = Field(None, description="Target language (auto-detect if not provided)")
    session_id: Optional[str] = Field(None, description="Session to associate execution with")
    context_artifacts: Optional[list[str]] = Field(None, description="Artifact IDs for context")
    llm_preference: Optional[str] = Field("balanced", description="'fast', 'balanced', or 'quality'")
    output_preference: Optional[str] = Field("snippet", description="'snippet', 'zip', or 'pr'")
    skip_tests: bool = Field(False, description="Skip test generation")


class ExecuteResponse(BaseModel):
    """Response from execute endpoint."""
    execution_id: str
    status: str
    estimated_time_seconds: int


class ExecutionStatusResponse(BaseModel):
    """Response with execution status and results."""
    id: str
    status: str
    attempt: int
    language: str
    complexity_score: Optional[int]
    llm_provider: Optional[str]
    llm_model: Optional[str]
    code: Optional[str]
    tests: Optional[str]
    test_passed: Optional[bool]
    lint_passed: Optional[bool]
    security_passed: Optional[bool]
    stdout: Optional[str]
    stderr: Optional[str]
    quality_score: Optional[int]
    output_type: Optional[str]
    output_artifact_id: Optional[str]
    created_at: str
    completed_at: Optional[str]


class ExecutionDiffResponse(BaseModel):
    """Response with diff between attempts."""
    from_attempt: int
    to_attempt: int
    unified_diff: str
    changes_summary: str


class RetryRequest(BaseModel):
    """Request to retry a failed execution."""
    custom_prompt: Optional[str] = Field(None, description="Optional additional instructions")


class ExecutionListItem(BaseModel):
    """Summary of an execution for list view."""
    id: str
    prompt: str
    language: str
    status: str
    attempt_number: int
    quality_score: Optional[int]
    created_at: str


class ExecutionListResponse(BaseModel):
    """Response with list of executions."""
    executions: list[ExecutionListItem]
    total: int
    page: int
    limit: int


# Background task storage (in-memory for now, would use Redis in production)
_running_executions: dict[str, ValidationLoop] = {}


async def run_execution_background(
    execution_id: str,
    request: ExecuteRequest,
    db: AsyncSession,
):
    """Background task to run code generation and validation."""
    logger.info("background_execution_started", execution_id=execution_id)

    try:
        # Create validation loop
        loop = create_validation_loop()
        _running_executions[execution_id] = loop

        # Update status to running
        execution = await db.get(CodeExecution, execution_id)
        if execution:
            execution.status = ExecutionStatus.RUNNING.value
            await db.commit()

        # Run the validation loop
        result = loop.run(
            prompt=request.prompt,
            language=request.language,
            skip_tests=request.skip_tests,
        )

        # Update execution with results
        execution = await db.get(CodeExecution, execution_id)
        if execution:
            execution.generated_code = result.final_code
            execution.generated_tests = result.final_tests
            execution.status = result.status.value
            execution.attempt_number = result.total_attempts
            execution.complexity_score = result.complexity_score
            execution.llm_provider = result.llm_provider
            execution.llm_model = result.llm_model
            execution.quality_score = result.quality_score

            # Set validation results from final attempt
            if result.attempts:
                final = result.attempts[-1]
                for signal in final.validation_signals:
                    if signal.name == "tests":
                        execution.test_passed = signal.passed
                    elif signal.name == "lint":
                        execution.lint_passed = signal.passed
                    elif signal.name == "security":
                        execution.security_passed = signal.passed

                if final.execution_result:
                    execution.stdout = final.execution_result.stdout
                    execution.stderr = final.execution_result.stderr
                    execution.execution_time_ms = final.execution_result.execution_time_ms

            execution.completed_at = datetime.utcnow()
            execution.output_type = request.output_preference

            # Save attempt history
            for attempt in result.attempts:
                attempt_record = ExecutionAttempt(
                    execution_id=execution_id,
                    attempt_number=attempt.attempt_number,
                    code_version=attempt.code,
                    diff_from_previous=attempt.diff_from_previous,
                    error_type=attempt.error_type,
                    error_message=attempt.error_message,
                    test_passed=any(s.name == "tests" and s.passed for s in attempt.validation_signals),
                    lint_passed=any(s.name == "lint" and s.passed for s in attempt.validation_signals),
                    security_passed=any(s.name == "security" and s.passed for s in attempt.validation_signals),
                    started_at=attempt.started_at,
                    completed_at=attempt.completed_at,
                )
                db.add(attempt_record)

            await db.commit()

        logger.info(
            "background_execution_completed",
            execution_id=execution_id,
            status=result.status.value,
            attempts=result.total_attempts,
        )

    except Exception as e:
        logger.error(
            "background_execution_failed",
            execution_id=execution_id,
            error=str(e),
        )
        # Update status to failed
        execution = await db.get(CodeExecution, execution_id)
        if execution:
            execution.status = ExecutionStatus.FAILED.value
            execution.stderr = str(e)
            execution.completed_at = datetime.utcnow()
            await db.commit()

    finally:
        # Clean up
        if execution_id in _running_executions:
            del _running_executions[execution_id]


@router.post("", response_model=ExecuteResponse)
async def execute_code(
    request: ExecuteRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """
    Generate and execute code from natural language prompt.

    This endpoint:
    1. Creates an execution record
    2. Starts background code generation
    3. Returns immediately with execution ID

    Use GET /execute/{id} to check status and get results.
    """
    # Estimate complexity for time estimate
    router_instance = get_llm_router()
    complexity = router_instance.analyze_complexity(request.prompt)

    # Estimate time based on complexity
    time_estimate = 10 + (complexity.score * 5)  # Base 10s + 5s per complexity point

    # Create execution record
    execution = CodeExecution(
        user_id=current_user.id if current_user else None,
        session_id=request.session_id,
        prompt=request.prompt,
        language=request.language or "python",
        complexity_score=complexity.score,
        status=ExecutionStatus.PENDING.value,
    )
    db.add(execution)
    await db.commit()
    await db.refresh(execution)

    logger.info(
        "execution_created",
        execution_id=execution.id,
        complexity=complexity.score,
        user_id=current_user.id if current_user else None,
    )

    # Start background execution
    background_tasks.add_task(
        run_execution_background,
        execution.id,
        request,
        db,
    )

    return ExecuteResponse(
        execution_id=execution.id,
        status="queued",
        estimated_time_seconds=time_estimate,
    )


@router.get("/{execution_id}", response_model=ExecutionStatusResponse)
async def get_execution_status(
    execution_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """Get execution status and results."""
    execution = await db.get(CodeExecution, execution_id)

    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")

    # Check ownership if authenticated
    if current_user and execution.user_id and execution.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this execution")

    return ExecutionStatusResponse(
        id=execution.id,
        status=execution.status,
        attempt=execution.attempt_number,
        language=execution.language,
        complexity_score=execution.complexity_score,
        llm_provider=execution.llm_provider,
        llm_model=execution.llm_model,
        code=execution.generated_code,
        tests=execution.generated_tests,
        test_passed=execution.test_passed,
        lint_passed=execution.lint_passed,
        security_passed=execution.security_passed,
        stdout=execution.stdout,
        stderr=execution.stderr,
        quality_score=execution.quality_score,
        output_type=execution.output_type,
        output_artifact_id=execution.output_artifact_id,
        created_at=execution.created_at.isoformat(),
        completed_at=execution.completed_at.isoformat() if execution.completed_at else None,
    )


@router.get("/{execution_id}/diff", response_model=ExecutionDiffResponse)
async def get_execution_diff(
    execution_id: str,
    from_attempt: int = 1,
    to_attempt: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
):
    """Get diff between execution attempts."""
    from sqlalchemy import select

    # Get the execution
    execution = await db.get(CodeExecution, execution_id)
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")

    # Get attempts
    stmt = (
        select(ExecutionAttempt)
        .where(ExecutionAttempt.execution_id == execution_id)
        .order_by(ExecutionAttempt.attempt_number)
    )
    result = await db.execute(stmt)
    attempts = result.scalars().all()

    if not attempts:
        raise HTTPException(status_code=404, detail="No attempts found")

    # Default to_attempt to latest
    if to_attempt is None:
        to_attempt = attempts[-1].attempt_number

    # Find the specific attempts
    from_attempt_record = next((a for a in attempts if a.attempt_number == from_attempt), None)
    to_attempt_record = next((a for a in attempts if a.attempt_number == to_attempt), None)

    if not from_attempt_record or not to_attempt_record:
        raise HTTPException(status_code=404, detail="Attempt not found")

    # Generate diff if not stored
    diff = to_attempt_record.diff_from_previous
    if not diff and from_attempt_record.code_version and to_attempt_record.code_version:
        import difflib
        from_lines = from_attempt_record.code_version.splitlines(keepends=True)
        to_lines = to_attempt_record.code_version.splitlines(keepends=True)
        diff = "".join(difflib.unified_diff(
            from_lines, to_lines,
            fromfile=f"attempt_{from_attempt}",
            tofile=f"attempt_{to_attempt}",
        ))

    # Generate summary
    additions = diff.count("\n+") if diff else 0
    deletions = diff.count("\n-") if diff else 0
    summary = f"{additions} additions, {deletions} deletions"

    return ExecutionDiffResponse(
        from_attempt=from_attempt,
        to_attempt=to_attempt,
        unified_diff=diff or "",
        changes_summary=summary,
    )


@router.post("/{execution_id}/retry", response_model=ExecuteResponse)
async def retry_execution(
    execution_id: str,
    request: RetryRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """Manually retry a failed execution."""
    # Get original execution
    original = await db.get(CodeExecution, execution_id)
    if not original:
        raise HTTPException(status_code=404, detail="Execution not found")

    # Check ownership
    if current_user and original.user_id and original.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Create new execution based on original
    prompt = original.prompt
    if request.custom_prompt:
        prompt = f"{prompt}\n\nAdditional instructions: {request.custom_prompt}"

    new_request = ExecuteRequest(
        prompt=prompt,
        language=original.language,
        session_id=original.session_id,
        output_preference=original.output_type,
    )

    # Create new execution
    execution = CodeExecution(
        user_id=original.user_id,
        session_id=original.session_id,
        prompt=prompt,
        language=original.language,
        status=ExecutionStatus.PENDING.value,
    )
    db.add(execution)
    await db.commit()
    await db.refresh(execution)

    # Start background execution
    background_tasks.add_task(
        run_execution_background,
        execution.id,
        new_request,
        db,
    )

    return ExecuteResponse(
        execution_id=execution.id,
        status="queued",
        estimated_time_seconds=30,
    )


@router.get("s", response_model=ExecutionListResponse)
async def list_executions(
    session_id: Optional[str] = None,
    status: Optional[str] = None,
    language: Optional[str] = None,
    page: int = 1,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """List user's executions with optional filters."""
    from sqlalchemy import select, func

    # Build query
    query = select(CodeExecution)

    # Filter by user if authenticated
    if current_user:
        query = query.where(CodeExecution.user_id == current_user.id)

    # Apply filters
    if session_id:
        query = query.where(CodeExecution.session_id == session_id)
    if status:
        query = query.where(CodeExecution.status == status)
    if language:
        query = query.where(CodeExecution.language == language)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Apply pagination
    query = query.order_by(CodeExecution.created_at.desc())
    query = query.offset((page - 1) * limit).limit(limit)

    result = await db.execute(query)
    executions = result.scalars().all()

    return ExecutionListResponse(
        executions=[
            ExecutionListItem(
                id=e.id,
                prompt=e.prompt[:100] + "..." if len(e.prompt) > 100 else e.prompt,
                language=e.language,
                status=e.status,
                attempt_number=e.attempt_number,
                quality_score=e.quality_score,
                created_at=e.created_at.isoformat(),
            )
            for e in executions
        ],
        total=total,
        page=page,
        limit=limit,
    )
