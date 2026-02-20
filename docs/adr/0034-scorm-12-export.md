# ADR 0034: SCORM 1.2 Export

## Status

Accepted

## Date

2026-02-21

## Context

ADR-0030 introduced IMS Common Cartridge (IMSCC) export (originally v1.2, now downgraded to v1.1 for Moodle compatibility). However, many LMS platforms — particularly older versions of Moodle, Blackboard, and proprietary institutional systems — support SCORM 1.2 but not Common Cartridge. SCORM 1.2 remains the most widely supported e-learning package format across the global LMS ecosystem.

Educators need the ability to export their unit content in a format that works with these platforms.

### Version choices

- **IMSCC v1.1** (not 1.2 or 1.3): Moodle only supports CC 1.0 and 1.1. Since we only export webcontent resources (no QTI, no LTI), the format is identical across versions. v1.1 maximises LMS compatibility. Additional versions (1.2, 1.3) can be added later if needed for Canvas-specific features.
- **SCORM 1.2** (not 2004): SCORM 1.2 is universally supported by every LMS. SCORM 2004 adds sequencing and navigation complexity we don't need for content delivery.

## Decision

Add SCORM 1.2 export alongside the existing IMSCC v1.1 export. Both services share a common data-gathering layer (`unit_export_data.py`) to avoid duplication.

### Package structure

A SCORM 1.2 package is a ZIP file containing:

- **`imsmanifest.xml`** — IMS Content Packaging v1.1.2 manifest with ADL SCORM namespace. Schema is "ADL SCORM", version "1.2". Resources are marked with `adlcp:scormtype="sco"`.
- **`scorm_api.js`** — Minimal JavaScript wrapper that locates the LMS `window.API` object, calls `LMSInitialize`, sets `cmi.core.lesson_status` to `"completed"`, and calls `LMSFinish` on page unload.
- **HTML content pages** — Same structure as IMSCC (overview, weekly materials, assessments) but with `<script src="../scorm_api.js">` injected in the `<head>`.
- **`curriculum_curator_meta.json`** — Same round-trip metadata as IMSCC, with an additional `export_format: "scorm_1.2"` field.

### Shared module

The DB query logic (fetching unit, outline, topics, materials, assessments, learning outcomes, accreditation mappings) was extracted from `imscc_service.py` into `unit_export_data.py`. Both IMSCC and SCORM services import from this shared module, along with utilities (`_slugify`, `_escape_html`, `HTML_TEMPLATE`).

### Frontend

The single "Export IMSCC" button was replaced with a dropdown menu offering both "Export IMSCC v1.1 (.imscc)" and "Export SCORM 1.2 (.zip)". Version numbers are shown in the UI so educators know exactly what format they're getting.

### API

- `GET /api/units/{unit_id}/export/scorm` — returns a SCORM 1.2 ZIP package

## Consequences

- Educators can export to the two most widely supported LMS package formats.
- The shared data-gathering module reduces duplication and makes adding future export formats (e.g., xAPI, cmi5) straightforward.
- SCORM 1.2's completion tracking is minimal (marks lesson as "completed" on view). This is appropriate for content-delivery SCOs but does not support quiz scoring or complex sequencing — those would require SCORM 2004, which is out of scope.
- Import for both formats is deferred to a later phase.
