# Code Audit — Pre-MVP Cleanup

**Date:** 2026-04-11
**Scope:** Backend (`backend/app/`) + Frontend (`frontend/src/`) + dependency security
**Context:** The project is approaching MVP. The last code-level audit was February 2026 and focused on `docs/` and `scripts/` rather than the application code. Significant work has shipped since (speaker notes round-trip ADR-064, structured material import ADR-065, Phase 2 parsers, bulk LMS wiring) and each addition has the potential to leave superseded code behind. Per CLAUDE.md there are no production users, so orphaned code can be deleted outright rather than deprecated with migration paths.

**Approach:** Two parallel Explore agents produced structured findings — one for backend, one for frontend — plus a dependabot sweep. This document is the synthesised report. **No deletions have been made yet.** Each finding is categorised by risk and comes with a concrete action recommendation; deletions will land as separate focused PRs after review.

---

## Executive summary

**Frontend is clean.** The audit found zero unused components, hooks, services, store actions, routes, or types. Every surveyed surface is wired end-to-end. The only item flagged (`SpeakerNotesNode` with minimal UI) is intentional Phase 1 scaffolding per ADR-064.

**Backend has one significant cleanup target**: the legacy `Content` model and its 14 CRUD + upload endpoints, which have been entirely superseded by `WeeklyMaterial` and the structured material import routes from ADR-065. Deletion is a meaningful win — removes ~15 files, one whole route module, and the largest source of pre-MVP technical debt in the codebase.

**Dependabot has 8 open alerts**, all deferred. None are trivial enough to fold into this cleanup; each has a wrinkle (pinned caps, transitive through `electron-vite`, fix versions that don't match upstream release channels). They belong in their own session.

### Scoreboard

| Area | Finding count | Risk |
|---|---|---|
| Backend — definitely dead | 0 | — |
| Backend — probably dead | 1 | Low (confirmed live) |
| Backend — deprecated paths to delete | 1 major cluster (Content ecosystem) | Medium, well-bounded |
| Backend — half-wired features | 1 (plugin system, intentional) | None — keep as-is |
| Backend — duplicate logic | 0 meaningful duplicates | — |
| Backend — tests orphaned by deletions above | ~1 file | Low |
| Frontend — unused anything | 0 | — |
| Dependabot open alerts | 8 | High severity but non-trivial fixes |

---

## Dependabot — deferred

Eight open alerts on `main`. Each has been assessed for "can this be fixed in one PR or does it need investigation?" Answer for all eight: **needs investigation**.

| Package | Manifest | Current | Fix | Severity | Wrinkle |
|---|---|---|---|---|---|
| `vite` | `frontend/package-lock.json` | `^6.4.0` | `6.4.2` | HIGH (File Read via WebSocket) | Should be a patch bump, but verify `npm update vite` doesn't cascade |
| `vite` | `frontend/package-lock.json` | `^6.4.0` | `6.4.2` | MEDIUM (Path Traversal) | Same patch as above |
| `vite` (×3) | `desktop/package-lock.json` | transitive via `electron-vite ^5.0.0` | `7.3.2` | HIGH/HIGH/MEDIUM | Transitive — fix requires `electron-vite` to publish a version pinning vite ≥7.3.2, or we add a package-level override. Needs coordination with the Electron upgrade cycle. |
| `lodash-es` (×2) | `frontend/package-lock.json` | `4.17.23` | `4.18.0` | HIGH (code injection) / MEDIUM (prototype pollution) | Real lodash 4.x historically topped out at 4.17.x. Fix version `4.18.0` needs verification that it exists in the release channel and isn't a typo or cooked advisory. |
| `litellm` | `backend/pyproject.toml` | pinned `>=1.50.0,<=1.82.6,!=1.82.7,!=1.82.8` | `1.83.0` | HIGH (password hash exposure / pass-the-hash) | Current constraint explicitly **caps below the fix version and excludes 1.82.7/1.82.8**, meaning somebody found a problem with those releases. Jumping to 1.83.0 requires investigating what the cap was protecting against. |

**Recommended handling:** Treat dependabot as its own follow-up session. A bulk "upgrade everything" PR would be a gamble; a careful one-at-a-time approach with CI verification is correct.

---

## Backend findings

### 1. Definitely dead

**None.**

All the functions that were pre-flagged as suspects turned out to still have callers:

| Pre-flagged suspect | Status | Caller |
|---|---|---|
| `file_import_service.process_zip_file()` | Live | `/import/zip/{unit_id}` route at `routes/import_content.py:647` |
| `file_import_service.strip_pptx_to_template()` | Live | `/import/pptx/extract-template` at `routes/import_content.py:715` (ADR-056) |
| `file_import_service.strip_docx_to_template()` | Live | `/import/docx/extract-template` at `routes/import_content.py:794` (ADR-056) |
| `file_import_service._extract_pptx()` | Live | `process_file()` internal path `file_import_service.py:240` |
| `PackageImportService._create_round_trip()` | Live | Conditional call when IMSCC has `curriculum_curator_meta.json` — `package_import_service.py:464` |
| `PackageImportService.extract_html_content()` | Live | Three internal calls from `_create_round_trip` at `package_import_service.py:635, 664, 978` (I was wrong earlier when I thought I removed its last caller — I only removed the call from `unified_import_service`, the round-trip path still uses it) |
| 3 × pre-existing basedpyright errors in `unified_import_service.py` | False positives | `_bg_task` is set in `apply()` before `_run_import` runs; the two `int(edit["week_number"])` warnings are casting narrowings the type checker can't prove but runtime-safe |

### 2. Probably dead

**None that weren't resolved above.** Everything classified as "probably dead" turned out to be live after a full trace.

### 3. Deprecated paths — safe to delete

#### 3.1 — The legacy `Content` model and its entire ecosystem

**This is the headline finding of the backend audit.** ADR-065 introduced structured material import that targets `WeeklyMaterial`; the entire `Content` model predates it and has no new writers since.

**Files to delete outright:**

| File | Purpose | Notes |
|---|---|---|
| `backend/app/api/routes/content.py` | 14 CRUD + upload endpoints for `Content` | Includes `/upload`, `/upload/batch`, and the legacy image-serving path |
| `backend/app/repositories/content_repo.py` | Content DAO | Only used by `routes/content.py` |
| `backend/app/schemas/content.py` | Pydantic schemas for Content | Keep any `ContentType` enum re-exports (used elsewhere); delete the rest |
| `backend/app/models/content.py` | SQLAlchemy Content model | 168 lines, multiple relationships to quiz/validation/generation-history tables |

**Files to modify:**

| File | Change |
|---|---|
| `backend/app/models/__init__.py` | Remove `Content` from the model barrel |
| `backend/app/main.py` | Remove the `include_router(content.router, ...)` line |
| `backend/tests/conftest.py` | The `test_quiz_content` fixture at line 501 creates a Content row. Rewrite to use `WeeklyMaterial` or delete the fixture entirely if the quiz tests don't need it |
| `backend/tests/test_import_endpoints.py` | Tests for `upload_content` / `upload_content_batch` — delete or repoint at the new structured import endpoints |

**Evidence this is safe:**

- Zero new code written since ADR-065 populates a Content row outside the routes we're deleting
- Frontend search found zero calls to `/api/content/upload` or the content CRUD routes (the old dialog was renamed to `MaterialImportDialog` and points at `/api/import/material/*`)
- `content_markdown`, `content_html`, and `content_json` fields on the Content model are **never populated** anywhere in the codebase — dead storage slots inside the model itself
- Per CLAUDE.md's "no production users — clean slate policy" the deletion needs no data migration

**One edge case to verify before the deletion PR:**

`backend/app/api/routes/import_content.py` around line 437 has a PDF-unit-structure flow that (per the backend agent's report) *may* still create `Content` rows as part of bulk PDF analysis. This was a pre-ADR-065 path. Before deleting `Content`, grep `import_content.py` for `Content(` and `content_repo.create_content` and confirm nothing still writes to the model outside the routes we're deleting. If it does, that flow needs migrating to `WeeklyMaterial` first.

**Relationships to handle:** Content has FK relationships to `QuizQuestion`, `GenerationHistory`, `ContentValidationResult`, `UnitLearningOutcome`, and others. The deletion PR needs to either:

1. Drop the FK columns from the related tables (safe on SQLite with no production data)
2. Or reset the database entirely (per CLAUDE.md: `rm backend/data/curriculum_curator.db && python backend/init_db.py`)

Option 2 is cleaner given the no-production-users stance — treat Content as an unsupported schema and rebuild.

**Estimated impact:** ~15 files changed, ~1,500 lines deleted. The single biggest code cleanup available before MVP.

### 4. Half-wired features

#### 4.1 — Plugin system (`backend/app/plugins/`) — intentional, keep as-is

Per ADR-003. The framework (10 validator/remediator implementations, plugin manager, `/api/plugins/*` routes) is complete and functional, but **not automatically invoked** anywhere in the content or import pipelines. Users have to call `/api/plugins/validate` explicitly.

**Verdict:** Not dead code. This is optional tooling waiting for a future "auto-validate on save" workflow. Leave it alone.

### 5. Duplicate logic

**No meaningful duplicates found.**

The backend agent initially flagged HTML title extraction as appearing in two places (`PackageImportService.extract_html_content` vs `HtmlStructuralParser`) but they serve different code paths — IMSCC round-trip vs structured material import — and the duplication is architecturally justified.

### 6. Test files orphaned by deletions

| Test file | Action | Reason |
|---|---|---|
| `backend/tests/test_import_endpoints.py` — `TestImportEndpoints` class | Delete or rewrite | Tests the legacy `/api/content/upload` path that's being deleted |
| `backend/tests/conftest.py` — `test_quiz_content` fixture | Rewrite against `WeeklyMaterial` or delete | Depends on whether any quiz tests actually need it; check `test_quiz_service.py` |

### 7. Anything else surprising

Nothing unexpected. No half-finished refactors, no TODOs naming specific dead code, no conflicting import patterns. The codebase is in good shape — the Content deletion is the one large win available.

---

## Frontend findings

### Result: zero dead code

Across all 10 audit categories the frontend agent found **zero orphaned components, hooks, services, store slices, routes, or types**. Every exported symbol in `frontend/src/` has at least one caller.

### Key verifications

| Suspect | Status | Notes |
|---|---|---|
| `PptxImportDialog` | Fully removed | `git mv` rename to `MaterialImportDialog` is complete; zero lingering references in imports, comments, or JSX |
| `ImportMaterials.tsx` (legacy import UI, 1,823 lines) | Live page | Registered at `/import` in `App.tsx:192`, still used for the legacy PDF/DOCX/PPTX batch-upload workflow. Not redundant with `MaterialImportDialog` — they serve different flows |
| `PDFImportDialog` | Never existed | The component referenced in story 6.1 was always `ImportMaterials.tsx`; no orphaned file to delete |
| `OutlineImport` + `OutlineReviewForm` | Fully wired | ADR-063 multi-step flow complete; `OutlineReviewForm` is a sub-component (not standalone-exported), which is correct |
| `WeeklyMaterialsManager.tsx` (1,101 lines) | No unused internals | All helpers (`handleMaterialDownload`, `SortableMaterialItem`, `QualityBadge`, `FormatIcon`) and event handlers verified as called |
| `unitStructureApi.ts` | Barrel re-exports only | Everything it re-exports has callers |
| Zustand stores (`authStore`, `teachingStyleStore`, `workingContextStore`, `unitsStore`) | All actions wired | No dead selectors or actions |

### The one flagged item: `SpeakerNotesNode` has no authoring UI

This is **intentional**. Per ADR-064 and `docs/speaker-notes-plan.md`, Phase 1 ships the schema node + renderer + export round-trip. Phase 2 (editor authoring affordances: auto-scaffold, coverage badge, empty-state prompt) is a separate future piece of work. The node is registered in `RichTextEditor.tsx:281`, has working parseHTML/renderHTML, and round-trips correctly through import/export — it just has no "+" button yet.

**Verdict:** Not dead code. Leave alone until speaker notes Phase 2 ships.

### Minor observations (not issues)

- `services/api.ts` exports `getCourses = getUnits` and `getCourse = getUnit` as backwards-compatibility aliases. Nothing currently calls them, but they're harmless two-line re-exports. Safe to keep or remove — not worth a PR on their own.
- `types/index.ts` exports `Course = Unit` as a type alias for the same reason. Same verdict.
- Two TODO comments found: one about migrating tokens to httpOnly cookies (`authStore.ts:29`), one about fetching assessment types in `AoLMappingPanel`. Both are legitimate future-work notes, not dead code markers.

---

## Recommended action plan

Ordered by value per effort, least risky first.

### Priority 1 — Delete the `Content` model ecosystem

**Scope:** ~15 files, ~1,500 lines deleted.

**Steps:**

1. **Pre-flight verification:**
   - Grep `backend/app/api/routes/import_content.py` for `Content(` and `content_repo` to confirm nothing in the PDF-unit-structure flow still writes to Content
   - Check `backend/tests/test_quiz_service.py` (and any other quiz tests) to see if they depend on the `test_quiz_content` conftest fixture
2. **Reset the database** per CLAUDE.md: `rm backend/data/curriculum_curator.db && python backend/init_db.py`
3. **Delete files:**
   - `backend/app/api/routes/content.py`
   - `backend/app/repositories/content_repo.py`
   - `backend/app/schemas/content.py` (preserve any `ContentType` enum used elsewhere in a separate enums module first)
   - `backend/app/models/content.py`
4. **Modify files:**
   - `backend/app/models/__init__.py` — remove `Content` from the barrel
   - `backend/app/main.py` — remove the `content.router` `include_router` line
   - `backend/tests/conftest.py` — rewrite or delete the `test_quiz_content` fixture
   - `backend/tests/test_import_endpoints.py` — delete the legacy upload tests
5. **Run quality gates:** ruff, basedpyright, pytest. The pre-existing 3 errors in `unified_import_service.py` should be unchanged.

**Risk:** Low. Well-bounded, verified by both the backend agent and the frontend agent finding zero callers. Single focused PR.

**Estimated effort:** 1–2 hours.

### Priority 2 — Reset the three pre-existing `basedpyright` errors

The errors in `unified_import_service.py` (uninitialized `_bg_task`, object→int conversions) are harmless at runtime and will keep getting flagged on every type check. While we're auditing, add targeted `# type: ignore[...]` annotations with inline comments explaining why they're safe, or fix them properly with narrower types.

**Risk:** None. Pure noise reduction.

**Estimated effort:** 15 minutes.

### Priority 3 (optional) — Delete the backward-compat frontend aliases

`getCourses`/`getCourse` in `services/api.ts` and `Course = Unit` in `types/index.ts`. Two files, a few lines each. Only worth doing if we're committing to "no course terminology at all" per ADR-028.

**Risk:** None (verified unused).

**Estimated effort:** 5 minutes.

### Deferred to separate sessions

- **Dependabot alerts** — each needs its own investigation. Not folded in.
- **Speaker notes Phase 2** (editor authoring UI) — planned feature, not cleanup.
- **Plugin auto-validation hooks** — planned feature, not cleanup.
- **`FileImportService.process_file()`** — will naturally deprecate once the legacy upload routes are gone, but the service itself is still needed for the `.txt` fallback in `unified_import`. Revisit after Priority 1 lands.

---

## Cross-references

- [ADR-003: Plugin Architecture](adr/003-plugin-architecture.md) — confirms plugin system is intentional even though inert
- [ADR-023: File Import and Processing Architecture](adr/023-file-import-processing-architecture.md) — the predecessor to the structured import work
- [ADR-042: IMSCC/SCORM Import with Round-Trip Detection](adr/042-package-import-round-trip.md) — why `_create_round_trip` and its internal callers stay alive
- [ADR-056: PPTX Template Extraction on Import](adr/056-pptx-template-extraction-on-import.md) — why `strip_pptx_to_template` stays alive
- [ADR-063: Unit Outline Import with Pluggable Parser System](adr/063-unit-outline-import-parser-system.md) — the first pluggable parser pattern, mirrored by ADR-065
- [ADR-064: Rough Slides Are a Feature](adr/064-rough-slides-as-feature.md) — why `SpeakerNotesNode` is intentional Phase 1 scaffolding
- [ADR-065: Structured Material Import Architecture](adr/065-structured-material-import-architecture.md) — the work that superseded the `Content` upload path
- [docs/speaker-notes-plan.md](speaker-notes-plan.md) — Phase 2 of speaker notes (editor UX)
- [docs/structured-import-plan.md](structured-import-plan.md) — Phase 3 of structured import (Mode B multi-format)
