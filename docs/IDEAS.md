# Ideas & Future Discussions

> Scratchpad for feature ideas, technical investigations, and design discussions.
> Items here are speculative — not committed to. When an idea matures, it graduates
> to a user story in `user-stories.md` or a GitHub issue.

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

## Template

Use this structure for new entries:

```markdown
### Short title

One-paragraph description of the idea.

**Key questions / constraints:**
- Bullet points

**Related:** ADRs, user stories, or other ideas
```
