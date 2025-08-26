/**
 * Types for the guided content creation workflow
 */

export enum WorkflowStage {
  INITIAL = 'initial',
  COURSE_OVERVIEW = 'course_overview',
  LEARNING_OUTCOMES = 'learning_outcomes',
  UNIT_BREAKDOWN = 'unit_breakdown',
  WEEKLY_PLANNING = 'weekly_planning',
  CONTENT_GENERATION = 'content_generation',
  QUALITY_REVIEW = 'quality_review',
  COMPLETED = 'completed',
}

export enum SessionStatus {
  ACTIVE = 'active',
  PAUSED = 'paused',
  COMPLETED = 'completed',
  CANCELLED = 'cancelled',
}

export interface WorkflowSession {
  id: string;
  name: string;
  unitId: string;
  status: SessionStatus;
  currentStage: WorkflowStage;
  progress: number;
  createdAt: string;
  updatedAt: string;
  messageCount: number;
}

export interface WorkflowQuestion {
  question_key: string;
  question_text: string;
  options?: string[];
  input_type: 'select' | 'text' | 'number' | 'multiselect';
  required: boolean;
  depends_on?: string;
  stage: WorkflowStage;
  progress: number;
}

export interface WorkflowAnswer {
  question_key: string;
  answer: string | number | string[];
}

export interface WorkflowDecision {
  key: string;
  value: any;
  timestamp: string;
}

export interface WorkflowStatus {
  session_id: string;
  status: SessionStatus;
  currentStage: WorkflowStage;
  progressPercentage: number;
  decisionsMade: Record<string, WorkflowDecision>;
  messageCount: number;
  canGenerateStructure: boolean;
  durationMinutes?: number;
}

export interface WorkflowStageInfo {
  stage: WorkflowStage;
  name: string;
  description: string;
  order: number;
}

export interface UnitStructureResult {
  status: 'success' | 'exists' | 'error';
  message: string;
  outlineId?: string;
  components?: {
    learningOutcomes: number;
    weeklyTopics: number;
    assessments: number;
  };
}

export interface PDFAnalysisResult {
  status: string;
  filename: string;
  document_type: string;
  metadata: {
    title: string;
    page_count: number;
    wordCount: number;
    has_toc: boolean;
  };
  extracted_content: {
    sections_count: number;
    learning_outcomes_count: number;
    assessments_count: number;
    weekly_content_count: number;
    key_concepts_count: number;
  };
  course_structure: any;
  sections: Array<{
    title: string;
    level: number;
    page_start: number;
    wordCount: number;
  }>;
}
