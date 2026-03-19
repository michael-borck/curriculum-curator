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

/** Shape returned by the backend GET endpoints (secrets are redacted). */
export interface LLMConfigResponse {
  id?: string;
  provider: LLMProvider;
  api_key_preview: string | null;
  api_url?: string;
  has_bearer_token: boolean;
  model_name?: string;
  temperature: number;
  max_tokens?: number;
  is_default: boolean;
  isActive?: boolean;
  userId?: string | null;
  user_email?: string | null;
}

/** Shape sent to the backend when creating / updating a config. */
export interface LLMConfigRequest {
  provider: LLMProvider;
  api_key?: string | undefined;
  api_url?: string | undefined;
  bearer_token?: string | undefined;
  model_name?: string | undefined;
  temperature?: number | undefined;
  max_tokens?: number | undefined;
  is_default?: boolean | undefined;
}

/**
 * Union used by form state — includes writable fields (api_key, bearer_token)
 * plus read-only preview fields so we can populate placeholders from a response.
 */
export interface LLMConfigFormData {
  id?: string;
  provider: LLMProvider;
  api_key?: string;
  api_url?: string;
  bearer_token?: string;
  model_name?: string;
  temperature: number;
  max_tokens?: number;
  is_default: boolean;
  /** Populated from response — used as placeholder text when editing. */
  api_key_preview?: string | null;
  /** Populated from response — shows whether a token is already saved. */
  has_bearer_token?: boolean;
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
  userId: string;
  total_tokens: number;
  total_cost: number;
  by_provider: Record<string, number>;
  by_model: Record<string, number>;
  period_start: string;
  period_end: string;
}

export interface TokenStats {
  userId: string;
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
