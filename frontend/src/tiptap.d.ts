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
    quizQuestion: {
      insertQuizQuestion: (attrs?: {
        questionType?:
          | 'multiple_choice'
          | 'true_false'
          | 'multi_select'
          | 'short_answer'
          | 'fill_in_blank'
          | undefined;
        questionText?: string | undefined;
        options?: Array<{ id: string; text: string; correct: boolean }> | undefined;
        feedback?: string | undefined;
        points?: number | undefined;
        explanation?: string | undefined;
      }) => ReturnType;
    };
  }
}
