import { useState, useEffect, useCallback } from 'react';
import * as tauriService from '../services/tauri';
import { AppError } from '../types';

// Custom hook for health check
export const useHealthCheck = () => {
  const [isHealthy, setIsHealthy] = useState<boolean | null>(null);
  const [error, setError] = useState<AppError | null>(null);

  const checkHealth = useCallback(async () => {
    try {
      await tauriService.healthCheck();
      setIsHealthy(true);
      setError(null);
    } catch (err) {
      setIsHealthy(false);
      setError(tauriService.handleTauriError(err));
    }
  }, []);

  useEffect(() => {
    checkHealth();
  }, [checkHealth]);

  return { isHealthy, error, refetch: checkHealth };
};

// Custom hook for session management
export const useSessions = () => {
  const [sessions, setSessions] = useState<tauriService.SessionSummary[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<AppError | null>(null);

  const loadSessions = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const sessionList = await tauriService.listSessions();
      setSessions(sessionList);
    } catch (err) {
      setError(tauriService.handleTauriError(err));
    } finally {
      setLoading(false);
    }
  }, []);

  const createSession = useCallback(async (name: string) => {
    setError(null);
    try {
      const sessionId = await tauriService.createNewSession(name);
      await loadSessions(); // Refresh the list
      return sessionId;
    } catch (err) {
      const error = tauriService.handleTauriError(err);
      setError(error);
      throw error;
    }
  }, [loadSessions]);

  useEffect(() => {
    loadSessions();
  }, [loadSessions]);

  return {
    sessions,
    loading,
    error,
    createSession,
    refetch: loadSessions,
  };
};

// Custom hook for session content
export const useSessionContent = (sessionId: string | null) => {
  const [content, setContent] = useState<tauriService.GeneratedContent[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<AppError | null>(null);

  const loadContent = useCallback(async () => {
    if (!sessionId) {
      setContent([]);
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const sessionContent = await tauriService.getSessionContent(sessionId);
      setContent(sessionContent);
    } catch (err) {
      setError(tauriService.handleTauriError(err));
    } finally {
      setLoading(false);
    }
  }, [sessionId]);

  useEffect(() => {
    loadContent();
  }, [loadContent]);

  return {
    content,
    loading,
    error,
    refetch: loadContent,
  };
};

// Custom hook for content generation
export const useContentGeneration = () => {
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<AppError | null>(null);

  const generateContent = useCallback(async (
    sessionId: string,
    topic: string,
    learningObjectives: string[],
    duration: string,
    audience: string,
    contentTypes: string[]
  ) => {
    setGenerating(true);
    setError(null);
    try {
      const result = await tauriService.generateContent(
        sessionId,
        topic,
        learningObjectives,
        duration,
        audience,
        contentTypes
      );
      return result;
    } catch (err) {
      const error = tauriService.handleTauriError(err);
      setError(error);
      throw error;
    } finally {
      setGenerating(false);
    }
  }, []);

  return {
    generateContent,
    generating,
    error,
  };
};

// Custom hook for LLM providers
export const useLLMProviders = () => {
  const [providers, setProviders] = useState<tauriService.LLMProvider[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<AppError | null>(null);

  const loadProviders = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const providerList = await tauriService.getAvailableProviders();
      setProviders(providerList);
    } catch (err) {
      setError(tauriService.handleTauriError(err));
    } finally {
      setLoading(false);
    }
  }, []);

  const testConnection = useCallback(async (provider: string) => {
    setError(null);
    try {
      return await tauriService.testLLMConnection(provider);
    } catch (err) {
      const error = tauriService.handleTauriError(err);
      setError(error);
      throw error;
    }
  }, []);

  useEffect(() => {
    loadProviders();
  }, [loadProviders]);

  return {
    providers,
    loading,
    error,
    testConnection,
    refetch: loadProviders,
  };
};

// Custom hook for app configuration
export const useAppConfig = (key: string) => {
  const [value, setValue] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<AppError | null>(null);

  const loadConfig = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const configValue = await tauriService.getAppConfig(key);
      setValue(configValue);
    } catch (err) {
      setError(tauriService.handleTauriError(err));
    } finally {
      setLoading(false);
    }
  }, [key]);

  const updateConfig = useCallback(async (newValue: string) => {
    setError(null);
    try {
      await tauriService.setAppConfig(key, newValue);
      setValue(newValue);
    } catch (err) {
      const error = tauriService.handleTauriError(err);
      setError(error);
      throw error;
    }
  }, [key]);

  useEffect(() => {
    loadConfig();
  }, [loadConfig]);

  return {
    value,
    loading,
    error,
    updateConfig,
    refetch: loadConfig,
  };
};