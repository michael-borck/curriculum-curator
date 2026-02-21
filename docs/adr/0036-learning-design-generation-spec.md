# ADR-0036: Learning Design as Canonical Generation Spec

Date: 2026-02-21

## Status

Accepted

## Context

The application currently has **four separate AI generation paths**, each collecting context in different ways and at different depths:

| Path | Context Source | Status |
|------|---------------|--------|
| **WorkflowWizard** | 8-9 hardcoded questions → single generate call | Orphaned (component exists, no entry point) |
| **Quick Scaffold** | Unit title + description only | Active, thin context |
| **Course Planner** | Unit metadata + ULOs + weekly structure | Active, medium context |
| **AI Sidebar Chat** | Free-text prompt, minimal unit context | Active, stateless |

None of these paths reference the **Learning Design** — a structured, persistent document that captures exactly the information AI needs: objectives, learning outcomes, class structure, assessment strategy, resources, and prerequisites.

### The Small Model Problem

Users may run local models via Ollama (llama3.2, mistral, phi-3) that have significantly less capacity than frontier models (GPT-4, Claude). Frontier models can infer reasonable curriculum structure from a sparse title and description. Small models cannot — they need dense, structured context to produce useful output. The Learning Design provides exactly this: a specification document that compensates for reduced model capability.

This is analogous to spec-driven development in AI coding tools (Cursor, Aider, Claude Code) where a structured requirements document keeps the AI focused and reduces hallucination.

### The Orphaned Wizard

The `WorkflowWizard` component collects 8-9 questions (unit goals, audience, duration, etc.) through a step-by-step flow, then offers "Generate with AI" or "Create Empty Structure". However:

- It is **never imported or rendered** anywhere in the application
- It has **no awareness** of the `aiAssistLevel` setting
- The backend `CONTENT_GENERATION` and `QUALITY_REVIEW` workflow stages it depends on are **stubbed but never entered**
- Its questions overlap almost entirely with what the Learning Design already captures

The wizard represents an earlier design that has been superseded by the Learning Design model.

## Decision

**The Learning Design becomes the canonical specification that feeds all AI generation paths.** It replaces the orphaned WorkflowWizard and serves as the single source of truth for what a unit should contain.

### AI Assist Level Mapping

The three AI assistance levels (ADR-0032) determine how the Learning Design is created and used:

| Level | Learning Design Flow | Generation Behaviour |
|-------|---------------------|---------------------|
| `none` | **Guided Setup** — structured form with pedagogy tips, static guidance, section-by-section manual entry. No AI involvement. | No AI generation. The Learning Design is a planning document the lecturer fills out and uses as their own reference. |
| `refine` | **Assisted Drafting** — lecturer fills in the basics (title, objectives, key topics). AI suggests improvements, identifies gaps, proposes alternatives. Lecturer approves each suggestion. | AI can refine and improve existing content using the Learning Design as context. No wholesale generation. |
| `create` | **AI-Drafted Spec** — lecturer provides title, description, and key constraints. AI drafts a complete Learning Design. AI asks clarifying questions. Lecturer reviews, edits, and approves the spec before any content is generated. | Full AI generation using the approved Learning Design as the specification. All generation paths read from it. |

### Key Design Principles

1. **Spec before generation**: In `create` mode, the Learning Design is drafted and approved *before* any unit content is generated. This gives the lecturer a review checkpoint and ensures AI has structured context.

2. **Clarifying dialogue**: In `create` mode, AI should ask clarifying questions about the Learning Design (audience level, assessment preferences, time constraints) rather than making assumptions. This is especially valuable with small models that hallucinate when given ambiguous input.

3. **No "wizard" terminology**: The guided setup for `none` mode is not called a "wizard" — users may associate "wizard" with AI automation. Instead, use neutral terms like "guided setup" or "design builder".

4. **Visible AI level indicator**: The UI must clearly communicate the active AI assistance level throughout the Learning Design flow, so lecturers always know whether AI is involved and to what degree.

5. **Learning Design is optional**: Per ADR-0020, lecturers can skip the Learning Design entirely and create unit content directly. The Learning Design enhances AI generation quality but never gates manual content creation.

### Generation Pipeline Integration

All AI generation paths should read from the unit's Learning Design when one exists:

```
Learning Design (approved)
    │
    ├── Quick Scaffold → uses LD objectives, structure, duration
    ├── Course Planner → uses LD weekly breakdown, assessments, outcomes
    ├── AI Sidebar Chat → includes LD summary in system prompt
    └── Content Generation → uses LD topic detail for specific materials
```

When no Learning Design exists, generation paths fall back to current behaviour (unit title + description + any available ULOs).

## Consequences

### Positive

- **Small model compensation**: Structured spec provides the dense context that local models need to produce useful output, narrowing the quality gap between Ollama and frontier models.
- **Consistency**: All generation paths use the same source of truth, eliminating contradictions between generated materials.
- **Lecturer checkpoint**: The spec-then-generate flow gives lecturers a review point before AI produces content, building trust and maintaining agency.
- **Reduces hallucination**: AI generates against an approved spec rather than inferring from sparse input.
- **Replaces dead code**: The orphaned WorkflowWizard can be removed — its functionality is superseded.
- **Iterative refinement**: The Learning Design is editable and versionable, supporting the lecturer's iterative design process.

### Negative

- **Extra step for power users**: Lecturers who want to "just generate" must create or approve a Learning Design first (in `create` mode). Mitigation: AI drafts the spec quickly from title + description.
- **Implementation effort**: All generation paths need updating to read from the Learning Design.
- **Schema coupling**: Changes to the Learning Design JSON structure affect all generation paths.

### Neutral

- **Learning Design remains a standalone feature**: Even without AI, it serves as a structured planning document — consistent with the app being a "course design IDE".
- **Existing Learning Design CRUD is already implemented**: The model, service, routes, and UI components are in place from the LRD → Learning Design rename.

## Alternatives Considered

### Keep Separate Context Collection Per Path

- **Description**: Each generation path continues to collect its own context independently.
- **Rejected because**: Duplicates effort, produces inconsistent output, and provides no small-model compensation.

### Inline Context Injection (No Persistent Spec)

- **Description**: Collect context via a wizard/form at generation time but don't persist it.
- **Rejected because**: Loses the spec on page refresh, can't be iteratively refined, and doesn't serve as a planning document in `none` mode.

### Auto-Generate Learning Design from Unit Data

- **Description**: AI silently constructs a Learning Design from existing unit data before generating content.
- **Rejected because**: Violates ADR-0020 (no AI defaults) — the lecturer should explicitly create and approve the spec. Also adds latency for a step the user never sees.

## Implementation Notes

### Phase 1: Wire Up (Minimum Viable)
- Remove the orphaned `WorkflowWizard` component
- Update Quick Scaffold and Course Planner to read from the unit's Learning Design (if one exists) and include its content in the LLM prompt context
- Add AI level indicator to the Learning Design creation flow

### Phase 2: Spec-First Flow
- In `create` mode, prompt users to create a Learning Design before first generation
- Add clarifying question dialogue when AI drafts a Learning Design
- Update AI Sidebar Chat system prompt to include Learning Design summary

### Phase 3: Refinement
- In `refine` mode, add inline AI suggestions to the Learning Design editor
- Add a "completeness score" showing how much of the Learning Design is filled out
- Track which generation outputs were produced with vs without a Learning Design (for quality comparison)

## Related Decisions

- [ADR-0020: AI-Optional User Empowerment](0020-ai-optional-user-empowerment.md) — AI assists, never gates
- [ADR-0032: AI Assistance Levels](0032-ai-assistance-levels.md) — The three-level model this ADR builds on
- [ADR-0018: Workflow Flexibility Philosophy](0018-workflow-flexibility-philosophy.md) — Assist any workflow, don't enforce
- [ADR-0025: Ollama Docker Sidecar](0025-ollama-docker-sidecar-local-ai.md) — Local model support that motivates small-model compensation
- [ADR-0035: Electron Desktop App](0035-electron-desktop-app.md) — Desktop deployment where local models are the primary AI option
