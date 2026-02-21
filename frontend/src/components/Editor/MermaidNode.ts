import { Node } from '@tiptap/core';
import { ReactNodeViewRenderer } from '@tiptap/react';
import MermaidView from './MermaidView';

export const MermaidNode = Node.create({
  name: 'mermaid',
  group: 'block',
  atom: true,

  addAttributes() {
    return {
      source: {
        default: 'graph TD\n  A[Start] --> B[End]',
      },
    };
  },

  parseHTML() {
    return [
      {
        tag: 'pre.mermaid',
        getAttrs(node) {
          const el = node as HTMLElement;
          return { source: el.textContent || '' };
        },
      },
    ];
  },

  renderHTML({ node }) {
    const source = node.attrs.source as string;
    return ['pre', { class: 'mermaid' }, source];
  },

  addNodeView() {
    return ReactNodeViewRenderer(MermaidView);
  },

  addCommands() {
    return {
      insertMermaid:
        (attrs?: { source?: string }) =>
        ({ commands }) =>
          commands.insertContent({
            type: this.name,
            attrs: attrs || {},
          }),
    };
  },
});
