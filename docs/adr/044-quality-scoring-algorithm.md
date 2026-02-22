# 44. Unit Quality Scoring Algorithm

Date: 2026-02-22

## Status

Accepted

## Context

Users need actionable feedback on unit quality — not just "is this complete?" but "is this well-structured?" The system should surface gaps (missing ULO alignment, unbalanced workload, assessment clustering) without requiring manual review. The score drives the quality panel on the unit page and the A–F grade shown in the dashboard.

The algorithm must work with incomplete units (a unit with only 3 weeks of content should get a proportional score, not zero) and produce stable, explainable results.

## Decision

Implement a six-dimension weighted scoring system where each dimension captures a different aspect of unit quality, using domain-appropriate algorithms.

### Dimensions and Weights

| Dimension | Weight | Algorithm |
|-----------|--------|-----------|
| Completeness | 0.20 | 50% week coverage + 50% materials with descriptions |
| Content Quality | 0.15 | Average of per-material quality scores (from plugin validators) |
| ULO Alignment | 0.25 | % of ULOs with both material and assessment links |
| Workload Balance | 0.10 | Inverted coefficient of variation across weekly durations |
| Material Diversity | 0.10 | Shannon entropy (Pielou's evenness index) of material types |
| Assessment Distribution | 0.20 | Spread score based on gap deviation from ideal + range coverage |

### Rating Methods

Three methods convert the overall score (0–100) to a user-facing rating:

1. **Weighted average** (default): `sum(dimension_score * weight)` — straightforward composite
2. **Lowest dimension**: `min(dimension_scores)` — "only as strong as the weakest link"
3. **Threshold-based**: count of thresholds (20/40/60/80/90) that ALL dimensions exceed — rewards consistency

### Output Scales

- **Stars:** 0–5 via stepped thresholds (95→5.0, 90→4.5, 85→4.0, 80→3.5, 70→3.0, 55→2.5, 40→2.0, 20→1.0)
- **Letter grade:** 90→A, 80→B, 70→C, 60→D, <60→F

## Consequences

### Positive
- Multi-dimensional scoring gives specific, actionable feedback ("your workload is unbalanced" vs "score is low")
- Statistically grounded algorithms (Shannon entropy, coefficient of variation) handle edge cases well
- Graceful degradation — incomplete units get partial scores rather than zero
- Three rating methods let different users optimise for different goals

### Negative
- Dimension weights are somewhat arbitrary — 0.25 for ULO alignment vs 0.10 for diversity is a pedagogical judgement that may not suit all disciplines
- Content Quality dimension depends on plugin validators populating `quality_score`, which may not always run
- The algorithm is opaque to users — they see a grade but not the maths behind it

### Neutral
- Insufficient data produces sentinel values (e.g. workload balance returns 50.0 with fewer than 2 weeks) rather than failing
- Per-ULO alignment saturates at 3 materials and 2 assessments — beyond that, more links don't increase the score

## Alternatives Considered

### Simple Checklist Scoring
- Award points for each completed item (has ULOs: +10, has assessments: +10, etc.)
- Rejected: doesn't capture quality or balance — a unit with 12 lectures and no tutorials scores the same as a diverse one

### AI-Based Quality Assessment
- Send the unit to an LLM for qualitative evaluation
- Rejected: expensive per evaluation, non-deterministic, slow for dashboard display; LLM recommendations are available separately via `get_recommendations()`

### Single Metric (e.g. Completeness Only)
- Track percentage of fields filled in
- Rejected: completeness without alignment or balance is misleading — a fully filled but poorly structured unit would score 100%

## Implementation Notes

- **Shannon diversity:** `evenness = entropy / log(num_types)` scaled to 0–100; single type with multiple items gets a baseline score of 20
- **Assessment spread:** combines gap regularity (`|mean_gap - ideal_gap| / ideal_gap`) with range coverage (`(last - first) / total_weeks`), 50/50 weighted
- **Workload balance:** `score = max(0, min(100, 100 - CV * 100))` where CV = std_dev / mean of non-zero weekly durations
- **Per-ULO alignment:** `material_score = min(links/3, 1) * 50` + `assessment_score = min(links/2, 1) * 50`
- Weights are configurable via `rating_config` parameter but defaults are hardcoded in `DEFAULT_QUALITY_WEIGHTS`

## References

- `backend/app/services/analytics_service.py` — `calculate_quality_score()`, `_calculate_balance_score()`, `_calculate_shannon_diversity()`, `_calculate_spread_score()`
- [ADR-003: Plugin Architecture](003-plugin-architecture.md) — content quality plugins that feed the Content Quality dimension
