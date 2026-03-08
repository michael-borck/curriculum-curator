import api from './api';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface ParserInfo {
  id: string;
  displayName: string;
  description: string;
  supportedFormats: string[];
}

export interface OutlineULO {
  code: string;
  description: string;
  bloomLevel: string;
}

export interface OutlineWeek {
  weekNumber: number;
  topic: string;
  activities: string[];
  readings: string[];
}

export interface OutlineAssessment {
  title: string;
  category: string;
  weight: number;
  dueWeek: number | null;
  description: string;
}

export interface OutlineTextbook {
  title: string;
  authors: string;
  isbn: string;
  required: boolean;
}

export interface OutlineSnippet {
  heading: string;
  content: string;
  keep: boolean;
}

export interface OutlineParseResponse {
  unitCode: string | null;
  unitTitle: string | null;
  description: string | null;
  creditPoints: number | null;
  durationWeeks: number | null;
  year: number | null;
  semester: string | null;
  prerequisites: string | null;
  deliveryMode: string | null;
  teachingPattern: string | null;
  learningOutcomes: OutlineULO[];
  weeklySchedule: OutlineWeek[];
  assessments: OutlineAssessment[];
  textbooks: OutlineTextbook[];
  supplementaryInfo: OutlineSnippet[];
  confidence: number;
  parserUsed: string;
  warnings: string[];
}

export interface OutlineApplyRequest {
  unitCode: string;
  unitTitle: string;
  description: string;
  creditPoints: number;
  durationWeeks: number;
  year: number | null;
  semester: string | null;
  prerequisites: string;
  deliveryMode: string;
  teachingPattern: string;
  pedagogyType: string;
  learningOutcomes: OutlineULO[];
  weeklySchedule: OutlineWeek[];
  assessments: OutlineAssessment[];
  textbooks: OutlineTextbook[];
  supplementaryInfo: OutlineSnippet[];
  parserUsed: string;
}

export interface OutlineApplyResponse {
  unitId: string;
  title: string;
  code: string;
  ulosCreated: number;
  weeksCreated: number;
  assessmentsCreated: number;
}

// ---------------------------------------------------------------------------
// API calls
// ---------------------------------------------------------------------------

export const listParsers = async (): Promise<ParserInfo[]> => {
  const res = await api.get('/import/outline/parsers');
  return res.data;
};

export const parseOutline = async (
  file: File,
  parserId: string = 'generic'
): Promise<OutlineParseResponse> => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('parser_id', parserId);
  const res = await api.post('/import/outline/parse', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 120_000, // LLM parsing can take a while
  });
  return res.data;
};

export const applyOutline = async (
  request: OutlineApplyRequest
): Promise<OutlineApplyResponse> => {
  const res = await api.post('/import/outline/apply', request);
  return res.data;
};
