import { ReactNode, FormEvent, ChangeEvent, MouseEvent } from 'react';

// User related types
export interface User {
  id?: string;
  email: string;
  name: string;
  role: 'USER' | 'ADMIN';
}

// Course related types
export interface CourseModule {
  id: number | string;
  title: string;
  type: 'lecture' | 'assignment' | 'project' | 'quiz';
  completed: boolean;
  description?: string;
  duration?: string;
}

export interface Course {
  id: string | number;
  title: string;
  description: string;
  pedagogy: PedagogyType;
  difficulty: DifficultyLevel;
  duration: string;
  learningObjectives: string[];
  modules: CourseModule[];
  createdAt: string;
  updatedAt?: string;
  authorId?: string;
}

// Content related types
export type ContentType = 'lecture' | 'assignment' | 'project' | 'quiz';
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
  pedagogyHints?: string[];
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

export interface CourseFormData {
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
