import { describe, it, expect, afterEach } from 'vitest';
import { Editor } from '@tiptap/core';
import StarterKit from '@tiptap/starter-kit';
import { QuizQuestionNode } from './QuizQuestionNode';

let editor: Editor | null = null;

afterEach(() => {
  editor?.destroy();
  editor = null;
});

function makeEditor(content: object | string): Editor {
  // ReactNodeViewRenderer isn't exercised in a headless editor; the node's
  // schema + parse/serialize round-trip is what we verify here.
  editor = new Editor({
    extensions: [StarterKit, QuizQuestionNode],
    content,
  });
  return editor;
}

describe('QuizQuestionNode matching attrs', () => {
  it('round-trips matching pairs through serialize/parse', () => {
    const pairs = [
      { id: 'p1', left: 'Dog', right: 'Bark' },
      { id: 'p2', left: 'Cat', right: 'Meow' },
    ];
    const doc = {
      type: 'doc',
      content: [
        {
          type: 'quizQuestion',
          attrs: {
            questionId: 'q1',
            questionType: 'matching',
            questionText: 'Match the animal to its sound',
            options: [],
            pairs,
            feedback: '',
            points: 2,
            explanation: '',
          },
        },
      ],
    };

    const ed = makeEditor(doc);
    // Serialize to HTML and re-parse into a fresh editor
    const html = ed.getHTML();
    expect(html).toContain('data-pairs');

    const reparsed = makeEditor(html);
    const node = reparsed.getJSON().content?.[0];
    expect(node?.attrs?.questionType).toBe('matching');
    expect(node?.attrs?.pairs).toEqual(pairs);
  });

  it('round-trips drag_drop words through options', () => {
    const options = [
      { id: 'o1', text: 'cat', correct: true },
      { id: 'o2', text: 'mat', correct: true },
      { id: 'o3', text: 'dog', correct: false },
    ];
    const ed = makeEditor({
      type: 'doc',
      content: [
        {
          type: 'quizQuestion',
          attrs: {
            questionId: 'q1',
            questionType: 'drag_drop',
            questionText: 'The ___ sat on the ___.',
            options,
            pairs: [],
          },
        },
      ],
    });
    const reparsed = makeEditor(ed.getHTML());
    const node = reparsed.getJSON().content?.[0];
    expect(node?.attrs?.questionType).toBe('drag_drop');
    expect(node?.attrs?.options).toEqual(options);
  });

  it('defaults pairs to an empty array for non-matching questions', () => {
    const ed = makeEditor({
      type: 'doc',
      content: [
        {
          type: 'quizQuestion',
          attrs: {
            questionId: 'q1',
            questionType: 'multiple_choice',
            questionText: 'Pick one',
            options: [{ id: 'o1', text: 'A', correct: true }],
          },
        },
      ],
    });
    const node = ed.getJSON().content?.[0];
    expect(node?.attrs?.pairs).toEqual([]);
  });
});
