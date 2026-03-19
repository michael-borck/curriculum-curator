/**
 * LLM Configuration API Service
 */

import api from './api';
import type {
  LLMConfigResponse,
  LLMConfigRequest,
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
      '/llm-config/test',
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
      `/llm-config/models/${provider}?${params.toString()}`
    );
    return response.data;
  }

  /**
   * Get user's LLM configurations
   */
  async getUserConfigurations(): Promise<LLMConfigResponse[]> {
    const response = await api.get<LLMConfigResponse[]>(
      '/llm-config/configurations'
    );
    return response.data;
  }

  /**
   * Get system-wide LLM configurations (admin only)
   */
  async getSystemConfigurations(): Promise<LLMConfigResponse[]> {
    const response = await api.get<LLMConfigResponse[]>(
      '/llm-config/configurations/system'
    );
    return response.data;
  }

  /**
   * Create a new LLM configuration
   */
  async createConfiguration(
    config: LLMConfigRequest
  ): Promise<LLMConfigResponse> {
    const response = await api.post<LLMConfigResponse>(
      '/llm-config/configurations',
      config
    );
    return response.data;
  }

  /**
   * Create a system-wide LLM configuration (admin only)
   */
  async createSystemConfiguration(
    config: LLMConfigRequest
  ): Promise<LLMConfigResponse> {
    const response = await api.post<LLMConfigResponse>(
      '/llm-config/configurations/system',
      config
    );
    return response.data;
  }

  /**
   * Get all user configurations (admin only)
   */
  async getAllUserConfigurations(): Promise<LLMConfigResponse[]> {
    const response = await api.get<LLMConfigResponse[]>(
      '/llm-config/configurations/users'
    );
    return response.data;
  }

  /**
   * Update an LLM configuration
   */
  async updateConfiguration(
    id: string,
    config: Partial<LLMConfigRequest>
  ): Promise<LLMConfigResponse> {
    const response = await api.put<LLMConfigResponse>(
      `/llm-config/configurations/${id}`,
      config
    );
    return response.data;
  }

  /**
   * Delete an LLM configuration
   */
  async deleteConfiguration(id: string): Promise<void> {
    await api.delete(`/llm-config/configurations/${id}`);
  }

  /**
   * Get token usage statistics
   */
  async getTokenStats(days: number = 30): Promise<TokenUsageStats> {
    const response = await api.get<TokenUsageStats>(
      `/llm-config/usage/stats?days=${days}`
    );
    return response.data;
  }

  /**
   * Get token usage statistics for all users (admin only)
   */
  async getAllUsersTokenStats(days: number = 30): Promise<TokenUsageStats[]> {
    const response = await api.get<TokenUsageStats[]>(
      `/llm-config/usage/stats/all?days=${days}`
    );
    return response.data;
  }
}

const llmApi = new LLMApiService();
export { llmApi };
export default llmApi;
