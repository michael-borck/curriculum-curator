# P3 Remaining: Implementation Plan

> Closes all 4 **Partial** user stories and 4 **Planned** P3 stories.
> Dependency order: each layer unlocks the next.

## Layer 1: Image Upload Infrastructure

**Unlocks**: PPTX image extraction (6.6), editor image upload (15.4)

### 1.1 Backend: Image upload endpoint
- [x] `POST /api/materials/units/{unit_id}/materials/{material_id}/images` — accept file upload, store in content repo
- [x] Return URL path for embedding
- [x] `GET /api/materials/units/{unit_id}/materials/{material_id}/images/{filename}` — serve stored images
- [x] Supported formats: PNG, JPG, GIF, SVG, WebP
- [x] Size limit: configurable (default 5MB per image)

### 1.2 Frontend: TipTap image upload handler
- [x] Add upload button to TipTap toolbar (ImagePlus icon + ImageInsertDialog)
- [x] File picker → upload to endpoint → insert image into editor
- [x] Show upload progress indicator
- [x] Preview before insert

**User story**: 15.4 ✅

---

## Layer 2: Import Improvements

### 2.1 PPTX image extraction (6.6)
- [x] Update `python-pptx` extraction to detect picture shapes and extract image bytes
- [x] Extract images from slide shapes with `{{IMAGE:filename}}` placeholders in markdown
- [x] Save extracted images via Layer 1 image storage
- [x] Reference images inline in generated markdown
- [x] Test coverage in `test_image_upload.py`

**User story**: 6.6 (partial → done) ✅

### 2.2 Post-import enhance prompt (6.4)
- [x] After successful import (PDF, DOCX, PPTX), show "Enhance with AI?" button
- [x] Clicking triggers existing enhance API with Learning Design context (already wired from Phase 3 work)
- [x] Pass `unit_id` and `design_id` automatically from import context
- [x] Batch enhance all imported materials in sequence ("Enhance All with AI" button)

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
- [x] Persist config in database (plugin_configurations table, loaded on startup)

### 3.4 Backend: Spell checker Australian English support
- [x] Extend technical whitelist with 60+ Australian educational terms (programme, honours, behaviour, organisation, analyse, specialisation, colour, centre, enrolment, etc.)
- [x] Grammar validator defaults to British spelling mode for Australian users (configurable via `spelling_standard` plugin config)

### 3.5 Frontend: Quality panel in editor
- [x] Add "Quality Checks" panel in editor right sidebar
- [x] Shows per-validator scores with colour-coded indicators
- [x] Expandable issue list with suggestions per validator
- [x] "Auto-fix All" button runs remediators on current content
- [x] "Run Quality Checks" button re-runs validation after edits
- [x] Individual validator toggle via Settings > Quality Plugins tab

### 3.6 Frontend: Quality score on material cards
- [x] Show quality badge (A/B/C/D colour pill) on material list items
- [x] Tooltip shows numeric score out of 100
- [x] Validation endpoint persists quality_score to material when `material_id` query param provided
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
