# Common Cartridge Import — How It Works

This document explains how Curriculum Curator imports IMS Common Cartridge (IMSCC) packages. It covers the format, the backend processing pipeline, the frontend UX flow, and the design decisions behind the implementation. Written for developers building similar functionality.

## Background

[IMS Common Cartridge](https://www.imsglobal.org/activity/common-cartridge) is the de facto interoperability standard for packaging educational content across LMS platforms (Canvas, Moodle, Blackboard, Brightspace). An `.imscc` file is a ZIP archive containing:

- `imsmanifest.xml` — an XML manifest describing the content structure and resources
- Resource files (HTML pages, images, QTI quiz XML, etc.) in subdirectories

The app supports CC versions 1.1, 1.2, and 1.3, as well as SCORM 1.2 packages. The import also accepts plain `.zip` files containing documents (PDF, DOCX, PPTX, HTML, TXT, MD).

### Manifest structure

```
manifest
├── metadata (schema version, Dublin Core via LOM)
├── organizations
│   └── organization (structure="rooted-hierarchy")
│       └── item (root)
│           ├── item (Week 1 / Module 1)
│           │   ├── item → resource (lecture.html)
│           │   └── item → resource (activity.html)
│           ├── item (Week 2 / Module 2)
│           │   └── ...
│           └── ...
└── resources
    ├── resource type="webcontent" href="week01/lecture.html"
    ├── resource type="imsqti_xmlv1p2" href="quizzes/quiz1.xml"
    └── ...
```

### IMS namespace handling

Real-world IMSCC packages use different XML namespace URIs depending on the CC version and exporting LMS. The parser tries these namespaces in order until it finds the one used by the package:

| Namespace URI | Source |
|---|---|
| `http://www.imsglobal.org/xsd/imsccv1p1/imscp_v1p1` | CC v1.1 |
| `http://www.imsglobal.org/xsd/imsccv1p2/imscp_v1p2` | CC v1.2 |
| `http://www.imsglobal.org/xsd/imsccv1p3/imscp_v1p3` | CC v1.3 |
| `http://www.imsglobal.org/xsd/imscp_v1p1` | Generic IMS Content Packaging |
| `http://www.adlnet.org/xsd/adlcp_rootv1p2` | SCORM 1.2 |

If none match, it falls back to no-namespace parsing. This is important because strict schema validation would reject valid packages from many LMS platforms.

---

## Two Import Modes

### 1. Round-trip import

If the ZIP contains a `curriculum_curator_meta.json` file, the package was previously exported from this app. The metadata file preserves everything the IMS spec can't represent:

```json
{
  "version": "2.0",
  "exported_from": "curriculum-curator",
  "exported_at": "2026-02-24T10:00:00Z",
  "unit": {
    "pedagogy_type": "inquiry-based",
    "difficulty_level": "intermediate",
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
  "materials": [
    {
      "id": "uuid",
      "week_number": 1,
      "title": "Welcome Reading",
      "type": "reading",
      "category": "pre_class",
      "order_index": 0,
      "ulo_ids": ["uuid-ulo1"],
      "assessment_ids": ["uuid-assess1"]
    }
  ],
  "assessments": [...],
  "weekly_topics": [...],
  "aol_mappings": [...],
  "sdg_mappings": [...]
}
```

Round-trip mode restores the full data model with no heuristics: pedagogy, learning outcomes with Bloom's levels, material categories (`pre_class`/`in_class`/`post_class`), material-to-ULO links, assessment details, accreditation mappings, and weekly topics.

### 2. Generic import (from an LMS)

For packages exported from Canvas, Moodle, Blackboard, or Brightspace, the app infers structure using heuristics since these packages only contain the standard IMS manifest and HTML content.

---

## Backend Processing Pipeline

### Step 1: Format detection

```
Is "imsmanifest.xml" present?
├── Yes → Does it contain "adlnet.org" or "ADL SCORM"?
│   ├── Yes → SCORM 1.2
│   └── No  → IMSCC
└── No  → Plain ZIP (process individual files)
```

### Step 2: Round-trip detection

```
Is "curriculum_curator_meta.json" present in the ZIP?
├── Yes → Round-trip mode (restore full metadata)
└── No  → Generic mode (use heuristics)
```

### Step 3: LMS source detection

For generic imports, the source LMS is identified by scanning the manifest text and ZIP contents:

| Signal | Detected LMS |
|---|---|
| "canvas" or "instructure" in manifest | Canvas |
| `course_settings/module_meta.xml` exists | Canvas |
| "moodle" in manifest | Moodle |
| "blackboard" in manifest | Blackboard |
| "brightspace" or "d2l" in manifest | Brightspace |

Knowing the source LMS enables platform-specific handling — for example, Blackboard exports use "content areas" (like "Course Information", "Course Materials", "Assignments") instead of weekly modules. The importer detects these and warns the user that the structure differs from weekly organisation.

### Step 4: Manifest parsing

The `imsmanifest.xml` is parsed to extract:

1. **Organization hierarchy** — the tree of `<item>` elements representing the content structure (modules/weeks containing resources)
2. **Resource map** — `<resource>` elements mapping identifiers to file paths and types (`webcontent`, `imsqti_xmlv1p2`, etc.)
3. **Metadata** — unit title, description from LOM metadata

Top-level items in the organization are treated as weeks/modules. Their child items are the individual content resources.

### Step 5: Content classification

Each manifest item is classified as either an **assessment** or a **material**:

**Assessment detection** — title keywords (case-insensitive):
- `quiz`, `exam`, `test`, `assignment`, `midterm`, `final`, `assessment`
- Additionally, resource type `imsqti_xmlv1p2` is always an assessment

**Material type inference** — from title/filename keywords:
- `lecture`, `reading`, `video`, `discussion`, `activity`, `handout`, `case study`, `notes`

**Material category inference** — from sub-headers or folder names:
- `pre-class` / `before class` → `pre_class`
- `in-class` / `during class` → `in_class`
- `post-class` / `after class` → `post_class`
- `resources`, `general`

**Week number extraction** — from directory paths matching `week(\d{2})/` (e.g., `week01/lecture.html` → week 1).

### Step 6: Content extraction

- **HTML resources**: Cleaned via BeautifulSoup — script tags removed, `<h1>` extracted as title, content sanitised
- **QTI quizzes**: Parsed by a dedicated QTI service into structured quiz question records (question text, answer choices, correct answer, question type)
- **Documents** (PDF, DOCX, PPTX, HTML, TXT, MD): Processed by file import services that extract text content
- **`$IMS-CC-FILEBASE$` tokens**: Canvas uses `%24IMS-CC-FILEBASE%24` for internal file references — these are resolved to actual file paths in the ZIP

### Step 7: Database record creation

All records are created in a single transaction:

| Record type | Source |
|---|---|
| `Unit` | Manifest metadata + defaults (or round-trip metadata) |
| `WeeklyTopic` | Organization hierarchy (one per top-level item) |
| `WeeklyMaterial` | Resource files classified as materials |
| `Assessment` | Resource files classified as assessments |
| `Content` | Extracted HTML/text content for each material |
| `UnitLearningOutcome` | Round-trip metadata only (not in standard CC) |
| `QuizQuestion` | QTI quiz XML parsing |
| Accreditation mappings | Round-trip metadata only |

For generic imports, sensible defaults are applied: inquiry-based pedagogy, intermediate difficulty, 6 credit points.

### Step 8: Import provenance

When importing from an LMS, the original CC identifiers and manifest structure are stored as JSON on the `Unit` model (`import_provenance` field). This enables **provenance-aware re-export**: if the user edits content and exports back to the same LMS, the original CC identifiers are reused so the LMS treats it as an update to the existing course shell rather than a brand new course.

---

## Skipped Content Reporting

Not everything in a CC package can be imported. The app follows a **no silent drops** policy — every item is accounted for in the import report, categorised as:

| Category | Examples | User action |
|---|---|---|
| **Action needed** | Videos (need a streaming URL) | User provides the URL |
| **Not supported** | LTI tool links, rubrics, access control | Feature doesn't exist in the app |
| **Not applicable** | Announcements, discussion boards, student groups | LMS-specific, no equivalent |

Images, external links, and discussion prompts are imported where possible. Items that genuinely can't be imported are surfaced at import time, not discovered later at export time.

---

## API Endpoints

There are two sets of endpoints. The **unified** endpoints are the current preferred path.

### Unified endpoints (recommended)

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/api/import/unified/analyze` | Upload a ZIP/IMSCC, get a full file preview |
| `POST` | `/api/import/unified/apply` | Apply the import (returns a `task_id` for progress polling) |
| `GET` | `/api/import/unified/status/{task_id}` | Poll background task progress |

### Legacy endpoints

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/api/import/package/analyze` | Preview a package without saving |
| `POST` | `/api/import/package/create` | Import and create all records |

### Analyze response

The analyze endpoint returns a preview with:

- `packageType`: `imscc`, `scorm`, `plain_zip`, or `round_trip`
- `sourceLms`: `canvas`, `moodle`, `blackboard`, `brightspace`, or `null`
- `isRoundTrip`: whether `curriculum_curator_meta.json` was found
- `unitCode`, `unitTitle`: extracted or inferred values (editable by user)
- `durationWeeks`: number of weeks detected
- `files[]`: list of processable files with `path`, `filename`, `extension`, `detectedType` (material/assessment/outline), `weekNumber`, `title`, `sizeBytes`
- `skippedFiles[]`: list of items that won't be imported, each with `reason`, `contentType`, `category`
- `detectedContentAreas`: Blackboard-specific content area names (if applicable)

### Apply request

Accepts the file again plus optional overrides:

- `unit_code`, `unit_title`: user-edited values
- `duration_weeks`: number of weeks for the unit

Returns a `task_id`. The import runs as a background task, trackable via SSE (Server-Sent Events) or polling.

### Task progress

The status endpoint returns:

```json
{
  "task_id": "abc-123",
  "status": "running",
  "total_files": 15,
  "processed_files": 8,
  "current_file": "week03/lecture_databases.html",
  "unit_id": null,
  "unit_code": "ICT100",
  "unit_title": "Introduction to IT",
  "errors": [],
  "skipped_items": []
}
```

---

## Frontend UX Flow

The import UI (`PackageImport.tsx`) has four phases:

### 1. Upload

Drag-and-drop zone or file picker. Accepts `.imscc` and `.zip` files (up to 500 MB). On file selection, the analyze endpoint is called immediately.

### 2. Preview

After analysis completes, the user sees:

- **Package badges**: package type (IMSCC/SCORM/ZIP), source LMS (Canvas/Moodle/etc.), round-trip indicator
- **Editable fields**: unit code and title (pre-filled from the package, with duplicate code detection)
- **Summary stats**: material count, assessment count, processable count, skipped count
- **File table**: every processable file with editable columns for type (material/assessment/outline), week number, and title
- **Skipped files**: expandable section grouped by category (action needed / not supported / not applicable)
- **LMS-specific warnings**: e.g., Blackboard content-area structure explanation

The user can adjust classifications and week assignments before proceeding.

### 3. Processing

A spinner with a progress bar, powered by background task tracking via SSE. Shows the current file being processed and the overall progress fraction.

### 4. Done

Success summary showing the unit code/title, file count, any errors, and skipped items. A button navigates to the newly created unit.

---

## Key Files

| File | Purpose |
|---|---|
| `backend/app/services/package_import_service.py` | Core IMSCC/SCORM parsing, classification, and DB record creation |
| `backend/app/services/unified_import_service.py` | Unified import orchestrator (handles IMSCC, SCORM, and plain ZIP) |
| `backend/app/services/qti_service.py` | QTI quiz XML parser |
| `backend/app/services/lms_terminology.py` | LMS-specific keyword sets for classification |
| `backend/app/services/import_task_store.py` | In-memory background task tracking |
| `backend/app/api/routes/package_import.py` | API endpoints |
| `backend/app/schemas/package_import.py` | Pydantic request/response schemas |
| `frontend/src/features/import/PackageImport.tsx` | Import UI component |
| `frontend/src/hooks/useTaskProgress.ts` | SSE-based task progress hook |

## Design Decisions (ADRs)

These Architecture Decision Records document the reasoning behind the implementation:

- **ADR-030**: IMS Common Cartridge export — chose CC v1.1 for broadest LMS compatibility, `curriculum_curator_meta.json` for round-trip metadata, zero external dependencies
- **ADR-042**: Package import with round-trip detection — dual-mode import (round-trip vs generic), heuristic classification, namespace iteration strategy
- **ADR-043**: In-memory import task store — background task tracking for long-running imports without requiring a task queue like Celery
- **ADR-054**: Import provenance for round-trip fidelity — storing CC identifiers on the Unit model so re-exports preserve LMS course structure, meta.json v2 with per-material metadata, Canvas-specific enhancements
- **ADR-061**: Transparent import reporting — no silent drops policy, categorised skipped items, surfacing issues at import time

## Lessons Learned

1. **Don't do strict schema validation.** Real-world LMS exports frequently deviate from the IMS spec. Strict XSD validation would reject valid packages from Canvas and Moodle. Lenient parsing with namespace fallbacks is essential.

2. **Heuristic classification is imperfect.** A material titled "Test Your Knowledge" gets classified as an assessment. Letting the user review and adjust classifications in the preview step mitigates this.

3. **Round-trip metadata belongs in a separate file, not in manifest extensions.** Embedding custom metadata as IMS manifest extensions risks breaking LMS import of the package. A separate JSON file is invisible to LMSs that don't understand it.

4. **Store import provenance.** If users edit content and re-export to the same LMS, reusing the original CC identifiers means the LMS treats it as an update rather than a new course. This requires storing the original manifest structure.

5. **Report everything at import time.** Users discovering missing content at export time (weeks later) erodes trust. Categorising skipped items as "action needed" / "not supported" / "not applicable" sets clear expectations upfront.

6. **LMS-specific handling is worth it.** Canvas, Blackboard, and Moodle all structure their exports differently. Detecting the source LMS and applying platform-specific parsing logic (e.g., Blackboard content areas, Canvas `module_meta.xml`) significantly improves import quality.
