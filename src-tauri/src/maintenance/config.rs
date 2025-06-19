use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use crate::maintenance::{MaintenanceOperation, ScheduleConfig};

/// Comprehensive maintenance configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MaintenanceConfig {
    pub enabled: bool,
    pub auto_maintenance_enabled: bool,
    pub cleanup_policies: CleanupPolicy,
    pub retention_policies: RetentionPolicy,
    pub database_config: DatabaseMaintenanceConfig,
    pub storage_config: StorageMaintenanceConfig,
    pub schedule_configs: HashMap<String, ScheduleConfig>,
    pub safety_settings: SafetySettings,
}

impl Default for MaintenanceConfig {
    fn default() -> Self {
        let mut schedule_configs = HashMap::new();
        
        // Daily database vacuum
        schedule_configs.insert("daily_vacuum".to_string(), ScheduleConfig {
            enabled: true,
            interval_hours: 24,
            operation: MaintenanceOperation::DatabaseVacuum,
            max_duration_minutes: 10,
            skip_if_active_sessions: true,
        });
        
        // Weekly orphan cleanup
        schedule_configs.insert("weekly_orphan_cleanup".to_string(), ScheduleConfig {
            enabled: true,
            interval_hours: 168, // 7 days
            operation: MaintenanceOperation::OrphanedDataCleanup,
            max_duration_minutes: 30,
            skip_if_active_sessions: true,
        });
        
        // Monthly storage optimization
        schedule_configs.insert("monthly_storage_optimization".to_string(), ScheduleConfig {
            enabled: true,
            interval_hours: 720, // 30 days
            operation: MaintenanceOperation::StorageOptimization,
            max_duration_minutes: 60,
            skip_if_active_sessions: true,
        });

        Self {
            enabled: true,
            auto_maintenance_enabled: true,
            cleanup_policies: CleanupPolicy::default(),
            retention_policies: RetentionPolicy::default(),
            database_config: DatabaseMaintenanceConfig::default(),
            storage_config: StorageMaintenanceConfig::default(),
            schedule_configs,
            safety_settings: SafetySettings::default(),
        }
    }
}

/// Cleanup policies for different data types
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CleanupPolicy {
    pub auto_cleanup_orphans: bool,
    pub backup_before_cleanup: bool,
    pub max_items_per_batch: u32,
    pub deduplication_enabled: bool,
    pub compress_old_content: bool,
    pub cleanup_empty_sessions: bool,
    pub cleanup_failed_exports: bool,
    pub cleanup_unused_templates: bool,
}

impl Default for CleanupPolicy {
    fn default() -> Self {
        Self {
            auto_cleanup_orphans: true,
            backup_before_cleanup: true,
            max_items_per_batch: 1000,
            deduplication_enabled: true,
            compress_old_content: true,
            cleanup_empty_sessions: false, // Conservative default
            cleanup_failed_exports: true,
            cleanup_unused_templates: false, // Conservative default
        }
    }
}

/// Data retention policies
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RetentionPolicy {
    pub llm_usage_retention_days: u32,
    pub validation_results_retention_days: u32,
    pub export_history_retention_days: u32,
    pub backup_retention_days: u32,
    pub session_inactivity_archive_days: u32,
    pub keep_aggregated_statistics: bool,
    pub max_content_versions_per_item: u32,
}

impl Default for RetentionPolicy {
    fn default() -> Self {
        Self {
            llm_usage_retention_days: 90,
            validation_results_retention_days: 30,
            export_history_retention_days: 180,
            backup_retention_days: 30,
            session_inactivity_archive_days: 365,
            keep_aggregated_statistics: true,
            max_content_versions_per_item: 10,
        }
    }
}

/// Database-specific maintenance configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DatabaseMaintenanceConfig {
    pub auto_vacuum_enabled: bool,
    pub vacuum_threshold_mb: f64,
    pub integrity_check_frequency_days: u32,
    pub optimize_frequency_days: u32,
    pub reindex_frequency_days: u32,
    pub connection_pool_size: u32,
    pub query_timeout_seconds: u32,
    pub enable_wal_mode: bool,
    pub checkpoint_interval_minutes: u32,
}

impl Default for DatabaseMaintenanceConfig {
    fn default() -> Self {
        Self {
            auto_vacuum_enabled: true,
            vacuum_threshold_mb: 50.0,
            integrity_check_frequency_days: 7,
            optimize_frequency_days: 1,
            reindex_frequency_days: 30,
            connection_pool_size: 5,
            query_timeout_seconds: 30,
            enable_wal_mode: true,
            checkpoint_interval_minutes: 60,
        }
    }
}

/// Storage-specific maintenance configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StorageMaintenanceConfig {
    pub auto_archive_old_exports: bool,
    pub export_archive_threshold_days: u32,
    pub compress_archived_exports: bool,
    pub max_storage_size_gb: f64,
    pub storage_cleanup_threshold_percent: f32,
    pub file_integrity_check_enabled: bool,
    pub duplicate_file_detection_enabled: bool,
    pub temp_file_cleanup_hours: u32,
}

impl Default for StorageMaintenanceConfig {
    fn default() -> Self {
        Self {
            auto_archive_old_exports: true,
            export_archive_threshold_days: 90,
            compress_archived_exports: true,
            max_storage_size_gb: 10.0,
            storage_cleanup_threshold_percent: 80.0,
            file_integrity_check_enabled: true,
            duplicate_file_detection_enabled: true,
            temp_file_cleanup_hours: 24,
        }
    }
}

/// Safety settings to prevent data loss
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SafetySettings {
    pub require_confirmation_for_destructive_ops: bool,
    pub create_backup_before_major_cleanup: bool,
    pub max_items_to_delete_per_operation: u32,
    pub dry_run_mode_default: bool,
    pub preserve_recent_data_days: u32,
    pub emergency_stop_on_error_count: u32,
}

impl Default for SafetySettings {
    fn default() -> Self {
        Self {
            require_confirmation_for_destructive_ops: true,
            create_backup_before_major_cleanup: true,
            max_items_to_delete_per_operation: 5000,
            dry_run_mode_default: false,
            preserve_recent_data_days: 7, // Never auto-delete data less than 7 days old
            emergency_stop_on_error_count: 10,
        }
    }
}