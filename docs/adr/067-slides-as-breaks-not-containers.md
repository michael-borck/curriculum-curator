# 67. Slides as Breaks, Not Containers

Date: 2026-06-18

## Status

Accepted

## Context

User story 19C.4 asked for "structured slide break nodes in the editor so I can
clearly separate slides with titles and content areas, making export to PPTX
and H5P Course Presentation predictable." Read literally, this suggests a
structured *slide container* node — a `slide` node that wraps a title field and
a content area, with the document being a list of `slide` nodes.

The editor and exporters already model slides differently. A deck is a flat
sequence of block nodes (headings, paragraphs, lists, images, speaker notes)
punctuated by atomic `slideBreak` nodes. Export reads this convention directly:

- `slide_splitter.split_at_slide_breaks` segments the document at `slideBreak`
  boundaries — content before the first break is slide 1, and so on.
- `h5p_course_presentation._extract_first_heading` titles each slide by the
  first heading in its segment.
- The PPTX export path (`export_service`) and structured PPTX *import*
  (`material_parsers/pptx_structural`) both produce and consume this same flat
  `slideBreak` shape.

A structured slide-container node would:

- **Break the splitter and both export paths**, which walk a flat node list, not
  nested slide containers.
- **Orphan every existing PPTX import**, which emits flat content + `slideBreak`s
  — they would need a re-import or a migration.
- **Conflict with [ADR-064](064-rough-slides-as-feature.md)** ("rough slides are
  a feature") and [ADR-038](038-content-not-presentation.md) ("content, not
  presentation"): a title+content-area container is a presentation structure,
  the kind of visual scaffolding those ADRs deliberately decline.

The actual problem the story names — *predictable* export — is already solved by
the convention: a slide's title is whatever heading starts it. What was missing
was making that convention **legible in the editor**, so authors understand why
the first heading matters and can see where each slide begins.

## Decision

Keep the flat `slideBreak` + first-heading-as-title convention. Do **not**
introduce a structured slide-container node.

Make the convention visible instead: a `SlideLabel` editor decoration renders
each slide-break divider as "Slide N — {first heading}", computed with the same
segmentation the exporter uses (`computeSlideLabels` mirrors
`split_at_slide_breaks` + `_extract_first_heading`). The slides starter template
(19C.1) models the heading-then-content-then-notes shape so new decks start in
the right structure.

Story 19C.4 is re-scoped accordingly: "structured slide break nodes" is read as
"clearly delineated slide breaks that make export predictable", which the
labelled divider delivers.

## Consequences

### Positive

- No change to the splitter, exporters, or importers; no migration of existing
  PPTX imports.
- Stays aligned with ADR-064 / ADR-038 — slides remain content, not a
  presentation structure.
- The editor now shows each slide's number and title at its boundary, so the
  "first heading is the title" rule is self-evident.
- The label is derived (a decoration), so it can never drift from the content or
  need persisting.

### Negative

- The title is implicit (the first heading) rather than a dedicated field, so a
  slide with no heading exports untitled — surfaced in the editor as a bare
  "Slide N" label, which nudges the author to add one.
- Slide 1 (before any break) has no divider and so no label; its title is still
  its first heading on export.
