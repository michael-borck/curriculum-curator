import { Node } from '@tiptap/core';
import { ReactNodeViewRenderer } from '@tiptap/react';
import VideoInteractionView from './VideoInteractionView';
import type { QuestionType, QuizOption } from './QuizQuestionNode';

export interface VideoInteractionAttrs {
  interactionId: string;
  time: number;
  pause: boolean;
  questionType: QuestionType;
  questionText: string;
  options: QuizOption[];
  feedback: string;
  points: number;
  explanation: string;
}

function generateId(): string {
  return globalThis.crypto.randomUUID();
}

function makeEmptyOptions(): QuizOption[] {
  return [
    { id: generateId(), text: '', correct: false },
    { id: generateId(), text: '', correct: false },
  ];
}

export const VideoInteractionNode = Node.create({
  name: 'videoInteraction',
  group: 'block',
  atom: true,

  addAttributes() {
    return {
      interactionId: { default: '' },
      time: { default: 0 },
      pause: { default: true },
      questionType: { default: 'multiple_choice' as QuestionType },
      questionText: { default: '' },
      options: { default: [] as QuizOption[] },
      feedback: { default: '' },
      points: { default: 1 },
      explanation: { default: '' },
    };
  },

  parseHTML() {
    return [
      {
        tag: 'div[data-video-interaction]',
        getAttrs(node) {
          const el = node as HTMLElement;
          let options: QuizOption[] = [];
          try {
            options = JSON.parse(
              el.getAttribute('data-options') || '[]'
            ) as QuizOption[];
          } catch {
            /* empty */
          }
          return {
            interactionId: el.getAttribute('data-interaction-id') || '',
            time: parseFloat(el.getAttribute('data-time') || '0'),
            pause: el.getAttribute('data-pause') !== 'false',
            questionType:
              el.getAttribute('data-question-type') || 'multiple_choice',
            questionText: el.getAttribute('data-question-text') || '',
            options,
            feedback: el.getAttribute('data-feedback') || '',
            points: parseInt(el.getAttribute('data-points') || '1', 10),
            explanation: el.getAttribute('data-explanation') || '',
          };
        },
      },
    ];
  },

  renderHTML({ node }) {
    return [
      'div',
      {
        'data-video-interaction': '',
        'data-interaction-id': node.attrs.interactionId as string,
        'data-time': String(node.attrs.time),
        'data-pause': String(node.attrs.pause),
        'data-question-type': node.attrs.questionType as string,
        'data-question-text': node.attrs.questionText as string,
        'data-options': JSON.stringify(node.attrs.options),
        'data-feedback': node.attrs.feedback as string,
        'data-points': String(node.attrs.points),
        'data-explanation': node.attrs.explanation as string,
      },
      `Interaction @ ${String(node.attrs.time)}s: ${(node.attrs.questionText as string) || '(new interaction)'}`,
    ];
  },

  addNodeView() {
    return ReactNodeViewRenderer(VideoInteractionView);
  },

  addCommands() {
    return {
      insertVideoInteraction:
        (attrs?: {
          time?: number | undefined;
          questionType?: QuestionType | undefined;
          questionText?: string | undefined;
          options?: QuizOption[] | undefined;
          feedback?: string | undefined;
          points?: number | undefined;
          explanation?: string | undefined;
        }) =>
        ({ commands }) =>
          commands.insertContent({
            type: this.name,
            attrs: {
              interactionId: generateId(),
              options: makeEmptyOptions(),
              ...attrs,
            },
          }),
    };
  },
});
