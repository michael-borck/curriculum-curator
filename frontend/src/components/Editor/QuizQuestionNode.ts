import { Node } from '@tiptap/core';
import { ReactNodeViewRenderer } from '@tiptap/react';
import QuizQuestionView from './QuizQuestionView';

export type QuestionType =
  | 'multiple_choice'
  | 'true_false'
  | 'multi_select'
  | 'short_answer'
  | 'fill_in_blank';

export interface QuizOption {
  id: string;
  text: string;
  correct: boolean;
}

export interface QuizQuestionAttrs {
  questionId: string;
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

export const QuizQuestionNode = Node.create({
  name: 'quizQuestion',
  group: 'block',
  atom: true,

  addAttributes() {
    return {
      questionId: { default: '' },
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
        tag: 'div[data-quiz-question]',
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
            questionId: el.getAttribute('data-question-id') || '',
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
        'data-quiz-question': '',
        'data-question-id': node.attrs.questionId as string,
        'data-question-type': node.attrs.questionType as string,
        'data-question-text': node.attrs.questionText as string,
        'data-options': JSON.stringify(node.attrs.options),
        'data-feedback': node.attrs.feedback as string,
        'data-points': String(node.attrs.points),
        'data-explanation': node.attrs.explanation as string,
      },
      `Quiz: ${(node.attrs.questionText as string) || '(new question)'}`,
    ];
  },

  addNodeView() {
    return ReactNodeViewRenderer(QuizQuestionView);
  },

  addCommands() {
    return {
      insertQuizQuestion:
        (attrs?: {
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
              questionId: generateId(),
              options: makeEmptyOptions(),
              ...attrs,
            },
          }),
    };
  },
});
