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
        ({ state, chain }) => {
          // Scaffold an empty speaker-notes block for the slide being
          // closed, unless it already has one. Notes sit before the break
          // (the canonical position the backend slide splitter expects),
          // so they render inside the slide they describe.
          const { doc, selection } = state;
          const topIndex = selection.$from.index(0);

          let segmentStart = 0;
          for (let i = Math.min(topIndex, doc.childCount - 1); i >= 0; i--) {
            if (doc.child(i).type.name === 'slideBreak') {
              segmentStart = i + 1;
              break;
            }
          }
          let hasNotes = false;
          for (let i = segmentStart; i < doc.childCount; i++) {
            const child = doc.child(i);
            if (child.type.name === 'slideBreak') break;
            if (child.type.name === 'speakerNotes') {
              hasNotes = true;
              break;
            }
          }

          const content = hasNotes
            ? [{ type: this.name }]
            : [
                { type: 'speakerNotes', content: [{ type: 'paragraph' }] },
                { type: this.name },
              ];

          // A slide break only makes sense at the top level. If the cursor
          // sits inside a speaker-notes block, insert after that block
          // instead of splitting it.
          const topNode = doc.maybeChild(
            Math.min(topIndex, doc.childCount - 1)
          );
          if (topNode?.type.name === 'speakerNotes') {
            return chain()
              .insertContentAt(selection.$from.after(1), content)
              .run();
          }
          return chain().insertContent(content).run();
        },
    };
  },
});
