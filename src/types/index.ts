// Core domain types
export interface ContentRequest {
  topic: string;
  learningObjectives: string[];
  duration: string;
  audience: string;
  contentTypes: ContentType[];
}

export type ContentType = 
  | 'Slides'
  | 'InstructorNotes'
  | 'Worksheet'
  | 'Quiz'
  | 'ActivityGuide';

export interface ContentMetadata {
  wordCount: number;
  estimatedDuration: string;
  difficultyLevel: string;
}

export interface GeneratedContent {
  contentType: ContentType;
  title: string;
  content: string;
  metadata: ContentMetadata;
}

// Session types
export interface Session {
  id: string;
  name: string;
  createdAt: string;
  updatedAt: string;
  contentRequest?: ContentRequest;
  generatedContent: GeneratedContent[];
  config: SessionConfig;
}

export interface SessionConfig {
  autoSave: boolean;
  backupIntervalMinutes: number;
  maxHistoryItems: number;
}

// Validation types
export interface ValidationResult {
  passed: boolean;
  score: number;
  issues: ValidationIssue[];
  suggestions: string[];
}

export interface ValidationIssue {
  severity: 'Error' | 'Warning' | 'Info';
  message: string;
  location?: string;
}

// LLM types
export type ProviderType = 'Ollama' | 'OpenAI' | 'Claude' | 'Gemini';

export interface LLMProvider {
  id: string;
  name: string;
  type: ProviderType;
  isLocal: boolean;
  requiresApiKey: boolean;
  status: 'available' | 'configured' | 'not_configured' | 'error';
}

export interface LLMResponse {
  content: string;
  tokensUsed: number;
  costUsd?: number;
}

// Export types
export type ExportFormat = 'Markdown' | 'Html' | 'Pdf' | 'PowerPoint' | 'Word';

export interface ExportOptions {
  format: ExportFormat;
  outputPath: string;
  templateName?: string;
  includeMetadata: boolean;
}

export interface ExportResult {
  success: boolean;
  outputPath: string;
  fileSize?: number;
  errorMessage?: string;
}

// UI state types
export type AppMode = 'wizard' | 'expert';

export interface UISettings {
  mode: AppMode;
  theme: 'light' | 'dark' | 'system';
  fontSize: 'small' | 'medium' | 'large';
  showAdvancedOptions: boolean;
}

// Error types
export interface AppError {
  message: string;
  code?: string;
  context?: Record<string, any>;
}

// Configuration types
export interface AppConfig {
  defaultProvider: string;
  autoSave: boolean;
  showCostTracking: boolean;
  validationEnabled: boolean;
  exportDefaults: {
    format: ExportFormat;
    includeMetadata: boolean;
  };
}