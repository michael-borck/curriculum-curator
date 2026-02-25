# ADR-059: Week-Aware AI Context & Source Grounding

Date: 2026-02-25

## Status

Accepted

## Context

The AI assistant was disconnected from the user's working context. It didn't know which week the user was viewing, couldn't reference existing materials for that week, and had no way to ground generation in the user's own content. This led to generic outputs that often duplicated what already existed.

Three specific problems:

1. **No week awareness** — the frontend had `activeWeek` in the Zustand store but never set it; the backend accepted `week_number` in `ContentGenerationRequest` but ignored it
2. **No existing-material awareness** — the AI couldn't see what materials already existed for a week, so it might suggest creating content that's already there
3. **No source grounding** — users couldn't say "base this on my lecture notes" without copy-pasting content into the chat

## Decision

### Week context wiring (frontend → backend)

`UnitPage.tsx` now calls `setActiveWeek(weekNumber)` when expanding a week accordion (and `null` when collapsing). The URL-sync `useEffect` also sets it. `AIAssistant.tsx` reads `ctx.activeWeek` and:

- Appends `Current Week: N` to the context prefix shown to the LLM
- Passes `weekNumber` in the API call to `/ai/generate`

### Week-aware enrichment (backend)

When `/generate` receives both `week_number` and `unit_id`, the route queries `WeeklyTopic` and `WeeklyMaterial` for that week and prepends:

- The weekly topic title (e.g. "Week 3 Topic: Database Normalisation")
- Existing material titles (e.g. "Existing materials for this week: Lecture Slides, Tutorial Worksheet")

This is injected as plain-text context before the user's prompt, so the LLM can generate complementary rather than duplicate content.

### Source material selection

A new `source_material_ids` field on `ContentGenerationRequest` accepts up to 5 material IDs. The backend fetches their titles and descriptions, then injects them as a `=== SOURCE MATERIALS ===` block in the prompt. This grounds generation in the user's own content without requiring copy-paste.

On the frontend, a collapsible "Source Materials" picker appears in the AI sidebar when a unit + week context is active. It shows checkboxes for materials in the current week.

### "Create with AI" entry point

Each week row in `WeekAccordion` gets a Sparkles icon button. Clicking it sets `activeWeek` and opens the AI sidebar, providing a direct creation workflow from the unit structure view.

## Consequences

- AI responses are now contextualised to the specific week the user is working on
- Duplicate content generation is reduced because the LLM sees what already exists
- Source grounding enables workflows like "create a tutorial based on my lecture notes"
- The Sparkles button on week rows provides a discoverable AI entry point
- Source material injection is capped at 5 items to stay within reasonable prompt sizes
- Only material titles and descriptions are injected (not full body content from Git) to keep prompts focused

## Key Files

- `frontend/src/pages/UnitPage.tsx` — sets `activeWeek` on expand/collapse
- `frontend/src/features/ai/AIAssistant.tsx` — week badge, source picker, `weekNumber` + `sourceMaterialIds` in API calls
- `frontend/src/components/UnitStructure/WeekAccordion.tsx` — Sparkles button + `onOpenAI` prop
- `backend/app/api/routes/ai.py` — `_enrich_with_week_context()` and `_inject_source_materials()` helpers
- `backend/app/schemas/content.py` — `source_material_ids` field on `ContentGenerationRequest`
