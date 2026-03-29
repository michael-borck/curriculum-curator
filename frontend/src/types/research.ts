// =============================================================================
// Research Feature Types
// Mirrors backend CamelModel schemas (all camelCase)
// =============================================================================

// Workflow stage management
export type ResearchStage =
  | 'input'
  | 'searching'
  | 'results'
  | 'select-action'
  | 'proposing'
  | 'review'
  | 'applying'
  | 'done';

// =============================================================================
// Phase 1: Academic Search
// =============================================================================

export interface AcademicSearchRequest {
  query: string;
  maxResults?: number | undefined;
  academicOnly?: boolean | undefined;
  preferredTier?: number | undefined;
  unitId?: string | undefined;
}

export interface AcademicSearchResultItem {
  title: string;
  url: string;
  doi?: string | undefined;
  abstract?: string | undefined;
  authors: string[];
  publicationYear?: number | undefined;
  sourceName?: string | undefined;
  citationCount?: number | undefined;
  academicScore: number;
  provider?: string | undefined;
}

export interface AcademicSearchResponse {
  query: string;
  results: AcademicSearchResultItem[];
  totalResults: number;
  tierUsed: number;
  tierName: string;
}

export interface TierInfo {
  tier: number;
  name: string;
  available: boolean;
  reason?: string | undefined;
}

export interface AvailableTiersResponse {
  tiers: TierInfo[];
}

// =============================================================================
// Phase 2: URL Extraction
// =============================================================================

export interface UrlExtractRequest {
  urls: string[];
  summarize?: boolean | undefined;
  purpose?: string | undefined;
}

export interface ExtractedUrlItem {
  url: string;
  title?: string | undefined;
  summary?: string | undefined;
  keyPoints: string[];
  academicScore: number;
  contentType: string;
  error?: string | undefined;
}

export interface UrlExtractResponse {
  results: ExtractedUrlItem[];
  total: number;
  successful: number;
  failed: number;
}

// =============================================================================
// Phase 3: Outline Synthesis — Inputs
// =============================================================================

export interface SourceInput {
  title: string;
  url?: string | undefined;
  summary?: string | undefined;
  keyPoints?: string[] | undefined;
}

export interface ScaffoldFromSourcesRequest {
  sourceData: SourceInput[];
  unitTitle: string;
  unitDescription?: string | undefined;
  durationWeeks?: number | undefined;
  pedagogyStyle?: string | undefined;
  unitId?: string | undefined;
  designId?: string | undefined;
}

export interface CompareRequest {
  sourceData: SourceInput[];
  unitId: string;
}

export interface MatchReadingListRequest {
  sourceData: SourceInput[];
  unitId: string;
}

// =============================================================================
// Phase 3: Outline Synthesis — Scaffold Response (mirrors ai.py)
// =============================================================================

export interface ScaffoldULO {
  code: string;
  description: string;
  bloomLevel: string;
}

export interface ScaffoldWeek {
  weekNumber: number;
  topic: string;
  activities: string[];
}

export interface ScaffoldAssessment {
  title: string;
  category: string;
  weight: number;
  dueWeek?: number | undefined;
}

export interface ScaffoldUnitResponse {
  title: string;
  description: string;
  ulos: ScaffoldULO[];
  weeks: ScaffoldWeek[];
  assessments: ScaffoldAssessment[];
}

// =============================================================================
// Phase 3: Outline Synthesis — Comparison Response
// =============================================================================

export interface ComparisonWeek {
  weekNumber: number;
  topic: string;
  coverage: 'well_covered' | 'partially_covered' | 'not_covered';
  matchingSources: string[];
}

export interface ComparisonProposal {
  unitId: string;
  weeks: ComparisonWeek[];
  gaps: string[];
  overlaps: string[];
  suggestions: string[];
}

// =============================================================================
// Phase 3: Outline Synthesis — Reading List Response
// =============================================================================

export interface UnitWeekInfo {
  weekNumber: number;
  topic: string;
}

export interface ResourceMatch {
  url: string;
  title: string;
  suggestedWeek: number;
  confidence: number;
  reasoning: string;
  assignedWeek?: number | undefined;
  skipped?: boolean | undefined;
}

export interface ReadingListProposal {
  unitId: string;
  unitWeeks: UnitWeekInfo[];
  matches: ResourceMatch[];
  unmatchedCount: number;
  avgConfidence: number;
}

// =============================================================================
// Phase 3: Apply Endpoints
// =============================================================================

export interface ApplyScaffoldRequest {
  proposal: ScaffoldUnitResponse;
  unitId?: string | undefined;
}

export interface ApplyComparisonRequest {
  proposal: ComparisonProposal;
  selectedSuggestions: number[];
}

export interface ApplyReadingListRequest {
  proposal: ReadingListProposal;
  saveAsSources?: boolean | undefined;
}

export interface ApplyScaffoldResponse {
  unitId: string;
  created: boolean;
}

export interface ApplyComparisonResponse {
  unitId: string;
  appliedSuggestions: number;
}

export interface ApplyReadingListResponse {
  savedSources: number;
}

// =============================================================================
// Phase 4: Research Settings
// =============================================================================

export interface SearchApiKeys {
  googleCseApiKey?: string | undefined;
  googleCseEngineId?: string | undefined;
  braveSearchApiKey?: string | undefined;
  tavilyApiKey?: string | undefined;
  coreApiKey?: string | undefined;
}

export interface ResearchSettings {
  preferredTier: number;
  searchApiKeys?: SearchApiKeys | undefined;
  searxngUrl?: string | undefined;
}

// =============================================================================
// =============================================================================
// Phase 5: Captured Page Metadata (Embedded Browser)
// =============================================================================

export interface CapturedPageMetadata {
  url: string;
  title: string;
  description?: string | undefined;
  doi?: string | undefined;
  authors?: string[] | undefined;
  publicationDate?: string | undefined;
  publisher?: string | undefined;
  journalName?: string | undefined;
  volume?: string | undefined;
  issue?: string | undefined;
  pages?: string | undefined;
  isbn?: string | undefined;
  contentText?: string | undefined;
  academicScore?: number | undefined;
  extractionError?: string | undefined;
}

// =============================================================================
// Shared action type for SourceSelector
// =============================================================================

export type ResearchAction = 'scaffold' | 'compare' | 'reading-list';
