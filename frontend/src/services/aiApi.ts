/**
 * AI API client — typed wrappers for AI/LLM endpoints.
 */

import api from './api';

// ─── Scaffold Types ──────────────────────────────────────────────────────────

export interface ScaffoldULO {
  code: string;
  description: string;
  bloomLevel: string;
}

export interface ScaffoldWeek {
  weekNumber: number;
  topic: string;
  activities: string[];
}

export interface ScaffoldAssessment {
  title: string;
  category: string;
  weight: number;
  dueWeek: number | null;
}

export interface ScaffoldUnitResponse {
  title: string;
  description: string;
  ulos: ScaffoldULO[];
  weeks: ScaffoldWeek[];
  assessments: ScaffoldAssessment[];
}

// ─── Fill Gap Types ──────────────────────────────────────────────────────────

export interface FillGapResponse {
  gapType: string;
  generatedContent: string;
  suggestions: string[];
}

// ─── Speaker Notes Types ─────────────────────────────────────────────────────

export interface SpeakerNotesDraft {
  slideIndex: number;
  notes: string;
}

export interface GenerateSpeakerNotesResponse {
  drafts: SpeakerNotesDraft[];
}

// ─── Structure Recovery Types (6.16) ─────────────────────────────────────────

export interface RestructureContentResponse {
  contentJson: Record<string, unknown>;
  headingCount: number;
  listCount: number;
  paragraphCount: number;
}

// ─── API Calls ───────────────────────────────────────────────────────────────

export const aiApi = {
  /** Generate a full unit scaffold from title + description. */
  scaffoldUnit(data: {
    title: string;
    description?: string | undefined;
    durationWeeks?: number | undefined;
    pedagogyStyle?: string | undefined;
    unitId?: string | undefined;
    designId?: string | undefined;
  }) {
    return api.post<ScaffoldUnitResponse>('/ai/scaffold-unit', data);
  },

  /** Generate content to fill a specific gap. */
  fillGap(data: {
    unitId: string;
    gapType: string;
    context?: string;
    designId?: string;
  }) {
    return api.post<FillGapResponse>('/ai/fill-gap', data);
  },

  /** Draft speaker notes for the selected slides of a material. */
  generateSpeakerNotes(materialId: string, slideIndices: number[]) {
    return api.post<GenerateSpeakerNotesResponse>(
      `/ai/materials/${materialId}/generate-speaker-notes`,
      { slideIndices }
    );
  },

  /** Recover structure (headings, lists) from a material's plain content. */
  restructureContent(materialId: string) {
    return api.post<RestructureContentResponse>(
      `/ai/materials/${materialId}/restructure`,
      {}
    );
  },
};
