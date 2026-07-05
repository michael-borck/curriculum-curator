"""
Generic in-memory task store for tracking background operations.

Provides a single `BackgroundTask` dataclass used by exports, imports, H5P
builds, and any future long-running operation.  Clients can poll for status
or subscribe via SSE.

Old tasks (>1 hour) are cleaned up automatically on access.
"""

from __future__ import annotations

import asyncio
import contextlib
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any, Protocol


class ProgressCallback(Protocol):
    """Signature for progress callbacks passed into services."""

    def __call__(self, current: int, total: int, label: str) -> None: ...


@dataclass
class BackgroundTask:
    """Tracks progress of a single background operation."""

    task_id: str
    kind: str  # "export", "import", "h5p_build", etc.
    owner_id: str | None = None  # user id that created the task (None = unowned)
    status: str = "pending"  # pending | processing | completed | failed
    progress: int = 0  # current step
    total: int = 0  # total steps (0 = indeterminate)
    label: str = ""  # human-readable current step description
    errors: list[str] = field(default_factory=list)
    meta: dict[str, Any] = field(default_factory=dict)  # domain-specific
    result: dict[str, Any] | None = None  # on completion: file_path, filename, etc.
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    _event: asyncio.Event = field(default_factory=asyncio.Event, repr=False)

    def notify(self) -> None:
        """Signal that something changed (wakes SSE waiters)."""
        self._event.set()
        self._event.clear()

    async def wait(self, timeout: float = 0.5) -> None:
        """Wait for the next change or until *timeout* seconds elapse."""
        with contextlib.suppress(TimeoutError):
            await asyncio.wait_for(self._event.wait(), timeout=timeout)


_TASK_TTL = timedelta(hours=1)
_tasks: dict[str, BackgroundTask] = {}


def create_task(
    kind: str,
    *,
    meta: dict[str, Any] | None = None,
    owner_id: str | None = None,
) -> BackgroundTask:
    """Create a new background task and return it."""
    _cleanup()
    task = BackgroundTask(
        task_id=str(uuid.uuid4()),
        kind=kind,
        owner_id=owner_id,
        meta=meta or {},
    )
    _tasks[task.task_id] = task
    return task


def get_task(task_id: str) -> BackgroundTask | None:
    """Look up a task by id, or return None."""
    _cleanup()
    return _tasks.get(task_id)


def get_owned_task(
    task_id: str, user_id: str, *, is_admin: bool = False
) -> BackgroundTask | None:
    """Look up a task, enforcing ownership.

    Returns None (indistinguishable from not-found — no existence leak) if the
    task is owned by another user. Tasks with no owner are treated as private
    and only visible to admins.
    """
    task = get_task(task_id)
    if task is None:
        return None
    if is_admin:
        return task
    if task.owner_id is not None and task.owner_id == user_id:
        return task
    return None


def make_progress_cb(task: BackgroundTask) -> ProgressCallback:
    """Return a plain callback that mutates *task* and wakes SSE waiters."""

    def _cb(current: int, total: int, label: str) -> None:
        task.progress = current
        task.total = total
        task.label = label
        task.notify()

    return _cb


def _cleanup() -> None:
    """Remove tasks older than _TASK_TTL."""
    cutoff = datetime.now(UTC) - _TASK_TTL
    stale = [tid for tid, t in _tasks.items() if t.created_at < cutoff]
    for tid in stale:
        del _tasks[tid]
