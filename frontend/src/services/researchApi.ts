import api from './api';
import type {
  AcademicSearchRequest,
  AcademicSearchResponse,
  AvailableTiersResponse,
  UrlExtractRequest,
  UrlExtractResponse,
  ScaffoldFromSourcesRequest,
  ScaffoldUnitResponse,
  CompareRequest,
  ComparisonProposal,
  MatchReadingListRequest,
  ReadingListProposal,
  ApplyScaffoldRequest,
  ApplyScaffoldResponse,
  ApplyComparisonRequest,
  ApplyComparisonResponse,
  ApplyReadingListRequest,
  ApplyReadingListResponse,
  ResearchSettings,
} from '../types/research';

// Phase 1: Academic Search

export const searchAcademic = async (
  req: AcademicSearchRequest
): Promise<AcademicSearchResponse> => {
  const res = await api.post('/research/search', req);
  return res.data;
};

export const getAvailableTiers = async (): Promise<AvailableTiersResponse> => {
  const res = await api.get('/research/tiers');
  return res.data;
};

// Phase 2: URL Extraction

export const extractUrls = async (
  req: UrlExtractRequest
): Promise<UrlExtractResponse> => {
  const res = await api.post('/research/extract-urls', req);
  return res.data;
};

// Phase 3: Propose

export const proposeScaffold = async (
  req: ScaffoldFromSourcesRequest
): Promise<ScaffoldUnitResponse> => {
  const res = await api.post('/research/scaffold', req);
  return res.data;
};

export const proposeComparison = async (
  req: CompareRequest
): Promise<ComparisonProposal> => {
  const res = await api.post('/research/compare', req);
  return res.data;
};

export const proposeReadingList = async (
  req: MatchReadingListRequest
): Promise<ReadingListProposal> => {
  const res = await api.post('/research/match-reading-list', req);
  return res.data;
};

// Phase 3: Apply

export const applyScaffold = async (
  req: ApplyScaffoldRequest
): Promise<ApplyScaffoldResponse> => {
  const res = await api.post('/research/scaffold/apply', req);
  return res.data;
};

export const applyComparison = async (
  req: ApplyComparisonRequest
): Promise<ApplyComparisonResponse> => {
  const res = await api.post('/research/compare/apply', req);
  return res.data;
};

export const applyReadingList = async (
  req: ApplyReadingListRequest
): Promise<ApplyReadingListResponse> => {
  const res = await api.post('/research/match-reading-list/apply', req);
  return res.data;
};

// Phase 4: Settings

export const saveResearchSettings = async (
  req: ResearchSettings
): Promise<{ saved: boolean }> => {
  const res = await api.put('/research/settings', req);
  return res.data;
};
