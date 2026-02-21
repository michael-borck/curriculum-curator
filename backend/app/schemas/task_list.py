"""
TaskList API schemas
"""

from datetime import datetime
from typing import Any

from app.schemas.base import CamelModel


class TaskListResponse(CamelModel):
    """Full TaskList response schema"""

    id: str
    lrd_id: str | None = None
    unit_id: str
    tasks: dict[str, Any]
    status: str
    total_tasks: int
    completed_tasks: int
    progress: dict[str, Any] | None = None
    progress_percentage: float
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None = None


class TaskStatusUpdate(CamelModel):
    """Request to update a single task's status within a TaskList"""

    task_index: int
    status: str
