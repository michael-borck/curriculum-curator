"""
In-memory task store for tracking background import progress.

Each import job gets a unique task_id that clients can poll for status.
Old tasks (>1 hour) are cleaned up automatically on access.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta


@dataclass
class ImportTask:
    """Tracks progress of a single import job."""

    task_id: str
    status: str = "pending"  # pending | processing | completed | failed
    total_files: int = 0
    processed_files: int = 0
    current_file: str | None = None
    unit_id: str | None = None
    unit_code: str | None = None
    unit_title: str | None = None
    errors: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


_TASK_TTL = timedelta(hours=1)
_tasks: dict[str, ImportTask] = {}


def create_task() -> ImportTask:
    """Create a new import task and return it."""
    _cleanup()
    task = ImportTask(task_id=str(uuid.uuid4()))
    _tasks[task.task_id] = task
    return task


def get_task(task_id: str) -> ImportTask | None:
    """Look up a task by id, or return None."""
    _cleanup()
    return _tasks.get(task_id)


def _cleanup() -> None:
    """Remove tasks older than _TASK_TTL."""
    cutoff = datetime.now(UTC) - _TASK_TTL
    stale = [tid for tid, t in _tasks.items() if t.created_at < cutoff]
    for tid in stale:
        del _tasks[tid]
