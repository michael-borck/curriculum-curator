/**
 * API client for the export preview and package export endpoints.
 */

import axios from 'axios';

// ─── Types ───────────────────────────────────────────────────────────

export interface MaterialExportPreview {
  materialId: string;
  title: string;
  weekNumber: number;
  category: string;
  contentTypes: string[];
  resolvedTargets: Record<string, string[]>;
  availableTargets: Record<string, string[]>;
}

export interface ExportPreviewResponse {
  materials: MaterialExportPreview[];
}

export interface MaterialTargetOverride {
  materialId: string;
  targets: Record<string, string[]>;
}

export interface ExportPackageRequest {
  packageType: string;
  targetLms: string;
  materialTargets: MaterialTargetOverride[];
}

// ─── API functions ───────────────────────────────────────────────────

const getAuthHeaders = () => {
  const token = localStorage.getItem('token');
  return token ? { Authorization: `Bearer ${token}` } : {};
};

export async function fetchExportPreview(
  unitId: string
): Promise<ExportPreviewResponse> {
  const { data } = await axios.get<ExportPreviewResponse>(
    `/api/units/${unitId}/export/preview`,
    { headers: getAuthHeaders() }
  );
  return data;
}

/**
 * Kick off an async background export. Returns the task_id
 * which can be tracked via SSE at /api/bg-tasks/{id}/events.
 */
export async function startPackageExport(
  unitId: string,
  request: ExportPackageRequest
): Promise<string> {
  const { data } = await axios.post<{ taskId: string }>(
    `/api/units/${unitId}/export/package`,
    request,
    {
      headers: {
        ...getAuthHeaders(),
        'Content-Type': 'application/json',
      },
    }
  );
  return data.taskId;
}
