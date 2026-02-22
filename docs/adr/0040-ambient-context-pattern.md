# 0040. Ambient Context — Best Guess + Human Override

Date: 2026-02-22

## Status

Accepted

## Context

Users frequently move between pages — dashboard, unit details, AI assistant, research, import — while mentally "working on" a particular unit. Without a shared context system, each page or tool starts from scratch: the AI assistant on its standalone page has no idea which unit the user cares about, Save to Unit always prompts for a target, and suggestions are generic rather than relevant.

The naive fix is to ask the user explicitly every time ("Which unit is this for?"). But that creates friction that compounds across a session. The opposite extreme — inferring everything silently with no escape hatch — risks locking users into a context they didn't intend.

We needed a pattern that:
- Reduces repetitive selection (most of the time the system can guess correctly)
- Never traps the user (they can always override or clear the guess)
- Stays transparent (the current context is always visible and obvious)

## Decision

We adopt the **Ambient Context** pattern, following the principle of **"best guess + human override"**:

1. **Infer**: The system observes user navigation and sets context automatically. Visiting `/units/abc123` sets that unit as the working context.
2. **Persist**: Context survives navigation. Moving to the dashboard, AI assistant, or research page does not clear it. Context is stored in localStorage and restored on page refresh.
3. **Display**: A persistent header indicator shows the current context at all times — which unit, optionally which week. The user always knows what the system thinks they're working on.
4. **Override**: The user can change context at any time via the header dropdown (switch to a different unit) or clear it entirely (X button). No confirmation dialogs, no friction.
5. **Fallback gracefully**: When no context is set, features degrade gracefully — AI gives generic responses, Save to Unit opens a picker, suggestions are not unit-specific. Nothing breaks.
6. **Props trump store**: When a component receives explicit props (e.g., AI assistant embedded in a unit page), those props take precedence over the ambient context. The store is a fallback, not a mandate.

### The Pattern in Summary

| Aspect | Behaviour |
|--------|-----------|
| **Set** | Auto-detected from navigation |
| **Persist** | Survives page changes and refresh |
| **Display** | Always visible in header |
| **Override** | One-click change or clear |
| **Absent** | Features degrade gracefully, nothing breaks |
| **Conflict** | Explicit props > ambient context > no context |

### Where This Pattern Applies Today

| Feature | Inference Source | Override Mechanism |
|---------|-----------------|-------------------|
| **Working Context** (unit) | URL navigation to `/units/:id` | Header pill dropdown / X button |
| **Teaching Style** | User profile setting | Header style selector dropdown |
| **AI Assist Level** | User profile setting | Settings page |

### Applying This Pattern to Future Features

Any new feature that needs a "current X" should follow the same contract:

- **Auto-set** from the most natural user action (navigation, selection, creation)
- **Persist** until explicitly changed — don't reset on navigation
- **Show** the current value somewhere visible and accessible
- **Let the user change it** with minimal friction (one or two clicks)
- **Degrade gracefully** when absent — never block functionality

Examples where this pattern could extend:
- Active week within a unit
- Default content type for new materials
- Preferred export format

## Consequences

### Positive
- Dramatically reduces repetitive "which unit?" prompts across the app
- Standalone AI assistant becomes contextually useful without any extra setup
- Save to Unit works with one click when context is set
- Transparent — users always see what the system inferred
- No lock-in — clearing or changing context is trivial
- Pattern is reusable for future "current X" needs

### Negative
- Stale context risk: user forgets context is set to Unit A while mentally working on Unit B. Mitigated by the always-visible header indicator.
- localStorage coupling: context is per-browser, not per-device. Acceptable for a single-user tool.
- Slightly more complex component logic: components must resolve `props ?? store ?? undefined` chains.

### Neutral
- Multiple tabs share context via localStorage (Zustand persist). This is usually desirable but could surprise a user working on different units in different tabs.
- ULOs and designId are not persisted (re-fetched per session) to avoid stale data, while id/title/code/week are persisted for quick restore.

## Alternatives Considered

### Always Ask Explicitly
- Every tool prompts "Which unit?" before doing anything
- Rejected: too much friction for the common case where the user has been working on one unit all session

### Infer Silently, No Override
- System guesses context and uses it without showing the user
- Rejected: violates transparency; users wouldn't know why AI responses changed or where content was being saved

### Persistent Sidebar with Unit Selector
- Dedicated sidebar panel always showing current unit and allowing switching
- Rejected: consumes screen real estate; a header pill achieves the same goal with less space

### Session-Only Context (No Persistence)
- Context resets on page refresh
- Rejected: users expect to resume where they left off; persistence via localStorage is cheap and reliable

## Implementation Notes

- **Store**: `workingContextStore.ts` — Zustand with `persist` middleware, `partialize` to only persist id/title/code/week
- **Sync hook**: `useWorkingContextSync.ts` — one-way URL → store, runs in `AppLayout`
- **Indicator**: `WorkingContextIndicator.tsx` — header pill with dropdown, placed in AppLayout header
- **Stale check**: sync hook auto-clears context if the active unit no longer exists in the units list (handles deletion)
- **Resolution pattern**: `const effectiveX = propX ?? ctx.activeX ?? undefined`

## References

- [ADR-0018: Workflow Flexibility Philosophy](0018-workflow-flexibility-philosophy.md) — "Assist any workflow, don't enforce"
- [ADR-0020: AI-Optional User Empowerment](0020-ai-optional-user-empowerment.md) — features degrade gracefully without AI, same principle applies to context
- [ADR-0004: Teaching Philosophy System](0004-teaching-philosophy-system.md) — earlier instance of the same pattern (persisted default with override)
