import axios, { InternalAxiosRequestConfig } from 'axios';
import type {
  ApiResponse,
  Unit,
  UnitListResponse,
  PedagogyType,
  ContentType,
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
  topic: string
): Promise<ApiResponse> =>
  api.post('/ai/generate', {
    content_type: type,
    pedagogy_style: pedagogy,
    topic,
  });

export const enhanceContent = (
  content: string,
  pedagogy: PedagogyType
): Promise<ApiResponse> =>
  api.post('/ai/enhance', {
    content,
    enhancement_type: 'improve',
    pedagogy_style: pedagogy,
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
export const uploadFile = (file: File): Promise<ApiResponse> => {
  const formData = new FormData();
  formData.append('file', file);
  return api.post('/content/upload', formData, {
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
  onError?: (error: Error) => void
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

export default api;
export { api };
