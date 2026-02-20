/**
 * Ollama API Service for local AI model management
 */

import api from './api';
import type {
  OllamaStatus,
  OllamaRecommendation,
  OllamaTestResult,
  PullProgress,
} from '../types/ollama';

class OllamaApiService {
  async getStatus(): Promise<OllamaStatus> {
    const response = await api.get<OllamaStatus>('/ollama/status');
    return response.data;
  }

  async getRecommendation(): Promise<OllamaRecommendation> {
    const response = await api.get<OllamaRecommendation>('/ollama/recommend');
    return response.data;
  }

  /**
   * Pull (download) a model with SSE progress streaming.
   * Returns an EventSource-like interface via fetch.
   */
  pullModel(
    model: string,
    onProgress: (progress: PullProgress) => void,
    onError: (error: string) => void,
    onComplete: () => void
  ): AbortController {
    const controller = new AbortController();
    const token = localStorage.getItem('token');

    window
      .fetch('/api/ollama/pull', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ model }),
        signal: controller.signal,
      })
      .then(async response => {
        if (!response.ok) {
          const text = await response.text();
          onError(`HTTP ${response.status}: ${text}`);
          return;
        }

        const reader = response.body?.getReader();
        if (!reader) {
          onError('No response body');
          return;
        }

        const decoder = new TextDecoder();
        let buffer = '';

        let done = false;
        while (!done) {
          const result = await reader.read();
          done = result.done;
          if (done) break;
          const value = result.value;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          buffer = lines.pop() || '';

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const data = JSON.parse(line.slice(6)) as PullProgress;
                if (data.status === 'error') {
                  onError(data.error || 'Unknown error');
                  return;
                }
                if (data.status === 'success') {
                  onComplete();
                  return;
                }
                onProgress(data);
              } catch {
                // skip malformed JSON
              }
            }
          }
        }

        onComplete();
      })
      .catch(err => {
        if (err instanceof DOMException && err.name === 'AbortError') return;
        onError(String(err));
      });

    return controller;
  }

  async deleteModel(modelName: string): Promise<void> {
    await api.delete(`/ollama/models/${modelName}`);
  }

  async testModel(model: string, prompt?: string): Promise<OllamaTestResult> {
    const response = await api.post<OllamaTestResult>('/ollama/test', {
      model,
      ...(prompt ? { prompt } : {}),
    });
    return response.data;
  }
}

const ollamaApi = new OllamaApiService();
export { ollamaApi };
export default ollamaApi;
