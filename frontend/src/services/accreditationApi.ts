/**
 * API service functions for Accreditation mappings
 * (Graduate Capabilities, AoL, SDG, Custom Alignment Frameworks)
 */

import api from './api';
import type {
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
  CustomAlignmentFramework,
  FrameworkCreate,
  FrameworkUpdate,
  FrameworkSummary,
  FrameworkItemCreate,
  FrameworkItemUpdate,
  FrameworkItem,
  ULOFrameworkItemMapping,
  BulkULOItemMappingCreate,
} from '../types/unitStructure';

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

  // Custom Alignment Frameworks
  getUnitFrameworks: async (unitId: string): Promise<FrameworkSummary> => {
    const response = await api.get(`/accreditation/units/${unitId}/frameworks`);
    return response.data;
  },

  createFramework: async (
    unitId: string,
    data: FrameworkCreate
  ): Promise<CustomAlignmentFramework> => {
    const response = await api.post(
      `/accreditation/units/${unitId}/frameworks`,
      data
    );
    return response.data;
  },

  updateFramework: async (
    unitId: string,
    frameworkId: string,
    data: FrameworkUpdate
  ): Promise<CustomAlignmentFramework> => {
    const response = await api.put(
      `/accreditation/units/${unitId}/frameworks/${frameworkId}`,
      data
    );
    return response.data;
  },

  deleteFramework: async (
    unitId: string,
    frameworkId: string
  ): Promise<void> => {
    await api.delete(
      `/accreditation/units/${unitId}/frameworks/${frameworkId}`
    );
  },

  // Framework Items
  addFrameworkItem: async (
    unitId: string,
    frameworkId: string,
    data: FrameworkItemCreate
  ): Promise<FrameworkItem> => {
    const response = await api.post(
      `/accreditation/units/${unitId}/frameworks/${frameworkId}/items`,
      data
    );
    return response.data;
  },

  updateFrameworkItem: async (
    unitId: string,
    frameworkId: string,
    itemId: string,
    data: FrameworkItemUpdate
  ): Promise<FrameworkItem> => {
    const response = await api.put(
      `/accreditation/units/${unitId}/frameworks/${frameworkId}/items/${itemId}`,
      data
    );
    return response.data;
  },

  deleteFrameworkItem: async (
    unitId: string,
    frameworkId: string,
    itemId: string
  ): Promise<void> => {
    await api.delete(
      `/accreditation/units/${unitId}/frameworks/${frameworkId}/items/${itemId}`
    );
  },

  // ULO->Framework Item Mappings
  getULOFrameworkMappings: async (
    uloId: string
  ): Promise<ULOFrameworkItemMapping[]> => {
    const response = await api.get(
      `/accreditation/ulos/${uloId}/framework-mappings`
    );
    return response.data;
  },

  updateULOFrameworkMappings: async (
    uloId: string,
    data: BulkULOItemMappingCreate
  ): Promise<ULOFrameworkItemMapping[]> => {
    const response = await api.put(
      `/accreditation/ulos/${uloId}/framework-mappings`,
      data
    );
    return response.data;
  },

  removeULOFrameworkMapping: async (
    uloId: string,
    itemId: string
  ): Promise<void> => {
    await api.delete(
      `/accreditation/ulos/${uloId}/framework-mappings/${itemId}`
    );
  },
};
