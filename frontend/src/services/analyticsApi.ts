/**
 * API service functions for Analytics, Quality, UDL, and Snapshots
 */

import api from './api';
import type {
  UnitOverview,
  AlignmentReport,
  WeeklyWorkload,
  QualityScore,
  WeekQualityScore,
  BatchQualityScores,
  BatchDashboardMetricsResponse,
  UDLUnitScore,
  UDLWeekScore,
  UDLSuggestionsResponse,
  SnapshotListItem,
  SnapshotResponse,
  SnapshotComparison,
} from '../types/unitStructure';

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

  getBatchDashboardMetrics: async (
    unitIds: string[]
  ): Promise<BatchDashboardMetricsResponse> => {
    const response = await api.post(
      `/analytics/units/batch-dashboard-metrics`,
      { unit_ids: unitIds }
    );
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

  // UDL endpoints
  getUDLScore: async (
    unitId: string,
    totalWeeks = 12,
    targetLevel = 'university'
  ): Promise<UDLUnitScore> => {
    const response = await api.get(`/analytics/units/${unitId}/udl-score`, {
      params: { total_weeks: totalWeeks, target_level: targetLevel },
    });
    return response.data;
  },

  getUDLWeekly: async (
    unitId: string,
    totalWeeks = 12,
    targetLevel = 'university'
  ): Promise<UDLWeekScore[]> => {
    const response = await api.get(`/analytics/units/${unitId}/udl-weekly`, {
      params: { total_weeks: totalWeeks, target_level: targetLevel },
    });
    return response.data;
  },

  getUDLSuggestions: async (
    unitId: string,
    totalWeeks = 12,
    targetLevel = 'university'
  ): Promise<UDLSuggestionsResponse> => {
    const response = await api.get(
      `/analytics/units/${unitId}/udl-suggestions`,
      { params: { total_weeks: totalWeeks, target_level: targetLevel } }
    );
    return response.data;
  },

  // Snapshot endpoints
  listSnapshots: async (unitId: string): Promise<SnapshotListItem[]> => {
    const response = await api.get(`/analytics/units/${unitId}/snapshots`);
    return response.data;
  },

  createSnapshot: async (
    unitId: string,
    label?: string
  ): Promise<SnapshotResponse> => {
    const response = await api.post(`/analytics/units/${unitId}/snapshots`, {
      label,
    });
    return response.data;
  },

  getSnapshot: async (
    unitId: string,
    snapshotId: string
  ): Promise<SnapshotResponse> => {
    const response = await api.get(
      `/analytics/units/${unitId}/snapshots/${snapshotId}`
    );
    return response.data;
  },

  deleteSnapshot: async (unitId: string, snapshotId: string): Promise<void> => {
    await api.delete(`/analytics/units/${unitId}/snapshots/${snapshotId}`);
  },

  compareSnapshots: async (
    unitId: string,
    aId: string,
    bId: string
  ): Promise<SnapshotComparison> => {
    const response = await api.get(
      `/analytics/units/${unitId}/snapshots/compare`,
      { params: { a: aId, b: bId } }
    );
    return response.data;
  },
};
