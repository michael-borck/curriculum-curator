import axios, { InternalAxiosRequestConfig } from 'axios';
import type {
  ApiResponse,
  Unit,
  PedagogyType,
  ContentType,
} from '../types/index';

// Use environment variable for API URL
// In production (Docker), VITE_API_URL is set to empty string, so we use /api
// In development, we use localhost:8000/api
const API_BASE_URL = import.meta.env.VITE_API_URL !== undefined 
  ? (import.meta.env.VITE_API_URL || '/api')  // Empty string in Docker means use /api
  : 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
});

// Add auth token to requests
api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = localStorage.getItem('token');
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  
  // Debug logging for login endpoint
  if (config.url?.includes('/auth/login')) {
    console.log('Login request config:', {
      url: config.url,
      method: config.method,
      headers: config.headers,
      data: config.data,
      dataType: typeof config.data,
      contentType: config.headers?.['Content-Type'],
    });
  }
  
  // Don't override Content-Type if it's already set
  // This is important for form-encoded requests
  if (config.headers && config.headers['Content-Type']) {
    // Content-Type is already set, don't change it
    return config;
  }
  
  // Only set Content-Type to JSON if:
  // 1. No Content-Type is set AND
  // 2. We have data to send AND  
  // 3. The data is not FormData, URLSearchParams, or a URL-encoded string
  if (config.headers && config.data) {
    const isFormData = config.data instanceof FormData;
    const isURLSearchParams = config.data instanceof URLSearchParams;
    const isURLEncodedString = typeof config.data === 'string' && config.data.includes('=');
    
    if (!isFormData && !isURLSearchParams && !isURLEncodedString) {
      config.headers['Content-Type'] = 'application/json';
    }
  }
  
  return config;
});

// Auth endpoints - Note: backend expects 'username' for login (not 'email')
export const login = (email: string, password: string): Promise<ApiResponse> => {
  // Create form data
  const params = new URLSearchParams();
  params.append('username', email);
  params.append('password', password);
  
  console.log('Login params:', params.toString());
  
  // Send with explicit headers to ensure they're not overridden
  return api.post('/auth/login', params.toString(), {
    headers: { 
      'Content-Type': 'application/x-www-form-urlencoded'
    }
  });
};

export const register = (
  email: string,
  password: string,
  name: string
): Promise<ApiResponse> =>
  api.post('/auth/register', { email, password, name });

// Content endpoints
export const generateContent = (
  type: ContentType,
  pedagogy: PedagogyType,
  context: string
): Promise<ApiResponse> =>
  api.post('/llm/generate', {
    content_type: type,
    pedagogy_style: pedagogy,
    context,
  });

export const enhanceContent = (
  content: string,
  pedagogy: PedagogyType
): Promise<ApiResponse> =>
  api.post('/llm/enhance', { content, pedagogy_style: pedagogy });

// Unit endpoints
export const getUnits = (): Promise<ApiResponse<Unit[]>> =>
  api.get('/units');
export const getUnit = (id: string): Promise<ApiResponse<Unit>> =>
  api.get(`/api/units/${id}`);

// Backwards compatibility aliases
export const getCourses = getUnits;
export const getCourse = getUnit;
export const createUnit = (data: Partial<Unit>): Promise<ApiResponse<Unit>> =>
  api.post('/units', data);
export const updateUnit = (
  id: string,
  data: Partial<Unit>
): Promise<ApiResponse<Unit>> => api.put(`/api/units/${id}`, data);

// File upload
export const uploadFile = (file: File): Promise<ApiResponse> => {
  const formData = new FormData();
  formData.append('file', file);
  return api.post('/content/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
};

export default api;
export { api };
