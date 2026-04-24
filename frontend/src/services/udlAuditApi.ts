import api from './api';
import type {
  UDLAuditAISuggestionsResponse,
  UDLAuditBatchUpsert,
  UDLAuditResponseItem,
  UDLAuditSummary,
  UDLGuidelinesData,
  UDLProfile,
} from '../types/unitStructure';

export const udlAuditApi = {
  listProfiles: async (): Promise<UDLProfile[]> => {
    const res = await api.get('/udl-audit/profiles');
    return res.data;
  },

  listGuidelines: async (): Promise<UDLGuidelinesData> => {
    const res = await api.get('/udl-audit/guidelines');
    return res.data;
  },

  getResponses: async (
    unitId: string,
    profileId: string,
    assessmentId = ''
  ): Promise<UDLAuditResponseItem[]> => {
    const res = await api.get(`/udl-audit/units/${unitId}/responses`, {
      params: { profile_id: profileId, assessment_id: assessmentId },
    });
    return res.data;
  },

  getSummary: async (
    unitId: string,
    profileId: string,
    assessmentId = ''
  ): Promise<UDLAuditSummary> => {
    const res = await api.get(`/udl-audit/units/${unitId}/summary`, {
      params: { profile_id: profileId, assessment_id: assessmentId },
    });
    return res.data;
  },

  upsertResponses: async (
    unitId: string,
    data: UDLAuditBatchUpsert
  ): Promise<UDLAuditResponseItem[]> => {
    const res = await api.put(`/udl-audit/units/${unitId}/responses`, data);
    return res.data;
  },

  getAISuggestions: async (
    unitId: string,
    profileId: string,
    assessmentId = ''
  ): Promise<UDLAuditAISuggestionsResponse> => {
    const res = await api.post(
      `/udl-audit/units/${unitId}/ai-suggestions`,
      null,
      { params: { profile_id: profileId, assessment_id: assessmentId } }
    );
    return res.data;
  },
};
