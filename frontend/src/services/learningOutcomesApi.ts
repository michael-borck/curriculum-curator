/**
 * API service functions for Learning Outcomes (ULOs, LLOs, ALOs)
 */

import api from './api';
import type {
  ULOCreate,
  ULOUpdate,
  ULOResponse,
  ULOWithMappings,
  BulkULOCreate,
  ALOResponse,
  LLOResponse,
} from '../types/unitStructure';

export const learningOutcomesApi = {
  // ULO Management
  createULO: async (unitId: string, data: ULOCreate): Promise<ULOResponse> => {
    const response = await api.post(`/outcomes/units/${unitId}/ulos`, data);
    return response.data;
  },

  getULOsByUnit: async (
    unitId: string,
    includeMappings = false
  ): Promise<ULOWithMappings[]> => {
    const response = await api.get(`/outcomes/units/${unitId}/ulos`, {
      params: { include_mappings: includeMappings },
    });
    return response.data;
  },

  getULO: async (uloId: string): Promise<ULOResponse> => {
    const response = await api.get(`/outcomes/ulos/${uloId}`);
    return response.data;
  },

  updateULO: async (uloId: string, data: ULOUpdate): Promise<ULOResponse> => {
    const response = await api.put(`/outcomes/ulos/${uloId}`, data);
    return response.data;
  },

  deleteULO: async (uloId: string): Promise<void> => {
    await api.delete(`/outcomes/ulos/${uloId}`);
  },

  reorderULOs: async (
    unitId: string,
    outcomeIds: string[]
  ): Promise<ULOResponse[]> => {
    const response = await api.post(`/outcomes/units/${unitId}/ulos/reorder`, {
      outcomeIds,
    });
    return response.data;
  },

  bulkCreateULOs: async (
    unitId: string,
    data: BulkULOCreate
  ): Promise<ULOResponse[]> => {
    const response = await api.post(
      `/outcomes/units/${unitId}/ulos/bulk`,
      data
    );
    return response.data;
  },

  getULOCoverage: async (unitId: string): Promise<any> => {
    const response = await api.get(`/outcomes/units/${unitId}/ulos/coverage`);
    return response.data;
  },

  // Local Learning Outcomes (Materials)
  addMaterialOutcome: async (
    materialId: string,
    description: string
  ): Promise<LLOResponse> => {
    const response = await api.post(
      `/outcomes/materials/${materialId}/outcomes`,
      {
        description,
      }
    );
    return response.data;
  },

  // Assessment Learning Outcomes
  addAssessmentOutcome: async (
    assessmentId: string,
    description: string
  ): Promise<ALOResponse> => {
    const response = await api.post(
      `/outcomes/assessments/${assessmentId}/outcomes`,
      {
        description,
      }
    );
    return response.data;
  },
};
