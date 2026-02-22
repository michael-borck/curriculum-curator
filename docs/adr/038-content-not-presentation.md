# ADR-038: Content Curation, Not Presentation Design

Date: 2026-02-21

## Status

Accepted

## Context

Curriculum Curator supports importing content from multiple sources (PDF, DOCX, PPTX, web, IMSCC, SCORM) and exporting to multiple formats (HTML, PDF, DOCX, PPTX, IMSCC, SCORM). This creates a tension: how much visual fidelity should be preserved across the import → edit → export pipeline?

Users naturally expect "what I import is what I get." But attempting to faithfully reproduce PowerPoint layouts, PDF formatting, or LMS styling in an editor would require building a presentation tool — competing with PowerPoint, Google Slides, and LMS editors on their home turf. That's not our product.

The question: where does Curriculum Curator's responsibility begin and end?

## Decision

Adopt a strict **content-in, content-out** pipeline with a clear three-phase model:

```
Import (strip styling) → Edit (semantic content) → Export (apply themes)
```

### 1. Import Extracts Content, Not Formatting

All importers (PDF, DOCX, PPTX, IMSCC, SCORM, web) produce clean semantic content:

- **Text** → Markdown (headings, paragraphs, lists, tables, code blocks)
- **Content images** → Inline images embedded with the material (diagrams, photos, illustrations on slides)
- **Speaker notes** → Preserved as a separate notes section
- **Metadata** → Title, author, structure hints (slide order, chapter breaks)

**Deliberately discarded on import:**
- Backgrounds, watermarks, slide masters, header/footer templates
- Transitions, animations, custom layouts
- Theme colours, custom fonts, decorative elements
- Slides/pages with no textual content (decorative/title-only slides flagged for review)

The UI must be explicit about this. Import screens should state:

> "Curriculum Curator extracts your content (text, images, notes), not your formatting. Import gives you editable materials — use your preferred tool for final presentation design."

### 2. The Editor Works With Semantic Content

The TipTap editor handles structured content:
- Headings, paragraphs, lists (ordered/unordered), blockquotes
- Tables, code blocks with syntax highlighting
- Inline images (from URL or uploaded from disk)
- Mermaid diagrams (flowcharts, sequence diagrams)
- Embedded video links (YouTube, Vimeo)

No slide layouts, no background images, no header/footer editing, no presentation-level styling. The editor is for *content authoring*, not visual design.

### 3. Export Applies Styling via Themes

Export is where presentation quality is added:

- **HTML**: 2–3 clean CSS themes (academic, minimal, modern). Suitable for direct LMS pasting.
- **PDF**: Pandoc + Typst templates with professional typography.
- **DOCX**: Pandoc reference document with university-appropriate styling.
- **PPTX**: Clean content-focused template (title + body per slide, images inline). Users style further in PowerPoint.
- **IMSCC / SCORM**: Package content with basic, clean styling that LMS platforms render well. Users accept these are functional packages, not design showcases — the LMS applies its own theme on top.

The export UI offers theme selection: "Choose a look for your export" with visual previews.

### 4. Images Are Part of the Document

No separate media library or asset manager. Images are stored alongside their material:

- **Editor upload**: User uploads from disk → stored in the content repository alongside the material → referenced by relative path
- **URL insert**: Already supported — image referenced by external URL
- **Import extraction**: Content images extracted from source documents → stored with the imported material
- **Export bundling**: Images included in the export package (IMSCC/SCORM resource files, PPTX media, PDF inline)

One material = one markdown file + its associated images. Simple, portable, Git-friendly.

## Consequences

### Positive

- **Clear product identity**: Content curation tool, not a presentation editor. No feature creep toward slide design.
- **Import robustness**: Extracting content is far more reliable than preserving formatting across formats. Complex PowerPoints with backgrounds and animations don't break the import — they just produce clean text.
- **User expectations managed**: The three-phase model (strip → edit → theme) is easy to explain and hard to misunderstand.
- **Export quality control**: A small set of curated themes produces consistently professional output, rather than garbage-in-garbage-out formatting.
- **Simpler codebase**: No need to model slide layouts, style hierarchies, or format-specific rendering in the editor.

### Negative

- **PowerPoint round-trip lossy**: Users importing a heavily styled PPTX will lose all visual design. The UI must make this obvious *before* import, not after.
- **IMSCC/SCORM styling is basic**: Exported LMS packages use clean but simple styling. Users wanting branded, visually rich LMS content need to edit in the LMS after import.
- **No media library**: Users managing many images across materials must organise them externally. Acceptable for the single-user desktop target (ADR-037).

### Neutral

- Theme development (Pandoc templates, CSS themes, PPTX reference documents) is a separate workstream that can expand over time without changing the architecture.
- The approach aligns with ADR-037 (local-first): images stored on-disk with content, no cloud media hosting.

## Alternatives Considered

### Preserve Import Formatting

- Attempt to reproduce source document styling in the editor.
- Rejected: Technically impractical across formats (PPTX ≠ PDF ≠ IMSCC styling models), creates false expectation of visual fidelity, and turns the editor into a layout tool.

### Separate Media Library

- Central asset manager for images, files, and media across all materials.
- Rejected for now: Over-engineering for single-user desktop app. Images-with-document is simpler, more portable, and Git-friendly. Could be revisited if multi-user collaboration is added.

### WYSIWYG Slide Editor

- Build a slide-by-slide visual editor for PPTX-like output.
- Rejected: Directly competes with PowerPoint/Google Slides. Not the product. Users should use those tools for presentation design and this tool for content curation.

## Implementation Notes

- PowerPoint import (`python-pptx`): Use shape type and position to distinguish content shapes from background/master elements. Extract `MSO_SHAPE_TYPE.PICTURE` from slide shapes only (not slide layouts or masters).
- Image storage: Store in the content Git repository under `materials/{material_id}/images/`. Reference with relative markdown paths.
- Import UI: Add pre-import notice explaining what will and won't be extracted.
- Export themes: Start with 2–3 Pandoc templates. PPTX uses a reference template (`--reference-doc`).
- IMSCC/SCORM exports: Include a minimal `styles.css` in the package. Keep it clean — the LMS theme takes over.

## References

- [ADR-033: Pandoc + Typst Export Engine](033-pandoc-typst-export-engine.md)
- [ADR-035: Electron Desktop App](035-electron-desktop-app.md)
- [ADR-037: Privacy-First, BYOK Architecture](037-privacy-first-byok-architecture.md)
- User stories: 6.4, 6.6, 15.4 (import/export/image handling)
