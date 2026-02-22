# ADR-031: Soft-Delete for Units

## Status

Accepted (implemented)

## Context

When users delete a unit, the data could be permanently removed (hard delete) or marked as deleted while remaining in the database (soft delete). Permanent deletion is simpler but irreversible — lecturers who accidentally delete a unit lose all their curriculum work. In a university context, units may also need to be temporarily shelved between semesters and restored later.

The application also supports a "local mode" (single-user, no authentication) where the risk profile differs — there is no multi-user data isolation concern, and power users may want the ability to permanently purge data.

## Decision

We implement **soft delete by default** with an optional **hard delete for local mode only**.

- `DELETE /api/units/{id}` performs a soft delete: sets `is_deleted = True` and `deleted_at = now()` on the unit row. The unit no longer appears in normal listings but remains in the database.
- `DELETE /api/units/{id}?permanent=true` performs a hard delete, but **only when the application is running in local mode**. In authenticated (server) mode, permanent deletion is rejected with 403.
- `POST /api/units/{id}/restore` restores a soft-deleted unit by clearing the deletion flags.
- `GET /api/units/archived` returns all soft-deleted units for the current user.
- All normal unit queries filter out soft-deleted rows via `is_deleted == False`.

## Consequences

### Positive

- Users can recover accidentally deleted units without admin intervention.
- Units can be archived between semesters and restored when needed.
- Database retains full audit history of curriculum development.
- Local-mode users retain the power to permanently clean up their data.

### Negative

- All unit queries must remember to filter `is_deleted == False`; forgetting this filter leaks "deleted" data.
- Database grows over time with soft-deleted rows (acceptable at university scale).
- Two code paths for delete (soft vs hard) add minor complexity.
