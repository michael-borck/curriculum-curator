# Speaker Notes — Implementation Plan

**Status:** Phase 1 (export half) shipped 2026-04-10. Phases 2–4 still planned.
**Date:** 2026-04-10
**Related:** [ADR-064](adr/064-rough-slides-as-feature.md), [ADR-038](adr/038-content-not-presentation.md), [ADR-048](adr/048-tiptap-custom-extensions.md), [ADR-032](adr/032-ai-assistance-levels.md)

## Background

Speaker notes are currently a gap in the import → edit → export pipeline:

- **Import** (`file_import_service.py:381-383`): PPTX notes are extracted but flattened into slide body text as `Notes: <text>`, losing their structural identity.
- **Storage:** `content_json` has no notes node type. TipTap editor has no notes UI.
- **Export** (`export_service.py:_convert_pandoc`): no `::: notes` Pandoc fenced divs emitted. Notes never reach the PowerPoint speaker notes pane.

ADR-064 established that speaker notes should be first-class citizens: the slide is scaffolding for delivery, and the notes carry the actual teaching. This plan implements that stance end-to-end.

## Guiding decisions

These were decided before planning and are not revisited in the phases below:

1. **Storage model:** new `speakerNotes` TipTap node embedded in `content_json`, placed adjacent to its slide. One document tree, one source of truth. Natural round-trip via Pandoc's `::: notes` fenced-div syntax.
2. **Exports other than PPTX:** drop notes from DOCX, PDF, HTML, IMSCC, SCORM. Notes are a delivery aid, not a student-facing artefact. Keeps exports simple and aligned with ADR-064.
3. **Coverage metric:** visibility indicator only ("5/8 slides have notes"), not scored into the quality dashboard. Some excellent lecturers don't use notes — the tool should let them teach their way.
4. **No migration:** existing materials with flattened `Notes: ...` body text stay as-is. Production DB is empty; dev users can re-import.
5. **AI generation:** per-slide opt-out toggle (default on), batched into a single LLM call when the user triggers generation. Propose/apply review before committing.
6. **Phasing:** ship in discrete PR-sized phases. Round-trip fix lands first, workflow visibility and AI follow.

## Phase 1 — Schema & round-trip pipeline

**Goal:** notes survive PPTX → import → storage → export → PPTX round-trip. No UI work beyond what's needed to render the node.

### Backend

- **`content_json` schema:** add `speakerNotes` as a valid node type (block-level, content: `block+`, attributes: `aiSelected: boolean = true`).
- **`slide_splitter.py`:** update `split_at_slide_breaks` so trailing `speakerNotes` nodes attach to the preceding slide segment, not a new segment or orphaned.
- **`content_json_renderer.py`:**
  - HTML path: render `speakerNotes` as `<aside data-type="speaker-notes">...</aside>` (editor display only).
  - Pandoc-bound markdown path: emit `\n::: notes\n<markdown>\n:::\n` blocks. Add a `target` parameter to distinguish editor HTML from export markdown.
- **`file_import_service._extract_pptx`:**
  - Replace the `Notes: <text>` flattening at lines 381-383.
  - After each slide's content is emitted, append a structured `speakerNotes` node containing the extracted notes text (parsed as plain paragraphs).
  - Empty notes → omit the node (no empty scaffolding on import).
- **`export_service.py`:**
  - The slide-aware PPTX path at lines 274-289 currently builds segments manually. Update to pass notes through to the markdown that reaches Pandoc.
  - For DOCX/PDF/HTML/IMSCC/SCORM paths: strip `speakerNotes` nodes from `content_json` before rendering. A small helper `strip_speaker_notes(content_json)` keeps this explicit.
- **Other importers (PDF, DOCX, IMSCC, SCORM):** no work — none have a speaker notes concept.

### Frontend

- **TipTap extension:** new `SpeakerNotes` node in `frontend/src/components/Editor/extensions/` (follows ADR-048 pattern). Minimal render: styled block, distinct background, "Speaker notes" label. No authoring affordances yet — this phase is pipeline-only.
- **Type definitions:** add the variant to `frontend/src/types/contentJson.ts`.
- **Register** in the editor's extension list so stored content doesn't error on load.

### Tests

- **Backend unit:**
  - `test_slide_splitter.py`: notes nodes attach to the correct segment.
  - `test_content_json_renderer.py`: emits `::: notes` for pandoc target, `<aside>` for editor target.
  - `test_file_import_service.py`: PPTX with notes → structured nodes, not flattened text. (Use a real python-pptx fixture, not a mock.)
- **Backend integration:** full round-trip — import a fixture PPTX with known notes, export back to PPTX, parse the output with python-pptx, assert `slide.notes_slide.notes_text_frame.text` matches.
- **Frontend:** basic render test for the `SpeakerNotes` node.

### Exit criteria

Round-trip works end-to-end. Notes are stored structurally, imported correctly, and appear in PowerPoint's speaker notes pane on export. Editor displays them but has no authoring affordances — that's Phase 2.

### Update

- Mark the implementation-notes gap in ADR-064 as resolved (edit in place — ADRs are immutable except for cross-links and status, but the implementation-notes follow-up tracker is fair to update).

---

## Phase 2 — Editor authoring UX

**Goal:** notes become a normal, visible part of slide authoring. Users can add, edit, and remove them fluidly.

### Affordances

- **Inline rendering:** `SpeakerNotes` node renders directly beneath its slide content. Muted background, smaller text, left border accent, "Speaker notes" label in the corner. Not collapsed by default — visibility is the point.
- **Auto-scaffold on slide-break insertion:** when the user inserts an `<hr>` slide break, automatically insert an empty `SpeakerNotes` node beneath it. User can delete if unwanted.
- **Empty-state affordance:** if a slide has no notes node, show a subtle "+ Add speaker notes" button beneath the slide. One click creates and focuses the node.
- **Delete affordance:** standard TipTap node deletion (select + delete, or a node-handle context menu).
- **Placeholder text** inside an empty notes node: *"What you'll say but not show. Notes export to PowerPoint's speaker notes pane."*

### Coverage indicator

- Material list card: small badge showing "Notes: N/M" where M is slide count and N is slides with non-empty notes. Purely informational — no colour alarm, no nagging.
- Computed on the frontend from `content_json`, no backend endpoint needed.

### Tooltip / onboarding

- First time a user creates a slide-break material (per-user flag in `localStorage` or user prefs), show a one-time tip card: *"Speaker notes carry your teaching — what you say, not what students see on screen. They export to PowerPoint's speaker notes pane. [Learn why](link to ADR-064 user-facing summary)."*

### Tests

- Frontend component tests for the notes node affordances.
- Frontend tests for auto-scaffold behaviour when slide break is inserted.
- E2E (Playwright): create a material, insert slide break, verify notes block auto-appears, type into it, save, reload, verify content persists.

### Exit criteria

A user with no prior knowledge can discover, add, edit, and delete speaker notes without documentation. Coverage badge is visible on material cards.

---

## Phase 3 — AI-assisted note generation

**Goal:** when AI is enabled, users can draft notes for selected slides in a single batched call, then review and apply.

### Per-slide selection toggle

- Add `aiSelected: boolean` attribute to the `SpeakerNotes` node (already declared in Phase 1 schema, default `true`).
- Small toggle checkbox on the notes block, labelled "Include in AI generation" (or a compact icon toggle).
- Default: `true` — opt-out model. User ticks off slides they don't want AI notes for.
- "Select all / none" bulk control in the material toolbar or AI Assistant sidebar.

### Bulk generation flow

1. User clicks **"Generate speaker notes with AI"** (surfaced in the AI Assistant sidebar, gated on AI assistance level per ADR-032).
2. Confirmation panel: *"Generate notes for N of M slides. Estimated cost: ~X tokens."* (Cost estimate via existing tracking from ADR-051.)
3. Single batched LLM call: prompt includes all slides flagged `aiSelected=true`, with slide indices, content, and the material's pedagogy/ULO context (via `design_context.py`).
4. Response: structured JSON with one notes draft per slide index (use ADR-045 structured-output retry loop).
5. **Propose/apply review pane** (per ADR-039 convention): show each slide's existing notes alongside the AI draft, with accept/edit/reject per slide. User commits in one action.

### Prompt design

- New system-seed template in `seed_prompt_templates.py`, e.g. `generate_speaker_notes_batch`.
- Critical constraints in the prompt (tied to ADR-064):
  - *"Do not repeat the slide text — speaker notes expand on what's visible, they don't duplicate it."* (Mayer redundancy principle)
  - *"Write in a lecturer's conversational voice, first-person, as if speaking aloud to students."*
  - *"Include brief transitions between slides where natural."*
  - *"Aim for 2–4 sentences per slide unless the content warrants more."*
- Template variables: `slides` (array of `{index, title, content, existing_notes}`), `pedagogy`, `week_topic`, `unit_ulos`.

### Respecting AI assistance levels (ADR-032)

- If `ai_assistance_level == "none"`: generate button is hidden entirely.
- If `"refine_only"`: generate button only appears for slides that already have non-empty notes (refining, not creating). Worth confirming with user whether this is the right interpretation.
- If `"full"`: generate works on any selected slides, including empty ones.

### Backend

- New endpoint: `POST /api/materials/{material_id}/generate-speaker-notes` — body `{ slide_indices: number[] }`.
- Uses existing `llm_service.py` with the new prompt template.
- Returns structured response for the propose/apply pane.
- Does **not** mutate `content_json` — the frontend applies changes after user review.

### Tests

- Backend unit: prompt template rendering, structured response parsing, ADR-032 gating.
- Frontend: toggle state persists, select-all works, propose/apply pane renders drafts correctly.
- Manual QA: generate for a real material, verify notes are conversational and don't duplicate slide text (the hard part to automate).

### Exit criteria

AI can draft notes for selected slides in one batched call. User reviews before anything commits. Respects assistance level. Prompt consistently produces lecturer-voice notes that don't repeat slide content.

---

## Phase 4 — Polish & documentation

**Goal:** tie off loose ends that aren't worth blocking earlier phases on.

- **User story:** add to `docs/user-stories/` in the slides/export area.
- **Getting started guide:** brief section in `docs/guides/getting-started.md` introducing speaker notes as part of the slide-authoring workflow.
- **Teaching styles guide:** note that speaker notes are pedagogy-agnostic but especially valuable for traditional/flipped styles where the educator's spoken content matters most.
- **ADR-064 implementation notes:** mark the speaker-notes gap as resolved (link to this plan doc and the merged PRs).
- **Prompt audit:** review existing slide-generation prompts in `seed_prompt_templates.py` to ensure they don't ask the model for "engaging visuals" or "compelling slide content" — the model should be generating scaffold content, with notes carrying the teaching (per ADR-064).

---

## Open questions resolved

| Question | Decision |
|---|---|
| Notes in DOCX/PDF exports? | Drop entirely. |
| AI generation granularity? | Per-slide opt-out toggle, single batched call. |
| Quality dashboard integration? | No — visibility indicator only. |
| Migration of flattened `Notes: ...` text? | No migration. |
| Phasing? | Step-by-step PRs (Phases 1–4). |

## Remaining open questions

1. **ADR-032 `refine_only` interpretation:** should the generate button appear for slides without existing notes? My read is no (refining implies existing content), but worth confirming before Phase 3.
2. **Notes persistence when slide break is deleted:** if a user deletes a slide break, what happens to the trailing notes block? Options: (a) delete with the slide, (b) keep as orphaned block, (c) merge into previous slide. Recommend (a) — delete together, it's the least surprising.
3. **Mermaid/video/embedded content inside notes:** should `SpeakerNotes` content be `block+` (allowing rich content) or restricted to paragraphs and lists? Recommend `block+` for flexibility — a lecturer might want a small table or code snippet in their notes. No extra implementation cost.

These can be resolved as each phase starts — none block Phase 1.

## Phase dependencies

```
Phase 1 (pipeline)  ──▶  Phase 2 (editor UX)  ──▶  Phase 3 (AI)
                                                ╲
                                                 ──▶  Phase 4 (polish)
```

Phase 2 depends on Phase 1 (needs the node type). Phase 3 depends on Phase 2 (needs the toggle UI surface). Phase 4 depends on Phase 3 (documentation references shipped behaviour).

## Out of scope

Explicitly not doing in this plan:

- Slide-level notes on non-slide materials (e.g. readings) — notes are a slide concept
- Per-export toggle to include notes in DOCX/PDF — decided against
- Quality scoring based on notes coverage — decided against
- Automatic translation of notes to other languages — future feature if requested
- Notes history / diff tracking — git-backed storage already handles this
- Shared notes between slides — not a real use case
