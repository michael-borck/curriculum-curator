import { Node } from '@tiptap/core';
import { ReactNodeViewRenderer } from '@tiptap/react';
import BranchingCardView from './BranchingCardView';

export type CardType = 'content' | 'branch' | 'ending';

export interface BranchingChoice {
  id: string;
  text: string;
  targetCardId: string;
  feedback: string;
}

export interface BranchingCardAttrs {
  cardId: string;
  cardType: CardType;
  cardTitle: string;
  cardContent: string;
  choices: BranchingChoice[];
  endScore: number;
  endMessage: string;
}

function generateId(): string {
  return globalThis.crypto.randomUUID();
}

function makeEmptyChoices(): BranchingChoice[] {
  return [
    { id: generateId(), text: '', targetCardId: '', feedback: '' },
    { id: generateId(), text: '', targetCardId: '', feedback: '' },
  ];
}

export const BranchingCardNode = Node.create({
  name: 'branchingCard',
  group: 'block',
  atom: true,

  addAttributes() {
    return {
      cardId: { default: '' },
      cardType: { default: 'content' as CardType },
      cardTitle: { default: '' },
      cardContent: { default: '' },
      choices: { default: [] as BranchingChoice[] },
      endScore: { default: 0 },
      endMessage: { default: '' },
    };
  },

  parseHTML() {
    return [
      {
        tag: 'div[data-branching-card]',
        getAttrs(node) {
          const el = node as HTMLElement;
          let choices: BranchingChoice[] = [];
          try {
            choices = JSON.parse(
              el.getAttribute('data-choices') || '[]'
            ) as BranchingChoice[];
          } catch {
            /* empty */
          }
          return {
            cardId: el.getAttribute('data-card-id') || '',
            cardType: el.getAttribute('data-card-type') || 'content',
            cardTitle: el.getAttribute('data-card-title') || '',
            cardContent: el.getAttribute('data-card-content') || '',
            choices,
            endScore: parseInt(el.getAttribute('data-end-score') || '0', 10),
            endMessage: el.getAttribute('data-end-message') || '',
          };
        },
      },
    ];
  },

  renderHTML({ node }) {
    return [
      'div',
      {
        'data-branching-card': '',
        'data-card-id': node.attrs.cardId as string,
        'data-card-type': node.attrs.cardType as string,
        'data-card-title': node.attrs.cardTitle as string,
        'data-card-content': node.attrs.cardContent as string,
        'data-choices': JSON.stringify(node.attrs.choices),
        'data-end-score': String(node.attrs.endScore),
        'data-end-message': node.attrs.endMessage as string,
      },
      `Card: ${(node.attrs.cardTitle as string) || '(new card)'}`,
    ];
  },

  addNodeView() {
    return ReactNodeViewRenderer(BranchingCardView);
  },

  addCommands() {
    return {
      insertBranchingCard:
        (attrs?: {
          cardType?: CardType | undefined;
          cardTitle?: string | undefined;
          cardContent?: string | undefined;
          choices?: BranchingChoice[] | undefined;
          endScore?: number | undefined;
          endMessage?: string | undefined;
        }) =>
        ({ commands }) =>
          commands.insertContent({
            type: this.name,
            attrs: {
              cardId: generateId(),
              cardType: 'branch',
              choices: makeEmptyChoices(),
              ...attrs,
            },
          }),
    };
  },
});
