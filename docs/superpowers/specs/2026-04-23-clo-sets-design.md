# CLO Sets — Design Spec

**Date:** 2026-04-23  
**Status:** Approved  
**Context:** Curtin unit coordinators need to map their Unit Learning Outcomes (ULOs) to Course Learning Outcomes (CLOs) defined at the degree-program level. CLOs are program-specific (unlike the fixed GC/AoL/SDG taxonomies), vary per program, and are shared across multiple units in the same program.

---

## Problem

CLOs already exist in the DB (`unit_learning_outcomes` table, `outcome_type = "clo"`) but are completely dormant — no API routes, no UI, no mapping flow. A lecturer maintaining three units in the same program must be able to define their CLO set once and apply it to all three units, with ULO→CLO mappings suggested by AI and confirmed/corrected by the user.

---

## Data Model

### New tables

**`clo_sets`** — user-scoped CLO library entry (one per degree program)

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID PK | |
| `user_id` | UUID FK → users | owner |
| `name` | String(100) | e.g. "Bachelor of Computer Science" |
| `description` | Text nullable | |
| `program_code` | String(20) nullable | e.g. "BCS" |
| `created_at` | DateTime | |
| `updated_at` | DateTime | |

**`clo_items`** — individual CLOs within a set

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID PK | |
| `clo_set_id` | UUID FK → clo_sets CASCADE | |
| `code` | String(20) | e.g. "CLO1" |
| `description` | Text | outcome text |
| `order_index` | Integer default 0 | |
| `created_at` | DateTime | |
| `updated_at` | DateTime | |

**`unit_clo_set_assignments`** — which CLO sets a unit uses

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID PK | |
| `unit_id` | UUID FK → units CASCADE | |
| `clo_set_id` | UUID FK → clo_sets CASCADE | |
| `created_at` | DateTime | |

Unique constraint on `(unit_id, clo_set_id)` — no duplicates.

**`ulo_clo_item_mappings`** — ULO → CLO item, many-to-many

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID PK | |
| `ulo_id` | UUID FK → unit_learning_outcomes CASCADE | |
| `clo_item_id` | UUID FK → clo_items CASCADE | |
| `is_ai_suggested` | Boolean default False | |
| `notes` | Text nullable | |
| `created_at` | DateTime | |
| `updated_at` | DateTime | |

Unique constraint on `(ulo_id, clo_item_id)`.

### Existing table — no changes

The `unit_learning_outcomes` rows with `outcome_type = "clo"` (created by the document analyser on outline import) are left untouched. Reconciling those into CLO sets is Phase 2.

---

## Backend

### New files

- `backend/app/models/clo_set.py` — four new models above
- `backend/app/schemas/clo_sets.py` — Pydantic request/response schemas
- `backend/app/services/clo_set_service.py` — business logic
- `backend/app/api/routes/clo_sets.py` — router
- `backend/migrations/versions/<hash>_add_clo_sets.py` — Alembic migration

### API routes

Mounted at `/api/clo-sets`:

```
GET    /api/clo-sets                              list user's CLO sets
POST   /api/clo-sets                              create CLO set
GET    /api/clo-sets/{set_id}                     get set + items
PUT    /api/clo-sets/{set_id}                     update set metadata
DELETE /api/clo-sets/{set_id}                     delete set

POST   /api/clo-sets/{set_id}/items               add item
PUT    /api/clo-sets/{set_id}/items/{item_id}     update item
DELETE /api/clo-sets/{set_id}/items/{item_id}     delete item
POST   /api/clo-sets/{set_id}/items/reorder       reorder items
```

On the units router:

```
GET    /api/units/{unit_id}/clo-sets              get assigned CLO sets (with items)
POST   /api/units/{unit_id}/clo-sets/{set_id}     assign CLO set to unit
DELETE /api/units/{unit_id}/clo-sets/{set_id}     unassign CLO set
```

On the outcomes router:

```
GET    /api/ulos/{ulo_id}/clo-mappings            get CLO mappings for a ULO
PUT    /api/ulos/{ulo_id}/clo-mappings            replace all CLO mappings for a ULO
POST   /api/units/{unit_id}/clo-suggestions       AI-suggest CLO mappings for all ULOs
```

### AI suggestion logic (`clo_set_service.suggest_clo_mappings`)

For each ULO in the unit, call the LLM with:
- The ULO code + description
- All CLO items (code + description) from all CLO sets assigned to the unit

The LLM returns a list of `(ulo_id, clo_item_id)` pairs. Matches are saved with `is_ai_suggested = True`. The user then confirms or rejects each suggestion in the UI. This mirrors the existing GC suggestion flow in `accreditation.py`.

---

## Frontend

### New files

- `frontend/src/components/UnitStructure/CLOMappingPanel.tsx` — alignment panel (mirrors `GraduateCapabilitiesPanel.tsx`)
- `frontend/src/features/settings/CLOSetManager.tsx` — library management UI
- `frontend/src/services/cloSetsApi.ts` — API client
- `frontend/src/types/cloSets.ts` — TypeScript interfaces

### CLOMappingPanel (Unit page)

Located in the alignment section of `UnitPage.tsx`, after the existing `GraduateCapabilitiesPanel`. Feature-flagged via `features.cloMapping ?? true`.

Collapsed by default. Header shows: "Course Learning Outcomes · N sets · M ULOs mapped".

When expanded:
- Each assigned CLO set renders as a sub-section with its program name
- Each CLO item row shows the code, truncated description, and ULO chips mapped to it
- "Assign CLO Set" button opens a picker modal listing the user's library
- "Suggest mappings" button calls `/api/units/{unit_id}/clo-suggestions`, then shows each suggestion with ✓/✗ controls
- Accepted suggestions become confirmed mappings; rejected ones are discarded
- User can also manually toggle any ULO→CLO mapping
- "Unassign" option per CLO set (removes the assignment, not the set from the library)

### CLO Set Manager (Settings)

New tab in the Settings page: "CLO Sets". Lists the user's CLO sets as cards showing name, program code, and item count. 

Per set:
- Inline-edit name, program code, description
- Add/edit/delete CLO items (code + description fields, drag handle to reorder)
- Delete set (with warning if assigned to any units)

### cloSetsApi.ts

Typed API client functions mirroring the route list above. All functions async, use the existing `api` Axios instance.

---

## Migration strategy

1. Add Alembic migration for the four new tables
2. No data migration needed — existing dormant CLO rows in `unit_learning_outcomes` are unaffected
3. DB reset is fine (no production users per CLAUDE.md)

---

## Out of scope (Phase 2)

- Importing CLOs from unit outline parse results into a CLO set
- Sharing CLO sets between users (e.g., a program coordinator publishing a canonical set)
- CLO→GC / CLO→AoL cross-framework shortcut mapping (AI suggestion already covers this)
- Bloom's level on CLO items
