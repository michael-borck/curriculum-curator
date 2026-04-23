import api from './api';
import type {
  BulkULOCLOMappingCreate,
  CLOItem,
  CLOItemCreate,
  CLOItemUpdate,
  CLOSet,
  CLOSetCreate,
  CLOSetUpdate,
  CLOSuggestionsResponse,
  ULOCLOMapping,
} from '../types/cloSets';

export const cloSetsApi = {
  // ── CLO Set CRUD ────────────────────────────────────────────

  listCLOSets: async (): Promise<CLOSet[]> => {
    const res = await api.get('/clo-sets');
    return res.data;
  },

  createCLOSet: async (data: CLOSetCreate): Promise<CLOSet> => {
    const res = await api.post('/clo-sets', data);
    return res.data;
  },

  getCLOSet: async (setId: string): Promise<CLOSet> => {
    const res = await api.get(`/clo-sets/${setId}`);
    return res.data;
  },

  updateCLOSet: async (setId: string, data: CLOSetUpdate): Promise<CLOSet> => {
    const res = await api.put(`/clo-sets/${setId}`, data);
    return res.data;
  },

  deleteCLOSet: async (setId: string): Promise<void> => {
    await api.delete(`/clo-sets/${setId}`);
  },

  // ── CLO Items ───────────────────────────────────────────────

  addCLOItem: async (setId: string, data: CLOItemCreate): Promise<CLOItem> => {
    const res = await api.post(`/clo-sets/${setId}/items`, data);
    return res.data;
  },

  updateCLOItem: async (
    setId: string,
    itemId: string,
    data: CLOItemUpdate
  ): Promise<CLOItem> => {
    const res = await api.put(`/clo-sets/${setId}/items/${itemId}`, data);
    return res.data;
  },

  deleteCLOItem: async (setId: string, itemId: string): Promise<void> => {
    await api.delete(`/clo-sets/${setId}/items/${itemId}`);
  },

  reorderCLOItems: async (
    setId: string,
    itemIds: string[]
  ): Promise<CLOItem[]> => {
    const res = await api.post(`/clo-sets/${setId}/items/reorder`, { itemIds });
    return res.data;
  },

  // ── Unit assignments ─────────────────────────────────────────

  getUnitCLOSets: async (unitId: string): Promise<CLOSet[]> => {
    const res = await api.get(`/clo-sets/units/${unitId}/clo-sets`);
    return res.data;
  },

  assignCLOSet: async (unitId: string, setId: string): Promise<void> => {
    await api.post(`/clo-sets/units/${unitId}/clo-sets/${setId}`);
  },

  unassignCLOSet: async (unitId: string, setId: string): Promise<void> => {
    await api.delete(`/clo-sets/units/${unitId}/clo-sets/${setId}`);
  },

  // ── ULO → CLO mappings ───────────────────────────────────────

  getULOCLOMappings: async (uloId: string): Promise<ULOCLOMapping[]> => {
    const res = await api.get(`/clo-sets/ulos/${uloId}/clo-mappings`);
    return res.data;
  },

  setULOCLOMappings: async (
    uloId: string,
    data: BulkULOCLOMappingCreate
  ): Promise<ULOCLOMapping[]> => {
    const res = await api.put(`/clo-sets/ulos/${uloId}/clo-mappings`, data);
    return res.data;
  },

  // ── AI suggestions ───────────────────────────────────────────

  suggestCLOMappings: async (
    unitId: string
  ): Promise<CLOSuggestionsResponse> => {
    const res = await api.post(`/clo-sets/units/${unitId}/clo-suggestions`);
    return res.data;
  },
};
