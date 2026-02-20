# IMSCC Import/Export Feature Specification

## Context

Curriculum Curator is an AI-powered course content platform (FastAPI + React + SQLAlchemy). We need to add IMS Common Cartridge (.imscc) export and import so educators can move course content between Curriculum Curator and LMS platforms (Blackboard, Canvas).

This spec should be placed in the `tasks/` directory and referenced when implementing.

## Scope

### Phase 1: Export (implement first)
- Export a single Unit as a valid .imscc file (Common Cartridge v1.2)
- Downloadable via API endpoint
- Frontend button on Unit detail page

### Phase 2: Import (implement after export is validated)
- Upload .imscc file and parse structure
- Preview parsed structure before committing
- Create a new Unit from the parsed content

---

## IMSCC Format Overview

An .imscc file is a ZIP archive containing:
- `imsmanifest.xml` — the manifest describing structure and resources
- Resource files (HTML, images, etc.) in subdirectories

We target **Common Cartridge v1.2** because both Blackboard and Canvas handle it reliably.

### Key XML namespaces for v1.2:
```xml
<manifest identifier="..."
  xmlns="http://www.imsglobal.org/xsd/imsccv1p2/imscp_v1p1"
  xmlns:lom="http://ltsc.ieee.org/xsd/imsccv1p2/LOM/manifest"
  xmlns:lomimscc="http://ltsc.ieee.org/xsd/imsccv1p2/LOM/resource">
```

### Manifest structure:
```
manifest
├── metadata (schema version, Dublin Core via LOM)
├── organizations
│   └── organization (structure="rooted-hierarchy")
│       └── item (root)
│           ├── item (Week 1 folder)
│           │   ├── item → resource (lecture.html)
│           │   └── item → resource (activity.html)
│           ├── item (Week 2 folder)
│           └── ...
└── resources
    ├── resource type="webcontent" href="week01/lecture.html"
    ├── resource type="webcontent" href="week01/activity.html"
    └── ...
```

---

## Export Specification

### New files to create:

1. **`backend/app/services/imscc_service.py`** — Core export/import logic
2. **`backend/app/api/routes/export.py`** — Export API endpoint
3. **`backend/app/api/routes/import_imscc.py`** — Import API endpoint (Phase 2)
4. **`backend/app/schemas/imscc.py`** — Pydantic schemas for import preview responses

### Architecture notes:
- Follow existing patterns: look at `backend/app/services/` for service conventions, `backend/app/api/routes/` for route patterns, `backend/app/api/deps.py` for dependency injection
- Look at how the existing PDF import route (`import_content.py`) handles file uploads as a pattern for IMSCC import
- Use the existing repository layer to fetch Unit data (don't query DB directly)
- Register new routes in `backend/app/main.py` following existing pattern

### Export endpoint:

```
GET /api/units/{unit_id}/export/imscc
```

- Requires authentication (use `get_current_user` dependency)
- Returns a `StreamingResponse` with content-type `application/zip`
- Filename: `{unit_code}_{unit_title_slug}.imscc`

### Data mapping (Unit → IMSCC):

| Curriculum Curator Model | IMSCC Target | Notes |
|---|---|---|
| Unit.title, Unit.unit_code | `<metadata>` LOM general/title | Combine as "{title} ({code})" |
| Unit.description | `<metadata>` LOM general/description | |
| UnitOutline weekly topics | `<organization>` folder items | Each week = one folder item with title "Week N: {topic}" |
| WeeklyMaterial (per week) | `<resource>` type="webcontent" | Convert content to standalone HTML files |
| WeeklyMaterial.content_type | Subfolder organisation | Group by type within week folder (lecture/, activity/, etc.) |
| Assessment | `<resource>` type="webcontent" | Export as formatted HTML, NOT as QTI |
| UnitLearningOutcome | Custom HTML page | Generate a "Learning Outcomes" HTML page at the top level |
| AoL/Graduate Capability mappings | Custom HTML page | Generate an "Accreditation Mapping" HTML page |
| Teaching philosophy, pedagogy_type | `curriculum_curator_meta.json` | See round-trip metadata below |

### HTML content conversion:

WeeklyMaterial content is stored as TipTap JSON or HTML. For export:
- If stored as HTML, wrap in a minimal HTML5 document template with basic CSS
- If stored as TipTap JSON, convert to HTML first (check existing TipTap rendering utils)
- Use a simple, clean HTML template:

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>{material.title}</title>
  <style>
    body { font-family: system-ui, sans-serif; max-width: 800px; margin: 2rem auto; padding: 0 1rem; line-height: 1.6; }
    h1, h2, h3 { color: #1a1a2e; }
    code { background: #f4f4f4; padding: 2px 6px; border-radius: 3px; }
    pre { background: #f4f4f4; padding: 1rem; overflow-x: auto; border-radius: 6px; }
    table { border-collapse: collapse; width: 100%; }
    th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
    th { background: #f0f0f0; }
  </style>
</head>
<body>
  <h1>{material.title}</h1>
  {content}
</body>
</html>
```

### Round-trip metadata file:

Include a `curriculum_curator_meta.json` at the root of the zip (alongside `imsmanifest.xml`). LMS platforms will ignore this file. Structure:

```json
{
  "version": "1.0",
  "exported_from": "curriculum-curator",
  "exported_at": "2026-02-20T10:00:00Z",
  "unit": {
    "pedagogy_type": "inquiry-based",
    "difficulty_level": "intermediate",
    "year": 2026,
    "semester": 1,
    "teaching_philosophy": "..."
  },
  "learning_outcomes": [
    {
      "code": "ULO1",
      "description": "...",
      "bloom_level": "analyze",
      "graduate_capabilities": ["GC1", "GC3"]
    }
  ],
  "aol_mappings": [
    {
      "competency_code": "...",
      "level": "R"
    }
  ]
}
```

### File structure inside the .imscc:

```
package.imscc (zip)
├── imsmanifest.xml
├── curriculum_curator_meta.json
├── overview/
│   ├── learning_outcomes.html
│   └── accreditation.html
├── week01/
│   ├── lecture.html
│   ├── activity.html
│   └── resources/
│       └── (any embedded images, if applicable)
├── week02/
│   └── ...
└── assessments/
    ├── assessment_1.html
    └── ...
```

### Implementation approach for the export service:

```python
# Pseudocode structure for imscc_service.py

import zipfile
import xml.etree.ElementTree as ET
from io import BytesIO

class IMSCCExportService:
    """Exports a Unit as an IMS Common Cartridge v1.2 package."""

    def export_unit(self, unit_id: int, db: Session) -> BytesIO:
        """Main export method. Returns a BytesIO containing the .imscc zip."""
        # 1. Fetch unit with all relationships via repository
        # 2. Build resource list (HTML files for each material)
        # 3. Build manifest XML
        # 4. Build round-trip metadata JSON
        # 5. Package everything into a zip
        # 6. Return BytesIO

    def _build_manifest(self, unit, resources) -> str:
        """Build imsmanifest.xml content."""
        # Use xml.etree.ElementTree to construct the XML
        # Register namespaces properly to avoid ns0: prefixes

    def _material_to_html(self, material) -> str:
        """Convert a WeeklyMaterial to standalone HTML."""

    def _build_overview_pages(self, unit) -> list:
        """Generate learning outcomes and accreditation HTML pages."""

    def _build_meta_json(self, unit) -> str:
        """Build the curriculum_curator_meta.json for round-trip."""
```

### Important implementation details:

- Use `ET.register_namespace()` to register all CC namespaces BEFORE building the tree, so the output doesn't have ugly `ns0:` prefixes
- The `<organization>` must use `structure="rooted-hierarchy"`
- Resource identifiers must be unique within the manifest (use slugified material IDs)
- Each `<resource>` must list all its `<file>` elements
- The zip should NOT include a top-level directory (files at root of zip)

---

## Import Specification (Phase 2)

### Import endpoint:

```
POST /api/import/imscc
```

- Accepts multipart file upload
- Returns a preview of the parsed structure (don't create the Unit yet)

```
POST /api/import/imscc/confirm
```

- Accepts the preview response + user-provided metadata (pedagogy type, etc.)
- Creates the Unit and materials
- Auto-commits via GitContentService

### Import parsing logic:

```python
class IMSCCImportService:
    """Imports an IMS Common Cartridge into Curriculum Curator."""

    def parse_preview(self, file: BytesIO) -> IMSCCPreview:
        """Parse .imscc and return a preview without creating anything."""
        # 1. Validate it's a valid zip with imsmanifest.xml
        # 2. Parse manifest to extract organization structure
        # 3. Check for curriculum_curator_meta.json (round-trip)
        # 4. Build preview tree: weeks → materials
        # 5. Return structured preview

    def create_unit_from_preview(self, preview, user_metadata, db) -> Unit:
        """Create a Unit from confirmed preview + user inputs."""
        # 1. Create Unit with metadata (from meta.json if available, else user input)
        # 2. Create weekly structure from organization hierarchy
        # 3. Import HTML content as WeeklyMaterials
        # 4. If meta.json exists, restore learning outcomes and mappings
        # 5. Git commit the initial import
```

### Preview response schema:

```python
class IMSCCPreview(BaseModel):
    title: str
    description: str | None
    has_curator_metadata: bool  # True if curriculum_curator_meta.json found
    weeks: list[IMSCCWeekPreview]
    assessments: list[IMSCCResourcePreview]
    unmatched_resources: list[IMSCCResourcePreview]  # Resources that didn't map to weeks

class IMSCCWeekPreview(BaseModel):
    week_number: int
    title: str
    materials: list[IMSCCResourcePreview]

class IMSCCResourcePreview(BaseModel):
    identifier: str
    title: str
    resource_type: str  # "webcontent", "assessment", etc.
    file_path: str
    content_preview: str | None  # First ~200 chars of text content
```

### Inference logic for mapping organization → weeks:

- Top-level folder items in `<organization>` → try to match as weeks
- Match patterns like "Week 1:", "Week 01", "Module 1:", "Topic 1" in item titles
- If no week pattern found, use folder order as week numbers
- Items not in folders → put in `unmatched_resources`
- Canvas exports often use "Modules" as top-level folders — treat these as weeks

---

## Frontend Changes

### Export:
- Add an "Export as IMSCC" button/menu option on the Unit detail page
- Simple: triggers a file download via the API endpoint
- Consider adding it to whatever dropdown/action menu already exists on units

### Import (Phase 2):
- Add "Import IMSCC" option alongside the existing PDF import in the content creation flow
- Two-step UI:
  1. Upload file → show preview tree with checkboxes (which weeks/materials to import)
  2. User fills in metadata not in IMSCC (pedagogy type, difficulty) → confirm
- Follow existing upload patterns in the codebase

---

## Testing

### Export tests:
- Export a unit and verify the zip structure contains expected files
- Verify `imsmanifest.xml` is valid XML with correct namespace declarations
- Verify the organization hierarchy matches the unit's weekly structure
- Verify HTML content files are well-formed
- **Manual validation**: Import the exported .imscc into a Canvas/Blackboard test course

### Import tests:
- Parse a known-good .imscc (export one from Canvas as test fixture)
- Verify preview correctly identifies weeks and materials
- Verify round-trip: export a unit → import it → compare structures
- Handle edge cases: empty weeks, missing resources, malformed manifests

### Test fixtures:
- Create a `backend/tests/fixtures/` directory with sample .imscc files
- Include at least: a minimal valid .imscc, a Canvas-exported .imscc, a Blackboard-exported .imscc

---

## Dependencies

No new Python packages required. Use only:
- `zipfile` (stdlib) — create and read zip archives
- `xml.etree.ElementTree` (stdlib) — build and parse XML
- `json` (stdlib) — round-trip metadata
- `io.BytesIO` (stdlib) — in-memory file handling

---

## Implementation Order

1. Create `backend/app/services/imscc_service.py` with `IMSCCExportService`
2. Create `backend/app/api/routes/export.py` with the export endpoint
3. Register the route in `main.py`
4. Test by exporting a unit and manually importing into Canvas/Blackboard
5. Add frontend export button
6. Then move to Phase 2 (import) once export is validated
