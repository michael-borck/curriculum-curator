# 065. Structured Material Import with Pluggable Parser System

Date: 2026-04-10

## Status

Accepted

## Context

The application has, until recently, treated material import as a text-extraction problem. Uploaded PowerPoints, Word documents, PDFs, and HTML files all flowed through `file_import_service.process_file()`, which extracted plain text (and, for PPTX, a flat list of images) and stored the result in a `Content.body` or `WeeklyMaterial.description` string. None of the import paths populated `WeeklyMaterial.content_json` — the structured ProseMirror/TipTap document the editor and export pipeline both operate on.

This created a fundamental gap. The TipTap editor produces structured content (slide breaks, bullet lists, tables, marks, embedded nodes). The export pipeline (Pandoc + Typst, IMSCC, SCORM, H5P) reads structured content. Authored materials had structure; imported materials did not. Editing an imported PowerPoint meant re-creating the slide layout from a wall of plain text. Round-tripping speaker notes (per [ADR-064](064-rough-slides-as-feature.md)) was impossible because notes were flattened into the body text on import.

A second pressure: **import is the lecturer's first encounter with the tool**. Users testing the application typically do so by uploading their existing course material — a PowerPoint deck, an LMS export, a folder of lecture files. If the import is structurally lossy, the rest of the product never gets a fair evaluation. Treating import as a first-class concern, not a legacy text-extraction shim, is necessary for the tool to be evaluable on its own merits.

A third constraint: **import format diversity is open-ended**. PPTX, DOCX, PDF, HTML, Markdown, Jupyter notebooks, reveal.js decks, Marp slides, Quarto documents, Obsidian vaults — each has its own structural conventions. Some are well-defined and structurally rich (PPTX, DOCX); some are ambiguous markdown dialects (Marp, Quarto); some are structurally hostile (PDF). Any architecture needs to handle this diversity without becoming a monolith of conditional branches.

[ADR-063](063-unit-outline-import-parser-system.md) established a pluggable parser pattern for outline import (institutional unit outline documents → structured Unit metadata) using an `OutlineParser` ABC, a module-level registry, and a generic LLM-powered fallback alongside institution-specific parsers. The pattern works well in practice, and material import benefits from the same shape: pluggable parsers, registry-driven dispatch, propose/review/apply flow.

## Decision

Implement a parallel **structured material import architecture** using a pluggable `MaterialParser` ABC and module-level registry, mirroring the ADR-063 outline parser pattern. Material parsers convert uploaded files into ProseMirror `content_json` (plus extracted images and warnings) instead of plain text.

The architecture supports three import modes corresponding to the three real-world entry points lecturers use, share the same parser layer, and differ only at the persistence and routing boundary.

### Architecture

```
backend/app/services/material_parsers/
├── __init__.py           # Registry + factory (get_parser, list_parsers,
│                          #                     get_default_for_format, autodetect)
├── base.py               # MaterialParser ABC + MaterialParseResult schema
│                          #                    + ExtractedImage
├── persistence.py        # Shared post-parse helpers (persist_extracted_images,
│                          #                           rewrite_image_src)
└── pptx_structural.py    # python-pptx → content_json (Phase 1)
                          # Future: docx_pandoc, html_structural, md_structural,
                          #         pdf_paragraphs, pdf_llm, ipynb_structural,
                          #         revealjs_parser, marp_parser, quarto_qmd_parser
```

The two parser registries (`outline_parsers/` and `material_parsers/`) are intentionally independent. They produce different result schemas (`OutlineParseResult` vs `MaterialParseResult`), serve different consumers, and have different default-selection rules. Sharing one registry would conflate concerns.

### Parser interface

Each parser implements:

```python
class MaterialParser(ABC):
    name: ClassVar[str]                       # e.g. "pptx_structural"
    display_name: ClassVar[str]
    description: ClassVar[str]
    supported_formats: ClassVar[list[str]]    # e.g. ["pptx"]
    requires_ai: ClassVar[bool] = False       # gates parser by ADR-032 level

    @abstractmethod
    async def parse(
        self,
        file_content: bytes,
        filename: str,
        *,
        user_context: dict[str, object] | None = None,
    ) -> MaterialParseResult: ...
```

Parsers are **pure transformation layers**. They do not write to the database, the filesystem, or git. They take bytes in and return a `MaterialParseResult` out. The route layer (or the unified import service) handles persistence. This separation makes parsers trivially unit-testable without mocking I/O and ensures every entry point persists results identically.

### Result schema

```python
class ExtractedImage(BaseModel):
    filename: str        # parser-assigned, e.g. "slide-3-img-0.png"
    data: bytes
    mime_type: str | None = None

class MaterialParseResult(BaseModel):
    title: str | None                     # extracted from doc title / first heading / filename
    content_json: dict[str, Any]          # ProseMirror document
    images: list[ExtractedImage] = []     # bytes referenced from content_json
    warnings: list[str] = []              # transparent reporting per ADR-061
    parser_used: str
    confidence: float = 1.0               # informational only
```

Image src values inside `content_json` are bare filenames (`"slide-1-0.png"`) — placeholders the parser cannot fill in because it does not know the target material's id. The persistence layer rewrites these to canonical URLs after the material is created.

### Per-format default parsers

Each file extension maps to a default parser via a registry table:

```python
DEFAULT_PARSER_BY_FORMAT: dict[str, str] = {
    "pptx": "pptx_structural",
    # Phase 2: docx, html, htm, md, pdf, ipynb
}
```

Defaults are intentionally per-format rather than a single "auto" parser:

| Format | Default parser | Why |
|---|---|---|
| `.pptx` | `pptx_structural` (deterministic, python-pptx) | Format is well-defined; deterministic parsing wins on accuracy and cost |
| `.docx` | `docx_pandoc` (Pandoc subprocess) | Pandoc's DOCX reader is significantly better than what we'd write ourselves; we already depend on the Pandoc binary for export |
| `.html` / `.htm` | `html_structural` (BeautifulSoup) | Structurally rich; reuses sanitisation patterns from `package_import_service` |
| `.md` | `md_structural` (markdown-it-py or similar) | Already structured |
| `.pdf` | `pdf_paragraphs` (default) **or** `pdf_llm` (opt-in) | PDF structure is fundamentally unrecoverable; honest plain paragraphs by default with LLM-assisted second pass when AI is enabled (per [ADR-032](032-ai-assistance-levels.md)) |
| `.ipynb` | `ipynb_structural` | Cell boundaries are obvious |

For LLM-powered parsers, the `requires_ai` class flag gates them via the AI assistance level. The dispatcher hides them entirely from users whose level is `none`.

### Auto-detection dispatch (scaffolding for Phase 5+)

The registry exposes an `autodetect(file_content, filename)` function that inspects file content for **confident dialect signals** and returns a specialised parser id, or `None` to fall back to the format default. v1 returns `None` always — the dispatcher is wired in early so adding format-dialect parsers (Marp, reveal.js, Quarto) in later phases doesn't require touching the route layer.

Per the structured-import plan, only **YAML front-matter style signals** count as confident. Comment-based directives (e.g. Marp HTML comments) are too easy to false-positive and are deferred until at least one specialised parser ships.

### Three import modes

Lecturers do not import material the same way every time. The architecture distinguishes three modes corresponding to three real workflows. Each mode has its own route surface and persistence flow but shares the parser layer.

| Mode | Input | Target | Status |
|---|---|---|---|
| **A. Single file → existing unit** | One PPTX/DOCX/PDF/HTML/MD/IPYNB | Existing `Unit`, optional week + category | **Phase 1 done** for `.pptx` |
| **B. Multi-file zip → existing unit** | Folder zip | Existing `Unit`, week assignment from filename + folder path | **Phase 3 planned** — includes canonical + source files conflict resolution |
| **C. Full course / LMS export → new unit** | IMSCC / SCORM / round-trip / plain zip | New `Unit` (created during import) | **Phase 1 done for `.pptx` files inside the zip**, via `unified_import_service` integration; full Mode C polish in Phase 3 |

**The parser layer is mode-agnostic.** A `pptx_structural` parser produces the same `MaterialParseResult` whether called by a Mode A single-file route or by `unified_import_service` while walking a Canvas package's contents. This guarantees consistency: a PowerPoint with speaker notes round-trips identically regardless of how the user uploaded it.

### Persistence flow (chicken-and-egg sequencing)

The image src placeholder pattern creates a circular dependency: the parser emits `src="slide-1-0.png"` because it does not know the target `material_id`, but the canonical URL the editor needs (`/api/materials/units/{unit_id}/materials/{material_id}/images/{filename}`) requires that id.

Resolution sequence (identical for Mode A and the bulk path):

1. **Parse** the file into a `MaterialParseResult` (no DB or filesystem writes)
2. **Create** the `WeeklyMaterial` row with `content_json=None` and `description=None`, then `db.flush()` to obtain `material.id` without committing the transaction
3. **Persist images** under `weeks/week-NN/material-{material_id}.html.images/{filename}` via `git_content_service.save_binary()`, with collision resolution by 8-char SHA256 suffix (matching the convention from `routes/materials.upload_material_image`)
4. **Rewrite image src** in the parsed `content_json` from bare filenames to canonical URLs using the `{filename: url}` map returned by step 3
5. **Save** the rewritten `content_json` on the material and commit

Steps 3 and 4 are encapsulated in `material_parsers/persistence.py` (`persist_extracted_images` and `rewrite_image_src`) so Mode A, the bulk path, and any future modes share a single source of truth.

### API surface

Following the outline parser pattern, with three sets of mode-specific endpoints sharing a registry-listing endpoint:

| Endpoint | Method | Purpose |
|---|---|---|
| `/api/import/material/parsers` | GET | List registered parsers, optionally filtered by format |
| `/api/import/material/single/preview` | POST | Mode A: parse and return preview, no DB write |
| `/api/import/material/single/apply` | POST | Mode A: parse, create `WeeklyMaterial`, persist images |
| `/api/import/material/batch/preview` | POST | Mode B: zip preview with grouping (planned) |
| `/api/import/material/batch/apply` | POST | Mode B: persist with canonical + source files (planned) |

Mode C is currently served by the existing `/api/import/unified/{analyze,apply,status}` endpoints; the unified service routes `.pptx` files through the new parser internally. A dedicated `/api/import/material/course/*` surface may follow in Phase 3 if the unified endpoints diverge in shape.

### Bulk import integration (Mode C wiring)

`unified_import_service._extract_content` dispatches files based on extension:

- Files in `_STRUCTURED_EXTENSIONS` (currently `{".pptx"}`) go to the registered material parser, returning a `_ExtractedContent` dataclass with the full `MaterialParseResult` attached
- Files in `(".pdf", ".docx", ".md", ".txt")` continue through the legacy `file_import_service.process_file()` plain-text path until Phase 2 ships parsers for them
- HTML files use `PackageImportService.extract_html_content()` (unchanged)

`unified_import_service._process_files` checks each `_ExtractedContent` for a structured `parsed` field. If present, it routes through `_persist_structured_material`, which mirrors the Mode A apply flow exactly (create → flush → persist images → rewrite src → save). If absent, it falls back to the legacy `description=content_html` path.

Parser warnings are surfaced into `ImportTask.errors` so the bulk import status polling shows what was dropped per slide (per [ADR-061](061-transparent-import-reporting.md)).

`apply()` and `_run_import()` now require both `user_id` and `user_email` because git commits for extracted images need an author identity. The route layer passes `current_user.email` through.

## Consequences

### Positive

- **Consistency across upload paths.** A PowerPoint with speaker notes produces the same structured `WeeklyMaterial` whether uploaded as a single file (Mode A), inside a Canvas IMSCC export (Mode C), or, when Phase 3 ships, as part of a folder zip (Mode B). Lecturers don't have to know which path they're using.
- **Editable imported materials.** The original goal: imports go straight into the editor with full structural fidelity, no manual rebuilding. Closes the speaker notes round-trip gap end-to-end (per [ADR-064](064-rough-slides-as-feature.md)).
- **Pluggable extension point.** New formats and dialects ship as standalone parser modules. Adding `marp_parser` or `quarto_qmd_parser` requires editing only `material_parsers/__init__.py` to register, plus the parser file itself. No conditional branches in routes or services.
- **Mirrors an existing pattern.** ADR-063's `outline_parsers/` is a working precedent. New contributors who understand outline parsers immediately understand material parsers.
- **Single source of truth for persistence.** The `material_parsers/persistence.py` helpers eliminate copy-pasted git-write and src-rewrite logic across entry points.
- **Parser purity makes testing trivial.** Parsers take bytes, return data. Unit tests build PPTX files in memory with python-pptx and assert on the resulting `content_json` — no mocks, no fixtures on disk, no I/O.
- **Graceful degradation.** Formats without a registered parser fall through to the legacy plain-text extractor. Adding a parser for a new format is purely additive — nothing breaks if the parser is missing.

### Negative

- **Two parser registries to maintain.** `outline_parsers/` and `material_parsers/` share shape but not code. Bug fixes and improvements to the registry pattern need to be applied twice. The duplication is intentional (different result schemas) but has a maintenance cost.
- **Image persistence couples parsers to a specific filesystem layout.** The persistence helpers assume the git-backed `weeks/week-NN/material-{id}.html.images/` convention from [ADR-041](041-image-storage-in-git.md). Migrating to a different image storage backend (S3, CDN) would require updating the helpers and every test that asserts on canonical URLs.
- **PDF support is structurally honest but visually thin.** Phase 2's `pdf_paragraphs` produces flat paragraphs because PDF structure is unrecoverable from text alone. Lecturers used to "PDF import preserves headings" tools elsewhere may find this disappointing without the `pdf_llm` opt-in pass.
- **Format coverage is incremental.** Phase 1 ships PPTX only. Phase 2 adds DOCX, HTML, MD, PDF (paragraphs). Phase 3+ adds dialect specialisations. Until Phase 2 lands, DOCX and PDF imports remain plain text — an inconsistent UX users may notice.
- **Bulk import warnings are flat.** Parser warnings get appended to `ImportTask.errors` as plain strings. The frontend has no per-file structured warning display; it sees them mixed with hard errors. A future refinement could split structured warnings from hard errors.

### Neutral

- The `Content` model and its `/api/content/upload` route are explicitly out of scope. They remain as a legacy path; new structured imports target `WeeklyMaterial` exclusively. A separate cleanup may eventually deprecate the `Content` model entirely.
- Round-trip imports of Curriculum Curator's own export packages (`curriculum_curator_meta.json`) bypass material parsers entirely — they restore from saved metadata via `package_import_service._create_round_trip()`, which already preserves `content_json`.
- Auto-detection via `autodetect()` is wired in early but inert in v1. The dispatcher path exists so adding format-dialect parsers later doesn't require touching routes.

## Alternatives Considered

### Extend `file_import_service` with a new `extract_structured()` method

- Add a parallel method on the existing service that returns structured content alongside the plain-text method.
- Rejected: `file_import_service` is a monolith of conditional branches per format. Adding a structured pathway would either bloat the file further or fork it. The pluggable parser pattern from ADR-063 is a known-good shape that handles format diversity without monolithic conditionals.

### Single "auto" parser that dispatches internally based on file format

- One `AutoMaterialParser` class that inspects the file and routes to format-specific handlers privately.
- Rejected: This is the monolith pattern wearing a class. The user can't choose a non-default parser, the registry has nothing to list, and per-format default selection becomes a hidden internal switch instead of an explicit configuration.

### Convert imports to structured content via Pandoc only

- Use Pandoc as the universal import engine (Pandoc reads PPTX, DOCX, HTML, MD natively).
- Rejected for PPTX: Pandoc's PPTX reader is far less capable than python-pptx for slide-aware extraction (slide breaks, speaker notes, per-slide images). It's a good fit for DOCX (and is the recommended Phase 2 backend for `docx_pandoc`) but not for the slide-heavy formats lecturers care most about.

### Make material parsers a subclass of outline parsers

- Share the ABC and registry between outline and material parsing.
- Rejected: The result schemas are fundamentally different (`OutlineParseResult` is unit-level metadata; `MaterialParseResult` is content-level structure). Forcing them through a shared interface would either water down both schemas or require complex generic typing for marginal code reuse. Two parallel registries with the same shape is simpler.

### Mutate the parser to handle persistence

- Have parsers write their own images to git and return canonical URLs in `content_json`.
- Rejected: Couples parsers to the filesystem and the database, breaks unit-testability, and means every parser implementation needs to know about git, image conventions, and material IDs. Pure parsers + a persistence helper is much cleaner.

### Frontend conversion (parse PPTX in the browser)

- Use a JS PPTX parser (e.g. PptxGenJS) to extract structure client-side.
- Rejected: Image extraction, file reading, and large-file handling are all easier on the backend. Sharing parser code between Mode A (single file) and Mode C (bulk LMS) is also impossible if the parser only runs in the browser. The backend is the right place.

## Implementation Notes

Phase 1 of [docs/structured-import-plan.md](../structured-import-plan.md) is shipped as of 2026-04-10:

- ✅ `material_parsers/` directory with `base.py`, `__init__.py`, `pptx_structural.py`, `persistence.py`
- ✅ Mode A endpoints (`/api/import/material/parsers`, `/single/preview`, `/single/apply`)
- ✅ Frontend `PptxImportDialog` triggered from `WeeklyMaterialsManager`'s "Import PPTX" button per week
- ✅ `unified_import_service` integration for `.pptx` files (Mode C consistency)
- ✅ End-to-end round-trip tests on both Mode A and the bulk path
- ✅ Speaker notes round-trip via the export pipeline (per [ADR-064](064-rough-slides-as-feature.md))

Subsequent phases per the plan:

- **Phase 2:** `docx_pandoc`, `html_structural`, `md_structural`, `pdf_paragraphs`. Each is independent and slots into the existing registry. Frontend dialog already accepts arbitrary parsers via the `/parsers` endpoint, so format expansion is largely backend work plus extending the file picker accept list.
- **Phase 3:** Mode B (multi-file zip → existing unit) with the canonical + source files conflict resolution pattern. Dialect specialisations (Marp, reveal.js, Quarto, Jupyter) registered as alternative parsers for their formats with `autodetect()` wired up.
- **Phase 4:** `pdf_llm` opt-in PDF structuring using the structured LLM output retry pattern from [ADR-045](045-structured-llm-output-retry.md), gated by [ADR-032](032-ai-assistance-levels.md).
- **Phase 5+:** Admin upload of new parsers at runtime (designed-for via the registry abstraction, not built — same trajectory as ADR-063's note about institution parser uploads).

Future runtime parser upload would back the registry with a directory scan or a database table. The public API (`get_parser`, `list_parsers`, `get_default_for_format`, `autodetect`) remains stable, so changing the registry implementation doesn't affect callers.

## References

- [ADR-023: File Import and Processing Architecture](023-file-import-processing-architecture.md) — the legacy text-extraction architecture this builds on top of
- [ADR-032: AI Assistance Levels](032-ai-assistance-levels.md) — gates `requires_ai=True` parsers
- [ADR-038: Content Curation, Not Presentation Design](038-content-not-presentation.md) — what the parser deliberately discards
- [ADR-041: Image Storage in Git Repositories](041-image-storage-in-git.md) — where extracted images live
- [ADR-042: IMSCC and SCORM Import with Round-Trip Detection](042-package-import-round-trip.md) — the bulk-import path the new parsers hook into
- [ADR-045: Structured LLM Output with Retry Loop](045-structured-llm-output-retry.md) — pattern for the future `pdf_llm` parser
- [ADR-061: Transparent Import Reporting](061-transparent-import-reporting.md) — why parsers emit warnings instead of silently dropping content
- [ADR-063: Unit Outline Import with Pluggable Parser System](063-unit-outline-import-parser-system.md) — the parallel pattern this mirrors
- [ADR-064: Rough Slides Are a Feature, Not a Limitation](064-rough-slides-as-feature.md) — the pedagogical basis for first-class speaker notes
- [docs/structured-import-plan.md](../structured-import-plan.md) — phased implementation plan
- [docs/speaker-notes-plan.md](../speaker-notes-plan.md) — speaker notes work that this enables end-to-end
