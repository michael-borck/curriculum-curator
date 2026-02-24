# ADR-057: UDL Inclusivity Scoring Model

Date: 2026-02-24

## Status

Accepted

## Context

ADR-055 established Universal Design for Learning (UDL) as the cross-cutting accessibility lens in the app's five-layer pedagogical framework. It defined *where* UDL fits but not *how* to measure it. We need a concrete scoring model that:

1. Quantifies how well a unit's design supports diverse learners
2. Provides per-week and per-unit scores so users can identify weak spots
3. Generates actionable improvement suggestions
4. Contextualises scores by target audience level (elementary through postgraduate)

The scoring must be **rule-based** (no LLM calls) so it runs instantly, is deterministic, and costs nothing per invocation. It should use data already in the system (weekly materials, assessments) rather than requiring users to fill in new fields.

### UDL background

CAST's Universal Design for Learning framework has three principles:

1. **Multiple Means of Representation** — present information in varied formats
2. **Multiple Means of Engagement** — motivate through choice and relevance
3. **Multiple Means of Action & Expression** — let learners demonstrate knowledge in different ways

We add a fourth practical dimension, **Content Accessibility**, covering readability and WCAG compliance — a measurable proxy for how accessible the actual content is.

## Decision

### Four scoring dimensions (0-100 each)

| Dimension | UDL Principle | Data source | Algorithm |
|-----------|--------------|-------------|-----------|
| Representation Diversity | Principle 1 | `WeeklyMaterial.category` | Shannon diversity index on material categories, +15 bonus for mixed description lengths (short + long) |
| Engagement Variety | Principle 2 | `WeeklyMaterial.type` | Shannon diversity on session formats, weighted by interactivity ratio (workshops/labs/seminars score higher than lectures); purely passive weeks penalised at 50% |
| Action & Expression | Principle 3 | `Assessment.category`, `group_work`, `submission_type` | Shannon diversity on assessment categories, +15 for group/individual mix, +5 per distinct submission type (capped at 10) |
| Content Accessibility | Practical | `WeeklyMaterial.description` | 50/50 blend of Flesch-Kincaid readability score (contextualised by target level) and WCAG accessibility score |

### Shannon diversity index

Used for Representation, Engagement, and Expression dimensions. Normalised to 0-100:

```
H = -SUM(p_i * ln(p_i))   for each category proportion p_i
evenness = H / ln(num_categories)
score = evenness * 100
```

Single-category items with multiple entries score 20 (acknowledges content exists but no diversity). Empty weeks score 0.

### Per-week vs per-unit scoring

- **Per-week**: Each dimension scored independently for each week. Weeks without content get 0 for Representation/Engagement and neutral 50 for Expression/Accessibility (not penalised for absence of assessments in non-assessment weeks).
- **Per-unit**: Weighted average of content-bearing weeks only. Plus a unit-level assessment format diversity score (Shannon on all assessment categories).

### Score presentation

| Score | Stars | Grade |
|-------|-------|-------|
| 95+ | 5.0 | A |
| 90-94 | 4.5 | A |
| 85-89 | 4.0 | B |
| 80-84 | 3.5 | B |
| 70-79 | 3.0 | C |
| 55-69 | 2.5 | D |
| 40-54 | 2.0 | D |
| 20-39 | 1.0 | F |
| 0-19 | 0.0 | F |

### Target audience levels

Readability expectations vary by audience. The `target_level` parameter (elementary, middle_school, high_school, university, postgraduate) adjusts the Flesch-Kincaid ideal range:

- **University**: Flesch 30-60 is ideal (scores 90); 20-30 or 60-70 scores 70; extremes penalised
- **Other levels**: Direct Flesch score mapping (higher = easier to read = better for younger audiences)

### Suggestion engine

Rule-based suggestions fire when:

- **Representation**: A week has materials in only one category
- **Engagement**: A week has no interactive session formats (no workshop, lab, seminar, or tutorial)
- **Expression**: All assessments use the same category; no group work mix; single submission type across 3+ assessments
- **Accessibility**: Material reads at 3+ grade levels above the target audience

Each suggestion includes dimension, priority (high/medium/low), issue description, and actionable advice.

### Feature toggles

Per ADR-052, users can toggle visibility of each UDL dimension independently via Unit Settings. The toggles control frontend display only — scores are always calculated server-side so toggling a dimension back on shows data immediately.

## Consequences

### Positive

- Instant feedback — no API costs, deterministic, < 100ms for a 12-week unit
- Actionable — per-week granularity shows exactly which weeks need attention
- Evidence-based — Shannon diversity is a well-established ecological diversity measure repurposed for curriculum variety
- Contextualised — readability expectations adjust to the audience level

### Negative

- **Proxy measures**: Shannon diversity rewards variety but can't assess *quality* of variety (e.g., 3 mediocre categories score the same as 3 excellent ones)
- **Data-dependent**: Scores are only meaningful when materials and assessments are populated. Empty units score 0/F, which may alarm users who haven't finished entering data yet
- **Readability limitations**: Flesch-Kincaid assumes English prose; non-English content or code-heavy descriptions will produce misleading scores
- **No peer benchmarking**: Scores are absolute, not relative to similar units. A 70 has no context of "how good is that compared to other units?"

### Neutral

- Expression dimension gives 50 (neutral) to weeks without assessments — this avoids penalising non-assessment weeks but means the dimension is partially invisible for most weeks
- The scoring model will likely need recalibration as we gather real usage data

## Alternatives Considered

### LLM-based scoring

- Use an LLM to evaluate UDL compliance by reading all materials
- Rejected: expensive per invocation, non-deterministic, slow, and hard to explain why a score changed
- We already offer separate "AI Recommendations" via the Quality Dashboard for LLM-powered advice

### Simple checklist scoring

- Binary checks: "Has multiple material types? +1. Has group assessment? +1."
- Rejected: too coarse. Shannon diversity captures the *degree* of variety, not just its presence. A week with 2 categories vs 5 categories should score differently.

### Weighted dimensions

- Give some dimensions higher weight (e.g., Accessibility 40%, others 20% each)
- Rejected for now: equal weighting is simpler and we don't have evidence that one dimension matters more. Can revisit with user feedback.

## Implementation Notes

- Service: `backend/app/services/udl_service.py` (singleton `udl_service`)
- Schemas: `backend/app/schemas/udl.py`
- API: 3 endpoints in `backend/app/api/routes/analytics.py`
  - `GET /analytics/units/{unit_id}/udl-score` — unit-level
  - `GET /analytics/units/{unit_id}/udl-weekly` — per-week breakdown
  - `GET /analytics/units/{unit_id}/udl-suggestions` — improvement suggestions
- Frontend: `UDLDashboard.tsx` renders scores, stars, and suggestions
- Reuses existing `ReadabilityValidator` and `AccessibilityValidator` plugins

## References

- [CAST UDL Guidelines](https://udlguidelines.cast.org/) — the framework this scoring model implements
- [Shannon Diversity Index](https://en.wikipedia.org/wiki/Shannon_diversity_index) — the entropy measure used for category diversity
- ADR-055 — Pedagogical Framework and Alignment Architecture (defines where UDL fits)
- ADR-052 — Unit-Level Feature Toggles (controls dimension visibility)
- ADR-053 — Material Content Categories (provides the category taxonomy scored by Representation)
