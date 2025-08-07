import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Auth endpoints
export const login = (email, password) =>
  api.post('/api/auth/login', { email, password });

export const register = (email, password, name) =>
  api.post('/api/auth/register', { email, password, name });

// Content endpoints
export const generateContent = (type, pedagogy, context) =>
  api.post('/api/llm/generate', { 
    content_type: type, 
    pedagogy_style: pedagogy, 
    context 
  });

export const enhanceContent = (content, pedagogy) =>
  api.post('/api/llm/enhance', { content, pedagogy_style: pedagogy });

// Course endpoints
export const getCourses = () => api.get('/api/courses');
export const getCourse = (id) => api.get(`/api/courses/${id}`);
export const createCourse = (data) => api.post('/api/courses', data);
export const updateCourse = (id, data) => api.put(`/api/courses/${id}`, data);

// File upload
export const uploadFile = (file) => {
  const formData = new FormData();
  formData.append('file', file);
  return api.post('/api/content/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
};

export default api;