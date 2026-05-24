# CONTEXT — domain & architecture vocabulary

Shared language for the codebase, used by `/grill-with-docs` and `/improve-codebase-architecture`. Domain entities (Unit, Course, etc.) are defined in `CLAUDE.md` and ADR-028; this file names the **seams and module shapes** we design against, plus subsystem-specific terms as they firm up.

## Architecture module shapes

These two shapes recur across the architecture-deepening work (`docs/architecture-deepening.md`). Naming them keeps related candidates consistent.

- **Registry / adapter shape** — a deep seam where many concrete **adapters** satisfy one **interface**, looked up by a key. Adding a variant = write one adapter + one registration line, touching nothing else. Used by candidates #1 (export), #5 (import extraction), #6 (H5P). The interface is the test surface: tests exercise every adapter through the registry.
  - *adapter* — a concrete thing satisfying the interface at the seam (e.g. the SCORM exporter).
  - The router/registry stays dumb; all per-variant variance lives in the adapter and its registration.

- **Service-orchestrator shape** — a deep service that owns a multi-step flow (gather context → call dependencies → assemble result) behind one interface, so routes stay thin HTTP glue. Used by candidates #2 (AI generation) and #4 (curriculum context).

## Export subsystem

- **Export format key** — the canonical string identifying one export format. **Locked vocabulary = `format_resolver`'s underscore names**, because those are already *persisted* (`WeeklyMaterial.export_targets`, `teaching_preferences.export_defaults`): `qti`, `h5p_question_set`, `h5p_course_presentation`, `h5p_branching`, `h5p_interactive_video`, `html`, plus the package/document keys `scorm`, `imscc`, `pdf`, `docx`, `pptx`. The old short HTTP segments (`h5p`, `h5p-slides`, …) are retired — URLs and the ~4 frontend GET call sites move onto the canonical names. `format_resolver` is unchanged.
- **Export scope** — whether an export targets a whole **Unit** or a single **WeeklyMaterial**. Not every format supports both (e.g. `scorm` is unit-only; document `pdf`/`docx` is material-only). The registry holds this capability matrix and rejects unsupported (format × scope) pairs cleanly.
- **`ExportResult`** — the uniform return shape at the export seam: `(buf, filename, media_type, metadata)`. Already defined in `services/export/base.py`. Each adapter computes its own filename and media_type (where that knowledge lives), instead of routes patching it.
- **Export adapter** — a `BaseExporter` subclass producing an `ExportResult` for a given scope. Declares its own typed options model (most are empty; `scorm`/`imscc` accept `target_lms`).
- **`ExportRegistry`** — the seam: maps an export format key → adapter, dispatches `export(format, scope, target, db, options)`, answers `supports(format, scope)` and `available_formats(scope)`. The single source of truth for "what formats exist."
- **Planning vs execution** — `format_resolver` + `export/preview` *plan* (which targets apply to which material); the `ExportRegistry` *executes* (produce the bytes). They now share one export format key vocabulary, so the old hidden frontend translation (`h5p_question_set` → `h5p`) disappears.
- **Package orchestration** — `POST .../export/package` builds a whole-unit IMSCC/SCORM cartridge with per-material target overrides. It is *not* an adapter; it is a batch orchestrator that dispatches through the `ExportRegistry` (by package type) and keeps its own async/task machinery.

## Cross-cutting access

- **`get_user_material`** — (to be added in `api/deps.py`) a dependency that loads a `WeeklyMaterial`, verifies the caller owns its Unit, and 404s otherwise — mirroring the existing `get_user_unit`. Closes the material-scope access gap and is the first slice of candidate #3 (resource-ownership seam).
