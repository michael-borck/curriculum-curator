/**
 * TypeScript interfaces for Unit Structure and Assessment Management
 */

// ============= Enums =============

export enum SessionFormat {
  LECTURE = 'lecture',
  TUTORIAL = 'tutorial',
  LAB = 'lab',
  WORKSHOP = 'workshop',
  SEMINAR = 'seminar',
  INDEPENDENT = 'independent',
  OTHER = 'other',
}

export enum MaterialStatus {
  DRAFT = 'draft',
  PUBLISHED = 'published',
  ARCHIVED = 'archived',
}

export enum MaterialCategory {
  PRE_CLASS = 'pre_class',
  IN_CLASS = 'in_class',
  POST_CLASS = 'post_class',
  RESOURCES = 'resources',
  GENERAL = 'general',
}

export enum AssessmentType {
  FORMATIVE = 'formative',
  SUMMATIVE = 'summative',
}

export enum AssessmentCategory {
  EXAM = 'exam',
  ASSIGNMENT = 'assignment',
  PROJECT = 'project',
  PRESENTATION = 'presentation',
  PARTICIPATION = 'participation',
  QUIZ = 'quiz',
  LAB_REPORT = 'lab_report',
  PORTFOLIO = 'portfolio',
  OTHER = 'other',
}

export enum AssessmentStatus {
  DRAFT = 'draft',
  PUBLISHED = 'published',
  ARCHIVED = 'archived',
}

// ============= Learning Outcomes =============

export interface ULOCreate {
  code: string;
  description: string;
  bloomLevel: string;
  orderIndex?: number;
}

export interface ULOUpdate {
  code?: string;
  description?: string;
  bloomLevel?: string;
  orderIndex?: number;
}

export interface ULOResponse {
  id: string;
  unitId: string;
  code: string;
  description: string;
  bloomLevel: string;
  orderIndex: number;
  createdAt: string;
  updatedAt: string;
}

export interface ULOWithMappings extends ULOResponse {
  materialCount: number;
  assessmentCount: number;
}

export interface LLOResponse {
  id: string;
  materialId: string;
  description: string;
  orderIndex: number;
  createdAt: string;
  updatedAt: string;
}

export interface ALOResponse {
  id: string;
  assessmentId: string;
  description: string;
  orderIndex: number;
  createdAt: string;
  updatedAt: string;
}

// ============= Weekly Materials =============

export interface MaterialCreate {
  weekNumber: number;
  title: string;
  type: SessionFormat;
  description?: string;
  durationMinutes?: number;
  category?: MaterialCategory;
  filePath?: string;
  materialMetadata?: Record<string, any>;
  orderIndex?: number;
  status?: MaterialStatus;
}

export interface MaterialUpdate {
  weekNumber?: number;
  title?: string;
  type?: SessionFormat;
  description?: string;
  durationMinutes?: number;
  category?: MaterialCategory;
  filePath?: string;
  materialMetadata?: Record<string, any>;
  orderIndex?: number;
  status?: MaterialStatus;
}

export interface MaterialResponse {
  id: string;
  unitId: string;
  weekNumber: number;
  title: string;
  type: SessionFormat;
  description?: string;
  durationMinutes?: number;
  category: MaterialCategory;
  filePath?: string;
  materialMetadata?: Record<string, any>;
  qualityScore?: number | undefined;
  orderIndex: number;
  status: MaterialStatus;
  createdAt: string;
  updatedAt: string;
}

export interface MaterialWithOutcomes extends MaterialResponse {
  localOutcomes: LLOResponse[];
  mappedUlos: ULOResponse[];
}

export interface WeekMaterials {
  weekNumber: number;
  totalDurationMinutes: number;
  materialCount: number;
  materials: MaterialResponse[];
}

// ============= Assessments =============

export interface AssessmentCreate {
  title: string;
  type: AssessmentType;
  category: AssessmentCategory;
  weight: number;
  description?: string;
  specification?: string;
  releaseWeek?: number;
  releaseDate?: string;
  dueWeek?: number;
  dueDate?: string;
  duration?: number;
  rubric?: Record<string, any>;
  questions?: string[];
  wordCount?: number;
  groupWork?: boolean;
  submissionType?: string;
  status?: AssessmentStatus;
}

export interface AssessmentUpdate {
  title?: string;
  type?: AssessmentType;
  category?: AssessmentCategory;
  weight?: number;
  description?: string;
  specification?: string;
  releaseWeek?: number;
  releaseDate?: string;
  dueWeek?: number;
  dueDate?: string;
  duration?: number;
  rubric?: Record<string, any>;
  questions?: string[];
  wordCount?: number;
  groupWork?: boolean;
  submissionType?: string;
  status?: AssessmentStatus;
}

export interface AssessmentResponse {
  id: string;
  unitId: string;
  title: string;
  type: AssessmentType;
  category: AssessmentCategory;
  weight: number;
  description?: string;
  specification?: string;
  releaseWeek?: number;
  releaseDate?: string;
  dueWeek?: number;
  dueDate?: string;
  duration?: number;
  rubric?: Record<string, any>;
  questions?: string[];
  wordCount?: number;
  groupWork: boolean;
  submissionType?: string;
  status: AssessmentStatus;
  createdAt: string;
  updatedAt: string;
}

export interface AssessmentWithOutcomes extends AssessmentResponse {
  assessmentOutcomes: ALOResponse[];
  mappedUlos: ULOResponse[];
  linkedMaterials: string[];
}

export interface GradeDistribution {
  unitId: string;
  totalWeight: number;
  byType: Record<string, number>;
  byCategory: Record<string, number>;
  assessments: Array<{
    id: string;
    title: string;
    type: string;
    category: string;
    weight: number;
  }>;
}

// ============= Analytics =============

export interface UnitOverview {
  unitId: string;
  uloCount: number;
  materials: {
    total: number;
    byStatus: Record<string, number>;
  };
  assessments: {
    total: number;
    byStatus: Record<string, number>;
  };
  totalAssessmentWeight: number;
  weeksWithContent: number;
  lastUpdated: string;
}

export interface AlignmentReport {
  unitId: string;
  alignmentDetails: Array<{
    uloId: string;
    uloCode: string;
    uloDescription: string;
    bloomLevel: string;
    materialCount: number;
    assessmentCount: number;
    materialIds: string[];
    assessmentIds: string[];
    alignmentScore: number;
  }>;
  summary: {
    totalUlos: number;
    fullyAligned: number;
    materialsOnly: number;
    assessmentsOnly: number;
    unaligned: number;
    alignmentPercentage: number;
  };
  recommendations: string[];
}

export interface WeeklyWorkload {
  weekNumber: number;
  materialCount: number;
  materialDurationMinutes: number;
  assessmentCount: number;
  assessmentDurationMinutes: number;
  totalDurationMinutes: number;
  workloadHours: number;
  materials: Array<{
    id: string;
    title: string;
    duration?: number;
  }>;
  assessments: Array<{
    id: string;
    title: string;
    weight: number;
  }>;
}

export interface QualityScore {
  unitId: string;
  overallScore: number;
  starRating: number;
  ratingMethod: string;
  subScores: {
    completeness: number;
    contentQuality: number;
    uloAlignment: number;
    workloadBalance: number;
    materialDiversity: number;
    assessmentDistribution: number;
  };
  grade: string;
  calculatedAt: string;
}

export interface WeekQualityScore {
  weekNumber: number;
  starRating: number;
  hasContent: boolean;
  materialCount: number;
  typeDiversityScore: number;
  avgQualityScore: number;
  totalDurationMinutes: number;
}

export interface BatchQualityScores {
  scores: Record<string, number>;
}

// ============= Filters =============

export interface MaterialFilter {
  weekNumber?: number;
  type?: SessionFormat;
  status?: MaterialStatus;
  search?: string;
}

export interface AssessmentFilter {
  type?: AssessmentType;
  category?: AssessmentCategory;
  status?: AssessmentStatus;
  releaseWeek?: number;
  dueWeek?: number;
  search?: string;
}

// ============= Bulk Operations =============

export interface BulkULOCreate {
  outcomes: ULOCreate[];
}

export interface MaterialReorder {
  materialIds: string[];
}

export interface OutcomeReorder {
  outcomeIds: string[];
}

export interface AssessmentMapping {
  uloIds: string[];
}

export interface MaterialMapping {
  uloIds: string[];
}

// ============= Accreditation Mappings =============

export type GraduateCapabilityCode =
  | 'GC1'
  | 'GC2'
  | 'GC3'
  | 'GC4'
  | 'GC5'
  | 'GC6';
export type AoLCompetencyCode =
  | 'AOL1'
  | 'AOL2'
  | 'AOL3'
  | 'AOL4'
  | 'AOL5'
  | 'AOL6'
  | 'AOL7';
export type AoLLevel = 'I' | 'R' | 'M';
export type SDGCode =
  | 'SDG1'
  | 'SDG2'
  | 'SDG3'
  | 'SDG4'
  | 'SDG5'
  | 'SDG6'
  | 'SDG7'
  | 'SDG8'
  | 'SDG9'
  | 'SDG10'
  | 'SDG11'
  | 'SDG12'
  | 'SDG13'
  | 'SDG14'
  | 'SDG15'
  | 'SDG16'
  | 'SDG17';

export interface GraduateCapabilityMapping {
  id: string;
  uloId: string;
  capabilityCode: GraduateCapabilityCode;
  isAiSuggested: boolean;
  notes?: string;
  createdAt: string;
  updatedAt: string;
}

export interface GraduateCapabilityMappingCreate {
  capabilityCode: GraduateCapabilityCode;
  isAiSuggested?: boolean;
  notes?: string;
}

export interface BulkGraduateCapabilityMappingCreate {
  capabilityCodes: GraduateCapabilityCode[];
  isAiSuggested?: boolean;
}

export interface AoLMapping {
  id: string;
  unitId: string;
  competencyCode: AoLCompetencyCode;
  level: AoLLevel;
  isAiSuggested: boolean;
  notes?: string;
  createdAt: string;
  updatedAt: string;
}

export interface AoLMappingCreate {
  competencyCode: AoLCompetencyCode;
  level: AoLLevel;
  isAiSuggested?: boolean;
  notes?: string;
}

export interface BulkAoLMappingCreate {
  mappings: AoLMappingCreate[];
}

export interface AoLMappingSummary {
  unitId: string;
  mappedCount: number;
  totalCompetencies: number;
  mappings: AoLMapping[];
}

// ============= SDG Mappings =============

export interface SDGMapping {
  id: string;
  unitId: string;
  sdgCode: SDGCode;
  isAiSuggested: boolean;
  notes?: string;
  createdAt: string;
  updatedAt: string;
}

export interface SDGMappingCreate {
  sdgCode: SDGCode;
  isAiSuggested?: boolean;
  notes?: string;
}

export interface BulkSDGMappingCreate {
  mappings: SDGMappingCreate[];
}

export interface SDGMappingSummary {
  unitId: string;
  mappedCount: number;
  totalSdgs: number;
  mappings: SDGMapping[];
}

// ============= Custom Alignment Frameworks =============

export type FrameworkPresetType =
  | 'plo'
  | 'grit'
  | 'ethics'
  | 'indigenous'
  | 'vision';

export interface FrameworkItem {
  id: string;
  frameworkId: string;
  code: string;
  description: string;
  isAiSuggested: boolean;
  notes?: string;
  orderIndex: number;
  createdAt: string;
  updatedAt: string;
}

export interface FrameworkItemCreate {
  code: string;
  description: string;
  isAiSuggested?: boolean;
  notes?: string;
  orderIndex?: number;
}

export interface FrameworkItemUpdate {
  code?: string;
  description?: string;
  notes?: string;
  orderIndex?: number;
}

export interface CustomAlignmentFramework {
  id: string;
  unitId: string;
  name: string;
  description?: string;
  presetType?: FrameworkPresetType;
  iconHint?: string;
  colorHint?: string;
  orderIndex: number;
  items: FrameworkItem[];
  createdAt: string;
  updatedAt: string;
}

export interface FrameworkCreate {
  name: string;
  description?: string | undefined;
  presetType?: FrameworkPresetType | undefined;
  iconHint?: string | undefined;
  colorHint?: string | undefined;
  orderIndex?: number | undefined;
  items?: FrameworkItemCreate[] | undefined;
}

export interface FrameworkUpdate {
  name?: string;
  description?: string;
  iconHint?: string;
  colorHint?: string;
  orderIndex?: number;
}

export interface FrameworkSummary {
  unitId: string;
  frameworkCount: number;
  frameworks: CustomAlignmentFramework[];
}

export interface ULOFrameworkItemMapping {
  id: string;
  uloId: string;
  itemId: string;
  isAiSuggested: boolean;
  notes?: string;
  createdAt: string;
  updatedAt: string;
}

export interface ULOItemMappingCreate {
  itemId: string;
  isAiSuggested?: boolean;
  notes?: string;
}

export interface BulkULOItemMappingCreate {
  mappings: ULOItemMappingCreate[];
}
