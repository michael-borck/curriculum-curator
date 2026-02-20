/**
 * Ollama-related types for local AI management
 */

export interface OllamaModel {
  name: string;
  modified_at: string;
  size: number;
  digest: string;
  details?: {
    format: string;
    family: string;
    parameter_size: string;
    quantization_level: string;
  };
}

export interface OllamaStatus {
  available: boolean;
  models: OllamaModel[];
  recommended: string;
}

export interface OllamaRecommendation {
  recommended_model: string;
  label: string;
  reason: string;
  total_ram_gb: number;
  available_ram_gb: number;
}

export interface PullProgress {
  status: string;
  digest?: string;
  total?: number;
  completed?: number;
  error?: string;
}

export interface OllamaTestResult {
  success: boolean;
  response?: string;
  error?: string;
  model: string;
}
