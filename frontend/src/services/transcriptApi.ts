/**
 * Transcript API client — fetch YouTube transcripts and parse VTT/SRT uploads.
 */

import api from './api';

export interface TranscriptSegment {
  start: number;
  end: number;
  text: string;
}

export interface TranscriptResponse {
  segments: TranscriptSegment[];
  source: string;
  language?: string | undefined;
}

export const transcriptApi = {
  /** Fetch auto-generated transcript from a YouTube video URL. */
  fetchYoutube(url: string) {
    return api.post<TranscriptResponse>('/transcript/fetch-youtube', { url });
  },

  /** Upload and parse a VTT or SRT subtitle file. */
  parseVtt(file: File) {
    const formData = new FormData();
    formData.append('file', file);
    return api.post<TranscriptResponse>('/transcript/parse-vtt', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
};
