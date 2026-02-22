import axios, { InternalAxiosRequestConfig } from 'axios';
import type {
  ApiResponse,
  Unit,
  UnitListResponse,
  PedagogyType,
  ContentType,
  VisualPromptRequest,
  VisualPromptResponse,
} from '../types/index';

// Same origin - backend serves both API and frontend
const API_BASE_URL = '/api';

const api = axios.create({
  baseURL: API_BASE_URL,
});

// Add auth token to requests
api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = localStorage.getItem('token');

  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  // Don't set Content-Type - let axios handle it based on the data type
  // axios will automatically set:
  // - application/json for objects
  // - application/x-www-form-urlencoded for URLSearchParams
  // - multipart/form-data for FormData

  return config;
});

// Handle 401 responses - clear token and redirect to login
api.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 401) {
      // Token is invalid or expired
      localStorage.removeItem('token');
      // Let the component handle the redirect via auth store
    }
    return Promise.reject(error);
  }
);

// Auth endpoints - now using simple JSON
export const login = (email: string, password: string): Promise<ApiResponse> =>
  api.post('/auth/login', { email, password });

export const register = (
  email: string,
  password: string,
  name: string
): Promise<ApiResponse> =>
  api.post('/auth/register', { email, password, name });

// Content endpoints (AI-powered)
export const generateContent = (
  type: ContentType,
  pedagogy: PedagogyType,
  topic: string,
  opts?: {
    unitId?: string | undefined;
    designId?: string | undefined;
    pedagogyOverride?: string | undefined;
  }
): Promise<ApiResponse> =>
  api.post('/ai/generate', {
    content_type: type,
    pedagogy_style: pedagogy,
    topic,
    unit_id: opts?.unitId,
    design_id: opts?.designId,
    pedagogy_override: opts?.pedagogyOverride,
  });

export const enhanceContent = (
  content: string,
  pedagogy: PedagogyType,
  opts?: { unitId?: string | undefined; designId?: string | undefined }
): Promise<ApiResponse> =>
  api.post('/ai/enhance', {
    content,
    enhancement_type: 'improve',
    pedagogy_style: pedagogy,
    unit_id: opts?.unitId,
    design_id: opts?.designId,
  });

// Unit endpoints
export const getUnits = (): Promise<ApiResponse<UnitListResponse>> =>
  api.get('/units');
export const getUnit = (id: string): Promise<ApiResponse<Unit>> =>
  api.get(`/units/${id}`);

// Backwards compatibility aliases
export const getCourses = getUnits;
export const getCourse = getUnit;
export const createUnit = (data: Partial<Unit>): Promise<ApiResponse<Unit>> =>
  api.post('/units/create', data);
export const updateUnit = (
  id: string,
  data: Partial<Unit>
): Promise<ApiResponse<Unit>> => api.put(`/units/${id}`, data);

export const deleteUnit = (
  id: string,
  permanent = false
): Promise<ApiResponse> =>
  api.delete(`/units/${id}`, { params: { permanent } });

export const restoreUnit = (id: string): Promise<ApiResponse<Unit>> =>
  api.post(`/units/${id}/restore`);

export const getArchivedUnits = (): Promise<ApiResponse<UnitListResponse>> =>
  api.get('/units/archived');

// Content management - routes are nested under /units/{unitId}/content
export const getUnitContents = (unitId: string): Promise<ApiResponse> =>
  api.get(`/units/${unitId}/content`);

export const getContent = (
  unitId: string,
  contentId: string
): Promise<ApiResponse> => api.get(`/units/${unitId}/content/${contentId}`);

export const createContent = (
  unitId: string,
  data: {
    title: string;
    contentType: string;
    body?: string;
    summary?: string;
    weekNumber?: number;
    estimatedDurationMinutes?: number;
  }
): Promise<ApiResponse> => api.post(`/units/${unitId}/content`, data);

export const updateContent = (
  unitId: string,
  contentId: string,
  data: {
    title?: string;
    body?: string;
    summary?: string;
    weekNumber?: number;
    estimatedDurationMinutes?: number;
  }
): Promise<ApiResponse> =>
  api.put(`/units/${unitId}/content/${contentId}`, data);

export const deleteContent = (
  unitId: string,
  contentId: string
): Promise<ApiResponse> => api.delete(`/units/${unitId}/content/${contentId}`);

// Legacy alias for backwards compatibility (deprecated)
export const getContents = getUnitContents;

// File upload
export const uploadFile = (
  unitId: string,
  file: File
): Promise<ApiResponse> => {
  const formData = new FormData();
  formData.append('file', file);
  return api.post(`/units/${unitId}/content/upload`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
};

// Streaming content generation
export const generateContentStream = async (
  type: ContentType,
  pedagogy: PedagogyType,
  topic: string,
  onChunk: (chunk: string) => void,
  onComplete?: () => void,
  onError?: (error: Error) => void,
  opts?: {
    unitId?: string | undefined;
    designId?: string | undefined;
    pedagogyOverride?: string | undefined;
  }
): Promise<void> => {
  const token = localStorage.getItem('token');

  try {
    const response = await window.fetch(`${API_BASE_URL}/ai/generate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({
        content_type: type,
        pedagogy_style: pedagogy,
        topic,
        stream: true,
        unit_id: opts?.unitId,
        design_id: opts?.designId,
        pedagogy_override: opts?.pedagogyOverride,
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const reader = response.body?.getReader();
    if (!reader) {
      throw new Error('No response body');
    }

    const decoder = new TextDecoder();

    // eslint-disable-next-line no-constant-condition
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const text = decoder.decode(value, { stream: true });
      // Parse SSE data
      const lines = text.split('\n');
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6));
            if (data.content) {
              onChunk(data.content);
            }
          } catch {
            // Skip invalid JSON
          }
        }
      }
    }

    onComplete?.();
  } catch (error) {
    onError?.(error instanceof Error ? error : new Error('Stream failed'));
  }
};

// Visual prompt generation
export const generateVisualPrompt = async (
  req: VisualPromptRequest
): Promise<VisualPromptResponse> => {
  const { data } = await api.post<VisualPromptResponse>(
    '/ai/visual-prompt',
    req
  );
  return data;
};

// Content validation
export const validateContent = (
  content: string,
  validationTypes: string[] = ['readability', 'structure']
): Promise<ApiResponse> =>
  api.post('/ai/validate', {
    content,
    validationTypes,
  });

// Content remediation (streaming)
export const remediateContentStream = async (
  content: string,
  remediationType: string,
  customPrompt?: string,
  onChunk: (chunk: string) => void = () => {},
  onComplete?: () => void,
  onError?: (error: Error) => void
): Promise<void> => {
  const token = localStorage.getItem('token');

  try {
    const response = await window.fetch(`${API_BASE_URL}/ai/remediate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({
        content,
        remediationType,
        customPrompt,
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const reader = response.body?.getReader();
    if (!reader) {
      throw new Error('No response body');
    }

    const decoder = new TextDecoder();

    // eslint-disable-next-line no-constant-condition
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const text = decoder.decode(value, { stream: true });
      const lines = text.split('\n');
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6));
            if (data.content) {
              onChunk(data.content);
            }
          } catch {
            // Skip invalid JSON
          }
        }
      }
    }

    onComplete?.();
  } catch (error) {
    onError?.(error instanceof Error ? error : new Error('Remediation failed'));
  }
};

// Plugin endpoints
export interface PluginInfo {
  name: string;
  description: string;
  pluginType: string;
  enabled: boolean;
  priority: number;
}

export interface PluginResultData {
  success: boolean;
  message: string;
  data?: Record<string, unknown>;
  suggestions?: string[];
}

export interface PluginValidateResponse {
  results: Record<string, PluginResultData>;
  overallScore: number;
}

export interface PluginRemediateResponse {
  content: string;
  results: Record<string, PluginResultData>;
  changesMade: string[];
}

export const getPlugins = (): Promise<ApiResponse<{ plugins: PluginInfo[] }>> =>
  api.get('/plugins');

export const runPluginValidation = (
  content: string,
  validators?: string[]
): Promise<ApiResponse<PluginValidateResponse>> =>
  api.post('/plugins/validate', { content, validators: validators ?? null });

export const runPluginRemediation = (
  content: string,
  remediators?: string[]
): Promise<ApiResponse<PluginRemediateResponse>> =>
  api.post('/plugins/remediate', { content, remediators: remediators ?? null });

export const updatePluginConfig = (
  name: string,
  config: {
    enabled?: boolean;
    priority?: number;
    config?: Record<string, unknown>;
  }
): Promise<ApiResponse<PluginInfo>> => api.patch(`/plugins/${name}`, config);

// Material image endpoints
export const uploadMaterialImage = (
  unitId: string,
  materialId: string,
  file: File
): Promise<ApiResponse<{ url: string; filename: string }>> => {
  const formData = new FormData();
  formData.append('file', file);
  return api.post(
    `/materials/units/${unitId}/materials/${materialId}/images`,
    formData,
    { headers: { 'Content-Type': 'multipart/form-data' } }
  );
};

export const listMaterialImages = (
  unitId: string,
  materialId: string
): Promise<ApiResponse<{ filename: string; url: string }[]>> =>
  api.get(`/materials/units/${unitId}/materials/${materialId}/images`);

export const deleteMaterialImage = (
  unitId: string,
  materialId: string,
  filename: string
): Promise<ApiResponse<void>> =>
  api.delete(
    `/materials/units/${unitId}/materials/${materialId}/images/${filename}`
  );

export default api;
export { api };
