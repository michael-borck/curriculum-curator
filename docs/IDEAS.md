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

## Template

Use this structure for new entries:

```markdown
### Short title

One-paragraph description of the idea.

**Key questions / constraints:**
- Bullet points

**Related:** ADRs, user stories, or other ideas
```
