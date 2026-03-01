"""
Thin compatibility shim that delegates to the generic task_store.

Existing import code continues to use ``ImportTask`` and its field names
(``total_files``, ``processed_files``, ``current_file``, …).  These are
now property aliases over a single ``BackgroundTask`` instance so that both
the import-specific and generic SSE endpoints see the same data.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from app.services.task_store import BackgroundTask
from app.services.task_store import create_task as _generic_create
from app.services.task_store import get_task as _generic_get


class ImportTask:
    """Adapter that exposes import-specific field names over BackgroundTask."""

    def __init__(self, inner: BackgroundTask) -> None:
        self._inner = inner

    # ── identity / lifecycle ──────────────────────────────────────

    @property
    def task_id(self) -> str:
        return self._inner.task_id

    @property
    def status(self) -> str:
        return self._inner.status

    @status.setter
    def status(self, value: str) -> None:
        self._inner.status = value
        self._inner.notify()

    @property
    def created_at(self) -> datetime:
        return self._inner.created_at

    # ── progress fields mapped to generic progress/total/label ───

    @property
    def total_files(self) -> int:
        return self._inner.total

    @total_files.setter
    def total_files(self, value: int) -> None:
        self._inner.total = value

    @property
    def processed_files(self) -> int:
        return self._inner.progress

    @processed_files.setter
    def processed_files(self, value: int) -> None:
        self._inner.progress = value
        self._inner.notify()

    @property
    def current_file(self) -> str | None:
        return self._inner.label or None

    @current_file.setter
    def current_file(self, value: str | None) -> None:
        self._inner.label = value or ""
        self._inner.notify()

    # ── domain-specific fields stored in meta ────────────────────

    @property
    def unit_id(self) -> str | None:
        return self._inner.meta.get("unit_id")  # type: ignore[return-value]

    @unit_id.setter
    def unit_id(self, value: str | None) -> None:
        self._inner.meta["unit_id"] = value

    @property
    def unit_code(self) -> str | None:
        return self._inner.meta.get("unit_code")  # type: ignore[return-value]

    @unit_code.setter
    def unit_code(self, value: str | None) -> None:
        self._inner.meta["unit_code"] = value

    @property
    def unit_title(self) -> str | None:
        return self._inner.meta.get("unit_title")  # type: ignore[return-value]

    @unit_title.setter
    def unit_title(self, value: str | None) -> None:
        self._inner.meta["unit_title"] = value

    @property
    def errors(self) -> list[str]:
        return self._inner.errors

    @errors.setter
    def errors(self, value: list[str]) -> None:
        self._inner.errors = value

    @property
    def skipped_items(self) -> list[dict[str, str]]:
        return self._inner.meta.get("skipped_items", [])  # type: ignore[return-value]

    @skipped_items.setter
    def skipped_items(self, value: list[dict[str, Any]]) -> None:
        self._inner.meta["skipped_items"] = value


def create_task() -> ImportTask:
    """Create a new import task via the generic store."""
    inner = _generic_create("import")
    return ImportTask(inner)


def get_task(task_id: str) -> ImportTask | None:
    """Look up an import task by id."""
    inner = _generic_get(task_id)
    if inner is None or inner.kind != "import":
        return None
    return ImportTask(inner)
