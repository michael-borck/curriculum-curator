import api from './api';

export interface SaveFromSearchRequest {
  url: string;
  title: string;
  summary?: string | undefined;
  academicScore?: number | undefined;
  tags?: string[] | undefined;
  unitId?: string | undefined;
}

export interface ResearchSourceResponse {
  id: string;
  userId: string;
  unitId?: string | undefined;
  url: string;
  title: string;
  summary?: string | undefined;
  academicScore: number;
  isFavorite: boolean;
  createdAt: string;
  updatedAt?: string | undefined;
}

export interface ResearchSourceList {
  sources: ResearchSourceResponse[];
  total: number;
  page: number;
  pageSize: number;
  hasMore: boolean;
}

export interface ListSourcesParams {
  unitId?: string | undefined;
  favoritesOnly?: boolean | undefined;
  tag?: string | undefined;
  search?: string | undefined;
  page?: number | undefined;
  pageSize?: number | undefined;
}

export const saveFromSearch = (data: SaveFromSearchRequest) =>
  api.post<ResearchSourceResponse>('/sources/from-search', data);

export const listSources = (params?: ListSourcesParams) =>
  api.get<ResearchSourceList>('/sources', { params });

export const deleteSource = (id: string) => api.delete(`/sources/${id}`);

export const toggleFavorite = (id: string) =>
  api.post<ResearchSourceResponse>(`/sources/${id}/favorite`);
