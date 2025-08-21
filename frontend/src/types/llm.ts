/**
 * LLM Configuration Types
 */

export enum LLMProvider {
  OPENAI = 'openai',
  ANTHROPIC = 'anthropic',
  GEMINI = 'gemini',
  OLLAMA = 'ollama',
  CUSTOM = 'custom',
}

export interface LLMConfig {
  id?: string;
  provider: LLMProvider;
  api_key?: string;
  api_url?: string;
  bearer_token?: string;
  model_name?: string;
  temperature: number;
  max_tokens?: number;
  is_default: boolean;
  is_active?: boolean;
  user_id?: string | null;
  user_email?: string | null;
}

export interface LLMTestRequest {
  provider: LLMProvider;
  api_key?: string;
  api_url?: string;
  bearer_token?: string;
  model_name?: string;
  test_prompt?: string;
}

export interface LLMTestResponse {
  success: boolean;
  message: string;
  available_models?: string[];
  response_text?: string;
  error?: string;
}

export interface TokenUsageStats {
  user_id: string;
  total_tokens: number;
  total_cost: number;
  by_provider: Record<string, number>;
  by_model: Record<string, number>;
  period_start: string;
  period_end: string;
}

export interface TokenStats {
  user_id: string;
  user_email?: string;
  provider: string;
  total_tokens: number;
  total_cost: number;
  request_count: number;
}

export const PROVIDER_DISPLAY_NAMES: Record<LLMProvider, string> = {
  [LLMProvider.OPENAI]: 'OpenAI',
  [LLMProvider.ANTHROPIC]: 'Anthropic (Claude)',
  [LLMProvider.GEMINI]: 'Google Gemini',
  [LLMProvider.OLLAMA]: 'Ollama (Local)',
  [LLMProvider.CUSTOM]: 'Custom Provider',
};

export const DEFAULT_MODELS: Record<LLMProvider, string[]> = {
  [LLMProvider.OPENAI]: ['gpt-4-turbo-preview', 'gpt-4', 'gpt-3.5-turbo'],
  [LLMProvider.ANTHROPIC]: [
    'claude-3-opus-20240229',
    'claude-3-sonnet-20240229',
    'claude-3-haiku-20240307',
  ],
  [LLMProvider.GEMINI]: ['gemini-pro', 'gemini-pro-vision'],
  [LLMProvider.OLLAMA]: ['llama2', 'mistral', 'codellama'],
  [LLMProvider.CUSTOM]: [],
};
