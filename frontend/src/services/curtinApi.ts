import api from './api';

// =============================================================================
// Curtin Integration Types
// =============================================================================

export interface CurtinSettings {
  curtinUsername: string;
  curtinPassword: string;
  litecUrl: string;
  blackboardUrl: string;
  campus: string;
}

export interface CurtinJobResponse {
  id: string;
  courseName: string;
  status: string;
  triggeredAt: string;
  errorMessage: string | null;
}

// =============================================================================
// Settings Management
// =============================================================================

export const getCurtinSettings = async (): Promise<CurtinSettings> => {
  const res = await api.get<CurtinSettings>('/curtin/settings');
  return res.data;
};

export const saveCurtinSettings = async (
  settings: CurtinSettings
): Promise<CurtinSettings> => {
  const res = await api.put<CurtinSettings>('/curtin/settings', settings);
  return res.data;
};

// =============================================================================
// Content Download & Processing
// =============================================================================

export const downloadOutline = async (
  unitCode: string
): Promise<{ filename: string; data: ArrayBuffer }> => {
  const res = await api.post(
    '/curtin/outline/download',
    { unitCode },
    { responseType: 'arraybuffer' }
  );

  // Extract filename from Content-Disposition header
  const contentDisposition = res.headers['content-disposition'] || '';
  let filename = 'outline.pdf';

  if (contentDisposition) {
    const match = contentDisposition.match(
      /filename[^;=\n]*=(?:(['"]).*?\1|[^;\n]*)/
    );
    if (match?.[0]) {
      filename = match[0].split('=')[1].replace(/['"]/g, '').trim();
    }
  }

  return {
    filename,
    data: res.data,
  };
};

// =============================================================================
// Course Build & Management
// =============================================================================

export const triggerCourseBuild = async (
  courseName: string
): Promise<CurtinJobResponse> => {
  const res = await api.post<CurtinJobResponse>('/curtin/course/build', {
    courseName,
  });
  return res.data;
};

export const listCourseJobs = async (): Promise<CurtinJobResponse[]> => {
  const res = await api.get<CurtinJobResponse[]>('/curtin/course/jobs');
  return res.data;
};

interface NotReadyError {
  notReady: true;
}

export const downloadCourseArchive = async (
  jobId: string
): Promise<{ filename: string; data: ArrayBuffer }> => {
  try {
    const res = await api.post(
      `/curtin/course/download/${jobId}`,
      {},
      { responseType: 'arraybuffer' }
    );

    // Extract filename from Content-Disposition header
    const contentDisposition = res.headers['content-disposition'] || '';
    let filename = 'course-archive.zip';

    if (contentDisposition) {
      const match = contentDisposition.match(
        /filename[^;=\n]*=(?:(['"]).*?\1|[^;\n]*)/
      );
      if (match?.[0]) {
        filename = match[0].split('=')[1].replace(/['"]/g, '').trim();
      }
    }

    return {
      filename,
      data: res.data,
    };
  } catch (error) {
    // Check if this is a 409 Not Ready error
    if (
      error instanceof Error &&
      'response' in error &&
      error.response instanceof Object &&
      'status' in error.response &&
      error.response.status === 409
    ) {
      throw { notReady: true } as NotReadyError;
    }
    throw error;
  }
};
