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

export async function downloadPackageExport(
  unitId: string,
  request: ExportPackageRequest
): Promise<string> {
  const response = await axios.post(
    `/api/units/${unitId}/export/package`,
    request,
    {
      responseType: 'blob',
      headers: {
        ...getAuthHeaders(),
        'Content-Type': 'application/json',
      },
    }
  );

  const disposition = response.headers['content-disposition'] as
    | string
    | undefined;
  const filenameMatch = disposition?.match(/filename="?([^"]+)"?/);
  const filename = filenameMatch?.[1] ?? 'export.zip';

  const url = URL.createObjectURL(response.data as Blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  URL.revokeObjectURL(url);
  a.remove();

  return filename;
}
