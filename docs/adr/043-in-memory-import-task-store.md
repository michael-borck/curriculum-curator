# 43. In-Memory Import Task Store

Date: 2026-02-22

## Status

Accepted

## Context

Package imports (IMSCC, SCORM, ZIP) are long-running operations that parse archives, classify items, create database records, and save content to Git. The user needs progress feedback (files processed, current file, errors) while the import runs in the background. This requires a mechanism to track task state and expose it via a polling API.

The app targets single-process deployments (including the Electron desktop build), so the solution should be simple and dependency-free.

## Decision

Use a process-level in-memory dictionary to track import tasks. No external dependencies (no Redis, no Celery, no database table).

**Data model:** An `ImportTask` dataclass with status (`pending` → `processing` → `completed` / `failed`), progress counters (`total_files`, `processed_files`, `current_file`), result fields (`unit_id`, `unit_code`, `unit_title`), and an error list.

**API:**
- `create_task() → ImportTask` — generates a UUID, stores the task, returns it
- `get_task(task_id) → ImportTask | None` — returns the task or None
- Callers mutate the returned dataclass directly (no update function)

**Expiry:** Lazy cleanup on every `create_task()` and `get_task()` call — tasks older than 1 hour are deleted. No background thread.

**Frontend polling:** `GET /api/package-import/status/{task_id}` returns the task state as JSON. The frontend polls until status is `completed` or `failed`.

## Consequences

### Positive
- Zero infrastructure — no Redis, no database migration, no external process
- Works identically in server and Electron desktop deployments
- Simple to understand and debug — it's a dict and a dataclass
- Lazy cleanup means no background threads or timer complexity

### Negative
- Task state is lost on server restart — an in-progress import becomes invisible
- Not thread-safe (no locking) — safe only with single-worker uvicorn or async-only access
- No horizontal scaling — each worker process has its own dict, so multi-worker deployments would lose track of tasks
- No capacity limit — unbounded growth between cleanup cycles (mitigated by 1-hour TTL)

### Neutral
- No explicit delete API — tasks simply expire after 1 hour
- Polling (not push) — adds latency vs WebSocket/SSE but simpler to implement

## Alternatives Considered

### Database-Backed Job Table
- Persist tasks in SQLite alongside other data; survives restarts
- Rejected: adds schema complexity for a transient concern; import tasks are only relevant for ~1 minute while running

### Redis + Celery Task Queue
- Industry-standard for background jobs with progress tracking
- Rejected: massive dependency overhead for a single-user desktop app; contradicts the zero-infrastructure deployment model

### Server-Sent Events for Progress
- Push progress updates instead of polling
- Rejected: the import endpoint already returns a task ID synchronously; SSE would require a second connection and more frontend complexity for marginal UX improvement

## Implementation Notes

- The store is a module-level singleton (`_tasks: dict[str, ImportTask]`)
- TTL is 1 hour (`_TASK_TTL = timedelta(hours=1)`)
- Cleanup iterates all tasks on every access — acceptable given the expected low task count (typically 0–2 concurrent imports)
- The import background task is launched via `asyncio.create_task()` from the endpoint handler

## References

- [ADR-042: IMSCC and SCORM Import](042-package-import-round-trip.md)
- `backend/app/services/import_task_store.py`
