# Structured Material Import — Architecture Plan

**Status:** Planned
**Date:** 2026-04-10
**Related:** [ADR-023](adr/023-file-import-processing-architecture.md), [ADR-042](adr/042-package-import-round-trip.md), [ADR-054](adr/054-import-provenance-round-trip-fidelity.md), [ADR-061](adr/061-transparent-import-reporting.md), [ADR-063](adr/063-unit-outline-import-parser-system.md), [ADR-038](adr/038-content-not-presentation.md), [ADR-064](adr/064-rough-slides-as-feature.md), [speaker-notes-plan.md](speaker-notes-plan.md)

## Background

The current import pipeline produces plain text or HTML, never structured `content_json`. Confirmed by exploration of all four import services:

| Service | Purpose | Output | Creates `content_json`? |
|---|---|---|---|
| `file_import_service` | Single file → text + images | Plain text in `Content.body` (legacy) | **No** |
| `pdf_parser_service` | PDF → text + structure metadata | `ExtractedDocument` with full text, blocks, TOC | **No** (used for analysis only) |
| `package_import_service` | IMSCC/SCORM/round-trip → Unit | Plain HTML in `WeeklyMaterial.description` | **No** |
| `unified_import_service` | Any ZIP → Unit, async | Plain HTML in `WeeklyMaterial.description` | **No** |

The TipTap editor and the export pipeline both operate on `WeeklyMaterial.content_json` (ProseMirror structure with slide breaks, marks, embedded nodes). Imports create materials whose `content_json` is `NULL` and whose `description` contains a flat blob of text. The result: imported materials cannot be edited structurally, slide breaks are lost, speaker notes are flattened as `Notes: <text>` lines, images are partially preserved but not positioned, and round-trip fidelity is impossible.

This plan introduces a **structured material import architecture** that produces `content_json` directly, mirroring the pluggable parser pattern from ADR-063 (unit outline parsers). The work is significant because it touches the import pipeline foundationally — but it unlocks several capabilities at once:

- Editable imported materials (currently impossible)
- Speaker notes round-trip from PPTX (the original speaker-notes-plan trigger)
- Slide-break preservation from PPTX/reveal.js
- Multi-format awareness (the same lecture as PPTX + PDF + DOCX in one zip)
- A clean extension point for format dialects (Marp, Quarto, Obsidian, Jupyter)

## Guiding decisions (already agreed)

These were settled in the conversation that produced this plan and are not revisited below:

1. **Speaker notes plan reframed.** The original `speaker-notes-plan.md` Phase 2/3/4 (editor UX, AI generation, polish) ships independently and doesn't depend on this plan. The original Phase 1 (pipeline) is partially absorbed here — the export half ships standalone, the import half lives in this plan.
2. **PDF default is plain paragraphs.** No structure inference from font sizes. Optional second pass with LLM-powered structuring when AI is enabled (per ADR-032 assistance level), surfaced as an explicit "improve structure with AI" action.
3. **Multi-format conflict resolution: canonical + source files pattern.** When the importer detects multiple files representing the same lecture, one becomes the editable canonical material; the others are attached as downloadable source files. User can re-promote any source file later.
4. **Pluggable parser registry mirroring `outline_parsers/`.** ABC + module-level registry + per-format default lookup + auto-detect dispatch. Source-only registration in v1; admin upload is a future enhancement consistent with ADR-063's trajectory.
5. **No user settings for parser selection in v1.** Auto-detect with confidence + format default + per-import override at upload time. Settings only if a clear need emerges.
6. **`Content` model is not in scope.** This plan targets `WeeklyMaterial` exclusively. The legacy `/api/content/upload` route stays as-is (does its own plain-text thing for the old `Content` model).

## Architecture

### Directory layout

```
backend/app/services/material_parsers/
├── __init__.py              # Registry, get_parser, list_parsers, get_default_for_format, autodetect
├── base.py                  # MaterialParser ABC + MaterialParseResult schema
├── pptx_structural.py       # python-pptx → content_json with slideBreaks + speakerNotes + images
├── docx_pandoc.py           # Pandoc DOCX→markdown → content_json
├── html_structural.py       # BeautifulSoup → content_json (handles reveal.js <section>)
├── md_structural.py         # markdown parser → content_json
├── pdf_paragraphs.py        # pdf_parser_service text → paragraph-only content_json
├── pdf_llm.py               # pdf_parser_service text → LLM-structured content_json (opt-in)
└── ipynb_structural.py      # Jupyter notebook cells → content_json (Phase 2 specialisation)
```

This mirrors `outline_parsers/` exactly. The two registries are independent (different result schemas, different consumers).

### Parser interface

```python
# base.py (sketch)

class MaterialParser(ABC):
    name: ClassVar[str]                       # e.g. "pptx_structural"
    display_name: ClassVar[str]               # e.g. "PowerPoint (structural)"
    description: ClassVar[str]
    supported_formats: ClassVar[list[str]]    # e.g. ["pptx"]
    is_default_for: ClassVar[list[str]]       # formats this is the registered default for
    requires_ai: ClassVar[bool] = False       # gates parser by ADR-032 assistance level

    @abstractmethod
    async def parse(
        self,
        file_content: bytes,
        filename: str,
        *,
        user_context: dict[str, object] | None = None,
    ) -> MaterialParseResult: ...
```

### Result schema

```python
# base.py (sketch)

class ExtractedImage(BaseModel):
    filename: str
    data: bytes  # raw image bytes for downstream storage
    placement_hint: str | None = None  # e.g. "slide-3-img-0"

class MaterialParseResult(BaseModel):
    title: str | None = None             # extracted from doc title / first heading / filename
    content_json: dict[str, Any]         # ProseMirror document — the editable material
    images: list[ExtractedImage] = []    # extracted from the source, referenced by content_json
    warnings: list[str] = []             # things the user should know (per ADR-061)
    parser_used: str
    confidence: float = 1.0              # parser self-reported confidence (informational)
```

The parser does *not* create DB rows. It returns a pure data result. The unified import service (or a new import route) handles persistence.

### Registry and dispatch

```python
# __init__.py (sketch)

DEFAULT_PARSER_BY_FORMAT: dict[str, str] = {
    "pptx": "pptx_structural",
    "docx": "docx_pandoc",
    "html": "html_structural",
    "htm":  "html_structural",
    "md":   "md_structural",
    "pdf":  "pdf_paragraphs",
    "ipynb": "ipynb_structural",
}

def get_default_for_format(ext: str) -> MaterialParser: ...
def get_parser(parser_id: str) -> MaterialParser: ...
def list_parsers(format: str | None = None) -> list[dict]: ...
def autodetect(file_content: bytes, filename: str) -> str | None:
    """Inspect file and return a parser name if a confident dialect signal is found."""
```

`autodetect` returns a parser name only when there's an unambiguous content signal (see "Auto-detection rules" below). Otherwise returns `None` and the caller uses `get_default_for_format`.

### Reuse, not duplication

Material parsers reuse existing extraction infrastructure rather than reimplementing it:

- **PDF parsers** call `pdf_parser_service.extract_from_bytes()` to get the `ExtractedDocument`, then transform that into `content_json`. They don't touch PyPDF2/pdfplumber/pymupdf directly.
- **DOCX parser** shells out to Pandoc (already a project dependency for export) via `subprocess` to get markdown, then runs the markdown through the markdown parser. This matches the existing Pandoc binary resolution pattern in `export_service.py`.
- **HTML parser** reuses BeautifulSoup-based extraction patterns from `package_import_service.extract_html_content()` but keeps structure (paragraphs, headings, lists, tables) instead of flattening to a body string.
- **PPTX parser** uses python-pptx directly (already a dependency).
- **Markdown parser** uses an existing markdown library (`markdown` is already imported in `file_import_service.py`).

The aim: parsers are thin transformation layers, not new extraction stacks.

## v1 parsers — what each one produces

### `pptx_structural`

Built on `python-pptx`. Per slide:

1. Title placeholder → `heading` level 1
2. Content placeholders (text frames) → `paragraph` / `bulletList` / `orderedList` based on bullet level depth
3. Text runs with formatting → marks (`bold`, `italic`, `underline`, `strike`, `link`)
4. Tables → `table` / `tableRow` / `tableCell`
5. Picture shapes → `image` node (with `src` referencing image upload URL after persistence) + entry in `images[]`
6. Notes slide text → `speakerNotes` node placed at end of slide segment, **before** the slide break that closes it
7. Slide boundary → `slideBreak` node

Edge cases:
- Text in non-placeholder shapes (loose text boxes) → flattened into the slide as additional paragraphs in shape order
- Grouped shapes → recursively flattened
- SmartArt → text-only extraction, paragraph node per item
- Equations → drop in v1, warning emitted
- Animations / transitions → dropped silently (per ADR-038)
- Slide masters → not extracted (per ADR-038 / ADR-056 — masters are template territory)

This is the parser that closes the speaker-notes import gap. Notes are emitted as structured `speakerNotes` nodes, not flattened text.

### `docx_pandoc`

Pandoc invocation: `pandoc input.docx -t markdown -o output.md`. Then a markdown → content_json transformation step (the same step `md_structural` uses).

Why Pandoc rather than python-docx directly: Pandoc's DOCX reader is significantly more robust at heading detection, list structures, table parsing, and image extraction than what we'd write ourselves. Reusing the existing Pandoc binary keeps the import code small.

Output: a single continuous content_json (no slide breaks — DOCX has no slide concept). Headings, paragraphs, lists, tables, images all become their TipTap equivalents. Pandoc extracts embedded images to a media folder; the parser reads them into `images[]`.

### `html_structural`

BeautifulSoup walks the DOM. Mapping:
- `<h1>`–`<h6>` → `heading` (level)
- `<p>` → `paragraph`
- `<ul>` / `<ol>` / `<li>` → `bulletList` / `orderedList` / `listItem`
- `<table>` / `<tr>` / `<td>` / `<th>` → `table` / `tableRow` / `tableCell` / `tableHeader`
- `<blockquote>` → `blockquote`
- `<pre>` / `<code>` → `codeBlock`
- `<strong>` / `<em>` / `<u>` / `<a>` → marks
- `<img>` → `image` (data URL → extracted to `images[]`, src remains URL otherwise)
- `<hr>` → `horizontalRule`
- `<section>` boundaries (reveal.js) → `slideBreak` between sections
- `<aside class="notes">` (reveal.js notes) → `speakerNotes` node

Sanitisation: same allowlist as `package_import_service.extract_html_content()` — drop scripts, styles, iframes, forms.

### `md_structural`

Standard Markdown → content_json. Use a markdown parser that exposes an AST (e.g. `markdown-it-py`) so transformation is deterministic. CommonMark + GFM tables + fenced code with language.

Slide breaks are inferred from `---` thematic breaks **at top level** (not inside lists/quotes). This handles plain markdown decks but not Marp/Quarto specifics — those are dialect specialisations.

### `pdf_paragraphs`

Calls `pdf_parser_service.extract_from_bytes()` to get the `ExtractedDocument`, then:

1. Flattens `full_text` into paragraphs (split on double newline)
2. Each paragraph → `paragraph` node
3. No headings (no reliable signal without font analysis)
4. No lists (cannot recover reliably)
5. No tables (`pdf_parser_service` already returns tables — could optionally include them as `table` nodes; Phase 2 enhancement)
6. Images from `ExtractedDocument.pages[].images` → `image` nodes with `images[]` entries

Emits a warning: *"PDF imported as plain paragraphs. Structure (headings, lists, tables) was not recovered. Use 'Improve with AI' to add structure if AI is enabled."*

### `pdf_llm` (opt-in)

`requires_ai = True`. Same starting point as `pdf_paragraphs`, but the extracted text is sent to an LLM with a structured-output prompt (per ADR-045 retry pattern) asking it to produce content_json. The prompt receives:

- The full extracted text
- The page count and any TOC entries from `ExtractedDocument`
- A schema description of valid TipTap node types
- Instructions: preserve all content, add headings where structure is implied, recover lists where bullet markers exist, do not invent content

Output: content_json with inferred structure. Tagged with `confidence` based on the LLM's self-report and post-validation (does the rendered text match the input by length and word frequency?).

This parser is **never auto-selected**. It only runs when the user explicitly chooses it from the parser picker, or via the "Improve with AI" action on an existing pdf_paragraphs import.

### `ipynb_structural` (Phase 2 specialisation)

Walks notebook cells:
- Markdown cells → run through markdown parser
- Code cells → `codeBlock` with language attribute
- Output cells → drop in v1 (could become images or text in Phase 2)
- Cell metadata (slide_type) → optional `slideBreak` for `subslide`/`slide` types

## Auto-detection rules

`autodetect()` inspects file content and returns a parser name only when there's a confident, unambiguous signal. False positives are worse than no detection — when in doubt, return `None` and let the format default handle it.

| Format | Signal | Parser to dispatch |
|---|---|---|
| `.html` | Contains `<section>` and `class="reveal"` or `data-state` | `revealjs_parser` (Phase 2 specialisation) |
| `.md` | Front-matter `format: revealjs` or `marp: true` | corresponding dialect parser |
| `.md` | Front-matter `jupyter:` or `kernelspec:` | `quarto_qmd_parser` (Phase 2) |
| `.pptx` | Marp metadata in slide notes | `marp_parser` (Phase 2) |

In v1, only the format defaults exist — auto-detection rules are scaffolding ready for Phase 2 dialect parsers. The dispatcher should be built in v1 so adding parsers later doesn't require touching the dispatch logic.

## Multi-format conflict resolution

The "lecturer's zip with reveal.js + PDF + PPTX + DOCX of the same lecture" scenario.

### Grouping heuristic

In the analysis phase (before any DB writes), the importer scans all files in the upload and groups them by:

1. **Filename stem matching within the same directory.** `lecture_01.pptx`, `lecture_01.pdf`, `lecture_01.docx`, `lecture_01.html` → one group called "lecture_01".
2. **IMSCC/SCORM manifest grouping.** When the manifest declares multiple resources for the same item, treat them as a group.
3. **Single files** (no matches) → singleton groups, treated as individual materials.

**Not in v1:** content similarity matching (hashing, fuzzy), filename normalisation beyond exact-stem-match. Conservative wins.

### Canonical selection ranking

Within each group, pick the canonical material by format priority:

```
PPTX > DOCX > HTML > MD > PDF
```

Rationale:
- PPTX has the most structurally recoverable content for slide-style materials
- DOCX is well-structured for handout-style materials
- HTML is structured but variable in quality
- Markdown is structured but less common in institutional content
- PDF is structurally hostile and should only win when nothing else exists

The canonical file is parsed via its format's parser, producing the editable `WeeklyMaterial`.

### Source files

Non-canonical files in the group become **attached source files**:

- Stored in the material's git-backed content directory under `source_files/`
- Listed in the material's metadata: `attached_source_files: list[{filename, format, original_size, sha256}]`
- Surfaced in the editor UI as a panel: *"Source files for this material: lecture_01.pdf (PDF, 2.4 MB), lecture_01.docx (DOCX, 180 KB)"*
- Each is downloadable as-is
- Each has a "Promote to canonical" action — re-runs the parser on that file and replaces `content_json` (with confirmation)

### Pre-import preview

Before any DB write, the user sees a summary in the import review screen:

> **12 lectures detected across 4 formats.**
>
> We'll import the **PPTX** version of each as the editable material. Other formats will be attached as source files.
>
> | Lecture | Canonical | Source files |
> |---|---|---|
> | lecture_01 | lecture_01.pptx | lecture_01.pdf, lecture_01.docx |
> | lecture_02 | lecture_02.pptx | lecture_02.pdf |
> | … | … | … |
>
> **3 standalone files detected:** reading_01.pdf, syllabus.docx, video_links.html
>
> *[Change individual lectures...]* *[Continue]*

User can override per-lecture canonical selection at this screen — useful when a particular PPTX is sparse but the DOCX has the real content.

## Integration with existing import services

The new architecture is additive — it doesn't replace `unified_import_service`, it slots into it.

### Modified: `unified_import_service._extract_content`

Currently routes everything through `file_import_service.process_file()` which returns plain text. Replace with parser dispatch:

```python
async def _extract_content(self, file_path, filename, ext, ...):
    parser_id = autodetect(file_bytes, filename) or get_default_for_format(ext).name
    parser = get_parser(parser_id)
    result = await parser.parse(file_bytes, filename)
    return result  # MaterialParseResult, not text
```

### Modified: `unified_import_service._run_import`

When persisting a `WeeklyMaterial`, populate `content_json` from `result.content_json` instead of `description` from text. Also write attached source files to the material's git directory and update metadata.

### Unchanged: `package_import_service` round-trip path

Round-trip imports (Curriculum Curator's own export format) already preserve `content_json` if present in `curriculum_curator_meta.json`. They go through a separate code path (`_create_round_trip()`) that this plan doesn't touch.

### Unchanged: `pdf_parser_service`, `file_import_service` extraction methods

These remain as the underlying extraction layer. Material parsers wrap them, transforming their output into `content_json`. The legacy `/api/content/upload` route is untouched.

### Deprecation tracking

The plain-text path through `unified_import_service` becomes a fallback for formats with no registered parser (none in v1, but the architecture should not assume parsers exist for every format). When a format has a parser, structured import is the only path. ADR-061 (transparent reporting) implies any format that falls through to plain-text should emit a warning so users know the import was lossy.

## Speaker notes integration

Speaker notes ride along under the PPTX parser — they're not a separate concern. Specifically:

1. `pptx_structural` extracts notes via `slide.notes_slide.notes_text_frame.text` and emits a `speakerNotes` node at the end of each slide segment.
2. The `content_json_renderer` and `slide_splitter` updates from the original speaker-notes plan still need to happen — but they're now part of the speaker-notes work, not this plan. They're prerequisites: the PPTX parser produces the nodes, but the export side needs the renderer/splitter changes to round-trip them to PowerPoint.

**Sequencing:** the original `speaker-notes-plan.md` Phase 1 (export half) ships first or in parallel with this plan's Phase 1. The PPTX parser depends on the `speakerNotes` node type existing in the schema (defined by speaker-notes Phase 1). Once both are in place, the round-trip closes.

## Import modes — three distinct user flows

Imports are not always full courses. The architecture must support three distinct modes, each with its own user expectation and target. The parser layer is mode-agnostic — the same parsers do the work — but the route layer differs because the persistence target and user intent differ.

### Mode A — Single file into an existing unit

**User intent:** "Add this lecture / worksheet / tutorial / case study to my unit."

- **Input:** one file (PPTX/DOCX/PDF/HTML/MD/IPYNB)
- **Target:** existing `Unit`, optionally a specific `week_number` and `content_category` (lecture / worksheet / case study / etc. — these already exist in the model per ADR-053)
- **Output:** one new `WeeklyMaterial` in the specified week
- **Replaces:** what `/api/content/upload` does today (which produces a legacy `Content` row, not a structured `WeeklyMaterial`)

This is the most common entry point for individual educators. Lecturer has a single PPTX they want to add to Week 3; they shouldn't have to bundle it into a zip or treat it as a course import.

### Mode B — Multi-file folder/zip into an existing unit

**User intent:** "Import this folder of lectures into my unit. Figure out which week each goes in."

- **Input:** zip file or multiple file uploads
- **Target:** existing `Unit`
- **Output:** multiple `WeeklyMaterial`s, week assignment derived from filename + folder path heuristics
- **Multi-format grouping:** apply the canonical + source files pattern (Phase 3 of this plan)

This handles the "I have a folder of 12 lectures, drop them into my unit" workflow, and the "lecture in 4 formats" scenario from the planning conversation.

### Mode C — Full course / LMS export into a new unit

**User intent:** "Import this Canvas export / IMSCC / SCORM package as a new unit."

- **Input:** IMSCC/SCORM/round-trip zip (with manifest)
- **Target:** new `Unit` (created during import)
- **Output:** Unit + UnitOutline + ULOs + WeeklyTopics + WeeklyMaterials + Assessments + accreditation mappings (round-trip mode) or sensible defaults (generic mode)
- **Replaces:** the existing `/import/unified/apply` flow, but with structured parsers underneath producing real `content_json`

This is the existing `unified_import_service` flow, refactored to use the new parsers internally.

## API surface

Three sets of endpoints, one per mode. All modes share the parser registry endpoints.

### Parser registry (shared)

| Endpoint | Method | Purpose |
|---|---|---|
| `/api/import/material/parsers` | GET | List all registered material parsers (id, displayName, description, supportedFormats, requiresAi, isDefaultFor) |
| `/api/import/material/parsers?format=pdf` | GET | List parsers for a specific format, with the default flagged |

### Mode A — Single file into existing unit

| Endpoint | Method | Purpose |
|---|---|---|
| `/api/import/material/single/preview` | POST | Upload one file + unit_id + optional week_number + optional parser_id override. Returns parser used, extracted title, content preview, image count, warnings. No DB write. |
| `/api/import/material/single/apply` | POST | Apply a reviewed preview — creates one `WeeklyMaterial`, persists images. Synchronous (single file is fast). |

Synchronous because a single file's parse + persist is fast enough that background-task overhead isn't worth it. The route returns the new material's ID directly.

### Mode B — Multi-file into existing unit

| Endpoint | Method | Purpose |
|---|---|---|
| `/api/import/material/batch/preview` | POST | Upload zip + unit_id. Returns: file list with detected weeks, multi-format groups, canonical selection per group, source files per group, warnings, total counts. No DB write. |
| `/api/import/material/batch/apply` | POST | Apply a reviewed preview (with optional per-file/per-group overrides). Async, returns task_id. Creates multiple `WeeklyMaterial`s and attached source files in the existing unit. |
| `/api/import/material/batch/status/{task_id}` | GET | Poll status. |

### Mode C — Full course / LMS export into new unit

| Endpoint | Method | Purpose |
|---|---|---|
| `/api/import/material/course/preview` | POST | Upload IMSCC/SCORM/round-trip zip. Returns: format, is_round_trip, detected unit metadata, file list, ULOs/assessments preview, warnings. No DB write. |
| `/api/import/material/course/apply` | POST | Apply a reviewed preview. Async, returns task_id. Creates new Unit + everything inside. |
| `/api/import/material/course/status/{task_id}` | GET | Poll status. |

This effectively replaces the existing `/import/unified/*` and `/import/package/*` endpoints. The legacy endpoints stay during the transition for compatibility, then deprecate after Phase 6.

### Progress reporting

All async modes (B and C) reuse the existing `ImportTask` model already used by `unified_import_service`. Per-file progress is tracked via:

- `total_files` — total to process
- `processed_files` — count completed
- `current_file` — filename currently being processed
- `status` — "running" / "completed" / "failed"
- `errors[]` — accumulated per-file errors

This is enough to render *"Importing 4 of 15: lecture_03.pptx"* in the UI. A `current_step` field could be added later for fine-grained per-file step display (extracting → parsing → writing) but is deferred unless users hit the limit.

### Mode dispatch on the frontend

The user chooses the mode via the import UI rather than from the URL — they pick "Add a single material" / "Import a folder" / "Import a course package" on the import landing page, and the frontend calls the appropriate endpoint set. No magic mode-detection on the backend.

## Phasing

This is a substantial body of work. Phased delivery, each phase shippable independently:

### Phase 1 — Foundation + PPTX

The minimum viable cut that delivers user value: structured PPTX import with speaker notes.

- `material_parsers/` directory, `MaterialParser` ABC, `MaterialParseResult` schema, registry, dispatcher
- `pptx_structural` parser
- New `/api/import/material/preview` and `/apply` endpoints (PPTX only)
- Integration with `unified_import_service._extract_content` for `.pptx` files only
- Image handling: extracted images written to git-backed material directory, content_json references them
- Speaker notes: depends on speaker-notes-plan Phase 1 (export half) being shipped first or in parallel — coordinate sequencing
- Tests: parser unit tests with real PPTX fixtures, round-trip integration test (PPTX import → editor render → PPTX export → notes preserved)
- Frontend: minimal preview UI surface (just shows what will be imported, no multi-format conflict resolution yet)

**Exit criteria:** a user uploads a PPTX with speaker notes, slide breaks, bullet lists, tables, and images. After import, they see a fully editable `WeeklyMaterial` in the editor with all of those preserved. Exporting back to PPTX produces a file with notes in the speaker pane, slide breaks intact, bullets and tables editable in PowerPoint.

### Phase 2 — DOCX, HTML, Markdown, PDF (paragraphs)

Add the other format defaults, all without LLM dependency.

- `docx_pandoc` parser (Pandoc subprocess)
- `html_structural` parser
- `md_structural` parser
- `pdf_paragraphs` parser
- Extend `unified_import_service._extract_content` dispatch to all formats
- Frontend preview UI shows per-file parser selection
- Tests: per-parser unit tests, integration tests for each format

**Exit criteria:** all common single-file imports produce structured `content_json`. PDFs are honestly plain-paragraph but warn the user about lost structure.

### Phase 3 — Multi-format conflict resolution

The canonical + source files pattern.

- Grouping heuristic in the preview phase
- `attached_source_files` metadata field on `WeeklyMaterial` (or in `unit_metadata` JSON if simpler)
- Source file storage in git-backed material directory under `source_files/`
- "Promote to canonical" action and backend endpoint
- Frontend preview UI: groups display, per-group canonical override
- Editor UI: source files panel on the material edit screen
- Tests: grouping heuristic tests, end-to-end test with a multi-format zip fixture

**Exit criteria:** uploading the lecturer's "lecture in four formats" zip produces one editable material per lecture with the other formats attached as downloadable source files. User can re-promote any source file.

### Phase 4 — AI-assisted PDF structuring

`pdf_llm` parser as opt-in.

- New parser implementation using ADR-045 structured-output retry pattern
- New prompt template (system seed) for "convert plain text to structured content_json"
- Gated on AI assistance level per ADR-032
- Frontend "Improve structure with AI" action on existing pdf_paragraphs imports — runs `pdf_llm` against the original source file (which means PDF imports must keep the source file by default)
- Cost transparency: token estimate before running
- Tests: prompt rendering, structured output validation, gating

**Exit criteria:** users with AI enabled can opt to upgrade a PDF import from plain paragraphs to structured content via a single button.

### Phase 5 — Format dialect specialisations

Add as needed; each is a self-contained parser module.

Likely first additions based on real usage:
- `revealjs_parser` (HTML dialect — `<section>` boundaries + `<aside class="notes">`)
- `marp_parser` (Markdown dialect)
- `quarto_qmd_parser` (Markdown dialect)
- `ipynb_structural` (Jupyter notebook)

Each ships independently; the registry pattern means adding a parser doesn't touch any other code. Auto-detection rules registered as the parser is added.

### Phase 6 — Polish & docs

- ADR for the structured material import architecture (let's call it ADR-065)
- User stories in `docs/user-stories/`
- Update the import-related docs in `docs/guides/`
- Audit `unified_import_service` for code that's now redundant; flag for cleanup or deprecate the plain-text fallback path entirely

## Open questions — resolutions

All open questions resolved during the planning conversation:

1. **Pandoc dependency on the import path.** ✅ **Accepted.** Pandoc is already on the path for export (bundled in Electron extraResources, included in Docker images). DOCX import and DOCX export share the same dependency surface — no new install requirement.

2. **Image deduplication across canonical and source files.** ✅ **Store twice.** Source files are immutable references; the canonical material's images are independent. Cost is low (a few KB per image), simplicity is high. No deduplication.

3. **Auto-detection confidence signals.** ✅ **YAML front-matter only in v1.** Comment-based directives (e.g. Marp HTML comments) are too easy to false-positive. Only structured signals like front-matter `marp: true` or `format: revealjs` count.

4. **Per-import progress UI.** ✅ **Reuse existing `ImportTask` model.** The current model already tracks `total_files`, `processed_files`, `current_file`, `status`, `errors[]` — enough to render *"Importing 4 of 15: lecture_03.pptx"*. A `current_step` field for fine-grained per-file display (extracting → parsing → writing) is deferred unless users hit the limit.

5. **Import scope (single file vs zip vs full course).** ✅ **Three explicit modes** — see the "Import modes" section above. The plan now supports Mode A (single file → existing unit), Mode B (zip → existing unit with multi-format grouping), and Mode C (LMS export → new unit). The parser layer is mode-agnostic; the route layer differs.

6. **Filename-derived metadata.** ✅ **Route layer, not parser.** The route reads filename + folder path before calling the parser. `file_import_service.detect_week_number(filename, folder_path)` already exists and supports folder-based metadata (e.g. `week_03/lecture.pptx` → week 3). Parsers stay format-focused. Folder paths inside zips become part of the metadata extraction.

## Out of scope

Explicitly not doing in this plan, even at later phases:

- **Replacing `unified_import_service` outright.** It still owns Unit creation, task progress, manifest parsing for IMSCC/SCORM. The new parsers slot into it; they don't replace it.
- **Round-trip import for non-Curriculum-Curator packages.** Generic IMSCC imports remain lossy at the metadata level — we can structurally import the content but can't recover pedagogy/ULOs/accreditation that was never in the source.
- **OCR for scanned PDFs.** `pdf_parser_service` doesn't OCR, and adding it is a separate large undertaking. PDFs without extractable text remain unsupported.
- **Live collaborative editing of source files.** Source files are immutable references — they're for download and re-promotion, not editing in place.
- **Cross-material content deduplication.** If two materials reference the same image, we don't unify them. Each material's images are independent.
- **Migration of existing imports.** Existing `WeeklyMaterial`s with plain-text `description` and `content_json=NULL` stay as they are. Per the project's "no production users, clean slate" stance, users can re-import if they want structure.
- **Admin upload of new parsers at runtime.** Parsers are source-only in this plan, same trajectory as outline parsers (ADR-063). When someone builds the runtime upload UI for outline parsers, the same mechanism applies to material parsers.

## Future: admin parser management

Designed-for, not built. When admin parser upload eventually ships (tracked in `backend/app/plugins/PLUGIN_IDEAS.md`), it should work for both outline and material parsers via a shared mechanism:

- Parser modules uploaded as Python files to a designated directory
- Registry rebuilds on startup or on admin action
- Admin UI lists installed parsers, can disable/remove
- Sandboxing concerns: parsers run arbitrary Python code, so this is admin-only and gated behind authentication. Worth its own ADR when it ships.

The architecture in this plan does not block that future — registries and dispatchers are accessed through stable functions (`get_parser`, `list_parsers`, `get_default_for_format`) that can be backed by a dynamic registry later without changing callers.

## Phase dependencies

```
                ┌─ speaker-notes-plan Phase 1 (export half) ─┐
                │                                             │
                ▼                                             ▼
       Phase 1 (Foundation + PPTX) ──▶ Phase 2 (DOCX/HTML/MD/PDF) ──▶ Phase 3 (multi-format)
                                                                              │
                                                                              ▼
                                                                       Phase 4 (PDF AI)
                                                                              │
                                                                              ▼
                                                                       Phase 5 (dialects)
                                                                              │
                                                                              ▼
                                                                       Phase 6 (polish + ADR)
```

The hard dependency is Phase 1 ↔ speaker-notes-plan Phase 1. The PPTX parser produces `speakerNotes` nodes that need a place in the schema (defined by speaker-notes Phase 1) and need to round-trip through the renderer/splitter (also in speaker-notes Phase 1). Sequencing: ship speaker-notes Phase 1 first, then this plan's Phase 1 immediately after — or run them in parallel and merge together.

## What ships first

**Recommended start: speaker-notes-plan Phase 1 (export half), then this plan's Phase 1 (PPTX import).** Combined, these close the original "speaker notes don't round-trip" bug *and* deliver the first real structured import path. Everything else builds on top.
