/**
 * API service functions for Weekly Materials management
 */

import api from './api';
import type { ApiResponse } from '../types/index';
import type {
  MaterialCreate,
  MaterialUpdate,
  MaterialResponse,
  MaterialWithOutcomes,
  MaterialFilter,
  WeekMaterials,
} from '../types/unitStructure';

export const materialsApi = {
  createMaterial: async (
    unitId: string,
    data: MaterialCreate
  ): Promise<MaterialResponse> => {
    const response = await api.post(
      `/materials/units/${unitId}/materials`,
      data
    );
    return response.data;
  },

  getMaterialsByUnit: async (
    unitId: string,
    filter?: MaterialFilter
  ): Promise<MaterialResponse[]> => {
    const response = await api.get(`/materials/units/${unitId}/materials`, {
      params: filter,
    });
    return response.data;
  },

  getMaterialsByWeek: async (
    unitId: string,
    weekNumber: number
  ): Promise<WeekMaterials> => {
    const response = await api.get(
      `/materials/units/${unitId}/weeks/${weekNumber}/materials`
    );
    return response.data;
  },

  getMaterial: async (
    materialId: string,
    includeOutcomes = false
  ): Promise<MaterialWithOutcomes> => {
    const response = await api.get(`/materials/materials/${materialId}`, {
      params: { include_outcomes: includeOutcomes },
    });
    return response.data;
  },

  updateMaterial: async (
    materialId: string,
    data: MaterialUpdate
  ): Promise<MaterialResponse> => {
    const response = await api.put(`/materials/materials/${materialId}`, data);
    return response.data;
  },

  deleteMaterial: async (materialId: string): Promise<void> => {
    await api.delete(`/materials/materials/${materialId}`);
  },

  duplicateMaterial: async (
    materialId: string,
    targetWeek: number
  ): Promise<MaterialResponse> => {
    const response = await api.post(
      `/materials/materials/${materialId}/duplicate`,
      {
        targetWeek,
      }
    );
    return response.data;
  },

  reorderMaterials: async (
    unitId: string,
    weekNumber: number,
    materialIds: string[]
  ): Promise<MaterialResponse[]> => {
    const response = await api.post(
      `/materials/units/${unitId}/weeks/${weekNumber}/materials/reorder`,
      { materialIds }
    );
    return response.data;
  },

  updateMaterialMappings: async (
    materialId: string,
    uloIds: string[]
  ): Promise<MaterialWithOutcomes> => {
    const response = await api.put(
      `/materials/materials/${materialId}/mappings`,
      {
        uloIds,
      }
    );
    return response.data;
  },

  getWeekSummary: async (unitId: string, weekNumber: number): Promise<any> => {
    const response = await api.get(
      `/materials/units/${unitId}/weeks/${weekNumber}/summary`
    );
    return response.data;
  },

  applyStructure: async (
    unitId: string,
    mode: 'stubs' | 'categories',
    sourceWeek = 1
  ): Promise<MaterialResponse[]> => {
    const response = await api.post(
      `/materials/units/${unitId}/apply-structure`,
      { mode, sourceWeek }
    );
    return response.data;
  },
};

// Material image upload (moved from api.ts)
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
