// Session data cleanup and maintenance tools
// Provides comprehensive maintenance functionality including:
// - Orphaned data detection and cleanup
// - Database optimization and maintenance
// - Storage cleanup and optimization
// - Automated maintenance scheduling

pub mod service;
pub mod commands;
pub mod config;
pub mod scheduler;
pub mod reports;

pub use service::MaintenanceService;
pub use config::{MaintenanceConfig, CleanupPolicy, RetentionPolicy};
pub use reports::{MaintenanceReport, CleanupSummary, StorageAnalysis};

use serde::{Deserialize, Serialize};
use std::collections::HashMap;

/// Types of maintenance operations available
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum MaintenanceOperation {
    DatabaseVacuum,
    IntegrityCheck,
    OrphanedDataCleanup,
    RetentionPolicyCleanup,
    StorageOptimization,
    IndexMaintenance,
    ContentDeduplication,
    FileSystemAudit,
}

/// Severity levels for maintenance issues
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum IssueSeverity {
    Low,
    Medium,
    High,
    Critical,
}

/// Maintenance issue detected during analysis
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MaintenanceIssue {
    pub id: String,
    pub severity: IssueSeverity,
    pub operation: MaintenanceOperation,
    pub title: String,
    pub description: String,
    pub affected_items: u32,
    pub estimated_space_savings_mb: Option<f64>,
    pub estimated_performance_impact: Option<String>,
    pub can_auto_fix: bool,
    pub requires_backup: bool,
}

/// Result of a maintenance operation
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MaintenanceResult {
    pub operation: MaintenanceOperation,
    pub success: bool,
    pub items_processed: u32,
    pub items_cleaned: u32,
    pub space_reclaimed_mb: f64,
    pub duration_ms: u64,
    pub errors: Vec<String>,
    pub warnings: Vec<String>,
    pub details: HashMap<String, serde_json::Value>,
}

/// Progress tracking for maintenance operations
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MaintenanceProgress {
    pub operation: MaintenanceOperation,
    pub current_step: String,
    pub progress_percentage: f32,
    pub items_processed: u32,
    pub total_items: u32,
    pub estimated_time_remaining_ms: Option<u64>,
    pub current_item: String,
}

/// Configuration for maintenance operation scheduling
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ScheduleConfig {
    pub enabled: bool,
    pub interval_hours: u32,
    pub operation: MaintenanceOperation,
    pub max_duration_minutes: u32,
    pub skip_if_active_sessions: bool,
}