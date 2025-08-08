import axios, { InternalAxiosRequestConfig } from 'axios';
import type {
  ApiResponse,
  Course,
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

// Course endpoints
export const getCourses = (): Promise<ApiResponse<Course[]>> =>
  api.get('/api/courses');
export const getCourse = (id: string): Promise<ApiResponse<Course>> =>
  api.get(`/api/courses/${id}`);
export const createCourse = (
  data: Partial<Course>
): Promise<ApiResponse<Course>> => api.post('/api/courses', data);
export const updateCourse = (
  id: string,
  data: Partial<Course>
): Promise<ApiResponse<Course>> => api.put(`/api/courses/${id}`, data);

// File upload
export const uploadFile = (file: File): Promise<ApiResponse> => {
  const formData = new FormData();
  formData.append('file', file);
  return api.post('/api/content/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
};

export default api;
