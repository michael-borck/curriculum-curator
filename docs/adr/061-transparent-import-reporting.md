# 61. Transparent Import Reporting (No Silent Drops)

Date: 2026-02-25

## Status

Accepted

## Context

When importing IMSCC, SCORM, or file-based content, the app silently drops certain content types — images, videos, discussion boards, LTI tool links, rubrics, and more. Users only discover these gaps at export time, leading to frustration and lost trust.

The current behaviour:

| Content type | Current handling |
|---|---|
| HTML/text | Extracted and stored |
| PDF/DOCX/PPTX | Extracted and stored |
| QTI quizzes | Parsed into quiz questions |
| Images (PNG, JPG, SVG, etc.) | **Silently dropped** |
| Video files | **Silently dropped** |
| External links | Kept in HTML text, not tracked |
| Discussion boards | Flattened to "discussion" material or dropped |
| Announcements | **Silently dropped** |
| Rubrics/grading | **Silently dropped** |
| LTI/tool integrations | **Silently dropped** |
| Access control/dates | **Silently dropped** |
| Accessibility metadata | **Silently dropped** |

Users deserve transparency. Silently dropping content is a recipe for disgruntled users.

## Decision

**No silent drops.** Every content item in an import package must be accounted for in the import report. The policy:

### 1. Import what we can

- **Images**: Extract from ZIP/PPTX and store (uploads directory or inline). The PPTX extractor already pulls image blobs — extend this to IMSCC/SCORM packages.
- **Video URLs**: Keep as URL references in materials. Don't store video files — prompt user to provide a URL (YouTube, Vimeo, LMS-hosted stream).
- **External links**: Track as explicit material entries, not just inline HTML.
- **Discussion prompts**: Import as material with type "discussion".

### 2. Report what we can't

For content that genuinely can't be imported (LTI tools, rubrics, access control, announcements), the import summary must list them explicitly:

> **Imported:** 15 materials, 3 assessments, 2 quizzes, 8 images across 12 weeks.
> **Not imported:** 2 LTI tool links, 1 rubric, 3 announcement items.
> **Action needed:** 2 videos require a URL — provide links in the material editor.

### 3. Categorise unimported items

Each skipped item falls into one of:

- **Action needed** — user can fix (e.g., provide video URL, re-upload image that failed)
- **Not supported** — feature doesn't exist in the app (e.g., LTI tools, rubrics, access control)
- **Not applicable** — LMS-specific feature with no equivalent (e.g., announcements, student groups)

### 4. Surface at import time, not export time

The import summary screen is where users learn what happened. Don't defer surprises to export.

## Consequences

### Positive
- Users trust the import process — no hidden data loss
- Action-needed items are surfaced immediately, not discovered weeks later
- Image support means richer imported content
- Video URL references maintain media links without storing large files

### Negative
- Image storage increases disk usage (mitigated by upload size limits already in place)
- More complex import summary UI
- Video URL workflow requires user action (can't be fully automated)

### Neutral
- `import_provenance` JSON continues to store manifest mapping for round-trip export
- No persistent import history needed — the one-time summary is sufficient

## Implementation Notes

### Phase 1 (import reporting)
- Extend the unified import response to include categorised skipped items
- Frontend: show import summary with imported/skipped/action-needed sections

### Phase 2 (image import)
- Extract images from IMSCC/SCORM ZIP files
- Store in uploads directory, reference in material content
- PPTX image extraction already works — generalise the pattern

### Phase 3 (video URL references)
- Create video URL material type
- On import, detect video references and create placeholder materials
- Prompt user to provide streaming URLs

### Not planned
- LTI tool import (requires LMS-specific integration)
- Rubric import (no rubric model in the app)
- Announcement import (no announcement feature)
- These are correctly reported as "not supported" in the import summary

## References

- ADR-056: Export template extraction from PPTX
- `backend/app/services/unified_import_service.py` — orchestrates all import types
- `backend/app/services/file_import_service.py` — file-level extraction
- `backend/app/services/package_import_service.py` — IMSCC/SCORM package parsing
