# 62. Education Sector Profiles

Date: 2026-02-26

## Status

Accepted

## Context

The app was built with Australian higher education assumptions baked in: units, semesters, credit points, AoL/SDG accreditation mappings. The recent "Dashboard → Portfolio" and configurable `unitLabel` work (ADR pending) exposed a deeper issue — the entire UX speaks one dialect of education.

A K-12 teacher creating a Year 10 Maths term plan sees "Unit Code", "Semester", "Credit Points", and "AoL Mapping" — none of which make sense in their world. A corporate trainer building a 2-day onboarding workshop sees the same. They have to mentally translate every label and manually hide irrelevant features via Settings.

Meanwhile, we already ask users almost nothing about themselves at registration — just name, email, password. We then default everyone to the same university-centric experience.

### The problem in a table

| Concept | K-12 | TAFE / VET | University | Corporate / PD |
|---------|------|------------|------------|----------------|
| What they build | Subject / Course | Unit of Competency | Unit | Program / Workshop |
| Time divisions | Lessons, Terms | Weeks | Weeks | Sessions, Days |
| Duration | 10 weeks (term) | 12–18 weeks | 12–13 weeks | 1–5 days |
| Credits | N/A | Credit points | Credit points | CPD hours (optional) |
| Accreditation | Curriculum standards | Training packages | AoL, SDG, grad caps | N/A or industry certs |
| Code format | "Year 10 Maths" | "ICTPRG302" | "COMP1001" | Free-form |
| Semester concept | Term 1–4 | Semester | Semester 1/2 | N/A |

### What we want

A single choice during onboarding that configures sensible defaults for each sector, so the app feels native to each user's context — without limiting what they can do.

## Decision

Add an **education sector** field to the User model, selectable during a post-registration onboarding step. Each sector maps to a profile of defaults that configure the new-unit experience and feature visibility.

### Sector definitions

| Sector ID | Label | Description |
|-----------|-------|-------------|
| `k12` | K-12 Education | Primary and secondary schools |
| `vet` | Vocational / TAFE | Vocational education and training, community colleges |
| `higher_ed` | Higher Education | Universities, postgraduate programs |
| `corporate` | Corporate / Professional | Workplace training, professional development, workshops |
| `other` | Other | Custom defaults for non-standard contexts |

### What each sector configures

Each sector provides a **default profile** — a bag of defaults applied when creating new units or viewing the UI. Users can always override per-unit.

```
SectorProfile {
  unitLabel: string           // "Subject", "Unit", "Program", etc.
  topicLabel: string          // "Lesson", "Week", "Session", etc.
  defaultDuration: number     // 10, 12, 5, etc.
  showCreditPoints: boolean   // Whether credit points field appears
  showSemester: boolean       // Whether semester picker appears
  showAccreditation: boolean  // AoL, SDG, grad capabilities panels
  codeLabel: string           // "Subject Code", "Unit Code", "Program Code"
  codePlaceholder: string     // "Year 10 Maths", "ICTPRG302", "CS101"
  structurePresets: string[]  // Which presets to show (subset of all presets)
}
```

### Where the sector is set

1. **Post-registration onboarding** — a single "Welcome" step after email verification asks "What best describes your teaching context?" with the 5 sector cards. This is NOT part of the registration form itself (keeps registration minimal).
2. **Settings → Profile tab** — can be changed any time.
3. **Stored on User model** as `education_sector` (String, nullable, default null).
4. **Null means "not yet chosen"** — triggers the onboarding prompt on first login.

### How defaults flow

```
User.education_sector
  → SECTOR_PROFILES[sector]          (static lookup, no DB)
  → New Unit form defaults            (unitLabel, topicLabel, duration, presets)
  → Feature visibility defaults        (credit points, accreditation, semester)
  → UI copy and placeholders           (code label, empty states)
```

The sector profile is a **frontend concern** — a static map from sector ID to defaults. The backend only stores the sector string; it doesn't need to know what defaults it implies.

### Onboarding flow

```
Register → Verify Email → Login → [First login: Welcome modal]
                                         │
                                    "What best describes
                                     your teaching context?"
                                         │
                                    ┌─────┼─────┐─────┐─────┐
                                   K-12  VET  Uni  Corp  Other
                                         │
                                    PATCH /auth/profile
                                    { educationSector: "k12" }
                                         │
                                    → Dashboard with sector-appropriate defaults
```

## Consequences

### Positive

- App feels native to K-12 teachers, corporate trainers, VET instructors — not just university lecturers
- Single choice replaces dozens of manual configuration decisions
- Existing users unaffected (null sector = current behaviour, equivalent to `higher_ed`)
- Per-unit overrides preserved — a university lecturer can still create a workshop-style unit
- Lightweight implementation — sector profiles are a static frontend map, not a complex backend system
- Opens the door for sector-specific prompt templates and AI context

### Negative

- One more step in the onboarding flow (mitigated: it's optional, skippable, and only shown once)
- Sector boundaries are fuzzy (a TAFE teacher might also do corporate training) — mitigated by allowing change in Settings and per-unit overrides
- Need to maintain sector profiles as the app evolves (new features need sector-aware defaults)

### Neutral

- Existing `unitLabel` and `topicLabel` on Unit model remain — they store the actual per-unit values, regardless of sector defaults
- The `STRUCTURE_PRESETS` array in DashboardPage becomes sector-filtered rather than one-size-fits-all
- No migration needed for existing units — they keep their current values

## Alternatives Considered

### Per-unit "context" instead of user-level sector

- User picks context each time they create a unit
- Rejected: Too much friction. The sector is a user attribute, not a unit attribute. A K-12 teacher creates K-12 subjects 95% of the time.

### Detailed onboarding wizard (sector + subject domain + experience level + class size)

- Captures more context upfront
- Rejected: Over-engineered for current stage. Sector alone covers 80% of the value. Can always add more profile fields later.

### Infer sector from institution name or email domain

- Auto-detect whether user is K-12, uni, corporate
- Rejected: Unreliable, privacy concerns, and many users won't fill in institution.

## Implementation Notes

- Backend: Add `education_sector` column to User model + schema. DB reset (no production users).
- Frontend: Add `SECTOR_PROFILES` constant map. Add `WelcomeOnboarding` modal component. Modify `DashboardPage` to read sector defaults. Modify `AppLayout` to trigger onboarding on first login.
- The sector profile does NOT replace per-unit `unitLabel`/`topicLabel` — those are the actual stored values. The sector just provides smarter defaults when creating new units.
- Consider seeding sector-specific prompt templates (ADR-058) in a future iteration.

## References

- ADR-052: Unit-Level Feature Toggles via Metadata
- ADR-058: Prompt Template Library
- `unit_label` field added to Unit model (2026-02-26)
