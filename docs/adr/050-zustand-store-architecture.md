# 50. Zustand Store Architecture with Selective Persistence

Date: 2026-02-23

## Status

Accepted

## Context

The React frontend needs client-side state management for authentication, user preferences, unit navigation context, and cached data. The state has mixed persistence requirements: auth tokens must survive page reloads, teaching style preferences should persist across sessions, navigation context should partially persist (which unit, but not ephemeral ULO data), and cached unit lists should not persist at all.

## Decision

Use Zustand with four purpose-specific stores, each with a tailored persistence strategy.

### Store Inventory

| Store | Persistence | Key | Strategy |
|-------|-------------|-----|----------|
| `authStore` | Manual `localStorage` | `'token'` | Token stored/cleared directly via `localStorage.getItem/setItem` — not through Zustand persist. State is in-memory only; token is the single source of truth for session recovery. |
| `teachingStyleStore` | Zustand `persist` | `'teaching-style-storage'` | Full state persisted — `globalStyle`, `isSet`, `aiAssistLevel`. No `partialize`. Initialised from user profile on login via `initFromUser()`. |
| `workingContextStore` | Zustand `persist` + `partialize` | `'working-context-storage'` | Only navigation-safe fields persisted: `activeUnitId`, `activeUnitTitle`, `activeUnitCode`, `activeTopicLabel`, `activeWeek`. Ephemeral fields (`activeULOs`, `activeDesignId`) are excluded — they're re-fetched on navigation. |
| `unitsStore` | None (memory only) | — | In-memory cache with 5-second stale-while-revalidate. `fetchUnits()` skips the API call if data is fresh. `invalidate()` forces refetch on next call. Optimistic local mutations (`addUnit`, `removeUnit`, `updateUnit`). |

### Key Patterns

**Selective persistence via `partialize`:** The working context store demonstrates the core pattern — persist just enough to restore the user's place (which unit, which week) without persisting data that may be stale on reload (ULO lists, design IDs). This avoids showing outdated ULOs from a previous session.

**Manual token management:** The auth store deliberately avoids Zustand persist for the JWT token. The token is stored directly in `localStorage` and read during `initializeAuth()`. This gives precise control over the clear-on-logout flow and avoids Zustand's persist middleware racing with manual localStorage operations.

**Stale-while-revalidate cache:** The units store uses a simple timestamp-based freshness check (`Date.now() - lastFetched < 5000`) rather than a library like React Query. This keeps the dependency footprint minimal while preventing redundant API calls during rapid navigation.

**Cross-store initialisation:** On successful auth, `authStore` calls `teachingStyleStore.initFromUser()` to sync the user's saved teaching style preference. This is the only cross-store dependency.

## Consequences

### Positive
- Each store's persistence matches its data lifecycle — no over-persisting stale data, no under-persisting user preferences
- `partialize` prevents stale ULO/design data from appearing on reload
- Minimal dependencies — Zustand is ~1KB, no React Query or Redux needed
- Optimistic mutations in `unitsStore` make the UI feel instant

### Negative
- Four stores with different persistence strategies add cognitive overhead for new developers
- Manual token management in `authStore` bypasses Zustand's middleware, splitting state management across two mechanisms
- 5-second cache in `unitsStore` is a magic number — too short for slow connections, too long for collaborative editing (not currently a concern)

### Neutral
- `teachingStyleStore` persists action functions too (they're no-ops in JSON serialisation) — harmless but imprecise
- No server-side state synchronisation — all persistence is localStorage-only, which means preferences don't follow the user across devices

## Alternatives Considered

### React Query / TanStack Query
- Automatic caching, deduplication, background refetching, stale-while-revalidate
- Rejected: adds a significant dependency for what amounts to one cached list (`units`) and three small preference stores; Zustand's simplicity is a better fit for this app's scale

### Redux + Redux Persist
- Industry standard with mature persistence middleware
- Rejected: boilerplate-heavy for 4 small stores; Zustand achieves the same with less code and no action/reducer ceremony

### Single Monolithic Store
- One Zustand store with all state, one persist configuration
- Rejected: impossible to persist teaching style but not unit cache, or persist unit ID but not ULOs, without `partialize` becoming a complex filter over unrelated concerns

### Context API Only
- React's built-in context for all shared state
- Rejected: causes unnecessary re-renders (context doesn't support selectors); Zustand's selector-based subscriptions are more performant

## Implementation Notes

- All stores in `frontend/src/stores/`
- `workingContextStore.partialize` explicitly lists the 5 persisted fields — adding new fields requires updating this list
- `unitsStore.invalidate()` should be called after any mutation that changes the unit list (create, delete, duplicate)
- Local mode detection in `authStore`: checks `GET /auth/config` first, then `GET /auth/local-session` for auto-login

## References

- `frontend/src/stores/authStore.ts`
- `frontend/src/stores/teachingStyleStore.ts`
- `frontend/src/stores/workingContextStore.ts`
- `frontend/src/stores/unitsStore.ts`
- [ADR-016: React + TypeScript Frontend](016-react-typescript-frontend.md)
- [ADR-040: Ambient Context Pattern](040-ambient-context-pattern.md) — working context store implements this pattern
