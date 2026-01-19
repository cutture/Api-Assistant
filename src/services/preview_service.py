"""
Preview Service for Intelligent Coding Agent.

Provides live preview functionality:
- Starting preview servers for generated code
- Managing preview sessions
- Handling preview expiration
"""

import asyncio
import os
import signal
import subprocess
import structlog
import tempfile
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

from src.config import get_settings

logger = structlog.get_logger(__name__)


@dataclass
class PreviewSession:
    """A live preview session."""
    id: str
    execution_id: str
    user_id: str
    port: int
    url: str
    status: str  # 'starting', 'running', 'stopped', 'error'
    process: Optional[subprocess.Popen] = field(default=None, repr=False)
    temp_dir: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc) + timedelta(minutes=30))
    error_message: Optional[str] = None

    def is_expired(self) -> bool:
        """Check if preview has expired."""
        return datetime.now(timezone.utc) > self.expires_at

    def time_remaining(self) -> int:
        """Get seconds remaining until expiration."""
        remaining = (self.expires_at - datetime.now(timezone.utc)).total_seconds()
        return max(0, int(remaining))


class PreviewService:
    """
    Service for managing live preview sessions.

    Features:
    - Start preview servers for various frameworks
    - Automatic port allocation
    - Session expiration handling
    - Cleanup of stopped previews
    """

    def __init__(self):
        self.settings = get_settings()
        self.sessions: dict[str, PreviewSession] = {}
        self._port_range_start = 9000
        self._port_range_end = 9999
        self._used_ports: set[int] = set()

        # Preview base URL (configurable)
        self._preview_base_url = os.getenv(
            "PREVIEW_BASE_URL",
            "http://localhost",
        )
        self._max_concurrent = int(os.getenv("PREVIEW_MAX_CONCURRENT", "10"))

    def _allocate_port(self) -> int:
        """Allocate an available port."""
        for port in range(self._port_range_start, self._port_range_end + 1):
            if port not in self._used_ports:
                self._used_ports.add(port)
                return port
        raise RuntimeError("No available ports for preview")

    def _release_port(self, port: int):
        """Release a port back to the pool."""
        self._used_ports.discard(port)

    async def start_preview(
        self,
        execution_id: str,
        user_id: str,
        code: str,
        language: str,
        framework: Optional[str] = None,
        dependencies: Optional[list[str]] = None,
        expiry_minutes: int = 30,
    ) -> PreviewSession:
        """
        Start a live preview server for generated code.

        Args:
            execution_id: ID of the code execution
            user_id: User ID
            code: The code to run
            language: Programming language
            framework: Framework (react, vue, express, flask, etc.)
            dependencies: List of dependencies
            expiry_minutes: Minutes until preview expires

        Returns:
            PreviewSession with URL and status
        """
        # Check concurrent limit
        active_count = sum(
            1 for s in self.sessions.values()
            if s.status == "running"
        )
        if active_count >= self._max_concurrent:
            raise RuntimeError(
                f"Maximum concurrent previews ({self._max_concurrent}) reached"
            )

        session_id = str(uuid.uuid4())
        port = self._allocate_port()

        session = PreviewSession(
            id=session_id,
            execution_id=execution_id,
            user_id=user_id,
            port=port,
            url=f"{self._preview_base_url}:{port}",
            status="starting",
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=expiry_minutes),
        )

        self.sessions[session_id] = session

        try:
            # Create temp directory for code
            temp_dir = tempfile.mkdtemp(prefix=f"preview_{session_id[:8]}_")
            session.temp_dir = temp_dir

            # Write code to temp directory
            await self._setup_preview_files(
                temp_dir=temp_dir,
                code=code,
                language=language,
                framework=framework,
                dependencies=dependencies,
            )

            # Start the preview server
            process = await self._start_server(
                temp_dir=temp_dir,
                port=port,
                language=language,
                framework=framework,
            )

            session.process = process
            session.status = "running"

            logger.info(
                "Preview started",
                session_id=session_id,
                port=port,
                url=session.url,
            )

            # Schedule cleanup
            asyncio.create_task(
                self._schedule_cleanup(session_id, expiry_minutes * 60)
            )

            return session

        except Exception as e:
            session.status = "error"
            session.error_message = str(e)
            self._release_port(port)
            logger.error("Failed to start preview", error=str(e))
            raise

    async def _setup_preview_files(
        self,
        temp_dir: str,
        code: str,
        language: str,
        framework: Optional[str],
        dependencies: Optional[list[str]],
    ):
        """Set up preview files in temp directory."""
        temp_path = Path(temp_dir)

        # Determine main file name and setup based on language/framework
        if language == "python":
            if framework == "flask":
                main_file = temp_path / "app.py"
                main_file.write_text(code)

                # Create requirements.txt
                reqs = ["flask"] + (dependencies or [])
                (temp_path / "requirements.txt").write_text("\n".join(reqs))

            elif framework == "fastapi":
                main_file = temp_path / "main.py"
                main_file.write_text(code)

                reqs = ["fastapi", "uvicorn"] + (dependencies or [])
                (temp_path / "requirements.txt").write_text("\n".join(reqs))

            else:
                main_file = temp_path / "main.py"
                main_file.write_text(code)
                if dependencies:
                    (temp_path / "requirements.txt").write_text("\n".join(dependencies))

        elif language in ("javascript", "typescript"):
            if framework in ("react", "vue", "next"):
                # For React/Vue/Next, we'd need a more complex setup
                # For now, treat as simple Node server
                main_file = temp_path / "index.js"
                main_file.write_text(code)
            else:
                main_file = temp_path / "index.js"
                main_file.write_text(code)

            # Create package.json
            pkg = {
                "name": "preview",
                "version": "1.0.0",
                "main": "index.js",
                "scripts": {
                    "start": "node index.js",
                },
                "dependencies": {},
            }

            if framework == "express":
                pkg["dependencies"]["express"] = "*"

            for dep in (dependencies or []):
                pkg["dependencies"][dep] = "*"

            import json
            (temp_path / "package.json").write_text(json.dumps(pkg, indent=2))

        else:
            # Generic: just write the code
            ext_map = {
                "go": ".go",
                "java": ".java",
                "csharp": ".cs",
            }
            ext = ext_map.get(language, ".txt")
            main_file = temp_path / f"main{ext}"
            main_file.write_text(code)

    async def _start_server(
        self,
        temp_dir: str,
        port: int,
        language: str,
        framework: Optional[str],
    ) -> subprocess.Popen:
        """Start the preview server process."""
        env = os.environ.copy()
        env["PORT"] = str(port)

        if language == "python":
            if framework == "flask":
                cmd = ["python", "-m", "flask", "run", "--host=0.0.0.0", f"--port={port}"]
                env["FLASK_APP"] = "app.py"
            elif framework == "fastapi":
                cmd = ["python", "-m", "uvicorn", "main:app", "--host=0.0.0.0", f"--port={port}"]
            else:
                cmd = ["python", "main.py"]
        elif language == "javascript":
            cmd = ["node", "index.js"]
        else:
            # Fallback - try to run with appropriate runtime
            raise ValueError(f"Unsupported language for preview: {language}")

        process = subprocess.Popen(
            cmd,
            cwd=temp_dir,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        # Wait a moment and check if process started
        await asyncio.sleep(1)

        if process.poll() is not None:
            # Process exited
            stdout, stderr = process.communicate()
            raise RuntimeError(
                f"Preview server failed to start: {stderr.decode()}"
            )

        return process

    async def _schedule_cleanup(self, session_id: str, delay_seconds: int):
        """Schedule cleanup after expiration."""
        await asyncio.sleep(delay_seconds)
        await self.stop_preview(session_id)

    async def stop_preview(self, session_id: str) -> bool:
        """
        Stop a preview session.

        Args:
            session_id: Session ID to stop

        Returns:
            True if stopped, False if not found
        """
        session = self.sessions.get(session_id)
        if not session:
            return False

        # Stop the process
        if session.process and session.process.poll() is None:
            try:
                session.process.terminate()
                try:
                    session.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    session.process.kill()
            except Exception as e:
                logger.warning("Error stopping process", error=str(e))

        # Cleanup temp directory
        if session.temp_dir:
            try:
                import shutil
                shutil.rmtree(session.temp_dir, ignore_errors=True)
            except Exception as e:
                logger.warning("Error cleaning temp dir", error=str(e))

        # Release port
        self._release_port(session.port)

        session.status = "stopped"
        del self.sessions[session_id]

        logger.info("Preview stopped", session_id=session_id)
        return True

    def get_preview(self, session_id: str) -> Optional[PreviewSession]:
        """Get preview session by ID."""
        return self.sessions.get(session_id)

    def get_user_previews(self, user_id: str) -> list[PreviewSession]:
        """Get all preview sessions for a user."""
        return [
            s for s in self.sessions.values()
            if s.user_id == user_id
        ]

    async def cleanup_expired(self) -> int:
        """
        Clean up all expired preview sessions.

        Returns:
            Number of sessions cleaned up
        """
        expired_ids = [
            session_id
            for session_id, session in self.sessions.items()
            if session.is_expired()
        ]

        for session_id in expired_ids:
            await self.stop_preview(session_id)

        return len(expired_ids)

    def get_stats(self) -> dict:
        """Get preview service statistics."""
        return {
            "total_sessions": len(self.sessions),
            "running": sum(1 for s in self.sessions.values() if s.status == "running"),
            "stopped": sum(1 for s in self.sessions.values() if s.status == "stopped"),
            "error": sum(1 for s in self.sessions.values() if s.status == "error"),
            "used_ports": len(self._used_ports),
            "available_ports": (self._port_range_end - self._port_range_start + 1) - len(self._used_ports),
        }


# Singleton instance
_preview_service: Optional[PreviewService] = None


def get_preview_service() -> PreviewService:
    """Get the global preview service instance."""
    global _preview_service
    if _preview_service is None:
        _preview_service = PreviewService()
    return _preview_service
