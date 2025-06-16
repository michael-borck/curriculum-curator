// React Hook for LLM Operations
// Bridges frontend UI to Tauri backend LLM commands

import { useState, useEffect, useCallback } from 'react';
import { invoke } from '@tauri-apps/api/core';

export interface LLMProvider {
  id: string;
  name: string;
  type: string;
  is_local: boolean;
  requires_api_key: boolean;
  status: 'available' | 'not_installed' | 'not_configured' | 'error';
  base_url?: string;
}

export interface LLMModel {
  id: string;
  name: string;
  description?: string;
  context_length?: number;
  supports_streaming?: boolean;
  supports_vision?: boolean;
  max_output_tokens?: number;
}

export interface GenerationRequest {
  prompt: string;
  model?: string;
  temperature?: number;
  max_tokens?: number;
  stream?: boolean;
}

export interface GenerationResponse {
  success: boolean;
  content?: string;
  model_used?: string;
  tokens_used?: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  };
  response_time_ms?: number;
  cost_usd?: number;
  finish_reason?: string;
  error?: string;
}

export interface ContentGenerationRequest {
  session_id: string;
  topic: string;
  learning_objectives: string[];
  duration: string;
  audience: string;
  content_types: string[];
}

export interface LLMHookState {
  providers: LLMProvider[];
  availableModels: LLMModel[];
  isLoading: boolean;
  error: string | null;
  currentProvider: string | null;
  isConnected: boolean;
  lastGeneration: GenerationResponse | null;
}

export function useLLM() {
  const [state, setState] = useState<LLMHookState>({
    providers: [],
    availableModels: [],
    isLoading: false,
    error: null,
    currentProvider: null,
    isConnected: false,
    lastGeneration: null,
  });

  const updateState = useCallback((updates: Partial<LLMHookState>) => {
    setState(prev => ({ ...prev, ...updates }));
  }, []);

  // Load available LLM providers
  const loadProviders = useCallback(async (): Promise<void> => {
    updateState({ isLoading: true, error: null });
    
    try {
      const providers: LLMProvider[] = await invoke('get_available_providers');
      updateState({ 
        providers, 
        isLoading: false,
        currentProvider: providers.find(p => p.status === 'available')?.id || null
      });
      
      // Auto-load models for available providers
      const availableProvider = providers.find(p => p.status === 'available');
      if (availableProvider) {
        await loadModels(availableProvider.id);
      }
    } catch (error) {
      updateState({ 
        error: `Failed to load providers: ${error}`, 
        isLoading: false 
      });
    }
  }, [updateState]);

  // Load available providers on mount
  useEffect(() => {
    loadProviders();
  }, [loadProviders]);

  // Load models for a specific provider
  const loadModels = async (providerId: string): Promise<void> => {
    updateState({ isLoading: true, error: null });
    
    try {
      let models: LLMModel[] = [];
      
      if (providerId === 'ollama') {
        models = await invoke('get_ollama_models');
      } else {
        // For external providers, we need to check if they're configured
        models = await invoke('get_external_provider_models', { provider: providerId });
      }
      
      updateState({ 
        availableModels: models, 
        isLoading: false,
        currentProvider: providerId,
        isConnected: models.length > 0
      });
    } catch (error) {
      updateState({ 
        error: `Failed to load models for ${providerId}: ${error}`, 
        isLoading: false,
        availableModels: [],
        isConnected: false
      });
    }
  };

  // Test LLM generation with a simple prompt
  const testGeneration = async (
    prompt: string, 
    model?: string, 
    temperature?: number
  ): Promise<GenerationResponse> => {
    updateState({ isLoading: true, error: null });
    
    try {
      const response: GenerationResponse = await invoke('test_llm_generation', {
        prompt,
        model,
        temperature
      });
      
      updateState({ 
        lastGeneration: response, 
        isLoading: false,
        isConnected: response.success
      });
      
      return response;
    } catch (error) {
      const errorResponse: GenerationResponse = {
        success: false,
        error: `Generation failed: ${error}`
      };
      
      updateState({ 
        error: errorResponse.error!, 
        isLoading: false,
        lastGeneration: errorResponse,
        isConnected: false
      });
      
      return errorResponse;
    }
  };

  // Generate content using the backend content generation system
  const generateContent = async (request: ContentGenerationRequest): Promise<unknown[]> => {
    updateState({ isLoading: true, error: null });
    
    try {
      const content = await invoke('generate_content', {
        sessionId: request.session_id,
        topic: request.topic,
        learningObjectives: request.learning_objectives,
        duration: request.duration,
        audience: request.audience,
        contentTypes: request.content_types
      });
      
      updateState({ isLoading: false });
      return content;
    } catch (error) {
      updateState({ 
        error: `Content generation failed: ${error}`, 
        isLoading: false 
      });
      throw error;
    }
  };

  // Check provider health and connectivity
  const checkProviderHealth = async (providerId: string): Promise<boolean> => {
    try {
      const result = await invoke('test_external_provider', { provider: providerId });
      const isHealthy = result.success && result.health_check;
      
      updateState({ isConnected: isHealthy });
      return isHealthy;
    } catch {
      updateState({ isConnected: false });
      return false;
    }
  };

  // Get best available provider (prioritizing offline if preferred)
  const getBestProvider = async (preferOffline: boolean = false): Promise<string | null> => {
    try {
      const result = await invoke('get_best_available_provider', { preferOffline });
      
      if (result.success) {
        const providerId = result.provider.toLowerCase();
        updateState({ currentProvider: providerId });
        return providerId;
      }
      
      return null;
    } catch (error) {
      updateState({ error: `Failed to get best provider: ${error}` });
      return null;
    }
  };

  // Store API key for external provider
  const storeApiKey = async (
    provider: string,
    apiKey: string,
    baseUrl?: string,
    rateLimit?: number
  ): Promise<void> => {
    try {
      await invoke('store_api_key', {
        provider,
        apiKey,
        baseUrl,
        rateLimit
      });
      
      // Reload providers to update status
      await loadProviders();
    } catch (error) {
      updateState({ error: `Failed to store API key: ${error}` });
      throw error;
    }
  };

  // Remove API key for provider
  const removeApiKey = async (provider: string): Promise<void> => {
    try {
      await invoke('remove_api_key', { provider });
      
      // Reload providers to update status
      await loadProviders();
    } catch (error) {
      updateState({ error: `Failed to remove API key: ${error}` });
      throw error;
    }
  };

  // Get provider configuration (without exposing API key)
  const getProviderConfig = async (provider: string): Promise<Record<string, unknown>> => {
    try {
      return await invoke('get_api_key_config', { provider });
    } catch (error) {
      updateState({ error: `Failed to get provider config: ${error}` });
      throw error;
    }
  };

  // Test offline generation capability
  const testOfflineGeneration = async (prompt: string): Promise<GenerationResponse> => {
    updateState({ isLoading: true, error: null });
    
    try {
      const response = await invoke('test_offline_generation', {
        prompt,
        preferOffline: true
      });
      
      const result: GenerationResponse = {
        success: response.success,
        content: response.content,
        model_used: response.model_used,
        tokens_used: response.tokens_used,
        response_time_ms: response.response_time_ms,
        cost_usd: response.cost_usd,
        error: response.error
      };
      
      updateState({ 
        lastGeneration: result, 
        isLoading: false,
        isConnected: result.success
      });
      
      return result;
    } catch (error) {
      const errorResponse: GenerationResponse = {
        success: false,
        error: `Offline generation failed: ${error}`
      };
      
      updateState({ 
        error: errorResponse.error!, 
        isLoading: false,
        lastGeneration: errorResponse
      });
      
      return errorResponse;
    }
  };

  // Get system requirements and recommendations
  const getSystemRequirements = async (availableRamGb: number) => {
    try {
      return await invoke('check_system_requirements', { availableRamGb });
    } catch (error) {
      updateState({ error: `Failed to check system requirements: ${error}` });
      throw error;
    }
  };

  // Get Ollama installation instructions
  const getOllamaInstructions = async () => {
    try {
      return await invoke('get_ollama_installation_instructions');
    } catch (error) {
      updateState({ error: `Failed to get installation instructions: ${error}` });
      throw error;
    }
  };

  // Clear any errors
  const clearError = useCallback(() => {
    updateState({ error: null });
  }, [updateState]);

  return {
    // State
    ...state,
    
    // Actions
    loadProviders,
    loadModels,
    testGeneration,
    generateContent,
    checkProviderHealth,
    getBestProvider,
    storeApiKey,
    removeApiKey,
    getProviderConfig,
    testOfflineGeneration,
    getSystemRequirements,
    getOllamaInstructions,
    clearError,
    
    // Computed properties
    hasAvailableProvider: state.providers.some(p => p.status === 'available'),
    needsConfiguration: state.providers.length > 0 && !state.providers.some(p => p.status === 'available'),
    supportsOffline: state.providers.some(p => p.is_local && p.status === 'available'),
  };
}