/**
 * API service functions for Assessments management
 */

import api from './api';
import type {
  AssessmentCreate,
  AssessmentUpdate,
  AssessmentResponse,
  AssessmentWithOutcomes,
  AssessmentFilter,
  GradeDistribution,
} from '../types/unitStructure';

export const assessmentsApi = {
  createAssessment: async (
    unitId: string,
    data: AssessmentCreate
  ): Promise<AssessmentResponse> => {
    const response = await api.post(
      `/assessments/units/${unitId}/assessments`,
      data
    );
    return response.data;
  },

  getAssessmentsByUnit: async (
    unitId: string,
    filter?: AssessmentFilter
  ): Promise<AssessmentResponse[]> => {
    const response = await api.get(`/assessments/units/${unitId}/assessments`, {
      params: filter,
    });
    return response.data;
  },

  getAssessment: async (
    assessmentId: string,
    includeOutcomes = false
  ): Promise<AssessmentWithOutcomes> => {
    const response = await api.get(`/assessments/assessments/${assessmentId}`, {
      params: { include_outcomes: includeOutcomes },
    });
    return response.data;
  },

  updateAssessment: async (
    assessmentId: string,
    data: AssessmentUpdate
  ): Promise<AssessmentResponse> => {
    const response = await api.put(
      `/assessments/assessments/${assessmentId}`,
      data
    );
    return response.data;
  },

  deleteAssessment: async (assessmentId: string): Promise<void> => {
    await api.delete(`/assessments/assessments/${assessmentId}`);
  },

  getGradeDistribution: async (unitId: string): Promise<GradeDistribution> => {
    const response = await api.get(
      `/assessments/units/${unitId}/assessments/grade-distribution`
    );
    return response.data;
  },

  validateWeights: async (unitId: string): Promise<any> => {
    const response = await api.get(
      `/assessments/units/${unitId}/assessments/validate-weights`
    );
    return response.data;
  },

  getAssessmentTimeline: async (unitId: string): Promise<any> => {
    const response = await api.get(
      `/assessments/units/${unitId}/assessments/timeline`
    );
    return response.data;
  },

  getAssessmentWorkload: async (unitId: string): Promise<any> => {
    const response = await api.get(
      `/assessments/units/${unitId}/assessments/workload`
    );
    return response.data;
  },

  updateAssessmentMappings: async (
    assessmentId: string,
    uloIds: string[]
  ): Promise<AssessmentWithOutcomes> => {
    const response = await api.put(
      `/assessments/assessments/${assessmentId}/mappings`,
      {
        uloIds,
      }
    );
    return response.data;
  },

  updateMaterialLinks: async (
    assessmentId: string,
    materialIds: string[]
  ): Promise<AssessmentWithOutcomes> => {
    const response = await api.put(
      `/assessments/assessments/${assessmentId}/materials`,
      {
        materialIds,
      }
    );
    return response.data;
  },
};
