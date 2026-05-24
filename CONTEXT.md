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

## AI generation subsystem

Candidate #2 (design locked in grill). Deepen the existing seam rather than add a new orchestrator layer — the deep retry/validate engine already exists.

- **`generate_structured_content`** — the deep generation engine (ADR-045): renders a prompt, calls the LLM, strips fences, parses JSON, validates against a Pydantic model, and **retries with temperature decay + error-feedback re-prompts**, returning `(result | None, error | None)`. Being made flexible: accept a **custom `system_prompt`** (so endpoints keep their injection-hardened prompts) and an **`inject_schema` flag** (schema comes from the response model by default, so prompts no longer hand-write it).
- **Strict-with-retry contract** — JSON endpoints validate against their response model; malformed/incomplete output re-prompts, then surfaces a clean error. Replaces the lenient `.get()`-with-defaults construction. Tolerance is encoded in the model (`Optional` fields + defaults), not hand-coded per route. Each model is shaped (required vs optional) during migration.
- **`CurriculumContextBuilder`** — one seam for "build the AI context" (design + pedagogy + week + source materials), replacing the scattered `get_design_context` / `_enrich_with_week_context` / `_inject_source_materials` / `build_pedagogy_instruction` stitching across ~7 endpoints. **This is candidate #4, delivered as part of #2.**
- **`ai_prompts/` package** — generation prompts live as code (a hardened system-prompt constant + a `render_*` function per endpoint), co-located with their response models. Not the Jinja2 library (ADR-046) and not the runtime-editable DB templates (ADR-058) — those serve user-facing content prompts, a separate concern.
- **Leaky endpoints in scope** — the 9 in `ai.py` that hand-roll prompt assembly + JSON parse + retry + error-string sniffing: `validate-content`, `generate-schedule`, `validate`, `remediate`, `scaffold-unit`, `fill-gap`, `visual-prompt`, `generate-video-interaction`, `suggest-interaction-points`. The 12 clean delegating endpoints stay as-is.
- **Error contract** — `generate_text` returns error *strings* (callers string-sniff `"Error generating text:"`). JSON endpoints stop using it; they go through `generate_structured_content`'s `(result, error)` tuple.

## Cross-cutting access

- **`get_user_material`** — (to be added in `api/deps.py`) a dependency that loads a `WeeklyMaterial`, verifies the caller owns its Unit, and 404s otherwise — mirroring the existing `get_user_unit`. Closes the material-scope access gap and is the first slice of candidate #3 (resource-ownership seam).
