# ADR-0030: IMS Common Cartridge Export

## Status

Accepted

## Context

Educators need to move unit content between Curriculum Curator and LMS platforms (Blackboard, Canvas, Moodle). The IMS Common Cartridge (CC) specification is the de facto interoperability standard for packaging educational content across LMS systems.

We need a way to export a unit's weekly materials, assessments, learning outcomes, and accreditation mappings as a portable package that any CC-compliant LMS can import.

## Decision

### Phase 1: Export (this ADR)

Implement IMS Common Cartridge **v1.2** export for individual units:

- **Format**: `.imscc` file (ZIP archive) containing `imsmanifest.xml` and HTML resource files
- **Target version**: CC v1.2 — both Blackboard and Canvas handle it reliably
- **No new dependencies**: Uses only Python stdlib (`zipfile`, `xml.etree.ElementTree`, `json`, `io`)
- **API endpoint**: `GET /api/units/{unit_id}/export/imscc` (authenticated, ownership-checked)
- **Frontend**: "Export IMSCC" button on unit detail page header

### Package structure

```
package.imscc (ZIP)
├── imsmanifest.xml
├── curriculum_curator_meta.json
├── overview/
│   ├── learning_outcomes.html
│   └── accreditation.html
├── week01/
│   ├── lecture_intro_to_topic.html
│   └── activity_workshop.html
├── week02/
│   └── ...
└── assessments/
    ├── assessment_1.html
    └── ...
```

### Round-trip metadata

A `curriculum_curator_meta.json` file at the ZIP root stores Curriculum Curator-specific data (pedagogy type, difficulty level, learning outcomes with Bloom's levels, AoL mappings, SDG mappings, graduate capability mappings). LMS platforms ignore this file; Phase 2 import will use it to restore full fidelity.

### Phase 2: Import (future ADR)

Import will parse uploaded `.imscc` files, show a preview, and create a new unit from the contents. Deferred until export is validated in production.

## Consequences

### Positive

- Educators can export units to any CC-compliant LMS
- No vendor lock-in — content is portable
- Round-trip metadata preserves Curriculum Curator-specific data for re-import
- Zero new dependencies — all stdlib

### Negative

- Assessments exported as HTML descriptions, not QTI (quiz interoperability) — this is intentional for Phase 1 simplicity
- Images embedded in TipTap content are not extracted as separate files (inline base64 or external URLs pass through as-is)

### Risks

- LMS platforms interpret CC manifests slightly differently; manual testing with Canvas and Blackboard is required before calling this production-ready

## Related

- [ADR-0015](0015-content-format-and-export-strategy.md) — Content Format and Export Strategy
- [ADR-0029](0029-accreditation-framework-mappings.md) — Accreditation Framework Mappings
