import { Extension } from '@tiptap/core';
import { Plugin, PluginKey } from '@tiptap/pm/state';
import { Decoration, DecorationSet } from '@tiptap/pm/view';
import type { Node as PMNode } from '@tiptap/pm/model';

/**
 * Labels each slide-break divider with the slide it introduces and that
 * slide's title (its first heading), e.g. "Slide 2 — Base cases".
 *
 * This mirrors the export semantics exactly: split_at_slide_breaks segments
 * the document at slideBreak nodes and h5p_course_presentation titles each
 * slide by its first heading. Per ADR-067 we keep the slideBreak +
 * first-heading convention rather than a structured slide container; this
 * decoration just makes that convention legible in the editor.
 *
 * The label is attached as a data attribute and rendered by CSS
 * (hr.slide-break::after { content: attr(data-slide-label) }), so there is
 * no widget DOM to manage.
 */

const pluginKey = new PluginKey('slideLabel');

/** A top-level node reduced to what slide labelling needs. */
export interface SlideLabelNode {
  type: string;
  /** Trimmed text content (only meaningful for headings). */
  text: string;
}

/**
 * Pure labelling: returns the divider label for each slideBreak, keyed by
 * its index in `nodes`. Content before the first break is slide 1, so the
 * break at index i introduces slide N and is labelled with that slide's
 * first heading.
 */
export function computeSlideLabels(
  nodes: SlideLabelNode[]
): Map<number, string> {
  const labels = new Map<number, string>();
  let slide = 1;
  for (let i = 0; i < nodes.length; i++) {
    if (nodes[i]!.type !== 'slideBreak') continue;
    slide += 1;
    let title = '';
    for (let j = i + 1; j < nodes.length; j++) {
      if (nodes[j]!.type === 'slideBreak') break;
      if (nodes[j]!.type === 'heading') {
        title = nodes[j]!.text;
        break;
      }
    }
    labels.set(i, title ? `Slide ${slide} — ${title}` : `Slide ${slide}`);
  }
  return labels;
}

function buildDecorations(doc: PMNode): DecorationSet {
  const children: { node: PMNode; offset: number }[] = [];
  doc.forEach((node, offset) => children.push({ node, offset }));

  if (!children.some(c => c.node.type.name === 'slideBreak')) {
    return DecorationSet.empty;
  }

  const labels = computeSlideLabels(
    children.map(c => ({
      type: c.node.type.name,
      text: c.node.textContent.trim(),
    }))
  );

  const decorations: Decoration[] = [];
  for (let i = 0; i < children.length; i++) {
    const label = labels.get(i);
    if (label === undefined) continue;
    const { node, offset } = children[i]!;
    decorations.push(
      Decoration.node(offset, offset + node.nodeSize, {
        'data-slide-label': label,
      })
    );
  }

  return DecorationSet.create(doc, decorations);
}

export const SlideLabel = Extension.create({
  name: 'slideLabel',

  addProseMirrorPlugins() {
    return [
      new Plugin({
        key: pluginKey,
        props: {
          decorations(state) {
            return buildDecorations(state.doc);
          },
        },
      }),
    ];
  },
});
