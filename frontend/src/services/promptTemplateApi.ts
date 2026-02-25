import api from './api';

export interface TemplateVariable {
  name: string;
  label: string;
  default?: string | null;
}

export interface PromptTemplate {
  id: string;
  name: string;
  description?: string | null;
  type: string;
  isSystem: boolean;
  isPublic: boolean;
  usageCount: number;
  variables?: TemplateVariable[] | null;
  tags?: string[] | null;
}

export interface PromptTemplateDetail extends PromptTemplate {
  templateContent: string;
  status: string;
  ownerId?: string | null;
  version: number;
  lastUsed?: string | null;
  createdAt: string;
  updatedAt?: string | null;
}

export const promptTemplateApi = {
  list: async (type?: string): Promise<PromptTemplate[]> => {
    const response = await api.get('/prompt-templates', {
      params: type ? { type } : undefined,
    });
    return response.data;
  },

  get: async (id: string): Promise<PromptTemplateDetail> => {
    const response = await api.get(`/prompt-templates/${id}`);
    return response.data;
  },

  incrementUsage: async (id: string): Promise<void> => {
    await api.post(`/prompt-templates/${id}/increment-usage`);
  },

  create: async (
    data: Omit<
      PromptTemplateDetail,
      'id' | 'isSystem' | 'isPublic' | 'usageCount' | 'version' | 'createdAt'
    >
  ): Promise<PromptTemplateDetail> => {
    const response = await api.post('/prompt-templates', data);
    return response.data;
  },

  copy: async (id: string): Promise<PromptTemplateDetail> => {
    const response = await api.post(`/prompt-templates/${id}/copy`);
    return response.data;
  },

  update: async (
    id: string,
    data: Partial<PromptTemplateDetail>
  ): Promise<PromptTemplateDetail> => {
    const response = await api.put(`/prompt-templates/${id}`, data);
    return response.data;
  },

  delete: async (id: string): Promise<void> => {
    await api.delete(`/prompt-templates/${id}`);
  },

  toggleVisibility: async (id: string): Promise<{ hidden: boolean }> => {
    const response = await api.post(
      `/prompt-templates/${id}/toggle-visibility`
    );
    return response.data;
  },
};
