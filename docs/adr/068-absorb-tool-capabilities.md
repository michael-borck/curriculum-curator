# 68. Absorb Standalone Tool Capabilities, Not the Apps

Date: 2026-08-25

## Status

Accepted

## Context

Four standalone tools exist in Michael's portfolio, each solving a slice of the
teaching-preparation workflow with its own LLM-provider layer:

| Tool | Capability relevant to Curriculum Curator | Form |
|---|---|---|
| **Limn** | Text-to-image generation across providers (SwarmUI, OpenAI-compatible, Google Imagen) | Python CLI |
| **Playable Lessons** | Material → branching Ink story, flashcards, quizzes, summaries; propose/refine authoring loop | Electron app + npm CLI |
| **Lesson Loom** | Material + pedagogical framework (Gagné's Nine Events, BOPPPS, 5E) → structured timed lesson plan | React/Tauri app |
| **UDL Lens** | CAST UDL 3.0 checkpoint audit of assessments | Next.js app |

Curriculum Curator already implements most of UDL Lens (ADR-057,
`udl_audit_service`). For the other three there are two options: integrate the
apps (embed, link out, or IPC) or absorb their *capabilities* as native
features.

Integrating the apps would mean a fifth LLM key-management surface per user
(each tool has its own provider layer), five places to fix provider bugs, and
workflow fragmentation — content leaves the editor's design context and comes
back as files. Story 15.9 already demonstrated the awkward version of this:
generate an image *prompt* here, copy it into an external tool, download the
result, upload it back.

## Decision

Absorb the capabilities as native Curriculum Curator features; do not
integrate, embed, or depend on the standalone apps or their CLIs.

The capabilities land on existing seams rather than new subsystems:

1. **AI image generation** (from Limn) — `POST /api/ai/generate-image` backed
   by litellm image generation using the existing per-user/system LLM config.
   Results flow through the existing material image storage/serve pipeline
   (story 15.4). Reverses the 2026-03-09 cut of story 15.5; closes the
   generate-prompt → external-tool → re-upload loop opened by 15.9, which stays
   as the escape hatch for users preferring their own tools.
2. **Branching scenario drafting** (from Playable Lessons) —
   `POST /api/ai/materials/{id}/generate-branching` drafts cards + choices +
   endings from material content, reviewed via propose/apply and emitted as
   existing `branchingCard` nodes (19A). No Ink runtime is introduced; the
   interactive HTML player from 19B remains the delivery vehicle.
3. **Quiz generation into structured blocks** (from Playable Lessons) —
   `POST /api/ai/materials/{id}/generate-quiz` emits existing `quizQuestion`
   nodes via propose/apply (19C.2/C.3), so AI-drafted questions export through
   QTI/H5P unchanged. Flashcards are deferred until a flashcard node/export
   target exists.
4. **Lesson-plan frameworks** (from Lesson Loom) — Gagné's Nine Events, BOPPPS,
   and 5E enter as seeded templates in the prompt-template library (ADR-058)
   plus a `/api/ai/generate-lesson-plan` endpoint that returns Bloom-tagged
   objectives, segments timed to the requested session length, formative checks
   with anticipated misconceptions, and differentiation notes. Framework
   "when to use" metadata ships with the seeds.

All four reuse the single LLM service (litellm, ADR for multi-provider), token
accounting, and AI-gating (`ENABLE_AI_FEATURES`, per-user keys) already in the
backend. Generation features follow the established propose/apply review
pattern (per speaker notes, story 15.11) — nothing writes to a material without
user review.

## Consequences

### Positive
- One LLM/provider layer, one key store, one usage-accounting path.
- Generated artefacts are first-class editor citizens (nodes, images in the
  unit library), so they import/export via all existing pipelines.
- The standalone tools remain useful independently; nothing breaks if they
  evolve or die.
- Prompt engineering from the tools (frameworks, branching structure) survives
  as inspectable, editable prompt templates.

### Negative
- Duplicated maintenance of prompts between the tools and this repo until the
  tools are retired or explicitly left to diverge.
- Image generation adds a provider capability with patchy litellm coverage;
  some providers will need dedicated handling.

### Neutral
- UDL Lens stays a separate grant deliverable; its remaining unique UI (radar
  chart, PDF report) may still be ported later.
- Flashcards and Playable Lessons' clarification step are deferred, not cut.

## Alternatives Considered

### Integrate the apps (link-out, iframe, or CLI invocation)
- Keeps each tool's UX intact, but fragments auth/keys across five surfaces,
  adds subprocess/packaging burden (CLIs in a PyInstaller desktop build), and
  pulls content out of the design context that is this app's differentiator.

### Port each tool wholesale as a plugin
- The plugin system (ADR-003) is scoped to validation/remediation of content,
  not generation pipelines; widening it for this is a larger architectural
  change than the capability absorption needs.

## Implementation Notes

- Endpoints live in `routes/ai.py` beside the other generation endpoints;
  schemas in `schemas/ai.py`; services in `services/` following the
  speaker-notes batching pattern where material content is involved.
- Image bytes are stored by the existing material-image service so serving,
  deletion, and export treat generated and uploaded images identically.
- Lesson-plan framework seeds are marked `is_system` so admins can customise
  copies but users cannot break the shipped definitions.

## References

- [ADR-003: Plugin Architecture](003-plugin-architecture.md)
- [ADR-057: UDL Inclusivity Scoring Model](057-udl-inclusivity-scoring-model.md)
- [ADR-058: Prompt Template Library](058-prompt-template-library.md)
- Stories: 15.5 (reinstated), 15.9, 5.12–5.13, 19A.7, 19C.6
- Standalone tools: Limn (`~/Projects/limn`), Playable Lessons
  (`~/Projects/playable-lessons`), Lesson Loom (`~/Projects/lesson-loom`),
  UDL Lens (`~/Projects/lens/udl-lens`)
