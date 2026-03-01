/**
 * Video Interaction AI API client — generate quiz interactions from transcripts.
 */

import api from './api';

export interface GenerateVideoInteractionOption {
  text: string;
  correct: boolean;
}

export interface GenerateVideoInteractionRequest {
  segmentText: string;
  questionType?: string | undefined;
  unitId?: string | undefined;
  designId?: string | undefined;
  weekNumber?: number | undefined;
  difficulty?: string | undefined;
}

export interface GenerateVideoInteractionResponse {
  questionText: string;
  questionType: string;
  options: GenerateVideoInteractionOption[];
  feedback: string;
  explanation: string;
  points: number;
}

export interface TranscriptSegmentInput {
  start: number;
  end: number;
  text: string;
}

export interface SuggestInteractionPointsRequest {
  transcriptSegments: TranscriptSegmentInput[];
  unitId?: string | undefined;
  designId?: string | undefined;
  weekNumber?: number | undefined;
  maxInteractions?: number | undefined;
}

export interface SuggestedInteraction {
  time: number;
  questionText: string;
  questionType: string;
  options: GenerateVideoInteractionOption[];
  feedback: string;
  explanation: string;
  points: number;
}

export interface SuggestInteractionPointsResponse {
  interactions: SuggestedInteraction[];
}

export const videoInteractionApi = {
  /** Generate a single quiz interaction from transcript context. */
  generateInteraction(req: GenerateVideoInteractionRequest) {
    return api.post<GenerateVideoInteractionResponse>(
      '/ai/generate-video-interaction',
      req
    );
  },

  /** Scan a full transcript and suggest interaction points with questions. */
  suggestInteractionPoints(req: SuggestInteractionPointsRequest) {
    return api.post<SuggestInteractionPointsResponse>(
      '/ai/suggest-interaction-points',
      req
    );
  },
};
