"""
Scheduler API Router for scheduled executions and tasks.

Provides endpoints for:
- Creating scheduled tasks
- Managing task lifecycle
- Viewing execution history
"""

import structlog
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field

from src.api.auth import get_current_user, CurrentUser
from src.services.scheduler_service import (
    SchedulerService,
    ScheduleType,
    TaskType,
    TaskStatus,
    get_scheduler_service,
)

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/scheduler", tags=["scheduler"])


# ============ Request/Response Models ============

class CreateTaskRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(default="", max_length=500)
    task_type: str  # execution, webhook, cleanup, custom
    schedule_type: str  # once, cron, interval
    schedule_value: str  # ISO datetime, cron expression, or minutes
    payload: dict = Field(default_factory=dict)
    max_runs: Optional[int] = Field(default=None, ge=1)
    timezone: str = Field(default="UTC")


class UpdateTaskRequest(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    description: Optional[str] = Field(default=None, max_length=500)
    schedule_value: Optional[str] = None
    payload: Optional[dict] = None
    max_runs: Optional[int] = Field(default=None, ge=1)


class TaskResponse(BaseModel):
    id: str
    user_id: str
    name: str
    description: str
    task_type: str
    schedule_type: str
    schedule_value: str
    payload: dict
    status: str
    created_at: str
    updated_at: str
    last_run_at: Optional[str]
    next_run_at: Optional[str]
    run_count: int
    max_runs: Optional[int]
    error_count: int
    last_error: Optional[str]
    timezone: str


class ExecutionResponse(BaseModel):
    id: str
    task_id: str
    started_at: str
    completed_at: Optional[str]
    status: str
    result: Optional[dict]
    error: Optional[str]


class SchedulerStatsResponse(BaseModel):
    total_tasks: int
    active_tasks: int
    paused_tasks: int
    completed_tasks: int
    total_executions: int
    total_errors: int
    scheduler_running: bool


class ScheduleTypesResponse(BaseModel):
    types: List[dict]


class TaskTypesResponse(BaseModel):
    types: List[dict]


# ============ Info Endpoints ============

@router.get("/schedule-types", response_model=ScheduleTypesResponse)
async def get_schedule_types():
    """Get available schedule types."""
    return ScheduleTypesResponse(types=[
        {"value": "once", "name": "One-time", "description": "Run once at a specific time"},
        {"value": "cron", "name": "Cron", "description": "Run on a cron schedule (e.g., '0 9 * * *' for 9 AM daily)"},
        {"value": "interval", "name": "Interval", "description": "Run every N minutes"},
    ])


@router.get("/task-types", response_model=TaskTypesResponse)
async def get_task_types():
    """Get available task types."""
    return TaskTypesResponse(types=[
        {"value": "execution", "name": "Code Execution", "description": "Execute code generation task"},
        {"value": "webhook", "name": "Webhook", "description": "Trigger a webhook"},
        {"value": "cleanup", "name": "Cleanup", "description": "System cleanup task"},
        {"value": "custom", "name": "Custom", "description": "Custom task with callback"},
    ])


@router.get("/stats", response_model=SchedulerStatsResponse)
async def get_scheduler_stats(
    current_user: CurrentUser = Depends(get_current_user),
    service: SchedulerService = Depends(get_scheduler_service),
):
    """Get scheduler statistics for current user."""
    stats = await service.get_stats(current_user.user_id)
    return SchedulerStatsResponse(**stats)


# ============ Task Management Endpoints ============

@router.post("/tasks", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    request: CreateTaskRequest,
    current_user: CurrentUser = Depends(get_current_user),
    service: SchedulerService = Depends(get_scheduler_service),
):
    """Create a new scheduled task."""
    try:
        task_type = TaskType(request.task_type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid task type: {request.task_type}")

    try:
        schedule_type = ScheduleType(request.schedule_type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid schedule type: {request.schedule_type}")

    try:
        task = await service.create_task(
            user_id=current_user.user_id,
            name=request.name,
            description=request.description,
            task_type=task_type,
            schedule_type=schedule_type,
            schedule_value=request.schedule_value,
            payload=request.payload,
            max_runs=request.max_runs,
            timezone_str=request.timezone,
        )
        return TaskResponse(**task.to_dict())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/tasks", response_model=List[TaskResponse])
async def list_tasks(
    status_filter: Optional[str] = Query(default=None, alias="status"),
    current_user: CurrentUser = Depends(get_current_user),
    service: SchedulerService = Depends(get_scheduler_service),
):
    """List all scheduled tasks for current user."""
    task_status = None
    if status_filter:
        try:
            task_status = TaskStatus(status_filter)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status_filter}")

    tasks = await service.list_user_tasks(current_user.user_id, task_status)
    return [TaskResponse(**t.to_dict()) for t in tasks]


@router.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    service: SchedulerService = Depends(get_scheduler_service),
):
    """Get a scheduled task by ID."""
    task = await service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if task.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    return TaskResponse(**task.to_dict())


@router.patch("/tasks/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: str,
    request: UpdateTaskRequest,
    current_user: CurrentUser = Depends(get_current_user),
    service: SchedulerService = Depends(get_scheduler_service),
):
    """Update a scheduled task."""
    task = await service.update_task(
        task_id=task_id,
        user_id=current_user.user_id,
        name=request.name,
        description=request.description,
        schedule_value=request.schedule_value,
        payload=request.payload,
        max_runs=request.max_runs,
    )

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return TaskResponse(**task.to_dict())


@router.delete("/tasks/{task_id}")
async def delete_task(
    task_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    service: SchedulerService = Depends(get_scheduler_service),
):
    """Delete a scheduled task."""
    success = await service.delete_task(task_id, current_user.user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Task not found")

    return {"message": "Task deleted successfully"}


@router.post("/tasks/{task_id}/pause")
async def pause_task(
    task_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    service: SchedulerService = Depends(get_scheduler_service),
):
    """Pause a scheduled task."""
    success = await service.pause_task(task_id, current_user.user_id)
    if not success:
        raise HTTPException(status_code=400, detail="Cannot pause task")

    return {"message": "Task paused successfully"}


@router.post("/tasks/{task_id}/resume")
async def resume_task(
    task_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    service: SchedulerService = Depends(get_scheduler_service),
):
    """Resume a paused task."""
    success = await service.resume_task(task_id, current_user.user_id)
    if not success:
        raise HTTPException(status_code=400, detail="Cannot resume task")

    return {"message": "Task resumed successfully"}


@router.post("/tasks/{task_id}/run", response_model=ExecutionResponse)
async def run_task_now(
    task_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    service: SchedulerService = Depends(get_scheduler_service),
):
    """Run a task immediately."""
    execution = await service.run_task_now(task_id, current_user.user_id)
    if not execution:
        raise HTTPException(status_code=404, detail="Task not found")

    return ExecutionResponse(**execution.to_dict())


@router.get("/tasks/{task_id}/executions", response_model=List[ExecutionResponse])
async def get_task_executions(
    task_id: str,
    limit: int = Query(default=50, ge=1, le=100),
    current_user: CurrentUser = Depends(get_current_user),
    service: SchedulerService = Depends(get_scheduler_service),
):
    """Get execution history for a task."""
    task = await service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if task.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    executions = await service.get_task_executions(task_id, limit)
    return [ExecutionResponse(**e.to_dict()) for e in executions]
