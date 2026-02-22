# ADR-032: AI Assistance Levels

## Status

Accepted

## Context

Lecturers have varying comfort levels with AI-generated content in curriculum design. Some want full AI generation capabilities, others prefer AI only for polishing their own writing, and some want no AI involvement at all — just a clean manual curriculum builder with pedagogy-guided tips.

A single "AI on/off" toggle is too coarse: it forces a choice between full AI and no AI, missing the middle ground of AI-assisted refinement. We need a model that respects lecturer autonomy — "use the tool their way to teach their way."

The existing pedagogy system (9 teaching styles with hints) currently only serves AI prompt engineering. In a no-AI mode, this pedagogy knowledge should still provide value as static guidance.

## Decision

We introduce **three AI assistance levels** that progressively gate AI features across the application:

| Level | Label | Behaviour |
|-------|-------|-----------|
| `none` | No AI | All AI buttons, icons, and sidebar hidden. The app is a manual curriculum builder. Pedagogy provides static tips and expanded guidance in the editor. |
| `refine` | Correct & Refine | Inline AI assist shows "Improve" and "Suggest alternatives" only. No content generation, scaffolding, or AI chat. Pedagogy guides AI refinement prompts. |
| `create` | Create & Generate | Full AI capabilities (current behaviour). Generation, scaffolding, planner, AI chat. Pedagogy guides AI content generation. |

**Default level**: `create` (preserves current behaviour for existing users).

### Implementation approach

- The level is stored in the user's `teaching_preferences` JSON field as `aiAssistLevel`.
- A single `useAILevel()` React hook provides boolean flags (`isAIDisabled`, `canGenerate`, `canRefine`, `canChat`, `canScaffold`) consumed by all AI-adjacent components.
- Components check these flags to conditionally render AI controls.
- In `none` mode, pedagogy shifts from AI prompt guidance to static tips: each teaching style provides 4 expanded guidance bullets displayed in the editor and materials manager.
- LLM settings remain accessible at all levels so users can configure API keys before enabling AI.

## Consequences

### Positive

- Lecturers who distrust or are restricted from using AI still get a fully functional curriculum builder with pedagogy guidance.
- The "refine" level provides a middle ground for lecturers who write their own content but want AI polish.
- Pedagogy knowledge is useful at every level, not just for AI prompts.
- Single hook pattern keeps gating logic consistent and easy to audit.
- Default of `create` means no behaviour change for existing users.

### Negative

- Every AI-adjacent component must check the level flags — missing a check could leak AI features into "no AI" mode.
- Three levels means more testing permutations for the UI.
- Static pedagogy tips need content authoring for all 9 styles (36 tips total).
