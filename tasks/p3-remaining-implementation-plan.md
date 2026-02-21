# P3 Remaining: Implementation Plan

> Closes all 4 **Partial** user stories and 4 **Planned** P3 stories.
> Dependency order: each layer unlocks the next.

## Layer 1: Image Upload Infrastructure

**Unlocks**: PPTX image extraction (6.6), editor image upload (15.4)

### 1.1 Backend: Image upload endpoint
- [ ] `POST /api/materials/{material_id}/images` — accept file upload, store in content repo under `materials/{id}/images/`
- [ ] Return relative path for markdown embedding
- [ ] `GET /api/materials/{material_id}/images/{filename}` — serve stored images
- [ ] Supported formats: PNG, JPG, GIF, SVG, WebP
- [ ] Size limit: configurable (default 5MB per image)

### 1.2 Frontend: TipTap image upload handler
- [ ] Add upload button to TipTap toolbar (alongside existing URL insert)
- [ ] File picker → upload to endpoint → insert markdown image with relative path
- [ ] Show upload progress indicator
- [ ] Preview before insert

**User story**: 15.4 ✅

---

## Layer 2: Import Improvements

### 2.1 PPTX image extraction (6.6)
- [ ] Update `python-pptx` extraction to distinguish content shapes vs master/background
- [ ] Extract `MSO_SHAPE_TYPE.PICTURE` from slide shapes only (not layouts/masters)
- [ ] Save extracted images via Layer 1 image storage
- [ ] Reference images inline in generated markdown
- [ ] Skip decorative-only slides (background image, no text) — log as "skipped: decorative"
- [ ] Add pre-import notice: "Extracts text, images, and notes. Presentation styling is not imported."

**User story**: 6.6 (partial → done) ✅

### 2.2 Post-import enhance prompt (6.4)
- [x] After successful import (PDF, DOCX, PPTX), show "Enhance with AI?" button
- [x] Clicking triggers existing enhance API with Learning Design context (already wired from Phase 3 work)
- [x] Pass `unit_id` and `design_id` automatically from import context
- [ ] Optional: batch enhance all imported materials in sequence

**User story**: 6.4 (partial → done) ✅

---

## Layer 3: Wire Plugin System

**Independent of Layers 1-2. All 9 plugins are production-ready, just need routes + UI.**

### 3.1 Backend: Validation endpoint
- [x] `POST /api/plugins/validate` — run validators on content (body param)
- [x] Returns: per-plugin results (score, issues, suggestions), overall score
- [x] Accepts optional `validators` param to run specific subset
- [x] Wire `plugin_manager.validate_content()` — already handles priority ordering

### 3.2 Backend: Remediation endpoint
- [x] `POST /api/plugins/remediate` — run remediators on content
- [x] Returns: modified content, list of changes applied
- [x] Accepts optional `remediators` param for specific subset

### 3.3 Backend: Plugin configuration endpoint
- [x] `GET /api/plugins` — list all available plugins with enabled/disabled status
- [x] `PATCH /api/plugins/{name}` — enable/disable, set priority, update config
- [ ] Persist config in database (currently in-memory only)

### 3.4 Backend: Spell checker Australian English support
- [x] Extend technical whitelist with 60+ Australian educational terms (programme, honours, behaviour, organisation, analyse, specialisation, colour, centre, enrolment, etc.)
- [ ] Consider: grammar validator's British/American consistency check — default to "British" mode for Australian users

### 3.5 Frontend: Quality panel in editor
- [x] Add "Quality Checks" panel in editor right sidebar
- [x] Shows per-validator scores with colour-coded indicators
- [x] Expandable issue list with suggestions per validator
- [x] "Auto-fix All" button runs remediators on current content
- [x] "Run Quality Checks" button re-runs validation after edits
- [x] Individual validator toggle via Settings > Quality Plugins tab

### 3.6 Frontend: Quality score on material cards
- [ ] Show quality badge (A-F or colour dot) on material list items
- [ ] Tooltip shows breakdown (readability, grammar, spelling scores)
- [ ] Optional: unit-level aggregate quality score on dashboard

**User stories**: 7.1, 7.2 (partial → done), 7.3 (planned → done) ✅

---

## Layer 4: LMS Package Import

**Independent of Layers 1-3.**

### 4.1 IMSCC import (9.2)
- [ ] `POST /api/import/imscc/{unit_id}` — upload .imscc file
- [ ] Parse `imsmanifest.xml` — extract organisations, resources, metadata
- [ ] Map CC content types to material types (webcontent → lecture/reading, assessment → quiz)
- [ ] Extract HTML resources → convert to markdown (strip styling per ADR-0038)
- [ ] Extract embedded files (images, attachments) → store via image infrastructure
- [ ] Create materials in unit with week assignment (from organisation structure)
- [ ] Return import summary (materials created, items skipped, warnings)
- [ ] Pre-import preview: show what will be imported before committing

### 4.2 SCORM import (9.7)
- [ ] `POST /api/import/scorm/{unit_id}` — upload SCORM .zip
- [ ] Parse `imsmanifest.xml` (SCORM variant) — extract SCOs and resources
- [ ] Extract HTML content from SCO launch pages → convert to markdown
- [ ] Handle SCORM-specific structures (sequencing, prerequisites) as metadata
- [ ] Same storage/conversion approach as IMSCC import
- [ ] Return import summary

**User stories**: 9.2, 9.7 (planned → done) ✅

---

## Summary

| Layer | Stories Closed | Status Before | Status After |
|-------|---------------|---------------|-------------|
| 1. Image upload | 15.4 | Planned | Done |
| 2. Import improvements | 6.4, 6.6 | Partial | Done |
| 3. Plugin wiring | 7.1, 7.2, 7.3 | Partial/Planned | Done |
| 4. LMS import | 9.2, 9.7 | Planned | Done |

**Total**: 4 Partial → Done, 4 Planned → Done = **8 stories closed**

## Implementation Order

1. Layer 1 (image infrastructure) — unlocks Layer 2
2. Layer 2 (import improvements) — depends on Layer 1
3. Layer 3 (plugin wiring) — independent, can parallel with 1+2
4. Layer 4 (LMS import) — independent, can parallel with 3

Layers 3 and 4 are independent of each other and of Layers 1-2, so could be
worked on in parallel or in any order after Layer 1+2 are done.

*Created: 2026-02-21*
