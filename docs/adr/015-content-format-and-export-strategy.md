# 15. Content Format and Export Strategy

Date: 2025-12-01

## Status

Proposed

## Context

The Curriculum Curator needs to support diverse user workflows for creating, editing, and exporting educational content. Our target users range from "PowerPoint people" (comfortable with Microsoft Office, unfamiliar with HTML/Markdown) to "power users" (comfortable with CLI, Markdown, and technical tools).

### The Core Tension

We face competing requirements:

| Requirement | Best Solution |
|-------------|---------------|
| Best editing UX for typical users | TipTap WYSIWYG (HTML-based) |
| Best export flexibility | Quarto/Pandoc (Markdown-based) |
| LLM content generation | Markdown or JSON (cleaner than HTML) |
| Offline editing continuity | DOCX, Markdown files |
| LMS integration | HTML copy-paste, SCORM packages |
| Slides/presentations | PPTX, Reveal.js |

### Current State

- TipTap editor outputs HTML (`editor.getHTML()`)
- ADR-013 proposes Git storage with `.md` files
- No export pipeline exists
- No formal decision on canonical storage format

### User Workflow Philosophy

> "I want this tool to assist the lecturer in whatever workflow they have, not enforce another opinion."

Users should be able to:
- Draft content in our tool, then continue in Word/PowerPoint offline
- Import existing materials (PDF, DOCX) for enhancement
- Export to any format their LMS accepts
- Use simple WYSIWYG or access raw Markdown (power users)

The tool provides a **default workflow** but does not **enforce** it.

## Decision

### 1. Markdown as Canonical Internal Format

All content is stored as Markdown internally. This enables:
- Clean LLM generation (LLMs produce better Markdown than HTML)
- Git-friendly storage (per ADR-013)
- Universal export via Quarto/Pandoc
- Power user access to source

```
┌─────────────────────────────────────────────────────────────┐
│              CANONICAL FORMAT: MARKDOWN                      │
│              (stored in database + git)                      │
└─────────────────────────────────────────────────────────────┘
```

### 2. Dual-Mode Editing

**Simple Mode (Default):** TipTap WYSIWYG editor with `tiptap-markdown` extension
- Users see familiar rich text editing
- Markdown stored transparently underneath
- Round-trips cleanly for standard formatting (headings, lists, bold, italic, code, tables)

**Power Mode (Opt-in):** Split-pane Markdown editor
- Left: Monaco/CodeMirror text editor with raw Markdown
- Right: Live preview (rendered via markdown-it or similar)
- Toggle via "View Source" button

```
┌─────────────────────────────────────────────────────────────┐
│  [Simple Mode]  [Power Mode]                                │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│   Simple Mode:              Power Mode:                      │
│   ┌─────────────────┐       ┌──────────┬──────────┐         │
│   │  TipTap WYSIWYG │       │ Markdown │ Preview  │         │
│   │  (familiar UI)  │       │ Source   │          │         │
│   └─────────────────┘       └──────────┴──────────┘         │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 3. Quarto as Export Engine

Quarto (built on Pandoc) transforms Markdown to any output format:

| Export Format | Use Case |
|---------------|----------|
| HTML | LMS copy-paste, web embedding |
| PDF | Printed handouts, worksheets |
| DOCX | Offline editing in Word |
| PPTX | Lecture slides |
| Reveal.js | Browser-based presentations |

```
Markdown (internal)
    │
    └──► Quarto
         ├──► HTML   (LMS paste)
         ├──► PDF    (handouts)
         ├──► DOCX   (offline editing)
         ├──► PPTX   (slides)
         └──► Reveal.js (web presentations)
```

### 4. Content Type Handling

| Content Type | Editor | LLM Output | Primary Export |
|--------------|--------|------------|----------------|
| Worksheet | TipTap WYSIWYG | Markdown | HTML, PDF |
| Quiz | TipTap + structure | Markdown/JSON | HTML, PDF |
| Handout | TipTap WYSIWYG | Markdown | PDF, DOCX |
| Lecture Slides | TipTap (slide-aware) | Markdown | PPTX, Reveal.js |
| Lecture Notes | TipTap WYSIWYG | Markdown | HTML, PDF |

### 5. Slides Strategy

Slides are Markdown with heading-based slide breaks:

```markdown
---
format: pptx
title: "Introduction to Neural Networks"
---

# Introduction
<!-- New slide on each H1 -->

- Point one
- Point two

# Main Concepts

Details here become slide content...
```

TipTap edits the whole document. Users can:
- Preview as slides (Reveal.js in browser)
- Download as PPTX for PowerPoint editing
- Continue development in PowerPoint if preferred

### 6. Import Strategy (Future)

Support importing existing materials:

| Import Format | Conversion |
|---------------|------------|
| DOCX | Pandoc → Markdown |
| PDF | PyMuPDF/pdfplumber → text → Markdown |
| HTML | Pandoc → Markdown |
| Markdown | Direct import |

Imported content becomes Markdown. Original files are not retained - the tool stores only the converted Markdown under Git version control.

## Consequences

### Positive

- **Universal export**: Single source (Markdown) produces any format
- **LLM-friendly**: LLMs generate cleaner Markdown than HTML
- **Git-friendly**: Markdown diffs are readable and meaningful
- **User choice**: Simple WYSIWYG or power-user Markdown access
- **Offline continuity**: Export to DOCX/PPTX for continued editing elsewhere
- **No workflow enforcement**: Tool assists without mandating specific practices

### Negative

- **Round-trip limitations**: Complex TipTap formatting may simplify when converted to Markdown
- **Tables complexity**: Markdown tables are less flexible than HTML tables
- **Learning curve**: Power mode requires Markdown knowledge
- **Quarto dependency**: Backend requires Quarto installation

### Neutral

- **Two editor modes**: More UI complexity, but clear separation
- **Slide editing**: Not a dedicated slide editor, but functional for content generation
- **Import fidelity**: Imported PDFs lose formatting; users must accept this trade-off

## Alternatives Considered

### HTML as Canonical Format

- **Description**: Store TipTap HTML directly, convert to Markdown only for export
- **Rejected because**: HTML→Markdown loses fidelity; Git diffs are noisy; LLMs generate worse HTML

### Separate Format Per Content Type

- **Description**: HTML for worksheets, Markdown for notes, JSON for quizzes
- **Rejected because**: Complexity; inconsistent export paths; harder to maintain

### No Power Mode

- **Description**: Only offer WYSIWYG, hide Markdown from all users
- **Rejected because**: Conflicts with "assist any workflow" philosophy; power users need source access

### Build Custom Slide Editor

- **Description**: Purpose-built slide editing UI with canvas positioning
- **Rejected because**: Significant complexity; Quarto's PPTX export handles 90% of use cases; users can refine in PowerPoint

### Skip Quarto, Use Individual Libraries

- **Description**: python-pptx for slides, WeasyPrint for PDF, python-docx for Word
- **Rejected because**: Multiple code paths; less consistent output; Quarto unifies all exports

## Implementation Notes

### TipTap Markdown Integration

```typescript
import { Markdown } from 'tiptap-markdown';

const editor = useEditor({
  extensions: [
    StarterKit,
    Markdown.configure({
      transformPastedText: true,
      transformCopiedText: true,
    }),
  ],
  content: markdownContent,
});

// Get markdown for storage
const markdown = editor.storage.markdown.getMarkdown();
```

### Database Schema

```python
class Content(SQLModel):
    id: UUID
    title: str
    content_markdown: str          # Canonical format
    content_type: ContentType      # lecture, worksheet, quiz, slides
    unit_id: UUID
    created_at: datetime
    updated_at: datetime
    git_commit_hash: str | None    # Per ADR-013
```

### Export Endpoint

```python
@router.get("/content/{content_id}/export")
async def export_content(
    content_id: UUID,
    format: ExportFormat,  # html, pdf, docx, pptx, revealjs
):
    content = await get_content(content_id)
    
    # Write markdown to temp file
    # Run: quarto render content.md --to {format}
    # Return rendered file
```

### Quarto Backend Requirements

```bash
# Install Quarto (backend dependency)
# macOS
brew install quarto

# Linux
wget https://quarto.org/download/latest/quarto-linux-amd64.deb
dpkg -i quarto-linux-amd64.deb

# Docker: Include in Dockerfile
```

## References

- [ADR-013: Git-Backed Content Storage](013-git-backed-content-storage.md)
- [ADR-005: Hybrid Storage Approach](005-hybrid-storage-approach.md)
- [Quarto Documentation](https://quarto.org/)
- [tiptap-markdown Extension](https://github.com/aguingand/tiptap-markdown)
- [Pandoc User's Guide](https://pandoc.org/MANUAL.html)
