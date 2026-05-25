# 66. Resource Ownership Seam

Date: 2026-05-25

## Status

Accepted

## Context

Object-level authorization (who may read/modify a given resource) was enforced
inconsistently across the API, and in several places not at all. An audit of the
routes found:

- **Six route groups with no ownership check** — any authenticated user could
  read or modify another user's resources by id: `assessments/{id}`,
  `learning_outcomes/{id}`, `designs/{id}`, `accreditation` mappings,
  `udl_audit` (`/units/{unit_id}/...`), and `analytics` (`/units/{unit_id}/...`).
  This is a Broken Access Control / IDOR class flaw (OWASP A01).
- **Duplicated inline checks** where ownership *was* enforced — `units.py` (×6),
  `research.py` (×5), `prompt_templates.py` (×2), `unit_structure.py` (×2) —
  that disagreed with each other: some returned 404, some 403; some honoured an
  admin bypass, some did not; the archived-unit check existed only in the
  `deps.py` helpers.
- Two pre-existing dependencies (`get_user_unit`, `get_user_material`) already
  embodied the correct pattern but covered only units and materials.
- A dead helper, `get_user_or_admin_override`, with zero callers.

Risk context: the app runs on a centralised server for authenticated,
authorised users (lecturers); ids are non-enumerable UUIDv4s; there are no
production users yet. So *active* exploitability is currently low, but the
write/DELETE gaps (assessments, ULOs, designs) are genuine horizontal
privilege-escalation holes the moment two real users share a deployment, and
UUIDs are a mitigation, not a control.

## Decision

Introduce a single **resource ownership seam** in `app/api/deps.py`:

- `load_owned_or_404(db, model, resource_id, current_user, *, owner_attr="owner_id", via_unit=False, detail=...)`
  — the deep helper: loads the resource by primary key, resolves its owner
  (directly via `owner_attr`, or transitively via the resource's `unit_id` →
  `Unit.owner_id` when `via_unit=True`), enforces ownership, and returns the ORM
  model or raises 404.
- A small shared check, `_verify_owner_or_404`, used by both the helper and
  `get_user_unit` so the admin-bypass / archived / 404 rules live in one place.
- **Thin per-resource dependencies** (`get_user_unit`, `get_user_material`,
  `get_user_assessment`, `get_user_design`, ...) — 3-line adapters that name
  their path param and ownership path and delegate to the helper.

Standardised behaviour for the whole seam:

- **Ownership failure → 404** (never 403): do not leak the existence of
  resources the caller may not access.
- **Admins always bypass** (`current_user.role == "admin"`).
- **Archived parent → 404**: transitive resources are inaccessible when their
  owning Unit is archived (soft-deleted), matching unit-level behaviour.

Scope: all single-resource-by-id endpoints adopt the seam (including the six
gaps and the previously inline-checked routes). **List/collection endpoints keep
owner query-filtering** (`WHERE user_id = me`) — there is no single id to load,
and filtering is the correct, already-gap-free pattern there (`clo_sets`,
`research_sources`).

## Consequences

### Positive
- Closes six concrete Broken Access Control gaps.
- One place to read, change, and test the authorization rule (locality); one
  interface every owned-resource route crosses (leverage).
- Consistent semantics (404, admin bypass, archived) — no more 403-vs-404 or
  missing-admin-bypass drift.
- New owned resources get authorization by adding one thin dependency.

### Negative
- `deps.py` imports the owned-resource models (acceptable coupling for the
  central auth module).
- A malformed (non-UUID) id still raises before the 404 (pre-existing GUID
  type-decorator behaviour, unchanged here).

### Neutral
- `get_user_unit` keeps returning the `UnitResponse` schema (load-bearing for
  its callers) rather than the ORM model, so it loads via the repo but shares
  the same ownership check.

## Alternatives Considered

### Generic dependency factory — `Depends(owned(Assessment, via_unit=True))`
- One registration line per resource, no named functions.
- Rejected: FastAPI resolves a dependency's path param by **name**, and this
  codebase uses `{assessment_id}`, `{unit_id}`, … (not a uniform `{id}`). A
  generic factory would require either renaming every route's path param to a
  common name (broad churn) or `inspect.Signature` manipulation (metaprogramming
  that hurts readability). The thin per-resource deps achieve the same DRY core
  (the shared helper) without fighting FastAPI, and are explicit, greppable, and
  independently testable. The factory is the better choice only for a greenfield
  API designed with uniform `{id}` params.

### Enforce ownership in service methods instead of route dependencies
- `clo_sets` does this (passes `user_id`, filters in queries).
- Rejected as the general pattern: most services don't take the caller, and
  enforcing at the dependency keeps the check at the trust boundary (the HTTP
  edge) where it's visible and uniform. Service-level filtering remains correct
  for list endpoints.

### Leave it as-is (UUIDs as the control)
- Rejected: non-enumerable ids are a mitigation, not an authorization control;
  the write/DELETE gaps are real, and the fix is cheap before users exist.

## Implementation Notes

- The seam lives in `app/api/deps.py`. `get_user_unit` returns `UnitResponse`;
  `load_owned_or_404` and the other per-resource deps return the ORM model.
- `db.get(model, resource_id)` is used for the primary-key load (typed via the
  PEP-695 generic `[T]`), avoiding `model.id` attribute access on a generic.

## References

- [ADR-007: Simple Authentication for Internal Network](007-simple-authentication-internal-network.md)
- [ADR-010: Security Hardening](010-security-hardening.md)
- [ADR-031: Soft-Delete Units](031-soft-delete-units.md) — archived-status rule
- `docs/architecture-deepening.md` — candidate #3 (resource-ownership seam)
- OWASP Top 10 A01:2021 — Broken Access Control
