/**
 * AI API client — typed wrappers for AI/LLM endpoints.
 */

import api from './api';

// ─── Scaffold Types ──────────────────────────────────────────────────────────

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
  dueWeek: number | null;
}

export interface ScaffoldUnitResponse {
  title: string;
  description: string;
  ulos: ScaffoldULO[];
  weeks: ScaffoldWeek[];
  assessments: ScaffoldAssessment[];
}

// ─── Fill Gap Types ──────────────────────────────────────────────────────────

export interface FillGapResponse {
  gapType: string;
  generatedContent: string;
  suggestions: string[];
}

// ─── Speaker Notes Types ─────────────────────────────────────────────────────

export interface SpeakerNotesDraft {
  slideIndex: number;
  notes: string;
}

export interface GenerateSpeakerNotesResponse {
  drafts: SpeakerNotesDraft[];
}

// ─── Structure Recovery Types (6.16) ─────────────────────────────────────────

export interface RestructureContentResponse {
  contentJson: Record<string, unknown>;
  headingCount: number;
  listCount: number;
  paragraphCount: number;
}

// ─── AI Image Generation Types (15.5 — ADR-068) ──────────────────────────────

export type ImageAspectRatio = 'square' | 'landscape' | 'portrait';

export interface GenerateImageRequest {
  prompt: string;
  aspectRatio: ImageAspectRatio;
  materialId?: string | undefined;
  style?: string | undefined;
}

export interface GenerateImageResponse {
  url: string;
  filename: string;
  modelUsed: string;
}

// ─── Branching Scenario Generation Types (19A.7 — ADR-068) ───────────────────

export interface BranchingChoiceDraft {
  id: string;
  text: string;
  targetCardId: string;
  feedback: string;
}

export type BranchingCardType = 'content' | 'branch' | 'ending';

export interface BranchingCardDraft {
  cardId: string;
  cardType: BranchingCardType;
  cardTitle: string;
  cardContent: string;
  choices: BranchingChoiceDraft[];
  endScore: number;
  endMessage: string;
  stepThreshold: number;
  endMessageEfficient: string;
  endMessageThorough: string;
}

export interface GenerateBranchingResponse {
  cards: BranchingCardDraft[];
  startCardId: string;
  warnings: string[];
}

// ─── Quiz Generation Types (19C.6 — ADR-068) ─────────────────────────────────

export type QuizQuestionType =
  | 'multiple_choice'
  | 'true_false'
  | 'multi_select'
  | 'short_answer'
  | 'fill_in_blank';

export interface QuizOptionDraft {
  id: string;
  text: string;
  correct: boolean;
}

export interface QuizQuestionDraft {
  questionType: QuizQuestionType;
  questionText: string;
  options: QuizOptionDraft[];
  feedback: string;
  explanation: string;
  points: number;
}

export interface GenerateQuizResponse {
  questions: QuizQuestionDraft[];
}

// ─── Lesson Plan Types (5.12/5.13 — ADR-068) ────────────────────────────────

export interface LessonPlanFramework {
  name: string;
  summary: string;
  whenToUse: string;
}

export interface LessonPlanObjective {
  text: string;
  bloomLevel: string;
}

export interface LessonPlanSegment {
  name: string;
  minutes: number;
  description: string;
}

export interface LessonPlanFormativeCheck {
  segment: string;
  question: string;
  misconceptions: string[];
}

export interface LessonPlanResponse {
  title: string;
  objectives: LessonPlanObjective[];
  segments: LessonPlanSegment[];
  formativeChecks: LessonPlanFormativeCheck[];
  differentiationNotes: string;
  materialsChecklist: string[];
  homeworkBridge: string;
}

// ─── API Calls ───────────────────────────────────────────────────────────────

export const aiApi = {
  /** Generate a full unit scaffold from title + description. */
  scaffoldUnit(data: {
    title: string;
    description?: string | undefined;
    durationWeeks?: number | undefined;
    pedagogyStyle?: string | undefined;
    unitId?: string | undefined;
    designId?: string | undefined;
  }) {
    return api.post<ScaffoldUnitResponse>('/ai/scaffold-unit', data);
  },

  /** Generate content to fill a specific gap. */
  fillGap(data: {
    unitId: string;
    gapType: string;
    context?: string;
    designId?: string;
  }) {
    return api.post<FillGapResponse>('/ai/fill-gap', data);
  },

  /** Draft speaker notes for the selected slides of a material. */
  generateSpeakerNotes(materialId: string, slideIndices: number[]) {
    return api.post<GenerateSpeakerNotesResponse>(
      `/ai/materials/${materialId}/generate-speaker-notes`,
      { slideIndices }
    );
  },

  /** Recover structure (headings, lists) from a material's plain content. */
  restructureContent(materialId: string) {
    return api.post<RestructureContentResponse>(
      `/ai/materials/${materialId}/restructure`,
      {}
    );
  },

  /** Generate an image from a text prompt (15.5). With materialId the
   * image is saved into that material's image library and a durable URL
   * is returned; otherwise only a base64 data URL for preview. */
  generateImage(data: GenerateImageRequest) {
    return api.post<GenerateImageResponse>('/ai/generate-image', data);
  },

  /** Draft a branching scenario from a material's content (19A.7). */
  generateBranching(
    materialId: string,
    data: {
      cardCount?: number;
      audience?: string | undefined;
    }
  ) {
    return api.post<GenerateBranchingResponse>(
      `/ai/materials/${materialId}/generate-branching`,
      data
    );
  },

  /** Draft practice questions from a material's content (19C.6). */
  generateQuiz(
    materialId: string,
    data: {
      questionTypes?: QuizQuestionType[];
      count?: number;
    }
  ) {
    return api.post<GenerateQuizResponse>(
      `/ai/materials/${materialId}/generate-quiz`,
      data
    );
  },

  /** List lesson-plan frameworks with when-to-use guidance (5.13). */
  listLessonPlanFrameworks() {
    return api.get<Record<string, LessonPlanFramework>>(
      '/ai/lesson-plan/frameworks'
    );
  },

  /** Generate a framework-structured lesson plan (5.12). */
  generateLessonPlan(data: {
    content: string;
    frameworkId: string;
    durationMinutes?: number;
    classSize?: number | undefined;
    deliveryMode?: string | undefined;
  }) {
    return api.post<LessonPlanResponse>('/ai/generate-lesson-plan', data);
  },
};
