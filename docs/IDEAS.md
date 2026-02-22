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

## LMS Interoperability

### LMS terminology and structure mapping

Different LMSs use different names and structures for the same concepts. Understanding
these mappings is needed before stories 9.9 (terminology mapping table) and 9.10
(LMS-targeted export) can be implemented.

**Investigation needed:**
- Canvas: Modules → Items, Assignments, Quizzes, Pages, Files
- Moodle: Sections → Activities/Resources, Assignments, Quizzes
- Blackboard: Content Areas → Items, Assignments, Tests

How do these map to our schema (Weeks → Materials/Assessments)? Are the IMSCC/SCORM
manifests structured differently per LMS, or is it the content naming that varies?

**Related:** ADR-042 (package import), stories 9.9, 9.10

---

## Dashboard & Navigation

### Unit quick actions: Clone, Export, Import

The unit dashboard currently has a Delete quick action icon. Add Clone, Export,
and Import as peer quick actions so common operations are one click away.

**Clone:** Duplicate a unit as a starting point. Use case: adapt an undergraduate
unit for postgraduate (or vice versa) — change depth, add research component,
adjust assessment weights. The backend already supports `POST /api/units/{id}/duplicate`
(story 1.5), this just surfaces it on the dashboard.

**Export:** Quick popup — select export format (IMSCC, SCORM, HTML, PDF, DOCX, PPTX),
optionally choose LMS target, export. Could also offer a "ZIP with rendered content"
option (HTML + assets bundled).

**Import:** Upload files directly from the dashboard rather than navigating to the
sidebar Import page. Reduces clicks for a common operation.

**Related:** Stories 1.5, 9.x, 6.x

### Remove Import from the sidebar?

If Import becomes a quick action on the unit dashboard, does the sidebar Import page
still earn its place? Removing it would simplify navigation.

**Questions:**
- The sidebar Import page currently handles both "import into existing unit" and
  "import to create a new unit" — the dashboard quick action only covers the first case
- What happens when imported material doesn't match the target unit (different topic,
  different level)? Currently no validation — the content just lands in the unit
- Could show a confirmation: "This PDF looks like a postgraduate unit but you're
  importing into ICT101 (undergraduate). Continue?"
- Maybe the sidebar page stays for "create new unit from import" and the dashboard
  action handles "add materials to this unit"

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

### In-app content preview (PDF, PPTX)

Add a preview panel so users can see how their content will look in export formats
without downloading a file. The existing Pandoc + Typst pipeline already renders
the output — the preview is just a UI wrapper around it.

**Approach:**
- **PDF preview:** Render via the existing export pipeline, serve the bytes from a
  `/api/preview` endpoint, display in a browser-native `<iframe>` (browsers have
  built-in PDF viewers). Upgrade to `react-pdf` later if more control is needed
  (page navigation, zoom, thumbnails).
- **PPTX preview:** Convert PPTX → PDF on the backend (LibreOffice headless or
  similar), then reuse the same PDF preview component. Loses animations but that's
  fine for content authoring — we care about structure and text, not transitions.
- **DOCX/HTML preview:** Same pattern — render to PDF via Pandoc, preview as PDF.
  HTML could alternatively render directly in an iframe.

**Key questions:**
- LibreOffice headless adds a dependency — acceptable for server deployments but
  needs thought for the Electron desktop build. Could skip PPTX preview in desktop
  mode or bundle a lighter converter.
- Caching: add a cache keyed on content hash so re-opening the preview doesn't
  re-render. Content changes invalidate the cache.
- Where does the preview panel live? Side panel in the editor? Modal? Separate tab?

**Related:** ADR-033 (Pandoc + Typst), ADR-035 (Electron desktop), story 9.4

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
