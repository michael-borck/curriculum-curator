# Product Positioning

> **"This is a curriculum design tool that happens to produce content, not a content tool that happens to know about curriculum."**

## The Problem

Educators currently use disconnected tools for curriculum work:

- **Learning design**: Spreadsheets, alignment matrices, institutional templates
- **Content authoring**: PowerPoint, Word, Google Docs — tools with zero awareness of learning outcomes or pedagogy
- **Delivery**: The LMS (Canvas, Blackboard, Moodle) — good at delivery, poor at design

No single tool connects the design decisions (ULOs, Bloom's taxonomy, pedagogy, accreditation) to the content production. The result is that learning design lives in one place, content lives in another, and alignment is checked manually (if at all).

## Where Curriculum Curator Sits

### What no LMS does well

- Structured learning design upfront — ULOs with Bloom's taxonomy, mapped to graduate capabilities, Assurance of Learning (AoL), and UN SDGs
- Design context flowing **into** content generation — the AI doesn't just write generic text, it writes to your ULOs at the right Bloom's level with the chosen pedagogy
- The pre/in/post-class category model — thinking about learning sequences, not just dumping files into weekly folders
- Quality scoring that checks alignment ("does this material actually serve a ULO?")
- Seeing the whole unit as a coherent design, not a collection of disconnected pages

### What PowerPoint and Word don't do

- They have zero awareness of learning outcomes, pedagogy, or curriculum structure
- No way to check "does my Week 3 lecture actually address ULO2?"
- No AI assistance grounded in pedagogical context
- No structured export that preserves the design intent

### What existing edtech tools miss

| Tool category | Example | Gap |
|---|---|---|
| LMS content authoring | CourseArc, Storyboard That | No learning design layer |
| Learning design tools | ATLAS (Laurillard's ABC) | Doesn't produce deliverable content |
| Alignment checkers | Various constructive alignment tools | No content authoring |

**Curriculum Curator bridges learning design and content production.** The designer does the thinking (ULOs, alignment, pedagogy, structure), and the content authoring is informed by that thinking. That integration doesn't exist as a single tool.

## The LMS Relationship

Curriculum Curator is not trying to replace the LMS. The LMS is the delivery platform. This app is the design and authoring environment. The boundary is the IMSCC export — a standard interchange format that any LMS can import.

The workflow: **design and author here, deliver in Canvas** (or Moodle, or Blackboard).

The round-trip via IMSCC means educators can go back and forth — import existing content from their LMS, enhance it with learning design structure and AI assistance, then export it back. The app preserves LMS identifiers and structure so re-exports update the existing course shell rather than creating a new one (see [ADR-054](adr/054-import-provenance-round-trip-fidelity.md)).

API integration with the LMS is deliberately out of scope. The moment you start managing LMS state directly, you're competing with the LMS on its own turf. The IMSCC package is the "save file" metaphor — clean, portable, institution-independent.

## Who It's For

- **Academics who care about constructive alignment** and are currently doing it in spreadsheets + Word + the LMS separately
- **Course and program coordinators** who need to ensure units meet accreditation requirements (AoL, SDGs, graduate capabilities) and currently track that in Excel
- **New unit developers** starting from scratch who want AI-assisted scaffolding grounded in pedagogy, not just "write me a lecture about X"
- **Teaching-focused academics** building evidence of pedagogical rigour for promotion or review
- **Anyone tired of the disconnect** between what they designed and what they delivered

It's probably not for the academic who is happy uploading PowerPoint slides and a PDF reading per week. That workflow works fine for them. This is for people who want their content to be intentionally aligned with their learning design — and want AI assistance that understands that intent.

## The Core Differentiator

Nobody connects learning design decisions to content production with AI assistance in one tool. That's a narrow gap, but it's real. The AI in this app isn't a generic writing assistant — it's grounded in the unit's learning outcomes, Bloom's levels, chosen pedagogy, and accreditation requirements. It produces content that is aligned by design, not by accident.
