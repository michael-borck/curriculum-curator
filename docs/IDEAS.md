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

## Python Package / CLI / TUI

Repackage the backend as a standalone Python package that can be used without
the web UI. The service layer (`services/`) is already cleanly separated from
FastAPI routes — services are plain classes that take a `db: Session` and return
domain objects, with zero FastAPI dependency.

**Options (not mutually exclusive):**
- **Library API** — `pip install curriculum-curator`, call services directly from scripts
- **CLI** (`typer` or `click`) — power users, scripting, CI pipelines
- **TUI** (`textual`) — interactive terminal UI for power users
- **`$EDITOR` integration** — shell out to the user's editor for content editing
  (markdown workflow, convert to HTML on save)

**What makes this feasible:**
- Services layer has no FastAPI coupling (decorators only on route functions)
- Only need a direct SQLAlchemy session provider (trivial) and simplified auth
- LLM streaming maps naturally to terminal output (print tokens as they arrive)

**Key questions:**
- Which level to target first — library, CLI, or TUI?
- Auth model for local use — skip auth, or simplified local-user mode?
- Content format — keep HTML, or use markdown for CLI/TUI and convert?

**Related:** ADR-013 (Git-backed storage would pair well with CLI workflows)

---

## Analytics

### Auto-snapshot cleanup policy

Daily auto-snapshots will accumulate over time. Consider adding a cleanup
policy to thin out old auto-snapshots — e.g., keep daily for the last 30 days,
then only weekly, then only monthly. Manual (labelled) snapshots would never
be auto-deleted.

**Key questions:**
- What retention windows make sense? (30 days daily, 6 months weekly, forever monthly?)
- Should this be a background task or run lazily when new snapshots are created?
- User-configurable retention, or just sensible defaults?

**Related:** `AnalyticsSnapshot` model, `snapshot_service.maybe_auto_snapshot()`

---

### Trend charts / sparklines

Add visual trend lines showing how quality and UDL scores have changed over
time, using the snapshot history. Could be sparklines on the dashboard or a
dedicated trends view.

**Related:** `SnapshotCompare.tsx`, snapshot API endpoints

---

## Outline Import — Future Enhancements

### Admin-managed custom outline parsers

Allow admins to add institution-specific outline parsers without code deployment.
Workflow: download a parser template (Python file with the `OutlineParser` ABC
pre-filled), edit it for their institution's outline format, upload it back.
Uploaded parsers stored in `backend/user_parsers/{org_id}/` with sandboxed
execution.

**Key questions:**
- Security model for executing user-uploaded Python — sandbox via subprocess + restricted imports?
- Storage: per-organisation or per-user?
- Validation: run against a sample document before activation?

### User-managed personal parsers

Educators working at multiple institutions may want their own parsers. Similar
to admin-managed but scoped to the individual user. Appears in their parser
dropdown only.

**Key questions:**
- Same sandbox approach as admin parsers?
- UI for managing personal parsers (list, test, delete)
- Could a non-technical user build a parser? Maybe a config-driven approach (section headings + regex patterns) instead of raw Python?

**Related:** ADR-063, user stories 1.13–1.15

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
