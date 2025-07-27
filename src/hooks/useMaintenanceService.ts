import { useState, useCallback } from 'react';
import { invoke } from '@tauri-apps/api/core';

export interface MaintenanceConfig {
  enabled: boolean;
  auto_maintenance_enabled: boolean;
  cleanup_policies: CleanupPolicy;
  retention_policies: RetentionPolicy;
  database_config: DatabaseMaintenanceConfig;
  storage_config: StorageMaintenanceConfig;
  schedule_configs: Record<string, ScheduleConfig>;
  safety_settings: SafetySettings;
}

export interface CleanupPolicy {
  auto_cleanup_orphans: boolean;
  backup_before_cleanup: boolean;
  max_items_per_batch: number;
  deduplication_enabled: boolean;
  compress_old_content: boolean;
  cleanup_empty_sessions: boolean;
  cleanup_failed_exports: boolean;
  cleanup_unused_templates: boolean;
}

export interface RetentionPolicy {
  llm_usage_retention_days: number;
  validation_results_retention_days: number;
  export_history_retention_days: number;
  backup_retention_days: number;
  session_inactivity_archive_days: number;
  keep_aggregated_statistics: boolean;
  max_content_versions_per_item: number;
}

export interface DatabaseMaintenanceConfig {
  auto_vacuum_enabled: boolean;
  vacuum_threshold_mb: number;
  integrity_check_frequency_days: number;
  optimize_frequency_days: number;
  reindex_frequency_days: number;
  connection_pool_size: number;
  query_timeout_seconds: number;
  enable_wal_mode: boolean;
  checkpoint_interval_minutes: number;
}

export interface StorageMaintenanceConfig {
  auto_archive_old_exports: boolean;
  export_archive_threshold_days: number;
  compress_archived_exports: boolean;
  max_storage_size_gb: number;
  storage_cleanup_threshold_percent: number;
  file_integrity_check_enabled: boolean;
  duplicate_file_detection_enabled: boolean;
  temp_file_cleanup_hours: number;
}

export interface SafetySettings {
  require_confirmation_for_destructive_ops: boolean;
  create_backup_before_major_cleanup: boolean;
  max_items_to_delete_per_operation: number;
  dry_run_mode_default: boolean;
  preserve_recent_data_days: number;
  emergency_stop_on_error_count: number;
}

export interface ScheduleConfig {
  enabled: boolean;
  interval_hours: number;
  operation: MaintenanceOperation;
  max_duration_minutes: number;
  skip_if_active_sessions: boolean;
}

export type MaintenanceOperation = 
  | 'DatabaseVacuum'
  | 'IntegrityCheck'
  | 'OrphanedDataCleanup'
  | 'RetentionPolicyCleanup'
  | 'StorageOptimization'
  | 'IndexMaintenance'
  | 'ContentDeduplication'
  | 'FileSystemAudit';

export type IssueSeverity = 'Low' | 'Medium' | 'High' | 'Critical';

export interface MaintenanceIssue {
  id: string;
  severity: IssueSeverity;
  operation: MaintenanceOperation;
  title: string;
  description: string;
  affected_items: number;
  estimated_space_savings_mb?: number;
  estimated_performance_impact?: string;
  can_auto_fix: boolean;
  requires_backup: boolean;
}

export interface MaintenanceResult {
  operation: MaintenanceOperation;
  success: boolean;
  items_processed: number;
  items_cleaned: number;
  space_reclaimed_mb: number;
  duration_ms: number;
  errors: string[];
  warnings: string[];
  details: Record<string, any>;
}

export interface MaintenanceProgress {
  operation: MaintenanceOperation;
  current_step: string;
  progress_percentage: number;
  items_processed: number;
  total_items: number;
  estimated_time_remaining_ms?: number;
  current_item: string;
}

export interface MaintenanceOperationInfo {
  operation: MaintenanceOperation;
  display_name: string;
  description: string;
  estimated_duration_minutes: number;
  requires_backup: boolean;
  destructive: boolean;
  can_run_while_active: boolean;
}

export interface MaintenanceRecommendation {
  operation: MaintenanceOperation;
  priority: 'Critical' | 'High' | 'Medium' | 'Low';
  reason: string;
  estimated_time_minutes: number;
  estimated_space_savings_mb: number;
  can_auto_execute: boolean;
  affected_items: number;
}

export interface SystemHealthSummary {
  overall_health_score: number; // 0-100
  critical_issues: number;
  high_priority_issues: number;
  medium_priority_issues: number;
  low_priority_issues: number;
  total_issues: number;
  estimated_space_reclaimable_mb: number;
  last_maintenance_date?: string;
  next_recommended_maintenance: string;
}

export interface MaintenanceImpactEstimate {
  total_operations: number;
  estimated_duration_minutes: number;
  estimated_space_savings_mb: number;
  requires_backup: boolean;
  can_run_while_active: boolean;
  affected_sessions: number;
  affected_content_items: number;
}

export function useMaintenanceService() {
  const [config, setConfig] = useState<MaintenanceConfig | null>(null);
  const [issues, setIssues] = useState<MaintenanceIssue[]>([]);
  const [availableOperations, setAvailableOperations] = useState<MaintenanceOperationInfo[]>([]);
  const [recommendations, setRecommendations] = useState<MaintenanceRecommendation[]>([]);
  const [systemHealth, setSystemHealth] = useState<SystemHealthSummary | null>(null);
  const [maintenanceProgress, setMaintenanceProgress] = useState<MaintenanceProgress | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isPerformingMaintenance, setIsPerformingMaintenance] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadConfig = useCallback(async () => {
    try {
      const result = await invoke<MaintenanceConfig>('get_maintenance_config');
      setConfig(result);
      setError(null);
    } catch (err) {
      setError(err as string);
    }
  }, []);

  const updateConfig = useCallback(async (newConfig: MaintenanceConfig) => {
    try {
      await invoke('update_maintenance_config', { config: newConfig });
      setConfig(newConfig);
      setError(null);
    } catch (err) {
      setError(err as string);
    }
  }, []);

  const analyzeMaintenanceIssues = useCallback(async () => {
    setIsAnalyzing(true);
    try {
      const result = await invoke<MaintenanceIssue[]>('analyze_maintenance_issues');
      setIssues(result);
      setError(null);
    } catch (err) {
      setError(err as string);
    } finally {
      setIsAnalyzing(false);
    }
  }, []);

  const loadMaintenanceIssues = useCallback(async () => {
    await analyzeMaintenanceIssues();
  }, [analyzeMaintenanceIssues]);

  const loadAvailableOperations = useCallback(async () => {
    try {
      const result = await invoke<MaintenanceOperationInfo[]>('get_available_maintenance_operations');
      setAvailableOperations(result);
      setError(null);
    } catch (err) {
      setError(err as string);
    }
  }, []);

  const loadRecommendations = useCallback(async () => {
    try {
      const result = await invoke<MaintenanceRecommendation[]>('get_maintenance_recommendations');
      setRecommendations(result);
      setError(null);
    } catch (err) {
      setError(err as string);
    }
  }, []);

  const loadSystemHealth = useCallback(async () => {
    try {
      const result = await invoke<SystemHealthSummary>('get_system_health_summary');
      setSystemHealth(result);
      setError(null);
    } catch (err) {
      setError(err as string);
    }
  }, []);

  const performMaintenance = useCallback(async (
    operations: MaintenanceOperation[],
    dryRun: boolean = false,
    withProgress: boolean = false
  ): Promise<MaintenanceResult[] | null> => {
    setIsPerformingMaintenance(true);
    setMaintenanceProgress(null);
    setError(null);

    try {
      let result: MaintenanceResult[];
      
      if (withProgress) {
        // Set up progress listener
        const unlisten = await window.__TAURI__.event.listen('maintenance-progress', (event) => {
          setMaintenanceProgress(event.payload as MaintenanceProgress);
        });

        try {
          result = await invoke<MaintenanceResult[]>('perform_maintenance_with_progress', {
            operations,
            dryRun
          });
        } finally {
          unlisten();
        }
      } else {
        result = await invoke<MaintenanceResult[]>('perform_maintenance', {
          operations,
          dryRun
        });
      }

      setMaintenanceProgress(null);
      return result;
    } catch (err) {
      setError(err as string);
      return null;
    } finally {
      setIsPerformingMaintenance(false);
    }
  }, []);

  const estimateMaintenanceImpact = useCallback(async (
    operations: MaintenanceOperation[]
  ): Promise<MaintenanceImpactEstimate | null> => {
    try {
      const result = await invoke<MaintenanceImpactEstimate>('estimate_maintenance_impact', {
        operations
      });
      setError(null);
      return result;
    } catch (err) {
      setError(err as string);
      return null;
    }
  }, []);

  const getOperationDisplayName = useCallback((operation: MaintenanceOperation): string => {
    const operationInfo = availableOperations.find(op => op.operation === operation);
    return operationInfo?.display_name || operation;
  }, [availableOperations]);

  const getOperationIcon = useCallback((operation: MaintenanceOperation): string => {
    switch (operation) {
      case 'DatabaseVacuum': return '🗜️';
      case 'IntegrityCheck': return '🔍';
      case 'OrphanedDataCleanup': return '🧹';
      case 'RetentionPolicyCleanup': return '📅';
      case 'StorageOptimization': return '💾';
      case 'IndexMaintenance': return '⚡';
      case 'ContentDeduplication': return '🔄';
      case 'FileSystemAudit': return '📋';
      default: return '⚙️';
    }
  }, []);

  const formatFileSize = useCallback((bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }, []);

  const formatDuration = useCallback((minutes: number): string => {
    if (minutes < 60) {
      return `${minutes} minute${minutes !== 1 ? 's' : ''}`;
    }
    
    const hours = Math.floor(minutes / 60);
    const remainingMinutes = minutes % 60;
    
    if (remainingMinutes === 0) {
      return `${hours} hour${hours !== 1 ? 's' : ''}`;
    }
    
    return `${hours}h ${remainingMinutes}m`;
  }, []);

  return {
    // State
    config,
    issues,
    availableOperations,
    recommendations,
    systemHealth,
    maintenanceProgress,
    isAnalyzing,
    isPerformingMaintenance,
    error,

    // Actions
    loadConfig,
    updateConfig,
    loadMaintenanceIssues,
    analyzeMaintenanceIssues,
    loadAvailableOperations,
    loadRecommendations,
    loadSystemHealth,
    performMaintenance,
    estimateMaintenanceImpact,

    // Utilities
    getOperationDisplayName,
    getOperationIcon,
    formatFileSize,
    formatDuration,
  };
}