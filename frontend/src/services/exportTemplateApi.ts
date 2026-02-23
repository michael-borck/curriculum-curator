import api from './api';
import type { AxiosResponse } from 'axios';

export interface TemplateInfo {
  id: string;
  filename: string;
  format: string;
  uploadedAt: string;
  isDefault: boolean;
}

export interface TemplateListResponse {
  templates: TemplateInfo[];
  defaults: Record<string, string | null>;
}

export const exportTemplateApi = {
  list: (): Promise<AxiosResponse<TemplateListResponse>> =>
    api.get('/export-templates'),

  upload: (file: File): Promise<AxiosResponse<TemplateInfo>> => {
    const form = new FormData();
    form.append('file', file);
    return api.post('/export-templates/upload', form);
  },

  remove: (id: string): Promise<AxiosResponse<void>> =>
    api.delete(`/export-templates/${id}`),

  setDefault: (id: string): Promise<AxiosResponse<TemplateInfo>> =>
    api.put(`/export-templates/${id}/default`),
};
