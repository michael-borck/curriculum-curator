import { Extension } from '@tiptap/core';
import { Plugin, PluginKey } from '@tiptap/pm/state';
import { Decoration, DecorationSet } from '@tiptap/pm/view';
import type { EditorView } from '@tiptap/pm/view';
import type { Node as PMNode } from '@tiptap/pm/model';

/**
 * Per-slide "+ Add speaker notes" affordance (speaker-notes plan Phase 2).
 *
 * Decorates the end of every slide segment that has content but no
 * speakerNotes node with a button that inserts an empty notes block at
 * the canonical position (end of the segment, before the next slideBreak).
 * Only active in slide-style documents (at least one slideBreak present).
 */

const pluginKey = new PluginKey('speakerNotesAffordance');

function makeAddNotesButton(view: EditorView, insertPos: number): HTMLElement {
  const button = document.createElement('button');
  button.type = 'button';
  button.className = 'speaker-notes-add-button';
  button.textContent = '+ Add speaker notes';
  button.contentEditable = 'false';
  button.addEventListener('mousedown', event => {
    event.preventDefault();
    const notesType = view.state.schema.nodes.speakerNotes;
    if (!notesType) return;
    const notesNode = notesType.createAndFill();
    if (!notesNode) return;
    const tr = view.state.tr.insert(insertPos, notesNode);
    view.dispatch(tr);
    view.focus();
  });
  return button;
}

function buildDecorations(doc: PMNode, view: EditorView): DecorationSet {
  let hasAnySlideBreak = false;
  doc.forEach((child: PMNode) => {
    if (child.type.name === 'slideBreak') hasAnySlideBreak = true;
  });
  if (!hasAnySlideBreak) return DecorationSet.empty;

  const decorations: Decoration[] = [];
  let segmentHasContent = false;
  let segmentHasNotes = false;
  let segmentEnd = 0;

  const flush = () => {
    if (segmentHasContent && !segmentHasNotes) {
      const pos = segmentEnd;
      decorations.push(
        Decoration.widget(pos, () => makeAddNotesButton(view, pos), {
          side: 1,
          key: `add-notes-${pos}`,
        })
      );
    }
    segmentHasContent = false;
    segmentHasNotes = false;
  };

  doc.forEach((child: PMNode, offset: number) => {
    if (child.type.name === 'slideBreak') {
      flush();
    } else {
      if (child.type.name === 'speakerNotes') {
        segmentHasNotes = true;
      } else if (child.textContent.trim() || child.isAtom) {
        segmentHasContent = true;
      }
      segmentEnd = offset + child.nodeSize;
    }
  });
  flush();

  return DecorationSet.create(doc, decorations);
}

export const SpeakerNotesAffordance = Extension.create({
  name: 'speakerNotesAffordance',

  addProseMirrorPlugins() {
    const editor = this.editor;
    return [
      new Plugin({
        key: pluginKey,
        props: {
          decorations(state) {
            if (!editor.isEditable) return DecorationSet.empty;
            return buildDecorations(state.doc, editor.view);
          },
        },
      }),
    ];
  },
});
