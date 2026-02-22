# 29. Accreditation Framework Mappings (AoL, Graduate Capabilities, SDGs)

Date: 2026-02-20

## Status

Accepted

## Context

University units don't exist in isolation — they must demonstrate alignment with multiple institutional and external quality frameworks. Australian lecturers are required to map their content against these frameworks for accreditation reviews, program-level reporting, and quality assurance.

The three frameworks most commonly required are:

1. **AACSB Assurance of Learning (AoL)** — International business school accreditation. Requires mapping learning outcomes to program-level competencies and demonstrating that assessments measure those competencies.

2. **Graduate Capabilities** — University-specific frameworks defining the attributes all graduates should possess (e.g., "critical thinking", "ethical practice", "communication skills"). Every unit must show which graduate capabilities it develops.

3. **UN Sustainable Development Goals (SDGs)** — Increasingly required by universities to demonstrate how curriculum contributes to the 17 SDGs. Used in sustainability reporting and institutional rankings.

Without tool support, lecturers track these mappings in spreadsheets — disconnected from the actual learning outcomes and assessments they describe. When accreditation reviews arrive, assembling the evidence is time-consuming and error-prone.

## Decision

Build **accreditation framework mappings into the Unit Structure**, allowing lecturers to map their learning outcomes and assessments against all three frameworks directly in the tool.

### Architecture

```
Unit
├── Learning Outcomes (ULOs)
│   ├── → Graduate Capabilities mapping
│   ├── → AoL competency mapping
│   └── → SDG alignment
├── Assessments
│   └── → AoL measurement mapping
└── Weekly Schedule
    └── → Topics aligned to outcomes
```

### Data Model

Each mapping is stored as a JSON structure on the unit's structure data, persisted via the existing unit structure API (`/api/units/{id}/structure`).

```typescript
interface UnitStructure {
  learningOutcomes: ULO[];
  assessments: Assessment[];
  weeklySchedule: Week[];
  graduateCapabilities: CapabilityMapping[];  // ULO → capability
  aolMappings: AoLMapping[];                  // ULO → AoL competency
  sdgMappings: SDGMapping[];                  // Unit → SDG goals
}
```

### UI Integration

Each mapping has a dedicated panel in the Unit Structure dashboard:

| Panel | Purpose | Interaction |
|-------|---------|-------------|
| **Graduate Capabilities** | Map ULOs to institutional capabilities | Checkbox matrix (ULO x Capability) |
| **AoL Mapping** | Map ULOs to AACSB competencies and assessments to measurement methods | Checkbox matrix + assessment linkage |
| **SDG Mapping** | Tag unit with relevant SDGs | Goal selector with relevance notes |
| **Learning Outcome Hierarchy** | Visual map showing all mappings for each ULO | Read-only summary view |

### Extensibility

The mapping system is generic: each framework is a list of items (capabilities, competencies, goals) that can be linked to ULOs or assessments. Adding a new framework (e.g., TEQSA standards, AQF levels) requires:

1. A constants file with the framework items
2. A mapping panel component
3. A field on the unit structure schema

No backend changes needed — the structure API stores arbitrary JSON.

## Consequences

### Positive

- **Single source of truth** — Mappings live alongside the outcomes they describe, not in separate spreadsheets
- **Accreditation-ready** — Lecturers can generate mapping reports directly from the tool
- **Visibility** — The Learning Outcome Hierarchy view shows gaps (unmapped outcomes) at a glance
- **Reusable pattern** — The checkbox matrix pattern works for any framework

### Negative

- **Opinionated framework selection** — We've built in AACSB, Graduate Capabilities, and SDGs specifically. Universities using different frameworks (EQUIS, AMBA, TEQSA) would need custom additions.
- **UI density** — The Unit Structure dashboard now has multiple mapping panels, which can feel overwhelming for lecturers who only need basic content creation
- **Australian/business school bias** — AoL is primarily relevant to business schools. Other disciplines may not need it.

### Neutral

- **Optional usage** — All mapping panels are available but none are required. Empty mappings don't affect content creation or export.
- **No validation** — The tool doesn't enforce that every ULO must be mapped. It's a documentation aid, not a compliance gate.

## Alternatives Considered

### Spreadsheet export only

- Don't build mapping UI; instead export ULOs to a spreadsheet template for manual mapping
- **Rejected**: Defeats the purpose. Lecturers already have spreadsheets — the value is integrating mappings into the tool.

### Plugin-based framework system

- Each framework as a plugin (per ADR-003) with its own schema and UI
- **Rejected for now**: Over-engineered for three frameworks. The current approach is simpler and can be refactored into plugins if more frameworks are needed.

### Dedicated accreditation module (separate from Unit Structure)

- A separate "Accreditation" section in the navigation
- **Rejected**: Mappings are meaningful only in the context of a unit's outcomes and assessments. Separating them creates a disconnected experience.

## References

- [ADR-020: AI-Optional User Empowerment](020-ai-optional-user-empowerment.md) — Mappings are manual, not AI-generated
- [ADR-018: Workflow Flexibility](018-workflow-flexibility-philosophy.md) — Mapping panels are optional, not enforced
- [AACSB Assurance of Learning Standards](https://www.aacsb.edu/accreditation/standards)
- [UN Sustainable Development Goals](https://sdgs.un.org/goals)
- Relevant commits: `9c0cf995`, `72a301e8`, `0e2e71e5`, `2f5a97a8`, `f1b0d0bd`
