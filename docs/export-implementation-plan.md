# Export System Implementation Plan

> Phased roadmap from current export state to the full vision described in
> [EXPORT_ARCHITECTURE.md](EXPORT_ARCHITECTURE.md). Each phase ships independently.

## Context

`EXPORT_ARCHITECTURE.md` describes: Tiptap custom nodes for structured content,
H5P export for interactive learning objects, branching scenario authoring, and a
two-level export system (material format → package bundling). The current
implementation covers document export (Pandoc+Typst), QTI, IMSCC, and SCORM.

## Phase Dependency Graph

```
Phase 1 (Foundations)
  └── Phase 2 (Quiz Nodes)
        └── Phase 3 (H5P Quiz + QTI)
              ├── Phase 4 (Slides) ──────┐
              ├── Phase 5 (Branching) ───┤
              └── Phase 6b (Int. Video)  │
                                         └── Phase 6a (Two-Level UI)
                                               └── Phase 6c (Progress)
```

Phases 4, 5, and 6b can run in parallel after Phase 3. Phase 6a needs all
content phases (2–5) complete.

---

## Phase 1 — Foundations: JSON Storage + Export Refactor — COMPLETE

**Commit:** `e7c93933`
**Ships**: No user-visible changes. Existing exports continue working.

### What was delivered

1. **`content_json` column** (nullable JSON) on `WeeklyMaterial`
   - Frontend: `RichTextEditor.tsx` calls `editor.getJSON()` alongside `getHTML()`, sends both
   - Backend: material PATCH/PUT endpoints accept and persist `content_json`
   - Migration path: nullable column, existing content has `content_json = null`, editor writes both on first edit+save

2. **Shared export data module** — `unit_export_data.py` with `UnitExportData` dataclass,
   `gather_unit_export_data()`, shared utilities

3. **`export_format` column** (nullable) on `WeeklyMaterial` — per-material export override

4. Fixed 15 pre-existing test failures

---

## Phase 2 — Quiz Authoring Nodes — COMPLETE

**Commit:** `d481158e`
**Ships**: In-editor quiz creation (5 question types).

### What was delivered

1. **Tiptap quiz nodes** — `QuizQuestionNode.ts` + `QuizQuestionView.tsx` React NodeView
   with question type selector, answer options, correct toggles, feedback
2. **Quiz toolbar button** in RichTextEditor (insert quiz question)
3. **5 question types**: multiple choice, true/false, multi-select, short answer, fill-in-blank
4. Quiz data stored as `quizQuestion` nodes in `content_json` (single source of truth)

---

## Phase 3 — H5P Question Set + QTI from content_json — COMPLETE

**Commits:** `20036524` (3a), `835dcc42` (3b), `fd65a516` (3c)
**Ships**: H5P quiz export, QTI from authored quizzes, content_json rendering, format selector UI, H5P embedding in IMSCC/SCORM.

### What was delivered

**Phase 3a** — QTI export from editor content_json:
- `extract_quiz_nodes()` walks `content_json` for `quizQuestion` nodes
- `_InMemoryQuizQuestion` duck-types as `QuizQuestion` for QTI exporter
- IMSCC/SCORM include QTI from both DB rows and editor content_json
- Standalone QTI 2.1 export includes editor-authored questions

**Phase 3b** — content_json rendering + H5P Question Set:
- `content_json_renderer.py` — server-side ProseMirror JSON → HTML (all node types)
- `render_material_html()` helper — prefers content_json, falls back to description
- All exports (IMSCC, SCORM, document) now use rendered content_json
- `h5p_service.py` — H5P Question Set builder (MultiChoice, TrueFalse, Essay, Blanks)
- H5P export endpoints: `/units/{id}/export/h5p`, `/materials/{id}/export/h5p`
- Frontend: QTI 2.1 and H5P export buttons in unit export menu

**Phase 3c** — format selector UI + H5P embedding in IMSCC/SCORM:
- Per-material format selector dropdown in material edit form
- H5P `.h5p` files embedded in IMSCC/SCORM packages when `export_format == "h5p_question_set"`

---

## Phase 4 — Slide Breaks + H5P Course Presentation

**Status**: COMPLETE
**Commit:** `fd65a516`
**Ships**: Slide break node, slide counter, H5P Course Presentation export, improved PPTX export.

### Work Items

1. **SlideBreak Tiptap node** — `SlideBreakNode.ts` + `SlideBreakView.tsx`
   (styled horizontal divider with slide numbers)

2. **H5P Course Presentation exporter** — `export/h5p/course_pres.py` splits
   `content_json` at slide breaks, each segment → H5P slide

3. **Improved PPTX export** — pre-process `content_json` to insert Pandoc slide
   markers at slide break positions

4. **Slides content template** — `frontend/src/templates/slides.json`
   (title slide + 3 content slides)

### Key Files (~9)
- `frontend/src/components/Editor/SlideBreakNode.ts`, `SlideBreakView.tsx`
- `frontend/src/templates/slides.json`
- `backend/app/services/h5p_service.py` (or new `h5p_course_pres.py`)
- `backend/app/services/export_service.py` — extend for slide breaks

### Dependencies: Phases 1, 3 (H5P base builder)
### Can run in parallel with Phase 5
### Risks: Tables/code blocks/Mermaid within slides need graceful H5P fallback

---

## Phase 5 — Branching Scenarios + Flat ZIP — COMPLETE

**Status**: COMPLETE
**Ships**: Case study card authoring, card map visualization, H5P Branching Scenario export. Flat ZIP export already existed (`export_materials_zip`).

### What was delivered

1. **BranchingCard TipTap node** — `BranchingCardNode.ts` (attrs-based atom node)
   with `cardId`, `cardType` (content/branch/ending), `cardTitle`, `cardContent`,
   `choices` (JSON array with targetCardId), `endScore`, `endMessage`

2. **BranchingCardView** — `BranchingCardView.tsx` React NodeView with
   edit/view toggle, color-coded type badges (blue/amber/pink), choice editor
   with target card dropdowns populated from document state

3. **BranchingMapDialog** — `BranchingMapDialog.tsx` modal SVG graph using
   dagre layout. Color-coded nodes, arrow edges with choice labels, dead end
   detection (dashed red border), orphan detection (grey fill), click-to-scroll

4. **H5P Branching Scenario builder** — `h5p_branching_service.py` with
   `H5PBranchingScenarioBuilder`. Content cards → `H5P.AdvancedText`,
   branch cards → `H5P.BranchingQuestion`, ending cards → `endScreens`.
   Single-pass index mapping, circular references safe.

5. **Backend integration** — `extract_branching_cards()` in `unit_export_data.py`,
   `_render_branching_card()` in `content_json_renderer.py`,
   `/materials/{id}/export/h5p-branching` endpoint in `h5p_export.py`

6. **Case study template** — `frontend/src/templates/case_study.json`
   (6-card template: intro, decision point, two paths, two endings)

7. **16 backend tests** — `test_h5p_branching_service.py` covering package
   structure, content nodes, sequential chaining, end screens, circular
   references, edge cases

### Key Files
- `frontend/src/components/Editor/BranchingCardNode.ts`
- `frontend/src/components/Editor/BranchingCardView.tsx`
- `frontend/src/components/Editor/BranchingMapDialog.tsx`
- `frontend/src/templates/case_study.json`
- `backend/app/services/h5p_branching_service.py`
- `backend/tests/test_h5p_branching_service.py`

---

## Phase 6a — Two-Level Export Dialog — COMPLETE

**Status**: COMPLETE
**Commit:** `707183ef`
**Ships**: Export dialog with per-material target resolution, 4-level defaults, user export preferences.

### What was delivered

1. **Export Dialog** — `ExportDialog.tsx` modal listing all materials grouped by
   week, each with toggleable target chips per content type. Package type selector
   (IMSCC / SCORM), LMS target dropdown. "Export... (full dialog)" added at top of
   existing export dropdown as entry point.

2. **Format resolver service** — `format_resolver.py` with 4-level resolution
   chain: auto-infer → user defaults → per-material override → at export time.
   `detect_content_types()` walks content_json for quiz/slide/branching nodes.
   16 tests in `test_format_resolver.py`.

3. **Model migration** — `export_format` String(30) → `export_targets` JSON list
   (same DB column name to avoid migration). `export_targets_list` property
   normalizes legacy string values.

4. **Preview + Package endpoints** — `GET /units/{id}/export/preview` returns
   resolved export plan; `POST /units/{id}/export/package` accepts per-material
   target overrides, delegates to IMSCC/SCORM services.

5. **User-level export defaults** — Settings → Export tab gains "Default Export
   Targets" section with toggleable pills per content type (Quiz, Slides,
   Branching). Saves to `teaching_preferences.export_defaults`.

6. **IMSCC/SCORM override support** — Both services accept `target_overrides`
   dict from the export dialog, checked before per-material `export_targets_list`.

### Key Files
- `frontend/src/components/ExportDialog/ExportDialog.tsx`, `MaterialExportRow.tsx`
- `frontend/src/services/exportApi.ts`
- `backend/app/services/format_resolver.py`
- `backend/app/schemas/export_preview.py`
- `backend/app/api/routes/export_preview.py`, `package_export.py`
- `frontend/src/features/settings/ExportTemplates.tsx` (extended)
- `frontend/src/pages/UnitPage.tsx` (dialog trigger added)

---

## Phase 6b — H5P Interactive Video (Optional)

**Status**: Not started
**Ships**: H5P Interactive Video export for video-type materials.

### Work Items

1. **InteractiveVideoNode Tiptap extension** — video URL + timeline markers
   pointing to embedded quiz nodes
2. **H5P Interactive Video exporter**

### Key Files (~4)
- `frontend/src/components/Editor/InteractiveVideoNode.ts`, `InteractiveVideoView.tsx`
- `backend/app/services/h5p_interactive_video_service.py`

### Dependencies: Phase 3 (H5P base builder), Phase 2 (quiz nodes for overlays)
### Note: Most speculative H5P type. Can be deferred indefinitely.

---

## Phase 6c — Export Progress Streaming (Nice-to-Have)

**Status**: Not started
**Ships**: Progress indicator and per-material error reporting for large unit exports.

### Work Items

1. **Backend SSE streaming** for export progress (material-by-material updates)
2. **Frontend progress bar** in the ExportDialog

### Dependencies: Phase 6a

---

## Intentionally Deferred

**Interactive HTML export** (standalone branching player with path-aware scoring)
uses the same branching card authoring from Phase 5 but outputs a self-contained
HTML file with a lightweight JS runtime instead of H5P. Can be added as a Phase 7
once Phase 5 ships and the branching card data model is proven.

---

## Summary

| Phase | Name | Key Deliverable | Status |
|-------|------|----------------|--------|
| 1 | Foundations | `content_json` storage, shared export data module | COMPLETE |
| 2 | Quiz Authoring | TipTap quiz nodes (5 question types) | COMPLETE |
| 3 | H5P Quiz + QTI | H5P Question Set, QTI from content_json, format selector, H5P embedding | COMPLETE |
| 4 | Slides | SlideBreak node, H5P Course Presentation | COMPLETE |
| 5 | Branching | Card authoring, map view, H5P Branching Scenario | COMPLETE |
| 6a | Export Dialog | Two-level export UI, 4-level format resolver, user defaults | COMPLETE |
| 6b | Interactive Video | H5P Interactive Video (optional) | Not started |
| 6c | Progress Streaming | SSE progress for large exports (nice-to-have) | Not started |

*Originally planned Feb 2026. Plan recovered from conversation transcript and
saved here Feb 2026.*
