# ADR-064: Rough Slides Are a Feature, Not a Limitation

Date: 2026-04-10

## Status

Accepted

## Context

[ADR-038](038-content-not-presentation.md) established the *scope* boundary: Curriculum Curator is a content curation tool, not a presentation editor. That decision was framed as "don't compete with PowerPoint" — a product positioning argument.

This ADR establishes a stronger, *pedagogical* basis for the same direction: plain, content-focused output is not merely "good enough" — it is **actively better for student learning** than visually polished slides. This reframes feature requests around themes, animations, slide layouts, design galleries, and visual customisation: such requests should be declined not only because they are out of scope, but because they would make the tool worse at its actual job.

The distinction matters. ADR-038 lets us decline features because they belong in another tool. ADR-064 lets us decline features *even when they would technically fit*, because they would harm the educational outcomes the tool exists to support.

### The pedagogical evidence

A consistent body of research finds that visually rich instructional materials reduce learning compared to plainer alternatives:

- **Mayer's Cognitive Theory of Multimedia Learning** — the *coherence principle* states that people learn better when extraneous material is excluded from a multimedia message. Decorative images, background patterns, and stylistic flourishes consume working memory without contributing to understanding.
  *Mayer, R. E. (2009). Multimedia Learning (2nd ed.). Cambridge University Press.*

- **Seductive details effect** — interesting-but-irrelevant content (including visual polish) measurably harms retention of the core material, even when learners report enjoying the material more.
  *Harp, S. F., & Mayer, R. E. (1998). How seductive details do their damage. Journal of Educational Psychology, 90(3), 414–434.*

- **Desirable difficulties** (Bjork) — content that requires slightly more cognitive effort to process is retained better long-term. Plain slides force students to attend to the educator's spoken explanation rather than read along passively.
  *Bjork, R. A. (1994). Memory and metamemory considerations in the training of human beings. In Metcalfe & Shimamura (Eds.), Metacognition.*

- **Tufte's critique of PowerPoint** — heavily designed, bullet-driven decks correlate with reduced comprehension compared to spoken explanation supported by minimal visual aids.
  *Tufte, E. R. (2003). The Cognitive Style of PowerPoint. Graphics Press.*

- **Redundancy principle** (Mayer & Sweller, Cognitive Load Theory) — presenting the same information simultaneously as on-screen text and spoken narration impairs learning compared to narration alone with minimal visual support.
  *Sweller, J., Ayres, P., & Kalyuga, S. (2011). Cognitive Load Theory. Springer.*

The convergent finding across these traditions: **slides are scaffolding for the educator's delivery, not a deliverable in themselves.** The real artefact is what happens in the classroom. The slide's job is to give the educator a structural prompt and the students a minimal anchor — nothing more.

## Decision

Treat visual plainness in exported materials as a deliberate, defensible product stance grounded in learning science. Specifically:

### 1. Plain by default, plain on purpose

Default exports are intentionally minimal — content-focused, free of decorative styling. This is not a placeholder for future "themeing"; it is the intended end state. The product communicates this stance honestly to users rather than apologising for it.

### 2. Customisation is institutional, not personal

Where styling exists (e.g. PPTX/DOCX `--reference-doc` templates from ADR-056), it serves institutional branding requirements, not personal aesthetic preferences. Templates are uploaded once and forgotten. There is no theme picker, no font selector, no per-export style tweaking, no preview gallery.

### 3. Resist polish on principle

Feature requests that would add visual flourish — animations, transitions, slide layouts, decorative templates, background images, design galleries, "make it look nice" buttons — are declined regardless of implementation cost. They are not just out of scope; they would actively degrade the pedagogical value of the output.

### 4. Edit content, not slides

The editor surfaces semantic content (headings, lists, code, tables, images that carry meaning). It does not surface slide-level visual primitives. Slides regenerate from content; users cannot fiddle with individual slide layouts. This protects against the slow drift toward becoming a worse PowerPoint.

### 5. Speaker notes are first-class

Because the slide is scaffolding for delivery, **speaker notes carry the actual teaching content**. Notes must be a structured concept in the content model — not flattened into slide body text — and must round-trip cleanly through import and export. (Implementation gap as of this ADR: notes are extracted on PPTX import but flattened into body text and lost on export. Fixing this is a direct corollary of this ADR. See Implementation Notes.)

### 6. Communicate the stance to users

Where users encounter the export pipeline, the UI should make the philosophy visible rather than apologetic. Suggested framing:

> *Curriculum Curator produces deliberately plain slides. Research on multimedia learning consistently finds that visual polish competes with the educator's voice for student attention — and the educator wins more learners than the slide ever will. Your speaker notes carry the teaching; the slide just keeps everyone in the same place.*

This is also worth surfacing in `docs/POSITIONING.md` and the README.

## Consequences

### Positive

- **Defensible against feature creep.** "Can we add themes?" has a principled answer: no, and here is the research. Every flourish declined is one less competing surface to maintain.
- **Aligns the tool with its users' actual job.** Educators want to teach well, not produce visual artefacts. The tool reinforces that priority instead of distracting from it.
- **Simplifies the codebase permanently.** Many features that might otherwise feel like "obvious next steps" (theme galleries, slide-level visual editors, animation support) are off the table forever, not just deferred.
- **Differentiates from tools competing on visual fidelity.** Marp, Beautiful.ai, Gamma, and similar tools compete on polish. Curriculum Curator competes on pedagogy. This is a clearer market position.
- **Forces the speaker-notes gap into visibility.** Once "the slide is scaffolding, the notes carry the teaching" is the official stance, the current notes-flattening behaviour becomes an obvious bug to fix.

### Negative

- **Some users will want polish.** Educators trained to equate slide quality with teaching quality may push back. The response is education about the research, not feature accommodation.
- **Risks looking unfinished to first-time evaluators.** A product demo with deliberately plain slides may read as "MVP that hasn't built themes yet" to viewers who don't share the philosophy. The README and onboarding need to surface the stance clearly so plainness reads as intentional.
- **May lose users who want a one-stop shop.** Users who want both curriculum design and visual polish in one tool will need a second tool for the polish step. This is acceptable — those users are not the target.

### Neutral

- This ADR does not constrain export of *content-bearing* visual elements — meaningful diagrams, mathematical notation, code highlighting, embedded images that carry instructional content are unaffected. The principle targets *decorative* polish, not communication.
- Institutional branding via `--reference-doc` (ADR-056) remains valuable and is not in tension with this ADR — institutional templates exist to satisfy compliance requirements, not to add visual interest.

## Alternatives Considered

### Treat plainness as a temporary limitation

- Frame current minimal output as "we'll add themes later" and roadmap visual customisation features.
- Rejected: This concedes the philosophical ground and creates an open-ended pull toward becoming a presentation tool. Every theme added is a precedent for the next.

### Build a "polish toggle" — plain by default, fancy on demand

- Default to plain output but offer a "make it pretty" mode for users who want it.
- Rejected: A toggle implies the two modes are equivalent in value. They are not — research says one is better. Offering the worse option as a feature legitimises it. Users who want polish can edit the exported PPTX in PowerPoint.

### Stay silent on the philosophy and just ship plain output

- Simply produce plain output without articulating why.
- Rejected: Without an explicit stance, every individual feature request gets argued on its merits, and the tool drifts. The ADR exists precisely so that future decisions have something to point at.

## Implementation Notes

- **Speaker notes pipeline (follow-up work):** The current state is that PPTX import flattens notes into body text (`file_import_service.py:381-383`) and PPTX export emits no `::: notes` divs. To honour this ADR, the work is:
  1. Add a structured `notes` block type to `content_json` (TipTap node, rendered below each slide in the editor with a "speaker notes" affordance).
  2. Update PPTX import to route extracted notes into that field instead of prepending `Notes: ...` to slide text.
  3. Update the pandoc input generation in `export_service._convert_pandoc` to emit `::: notes\n<notes markdown>\n:::` blocks before each slide break, so Pandoc populates the PPTX speaker notes pane.
  4. Verify round-trip: PPTX → import → export should preserve notes in the speaker notes pane.

- **Resist UI hooks for visual customisation.** When adding any export-related UI, do not add per-export style options. Settings → Export Templates (ADR-056) is the *only* surface where styling decisions live, and it is intentionally bare.

- **Surface the philosophy in onboarding.** Add a short explainer to the README and `docs/POSITIONING.md` referencing this ADR. The goal is that users encountering plain output understand it as a deliberate choice, not a missing feature.

- **AI prompt review.** Audit the prompt templates that generate slide content (`services/seed_prompt_templates.py`) to ensure they are written in a "lecturer's outline" voice — structural prompts and speaker notes — rather than asking the model for "engaging visual content" or "compelling slides." The AI should not be encouraged to compensate for the tool's plainness; it should embrace it.

## References

- [ADR-038: Content Curation, Not Presentation Design](038-content-not-presentation.md) — the scope-boundary version of this argument
- [ADR-056: PPTX Template Extraction on Import](056-pptx-template-extraction-on-import.md) — institutional template support, the one place styling lives
- [ADR-033: Pandoc + Typst Export Engine](033-pandoc-typst-export-engine.md)
- Mayer, R. E. (2009). *Multimedia Learning* (2nd ed.). Cambridge University Press.
- Harp, S. F., & Mayer, R. E. (1998). How seductive details do their damage: A theory of cognitive interest in science learning. *Journal of Educational Psychology*, 90(3), 414–434.
- Sweller, J., Ayres, P., & Kalyuga, S. (2011). *Cognitive Load Theory*. Springer.
- Tufte, E. R. (2003). *The Cognitive Style of PowerPoint*. Graphics Press.
- Bjork, R. A. (1994). Memory and metamemory considerations in the training of human beings. In Metcalfe & Shimamura (Eds.), *Metacognition: Knowing About Knowing*. MIT Press.
