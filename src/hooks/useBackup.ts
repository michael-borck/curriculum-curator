import { useState, useCallback, useEffect } from 'react';
import { invoke } from '@tauri-apps/api/core';

// Define base types first
export interface BackupInterval {
  Never: null;
  EverySession: null;
  Every5Minutes: null;
  Every15Minutes: null;
  Every30Minutes: null;
  Hourly: null;
  Daily: null;
}

export interface BackupType {
  Automatic: null;
  Manual: null;
  OnSessionClose: null;
  OnContentGeneration: null;
  BeforeImport: null;
}

// Export types that depend on base types
export interface BackupFilter {
  session_id?: string;
  backup_type?: BackupType;
  start_date?: string;
  end_date?: string;
  auto_generated_only?: boolean;
  limit?: number;
  offset?: number;
}

export interface BackupListItem {
  id: string;
  session_id: string;
  session_name: string;
  created_at: string;
  backup_type: BackupType;
  file_size: number;
  content_count: number;
  auto_generated: boolean;
  is_recoverable: boolean;
}

export interface BackupConfig {
  enabled: boolean;
  auto_backup_interval: BackupInterval;
  backup_on_session_close: boolean;
  backup_on_content_generation: boolean;
  max_backups_per_session: number;
  max_total_backups: number;
  compress_backups: boolean;
  backup_location?: string;
}

// BackupInterval, BackupType, BackupListItem and BackupFilter already defined above

export interface BackupStatistics {
  total_backups: number;
  total_size: number;
  automatic_backups: number;
  manual_backups: number;
  sessions_with_backups: number;
  oldest_backup?: string;
  newest_backup?: string;
  average_backup_size: number;
}

export function useBackup() {
  const [backups, setBackups] = useState<BackupListItem[]>([]);
  const [statistics, setStatistics] = useState<BackupStatistics | null>(null);
  const [config, setConfig] = useState<BackupConfig | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadBackups = useCallback(async (filter?: BackupFilter) => {
    setIsLoading(true);
    setError(null);
    
    try {
      const result = await invoke<BackupListItem[]>('list_backups', { filter });
      setBackups(result);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load backups';
      setError(errorMessage);
      console.error('Failed to load backups:', err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const loadStatistics = useCallback(async () => {
    try {
      const stats = await invoke<BackupStatistics>('get_backup_statistics');
      setStatistics(stats);
    } catch (err) {
      console.error('Failed to load backup statistics:', err);
    }
  }, []);

  const loadConfig = useCallback(async () => {
    try {
      const backupConfig = await invoke<BackupConfig>('get_backup_config');
      setConfig(backupConfig);
    } catch (err) {
      console.error('Failed to load backup config:', err);
    }
  }, []);

  const createManualBackup = useCallback(async (sessionId: string) => {
    try {
      setError(null);
      const backupId = await invoke<string>('create_manual_backup', { sessionId });
      
      // Refresh backups list
      await loadBackups();
      await loadStatistics();
      
      return backupId;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to create backup';
      setError(errorMessage);
      throw new Error(errorMessage);
    }
  }, [loadBackups, loadStatistics]);

  const restoreFromBackup = useCallback(async (backupId: string) => {
    try {
      setError(null);
      const newSessionId = await invoke<string>('restore_from_backup', { backupId });
      return newSessionId;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to restore backup';
      setError(errorMessage);
      throw new Error(errorMessage);
    }
  }, []);

  const deleteBackup = useCallback(async (backupId: string) => {
    try {
      setError(null);
      await invoke('delete_backup', { backupId });
      
      // Refresh backups list
      await loadBackups();
      await loadStatistics();
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to delete backup';
      setError(errorMessage);
      throw new Error(errorMessage);
    }
  }, [loadBackups, loadStatistics]);

  const updateConfig = useCallback(async (newConfig: BackupConfig) => {
    try {
      setError(null);
      await invoke('update_backup_config', { config: newConfig });
      setConfig(newConfig);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to update backup config';
      setError(errorMessage);
      throw new Error(errorMessage);
    }
  }, []);

  const verifyBackupIntegrity = useCallback(async (backupId: string) => {
    try {
      const isValid = await invoke<boolean>('verify_backup_integrity', { backupId });
      return isValid;
    } catch (err) {
      console.error('Failed to verify backup integrity:', err);
      return false;
    }
  }, []);

  const getSessionBackups = useCallback(async (sessionId: string, limit?: number) => {
    try {
      const sessionBackups = await invoke<BackupListItem[]>('get_session_backups', { 
        sessionId, 
        limit 
      });
      return sessionBackups;
    } catch (err) {
      console.error('Failed to get session backups:', err);
      return [];
    }
  }, []);

  const cleanupOldBackups = useCallback(async () => {
    try {
      const cleanedCount = await invoke<number>('cleanup_old_backups');
      
      // Refresh data
      await loadBackups();
      await loadStatistics();
      
      return cleanedCount;
    } catch (err) {
      console.error('Failed to cleanup old backups:', err);
      return 0;
    }
  }, [loadBackups, loadStatistics]);

  // Load initial data
  useEffect(() => {
    loadBackups();
    loadStatistics();
    loadConfig();
  }, [loadBackups, loadStatistics, loadConfig]);

  // Utility functions
  const formatBackupSize = useCallback((bytes: number) => {
    const units = ['B', 'KB', 'MB', 'GB'];
    let size = bytes;
    let unitIndex = 0;
    
    while (size >= 1024 && unitIndex < units.length - 1) {
      size /= 1024;
      unitIndex++;
    }
    
    return `${size.toFixed(1)} ${units[unitIndex]}`;
  }, []);

  const getBackupTypeIcon = useCallback((backupType: BackupType) => {
    if ('Automatic' in backupType) return '🔄';
    if ('Manual' in backupType) return '💾';
    if ('OnSessionClose' in backupType) return '📤';
    if ('OnContentGeneration' in backupType) return '✨';
    if ('BeforeImport' in backupType) return '📥';
    return '📋';
  }, []);

  const getBackupTypeName = useCallback((backupType: BackupType) => {
    if ('Automatic' in backupType) return 'Automatic';
    if ('Manual' in backupType) return 'Manual';
    if ('OnSessionClose' in backupType) return 'Session Close';
    if ('OnContentGeneration' in backupType) return 'Content Generation';
    if ('BeforeImport' in backupType) return 'Before Import';
    return 'Unknown';
  }, []);

  const getIntervalDisplayName = useCallback((interval: BackupInterval) => {
    if ('Never' in interval) return 'Never';
    if ('EverySession' in interval) return 'Every Session';
    if ('Every5Minutes' in interval) return 'Every 5 Minutes';
    if ('Every15Minutes' in interval) return 'Every 15 Minutes';
    if ('Every30Minutes' in interval) return 'Every 30 Minutes';
    if ('Hourly' in interval) return 'Hourly';
    if ('Daily' in interval) return 'Daily';
    return 'Unknown';
  }, []);

  const formatRelativeTime = useCallback((dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / (1000 * 60));
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString();
  }, []);

  return {
    // State
    backups,
    statistics,
    config,
    isLoading,
    error,
    
    // Actions
    loadBackups,
    loadStatistics,
    loadConfig,
    createManualBackup,
    restoreFromBackup,
    deleteBackup,
    updateConfig,
    verifyBackupIntegrity,
    getSessionBackups,
    cleanupOldBackups,
    
    // Utility functions
    formatBackupSize,
    getBackupTypeIcon,
    getBackupTypeName,
    getIntervalDisplayName,
    formatRelativeTime,
    
    // Reset functions
    clearError: () => setError(null),
  };
}