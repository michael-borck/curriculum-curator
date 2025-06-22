import { useState, useCallback, useEffect } from 'react';
import { invoke } from '@tauri-apps/api/core';

export interface SessionListItem {
  id: string;
  name: string;
  created_at: string;
  updated_at: string;
  content_count: number;
  preview: string;
  tags: string[];
  is_favorite: boolean;
  content_types: string[];
  topic: string;
  complexity: string;
  duration: string;
  cost_estimate?: number;
}

export interface SessionFilter {
  search?: string;
  start_date?: string;
  end_date?: string;
  tags?: string[];
  content_types?: string[];
  is_favorite?: boolean;
  sort_by?: 'created_at' | 'updated_at' | 'name';
  sort_order?: 'asc' | 'desc';
  limit?: number;
  offset?: number;
}

export interface SessionStatistics {
  total_sessions: number;
  total_content_items: number;
  total_cost: number;
  sessions_this_week: number;
  sessions_this_month: number;
  most_used_content_types: Array<{ type: string; count: number }>;
  average_session_cost: number;
  favorite_count: number;
}

export function useSessionManagement() {
  const [sessions, setSessions] = useState<SessionListItem[]>([]);
  const [statistics, setStatistics] = useState<SessionStatistics | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [currentFilter, setCurrentFilter] = useState<SessionFilter>({
    sort_by: 'updated_at',
    sort_order: 'desc',
    limit: 50
  });

  const loadSessions = useCallback(async (filter?: SessionFilter) => {
    setIsLoading(true);
    setError(null);
    
    try {
      const finalFilter = { ...currentFilter, ...filter };
      setCurrentFilter(finalFilter);
      
      const result = await invoke<SessionListItem[]>('list_sessions', {
        filter: finalFilter
      });
      
      setSessions(result);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load sessions';
      setError(errorMessage);
      console.error('Failed to load sessions:', err);
    } finally {
      setIsLoading(false);
    }
  }, [currentFilter]);

  const loadStatistics = useCallback(async () => {
    try {
      const stats = await invoke<SessionStatistics>('get_session_statistics');
      setStatistics(stats);
    } catch (err) {
      console.error('Failed to load session statistics:', err);
    }
  }, []);

  const createSession = useCallback(async (name: string, config?: Record<string, unknown>) => {
    try {
      const result = await invoke<{ session_id: string }>('create_session', {
        name,
        config: config || {}
      });
      
      // Refresh sessions list
      await loadSessions();
      
      return result.session_id;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to create session';
      setError(errorMessage);
      throw new Error(errorMessage);
    }
  }, [loadSessions]);

  const duplicateSession = useCallback(async (sessionId: string, newName?: string) => {
    try {
      const result = await invoke<{ session_id: string }>('duplicate_session', {
        sessionId,
        newName
      });
      
      // Refresh sessions list
      await loadSessions();
      
      return result.session_id;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to duplicate session';
      setError(errorMessage);
      throw new Error(errorMessage);
    }
  }, [loadSessions]);

  const deleteSession = useCallback(async (sessionId: string) => {
    try {
      await invoke('delete_session', { sessionId });
      
      // Refresh sessions list
      await loadSessions();
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to delete session';
      setError(errorMessage);
      throw new Error(errorMessage);
    }
  }, [loadSessions]);

  const updateSession = useCallback(async (sessionId: string, updates: {
    name?: string;
    tags?: string[];
    is_favorite?: boolean;
  }) => {
    try {
      await invoke('update_session', {
        sessionId,
        updates
      });
      
      // Refresh sessions list
      await loadSessions();
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to update session';
      setError(errorMessage);
      throw new Error(errorMessage);
    }
  }, [loadSessions]);

  const loadSession = useCallback(async (sessionId: string) => {
    try {
      const result = await invoke('load_session', { sessionId });
      return result;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load session';
      setError(errorMessage);
      throw new Error(errorMessage);
    }
  }, []);

  const searchSessions = useCallback(async (query: string) => {
    await loadSessions({
      search: query,
      limit: 20
    });
  }, [loadSessions]);

  const filterByTags = useCallback(async (tags: string[]) => {
    await loadSessions({
      tags,
      limit: 50
    });
  }, [loadSessions]);

  const toggleFavorite = useCallback(async (sessionId: string, isFavorite: boolean) => {
    await updateSession(sessionId, { is_favorite: isFavorite });
  }, [updateSession]);

  const getRecentSessions = useCallback(async (limit: number = 10) => {
    await loadSessions({
      sort_by: 'updated_at',
      sort_order: 'desc',
      limit
    });
  }, [loadSessions]);

  // Load initial data
  useEffect(() => {
    loadSessions();
    loadStatistics();
  }, []);

  // Utility functions
  const getSessionsByContentType = useCallback((contentType: string) => {
    return sessions.filter(session => 
      session.content_types.includes(contentType)
    );
  }, [sessions]);

  const getFavoriteSessions = useCallback(() => {
    return sessions.filter(session => session.is_favorite);
  }, [sessions]);

  const getSessionsByTag = useCallback((tag: string) => {
    return sessions.filter(session => 
      session.tags.includes(tag)
    );
  }, [sessions]);

  const getAllTags = useCallback(() => {
    const tagSet = new Set<string>();
    sessions.forEach(session => {
      session.tags.forEach(tag => tagSet.add(tag));
    });
    return Array.from(tagSet).sort();
  }, [sessions]);

  return {
    // State
    sessions,
    statistics,
    isLoading,
    error,
    currentFilter,
    
    // Actions
    loadSessions,
    loadStatistics,
    createSession,
    duplicateSession,
    deleteSession,
    updateSession,
    loadSession,
    searchSessions,
    filterByTags,
    toggleFavorite,
    getRecentSessions,
    
    // Utility functions
    getSessionsByContentType,
    getFavoriteSessions,
    getSessionsByTag,
    getAllTags,
    
    // Reset functions
    clearError: () => setError(null),
    resetFilter: () => setCurrentFilter({
      sort_by: 'updated_at',
      sort_order: 'desc',
      limit: 50
    })
  };
}