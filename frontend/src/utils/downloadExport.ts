import axios from 'axios';

/**
 * Downloads an export file from the backend and triggers a browser download.
 * Returns the filename for use in toast messages.
 */
export async function downloadExport(
  unitId: string,
  format: string,
  targetLms?: string | undefined
): Promise<string> {
  const token = localStorage.getItem('token');
  const lmsParam =
    format !== 'html' && targetLms && targetLms !== 'generic'
      ? `?target_lms=${targetLms}`
      : '';

  const response = await axios.get(
    `/api/units/${unitId}/export/${format}${lmsParam}`,
    {
      responseType: 'blob',
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    }
  );

  const disposition = response.headers['content-disposition'] as
    | string
    | undefined;
  const filenameMatch = disposition?.match(/filename="?([^"]+)"?/);
  const fallbackMap: Record<string, string> = {
    imscc: 'export.imscc',
    scorm: 'export.zip',
    html: 'export.html',
    qti: 'export_qti.zip',
    h5p: 'export_quiz.h5p',
  };
  const filename = filenameMatch?.[1] ?? fallbackMap[format] ?? 'export.bin';

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

/**
 * Downloads a materials ZIP export.
 */
export async function downloadMaterialsExport(
  unitId: string,
  format: 'html' | 'pdf' | 'docx' | 'pptx'
): Promise<string> {
  const token = localStorage.getItem('token');

  const response = await axios.get(
    `/api/units/${unitId}/export/materials?format=${format}`,
    {
      responseType: 'blob',
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    }
  );

  const disposition = response.headers['content-disposition'] as
    | string
    | undefined;
  const filenameMatch = disposition?.match(/filename="?([^"]+)"?/);
  const filename = filenameMatch?.[1] ?? 'materials.zip';

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
