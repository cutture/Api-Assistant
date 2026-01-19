"""
Scheduler Service for scheduled code executions and webhook triggers.

This module provides:
- Cron-like scheduling for executions
- One-time scheduled tasks
- Recurring task management
- Task execution tracking
"""

import asyncio
import secrets
import structlog
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Callable
from croniter import croniter

logger = structlog.get_logger(__name__)


class ScheduleType(str, Enum):
    """Type of schedule."""
    ONCE = "once"           # One-time execution
    CRON = "cron"           # Cron expression
    INTERVAL = "interval"   # Fixed interval (minutes)


class TaskType(str, Enum):
    """Type of scheduled task."""
    EXECUTION = "execution"     # Code execution
    WEBHOOK = "webhook"         # Webhook trigger
    CLEANUP = "cleanup"         # System cleanup
    CUSTOM = "custom"           # Custom callback


class TaskStatus(str, Enum):
    """Status of a scheduled task."""
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ScheduledTask:
    """A scheduled task."""
    id: str
    user_id: str
    name: str
    description: str
    task_type: TaskType
    schedule_type: ScheduleType
    schedule_value: str  # cron expression, ISO datetime, or interval in minutes
    payload: Dict[str, Any]
    status: TaskStatus = TaskStatus.ACTIVE
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_run_at: Optional[datetime] = None
    next_run_at: Optional[datetime] = None
    run_count: int = 0
    max_runs: Optional[int] = None  # None = unlimited
    error_count: int = 0
    last_error: Optional[str] = None
    timezone: str = "UTC"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "description": self.description,
            "task_type": self.task_type.value,
            "schedule_type": self.schedule_type.value,
            "schedule_value": self.schedule_value,
            "payload": self.payload,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "last_run_at": self.last_run_at.isoformat() if self.last_run_at else None,
            "next_run_at": self.next_run_at.isoformat() if self.next_run_at else None,
            "run_count": self.run_count,
            "max_runs": self.max_runs,
            "error_count": self.error_count,
            "last_error": self.last_error,
            "timezone": self.timezone,
        }


@dataclass
class TaskExecution:
    """Record of a task execution."""
    id: str
    task_id: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    status: str = "running"  # running, success, failed
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "task_id": self.task_id,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "status": self.status,
            "result": self.result,
            "error": self.error,
        }


class SchedulerService:
    """Service for managing scheduled tasks."""

    def __init__(self):
        self.tasks: Dict[str, ScheduledTask] = {}
        self.executions: Dict[str, List[TaskExecution]] = {}  # task_id -> executions
        self.callbacks: Dict[TaskType, Callable] = {}
        self._running = False
        self._scheduler_task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()
        logger.info("SchedulerService initialized")

    def register_callback(self, task_type: TaskType, callback: Callable):
        """Register a callback for a task type."""
        self.callbacks[task_type] = callback
        logger.info("Callback registered", task_type=task_type)

    async def start(self):
        """Start the scheduler loop."""
        if self._running:
            return

        self._running = True
        self._scheduler_task = asyncio.create_task(self._scheduler_loop())
        logger.info("Scheduler started")

    async def stop(self):
        """Stop the scheduler loop."""
        self._running = False
        if self._scheduler_task:
            self._scheduler_task.cancel()
            try:
                await self._scheduler_task
            except asyncio.CancelledError:
                pass
        logger.info("Scheduler stopped")

    async def _scheduler_loop(self):
        """Main scheduler loop."""
        while self._running:
            try:
                await self._check_and_run_tasks()
                await asyncio.sleep(10)  # Check every 10 seconds
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Scheduler loop error", error=str(e))
                await asyncio.sleep(30)

    async def _check_and_run_tasks(self):
        """Check for due tasks and run them."""
        now = datetime.now(timezone.utc)

        tasks_to_run = []
        async with self._lock:
            for task in self.tasks.values():
                if task.status != TaskStatus.ACTIVE:
                    continue

                if task.next_run_at and task.next_run_at <= now:
                    tasks_to_run.append(task)

        for task in tasks_to_run:
            asyncio.create_task(self._run_task(task))

    async def _run_task(self, task: ScheduledTask):
        """Run a scheduled task."""
        execution = TaskExecution(
            id=f"exec_{secrets.token_urlsafe(8)}",
            task_id=task.id,
            started_at=datetime.now(timezone.utc),
        )

        if task.id not in self.executions:
            self.executions[task.id] = []
        self.executions[task.id].append(execution)

        # Keep only last 100 executions per task
        if len(self.executions[task.id]) > 100:
            self.executions[task.id] = self.executions[task.id][-100:]

        try:
            callback = self.callbacks.get(task.task_type)
            if callback:
                result = await callback(task.payload)
                execution.result = result
                execution.status = "success"
                logger.info("Task executed successfully", task_id=task.id)
            else:
                execution.status = "failed"
                execution.error = f"No callback registered for {task.task_type}"
                logger.warning("No callback for task type", task_type=task.task_type)

        except Exception as e:
            execution.status = "failed"
            execution.error = str(e)
            task.error_count += 1
            task.last_error = str(e)
            logger.error("Task execution failed", task_id=task.id, error=str(e))

        finally:
            execution.completed_at = datetime.now(timezone.utc)
            task.last_run_at = execution.started_at
            task.run_count += 1
            task.updated_at = datetime.now(timezone.utc)

            # Calculate next run
            await self._calculate_next_run(task)

            # Check if task should be marked as completed
            if task.max_runs and task.run_count >= task.max_runs:
                task.status = TaskStatus.COMPLETED

            if task.schedule_type == ScheduleType.ONCE:
                task.status = TaskStatus.COMPLETED

    async def _calculate_next_run(self, task: ScheduledTask):
        """Calculate the next run time for a task."""
        now = datetime.now(timezone.utc)

        if task.schedule_type == ScheduleType.ONCE:
            task.next_run_at = None

        elif task.schedule_type == ScheduleType.CRON:
            try:
                cron = croniter(task.schedule_value, now)
                task.next_run_at = cron.get_next(datetime)
            except Exception as e:
                logger.error("Invalid cron expression", task_id=task.id, error=str(e))
                task.next_run_at = None

        elif task.schedule_type == ScheduleType.INTERVAL:
            try:
                minutes = int(task.schedule_value)
                task.next_run_at = now + timedelta(minutes=minutes)
            except ValueError:
                task.next_run_at = None

    # ============ Task Management ============

    async def create_task(
        self,
        user_id: str,
        name: str,
        description: str,
        task_type: TaskType,
        schedule_type: ScheduleType,
        schedule_value: str,
        payload: Dict[str, Any],
        max_runs: Optional[int] = None,
        timezone_str: str = "UTC",
    ) -> ScheduledTask:
        """Create a new scheduled task."""
        async with self._lock:
            task_id = f"task_{secrets.token_urlsafe(12)}"

            task = ScheduledTask(
                id=task_id,
                user_id=user_id,
                name=name,
                description=description,
                task_type=task_type,
                schedule_type=schedule_type,
                schedule_value=schedule_value,
                payload=payload,
                max_runs=max_runs,
                timezone=timezone_str,
            )

            # Calculate initial next_run_at
            now = datetime.now(timezone.utc)

            if schedule_type == ScheduleType.ONCE:
                try:
                    task.next_run_at = datetime.fromisoformat(schedule_value.replace("Z", "+00:00"))
                except Exception:
                    task.next_run_at = now + timedelta(minutes=1)

            elif schedule_type == ScheduleType.CRON:
                try:
                    cron = croniter(schedule_value, now)
                    task.next_run_at = cron.get_next(datetime)
                except Exception as e:
                    raise ValueError(f"Invalid cron expression: {e}")

            elif schedule_type == ScheduleType.INTERVAL:
                try:
                    minutes = int(schedule_value)
                    task.next_run_at = now + timedelta(minutes=minutes)
                except ValueError:
                    raise ValueError("Interval must be a number of minutes")

            self.tasks[task_id] = task
            logger.info("Task created", task_id=task_id, user_id=user_id)
            return task

    async def get_task(self, task_id: str) -> Optional[ScheduledTask]:
        """Get a task by ID."""
        return self.tasks.get(task_id)

    async def list_user_tasks(
        self,
        user_id: str,
        status: Optional[TaskStatus] = None,
    ) -> List[ScheduledTask]:
        """List all tasks for a user."""
        tasks = [t for t in self.tasks.values() if t.user_id == user_id]

        if status:
            tasks = [t for t in tasks if t.status == status]

        return sorted(tasks, key=lambda t: t.created_at, reverse=True)

    async def update_task(
        self,
        task_id: str,
        user_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        schedule_value: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
        max_runs: Optional[int] = None,
    ) -> Optional[ScheduledTask]:
        """Update a scheduled task."""
        async with self._lock:
            task = self.tasks.get(task_id)
            if not task or task.user_id != user_id:
                return None

            if name:
                task.name = name
            if description:
                task.description = description
            if payload:
                task.payload = payload
            if max_runs is not None:
                task.max_runs = max_runs

            if schedule_value:
                task.schedule_value = schedule_value
                await self._calculate_next_run(task)

            task.updated_at = datetime.now(timezone.utc)
            logger.info("Task updated", task_id=task_id)
            return task

    async def pause_task(self, task_id: str, user_id: str) -> bool:
        """Pause a scheduled task."""
        async with self._lock:
            task = self.tasks.get(task_id)
            if not task or task.user_id != user_id:
                return False

            if task.status == TaskStatus.ACTIVE:
                task.status = TaskStatus.PAUSED
                task.updated_at = datetime.now(timezone.utc)
                logger.info("Task paused", task_id=task_id)
                return True
            return False

    async def resume_task(self, task_id: str, user_id: str) -> bool:
        """Resume a paused task."""
        async with self._lock:
            task = self.tasks.get(task_id)
            if not task or task.user_id != user_id:
                return False

            if task.status == TaskStatus.PAUSED:
                task.status = TaskStatus.ACTIVE
                await self._calculate_next_run(task)
                task.updated_at = datetime.now(timezone.utc)
                logger.info("Task resumed", task_id=task_id)
                return True
            return False

    async def delete_task(self, task_id: str, user_id: str) -> bool:
        """Delete a scheduled task."""
        async with self._lock:
            task = self.tasks.get(task_id)
            if not task or task.user_id != user_id:
                return False

            del self.tasks[task_id]
            if task_id in self.executions:
                del self.executions[task_id]

            logger.info("Task deleted", task_id=task_id)
            return True

    async def run_task_now(self, task_id: str, user_id: str) -> Optional[TaskExecution]:
        """Run a task immediately."""
        task = self.tasks.get(task_id)
        if not task or task.user_id != user_id:
            return None

        await self._run_task(task)

        # Return the latest execution
        executions = self.executions.get(task_id, [])
        return executions[-1] if executions else None

    async def get_task_executions(
        self,
        task_id: str,
        limit: int = 50,
    ) -> List[TaskExecution]:
        """Get execution history for a task."""
        executions = self.executions.get(task_id, [])
        return executions[-limit:]

    # ============ Statistics ============

    async def get_stats(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get scheduler statistics."""
        tasks = list(self.tasks.values())
        if user_id:
            tasks = [t for t in tasks if t.user_id == user_id]

        active = sum(1 for t in tasks if t.status == TaskStatus.ACTIVE)
        paused = sum(1 for t in tasks if t.status == TaskStatus.PAUSED)
        completed = sum(1 for t in tasks if t.status == TaskStatus.COMPLETED)

        total_runs = sum(t.run_count for t in tasks)
        total_errors = sum(t.error_count for t in tasks)

        return {
            "total_tasks": len(tasks),
            "active_tasks": active,
            "paused_tasks": paused,
            "completed_tasks": completed,
            "total_executions": total_runs,
            "total_errors": total_errors,
            "scheduler_running": self._running,
        }


# Singleton instance
_scheduler_service: Optional[SchedulerService] = None


def get_scheduler_service() -> SchedulerService:
    """Get the scheduler service singleton."""
    global _scheduler_service
    if _scheduler_service is None:
        _scheduler_service = SchedulerService()
    return _scheduler_service
