# 52. Unit-Level Feature Toggles via Metadata

Date: 2026-02-23

## Status

Accepted

## Context

The app offers several optional panels and capabilities per unit: Graduate Capability mappings, AoL (Assurance of Learning) mappings, UN SDG mappings, and potentially more in the future. Not every unit needs all of these — an introductory programming unit rarely needs SDG mappings, while a capstone unit probably needs everything. Previously all panels were always visible, adding visual clutter for units that didn't use them.

We needed a way for each unit to opt in/out of features without:

1. Adding a column per feature to the `units` table (schema churn every time a feature is added)
2. Creating a separate `unit_features` table (over-engineering for simple boolean flags)
3. Using a global config that applies to all units equally

## Decision

Store feature flags as a JSON object inside the existing `unit_metadata` JSONB column on the `Unit` model, under the key `features`.

### Schema

```python
# Stored in Unit.unit_metadata
{
  "features": {
    "graduateCapabilities": true,   # default: true
    "aolMapping": true,             # default: true
    "sdgMapping": true              # default: true
    # Future toggles go here
  }
  # ... other metadata keys remain unaffected
}
```

### Frontend Consumption

In `UnitPage.tsx`, features are read with a default-true pattern:

```typescript
const features = unit.unitMetadata?.features ?? {};
const showGradCaps = features.graduateCapabilities ?? true;
const showAolMapping = features.aolMapping ?? true;
const showSdgMapping = features.sdgMapping ?? true;
```

This means existing units (where `features` is absent) get all panels — opt-out, not opt-in.

### Settings UI

The `UnitSettings` component provides toggle switches for each feature. Toggling writes to `unit_metadata.features` via `PUT /api/units/{id}` — no separate endpoint needed.

## Consequences

### Positive
- Zero schema migrations when adding a new toggle — just add a key to the JSON and a toggle to the Settings UI
- Existing units are unaffected (defaults are all `true`)
- Feature state travels with the unit on export/import (it's in the metadata blob)
- Simple to implement — no new tables, no new endpoints, no new services

### Negative
- No database-level querying of feature flags (can't do `WHERE features->>'sdgMapping' = 'false'`) — acceptable because there's no use case for filtering units by feature flags
- No validation of the `features` keys at the schema level — a typo (`"sdgMaping"`) would silently do nothing; the frontend default-true pattern masks it
- Feature flags are per-unit only — no "set defaults for all new units" mechanism yet

### Neutral
- The `unit_metadata` column was already JSONB, so this adds no new column or index
- Default-true means features are visible unless explicitly disabled — matches the "assist any workflow" philosophy (ADR-018)

## Alternatives Considered

### Separate `unit_features` Table
- One row per unit per feature, with `unit_id`, `feature_key`, `enabled` columns
- Rejected: over-engineering for 3-5 boolean flags; adds joins to every unit query; JSONB is already there

### Column Per Feature on Units Table
- `show_grad_caps: bool`, `show_aol: bool`, `show_sdg: bool`
- Rejected: requires an Alembic migration every time a feature is added; clutters the units table; boolean columns don't scale

### Global Config in Admin Settings
- Admin sets which features are available system-wide
- Rejected: different units genuinely need different features; a capstone unit and a first-year elective shouldn't share the same panel visibility

## Implementation Notes

- Feature toggles live in `UnitSettings` component (`frontend/src/components/UnitStructure/UnitSettings.tsx`)
- Conditional rendering in `UnitPage.tsx` controls panel visibility
- The `unit_metadata` column is typed as `JSON` in SQLAlchemy (`backend/app/models/unit.py`)
- Structure presets in the Create Unit modal can set initial feature flags (e.g. a "minimal" preset might disable all three)

## References

- [ADR-018: Workflow Flexibility Philosophy](018-workflow-flexibility-philosophy.md) — "assist, don't enforce"
- [ADR-029: Accreditation Framework Mappings](029-accreditation-framework-mappings.md) — the features being toggled
- `frontend/src/components/UnitStructure/UnitSettings.tsx`
- `frontend/src/pages/UnitPage.tsx`
