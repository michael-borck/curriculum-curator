/**
 * Structured material import API client.
 *
 * Wraps the Mode A endpoints from docs/structured-import-plan.md Phase 1:
 * single file → existing unit. PPTX is the only supported format in this
 * phase. Other formats and Modes B/C ship in later phases.
 *
 * Form fields use snake_case on the wire (Python/FastAPI convention);
 * response bodies are camelCase via the backend's CamelModel base.
 */

import api from './api';

// ---------------------------------------------------------------------------
// Types — match the camelCase response bodies from material_import.py
// ---------------------------------------------------------------------------

export interface ParserInfo {
  id: string;
  displayName: string;
  description: string;
  supportedFormats: string[];
  requiresAi: boolean;
  isDefault: boolean;
}

export interface ParserListResponse {
  parsers: ParserInfo[];
}

/**
 * Result of /single/preview — the parser's structured output without
 * any database write. The user reviews this before deciding to apply.
 */
export interface MaterialPreviewResponse {
  parserUsed: string;
  title: string;
  contentJson: Record<string, unknown>;
  imageCount: number;
  warnings: string[];
  confidence: number;
}

/**
 * Result of /single/apply — the persisted material's identifiers plus
 * the warnings the parser surfaced (so the UI can show them after the
 * import completes, not just at preview time).
 */
export interface MaterialApplyResponse {
  materialId: string;
  unitId: string;
  weekNumber: number;
  title: string;
  parserUsed: string;
  imageCount: number;
  warnings: string[];
}

export interface ApplySingleParams {
  file: File;
  unitId: string;
  weekNumber: number;
  // Optional fields use `T | undefined` because the project enables
  // exactOptionalPropertyTypes — `field?: T` would forbid passing undefined
  parserId?: string | undefined;
  titleOverride?: string | undefined;
  category?: string | undefined;
  type?: string | undefined;
}

// ---------------------------------------------------------------------------
// API calls
// ---------------------------------------------------------------------------

export const listMaterialParsers = async (
  format?: string
): Promise<ParserInfo[]> => {
  const params = format ? { format } : undefined;
  const res = await api.get<ParserListResponse>('/import/material/parsers', {
    params,
  });
  return res.data.parsers;
};

export const previewSingleMaterial = async (
  file: File,
  unitId: string,
  parserId?: string
): Promise<MaterialPreviewResponse> => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('unit_id', unitId);
  if (parserId) {
    formData.append('parser_id', parserId);
  }
  const res = await api.post<MaterialPreviewResponse>(
    '/import/material/single/preview',
    formData,
    {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 60_000,
    }
  );
  return res.data;
};

export const applySingleMaterial = async (
  params: ApplySingleParams
): Promise<MaterialApplyResponse> => {
  const formData = new FormData();
  formData.append('file', params.file);
  formData.append('unit_id', params.unitId);
  formData.append('week_number', String(params.weekNumber));
  if (params.parserId) {
    formData.append('parser_id', params.parserId);
  }
  if (params.titleOverride) {
    formData.append('title_override', params.titleOverride);
  }
  if (params.category) {
    formData.append('category', params.category);
  }
  if (params.type) {
    formData.append('type', params.type);
  }
  const res = await api.post<MaterialApplyResponse>(
    '/import/material/single/apply',
    formData,
    {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 120_000,
    }
  );
  return res.data;
};
