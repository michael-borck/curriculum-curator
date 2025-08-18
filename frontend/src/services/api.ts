import axios, { InternalAxiosRequestConfig } from 'axios';
import type {
  ApiResponse,
  Unit,
  PedagogyType,
  ContentType,
} from '../types/index';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = localStorage.getItem('token');
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Auth endpoints
export const login = (email: string, password: string): Promise<ApiResponse> =>
  api.post('/api/auth/login', { email, password });

export const register = (
  email: string,
  password: string,
  name: string
): Promise<ApiResponse> =>
  api.post('/api/auth/register', { email, password, name });

// Content endpoints
export const generateContent = (
  type: ContentType,
  pedagogy: PedagogyType,
  context: string
): Promise<ApiResponse> =>
  api.post('/api/llm/generate', {
    content_type: type,
    pedagogy_style: pedagogy,
    context,
  });

export const enhanceContent = (
  content: string,
  pedagogy: PedagogyType
): Promise<ApiResponse> =>
  api.post('/api/llm/enhance', { content, pedagogy_style: pedagogy });

// Unit endpoints
export const getUnits = (): Promise<ApiResponse<Unit[]>> =>
  api.get('/api/units');
export const getUnit = (id: string): Promise<ApiResponse<Unit>> =>
  api.get(`/api/units/${id}`);

// Backwards compatibility aliases
export const getCourses = getUnits;
export const getCourse = getUnit;
export const createUnit = (data: Partial<Unit>): Promise<ApiResponse<Unit>> =>
  api.post('/api/units', data);
export const updateUnit = (
  id: string,
  data: Partial<Unit>
): Promise<ApiResponse<Unit>> => api.put(`/api/units/${id}`, data);

// File upload
export const uploadFile = (file: File): Promise<ApiResponse> => {
  const formData = new FormData();
  formData.append('file', file);
  return api.post('/api/content/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
};

export default api;
export { api };
