# Architecture Deepening — Tracker

**Started:** 2026-05-23
**Source:** `/improve-codebase-architecture` review (four parallel Explore passes over the import, export, AI, and search/cross-cutting clusters; load-bearing claims verified by grep before recording).

These are **deepening opportunities** — turning shallow modules into deep ones (lots of behaviour behind a small interface), for testability and AI-navigability. None re-litigate an accepted ADR; #1 and #2 *finish* seams the ADRs already call for.

**Vocabulary** (from the skill's LANGUAGE.md, used throughout): *module* (interface + implementation), *interface* (everything a caller must know), *deep/shallow* (leverage at the interface), *seam* (where an interface lives), *adapter* (a concrete thing satisfying an interface at a seam), *deletion test* (delete it — does complexity vanish or reappear across N callers?).

## Workflow

Grill-one → implement-one → verify → next (interleaved), **not** grill-all-then-implement. Candidates are coupled (#6 is an adapter of #1; #4 is a sub-seam of #2) and implementation surfaces constraints that change later designs. Two shared patterns are agreed up front in `CONTEXT.md` so the registry-shaped (#1/#5/#6) and orchestrator-shaped (#2/#4) candidates stay consistent.

## Progress

| # | Candidate | Strength | Status |
|---|-----------|----------|--------|
| 1 | Export dispatch registry | Strong | ● implemented + verified (branch `refactor/export-registry`) |
| 2 | AI generation orchestrator | Strong | ● implemented + verified (branch `refactor/ai-generation-orchestrator`) |
| 3 | Resource-ownership seam | Strong | ● implemented + verified (branch `refactor/ownership-seam`) — ADR-066 |
| 4 | Curriculum context builder | Worth exploring | ● delivered as part of #2 (CurriculumContextBuilder) |
| 5 | Import extraction seam | Worth exploring | ☐ not started |
| 6 | H5P collapse | Worth exploring | ☐ not started |

Status legend: ☐ not started · ◐ grilled (design agreed) · ● implemented + verified

---

## 1 · Collapse the export dispatch behind one seam — **Strong**

**Files:** 11× `api/routes/*_export.py` · `services/{export_service,qti_service,scorm_service,imscc_service,h5p_service}.py` · `services/export/base.py` (`BaseExporter` — written, never wired)

**Problem:** Eleven routes are shallow pass-throughs over the format services; the client memorises a path-per-format, and the qti/h5p routes leak `db.query` directly into the route.

**Solution:** One `/export/{format}` route over an `ExportRegistry` seam. Each format is one adapter satisfying the `BaseExporter` interface that already exists.

**Wins:** leverage — one interface, every format · locality — data-gathering leaves the routes · add a format = one adapter + one register line · tests hit one seam.

**Verified:** `BaseExporter` has two adapters (`DocumentExporter`, `HTMLExporter`) but **no route references it** — deleting it breaks nothing today. The seam is real and unwired; this adopts what's already designed. Candidate 6 folds in as its `h5p` adapter.

### Design decisions (locked in grill, 2026-05-23)

Three real frictions (grounded, not the report's vague "shallow routes"): (a) **inconsistent return shapes** — scorm returns `(buf, filename)`, qti returns `buf`, document returns `(buf, filename, media_type)`; routes patch the gap; (b) **data-gathering leaks** into qti/h5p routes (`db.query` + `extract_quiz_nodes` + filename building); (c) **format ≠ adapter** — `h5p` is 4 variants, `document` serves 4 formats. Plus a **security gap**: material-scope routes query `WeeklyMaterial` by id with no ownership check.

- **Registry keys:** flat — every user-facing format is its own key → `(adapter, preset)`. `document` registered 4× (`pdf`/`docx`/`pptx`/`html`) with an `fmt` preset; the h5p family as 4 keys.
- **Options:** typed per adapter (Pydantic for serialisable fields). The only client-supplied option is `target_lms` (scorm/imscc); document's `reference_doc`/`author` derive server-side; `target_overrides`/`on_progress` are passed programmatically by the package orchestrator, not over HTTP.
- **Auth:** introduce `get_user_material` now (first slice of #3); the material-scope route depends on it.
- **Format vocabulary:** **unify everywhere** on `format_resolver`'s underscore names (they are persisted) — see `CONTEXT.md` "Export format key". Retire the short HTTP segments; `format_resolver` unchanged.
- **Scope:** registry covers single-format content exports **and** `package_export` is rewired to dispatch through it. Out of scope (unchanged): `export/preview`, `export/availability`, `/user/export/data`, `export_templates`.
- **HTTP shape:** two thin generic routes — `GET /units/{unit_id}/export/{format}` (`Depends(get_user_unit)`) and `GET /materials/{material_id}/export/{format}` (`Depends(get_user_material)`), one optional `target_lms` query. `registry.supports(format, scope)` → clean 404/422 on unsupported pairs.
- **Frontend blast radius (small):** GET path uses short names in only ~4 spots (`downloadExport.ts` URL + `fallbackMap`, quick-export buttons in `UnitPage.tsx`/`DashboardPage.tsx`); the dialog/package flow already uses canonical names. No frontend code calls material-scope export endpoints (UI-unused; tests/e2e only).

### Implemented (6 staged commits on `refactor/export-registry`)

1. `ExportRegistry` + `BaseExporter`/`ExportResult`/`ExportOptions`/`ExportScope` in `services/export/`; one adapter per format (scorm, imscc, qti, h5p×4, html, pdf/docx/pptx). Adapters gather their own data and build their own filename/media_type.
2. `get_user_material` in `api/deps.py`.
3. Two generic routes (`api/routes/export.py`) replace 5 per-format route files; registry exceptions → 404/422/503/500; route order keeps `/export/materials`, `/export/preview`, `/export/package` ahead of the catch-all.
4. `package_export` dispatches through the registry; scorm/imscc adapters offload via `asyncio.to_thread`.
5. Frontend `h5p` → `h5p_question_set` (canonical).
6. `tests/test_export_registry.py` — 24 tests (capability matrix, dispatch errors, real exports, route auth via `get_user_material`, route precedence).

**Verification:** ruff + basedpyright clean on all touched backend files; 77 export tests pass (24 new + 53 existing); full suite 859 passed. Known non-blockers: (a) 13 `test_integration.py` auth tests need a live server (pre-existing, fail identically on `main`); (b) 6 pre-existing ruff `default-type-args` errors in `llm_service.py`/`ollama_service.py` (untouched); (c) frontend type-check/lint baseline broken (missing `@types/react` in `node_modules` — run `./frontend.sh`); my frontend edits add 0 new tsc errors.

**Env note:** run backend tests via `.venv/bin/python -m pytest` after `uv sync --extra dev` (installs pytest into the project venv with the working FastAPI). `uv run pytest` uses a shared base env whose FastAPI breaks the `client` fixture's annotation resolution.

## 2 · Pull generation logic out of `ai.py` behind a service seam — **Strong**

**Files:** `api/routes/ai.py` (1445 lines, 20 endpoints) · `services/llm_service.py` (1075 lines) · `services/prompt_templates.py` (Jinja2 library, underused) · `generate_structured_content()` (ADR-045 retry, bypassed)

**Problem:** The largest route in the codebase holds prompt assembly, context stitching, JSON fence-stripping (**4× inline + a `_strip_markdown_fences` helper that only 2 callers use** — verified), manual parse, and ad-hoc retry. Business logic leaked into the route.

**Solution:** A generation orchestrator behind one interface — `generate(kind, context) → typed | error` — that selects the prompt template, calls the retry-capable LLM module, and parses once. Routes become thin.

**Wins:** locality — prompt+parse+retry in one module · leverage — 20 endpoints share one path · ADR-045 retry actually gets used · fence-stripping written once.

**ADR note:** Aligns with ADR-045 (structured retry) and ADR-046 (Jinja2 prompts), which are accepted but currently bypassed. This makes them bind, not contradicts them.

### Implemented (staged commits on `refactor/ai-generation-orchestrator`)

1. **Engine** — `generate_structured_content` gained `system_prompt` (preserve injection-hardened prompts), `inject_schema` (caller supplies schema), `max_tokens`, and PEP-695 generics (callers get their exact type, no casts). The deep ADR-045 retry/validate loop now actually gets used.
2. **`CurriculumContextBuilder`** (candidate #4) — `services/curriculum_context.py`; `build_context()` → `CurriculumContext.as_block()`/`prepend_to()`. `/generate`'s 3 stitches → 1 call.
3+4. **All 6 JSON endpoints migrated** (scaffold-unit, generate-schedule, validate, visual-prompt, generate-video-interaction, suggest-interaction-points) — strict Pydantic + retry; prompts in `services/ai_prompts/`; dropped the duplicated fence-strip/`json.loads`/retry/error-string-sniff.
5. **Tests** — `test_generate_structured.py` (7) + `test_curriculum_context.py` (12); updated `test_ai_video_interactions.py` to the new seam.
6. **3 text endpoints** (remediate, fill-gap, validate-content) — prompts relocated to `ai_prompts/`; fixed fill-gap returning error strings as content.

**Bugs fixed along the way:** `WeeklyTopic.title` → `.topic_title` (latent `AttributeError` in week context); fill-gap error-string leak.

**Verification:** ruff + basedpyright clean across `app/`; **842 passed, 24 skipped, 0 failed**. `generate_text` remains for genuinely streaming/text paths; the JSON leak is gone.

## 3 · Generalise the resource-ownership dependency — **Strong**

**Files:** `api/deps.py` (`get_user_unit`) · `units.py`, `materials.py`, `assessments.py`, `learning_outcomes.py`, `research.py` …

**Problem:** `get_user_unit` is a genuinely deep dependency (existence + ownership + admin override + archived filter + 404) but adopted in only **8 of 43 route files** (verified). The rest re-implement the check inline, or skip it (a silent access bug, not a compile error).

**Solution:** Generalise to a parametric `get_user_resource[T]` and adopt across the owned-resource routes. Ownership becomes a property of the seam, not of each route author's memory.

**Wins:** locality — access rule in one module · safety holes close by construction · ~100 lines of repeated guards deleted · smallest blast radius of the six.

### Implemented (staged commits on `refactor/ownership-seam`, ADR-066)

Grounding reframed this from "tidy boilerplate" to a **security fix**: six route groups had **no ownership check at all** (Broken Access Control / IDOR).

1. **Seam** — `load_owned_or_404(db, model, id, user, *, owner_attr/via_unit)` + shared `_verify_owner_or_404`; per-resource deps (`get_user_unit/_material/_assessment/_ulo/_design`). Standardised: 404 (never 403), admin bypass, archived→404. Dead `get_user_or_admin_override` deleted.
2. **Closed 6 gaps** — gated ~73 endpoints (assessments, learning_outcomes, designs, udl_audit, analytics, accreditation); body-based gaps closed in-handler (`create_design` via `require_unit_owner`; analytics batch via `filter_owned_unit_ids`).
3. **Consolidated** research.py (403→404 + admin) and unit_structure.py (admin bypass).
4–5. `clo_sets`/`research_sources` **left as-is** (gap-free query-filtering; admin-bypass gain not worth a service refactor). units.py + prompt_templates.py also left (see ADR-066). 13 ownership tests prove non-owner→404, owner→200, admin bypass, batch filtering.

**Verification:** ruff + basedpyright clean; 879 passed. Shape decision (helper+per-resource over a factory) and the deliberate exclusions recorded in ADR-066.

## 4 · One seam for "build the AI context" — **Worth exploring**

**Files:** `api/routes/ai.py` (`_enrich_with_week_context`, `_inject_source_materials`) · `services/design_context.py` (`get_design_context`, `format_design_context`, `build_pedagogy_instruction`) — stitched at ~8 call sites.

**Problem:** "Assemble the generation context" is real, reusable work spread across ~8 call sites, each re-ordering helpers and re-running DB queries; the context format has no single owner.

**Solution:** A `CurriculumContextBuilder` with one `build_context(unit, week, design, …)` entry point that resolves design, week and sources behind a deep interface.

**Wins:** locality — context format owned in one place · 8 call sites collapse to one call · fewer DB round-trips · pairs with #2 (it's #2's natural sub-seam, but reusable beyond AI endpoints — e.g. preview, ADR-059 research grounding).

## 5 · Unify the import extraction seam & retire the legacy wrapper — **Worth exploring**

**Files:** `services/unified_import_service.py` (`_extract_content`) · `services/file_import_service.py` (legacy text wrapper) · `services/material_parsers/` (ADR-065)

**Problem:** The extraction dispatch returns two incompatible shapes (`MaterialParseResult` vs a `file_import_service` dict), so the orchestrator branches on both. `FileImportService` is a shallow pass-through whose only live job is the `.txt` fallback.

**Solution:** A `FileExtractor` seam keyed by extension, every adapter returning one `ExtractedContent`. The legacy text path becomes one more adapter; its classification helpers move to a tiny pure module.

**Wins:** locality — one result type, no branch · add a format = one adapter · retires a shallow legacy wrapper · classification becomes pure + testable.

**ADR note:** Stays inside ADR-063/ADR-065 — the two pluggable parser systems (outline vs material) remain separate seams; this does *not* merge them. It only unifies the extraction return shape.

## 6 · Collapse the four H5P builders into one deep module — **Worth exploring**

**Files:** `services/h5p_service.py` · `h5p_branching_service.py` · `h5p_course_presentation.py` · `h5p_interactive_video_service.py`

**Problem:** A single deep concept — "package content as H5P" — is fragmented into four shallow files, each re-implementing `_build_h5p_json`, `_build_content_json` and zip assembly (verified), each 1:1 with a route.

**Solution:** One `H5PBuilder.build(content_type, …)` with the manifest/zip layers shared internally and the four variants as private methods behind one interface.

**Wins:** locality — H5P packaging in one module · shared manifest/zip written once · interface shrinks, variants go private · one fixture tests all four · becomes the single `h5p` adapter for #1.

---

## Explicitly *not* recommended

- **Creating repositories for the other ~21 domains.** Most would be CRUD-only pass-throughs (shallow) — the deletion test says the complexity wouldn't reappear. That's the opposite of deepening. Keep repos where there's real query logic to concentrate (unit, user, security).
