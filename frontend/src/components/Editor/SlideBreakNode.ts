import { Node } from '@tiptap/core';

declare module '@tiptap/core' {
  interface Commands<ReturnType> {
    slideBreak: {
      insertSlideBreak: () => ReturnType;
    };
  }
}

export const SlideBreakNode = Node.create({
  name: 'slideBreak',
  group: 'block',
  atom: true,

  parseHTML() {
    return [{ tag: 'hr[data-slide-break]' }];
  },

  renderHTML() {
    return ['hr', { 'data-slide-break': '', class: 'slide-break' }];
  },

  addCommands() {
    return {
      insertSlideBreak:
        () =>
        ({ commands }) =>
          commands.insertContent({ type: this.name }),
    };
  },
});
