# 60. Analytics Snapshot Storage

Date: 2026-02-25

## Status

Accepted

## Context

ADR-044 and ADR-057 established quality scoring and UDL scoring as rule-based calculations that run on demand. Users want to track how their unit improves over time — comparing this semester's quality score to last month's, or seeing whether recent edits improved UDL inclusivity.

The obvious first approach was to **recalculate historical scores from git history**: since all content lives in git-backed repos (ADR-013), we could check out prior commits and re-run the scoring algorithms against that state. This would require zero additional storage — the history is already there.

However, this approach has significant drawbacks:

1. **Performance**: Checking out old commits, loading content into memory, and running six quality dimensions + four UDL dimensions per historical point is expensive. A "show me the last 30 days" chart would require 30 full recalculations.
2. **Score algorithm drift**: When we improve the scoring algorithm (adjust weights, add dimensions), old scores recalculated with the new algorithm wouldn't match what the user saw at the time. The "improvement" a user sees might be an algorithm change, not a real content improvement.
3. **Coupling to git**: Not all state lives in git. Assessment metadata, ULO mappings, and material quality scores are in SQLite. Reconstructing a full scoring context from a historical git commit + current DB state would be unreliable.
4. **Complexity**: Implementing time-travel across both git and DB for score reconstruction is disproportionately complex for the value delivered.

## Decision

Persist scores as **point-in-time snapshots** in an `analytics_snapshots` table. Each snapshot captures the full scoring output (quality + UDL overall scores, star ratings, grades, sub-scores) plus contextual stats (material count, assessment count, ULO count, weeks with content).

### Snapshot types

- **Auto-snapshots**: Created transparently when a user views quality or UDL scores, at most once per unit per day. This captures scores as a side-effect of normal usage with no extra user effort.
- **Manual snapshots**: User-initiated with an optional label (e.g., "Pre-moderation review", "End of Semester 1"). Never auto-deleted.

### Storage model

```
analytics_snapshots
├── id (UUID PK)
├── unit_id (FK → units)
├── label (nullable, for manual snapshots)
├── is_auto (bool)
├── quality_overall, quality_star_rating, quality_grade
├── quality_sub_scores (JSON text — all 6 dimensions)
├── udl_overall, udl_star_rating, udl_grade
├── udl_sub_scores (JSON text — all 4 dimensions)
├── material_count, assessment_count, ulo_count, weeks_with_content
├── created_by_id (FK → users, nullable)
└── created_at
```

Sub-scores are stored as JSON text rather than separate columns because the set of dimensions may evolve (ADR-044 has 6 quality dimensions, ADR-057 has 4 UDL dimensions, both could grow). JSON keeps the schema stable while dimensions change.

### Comparison

The service supports comparing any two snapshots, or a snapshot against live (current) scores. Deltas are calculated per-dimension, allowing users to see exactly which aspects improved or regressed.

### Auto-snapshot trigger

The `maybe_auto_snapshot()` method is called as a side-effect in the `GET /quality-score` and `GET /udl-score` endpoints. It checks whether an auto-snapshot already exists for today; if not, it creates one. This means scores are captured naturally as users work, without a background scheduler.

## Consequences

### Positive
- **O(1) historical lookups**: Displaying 30 days of history is 30 row reads, not 30 full recalculations
- **Score fidelity**: Snapshots capture what the user actually saw at the time, immune to algorithm changes
- **Simple comparison**: Delta calculation is subtraction, not time-travel reconstruction
- **No infrastructure**: No cron jobs, no background workers — auto-snapshots piggyback on existing API calls
- **Low coupling**: Snapshots are self-contained rows; no dependency on git state or DB reconstruction

### Negative
- **Storage growth**: Each snapshot is ~1KB. A user with 10 units generating daily auto-snapshots accumulates ~3.6MB/year — negligible, but needs eventual cleanup policy
- **Stale if unused**: If a user doesn't view scores for a month, there are no auto-snapshots for that period. Scores are only captured when viewed.
- **Algorithm changes invisible**: If we improve the scoring algorithm, old snapshots won't retroactively reflect the improvement. This is a feature (fidelity) but could confuse users who see a score jump after an update.

### Neutral
- Sub-score JSON needs parsing on read, but this is trivial and avoids schema migrations when dimensions change
- Manual snapshots are unlimited; auto-snapshot cleanup policy is a future concern (tracked in IDEAS.md)

## Alternatives Considered

### Recalculate from git history
- Check out historical commits, reconstruct full unit state, re-run scoring
- Rejected: too slow for charts, scores drift with algorithm changes, incomplete without DB state, high implementation complexity

### Background scheduler (cron-based snapshots)
- A scheduled job creates snapshots for all units nightly
- Rejected: requires infrastructure (celery/cron), snapshots units nobody is working on (wasted writes), and the app currently has no background task system

### Store only deltas (event sourcing)
- Record individual score-affecting events and replay to reconstruct history
- Rejected: massive over-engineering for the use case; full snapshots are small and self-contained

## Implementation Notes

- **Files**: `models/analytics_snapshot.py`, `services/snapshot_service.py`, `SnapshotCompare.tsx`
- **API**: Snapshot CRUD and comparison endpoints live under `/analytics/units/{unit_id}/snapshots`
- **Alembic migration**: Required to create the `analytics_snapshots` table
- **Cleanup policy**: Tracked as a future idea in `docs/IDEAS.md` — thin auto-snapshots over time (daily → weekly → monthly)

## References

- [ADR-044: Unit Quality Scoring Algorithm](044-quality-scoring-algorithm.md) — quality score dimensions
- [ADR-057: UDL Inclusivity Scoring Model](057-udl-inclusivity-scoring-model.md) — UDL score dimensions
- [ADR-013: Git-Backed Content Storage](013-git-backed-content-storage.md) — the alternative history source considered and rejected
