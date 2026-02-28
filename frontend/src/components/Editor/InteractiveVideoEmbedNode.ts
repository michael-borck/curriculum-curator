import { Node } from '@tiptap/core';
import { ReactNodeViewRenderer } from '@tiptap/react';
import InteractiveVideoEmbedView from './InteractiveVideoEmbedView';

export interface InteractiveVideoEmbedAttrs {
  url: string;
  platform: string;
  title: string;
}

function detectPlatform(url: string): string {
  if (/youtube\.com|youtu\.be/i.test(url)) return 'youtube';
  if (/vimeo\.com/i.test(url)) return 'vimeo';
  if (/echo360/i.test(url)) return 'echo360';
  return 'other';
}

export const InteractiveVideoEmbedNode = Node.create({
  name: 'interactiveVideoEmbed',
  group: 'block',
  atom: true,

  addAttributes() {
    return {
      url: { default: '' },
      platform: { default: 'youtube' },
      title: { default: 'Interactive Video' },
    };
  },

  parseHTML() {
    return [
      {
        tag: 'div[data-interactive-video-embed]',
        getAttrs(node) {
          const el = node as HTMLElement;
          return {
            url: el.getAttribute('data-url') || '',
            platform: el.getAttribute('data-platform') || 'youtube',
            title: el.getAttribute('data-title') || 'Interactive Video',
          };
        },
      },
    ];
  },

  renderHTML({ node }) {
    return [
      'div',
      {
        'data-interactive-video-embed': '',
        'data-url': node.attrs.url as string,
        'data-platform': node.attrs.platform as string,
        'data-title': node.attrs.title as string,
      },
      `Video: ${(node.attrs.title as string) || (node.attrs.url as string) || '(no video)'}`,
    ];
  },

  addNodeView() {
    return ReactNodeViewRenderer(InteractiveVideoEmbedView);
  },

  addCommands() {
    return {
      insertInteractiveVideoEmbed:
        (attrs?: { url?: string | undefined; title?: string | undefined }) =>
        ({ commands }) =>
          commands.insertContent({
            type: this.name,
            attrs: {
              platform: attrs?.url ? detectPlatform(attrs.url) : 'youtube',
              ...attrs,
            },
          }),
    };
  },
});
