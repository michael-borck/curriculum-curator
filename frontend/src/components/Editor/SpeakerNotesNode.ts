import { Node, mergeAttributes } from '@tiptap/core';

/**
 * SpeakerNotes node — author-only delivery prompts that travel with their slide.
 *
 * Per ADR-064 the slide is scaffolding for the educator's delivery; the
 * speaker notes are where the actual teaching content lives. They round-trip
 * to PowerPoint's speaker notes pane via Pandoc's `::: notes` fenced div on
 * PPTX export. All other export targets strip them — they are never shown
 * to students.
 *
 * This Phase 1 node is the minimum needed for the storage and round-trip
 * pipeline. Authoring affordances (auto-scaffold on slide-break insertion,
 * AI generation, coverage indicators) are Phase 2 of the speaker-notes plan.
 */
export const SpeakerNotesNode = Node.create({
  name: 'speakerNotes',
  group: 'block',
  content: 'block+',
  defining: true,

  addAttributes() {
    return {
      // Per-slide opt-in/out toggle for AI generation (Phase 3 of the plan).
      // Defaults to true so AI bulk generation operates on every slide unless
      // the user explicitly opts out.
      aiSelected: {
        default: true,
        parseHTML: element =>
          element.getAttribute('data-ai-selected') !== 'false',
        renderHTML: attributes => ({
          'data-ai-selected': attributes.aiSelected ? 'true' : 'false',
        }),
      },
    };
  },

  parseHTML() {
    return [{ tag: 'aside[data-type="speaker-notes"]' }];
  },

  renderHTML({ HTMLAttributes }) {
    return [
      'aside',
      mergeAttributes(HTMLAttributes, { 'data-type': 'speaker-notes' }),
      0,
    ];
  },
});
