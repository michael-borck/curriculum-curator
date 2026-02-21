import { Node, mergeAttributes } from '@tiptap/core';

export const VideoNode = Node.create({
  name: 'video',
  group: 'block',
  atom: true,

  addAttributes() {
    return {
      src: { default: null },
    };
  },

  parseHTML() {
    return [{ tag: 'video[src]' }];
  },

  renderHTML({ HTMLAttributes }) {
    return [
      'video',
      mergeAttributes(HTMLAttributes, {
        controls: 'true',
        style: 'max-width:100%;height:auto;',
      }),
    ];
  },

  addCommands() {
    return {
      setVideo:
        (attrs: { src: string }) =>
        ({ commands }) =>
          commands.insertContent({ type: this.name, attrs }),
    };
  },
});
