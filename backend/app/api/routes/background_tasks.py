"""
Generic background-task endpoints.

- GET /bg-tasks/{task_id}          — poll for current status
- GET /bg-tasks/{task_id}/events   — SSE stream until completed/failed
- GET /bg-tasks/{task_id}/download — serve the result file
"""

from __future__ import annotations

import json
import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse, StreamingResponse

from app.api import deps
from app.schemas.task import TaskStatusResponse
from app.schemas.user import UserResponse  # noqa: TC001 — FastAPI needs at runtime
from app.services.task_store import BackgroundTask, get_task

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/bg-tasks")


def _task_or_404(task_id: str) -> BackgroundTask:
    task = get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


def _serialise(task: BackgroundTask) -> dict[str, Any]:
    return TaskStatusResponse(
        task_id=task.task_id,
        kind=task.kind,
        status=task.status,
        progress=task.progress,
        total=task.total,
        label=task.label,
        errors=task.errors,
        meta=task.meta,
        result=task.result,
        created_at=task.created_at,
    ).model_dump(by_alias=True, mode="json")


# ------------------------------------------------------------------
# Poll endpoint
# ------------------------------------------------------------------
@router.get("/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(
    task_id: str,
    _current_user: Annotated[UserResponse, Depends(deps.get_current_active_user)],
) -> TaskStatusResponse:
    """Return the current status of a background task."""
    task = _task_or_404(task_id)
    return TaskStatusResponse(
        task_id=task.task_id,
        kind=task.kind,
        status=task.status,
        progress=task.progress,
        total=task.total,
        label=task.label,
        errors=task.errors,
        meta=task.meta,
        result=task.result,
        created_at=task.created_at,
    )


# ------------------------------------------------------------------
# SSE endpoint
# ------------------------------------------------------------------
@router.get("/{task_id}/events")
async def stream_task_events(
    task_id: str,
    _current_user: Annotated[UserResponse, Depends(deps.get_current_active_user)],
) -> StreamingResponse:
    """Stream progress events via SSE until the task reaches a terminal state."""
    task = _task_or_404(task_id)

    async def _generate():
        while True:
            payload = _serialise(task)
            yield f"data: {json.dumps(payload)}\n\n"
            if task.status in ("completed", "failed"):
                break
            await task.wait(timeout=0.5)

    return StreamingResponse(_generate(), media_type="text/event-stream")


# ------------------------------------------------------------------
# Download endpoint
# ------------------------------------------------------------------
@router.get("/{task_id}/download")
async def download_task_result(
    task_id: str,
    _current_user: Annotated[UserResponse, Depends(deps.get_current_active_user)],
) -> FileResponse:
    """Serve the result file of a completed task."""
    task = _task_or_404(task_id)

    if task.status != "completed" or task.result is None:
        raise HTTPException(status_code=404, detail="Result not ready")

    file_path: str | None = task.result.get("file_path")
    filename: str = task.result.get("filename", "download")
    media_type: str = task.result.get("media_type", "application/octet-stream")

    if not file_path:
        raise HTTPException(status_code=404, detail="No file associated with task")

    return FileResponse(
        path=file_path,
        filename=filename,
        media_type=media_type,
    )
