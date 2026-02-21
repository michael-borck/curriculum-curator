import '@tiptap/core';

declare module '@tiptap/core' {
  interface Commands<ReturnType> {
    video: {
      setVideo: (attrs: { src: string }) => ReturnType;
    };
    youtube: {
      setYoutubeVideo: (attrs: { src: string }) => ReturnType;
    };
    mermaid: {
      insertMermaid: (attrs?: { source?: string }) => ReturnType;
    };
  }
}
