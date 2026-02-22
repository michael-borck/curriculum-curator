# 47. Editor Modes with Quarto Export Configuration

Date: 2026-02-23

## Status

Superseded by [ADR-033](033-pandoc-typst-export-engine.md)

## Context

The rich text editor (TipTap WYSIWYG) is the primary content authoring surface. Some users also need fine-grained control over document export — Quarto output formats, themes, table of contents, and custom YAML front matter. Exposing these settings by default would overwhelm users who just want to write content.

The question: how to offer export configuration power without cluttering the simple editing experience.

## Decision

Implement a two-mode editor toggled via a Simple/Advanced pill switch, where both modes share the same TipTap WYSIWYG editor for content authoring. The modes differ only in what surrounds the editor.

**Simple mode** (`RichTextEditor`): Full WYSIWYG editor with toolbar (formatting, tables, code blocks, images, video embeds, Mermaid diagrams). Pedagogy hints shown based on teaching style. No export settings visible.

**Advanced mode** (`QuartoEditor`): Wraps the same `RichTextEditor` with an additional Quarto controls panel offering:
- Output format selection (HTML, PDF, DOCX, revealjs, beamer)
- Theme picker, TOC toggle, author/title/subtitle fields
- A sub-toggle between "simple" (form fields) and "advanced" (raw YAML editor with optional presets)
- Preview button (renders via backend and displays in a side panel)
- Export button (triggers file download)
- Settings persisted to the backend via `PUT /content/{id}/quarto-settings`

**Mode preference** stored in `localStorage` key `'editor-mode-preference'`, defaulting to `'simple'`.

Critically, there is no raw markdown editing mode — content is always authored through TipTap WYSIWYG. The "Advanced" label refers to export configuration, not editing capability.

## Consequences

### Positive
- Simple mode is uncluttered — most users never see Quarto settings
- Power users get full Quarto control without leaving the editor
- Same underlying editor means no content format divergence between modes
- Mode preference persists across sessions

### Negative
- The "Simple" vs "Advanced" labelling may mislead users into thinking Advanced offers different editing features (it doesn't — only export settings differ)
- Quarto settings are per-content-item, stored server-side — switching modes doesn't affect what's saved

### Neutral
- Quarto settings have their own simple/advanced sub-toggle (form fields vs raw YAML), adding a second layer of progressive disclosure

## Alternatives Considered

### Raw Markdown / Split-Pane Editor
- Show source markdown alongside WYSIWYG preview
- Rejected: adds complexity for minimal benefit — Quarto YAML is the only "source" users need to see, and most content is authored visually

### Export Settings as a Separate Page
- Move Quarto configuration to an export dialog or settings page
- Rejected: users want to preview and tweak export settings while viewing their content, not navigate away

### Always-Visible Export Panel
- Show Quarto controls in both modes
- Rejected: overwhelms the majority of users who just need WYSIWYG editing

## Implementation Notes

- `UnifiedEditor.tsx` reads mode from localStorage on mount, conditionally renders `RichTextEditor` or `QuartoEditor`
- `EditorModeToggle.tsx` is a controlled component — no internal state
- `QuartoEditor` renders `RichTextEditor` as a child, passing through all content props
- Quarto settings are a `QuartoSettings` interface with `mode: 'simple' | 'advanced'`
- Export endpoint: `POST /content/{id}/export`, preview: `POST /content/{id}/preview`

## References

- `frontend/src/components/Editor/UnifiedEditor.tsx`
- `frontend/src/components/Editor/QuartoEditor.tsx`
- `frontend/src/components/Editor/EditorModeToggle.tsx`
- [ADR-015: Content Format and Export Strategy](015-content-format-and-export-strategy.md)
- [ADR-033: Pandoc + Typst Export Engine](033-pandoc-typst-export-engine.md)
