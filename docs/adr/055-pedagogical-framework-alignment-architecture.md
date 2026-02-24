# ADR-055: Pedagogical Framework and Alignment Architecture

Date: 2026-02-24

## Status

Accepted

## Context

Curriculum Curator has organically grown a rich set of pedagogical features across 10+ ADRs (004, 022, 029, 032, 036, 040, 044, 052, 053, 054). Each decision solved a specific problem well, but no single document explains the **coherent pedagogical framework** that ties them together — the *why* behind the data model.

This matters for three reasons:

1. **For users**: Academics range from pedagogical experts to first-time unit coordinators. The app should educate, not just implement. Without a unifying frame, the tool feels like a bag of disconnected features.
2. **For development**: Without a clear framework, new features risk duplicating or contradicting existing concepts. Developers need to know where a new idea fits.
3. **For positioning**: The app's differentiator is "curriculum design tool that produces content" (POSITIONING.md). This ADR makes explicit the educational theory that underpins that claim.

### Terminology note

This document uses **learning modalities** (visual, auditory, read/write, kinaesthetic) rather than "learning styles". The "learning styles" hypothesis (e.g. VARK as a fixed trait) has been [widely debunked](https://doi.org/10.1111/jopy.12610). Modern evidence-based practice uses **modalities** — varied presentation modes that benefit *all* learners, not matched to individual preference. This distinction matters: we design for **multimodal delivery**, not personalised style matching.

## Decision

We adopt a **five-layer pedagogical framework** that the application models explicitly. Each layer has a clear scope, connects to adjacent layers, and maps to specific database models and UI surfaces.

### The Five Layers

```
┌─────────────────────────────────────────────────────────┐
│  Layer 5: ACCREDITATION & EXTERNAL ALIGNMENT            │
│  "Does this unit meet institutional/professional        │
│   requirements?"                                        │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐      │
│  │   PLO   │ │   GC    │ │   AoL   │ │   SDG   │      │
│  │(Program)│ │(Instit.)│ │(AACSB)  │ │  (UN)   │      │
│  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘      │
│       └──────┬─────┘          │            │            │
│              ▼                ▼            ▼            │
├─────────────────────────────────────────────────────────┤
│  Layer 4: UNIT LEARNING OUTCOMES (ULOs)                 │
│  "What will students be able to DO after this unit?"    │
│  ┌──────────────────────────────────────────┐           │
│  │  ULO + Bloom's Level + Action Verb       │           │
│  │  e.g. "Analyse (L4) competing design     │           │
│  │        patterns for distributed systems"  │           │
│  └──────────────┬───────────────────────────┘           │
│                 │ constructive alignment                 │
│           ┌─────┴─────┐                                 │
│           ▼           ▼                                 │
├─────────────────────────────────────────────────────────┤
│  Layer 3: ASSESSMENT DESIGN                             │
│  "How do we MEASURE that students achieved the ULOs?"   │
│  ┌────────────┐  ┌─────────────┐  ┌──────────────┐     │
│  │ Formative  │  │  Summative  │  │   Rubric     │     │
│  │ (quiz,     │  │  (exam,     │  │   Criteria   │     │
│  │  discuss.) │  │   project)  │  │              │     │
│  └────────────┘  └─────────────┘  └──────────────┘     │
│                                                         │
├─────────────────────────────────────────────────────────┤
│  Layer 2: TEACHING & LEARNING ACTIVITIES                │
│  "How do we TEACH so students can achieve the ULOs?"    │
│  ┌───────────────────────────────────────────────┐      │
│  │  Session Format  ×  Content Type  ×  Phase    │      │
│  │  (lecture, lab)    (slides, quiz)   (pre/in/  │      │
│  │                                      post)    │      │
│  │  + Local Learning Outcomes (per material)     │      │
│  │  + Pedagogy type (inquiry, flipped, etc.)     │      │
│  └───────────────────────────────────────────────┘      │
│                                                         │
├─────────────────────────────────────────────────────────┤
│  Layer 1: UNIVERSAL DESIGN FOR LEARNING (UDL)           │
│  "How do we make this ACCESSIBLE to all learners?"      │
│  ┌─────────────┐ ┌──────────────┐ ┌──────────────┐     │
│  │  Multiple   │ │   Multiple   │ │   Multiple   │     │
│  │  Means of   │ │   Means of   │ │   Means of   │     │
│  │ Engagement  │ │Representation│ │Action/Express.│    │
│  └─────────────┘ └──────────────┘ └──────────────┘     │
└─────────────────────────────────────────────────────────┘
```

### Layer 1: Universal Design for Learning (UDL)

UDL (CAST, 2018) is a cross-cutting concern, not a checkbox. The app supports UDL through:

| UDL Principle | How the app supports it | Where |
|---|---|---|
| **Multiple Means of Engagement** | Varied session formats (lecture, lab, workshop, seminar); pedagogy types (inquiry, game-based, experiential); pre/in/post-class phases | SessionFormat enum, MaterialCategory, PedagogyType |
| **Multiple Means of Representation** | Multiple content types (slides, notes, video, reading, handout); multimodal delivery within a single week | ContentType enum, weekly material structure |
| **Multiple Means of Action & Expression** | Varied assessment types (quiz, project, discussion, portfolio, presentation); formative + summative mix | Assessment model, AssessmentCategory |

UDL is not a separate feature to toggle — it's a **design lens** the app encourages by making it easy to create varied materials and assessments. The in-app guide (see Consequences) will make this explicit.

### Layer 2: Teaching & Learning Activities

Three orthogonal dimensions (established in the content/material type unification):

| Dimension | Describes | Model | Values |
|---|---|---|---|
| **SessionFormat** | What kind of teaching session | `WeeklyMaterial.type` | lecture, tutorial, lab, workshop, seminar, independent, other |
| **ContentType** | What artifact you're creating | `Content.content_type` | slides, notes, worksheet, handout, quiz, case_study, reading, video, discussion, activity, assignment, resource |
| **MaterialCategory** | When in the learning cycle | `WeeklyMaterial.category` | pre_class, in_class, post_class, resources, general |

**Pedagogy type** (on Unit) influences *how* activities are designed — a flipped classroom puts content delivery in pre_class and active learning in in_class; a traditional approach puts lecture in in_class and practice in post_class.

**Local Learning Outcomes** (on WeeklyMaterial) break ULOs down to session-level granularity — "by the end of this lab, students will be able to..."

### Layer 3: Assessment Design

Assessments connect to ULOs via many-to-many mapping. Every summative assessment should assess at least one ULO; every ULO should be assessed by at least one summative assessment. This is **constructive alignment** (Biggs & Tang, 2011).

The quality scoring algorithm (ADR-044) checks this alignment and flags gaps.

Assessment types serve different purposes:

| Type | Purpose | Examples |
|---|---|---|
| **Formative** | Learning feedback, low/no stakes | Quiz, discussion, peer review, draft submission |
| **Summative** | Grade contribution, measures achievement | Exam, project, portfolio, presentation |

### Layer 4: Unit Learning Outcomes (ULOs)

ULOs are the anchor point. They:
- Are written using **Bloom's taxonomy** action verbs (remember → create)
- Map upward to accreditation frameworks (Layer 5)
- Map downward to assessments and materials (Layers 2-3)
- Have automatic Bloom's level detection from verb analysis

The Bloom's hierarchy matters because it ensures the unit targets appropriate cognitive complexity:

| Level | Verbs (examples) | Assessment fit |
|---|---|---|
| **Remember** (L1) | Define, list, recall, identify | MC quiz, matching |
| **Understand** (L2) | Explain, summarise, classify | Short answer, discussion |
| **Apply** (L3) | Implement, solve, demonstrate | Lab exercise, worksheet |
| **Analyse** (L4) | Compare, contrast, examine | Case study, report |
| **Evaluate** (L5) | Critique, justify, assess | Peer review, essay |
| **Create** (L6) | Design, construct, develop | Project, portfolio |

### Layer 5: Accreditation & External Alignment

Four mapping frameworks, each optional and context-dependent:

| Framework | Scope | Mapped to | Typical use case |
|---|---|---|---|
| **Program Learning Outcomes (PLO)** | Degree program | ULO | Any unit within a degree program |
| **Graduate Capabilities (GC)** | Institution | ULO | Degree program units (Curtin-specific) |
| **AACSB Assurance of Learning (AoL)** | Professional body | Unit | Business school accredited programs |
| **UN SDGs** | Global | Unit | Any unit (sustainability reporting) |

**Key insight**: Not all frameworks apply to all units.

- A unit in a Bachelor of Commerce needs AoL and GC mappings
- A unit in a Bachelor of Arts needs GC but not AoL
- An executive education short course typically needs none of these
- PLOs only make sense when the unit sits within a defined degree program

### Program Learning Outcomes (PLO) — New

PLOs are the **degree-level outcomes** that a program promises its graduates will achieve. Unlike GC/AoL/SDG (which are standardised catalogues), PLOs are:

- **User-defined**: Each program has its own PLOs, written by the program coordinator
- **Not exhaustive per unit**: A single unit addresses a subset of PLOs (typically 2-5 of 8-12)
- **Mapped to ULOs**: Each ULO should trace to at least one PLO (when PLOs are provided)

#### Data model for PLOs

PLOs are user-created text items associated with a unit, then mapped to ULOs:

```
ProgramLearningOutcome
  id: GUID
  unit_id: FK → Unit           # stored per-unit (user enters relevant PLOs)
  code: str                    # e.g. "PLO1", "PLO2" (user-assigned)
  description: str             # e.g. "Apply advanced programming concepts..."
  is_ai_suggested: bool
  notes: str | None
  created_at, updated_at

ULOProgramOutcomeMapping
  id: GUID
  ulo_id: FK → UnitLearningOutcome
  plo_id: FK → ProgramLearningOutcome
  is_ai_suggested: bool
  notes: str | None
  created_at, updated_at
```

This follows the existing accreditation mapping pattern (ADR-029) — a constants-free variant where the user provides the items rather than selecting from a predefined list.

#### Visibility rules for accreditation panels

Accreditation panels should be **context-aware** rather than always visible:

| Panel | Default visibility | Show when |
|---|---|---|
| **PLO** | Hidden | User adds at least one PLO, or enables via unit settings |
| **GC** | Visible (degree units) | Unit has `credit_points > 0` or user enables |
| **AoL** | Hidden | User enables via unit settings (business school context) |
| **SDG** | Visible | Always available (universal applicability) |

All panels can be shown/hidden via the existing unit-level feature toggles (ADR-052). The defaults above apply when no explicit toggle is set.

## Consequences

### Positive

1. **Coherent mental model**: Users (and developers) can see how every feature connects. The five-layer diagram becomes the app's conceptual backbone.

2. **PLO support completes the alignment chain**: Program outcomes → Unit outcomes → Assessment → Teaching activities. This is the full constructive alignment picture that accreditation bodies expect.

3. **Context-aware panels reduce clutter**: Executive education users won't see AoL/GC panels they don't need. Degree program users get PLO mapping when they need it.

4. **UDL as design lens, not feature**: Rather than adding a "UDL checkbox", the app naturally encourages UDL through variety in content types, session formats, assessment categories, and material phases.

5. **Correct terminology**: Using "modalities" rather than "learning styles" aligns with current evidence-based practice and avoids perpetuating debunked theory.

6. **In-app education**: The learning design guide (a new `/guide/learning-design` route) will make this framework accessible to beginners, doubling as product positioning for visitors.

### Negative

1. **PLO implementation effort**: New model, migration, API endpoints, frontend panel, and AI suggestion logic. Mitigated by following the exact pattern of existing accreditation mappings.

2. **Panel visibility logic adds complexity**: Must handle defaults, user overrides, and edge cases (no credit points set, etc.). Mitigated by building on ADR-052's feature toggle system.

### Implementation phases

| Phase | Scope | Priority |
|---|---|---|
| **Phase 1** | ADR + in-app learning design guide page | Now |
| **Phase 2** | PLO model, API, and frontend panel | Next |
| **Phase 3** | Context-aware panel visibility (feature toggle defaults) | Next |
| **Phase 4** | Wire PLO suggestions into AI generation context | Later |

## References

- Biggs, J., & Tang, C. (2011). *Teaching for Quality Learning at University* (4th ed.). McGraw-Hill.
- CAST (2018). *Universal Design for Learning Guidelines* version 2.2. https://udlguidelines.cast.org/
- Anderson, L. W., & Krathwohl, D. R. (2001). *A Taxonomy for Learning, Teaching, and Assessing* (Bloom's Revised). Longman.
- Hussey, T., & Smith, P. (2008). Learning outcomes: a conceptual analysis. *Teaching in Higher Education*, 13(1), 107-115.
- Pashler, H., et al. (2008). Learning Styles: Concepts and Evidence. *Psychological Science in the Public Interest*, 9(3), 105-119. (The debunking paper on learning styles)

## Related ADRs

- [ADR-004](004-teaching-philosophy-system.md): Teaching Philosophy System (pedagogy types)
- [ADR-029](029-accreditation-framework-mappings.md): Accreditation Framework Mappings
- [ADR-032](032-ai-assistance-levels.md): AI Assistance Levels
- [ADR-036](036-learning-design-generation-spec.md): Learning Design as Canonical Generation Spec
- [ADR-044](044-quality-scoring-algorithm.md): Unit Quality Scoring Algorithm
- [ADR-052](052-unit-level-feature-toggles.md): Unit-Level Feature Toggles
- [ADR-053](053-material-content-categories.md): Material Content Categories
