# 54. Import Provenance for Round-Trip Fidelity

Date: 2026-02-24

## Status

Accepted

## Context

ADRs 030, 034, and 042 established IMSCC/SCORM export and import. The current round-trip mechanism embeds a `curriculum_curator_meta.json` file in exported packages, preserving unit-level metadata (pedagogy, ULOs, accreditation mappings). However, several gaps undermine real-world round-trip workflows, particularly for educators moving content between Curriculum Curator and Canvas (or Blackboard during the transition period):

1. **Material categories are lost**: The `pre_class`/`in_class`/`post_class`/`resources` categories (ADR-053) are not exported — not in the CC manifest, not in filenames, and not in the round-trip metadata. All materials revert to `general` on re-import.

2. **Per-material metadata is not preserved**: Material-to-ULO links, material-to-assessment links, material types, ordering, and status are absent from `curriculum_curator_meta.json`.

3. **CC identifiers are discarded on import**: When importing a Canvas IMSCC, the original CC identifiers (`m_101`, `i_201`, etc.) and organization structure are thrown away. On re-export, entirely new identifiers are generated, so the LMS treats the re-import as a brand new course rather than an update to the existing shell.

4. **Blackboard content areas mapped as weeks**: The generic import assumes each top-level manifest item is a week. Blackboard uses structural content areas ("Course Information", "Content", "Assignments"), not weekly modules. A Blackboard export with 4 content areas creates a 4-week unit.

5. **Canvas `module_meta.xml` is ignored**: Canvas stores detailed module structure (positions, indent levels, completion requirements) in a Canvas-specific extension file. Only the standard `imsmanifest.xml` is parsed.

6. **`$IMS-CC-FILEBASE$` tokens not resolved**: Canvas HTML content uses `%24IMS-CC-FILEBASE%24` for file references. These are not resolved on import, leaving broken image/file links.

The university is retiring Blackboard at the end of 2026 and switching to Canvas, making Canvas round-trip fidelity the priority.

## Decision

### 1. Store import provenance on the Unit model

Add a nullable JSON field `import_provenance` to the `Unit` model that captures the source LMS, original CC identifiers, and the mapping between CC items and internal records:

```python
# On Unit model
import_provenance: dict[str, Any] | None = Column(JSON, nullable=True)
```

Structure:

```json
{
  "schema_version": "1.0",
  "source_lms": "canvas",
  "source_format": "imscc",
  "imported_at": "2026-02-24T10:30:00Z",
  "original_title": "ICT100 Introduction to IT",
  "organization": [
    {
      "cc_identifier": "m_101",
      "title": "Module 1: Introduction",
      "mapped_week": 1,
      "items": [
        {
          "cc_identifier": "i_201",
          "cc_href": "web_content/welcome.html",
          "cc_resource_type": "webcontent",
          "original_title": "Welcome and Overview",
          "mapped_to_type": "material",
          "mapped_to_id": "uuid-of-our-material",
          "category_hint": "pre_class"
        },
        {
          "cc_identifier": "i_202",
          "cc_href": "web_content/lecture1.html",
          "cc_resource_type": "webcontent",
          "original_title": "Lecture: What is IT?",
          "mapped_to_type": "material",
          "mapped_to_id": "uuid-of-another-material",
          "category_hint": "in_class"
        }
      ]
    }
  ],
  "unmapped_resources": [
    {
      "cc_identifier": "r_999",
      "cc_href": "lti_links/turnitin.xml",
      "cc_resource_type": "imsbasiclti_xmlv1p0",
      "reason": "unsupported_type"
    }
  ]
}
```

### 2. Provenance-aware export

When exporting a unit that has `import_provenance`:

- **If target LMS matches source LMS**: Use stored CC identifiers as the skeleton. For each provenance item, look up the mapped internal record. If it still exists, export its current content under the original CC identifier. If the internal record was deleted, omit the item (user manages the orphan in the LMS). New items (no provenance mapping) get fresh identifiers and are appended to the relevant week/module.

- **If target LMS differs or no provenance**: Export from scratch using current behaviour. Provenance from a different LMS is not useful.

This maximises structural preservation in the common case: user imports from Canvas, edits content in Curriculum Curator, re-exports to the same Canvas shell.

### 3. Enrich `curriculum_curator_meta.json` to v2

Extend the round-trip metadata to include per-material and per-assessment data:

```json
{
  "version": "2.0",
  "exported_from": "curriculum-curator",
  "exported_at": "...",
  "unit": { "...existing fields..." },
  "learning_outcomes": [ "...existing..." ],
  "aol_mappings": [ "...existing..." ],
  "sdg_mappings": [ "...existing..." ],
  "materials": [
    {
      "id": "uuid",
      "week_number": 1,
      "title": "Welcome Reading",
      "type": "reading",
      "category": "pre_class",
      "order_index": 0,
      "status": "complete",
      "ulo_ids": ["uuid-ulo1", "uuid-ulo3"],
      "assessment_ids": ["uuid-assess1"]
    }
  ],
  "assessments": [
    {
      "id": "uuid",
      "title": "Quiz 1",
      "type": "summative",
      "category": "quiz",
      "weight": 10.0,
      "due_week": 3,
      "release_week": 1,
      "duration": "30 minutes",
      "submission_type": "online",
      "group_work": false,
      "ulo_ids": ["uuid-ulo2"]
    }
  ],
  "weekly_topics": [
    {
      "week_number": 1,
      "topic_title": "Introduction to IT",
      "week_type": "regular"
    }
  ]
}
```

Import of v2 metadata restores categories, material types, ordering, ULO linkages, and assessment details. Import of v1 metadata continues to work (materials fall back to current heuristic behaviour).

### 4. Map categories to CC organization structure

On export, encode categories as structural hints that LMSs can display meaningfully:

- Within each week/module in the manifest, group items by category and insert **text/label items** as sub-headers: `"--- Pre-class ---"`, `"--- In-class ---"`, etc.
- These render as non-clickable section dividers in Canvas modules.
- On re-import, detect these label patterns and use them to restore category assignments (via `category_hint` in provenance, or by parsing the label items in generic mode).

### 5. Canvas-aware import enhancements

- **Parse `module_meta.xml`**: When a Canvas package is detected, read `course_settings/module_meta.xml` for module positions, item ordering, and indent levels. Use indent levels as hints for category assignment (indented items under a heading may indicate sub-grouping).
- **Resolve `$IMS-CC-FILEBASE$` tokens**: Replace `%24IMS-CC-FILEBASE%24` with relative paths to the actual files in the ZIP. Store referenced files (images, PDFs) as material attachments.
- **Detect Canvas content types**: Canvas uses `content_type` in `module_meta.xml` (`WikiPage`, `Assignment`, `Discussion`, `ExternalUrl`, `File`, `SubHeader`). Map `SubHeader` to category labels; map the rest to materials/assessments using the existing classification logic enhanced with Canvas type hints.

### 6. Blackboard-aware import

- **Detect content-area structure**: When source LMS is Blackboard and top-level items have names like "Course Information", "Content", "Assignments" (rather than "Week 1", "Module 1"), flag as non-weekly structure.
- **Prompt user for week mapping**: In the import preview UI, show the detected content areas and let the user drag/assign them to weeks, or choose "flatten all into Week 1" as a default.
- **Lower priority**: Blackboard is being retired. Basic support is sufficient; Canvas fidelity is the investment priority.

## Consequences

### Positive

- Edit-only round-trips to Canvas become essentially lossless — same identifiers, same structure, updated content
- Material categories survive export and re-import via both provenance hints and enriched meta.json
- Per-material metadata (ULO links, assessment links, types, ordering) survives round-trip
- Graceful degradation: deletions and additions are handled predictably (dropped/appended), user manages residual cleanup in the LMS
- Provenance is just a JSON column on Unit — no new tables, no new relationships
- v1 meta.json imports continue to work unchanged

### Negative

- Provenance JSON can grow large for units with many materials (mitigated: it's nullable, only populated on import, and JSON compresses well in SQLite)
- Provenance mappings go stale if the user heavily restructures — identifiers pointing to deleted records are harmless (they get skipped on export) but the stored organization may diverge from reality
- Maintaining CC identifier stability requires care in the export path — must not accidentally regenerate identifiers for items that have provenance
- Canvas-specific parsing (module_meta.xml, $IMS-CC-FILEBASE$) adds Canvas coupling, though this is pragmatic given the university's LMS direction

### Neutral

- Changes outside Curriculum Curator are explicitly out of scope — if a colleague edits the Canvas shell directly, the next re-import from this app will overwrite those changes. This is documented and accepted.
- Provenance is per-unit, not per-user — if two users import the same Canvas course, they get separate Unit records with separate provenance.

## Implementation Order

1. **Meta.json v2**: Enrich export metadata with materials, assessments, weekly topics (backwards-compatible — v1 import still works)
2. **Import provenance storage**: Capture CC identifiers and mappings on import, store in `Unit.import_provenance`
3. **Provenance-aware export**: Use stored identifiers when re-exporting to the same LMS
4. **Category encoding in CC manifest**: Add sub-header items for category grouping
5. **Canvas-specific import**: Parse `module_meta.xml`, resolve file tokens
6. **Blackboard content-area detection**: Lower priority; basic heuristic + user prompt

## Alternatives Considered

### Full manifest storage + separate mapping table

Store the entire raw `imsmanifest.xml` and a `cc_mapping` table with rows for each CC identifier → internal ID pair.

Rejected: the separate table adds schema complexity (foreign keys, cascading deletes, migration) for the same data that fits cleanly in a JSON column. The raw manifest is useful for debugging but not needed for the export path — the structured provenance captures everything needed to reconstruct identifiers.

### LMS API integration (Canvas REST API)

Use the Canvas API to directly push/pull content, avoiding the IMSCC round-trip entirely.

Rejected for now: requires per-institution OAuth configuration, API tokens, and admin cooperation. Many universities restrict API access. IMSCC import/export is universally available to instructors without admin involvement. API integration remains a future possibility (especially for Moodle, which is open source) but is not a prerequisite for improved round-trip fidelity.

### Store provenance in a separate file (not on Unit model)

Keep a `.provenance.json` file on disk alongside the database.

Rejected: the provenance is logically part of the unit and should travel with it (database backups, unit duplication, etc.). A JSON column on the Unit model is simpler and more reliable.

## References

- [ADR-030: IMS Common Cartridge Export](030-ims-common-cartridge-export.md)
- [ADR-034: SCORM 1.2 Export](034-scorm-12-export.md)
- [ADR-042: IMSCC and SCORM Import with Round-Trip Detection](042-package-import-round-trip.md)
- [ADR-053: Material Content Categories](053-material-content-categories.md)
- `backend/app/services/imscc_service.py`
- `backend/app/services/package_import_service.py`
- `backend/app/models/unit.py`
