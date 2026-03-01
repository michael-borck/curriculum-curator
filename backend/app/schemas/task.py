"""Pydantic models for the generic background-task system."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from app.schemas.base import CamelModel


class TaskStatusResponse(CamelModel):
    """Wire format returned by poll and SSE endpoints."""

    task_id: str
    kind: str
    status: str
    progress: int
    total: int
    label: str
    errors: list[str]
    meta: dict[str, Any]
    result: dict[str, Any] | None = None
    created_at: datetime
