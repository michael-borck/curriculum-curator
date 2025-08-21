/**
 * LLM Configuration API Service
 */

import api from './api';
import type {
  LLMConfig,
  LLMTestRequest,
  LLMTestResponse,
  TokenUsageStats,
  LLMProvider,
} from '../types/llm';

class LLMApiService {
  /**
   * Test LLM connection
   */
  async testConnection(request: LLMTestRequest): Promise<LLMTestResponse> {
    const response = await api.post<LLMTestResponse>(
      '/api/llm-config/test',
      request
    );
    return response.data;
  }

  /**
   * List available models for a provider
   */
  async listModels(
    provider: LLMProvider,
    apiKey?: string,
    apiUrl?: string,
    bearerToken?: string
  ): Promise<string[]> {
    const params = new URLSearchParams();
    if (apiKey) params.append('api_key', apiKey);
    if (apiUrl) params.append('api_url', apiUrl);
    if (bearerToken) params.append('bearer_token', bearerToken);

    const response = await api.get<string[]>(
      `/api/llm-config/models/${provider}?${params.toString()}`
    );
    return response.data;
  }

  /**
   * Get user's LLM configurations
   */
  async getUserConfigurations(): Promise<LLMConfig[]> {
    const response = await api.get<LLMConfig[]>(
      '/api/llm-config/configurations'
    );
    return response.data;
  }

  /**
   * Get system-wide LLM configurations (admin only)
   */
  async getSystemConfigurations(): Promise<LLMConfig[]> {
    const response = await api.get<LLMConfig[]>(
      '/api/llm-config/configurations/system'
    );
    return response.data;
  }

  /**
   * Create a new LLM configuration
   */
  async createConfiguration(config: Omit<LLMConfig, 'id'>): Promise<LLMConfig> {
    const response = await api.post<LLMConfig>(
      '/api/llm-config/configurations',
      config
    );
    return response.data;
  }

  /**
   * Create a system-wide LLM configuration (admin only)
   */
  async createSystemConfiguration(
    config: Omit<LLMConfig, 'id'>
  ): Promise<LLMConfig> {
    const response = await api.post<LLMConfig>(
      '/api/llm-config/configurations/system',
      config
    );
    return response.data;
  }

  /**
   * Update an LLM configuration
   */
  async updateConfiguration(
    id: string,
    config: Partial<LLMConfig>
  ): Promise<LLMConfig> {
    const response = await api.put<LLMConfig>(
      `/api/llm-config/configurations/${id}`,
      config
    );
    return response.data;
  }

  /**
   * Delete an LLM configuration
   */
  async deleteConfiguration(id: string): Promise<void> {
    await api.delete(`/api/llm-config/configurations/${id}`);
  }

  /**
   * Get token usage statistics
   */
  async getTokenStats(days: number = 30): Promise<TokenUsageStats> {
    const response = await api.get<TokenUsageStats>(
      `/api/llm-config/usage/stats?days=${days}`
    );
    return response.data;
  }

  /**
   * Get token usage statistics for all users (admin only)
   */
  async getAllUsersTokenStats(days: number = 30): Promise<TokenUsageStats[]> {
    const response = await api.get<TokenUsageStats[]>(
      `/api/llm-config/usage/stats/all?days=${days}`
    );
    return response.data;
  }
}

export default new LLMApiService();
