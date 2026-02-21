/**
 * API service functions for Unit Structure and Assessment Management
 */

import api from './api';
import {
  // Learning Outcomes
  ULOCreate,
  ULOUpdate,
  ULOResponse,
  ULOWithMappings,
  BulkULOCreate,
  ALOResponse,
  LLOResponse,

  // Materials
  MaterialCreate,
  MaterialUpdate,
  MaterialResponse,
  MaterialWithOutcomes,
  MaterialFilter,
  WeekMaterials,

  // Assessments
  AssessmentCreate,
  AssessmentUpdate,
  AssessmentResponse,
  AssessmentWithOutcomes,
  AssessmentFilter,
  GradeDistribution,

  // Analytics
  UnitOverview,
  AlignmentReport,
  WeeklyWorkload,
  QualityScore,
  WeekQualityScore,
  BatchQualityScores,

  // Accreditation
  GraduateCapabilityMapping,
  GraduateCapabilityMappingCreate,
  BulkGraduateCapabilityMappingCreate,
  AoLMapping,
  AoLMappingCreate,
  BulkAoLMappingCreate,
  AoLMappingSummary,
  GraduateCapabilityCode,
  SDGMapping,
  SDGMappingCreate,
  BulkSDGMappingCreate,
  SDGMappingSummary,
  SDGCode,
} from '../types/unitStructure';

// ============= Learning Outcomes API =============

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

// ============= Materials API =============

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
};

// ============= Assessments API =============

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

// ============= Analytics API =============

export const analyticsApi = {
  getUnitOverview: async (unitId: string): Promise<UnitOverview> => {
    const response = await api.get(`/analytics/units/${unitId}/overview`);
    return response.data;
  },

  getProgressReport: async (
    unitId: string,
    includeDetails = false
  ): Promise<any> => {
    const response = await api.get(`/analytics/units/${unitId}/progress`, {
      params: { include_details: includeDetails },
    });
    return response.data;
  },

  getCompletionReport: async (unitId: string): Promise<any> => {
    const response = await api.get(`/analytics/units/${unitId}/completion`);
    return response.data;
  },

  getAlignmentReport: async (unitId: string): Promise<AlignmentReport> => {
    const response = await api.get(`/analytics/units/${unitId}/alignment`);
    return response.data;
  },

  getWeeklyWorkload: async (
    unitId: string,
    startWeek = 1,
    endWeek = 52
  ): Promise<WeeklyWorkload[]> => {
    const response = await api.get(`/analytics/units/${unitId}/workload`, {
      params: { start_week: startWeek, end_week: endWeek },
    });
    return response.data;
  },

  getRecommendations: async (unitId: string): Promise<any> => {
    const response = await api.get(
      `/analytics/units/${unitId}/recommendations`
    );
    return response.data;
  },

  exportUnitData: async (
    unitId: string,
    format: 'json' | 'csv' | 'pdf' = 'json'
  ): Promise<any> => {
    const response = await api.get(`/analytics/units/${unitId}/export`, {
      params: { format },
    });
    return response.data;
  },

  getQualityScore: async (
    unitId: string,
    totalWeeks = 12
  ): Promise<QualityScore> => {
    const response = await api.get(`/analytics/units/${unitId}/quality-score`, {
      params: { total_weeks: totalWeeks },
    });
    return response.data;
  },

  getWeeklyQuality: async (
    unitId: string,
    totalWeeks = 12
  ): Promise<WeekQualityScore[]> => {
    const response = await api.get(
      `/analytics/units/${unitId}/weekly-quality`,
      { params: { total_weeks: totalWeeks } }
    );
    return response.data;
  },

  getBatchQualityScores: async (
    unitIds: string[]
  ): Promise<BatchQualityScores> => {
    const response = await api.post(`/analytics/units/batch-quality-scores`, {
      unit_ids: unitIds,
    });
    return response.data;
  },

  validateUnit: async (unitId: string, strict = false): Promise<any> => {
    const response = await api.get(`/analytics/units/${unitId}/validation`, {
      params: { strict },
    });
    return response.data;
  },

  getUnitStatistics: async (unitId: string): Promise<any> => {
    const response = await api.get(`/analytics/units/${unitId}/statistics`);
    return response.data;
  },
};

// ============= Accreditation API =============

export const accreditationApi = {
  // Graduate Capability Mappings (ULO-level)
  getULOGraduateCapabilities: async (
    uloId: string
  ): Promise<GraduateCapabilityMapping[]> => {
    const response = await api.get(
      `/accreditation/ulos/${uloId}/graduate-capabilities`
    );
    return response.data;
  },

  addULOGraduateCapability: async (
    uloId: string,
    data: GraduateCapabilityMappingCreate
  ): Promise<GraduateCapabilityMapping> => {
    const response = await api.post(
      `/accreditation/ulos/${uloId}/graduate-capabilities`,
      data
    );
    return response.data;
  },

  updateULOGraduateCapabilities: async (
    uloId: string,
    data: BulkGraduateCapabilityMappingCreate
  ): Promise<GraduateCapabilityMapping[]> => {
    const response = await api.put(
      `/accreditation/ulos/${uloId}/graduate-capabilities`,
      data
    );
    return response.data;
  },

  removeULOGraduateCapability: async (
    uloId: string,
    capabilityCode: GraduateCapabilityCode
  ): Promise<void> => {
    await api.delete(
      `/accreditation/ulos/${uloId}/graduate-capabilities/${capabilityCode}`
    );
  },

  // AoL Mappings (Unit-level)
  getUnitAoLMappings: async (unitId: string): Promise<AoLMappingSummary> => {
    const response = await api.get(
      `/accreditation/units/${unitId}/aol-mappings`
    );
    return response.data;
  },

  addUnitAoLMapping: async (
    unitId: string,
    data: AoLMappingCreate
  ): Promise<AoLMapping> => {
    const response = await api.post(
      `/accreditation/units/${unitId}/aol-mappings`,
      data
    );
    return response.data;
  },

  updateUnitAoLMappings: async (
    unitId: string,
    data: BulkAoLMappingCreate
  ): Promise<AoLMappingSummary> => {
    const response = await api.put(
      `/accreditation/units/${unitId}/aol-mappings`,
      data
    );
    return response.data;
  },

  removeUnitAoLMapping: async (
    unitId: string,
    competencyCode: string
  ): Promise<void> => {
    await api.delete(
      `/accreditation/units/${unitId}/aol-mappings/${competencyCode}`
    );
  },

  // SDG Mappings (Unit-level)
  getUnitSDGMappings: async (unitId: string): Promise<SDGMappingSummary> => {
    const response = await api.get(
      `/accreditation/units/${unitId}/sdg-mappings`
    );
    return response.data;
  },

  addUnitSDGMapping: async (
    unitId: string,
    data: SDGMappingCreate
  ): Promise<SDGMapping> => {
    const response = await api.post(
      `/accreditation/units/${unitId}/sdg-mappings`,
      data
    );
    return response.data;
  },

  updateUnitSDGMappings: async (
    unitId: string,
    data: BulkSDGMappingCreate
  ): Promise<SDGMappingSummary> => {
    const response = await api.put(
      `/accreditation/units/${unitId}/sdg-mappings`,
      data
    );
    return response.data;
  },

  removeUnitSDGMapping: async (
    unitId: string,
    sdgCode: SDGCode
  ): Promise<void> => {
    await api.delete(`/accreditation/units/${unitId}/sdg-mappings/${sdgCode}`);
  },
};
