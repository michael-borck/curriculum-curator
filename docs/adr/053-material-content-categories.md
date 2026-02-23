# 53. Material Content Categories

Date: 2026-02-23

## Status

Accepted

## Context

Weekly materials in a unit serve different purposes at different times: students read before class, participate during class, and consolidate afterwards. Without structure, a week with 6-8 materials presents a flat list where a lecture slide deck sits next to a pre-reading PDF and a post-class reflection quiz with no visual or semantic grouping.

Educators designing blended or flipped classrooms think in terms of learning phases: "what do students do before class?", "what happens in class?", "what follows up?". The system needed to reflect this mental model.

## Decision

Add a `category` string field to the `WeeklyMaterial` model with a fixed set of values representing learning phases, plus a general fallback.

### Categories

| Value | Label | Purpose |
|-------|-------|---------|
| `pre_class` | Pre-class | Readings, videos, prep quizzes — before the session |
| `in_class` | In-class | Lectures, tutorials, labs, workshops — during the session |
| `post_class` | Post-class | Reflection activities, practice problems — after the session |
| `resources` | Resources | Reference materials, links, supplementary content — anytime |
| `general` | General | Default for uncategorised materials |

### Storage

```python
# On WeeklyMaterial model
category: str = Field(default="general")
```

A plain string column with application-level validation, not a database enum. This avoids Alembic migrations when adding categories. The frontend defines the canonical list and display order.

### Frontend Display

The `WeekAccordion` component groups materials by category within each week:

1. Uncategorised (general) materials render as a flat list at the top
2. Categorised materials render under labelled section headers (Pre-class, In-class, Post-class, Resources) with colour-coded badges
3. Categories appear in a fixed pedagogical order, not alphabetical
4. The category selector appears in the material creation/edit form

### Bulk Structure Operations

The "Apply Structure to All Weeks" feature (story 3.12) uses categories in two modes:

- **Stubs mode**: copies each material from Week 1 including its category
- **Categories mode**: creates one placeholder material per unique category found in Week 1

This enables rapid scaffolding: set up one week's category structure, then propagate it.

## Consequences

### Positive
- Visual grouping matches how educators think about learning sequences (before → during → after)
- Enables the "apply structure" bulk operation — categories become the structural skeleton
- Categories are optional — uncategorised materials still work fine (default `general`)
- Supports blended, flipped, and traditional teaching models equally
- Simple implementation: one string field, no joins, no additional tables

### Negative
- Fixed category set may not suit all disciplines (e.g. clinical placements might want "pre-placement", "on-site", "debrief") — would need custom categories in future
- No per-unit customisation of category labels — "Pre-class" is always "Pre-class"
- String-based storage means no referential integrity — a typo in a migration or API call could create orphan categories

### Neutral
- Categories are orthogonal to material types (lecture, tutorial, lab, etc.) — a lecture can be pre-class (flipped classroom) or in-class (traditional)
- The `general` default means existing materials and imports are unaffected
- Category is stored on the material, not on a join table — one material belongs to exactly one category

## Alternatives Considered

### Separate Categories Table with Foreign Key
- `MaterialCategory` model with `id`, `unit_id`, `name`, `order_index`, `color`
- Materials get a `category_id` FK
- Rejected: over-engineering for a 5-item fixed list; adds joins; unit-specific categories are a future need, not a current one

### Tags System (Many-to-Many)
- Materials can have multiple tags; categories are just a special tag type
- Rejected: materials belong to exactly one learning phase — "pre-class AND in-class" doesn't make pedagogical sense; many-to-many adds complexity without benefit

### Database Enum
- PostgreSQL `ENUM` type or SQLAlchemy `Enum` column
- Rejected: requires Alembic migration to add a new category; SQLite (used in development and desktop app) handles enums poorly; string column with app-level validation is simpler

### No Categories — Use Material Type Instead
- Rely on types (lecture, reading, quiz) to imply timing
- Rejected: type and timing are independent dimensions — a reading can be pre-class prep or an in-class reference; a quiz can be a pre-class knowledge check or a post-class assessment

## Implementation Notes

- Model field: `backend/app/models/weekly_material.py` — `category = Column(String, default="general")`
- Schema: `backend/app/schemas/materials.py` — `MaterialBase.category`
- Frontend constants: `frontend/src/components/UnitStructure/WeekAccordion.tsx` — `CATEGORY_ORDER`, `CATEGORY_LABELS`, `CATEGORY_COLORS`
- Frontend types: `frontend/src/types/unitStructure.ts` — `MaterialCategory` enum
- Apply structure: `backend/app/services/materials_service.py` — `apply_structure()`, `_create_stubs()`, `_create_category_placeholders()`

## References

- [ADR-018: Workflow Flexibility Philosophy](018-workflow-flexibility-philosophy.md) — categories are optional, not enforced
- [ADR-022: Content Type System Evolution](022-content-type-system-evolution.md) — material types are a separate dimension
- `backend/app/models/weekly_material.py`
- `frontend/src/components/UnitStructure/WeekAccordion.tsx`
