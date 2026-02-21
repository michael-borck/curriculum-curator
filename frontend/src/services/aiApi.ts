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
};
