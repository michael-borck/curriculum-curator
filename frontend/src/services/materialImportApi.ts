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

// ---------------------------------------------------------------------------
// Mode B — multi-file zip → existing unit (multi-format grouping)
// ---------------------------------------------------------------------------

export interface BatchGroupSourceFile {
  path: string;
  filename: string;
  fileFormat: string;
}

/** One multi-format group: a canonical file plus its attached source files. */
export interface BatchGroupPreview {
  name: string;
  directory: string;
  detectedWeek: number | null;
  canonicalPath: string;
  canonicalFilename: string;
  canonicalFormat: string;
  parser: string;
  sourceFiles: BatchGroupSourceFile[];
}

/** A single-format file imported as its own material. */
export interface BatchStandaloneFile {
  path: string;
  filename: string;
  fileFormat: string;
  detectedWeek: number | null;
  parser: string;
}

export interface BatchPreviewResponse {
  unitId: string;
  groups: BatchGroupPreview[];
  standaloneFiles: BatchStandaloneFile[];
  warnings: string[];
  totalMaterials: number;
  totalSourceFiles: number;
}

/** Per-group override applied at apply time, keyed by group name. */
export interface BatchGroupOverride {
  name: string;
  canonicalFilename?: string | undefined;
  weekNumber?: number | undefined;
}

export interface BatchStatusResponse {
  taskId: string;
  status: string;
  totalFiles: number;
  processedFiles: number;
  currentFile: string | null;
  unitId: string | null;
  errors: string[];
}

export const previewBatchMaterials = async (
  file: File,
  unitId: string
): Promise<BatchPreviewResponse> => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('unit_id', unitId);
  const res = await api.post<BatchPreviewResponse>(
    '/import/material/batch/preview',
    formData,
    {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 120_000,
    }
  );
  return res.data;
};

export const applyBatchMaterials = async (
  file: File,
  unitId: string,
  overrides?: BatchGroupOverride[]
): Promise<string> => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('unit_id', unitId);
  if (overrides && overrides.length > 0) {
    formData.append('overrides', JSON.stringify(overrides));
  }
  const res = await api.post<{ taskId: string }>(
    '/import/material/batch/apply',
    formData,
    {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 120_000,
    }
  );
  return res.data.taskId;
};

export const getBatchStatus = async (
  taskId: string
): Promise<BatchStatusResponse> => {
  const res = await api.get<BatchStatusResponse>(
    `/import/material/batch/status/${taskId}`
  );
  return res.data;
};

// ---------------------------------------------------------------------------
// Attached source files (download + promote to canonical)
// ---------------------------------------------------------------------------

export interface AttachedSourceFile {
  filename: string;
  // Backend records snake_case keys inside material_metadata JSON, which is
  // passed through untransformed — accept both spellings defensively.
  fileFormat?: string | undefined;
  file_format?: string | undefined;
  originalSize?: number | undefined;
  original_size?: number | undefined;
  sha256?: string | undefined;
}

export const downloadSourceFile = async (
  materialId: string,
  filename: string
): Promise<void> => {
  const res = await api.get(
    `/materials/${materialId}/source-files/${encodeURIComponent(filename)}`,
    { responseType: 'blob' }
  );
  const url = URL.createObjectURL(res.data as Blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  URL.revokeObjectURL(url);
  a.remove();
};

export const promoteSourceFile = async (
  materialId: string,
  filename: string
): Promise<void> => {
  await api.post(
    `/materials/${materialId}/source-files/${encodeURIComponent(filename)}/promote`
  );
};
