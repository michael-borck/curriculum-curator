import { ReactNode, FormEvent, ChangeEvent, MouseEvent } from 'react';

// Add Course as an alias for Unit for backwards compatibility
export type Course = Unit;

// AI Assistance Levels
export type AIAssistLevel = 'none' | 'refine' | 'create';

// User related types
export interface User {
  id?: string;
  email: string;
  name: string;
  role: 'lecturer' | 'admin' | 'student' | 'assistant';
  teachingPhilosophy?: string;
  languagePreference?: string;
  teachingPreferences?: {
    aiAssistLevel?: AIAssistLevel;
  };
  llmConfig?: {
    provider?: string;
    model?: string;
    openaiApiKey?: string;
    anthropicApiKey?: string;
    geminiApiKey?: string;
  };
}

// Unit related types
export interface UnitModule {
  id: number | string;
  title: string;
  type: 'lecture' | 'assignment' | 'project' | 'quiz';
  completed: boolean;
  description?: string;
  duration?: string;
}

export interface Unit {
  id: string;
  title: string;
  code: string;
  description?: string;
  year: number;
  semester: string;
  status: string;
  pedagogyType: string;
  difficultyLevel: string;
  durationWeeks: number;
  creditPoints: number;
  prerequisites?: string;
  learningHours?: number;
  unitMetadata?: any;
  generationContext?: string;
  ownerId: string;
  createdById: string;
  updatedById?: string;
  createdAt: string;
  updatedAt: string;
  // Frontend-specific fields (optional)
  modules?: UnitModule[];
  progressPercentage?: number;
  moduleCount?: number;
  materialCount?: number;
  designCount?: number;
}

// Content related types
export type ContentType =
  | 'syllabus'
  | 'schedule'
  | 'lecture'
  | 'module'
  | 'worksheet'
  | 'faq'
  | 'quiz'
  | 'short_answer'
  | 'matching'
  | 'case_study'
  | 'interactive'
  | 'resource' // Renamed from 'reading'
  | 'assignment'
  | 'project'
  | 'assessment'
  | 'video'
  | 'podcast'
  | 'tutorial';
export type PedagogyType =
  | 'inquiry-based'
  | 'project-based'
  | 'traditional'
  | 'collaborative'
  | 'game-based'
  | 'constructivist'
  | 'problem-based'
  | 'experiential'
  | 'competency-based';
export type DifficultyLevel = 'beginner' | 'intermediate' | 'advanced';

export interface Content {
  id: string;
  title: string;
  contentType: string;
  status: string;
  unitId: string;
  orderIndex: number;
  body: string; // Markdown content
  summary?: string;
  weekNumber?: number;
  estimatedDurationMinutes?: number;
  currentCommit?: string;
  createdAt: string;
  updatedAt?: string;
}

// Alias for backwards compatibility
export interface ContentLegacy {
  id: string;
  title: string;
  type: string;
  status: string;
  unitId: string;
  parentContentId?: string;
  orderIndex: number;
  contentMarkdown: string;
  summary: string;
  estimatedDurationMinutes?: number;
  difficultyLevel?: string;
  createdAt: string;
  updatedAt: string;
}

export interface UnitListResponse {
  units: Unit[];
  total: number;
}

export interface ContentListResponse {
  contents: Content[];
  total: number;
  skip: number;
  limit: number;
}

export interface ContentRequest {
  type: ContentType;
  pedagogy: PedagogyType;
  topic?: string;
  difficulty?: DifficultyLevel;
  duration?: string;
}

export interface GeneratedContent {
  id?: string;
  content: string;
  type: ContentType;
  pedagogy: PedagogyType;
  metadata?: {
    wordCount?: number;
    estimatedDuration?: string;
    difficulty?: DifficultyLevel;
  };
}

// Component prop types
export interface DashboardProps {
  children: ReactNode;
  onLogout: () => void;
}

export interface LoginProps {
  onBackToLanding: () => void;
}

export interface LandingProps {
  onSignInClick: () => void;
}

export interface PedagogySelectorProps {
  selected: PedagogyType;
  onChange: (pedagogy: PedagogyType) => void;
}

export interface RichTextEditorProps {
  content: string;
  onChange: (content: string) => void;
  pedagogyHints?: string[] | undefined;
  unitId?: string | undefined;
  materialId?: string | undefined;
}

// API related types
export interface ApiResponse<T = any> {
  data: T;
  success: boolean;
  message?: string;
}

export interface StreamedContentData {
  content: string;
  isComplete?: boolean;
}

// Auth store types (extending existing)
export interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  login: (user: User) => void;
  logout: () => void;
}

// Form types
export interface LoginFormData {
  email: string;
  password: string;
}

export interface UnitFormData {
  title: string;
  description: string;
  pedagogy: PedagogyType;
  difficulty: DifficultyLevel;
  duration: string;
  learningObjectives: string[];
}

// Event handler types
export type HandleSubmitFunction = (
  e: FormEvent<HTMLFormElement>
) => void | Promise<void>;
export type HandleChangeFunction = (
  e: ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
) => void;
export type HandleClickFunction = (
  e: MouseEvent<HTMLButtonElement>
) => void | Promise<void>;

// Utility types
export type Optional<T, K extends keyof T> = Omit<T, K> & Partial<Pick<T, K>>;
export type RequiredFields<T, K extends keyof T> = T & Required<Pick<T, K>>;
