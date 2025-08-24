/**
 * TypeScript interfaces for Unit Structure and Assessment Management
 */

// ============= Enums =============

export enum MaterialType {
  LECTURE = 'lecture',
  TUTORIAL = 'tutorial',
  LAB = 'lab',
  WORKSHOP = 'workshop',
  READING = 'reading',
  VIDEO = 'video',
  ASSIGNMENT = 'assignment',
  OTHER = 'other',
}

export enum MaterialStatus {
  DRAFT = 'draft',
  PUBLISHED = 'published',
  ARCHIVED = 'archived',
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
  type: MaterialType;
  description?: string;
  durationMinutes?: number;
  filePath?: string;
  materialMetadata?: Record<string, any>;
  orderIndex?: number;
  status?: MaterialStatus;
}

export interface MaterialUpdate {
  weekNumber?: number;
  title?: string;
  type?: MaterialType;
  description?: string;
  durationMinutes?: number;
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
  type: MaterialType;
  description?: string;
  durationMinutes?: number;
  filePath?: string;
  materialMetadata?: Record<string, any>;
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
  subScores: {
    alignment: number;
    completion: number;
    assessmentWeights: number;
  };
  grade: string;
  calculatedAt: string;
}

// ============= Filters =============

export interface MaterialFilter {
  weekNumber?: number;
  type?: MaterialType;
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
