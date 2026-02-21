import { Node, mergeAttributes } from '@tiptap/core';

/**
 * Extract a YouTube video ID from various URL formats.
 * Returns null if the URL is not a recognized YouTube URL.
 */
function extractYoutubeId(url: string): string | null {
  const patterns = [
    /(?:youtube\.com\/watch\?v=|youtube\.com\/embed\/|youtu\.be\/)([\w-]{11})/,
    /youtube\.com\/shorts\/([\w-]{11})/,
    /youtube-nocookie\.com\/embed\/([\w-]{11})/,
  ];
  for (const pattern of patterns) {
    const match = url.match(pattern);
    if (match) return match[1];
  }
  return null;
}

export const YoutubeNode = Node.create({
  name: 'youtube',
  group: 'block',
  atom: true,

  addAttributes() {
    return {
      src: { default: null },
      width: { default: 640 },
      height: { default: 360 },
    };
  },

  parseHTML() {
    return [
      {
        tag: 'div[data-youtube-video]',
        getAttrs(node) {
          const iframe = (node as HTMLElement).querySelector('iframe');
          return iframe ? { src: iframe.getAttribute('src') } : false;
        },
      },
    ];
  },

  renderHTML({ HTMLAttributes }) {
    const { src, width, height, ...rest } = HTMLAttributes as {
      src: string;
      width: number;
      height: number;
      [key: string]: unknown;
    };
    return [
      'div',
      mergeAttributes(rest, { 'data-youtube-video': '' }),
      [
        'iframe',
        {
          src,
          width,
          height,
          allowfullscreen: 'true',
          allow:
            'accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture',
          style: 'border:0;',
        },
      ],
    ];
  },

  addCommands() {
    return {
      setYoutubeVideo:
        (attrs: { src: string }) =>
        ({ commands }) => {
          const id = extractYoutubeId(attrs.src);
          if (!id) return false;
          const embedUrl = `https://www.youtube-nocookie.com/embed/${id}`;
          return commands.insertContent({
            type: this.name,
            attrs: { src: embedUrl },
          });
        },
    };
  },
});
