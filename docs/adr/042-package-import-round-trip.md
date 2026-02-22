# 42. IMSCC and SCORM Import with Round-Trip Detection

Date: 2026-02-22

## Status

Accepted

## Context

ADR-030 and ADR-034 cover exporting units as IMSCC and SCORM packages. Users also need to import packages — both packages previously exported from Curriculum Curator ("round-trip") and packages exported from other LMSs like Canvas, Moodle, or Blackboard ("generic"). These two scenarios have very different data fidelity: our own exports embed full metadata (pedagogy, ULOs, accreditation mappings), while generic LMS exports contain only basic content structure.

## Decision

Implement a dual-mode import system that detects whether a package originated from Curriculum Curator and adjusts its parsing strategy accordingly.

**Format detection** (IMSCC vs SCORM):
- If `imsmanifest.xml` contains `"adlnet.org"` or `"ADL SCORM"` → SCORM 1.2
- Otherwise → IMSCC
- Simple string matching, no full XML schema validation

**Round-trip detection:**
- If the ZIP contains `curriculum_curator_meta.json` → round-trip mode
- Otherwise → generic mode

**Round-trip mode** restores the full data model: unit metadata, ULOs with Bloom's levels, graduate capability mappings, AoL mappings, SDG mappings, weekly topics, materials (from `week{NN}/` paths), and assessments (from `assessments/` path). Pedagogy and accreditation data survive the export/import cycle.

**Generic mode** uses heuristics to reconstruct structure:
- LMS source detection via keyword scan ("canvas", "instructure", "moodle", "blackboard", "brightspace") in manifest text
- Unit code extraction via regex `[A-Z]{2,6}\d{3,5}` from title or manifest
- Item classification: title keywords (`quiz`, `exam`, `assignment`, etc.) determine assessment vs material; filename prefixes (`lecture_`, `quiz_`, etc.) determine material type
- Sensible defaults: inquiry-based pedagogy, intermediate difficulty, 6 credit points
- IMS namespace detection tries 5 namespace URIs (3 CC versions, 1 generic CP, 1 SCORM ADL) before falling back to no-namespace parsing

## Consequences

### Positive
- Full round-trip fidelity — export from Curriculum Curator, import into LMS, export from LMS, import back without metadata loss
- Generic imports work with real-world LMS exports without requiring users to manually classify content
- LMS-aware heuristics improve classification accuracy for major platforms

### Negative
- Heuristic classification can miscategorise items — a material titled "Test Your Knowledge" would be classified as an assessment
- Generic imports lose pedagogy and accreditation data that doesn't exist in standard LMS packages
- Keyword lists and regex patterns need maintenance as LMS formats evolve

### Neutral
- HTML content is cleaned via BeautifulSoup (scripts removed, h1 extracted as title) — some LMS-specific formatting may be lost
- Generic defaults (inquiry-based, intermediate) are reasonable but may not match the original unit

## Alternatives Considered

### Full IMS/SCORM Schema Validation
- Parse against the official XSD schemas for strict compliance
- Rejected: real-world LMS exports frequently deviate from the spec; strict validation would reject valid packages from Canvas/Moodle

### Single Import Mode (Generic Only)
- Treat all packages the same, always use heuristics
- Rejected: wastes the rich metadata we embed in our own exports; round-trip fidelity is a key feature for users who work across LMS boundaries

### Metadata in Manifest Extensions
- Embed our metadata as IMS manifest extensions instead of a separate JSON file
- Rejected: complicates the manifest XML and risks breaking LMS import of our packages; a separate file is invisible to LMSs that don't know about it

## Implementation Notes

- The import runs as a background task tracked via `ImportTaskStore` (see ADR-043)
- Namespace handling: iterates `["imsccv1p1", "imsccv1p2", "imsccv1p3", "imscp_v1p1", "adlcp_rootv1p2"]` to find the right IMS namespace
- Week assignment for round-trip uses directory structure (`week01/`, `week02/`); for generic imports, items are assigned to weeks based on manifest order
- Assessment keywords: `{"quiz", "exam", "test", "assignment", "midterm", "final", "assessment"}`

## References

- [ADR-030: IMS Common Cartridge Export](030-ims-common-cartridge-export.md)
- [ADR-034: SCORM 1.2 Export](034-scorm-12-export.md)
- `backend/app/services/package_import_service.py`
