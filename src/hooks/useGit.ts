import { useState, useCallback } from 'react';
import { invoke } from '@tauri-apps/api/core';

export interface GitConfig {
  enabled: boolean;
  auto_commit: boolean;
  auto_commit_on_session_save: boolean;
  auto_commit_on_content_generation: boolean;
  commit_message_template: string;
  ignored_patterns: string[];
  repository_path?: string;
}

export interface GitStatus {
  is_repository: boolean;
  is_initialized: boolean;
  current_branch?: string;
  has_remote: boolean;
  remote_url?: string;
  modified_files: string[];
  staged_files: string[];
  untracked_files: string[];
  commits_ahead: number;
  commits_behind: number;
  last_commit?: GitCommit;
}

export interface GitCommit {
  hash: string;
  short_hash: string;
  message: string;
  author: string;
  email: string;
  timestamp: string;
  files_changed: string[];
}

export interface GitHistory {
  commits: GitCommit[];
  total_count: number;
  page: number;
  per_page: number;
}

export interface GitDiff {
  file_path: string;
  old_content?: string;
  new_content?: string;
  hunks: DiffHunk[];
  is_binary: boolean;
  is_new_file: boolean;
  is_deleted_file: boolean;
}

export interface DiffHunk {
  old_start: number;
  old_lines: number;
  new_start: number;
  new_lines: number;
  lines: DiffLine[];
}

export interface DiffLine {
  line_type: DiffLineType;
  content: string;
  old_line_number?: number;
  new_line_number?: number;
}

export enum DiffLineType {
  Context = 'Context',
  Added = 'Added',
  Removed = 'Removed',
  Header = 'Header',
}

export interface GitInitOptions {
  repository_path: string;
  initial_commit: boolean;
  setup_gitignore: boolean;
  setup_remote?: string;
}

export interface CommitOptions {
  message: string;
  author_name?: string;
  author_email?: string;
  add_all: boolean;
  specific_files: string[];
}

export interface GitInstallationInfo {
  is_installed: boolean;
  version?: string;
  path?: string;
  error?: string;
}

export interface GitUserConfig {
  name?: string;
  email?: string;
}

export interface RepositoryValidation {
  is_valid: boolean;
  is_git_repository: boolean;
  can_initialize: boolean;
  error_message?: string;
}

export function useGit() {
  const [config, setConfig] = useState<GitConfig | null>(null);
  const [status, setStatus] = useState<GitStatus | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [installationInfo, setInstallationInfo] = useState<GitInstallationInfo | null>(null);

  const loadConfig = useCallback(async () => {
    try {
      setIsLoading(true);
      const result = await invoke<GitConfig>('get_git_config');
      setConfig(result);
      setError(null);
    } catch (err) {
      setError(err as string);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const updateConfig = useCallback(async (newConfig: GitConfig) => {
    try {
      setIsLoading(true);
      await invoke('update_git_config', { config: newConfig });
      setConfig(newConfig);
      setError(null);
    } catch (err) {
      setError(err as string);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const checkInstallation = useCallback(async () => {
    try {
      setIsLoading(true);
      const result = await invoke<GitInstallationInfo>('check_git_installation');
      setInstallationInfo(result);
      setError(null);
      return result;
    } catch (err) {
      setError(err as string);
      return null;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const detectRepository = useCallback(async () => {
    try {
      setIsLoading(true);
      const result = await invoke<GitStatus>('detect_git_repository');
      setStatus(result);
      setError(null);
      return result;
    } catch (err) {
      setError(err as string);
      return null;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const initializeRepository = useCallback(async (options: GitInitOptions) => {
    try {
      setIsLoading(true);
      await invoke('initialize_git_repository', { options });
      
      // Refresh status after initialization
      const newStatus = await invoke<GitStatus>('detect_git_repository');
      setStatus(newStatus);
      setError(null);
      return true;
    } catch (err) {
      setError(err as string);
      return false;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const getStatus = useCallback(async () => {
    try {
      setIsLoading(true);
      const result = await invoke<GitStatus>('get_git_status');
      setStatus(result);
      setError(null);
      return result;
    } catch (err) {
      setError(err as string);
      return null;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const commitChanges = useCallback(async (options: CommitOptions) => {
    try {
      setIsLoading(true);
      const commitHash = await invoke<string>('commit_git_changes', { options });
      
      // Refresh status after commit
      await getStatus();
      setError(null);
      return commitHash;
    } catch (err) {
      setError(err as string);
      return null;
    } finally {
      setIsLoading(false);
    }
  }, [getStatus]);

  const getHistory = useCallback(async (page: number = 0, perPage: number = 20) => {
    try {
      setIsLoading(true);
      const result = await invoke<GitHistory>('get_git_history', {
        page,
        perPage
      });
      setError(null);
      return result;
    } catch (err) {
      setError(err as string);
      return null;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const getDiff = useCallback(async (commitHash?: string, filePath?: string) => {
    try {
      setIsLoading(true);
      const result = await invoke<GitDiff[]>('get_git_diff', {
        commitHash,
        filePath
      });
      setError(null);
      return result;
    } catch (err) {
      setError(err as string);
      return null;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const autoCommitSession = useCallback(async (sessionName: string) => {
    try {
      const commitHash = await invoke<string | null>('auto_commit_session', {
        sessionName
      });
      
      if (commitHash) {
        // Refresh status after auto-commit
        await getStatus();
      }
      
      return commitHash;
    } catch (err) {
      console.warn('Auto-commit failed:', err);
      return null;
    }
  }, [getStatus]);

  const autoCommitContentGeneration = useCallback(async (contentTypes: string[]) => {
    try {
      const commitHash = await invoke<string | null>('auto_commit_content_generation', {
        contentTypes
      });
      
      if (commitHash) {
        // Refresh status after auto-commit
        await getStatus();
      }
      
      return commitHash;
    } catch (err) {
      console.warn('Auto-commit failed:', err);
      return null;
    }
  }, [getStatus]);

  const getUserConfig = useCallback(async () => {
    try {
      const result = await invoke<GitUserConfig>('get_git_user_config');
      return result;
    } catch (err) {
      setError(err as string);
      return null;
    }
  }, []);

  const setUserConfig = useCallback(async (name?: string, email?: string) => {
    try {
      await invoke('set_git_user_config', { name, email });
      setError(null);
      return true;
    } catch (err) {
      setError(err as string);
      return false;
    }
  }, []);

  const validateRepositoryPath = useCallback(async (path: string) => {
    try {
      const result = await invoke<RepositoryValidation>('validate_repository_path', {
        path
      });
      return result;
    } catch (err) {
      setError(err as string);
      return {
        is_valid: false,
        is_git_repository: false,
        can_initialize: false,
        error_message: err as string,
      };
    }
  }, []);

  const formatCommitMessage = useCallback((commit: GitCommit, maxLength?: number) => {
    if (maxLength && commit.message.length > maxLength) {
      return commit.message.substring(0, maxLength - 3) + '...';
    }
    return commit.message;
  }, []);

  const getRelativeTime = useCallback((timestamp: string) => {
    const now = new Date();
    const commitTime = new Date(timestamp);
    const diffMs = now.getTime() - commitTime.getTime();
    
    const seconds = Math.floor(diffMs / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);
    
    if (days > 0) {
      return `${days} day${days === 1 ? '' : 's'} ago`;
    } else if (hours > 0) {
      return `${hours} hour${hours === 1 ? '' : 's'} ago`;
    } else if (minutes > 0) {
      return `${minutes} minute${minutes === 1 ? '' : 's'} ago`;
    } else {
      return 'Just now';
    }
  }, []);

  const getDiffLineColor = useCallback((lineType: DiffLineType) => {
    switch (lineType) {
      case DiffLineType.Added:
        return '#059669';
      case DiffLineType.Removed:
        return '#dc2626';
      case DiffLineType.Header:
        return '#3b82f6';
      default:
        return '#374151';
    }
  }, []);

  const getDiffLineSymbol = useCallback((lineType: DiffLineType) => {
    switch (lineType) {
      case DiffLineType.Added:
        return '+';
      case DiffLineType.Removed:
        return '-';
      case DiffLineType.Header:
        return '@';
      default:
        return ' ';
    }
  }, []);

  return {
    // State
    config,
    status,
    isLoading,
    error,
    installationInfo,

    // Actions
    loadConfig,
    updateConfig,
    checkInstallation,
    detectRepository,
    initializeRepository,
    getStatus,
    commitChanges,
    getHistory,
    getDiff,
    autoCommitSession,
    autoCommitContentGeneration,
    getUserConfig,
    setUserConfig,
    validateRepositoryPath,

    // Utilities
    formatCommitMessage,
    getRelativeTime,
    getDiffLineColor,
    getDiffLineSymbol,
  };
}