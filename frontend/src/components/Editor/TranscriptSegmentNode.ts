import { Node } from '@tiptap/core';
import { ReactNodeViewRenderer } from '@tiptap/react';
import TranscriptSegmentView from './TranscriptSegmentView';

export interface TranscriptSegmentAttrs {
  startTime: number;
  endTime: number;
}

export const TranscriptSegmentNode = Node.create({
  name: 'transcriptSegment',
  group: 'block',
  content: 'text*',

  addAttributes() {
    return {
      startTime: { default: 0 },
      endTime: { default: 0 },
    };
  },

  parseHTML() {
    return [
      {
        tag: 'div[data-transcript-segment]',
        getAttrs(node) {
          const el = node as HTMLElement;
          return {
            startTime: parseFloat(el.getAttribute('data-start-time') || '0'),
            endTime: parseFloat(el.getAttribute('data-end-time') || '0'),
          };
        },
      },
    ];
  },

  renderHTML({ node, HTMLAttributes }) {
    return [
      'div',
      {
        ...HTMLAttributes,
        'data-transcript-segment': '',
        'data-start-time': String(node.attrs.startTime),
        'data-end-time': String(node.attrs.endTime),
      },
      0, // content hole
    ];
  },

  addNodeView() {
    return ReactNodeViewRenderer(TranscriptSegmentView);
  },
});
