"""
Code Execution Service for the Intelligent Coding Agent.

Provides code execution capabilities:
- Local execution (development)
- Cloud Run Jobs (production) - planned

This service executes generated code and tests in isolated environments
and returns execution results for the validation loop.
"""

import asyncio
import subprocess
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import structlog

from src.config import settings

logger = structlog.get_logger(__name__)


@dataclass
class ExecutionResult:
    """Result of code execution."""
    success: bool
    stdout: str
    stderr: str
    exit_code: int
    execution_time_ms: int


@dataclass
class ExecutionEnvironment:
    """Configuration for execution environment."""
    language: str
    runtime_version: Optional[str] = None
    dependencies: Optional[list[str]] = None
    timeout_seconds: int = 120


class LocalExecutor:
    """
    Executes code locally using subprocess.

    This executor is intended for development and testing.
    In production, use CloudRunExecutor for isolated execution.
    """

    # Language to command mapping
    LANGUAGE_COMMANDS = {
        "python": {
            "run": ["python", "-u"],
            "test": ["python", "-m", "pytest", "-v"],
            "extension": ".py",
        },
        "javascript": {
            "run": ["node"],
            "test": ["npx", "jest"],
            "extension": ".js",
        },
        "typescript": {
            "run": ["npx", "ts-node"],
            "test": ["npx", "jest"],
            "extension": ".ts",
        },
        "go": {
            "run": ["go", "run"],
            "test": ["go", "test", "-v"],
            "extension": ".go",
        },
    }

    def __init__(self, timeout_seconds: int = None):
        """
        Initialize the local executor.

        Args:
            timeout_seconds: Default execution timeout
        """
        self.timeout = timeout_seconds or settings.execution_timeout_seconds

    def execute(
        self,
        code: str,
        tests: Optional[str],
        language: str,
        dependencies: Optional[list[str]] = None,
    ) -> ExecutionResult:
        """
        Execute code locally.

        Args:
            code: Main code to execute
            tests: Test code (if any)
            language: Programming language
            dependencies: Required dependencies

        Returns:
            ExecutionResult with stdout, stderr, exit code
        """
        if language not in self.LANGUAGE_COMMANDS:
            return ExecutionResult(
                success=False,
                stdout="",
                stderr=f"Unsupported language: {language}",
                exit_code=1,
                execution_time_ms=0,
            )

        lang_config = self.LANGUAGE_COMMANDS[language]
        start_time = time.time()

        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                tmppath = Path(tmpdir)

                # Write main code file
                main_file = tmppath / f"main{lang_config['extension']}"
                main_file.write_text(code)

                # Write test file if provided
                if tests:
                    test_file = tmppath / f"test_main{lang_config['extension']}"
                    test_file.write_text(tests)

                # Install dependencies if needed
                if dependencies:
                    self._install_dependencies(language, dependencies, tmppath)

                # Determine what to run
                if tests:
                    # Run tests
                    cmd = lang_config["test"]
                    if language == "python":
                        cmd = cmd + [str(test_file)]
                    working_dir = tmpdir
                else:
                    # Run main code
                    cmd = lang_config["run"] + [str(main_file)]
                    working_dir = tmpdir

                # Execute
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=self.timeout,
                    cwd=working_dir,
                    env=self._get_env(language, tmppath),
                )

                execution_time = int((time.time() - start_time) * 1000)

                return ExecutionResult(
                    success=result.returncode == 0,
                    stdout=result.stdout,
                    stderr=result.stderr,
                    exit_code=result.returncode,
                    execution_time_ms=execution_time,
                )

        except subprocess.TimeoutExpired:
            execution_time = int((time.time() - start_time) * 1000)
            return ExecutionResult(
                success=False,
                stdout="",
                stderr=f"Execution timed out after {self.timeout} seconds",
                exit_code=124,
                execution_time_ms=execution_time,
            )

        except Exception as e:
            execution_time = int((time.time() - start_time) * 1000)
            logger.error("execution_failed", error=str(e))
            return ExecutionResult(
                success=False,
                stdout="",
                stderr=f"Execution error: {str(e)}",
                exit_code=1,
                execution_time_ms=execution_time,
            )

    def _install_dependencies(
        self,
        language: str,
        dependencies: list[str],
        workdir: Path,
    ):
        """Install dependencies for execution."""
        if not dependencies:
            return

        try:
            if language == "python":
                subprocess.run(
                    ["pip", "install", "--quiet"] + dependencies,
                    capture_output=True,
                    timeout=60,
                )
            elif language in ["javascript", "typescript"]:
                subprocess.run(
                    ["npm", "install", "--save-dev"] + dependencies,
                    cwd=workdir,
                    capture_output=True,
                    timeout=60,
                )
            elif language == "go":
                for dep in dependencies:
                    subprocess.run(
                        ["go", "get", dep],
                        cwd=workdir,
                        capture_output=True,
                        timeout=60,
                    )
        except Exception as e:
            logger.warning("dependency_install_failed", error=str(e))

    def _get_env(self, language: str, workdir: Path) -> dict:
        """Get environment variables for execution."""
        import os
        env = os.environ.copy()

        if language == "python":
            # Add current directory to Python path
            pythonpath = env.get("PYTHONPATH", "")
            env["PYTHONPATH"] = f"{workdir}:{pythonpath}"

        return env


class CloudRunExecutor:
    """
    Executes code using Cloud Run Jobs.

    This executor provides isolated, secure execution in containers.
    It requires Google Cloud setup and is used in production.

    TODO: Implement in Phase 2 when Cloud Run Jobs infrastructure is ready.
    """

    def __init__(
        self,
        project_id: str = None,
        region: str = None,
    ):
        """
        Initialize the Cloud Run executor.

        Args:
            project_id: GCP project ID
            region: GCP region for Cloud Run
        """
        self.project_id = project_id or settings.cloud_run_project
        self.region = region or settings.cloud_run_region
        self._client = None

    def execute(
        self,
        code: str,
        tests: Optional[str],
        language: str,
        dependencies: Optional[list[str]] = None,
    ) -> ExecutionResult:
        """
        Execute code using Cloud Run Jobs.

        This creates a new Cloud Run Job, executes the code,
        and returns the results.
        """
        # TODO: Implement Cloud Run Jobs execution
        # For now, fall back to local execution
        logger.warning("cloud_run_not_implemented_falling_back_to_local")
        local = LocalExecutor()
        return local.execute(code, tests, language, dependencies)


class ExecutionService:
    """
    Main execution service that routes to appropriate executor.

    Automatically selects between local and cloud execution
    based on configuration and environment.
    """

    def __init__(self):
        """Initialize the execution service."""
        self.environment = settings.environment

        if self.environment == "production" and settings.cloud_run_project:
            self.executor = CloudRunExecutor()
        else:
            self.executor = LocalExecutor()

        logger.info(
            "execution_service_initialized",
            environment=self.environment,
            executor=self.executor.__class__.__name__,
        )

    def execute(
        self,
        code: str,
        tests: Optional[str] = None,
        language: str = "python",
        dependencies: Optional[list[str]] = None,
    ) -> ExecutionResult:
        """
        Execute code and return results.

        Args:
            code: Main code to execute
            tests: Test code (optional)
            language: Programming language
            dependencies: Required dependencies

        Returns:
            ExecutionResult with execution output
        """
        logger.info(
            "executing_code",
            language=language,
            has_tests=tests is not None,
            code_length=len(code),
        )

        result = self.executor.execute(code, tests, language, dependencies)

        logger.info(
            "execution_complete",
            success=result.success,
            exit_code=result.exit_code,
            execution_time_ms=result.execution_time_ms,
        )

        return result

    async def execute_async(
        self,
        code: str,
        tests: Optional[str] = None,
        language: str = "python",
        dependencies: Optional[list[str]] = None,
    ) -> ExecutionResult:
        """
        Execute code asynchronously.

        Wraps sync execution in a thread pool for async compatibility.
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.execute(code, tests, language, dependencies),
        )


# Singleton instance
_service: Optional[ExecutionService] = None


def get_execution_service() -> ExecutionService:
    """Get the global execution service instance."""
    global _service
    if _service is None:
        _service = ExecutionService()
    return _service


def create_executor_callback():
    """
    Create an executor callback for the validation loop.

    Returns a callable that matches the ValidationLoop executor signature.
    """
    service = get_execution_service()

    def executor(code: str, tests: str, language: str) -> ExecutionResult:
        return service.execute(code, tests if tests else None, language)

    return executor
