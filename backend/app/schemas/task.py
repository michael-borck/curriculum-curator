"""
Pydantic schemas for task management
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class TaskUpdate(BaseModel):
    """Update a single task within a task list"""

    status: str | None = None
    title: str | None = None
    description: str | None = None
    assignee: str | None = None
    priority: str | None = None
    due_date: datetime | None = None
    metadata: dict[str, Any] | None = None


class TaskListCreate(BaseModel):
    """Create a new task list"""

    course_id: UUID
    lrd_id: UUID | None = None
    tasks: list[dict[str, Any]] = Field(default_factory=list)


class TaskListUpdate(BaseModel):
    """Update a task list"""

    status: str | None = None
    tasks: list[dict[str, Any]] | None = None
    progress: dict[str, Any] | None = None


class TaskListResponse(BaseModel):
    """Task list response"""

    id: UUID
    course_id: UUID
    lrd_id: UUID | None
    tasks: list[dict[str, Any]]
    status: str
    total_tasks: int
    completed_tasks: int
    progress: dict[str, Any] | None
    progress_percentage: float
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None

    class Config:
        from_attributes = True
