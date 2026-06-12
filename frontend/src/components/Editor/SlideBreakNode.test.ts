import { describe, it, expect, afterEach } from 'vitest';
import { Editor } from '@tiptap/core';
import StarterKit from '@tiptap/starter-kit';
import { SlideBreakNode } from './SlideBreakNode';
import { SpeakerNotesNode } from './SpeakerNotesNode';

let editor: Editor | null = null;

const paragraph = (text: string) => ({
  type: 'paragraph',
  content: text ? [{ type: 'text', text }] : [],
});

const notes = (text: string) => ({
  type: 'speakerNotes',
  content: [paragraph(text)],
});

// Content is built as JSON (like production content_json), not HTML — an
// `<hr>` in HTML parses as StarterKit's horizontalRule, not a slideBreak.
function makeEditor(content: object[]): Editor {
  editor = new Editor({
    extensions: [StarterKit, SlideBreakNode, SpeakerNotesNode],
    content: { type: 'doc', content },
  });
  return editor;
}

afterEach(() => {
  editor?.destroy();
  editor = null;
});

const topLevelTypes = (ed: Editor): string[] =>
  (ed.getJSON().content ?? []).map(node => node.type as string);

describe('insertSlideBreak', () => {
  it('scaffolds an empty speaker-notes block for a slide without notes', () => {
    const ed = makeEditor([paragraph('Slide one content')]);
    ed.commands.setTextSelection(ed.state.doc.content.size - 1);

    ed.commands.insertSlideBreak();

    const types = topLevelTypes(ed);
    expect(types).toContain('speakerNotes');
    expect(types).toContain('slideBreak');
    expect(types.indexOf('speakerNotes')).toBeLessThan(
      types.indexOf('slideBreak')
    );
  });

  it('does not scaffold a second notes block when the slide already has one', () => {
    const ed = makeEditor([paragraph('Slide one'), notes('existing')]);
    // Cursor inside the first paragraph
    ed.commands.setTextSelection(3);

    ed.commands.insertSlideBreak();

    const types = topLevelTypes(ed);
    expect(types.filter(t => t === 'speakerNotes')).toHaveLength(1);
    expect(types.filter(t => t === 'slideBreak')).toHaveLength(1);
  });

  it('only inspects the current slide segment for existing notes', () => {
    const ed = makeEditor([
      paragraph('Slide one'),
      notes('notes for one'),
      { type: 'slideBreak' },
      paragraph('Slide two without notes'),
    ]);
    ed.commands.setTextSelection(ed.state.doc.content.size - 1);

    ed.commands.insertSlideBreak();

    const types = topLevelTypes(ed);
    // One existing notes block plus a freshly scaffolded one for slide two
    expect(types.filter(t => t === 'speakerNotes')).toHaveLength(2);
    expect(types.filter(t => t === 'slideBreak')).toHaveLength(2);
  });

  it('never nests a slide break inside a speaker-notes block', () => {
    const ed = makeEditor([paragraph('Slide one'), notes('existing notes')]);
    // Place the cursor inside the notes block (after its text)
    ed.commands.setTextSelection(ed.state.doc.content.size - 2);

    ed.commands.insertSlideBreak();

    const json = ed.getJSON();
    const notesNode = (json.content ?? []).find(
      node => node.type === 'speakerNotes'
    );
    const nestedTypes = (notesNode?.content ?? []).map(node => node.type);
    expect(nestedTypes).not.toContain('slideBreak');
    expect(topLevelTypes(ed)).toContain('slideBreak');
  });
});
