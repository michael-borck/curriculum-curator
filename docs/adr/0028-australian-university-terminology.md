# 28. Australian University Terminology (Course-to-Unit Refactoring)

Date: 2026-02-20

## Status

Accepted

## Context

The application was originally built using US academic terminology, where "course" means an individual subject (e.g., "Programming 101"). In Australian universities — the primary target audience — "course" means a degree program (e.g., "Bachelor of Computer Science"), and the individual subject is called a "unit".

This caused persistent confusion:

1. **Domain model mismatch** — The `Course` model represented what Australian lecturers call a "Unit", leading to confusion in user-facing language, API naming, and internal discussions
2. **Scope ambiguity** — "Course management" could mean managing degree programs (not our scope) or managing individual subjects (our actual scope)
3. **User testing feedback** — Australian lecturers found the terminology jarring and confusing

The terminology difference is not cosmetic — it affects how users understand the application's purpose and scope.

### Terminology Mapping

| Concept | USA | Australia |
|---------|-----|-----------|
| Degree program | Program | Course |
| Individual subject | Course | **Unit** |
| Single class session | Class | Class |

## Decision

Adopt **Australian university terminology** throughout the entire stack. The core entity is a **Unit** (an individual subject that runs for one semester).

### Scope Clarification

This application manages **Units** (individual subjects), NOT degree programs (Courses). A unit:
- Runs for one semester (12-13 weeks)
- Has credit points (typically 6-25)
- Contains learning outcomes, materials, assessments
- Is taught by one or more lecturers

### Implementation

The refactoring touched every layer:

| Layer | Before | After |
|-------|--------|-------|
| Database model | `Course` | `Unit` |
| Database table | `courses` | `units` |
| API endpoints | `/api/courses` | `/api/units` |
| Pydantic schemas | `CourseCreate`, `CourseResponse` | `UnitCreate`, `UnitResponse` |
| Frontend types | `Course` interface | `Unit` interface |
| Frontend components | `CourseManager` | `UnitManager` |
| UI labels | "Course", "Courses" | "Unit", "Units" |
| URL routes | `/courses/:id` | `/units/:id` |

### Backwards Compatibility

A `Course` type alias exists in the frontend (`export type Course = Unit`) and legacy `/api/courses` endpoints exist in the backend. Both are deprecated and will be removed (no production users to migrate).

## Consequences

### Positive

- **Domain accuracy** — The model matches how Australian lecturers actually think and speak about their work
- **Scope clarity** — "Unit management" is unambiguous; "course management" was not
- **User trust** — Lecturers immediately understand what the tool manages when they see "Units"
- **Consistent mental model** — Internal discussions, documentation, and code all use the same term

### Negative

- **One-time refactoring cost** — Touching every layer was a significant effort (commits `3d9f3412`, `016952e7`, `ca63096c`, `be72a6c4`)
- **International confusion** — Developers from US/UK backgrounds need to learn the Australian convention (documented in CLAUDE.md)
- **Legacy references** — Some comments, variable names, or documentation may still say "course" when meaning "unit"

### Neutral

- **CLAUDE.md documentation** — The terminology mapping is prominently documented in the project's AI coding instructions to prevent regression
- **No database migration needed** — The project has no production users, so the table rename was a clean slate operation

## Alternatives Considered

### Keep US terminology ("Course")

- Use "Course" throughout, add a glossary for Australian users
- **Rejected**: The primary audience is Australian lecturers. Using foreign terminology undermines trust and clarity.

### Use generic terminology ("Subject")

- Avoid both "course" and "unit" in favour of a neutral term
- **Rejected**: "Subject" is used in some Australian contexts but "unit" is more widely understood in the university sector. Using generic terms feels clinical and disconnected from the domain.

### Support both terminologies (locale-based)

- Let users choose their preferred terminology via a setting
- **Rejected**: Unnecessary complexity. The codebase should have one canonical term. Users in other regions can adapt to "unit" (it's self-explanatory), but the code cannot maintain two parallel terminologies without bugs.

## References

- [CLAUDE.md: Terminology section](../../CLAUDE.md) — Canonical terminology documentation
- Relevant commits: `3d9f3412`, `016952e7`, `ca63096c`, `be72a6c4`, `7c0cdc78`
