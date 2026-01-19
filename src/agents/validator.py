"""
Validation Loop Orchestrator for the Intelligent Coding Agent.

This orchestrator manages the iterative refinement loop:
1. Generate code
2. Generate tests
3. Execute and validate
4. If failed, regenerate with error feedback
5. Repeat up to max retries
"""

import difflib
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Callable, Optional

import structlog

from src.agents.code_generator import EnhancedCodeGenerator, CodeGenerationResult, GeneratedCode
from src.agents.test_generator import TestGenerator, GeneratedTests
from src.config import settings

logger = structlog.get_logger(__name__)


class ValidationStatus(str, Enum):
    """Status of validation attempt."""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    PARTIAL = "partial"  # Some validations passed


@dataclass
class ValidationSignal:
    """Result of a single validation signal."""
    name: str  # "tests", "lint", "security"
    passed: bool
    message: str
    details: Optional[dict] = None


@dataclass
class ExecutionResult:
    """Result of code execution."""
    success: bool
    stdout: str
    stderr: str
    exit_code: int
    execution_time_ms: int


@dataclass
class AttemptResult:
    """Result of a single validation attempt."""
    attempt_number: int
    code: str
    tests: Optional[str]
    execution_result: Optional[ExecutionResult]
    validation_signals: list[ValidationSignal]
    status: ValidationStatus
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    diff_from_previous: Optional[str] = None
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None


@dataclass
class ValidationLoopResult:
    """Complete result of the validation loop."""
    final_code: str
    final_tests: Optional[str]
    language: str
    status: ValidationStatus
    total_attempts: int
    attempts: list[AttemptResult]
    llm_provider: str
    llm_model: str
    complexity_score: int
    quality_score: Optional[int] = None  # 1-10


class ValidationLoop:
    """
    Orchestrates the iterative code generation and validation loop.

    The loop:
    1. Generates initial code using the code generator
    2. Generates tests using the test generator
    3. Executes code with tests (via executor callback)
    4. Validates results using multiple signals
    5. If validation fails, regenerates with error feedback
    6. Repeats until success or max retries reached
    """

    def __init__(
        self,
        code_generator: Optional[EnhancedCodeGenerator] = None,
        test_generator: Optional[TestGenerator] = None,
        max_retries: int = 5,
        executor: Optional[Callable[[str, str, str], ExecutionResult]] = None,
    ):
        """
        Initialize the validation loop.

        Args:
            code_generator: Code generation agent
            test_generator: Test generation agent
            max_retries: Maximum number of retry attempts
            executor: Callback to execute code (code, tests, language) -> ExecutionResult
        """
        self.code_generator = code_generator or EnhancedCodeGenerator()
        self.test_generator = test_generator or TestGenerator()
        self.max_retries = max_retries or settings.execution_max_retries
        self.executor = executor or self._mock_executor

    def run(
        self,
        prompt: str,
        language: Optional[str] = None,
        context: Optional[str] = None,
        skip_tests: bool = False,
        on_attempt: Optional[Callable[[AttemptResult], None]] = None,
    ) -> ValidationLoopResult:
        """
        Run the complete validation loop.

        Args:
            prompt: Natural language description of code to generate
            language: Target language (auto-detected if not provided)
            context: Additional context for generation
            skip_tests: Skip test generation (for simple snippets)
            on_attempt: Callback called after each attempt

        Returns:
            ValidationLoopResult with final code and attempt history
        """
        attempts: list[AttemptResult] = []
        previous_code: Optional[str] = None
        generation_result: Optional[CodeGenerationResult] = None

        logger.info(
            "validation_loop_started",
            prompt=prompt[:100],
            max_retries=self.max_retries,
        )

        for attempt_num in range(1, self.max_retries + 1):
            attempt = self._run_attempt(
                prompt=prompt,
                language=language,
                context=context,
                attempt_number=attempt_num,
                previous_code=previous_code,
                previous_error=attempts[-1].error_message if attempts else None,
                skip_tests=skip_tests,
            )

            # Calculate diff from previous
            if previous_code and attempt.code:
                attempt.diff_from_previous = self._generate_diff(
                    previous_code,
                    attempt.code,
                    language or "python",
                )

            # Store generation result from first attempt
            if attempt_num == 1 and attempt.code:
                # Get the generation info
                generation_result = self.code_generator.generate(
                    prompt=prompt,
                    language=language,
                    context=context,
                )

            attempts.append(attempt)
            previous_code = attempt.code

            # Notify callback
            if on_attempt:
                on_attempt(attempt)

            # Check if we're done
            if attempt.status == ValidationStatus.PASSED:
                logger.info(
                    "validation_loop_passed",
                    attempt=attempt_num,
                    total_attempts=len(attempts),
                )
                break

            # Log retry
            if attempt_num < self.max_retries:
                logger.info(
                    "validation_loop_retrying",
                    attempt=attempt_num,
                    error=attempt.error_message,
                )

        # Determine final status
        final_attempt = attempts[-1]
        final_status = final_attempt.status

        # Calculate quality score
        quality_score = self._calculate_quality_score(attempts)

        return ValidationLoopResult(
            final_code=final_attempt.code,
            final_tests=final_attempt.tests,
            language=language or "python",
            status=final_status,
            total_attempts=len(attempts),
            attempts=attempts,
            llm_provider=generation_result.llm_provider if generation_result else "unknown",
            llm_model=generation_result.llm_model if generation_result else "unknown",
            complexity_score=generation_result.complexity_score if generation_result else 0,
            quality_score=quality_score,
        )

    def _run_attempt(
        self,
        prompt: str,
        language: Optional[str],
        context: Optional[str],
        attempt_number: int,
        previous_code: Optional[str],
        previous_error: Optional[str],
        skip_tests: bool,
    ) -> AttemptResult:
        """Run a single validation attempt."""
        started_at = datetime.utcnow()
        validation_signals: list[ValidationSignal] = []

        try:
            # Generate or regenerate code
            if attempt_number == 1 or not previous_code:
                # First attempt: generate fresh
                result = self.code_generator.generate(
                    prompt=prompt,
                    language=language,
                    context=context,
                )
                code = result.files[0].code if result.files else ""
                detected_language = result.language
            else:
                # Retry: regenerate with error feedback
                regenerated = self.code_generator.regenerate_with_feedback(
                    original_code=previous_code,
                    error_message=previous_error or "Unknown error",
                    language=language or "python",
                    attempt=attempt_number,
                )
                code = regenerated.code
                detected_language = regenerated.language

            if not code:
                return AttemptResult(
                    attempt_number=attempt_number,
                    code="",
                    tests=None,
                    execution_result=None,
                    validation_signals=[],
                    status=ValidationStatus.FAILED,
                    error_type="generation_failed",
                    error_message="Code generation returned empty result",
                    started_at=started_at,
                    completed_at=datetime.utcnow(),
                )

            # Generate tests if not skipped
            tests = None
            if not skip_tests:
                try:
                    test_result = self.test_generator.generate(
                        code=code,
                        language=detected_language,
                    )
                    tests = test_result.test_code
                except Exception as e:
                    logger.warning(
                        "test_generation_failed",
                        error=str(e),
                        attempt=attempt_number,
                    )
                    validation_signals.append(ValidationSignal(
                        name="test_generation",
                        passed=False,
                        message=f"Test generation failed: {str(e)}",
                    ))

            # Execute code
            execution_result = self.executor(code, tests or "", detected_language)

            # Validate execution result
            test_signal = self._validate_tests(execution_result)
            validation_signals.append(test_signal)

            # Run lint validation (basic for now)
            lint_signal = self._validate_lint(code, detected_language)
            validation_signals.append(lint_signal)

            # Determine overall status
            all_passed = all(s.passed for s in validation_signals)
            some_passed = any(s.passed for s in validation_signals)

            if all_passed:
                status = ValidationStatus.PASSED
            elif some_passed:
                status = ValidationStatus.PARTIAL
            else:
                status = ValidationStatus.FAILED

            # Extract error message if failed
            error_type = None
            error_message = None
            if status != ValidationStatus.PASSED:
                failed_signals = [s for s in validation_signals if not s.passed]
                if failed_signals:
                    error_type = failed_signals[0].name
                    error_message = failed_signals[0].message

            return AttemptResult(
                attempt_number=attempt_number,
                code=code,
                tests=tests,
                execution_result=execution_result,
                validation_signals=validation_signals,
                status=status,
                error_type=error_type,
                error_message=error_message,
                started_at=started_at,
                completed_at=datetime.utcnow(),
            )

        except Exception as e:
            logger.error(
                "validation_attempt_failed",
                attempt=attempt_number,
                error=str(e),
            )
            return AttemptResult(
                attempt_number=attempt_number,
                code=previous_code or "",
                tests=None,
                execution_result=None,
                validation_signals=validation_signals,
                status=ValidationStatus.FAILED,
                error_type="exception",
                error_message=str(e),
                started_at=started_at,
                completed_at=datetime.utcnow(),
            )

    def _validate_tests(self, result: ExecutionResult) -> ValidationSignal:
        """Validate test execution results."""
        if result.exit_code == 0:
            return ValidationSignal(
                name="tests",
                passed=True,
                message="All tests passed",
                details={
                    "stdout": result.stdout[:500],
                    "execution_time_ms": result.execution_time_ms,
                },
            )
        else:
            # Extract error from stderr or stdout
            error_output = result.stderr or result.stdout
            return ValidationSignal(
                name="tests",
                passed=False,
                message=f"Tests failed: {error_output[:200]}",
                details={
                    "exit_code": result.exit_code,
                    "stderr": result.stderr[:500],
                    "stdout": result.stdout[:500],
                },
            )

    def _validate_lint(self, code: str, language: str) -> ValidationSignal:
        """Basic lint validation (syntax check)."""
        if language == "python":
            try:
                compile(code, "<string>", "exec")
                return ValidationSignal(
                    name="lint",
                    passed=True,
                    message="Syntax check passed",
                )
            except SyntaxError as e:
                return ValidationSignal(
                    name="lint",
                    passed=False,
                    message=f"Syntax error: {str(e)}",
                    details={"line": e.lineno, "offset": e.offset},
                )
        else:
            # For other languages, assume passed (will be validated at execution)
            return ValidationSignal(
                name="lint",
                passed=True,
                message="Lint check skipped for non-Python",
            )

    def _generate_diff(
        self,
        old_code: str,
        new_code: str,
        language: str,
    ) -> str:
        """Generate unified diff between code versions."""
        old_lines = old_code.splitlines(keepends=True)
        new_lines = new_code.splitlines(keepends=True)

        diff = difflib.unified_diff(
            old_lines,
            new_lines,
            fromfile=f"attempt_prev.{language}",
            tofile=f"attempt_curr.{language}",
        )

        return "".join(diff)

    def _calculate_quality_score(self, attempts: list[AttemptResult]) -> int:
        """
        Calculate quality score based on attempts.

        Scoring:
        - Base score: 10
        - Deduct 1 per retry needed
        - Deduct 2 for any failed validation
        - Minimum score: 1
        """
        score = 10

        # Deduct for retries
        score -= (len(attempts) - 1)

        # Check final attempt validations
        if attempts:
            final = attempts[-1]
            failed_signals = [s for s in final.validation_signals if not s.passed]
            score -= len(failed_signals) * 2

        return max(1, min(10, score))

    def _mock_executor(
        self,
        code: str,
        tests: str,
        language: str,
    ) -> ExecutionResult:
        """
        Mock executor for testing without actual code execution.

        In production, this should be replaced with the actual
        execution service (Cloud Run Jobs or local container).
        """
        logger.warning("using_mock_executor")

        # Simple syntax check for Python
        if language == "python":
            try:
                compile(code, "<string>", "exec")
                if tests:
                    compile(tests, "<string>", "exec")
                return ExecutionResult(
                    success=True,
                    stdout="Mock execution passed",
                    stderr="",
                    exit_code=0,
                    execution_time_ms=100,
                )
            except SyntaxError as e:
                return ExecutionResult(
                    success=False,
                    stdout="",
                    stderr=f"SyntaxError: {str(e)}",
                    exit_code=1,
                    execution_time_ms=10,
                )

        # For other languages, assume success
        return ExecutionResult(
            success=True,
            stdout="Mock execution passed (non-Python)",
            stderr="",
            exit_code=0,
            execution_time_ms=100,
        )


# Convenience function
def create_validation_loop(executor: Optional[Callable] = None) -> ValidationLoop:
    """Create a new validation loop instance."""
    return ValidationLoop(executor=executor)
