# Ideas & Future Discussions

> Scratchpad for feature ideas, technical investigations, and design discussions.
> Items here are speculative — not committed to.
>
> **Workflow:** Explore an idea → make a decision → remove it from this file.
> - **Build it** → write a user story in `user-stories.md`, update `acceptance-tests.md`, delete from here
> - **Reject it** → delete from here (note the reason in the commit message)
>
> This file should stay small. If it's growing, ideas aren't being resolved.

---

## Export & Theming

### PPTX/DOCX reference document templates

Pandoc supports `--reference-doc=template.pptx` (and `.docx`) — the template's
slide masters, colours, and fonts are applied to exported content. This could let
users produce institution-branded exports without manual formatting.

**Possible flow:**
1. User imports a PPTX → content is extracted as materials (existing feature)
2. The original file is also saved as an export template for that unit
3. Future PPTX exports use the saved template, preserving institutional branding

**Constraints:**
- Pandoc only uses master slides/layouts and theme from the reference doc, not content
- A content-heavy PPTX with no custom masters would produce a generic export
- Need a place to store templates (per-unit? per-user? system-wide?)
- UI needed to manage templates (upload, select default, preview)

**Related:** ADR-033 (Pandoc + Typst), story 9.4 (document export)

---

## Dashboard & Navigation

### ~~Remove Import from the sidebar?~~ — Done

Sidebar "Import Materials" entry removed. The dashboard quick actions cover both
"Import Files" (per-unit) and "Import Package" (header + per-unit dropdown). The
`/import` route still works via deep-links from the dashboard.

Content-level validation on import (topic/level mismatch detection) is still missing.

**Related:** Stories 6.x, ADR-023 (file import architecture)

---

## Editor

### Auto-save with save indicator

Add debounced auto-save while editing materials, with a visible indicator
("Saving...", "Saved", "Unsaved changes"). Currently users must manually save,
and there's no feedback about save state.

**Key questions:**
- Debounce interval — 2 seconds after last keystroke? Configurable?
- What about Git versioning — should auto-save create Git commits, or only
  save to the database (with explicit "Save Version" for Git commits)?
- Conflict handling if the same material is open in two tabs

**Related:** Story 13.1 (save version / commit), ADR-013 (Git-backed storage)

---

## Preview

### ~~In-app content preview (PDF, PPTX)~~ — Done

PDF and HTML preview added as a modal on the MaterialDetail page. Uses the existing
`POST /content/{id}/export/document` endpoint; renders in a browser-native iframe.
Preview button only appears when Pandoc/Typst are installed (checked via
`GET /export/availability`). PPTX/DOCX preview not yet supported — would need
LibreOffice headless for server-side conversion.

---

## Deployment & Landing Page

### ~~Landing page with platform-detected download~~ — Done

`/download` page added with `navigator.userAgent` platform detection, GitHub
Releases API integration for dynamic download links, Docker self-host section,
and source link. Landing page hero CTA navigates to `/download`; "Install" text
link added to the nav bar.

---

## Template

Use this structure for new entries:

```markdown
### Short title

One-paragraph description of the idea.

**Key questions / constraints:**
- Bullet points

**Related:** ADRs, user stories, or other ideas
```
