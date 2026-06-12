# Implementation Roadmap — Remaining Planned Stories

**Date:** 2026-06-12
**Scope:** the 17 stories still marked Planned in [user-stories.md](user-stories.md)
(6.15–6.16, 9.17, 9.19–9.21, 15.10–15.11, 19B.1–19B.4, 19C.1–19C.5), plus two
prerequisites discovered while planning.
**Defers to:** [speaker-notes-plan.md](speaker-notes-plan.md) (Phases 2–4) and
[structured-import-plan.md](structured-import-plan.md) (Phases 3–5) for their
detailed designs — this document sequences across all streams and records what
the code audit changed about the assumptions.

---

## Discoveries that reshaped the plan

1. **The TipTap editor is orphaned (blocking).** `UnifiedEditor`/`RichTextEditor`
   and every custom node under `frontend/src/components/Editor/` have **no live
   mount** — the only consumer (`features/materials/MaterialDetail.tsx`) was
   deleted with the Content-model cleanup (commit `0f48b1fd`). The edit form in
   `WeeklyMaterialsManager.tsx` is a plain `description` textarea; there is
   currently no UI path to author `content_json`. Re-hosting the editor is a
   hard prerequisite for speaker notes authoring (15.10–15.11), all of 19C,
   19B.3 threshold authoring, and the import plan's source-files panel.

2. **9.20 is ~80 % done.** `format_resolver.py` already implements the
   resolution chain including user defaults from
   `teaching_preferences.export_defaults`; the settings UI to edit them exists
   (`DefaultExportTargets` in `ExportTemplates.tsx`). The gap: the per-material
   download menu and UnitPage quick-export ignore the resolved defaults.

3. **9.21 does not depend on 19C** (previously assumed). Exporters already
   consume structured nodes (`extract_quiz_nodes`, `extract_branching_cards` in
   `unit_export_data.py`) — feature detection for capability warnings reads
   `questionType` straight off the nodes today. The real silent-degradation
   points to warn about: `h5p_service._TYPE_MAP.get(..., _MULTI_CHOICE_LIB)`
   silently converts unsupported question types; `qti_service` drops them with
   only a log line.

4. **Much of 19C already exists.** `QuizQuestionNode.ts` implements 5 of 7
   question types (missing: matching, drag-and-drop). `BranchingCardNode` +
   `BranchingCardView` *are* the form-field card editor — 19C.5 is effectively
   done. Two template skeletons (`frontend/src/templates/case_study.json`,
   `interactive_video.json`) exist but were never imported anywhere.

5. **Bug found:** the per-material download menu in `WeeklyMaterialsManager.tsx`
   is gated on `material.description &&` — materials that only have
   `content_json` (structured imports per ADR-065) get no download menu at all.

6. **Structured-import Phase 2 is already shipped** (all four parsers have test
   files), so 6.16 reduces to Phase 4 (AI recovery), which depends on Phase 3's
   source-file retention.

7. **19C.4 (structured slide nodes) is recommended *against* as written.** A
   slide-container node would break `slide_splitter.py`, conflict with ADR-064
   ("rough slides are a feature") / ADR-038 (content, not presentation), and
   orphan every PPTX import. The existing `slideBreak` + first-heading-as-title
   convention already makes export predictable. Counter-proposal in Stage F4.

---

## Milestones

Stages are PR-sized. Effort: S ≈ half-day, M ≈ 1–2 days, L ≈ 3 days+ (AI-assisted pace).

### M0 — Foundations (unblocks everything)

| Stage | Work | Effort |
|---|---|---|
| **F1** | **Re-host the editor.** Full-width "Edit content" surface (modal or route) launched from the edit pencil in `WeeklyMaterialsManager`, loading/saving `contentJson` via the existing materials API. Reuse the save shape from the deleted `MaterialDetail` (`git show 0f48b1fd^:frontend/src/features/materials/MaterialDetail.tsx`). The metadata form stays for title/type/status. Verify `BranchingCardView` works in the new host and flip **19C.5** to Done. | M |
| **F2** | **Fix the `description` gate** so the download/preview actions appear for `contentJson`-only materials (`material.contentJson \|\| material.description`). | S |
| **F3** | **Single source of truth for format labels (9.19).** New `frontend/src/constants/exportFormats.ts` (`EXPORT_FORMAT_META`: label, friendly label, tooltip, file hint — modelled on `sessionFormats.ts`). Replace the four divergent maps: `MaterialExportRow.TARGET_LABELS`, `ExportTemplates.CONTENT_TYPE_ROWS` labels, `UnitPage.labelMap` + button copy, `WeeklyMaterialsManager.exportFormats`. Native `title` tooltips on target chips and menu entries. Flip **9.19**. | S |

### M1 — Speaker notes authoring (15.10 → 15.11, P2)

Execute [speaker-notes-plan.md](speaker-notes-plan.md) Phases 2–4 as written —
the pipeline (Phase 1) shipped in April; the plan's designs are still valid.
Depends on F1 (there is no editor to put the affordances in until it's re-hosted).

| Stage | Work | Effort |
|---|---|---|
| **N1** | Phase 2: inline notes block beneath each slide, "+ Add speaker notes" affordance, auto-scaffold on slide-break insert, placeholder copy, "Notes: N/M" coverage badge on material cards. Flip **15.10**. | M |
| **N2** | Phase 3: "Generate speaker notes with AI" — per-slide opt-out toggle (`aiSelected` attr already in schema), single batched LLM call via the ADR-045 structured-output loop, propose/apply review pane, ADR-032 gating. New endpoint `POST /api/materials/{id}/generate-speaker-notes`. Flip **15.11**. | M/L |
| **N3** | Phase 4 polish: guides, ADR-064 implementation notes, prompt audit. | S |

Open question to resolve at N2 start (from the plan doc): `refine_only`
assistance level — generate only for slides with existing notes (recommended) or all.

### M2 — Advanced import (6.15 → 6.16, P2)

Execute [structured-import-plan.md](structured-import-plan.md) Phases 3–4.
Phase 3 must precede Phase 4 (AI recovery re-runs against the retained source file).

| Stage | Work | Effort |
|---|---|---|
| **I1** | Phase 3 (Mode B): grouping heuristic in preview, `attached_source_files` metadata, source files stored in the git-backed material dir under `source_files/`, "promote to canonical" endpoint + UI, source-files panel in the F1 editor surface. Flip **6.15**. | L |
| **I2** | Phase 4: `pdf_llm` parser (ADR-045 retry pattern), "Improve structure with AI" action on `pdf_paragraphs` imports, cost estimate, ADR-032 gating. Flip **6.16**. | M |
| **I3** | (Optional, Phase 5) dialect parsers — `revealjs`, `marp`, `quarto`, `ipynb` — each self-contained; add on demand. | S each |

### M3 — Export UX completion (9.20 → 9.21)

| Stage | Work | Effort |
|---|---|---|
| **E1** | **Finish 9.20.** Material-scope preview endpoint (`GET /materials/{id}/export/preview` reusing `detect_content_types` + `resolve_targets_for_material` + `get_user_material`); per-material download menu lists resolved targets first (badged "Default") then document formats, labels from `exportFormats.ts`. Add the missing `interactive_video` row to settings `CONTENT_TYPE_ROWS`. Flip **9.20**. | M |
| **E2** | **Capability warnings (9.21).** New `backend/app/services/export/capabilities.py`: `detect_content_features(content_json)` (typed-node walk — question types, tables, images, mermaid, video) + `FORMAT_CAPABILITIES` matrix seeded from actual adapter behaviour + `warnings_for()` returning severity (converted / dropped), message, suggested alternative target. Extend `MaterialExportPreview` with warnings; warning triangle + one-click switch in `MaterialExportRow` and the material menu. Drift guard: a test that round-trips each declared-supported question type through the real adapters. Optionally make `h5p_service` raise `ExportUnsupportedError` instead of silently converting once the UI exists. Flip **9.21**. | L |

### M4 — Interactive HTML export (19B)

| Stage | Work | Effort |
|---|---|---|
| **H1** | `interactive_html` registry adapter + standalone player (19B.1): `interactive_html_service.py` (mirrors `h5p_branching_service` builder shape) emitting one self-contained HTML file — inline CSS/JS, card graph embedded as JSON (escape `</`), vanilla ~150-line runtime. Register the canonical-vocabulary triple: `registry.py`, `TARGETS_FOR_CONTENT_TYPE["branching"]`, `exportFormats.ts` label. The unified route works with zero route changes. Handle choice→ending transitions and convergence properly (the H5P builder treats endings as fall-off-the-end; the new player should not). | M |
| **H2** | Step tracking + replay (19B.2 partial, 19B.4): visited-card counter, "Steps taken: N" on end screen, "Start again" reset. No schema changes. | S |
| **H3** | Threshold fields (19B.2/19B.3) — *depends on F1*: `BranchingCardNode` attrs `stepThreshold` (0 = off), `endMessageEfficient`, `endMessageThorough` (keep `endMessage` as fallback); plain-language number + two-textarea fields in `BranchingCardView`'s ending section; pass attrs through `extract_branching_cards`; player picks the variant. H5P export ignores them (its end screens are static) — correct, not a gap. Flip **19B.1–19B.4**. | M |

### M5 — Content templates & question types (19C remainder)

| Stage | Work | Effort |
|---|---|---|
| **T1** | **Templates (19C.1):** revive `frontend/src/templates/` (add `quiz.json`, `slides.json` with heading + `slideBreak` + `speakerNotes` scaffolding; keep the two existing), new `templates/index.ts` with `getTemplateForContentType()` that **regenerates all node IDs on insert** (`crypto.randomUUID()` — verbatim template IDs would collide across materials). "Start from: blank / quiz / slides / case study / interactive video" choice on material creation, decoupled from the session-format field. Flip **19C.1**. | M |
| **T2** | **Matching questions (19C.3 part 1):** add `'matching'` to `QuizQuestionNode` with `pairs: {id,left,right}[]`; pairs editor in `QuizQuestionView`; emit `options=[{left,right}]` from `extract_quiz_nodes` — the exact shape `qti_service._matching_to_qti*` already consumes, so QTI export works with zero QTI changes. Capability matrix: `qti` yes, `h5p_question_set` no → E2 warning falls out automatically. | M |
| **T3** | **Drag-and-drop questions (19C.3 part 2):** new `'drag_drop'` type; backend `QuestionType` enum member (clean-slate, no migration); H5P target `H5P.DragText` (param shape near `_build_blanks`); QTI declared unsupported in the matrix. Flip **19C.2–19C.3**. | M/L |
| **T4** | **Slides decision (19C.4):** keep `slideBreak` + first-heading convention (see Discovery 7); improve the editor's `slideBreak` rendering to a labelled divider ("Slide N — {first heading}") and let the T1 slides template model the convention. Document via short ADR; re-word 19C.4 in user-stories to match the decision and flip it. | S |

### Deliberately deferred

- **9.17 (H5P inside IMSCC packages)** — needs real-LMS validation (Canvas/Moodle
  import behaviour with embedded `.h5p` files); revisit after M3 when warnings
  can communicate partial support honestly.
- **Import Phase 5 dialect parsers (I3)** — add when a real course folder needs one.

---

## Dependency graph

```
F1 (editor re-host) ──▶ N1 ──▶ N2 ──▶ N3        (speaker notes)
        │ ──▶ H3                                  (19B thresholds)
        │ ──▶ T1 ──▶ T2 ──▶ T3                    (templates/questions)
        │ ──▶ I1 source-files panel
F3 (labels) ──▶ E1 ──▶ E2                         (export UX)
        │ ──▶ H1 menu label
H1 ──▶ H2 ──▶ H3
I1 ──▶ I2                                         (import AI needs retained sources)
T2/T3 ──▶ E2 matrix rows (additive, not blocking)
```

Parallelisable: M1 (notes) and M3 (export UX) touch disjoint files after M0;
M4 H1/H2 is backend-only and independent of everything except F3's label entry.

## Suggested execution order

**M0 → M1 → M3-E1 → M2-I1 → M4-H1+H2 → M2-I2 → M3-E2 → M5-T1..T4 → M4-H3 → N3**

Rationale: M0 unblocks three streams for one M of work; speaker notes is the
highest-value P2 with its plan already locked; E1 is a cheap finish of an
80 %-done story; the import stream (P2, Enhancer adoption path) interleaves
around the larger E2/T stages; H3 and T-stages ride on the editor once it has
settled under real use from N1/N2.

## Decisions needed before starting

1. **F1 editor host form:** modal over the materials list vs a dedicated route
   (`/units/:unitId/materials/:materialId/edit`). Route recommended — full-width
   editing, lighter state management, linkable.
2. **19C.4 stance (T4):** accept the keep-slideBreak counter-proposal, or build
   slide-container nodes as the story literally reads (not recommended — see
   Discovery 7).
3. **ADR-032 `refine_only` × AI note generation (N2):** restrict generation to
   slides with existing notes (recommended) or allow all.
