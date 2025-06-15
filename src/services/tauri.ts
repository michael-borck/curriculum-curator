import { invoke } from '@tauri-apps/api/core';

// Types for Tauri command responses
export interface AppError {
  message: string;
  code?: string;
}

export interface SessionSummary {
  id: string;
  name: string;
  created_at: string;
  updated_at: string;
  has_content_request: boolean;
  content_count: number;
}

export interface GeneratedContent {
  content_type: string;
  title: string;
  content: string;
  metadata: {
    word_count: number;
    estimated_duration: string;
    difficulty_level: string;
  };
}

export interface ValidationResult {
  passed: boolean;
  score: number;
  issues: any[];
  suggestions: string[];
}

export interface LLMProvider {
  id: string;
  name: string;
  type: string;
  is_local: boolean;
  requires_api_key: boolean;
  status: string;
}

export interface ExportResult {
  success: boolean;
  output_path: string;
  file_size: number;
  format: string;
  message: string;
}

// Health and utility commands
export const healthCheck = async (): Promise<string> => {
  return await invoke('health_check');
};

export const createProjectDirectory = async (path: string): Promise<void> => {
  return await invoke('create_project_directory', { path });
};

export const checkFileExists = async (path: string): Promise<boolean> => {
  return await invoke('check_file_exists', { path });
};

// Session management commands
export const createNewSession = async (name: string): Promise<string> => {
  return await invoke('create_new_session', { name });
};

export const listSessions = async (): Promise<SessionSummary[]> => {
  return await invoke('list_sessions');
};

export const getSessionContent = async (sessionId: string): Promise<GeneratedContent[]> => {
  return await invoke('get_session_content', { sessionId });
};

export const getSessionCost = async (sessionId: string): Promise<number> => {
  return await invoke('get_session_cost', { sessionId });
};

// Content generation commands
export const generateContent = async (
  sessionId: string,
  topic: string,
  learningObjectives: string[],
  duration: string,
  audience: string,
  contentTypes: string[]
): Promise<GeneratedContent[]> => {
  return await invoke('generate_content', {
    sessionId,
    topic,
    learningObjectives,
    duration,
    audience,
    contentTypes,
  });
};

// Configuration commands
export const getAppConfig = async (key: string): Promise<string | null> => {
  return await invoke('get_app_config', { key });
};

export const setAppConfig = async (key: string, value: string): Promise<void> => {
  return await invoke('set_app_config', { key, value });
};

// Validation commands
export const validateContent = async (
  content: string,
  validatorName: string
): Promise<ValidationResult> => {
  return await invoke('validate_content', { content, validatorName });
};

// LLM provider commands
export const getAvailableProviders = async (): Promise<LLMProvider[]> => {
  return await invoke('get_available_providers');
};

export const testLLMConnection = async (provider: string): Promise<boolean> => {
  return await invoke('test_llm_connection', { provider });
};

// Export commands
export const exportContent = async (
  sessionId: string,
  format: string,
  outputPath: string
): Promise<ExportResult> => {
  return await invoke('export_content', { sessionId, format, outputPath });
};

// Error handling utility
export const handleTauriError = (error: any): AppError => {
  if (typeof error === 'string') {
    return { message: error };
  }
  if (error && typeof error === 'object') {
    return {
      message: error.message || 'Unknown error occurred',
      code: error.code,
    };
  }
  return { message: 'Unknown error occurred' };
};