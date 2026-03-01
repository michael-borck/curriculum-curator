"""
Tests for the generic background-task store and API endpoints.
"""

from __future__ import annotations

import asyncio
import json

import pytest

from app.services.task_store import (
    BackgroundTask,
    create_task,
    get_task,
    make_progress_cb,
)


# ──────────────────────────────────────────────────────────────
# Unit tests for the in-memory store
# ──────────────────────────────────────────────────────────────


class TestTaskStore:
    def test_create_task_returns_pending(self) -> None:
        task = create_task("export")
        assert task.status == "pending"
        assert task.kind == "export"
        assert task.progress == 0
        assert task.total == 0
        assert task.errors == []
        assert task.result is None

    def test_create_task_with_meta(self) -> None:
        task = create_task("import", meta={"unit_id": "abc"})
        assert task.meta == {"unit_id": "abc"}

    def test_get_task_returns_task(self) -> None:
        task = create_task("export")
        found = get_task(task.task_id)
        assert found is task

    def test_get_task_returns_none_for_missing(self) -> None:
        assert get_task("nonexistent-id") is None

    def test_make_progress_cb_updates_task(self) -> None:
        task = create_task("export")
        cb = make_progress_cb(task)
        cb(3, 10, "Processing week 3")
        assert task.progress == 3
        assert task.total == 10
        assert task.label == "Processing week 3"


class TestBackgroundTaskWait:
    @pytest.mark.asyncio
    async def test_wait_times_out(self) -> None:
        task = create_task("export")
        # Should return quickly without blocking
        await task.wait(timeout=0.01)

    @pytest.mark.asyncio
    async def test_notify_wakes_waiter(self) -> None:
        task = create_task("export")

        woke = False

        async def _waiter() -> None:
            nonlocal woke
            await task.wait(timeout=5.0)
            woke = True

        waiter = asyncio.create_task(_waiter())
        await asyncio.sleep(0.01)
        task.notify()
        await waiter
        assert woke


# ──────────────────────────────────────────────────────────────
# HTTP endpoint tests
# ──────────────────────────────────────────────────────────────


class TestTaskEndpoints:
    def test_get_task_status(self, client) -> None:  # type: ignore[no-untyped-def]
        task = create_task("export", meta={"unit_id": "u1"})
        task.status = "processing"
        task.progress = 2
        task.total = 5
        task.label = "Building week 2"

        resp = client.get(f"/api/bg-tasks/{task.task_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["taskId"] == task.task_id
        assert data["kind"] == "export"
        assert data["status"] == "processing"
        assert data["progress"] == 2
        assert data["total"] == 5
        assert data["label"] == "Building week 2"
        assert data["meta"]["unit_id"] == "u1"

    def test_get_task_status_404(self, client) -> None:  # type: ignore[no-untyped-def]
        resp = client.get("/api/bg-tasks/nonexistent-id")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_stream_task_events_completed(self) -> None:
        """SSE generator yields at least one event and stops on completed."""
        from app.api.routes.background_tasks import _serialise

        task = create_task("export")
        task.status = "completed"
        task.result = {"filename": "test.imscc"}

        # Drive the generator directly (avoids test-client SSE quirks)
        async def _generate():
            while True:
                payload = _serialise(task)
                yield f"data: {json.dumps(payload)}\n\n"
                if task.status in ("completed", "failed"):
                    break
                await task.wait(timeout=0.5)

        events = [chunk async for chunk in _generate()]

        assert len(events) == 1
        payload = json.loads(events[0].removeprefix("data: ").strip())
        assert payload["status"] == "completed"
        assert payload["result"]["filename"] == "test.imscc"

    def test_download_task_result_not_ready(self, client) -> None:  # type: ignore[no-untyped-def]
        task = create_task("export")
        task.status = "processing"

        resp = client.get(f"/api/bg-tasks/{task.task_id}/download")
        assert resp.status_code == 404

    def test_download_task_result_404_no_task(self, client) -> None:  # type: ignore[no-untyped-def]
        resp = client.get("/api/bg-tasks/nonexistent-id/download")
        assert resp.status_code == 404
