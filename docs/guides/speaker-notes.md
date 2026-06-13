# Speaker Notes

Speaker notes carry your teaching — what you *say*, not what students see on
screen. Curriculum Curator treats the slide as scaffolding for delivery and
the notes as the substance (see [ADR-064](../adr/064-rough-slides-as-feature.md)
for the pedagogy behind this).

## Writing notes

Open a material's content editor (the file icon on a material card). In
slide-style materials (anything with slide breaks):

- Every slide shows its notes in a distinct amber block labelled
  **Speaker notes**, rendered beneath the slide content.
- Inserting a slide break automatically scaffolds an empty notes block for
  the slide you just finished. Delete it if you don't want notes there.
- Slides without notes show a **+ Add speaker notes** button.
- Material cards display a **Notes N/M** badge so you can see coverage at a
  glance. It's informational only — some excellent lecturers don't use notes.

## Generating notes with AI

With AI features enabled, the **Notes with AI** button in the editor drafts
conversational notes for your slides:

1. Choose which slides to include (slides whose notes block is opted out of
   AI generation are unticked by default).
2. One batched call drafts notes for all selected slides, using your unit's
   pedagogy and Learning Design context.
3. Review each draft side by side with any existing notes, untick the ones
   you don't want, and apply. Nothing is saved until you accept the drafts
   and save the material.

The drafts follow the house rules: they never repeat the slide text (notes
expand on what's visible), they're written in a lecturer's first-person
voice, and they include natural transitions between slides.

## Where notes go on export

- **PPTX** — notes land in PowerPoint's speaker notes pane, exactly where
  presenter view expects them. They survive a full import → edit → export
  round trip.
- **Everything else** (PDF, DOCX, HTML, IMSCC, SCORM, H5P) — notes are
  stripped. They're a delivery aid for you, never a student-facing artefact.
