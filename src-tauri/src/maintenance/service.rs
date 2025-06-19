use std::collections::{HashMap, HashSet};
use std::path::PathBuf;
use std::sync::Arc;
use anyhow::{Result, anyhow};
use chrono::{DateTime, Utc, Duration};
use serde_json;
use sqlx::{Pool, Sqlite, Row};
use tokio::fs;
use tokio::sync::Mutex;

use crate::maintenance::{
    MaintenanceConfig, MaintenanceOperation, MaintenanceResult, MaintenanceIssue, 
    MaintenanceProgress, IssueSeverity, CleanupPolicy, RetentionPolicy
};
use crate::session::SessionManager;
use crate::backup::service::BackupService;

/// Service for managing session data cleanup and maintenance
pub struct MaintenanceService {
    db: Pool<Sqlite>,
    config: Arc<Mutex<MaintenanceConfig>>,
    session_manager: Arc<Mutex<SessionManager>>,
    backup_service: Option<Arc<BackupService>>,
    progress_callback: Option<Arc<dyn Fn(MaintenanceProgress) + Send + Sync>>,
}

impl MaintenanceService {
    /// Create new maintenance service
    pub fn new(
        db: Pool<Sqlite>,
        session_manager: Arc<Mutex<SessionManager>>,
        backup_service: Option<Arc<BackupService>>,
    ) -> Self {
        Self {
            db,
            config: Arc::new(Mutex::new(MaintenanceConfig::default())),
            session_manager,
            backup_service,
            progress_callback: None,
        }
    }

    /// Set progress callback for maintenance operations
    pub fn set_progress_callback<F>(&mut self, callback: F)
    where
        F: Fn(MaintenanceProgress) + Send + Sync + 'static,
    {
        self.progress_callback = Some(Arc::new(callback));
    }

    /// Get current maintenance configuration
    pub async fn get_config(&self) -> MaintenanceConfig {
        self.config.lock().await.clone()
    }

    /// Update maintenance configuration
    pub async fn update_config(&self, new_config: MaintenanceConfig) -> Result<()> {
        let mut config = self.config.lock().await;
        *config = new_config;
        Ok(())
    }

    /// Analyze system and detect maintenance issues
    pub async fn analyze_maintenance_issues(&self) -> Result<Vec<MaintenanceIssue>> {
        let mut issues = Vec::new();

        // Check for orphaned data
        issues.extend(self.detect_orphaned_data().await?);
        
        // Check database health
        issues.extend(self.analyze_database_health().await?);
        
        // Check storage usage
        issues.extend(self.analyze_storage_usage().await?);
        
        // Check retention policy violations
        issues.extend(self.check_retention_policy_violations().await?);

        Ok(issues)
    }

    /// Perform comprehensive maintenance operation
    pub async fn perform_maintenance(
        &self, 
        operations: Vec<MaintenanceOperation>,
        dry_run: bool
    ) -> Result<Vec<MaintenanceResult>> {
        let mut results = Vec::new();
        let config = self.get_config().await;

        for operation in operations {
            let start_time = std::time::Instant::now();
            
            self.emit_progress(MaintenanceProgress {
                operation: operation.clone(),
                current_step: "Starting".to_string(),
                progress_percentage: 0.0,
                items_processed: 0,
                total_items: 0,
                estimated_time_remaining_ms: None,
                current_item: "Initializing operation".to_string(),
            }).await;

            let result = match operation {
                MaintenanceOperation::DatabaseVacuum => {
                    self.perform_database_vacuum(dry_run).await
                }
                MaintenanceOperation::IntegrityCheck => {
                    self.perform_integrity_check().await
                }
                MaintenanceOperation::OrphanedDataCleanup => {
                    self.cleanup_orphaned_data(&config.cleanup_policies, dry_run).await
                }
                MaintenanceOperation::RetentionPolicyCleanup => {
                    self.apply_retention_policies(&config.retention_policies, dry_run).await
                }
                MaintenanceOperation::StorageOptimization => {
                    self.optimize_storage(&config.storage_config, dry_run).await
                }
                MaintenanceOperation::IndexMaintenance => {
                    self.maintain_database_indexes(dry_run).await
                }
                MaintenanceOperation::ContentDeduplication => {
                    self.deduplicate_content(dry_run).await
                }
                MaintenanceOperation::FileSystemAudit => {
                    self.audit_file_system().await
                }
            };

            let duration = start_time.elapsed();
            
            match result {
                Ok(mut maintenance_result) => {
                    maintenance_result.duration_ms = duration.as_millis() as u64;
                    results.push(maintenance_result);
                }
                Err(e) => {
                    results.push(MaintenanceResult {
                        operation,
                        success: false,
                        items_processed: 0,
                        items_cleaned: 0,
                        space_reclaimed_mb: 0.0,
                        duration_ms: duration.as_millis() as u64,
                        errors: vec![e.to_string()],
                        warnings: vec![],
                        details: HashMap::new(),
                    });
                }
            }
        }

        Ok(results)
    }

    /// Detect orphaned data across the system
    async fn detect_orphaned_data(&self) -> Result<Vec<MaintenanceIssue>> {
        let mut issues = Vec::new();

        // Check for orphaned validation results
        let orphaned_validations = sqlx::query(
            "SELECT COUNT(*) as count FROM validation_results vr 
             LEFT JOIN generated_content gc ON vr.content_id = gc.id 
             WHERE gc.id IS NULL"
        )
        .fetch_one(&self.db)
        .await?
        .get::<i64, _>("count") as u32;

        if orphaned_validations > 0 {
            issues.push(MaintenanceIssue {
                id: "orphaned_validation_results".to_string(),
                severity: IssueSeverity::Medium,
                operation: MaintenanceOperation::OrphanedDataCleanup,
                title: "Orphaned Validation Results".to_string(),
                description: format!("{} validation results reference deleted content", orphaned_validations),
                affected_items: orphaned_validations,
                estimated_space_savings_mb: Some((orphaned_validations as f64) * 0.01), // Rough estimate
                estimated_performance_impact: Some("Improved query performance".to_string()),
                can_auto_fix: true,
                requires_backup: false,
            });
        }

        // Check for orphaned LLM usage records
        let orphaned_llm_usage = sqlx::query(
            "SELECT COUNT(*) as count FROM llm_usage lu 
             LEFT JOIN sessions s ON lu.session_id = s.id 
             WHERE s.id IS NULL"
        )
        .fetch_one(&self.db)
        .await?
        .get::<i64, _>("count") as u32;

        if orphaned_llm_usage > 0 {
            issues.push(MaintenanceIssue {
                id: "orphaned_llm_usage".to_string(),
                severity: IssueSeverity::Low,
                operation: MaintenanceOperation::OrphanedDataCleanup,
                title: "Orphaned LLM Usage Records".to_string(),
                description: format!("{} LLM usage records reference deleted sessions", orphaned_llm_usage),
                affected_items: orphaned_llm_usage,
                estimated_space_savings_mb: Some((orphaned_llm_usage as f64) * 0.002), // Smaller records
                estimated_performance_impact: Some("Improved reporting queries".to_string()),
                can_auto_fix: true,
                requires_backup: false,
            });
        }

        // Check for orphaned export history
        let orphaned_exports = sqlx::query(
            "SELECT COUNT(*) as count FROM export_history eh 
             WHERE eh.file_path IS NOT NULL AND NOT EXISTS(
                 SELECT 1 FROM sessions s WHERE s.id = eh.session_id
             )"
        )
        .fetch_one(&self.db)
        .await?
        .get::<i64, _>("count") as u32;

        if orphaned_exports > 0 {
            issues.push(MaintenanceIssue {
                id: "orphaned_export_history".to_string(),
                severity: IssueSeverity::Low,
                operation: MaintenanceOperation::OrphanedDataCleanup,
                title: "Orphaned Export History".to_string(),
                description: format!("{} export records reference deleted sessions", orphaned_exports),
                affected_items: orphaned_exports,
                estimated_space_savings_mb: Some((orphaned_exports as f64) * 0.001),
                estimated_performance_impact: Some("Cleaner export history".to_string()),
                can_auto_fix: true,
                requires_backup: false,
            });
        }

        Ok(issues)
    }

    /// Analyze database health and performance
    async fn analyze_database_health(&self) -> Result<Vec<MaintenanceIssue>> {
        let mut issues = Vec::new();

        // Check database size and fragmentation
        let db_stats = sqlx::query(
            "SELECT 
                page_count * page_size / 1024.0 / 1024.0 as size_mb,
                freelist_count * page_size / 1024.0 / 1024.0 as free_mb
             FROM pragma_page_count(), pragma_page_size(), pragma_freelist_count()"
        )
        .fetch_one(&self.db)
        .await?;

        let size_mb = db_stats.get::<f64, _>("size_mb");
        let free_mb = db_stats.get::<f64, _>("free_mb");
        let fragmentation_percent = (free_mb / size_mb) * 100.0;

        if fragmentation_percent > 10.0 {
            issues.push(MaintenanceIssue {
                id: "database_fragmentation".to_string(),
                severity: if fragmentation_percent > 25.0 { IssueSeverity::High } else { IssueSeverity::Medium },
                operation: MaintenanceOperation::DatabaseVacuum,
                title: "Database Fragmentation".to_string(),
                description: format!("Database is {:.1}% fragmented ({:.1} MB can be reclaimed)", fragmentation_percent, free_mb),
                affected_items: 1,
                estimated_space_savings_mb: Some(free_mb),
                estimated_performance_impact: Some("Improved query and write performance".to_string()),
                can_auto_fix: true,
                requires_backup: true,
            });
        }

        // Check for missing or outdated statistics
        let stats_age = sqlx::query("SELECT datetime('now') - datetime(last_analyze) as age_days FROM pragma_stats")
            .fetch_optional(&self.db)
            .await?;

        if let Some(stats) = stats_age {
            let age_days = stats.get::<f64, _>("age_days");
            if age_days > 7.0 {
                issues.push(MaintenanceIssue {
                    id: "outdated_statistics".to_string(),
                    severity: IssueSeverity::Medium,
                    operation: MaintenanceOperation::IndexMaintenance,
                    title: "Outdated Database Statistics".to_string(),
                    description: format!("Database statistics are {:.1} days old", age_days),
                    affected_items: 1,
                    estimated_space_savings_mb: None,
                    estimated_performance_impact: Some("Improved query planning".to_string()),
                    can_auto_fix: true,
                    requires_backup: false,
                });
            }
        }

        Ok(issues)
    }

    /// Analyze storage usage patterns
    async fn analyze_storage_usage(&self) -> Result<Vec<MaintenanceIssue>> {
        let mut issues = Vec::new();
        let config = self.get_config().await;

        // Estimate total storage usage
        let total_size = self.calculate_total_storage_size().await?;
        let max_size_bytes = (config.storage_config.max_storage_size_gb * 1024.0 * 1024.0 * 1024.0) as u64;
        
        let usage_percent = (total_size as f64 / max_size_bytes as f64) * 100.0;

        if usage_percent > config.storage_config.storage_cleanup_threshold_percent as f64 {
            issues.push(MaintenanceIssue {
                id: "storage_usage_high".to_string(),
                severity: if usage_percent > 90.0 { IssueSeverity::Critical } else { IssueSeverity::High },
                operation: MaintenanceOperation::StorageOptimization,
                title: "High Storage Usage".to_string(),
                description: format!("Storage is {:.1}% full ({:.1} GB used)", usage_percent, total_size as f64 / 1024.0 / 1024.0 / 1024.0),
                affected_items: 1,
                estimated_space_savings_mb: Some(self.estimate_reclaimable_storage().await? as f64 / 1024.0 / 1024.0),
                estimated_performance_impact: Some("Improved I/O performance".to_string()),
                can_auto_fix: true,
                requires_backup: false,
            });
        }

        Ok(issues)
    }

    /// Check for retention policy violations
    async fn check_retention_policy_violations(&self) -> Result<Vec<MaintenanceIssue>> {
        let mut issues = Vec::new();
        let config = self.get_config().await;
        let cutoff_date = Utc::now() - Duration::days(config.retention_policies.llm_usage_retention_days as i64);

        // Check old LLM usage data
        let old_llm_usage = sqlx::query(
            "SELECT COUNT(*) as count FROM llm_usage WHERE timestamp < ?"
        )
        .bind(cutoff_date.timestamp())
        .fetch_one(&self.db)
        .await?
        .get::<i64, _>("count") as u32;

        if old_llm_usage > 0 {
            issues.push(MaintenanceIssue {
                id: "retention_policy_llm_usage".to_string(),
                severity: IssueSeverity::Low,
                operation: MaintenanceOperation::RetentionPolicyCleanup,
                title: "Old LLM Usage Data".to_string(),
                description: format!("{} LLM usage records exceed retention policy", old_llm_usage),
                affected_items: old_llm_usage,
                estimated_space_savings_mb: Some((old_llm_usage as f64) * 0.002),
                estimated_performance_impact: Some("Faster reporting queries".to_string()),
                can_auto_fix: true,
                requires_backup: false,
            });
        }

        Ok(issues)
    }

    /// Perform database vacuum operation
    async fn perform_database_vacuum(&self, dry_run: bool) -> Result<MaintenanceResult> {
        let start_size = self.get_database_size().await?;
        
        if !dry_run {
            self.emit_progress(MaintenanceProgress {
                operation: MaintenanceOperation::DatabaseVacuum,
                current_step: "Executing VACUUM".to_string(),
                progress_percentage: 50.0,
                items_processed: 1,
                total_items: 2,
                estimated_time_remaining_ms: None,
                current_item: "Reclaiming unused space".to_string(),
            }).await;

            sqlx::query("VACUUM").execute(&self.db).await?;
            
            self.emit_progress(MaintenanceProgress {
                operation: MaintenanceOperation::DatabaseVacuum,
                current_step: "Optimizing database".to_string(),
                progress_percentage: 75.0,
                items_processed: 2,
                total_items: 2,
                estimated_time_remaining_ms: None,
                current_item: "Updating statistics".to_string(),
            }).await;

            sqlx::query("PRAGMA optimize").execute(&self.db).await?;
        }

        let end_size = self.get_database_size().await?;
        let space_reclaimed = ((start_size - end_size) as f64) / 1024.0 / 1024.0;

        Ok(MaintenanceResult {
            operation: MaintenanceOperation::DatabaseVacuum,
            success: true,
            items_processed: 1,
            items_cleaned: 0,
            space_reclaimed_mb: space_reclaimed,
            duration_ms: 0, // Will be set by caller
            errors: vec![],
            warnings: if dry_run { vec!["Dry run - no changes made".to_string()] } else { vec![] },
            details: {
                let mut details = HashMap::new();
                details.insert("start_size_mb".to_string(), serde_json::json!(start_size as f64 / 1024.0 / 1024.0));
                details.insert("end_size_mb".to_string(), serde_json::json!(end_size as f64 / 1024.0 / 1024.0));
                details.insert("dry_run".to_string(), serde_json::json!(dry_run));
                details
            },
        })
    }

    /// Perform database integrity check
    async fn perform_integrity_check(&self) -> Result<MaintenanceResult> {
        self.emit_progress(MaintenanceProgress {
            operation: MaintenanceOperation::IntegrityCheck,
            current_step: "Checking integrity".to_string(),
            progress_percentage: 50.0,
            items_processed: 1,
            total_items: 1,
            estimated_time_remaining_ms: None,
            current_item: "Verifying database structure".to_string(),
        }).await;

        let integrity_result = sqlx::query("PRAGMA integrity_check")
            .fetch_one(&self.db)
            .await?;

        let result = integrity_result.get::<String, _>(0);
        let success = result == "ok";

        Ok(MaintenanceResult {
            operation: MaintenanceOperation::IntegrityCheck,
            success,
            items_processed: 1,
            items_cleaned: 0,
            space_reclaimed_mb: 0.0,
            duration_ms: 0,
            errors: if !success { vec![result] } else { vec![] },
            warnings: vec![],
            details: {
                let mut details = HashMap::new();
                details.insert("integrity_result".to_string(), serde_json::json!(result));
                details
            },
        })
    }

    /// Clean up orphaned data
    async fn cleanup_orphaned_data(&self, policy: &CleanupPolicy, dry_run: bool) -> Result<MaintenanceResult> {
        let mut total_cleaned = 0;
        let mut errors = vec![];

        // Clean orphaned validation results
        let orphaned_validations = if dry_run {
            sqlx::query("SELECT COUNT(*) as count FROM validation_results vr LEFT JOIN generated_content gc ON vr.content_id = gc.id WHERE gc.id IS NULL")
                .fetch_one(&self.db).await?.get::<i64, _>("count") as u32
        } else {
            let result = sqlx::query("DELETE FROM validation_results WHERE content_id NOT IN (SELECT id FROM generated_content)")
                .execute(&self.db).await?;
            result.rows_affected() as u32
        };

        total_cleaned += orphaned_validations;

        // Clean orphaned LLM usage records
        let orphaned_llm_usage = if dry_run {
            sqlx::query("SELECT COUNT(*) as count FROM llm_usage lu LEFT JOIN sessions s ON lu.session_id = s.id WHERE s.id IS NULL")
                .fetch_one(&self.db).await?.get::<i64, _>("count") as u32
        } else {
            let result = sqlx::query("DELETE FROM llm_usage WHERE session_id NOT IN (SELECT id FROM sessions)")
                .execute(&self.db).await?;
            result.rows_affected() as u32
        };

        total_cleaned += orphaned_llm_usage;

        Ok(MaintenanceResult {
            operation: MaintenanceOperation::OrphanedDataCleanup,
            success: errors.is_empty(),
            items_processed: total_cleaned,
            items_cleaned: total_cleaned,
            space_reclaimed_mb: (total_cleaned as f64) * 0.01, // Rough estimate
            duration_ms: 0,
            errors,
            warnings: if dry_run { vec!["Dry run - no changes made".to_string()] } else { vec![] },
            details: {
                let mut details = HashMap::new();
                details.insert("orphaned_validations".to_string(), serde_json::json!(orphaned_validations));
                details.insert("orphaned_llm_usage".to_string(), serde_json::json!(orphaned_llm_usage));
                details.insert("dry_run".to_string(), serde_json::json!(dry_run));
                details
            },
        })
    }

    /// Apply retention policies
    async fn apply_retention_policies(&self, policy: &RetentionPolicy, dry_run: bool) -> Result<MaintenanceResult> {
        let mut total_cleaned = 0;
        let cutoff_date = Utc::now() - Duration::days(policy.llm_usage_retention_days as i64);

        // Clean old LLM usage data
        let old_llm_usage = if dry_run {
            sqlx::query("SELECT COUNT(*) as count FROM llm_usage WHERE timestamp < ?")
                .bind(cutoff_date.timestamp())
                .fetch_one(&self.db).await?.get::<i64, _>("count") as u32
        } else {
            let result = sqlx::query("DELETE FROM llm_usage WHERE timestamp < ?")
                .bind(cutoff_date.timestamp())
                .execute(&self.db).await?;
            result.rows_affected() as u32
        };

        total_cleaned += old_llm_usage;

        Ok(MaintenanceResult {
            operation: MaintenanceOperation::RetentionPolicyCleanup,
            success: true,
            items_processed: total_cleaned,
            items_cleaned: total_cleaned,
            space_reclaimed_mb: (total_cleaned as f64) * 0.002,
            duration_ms: 0,
            errors: vec![],
            warnings: if dry_run { vec!["Dry run - no changes made".to_string()] } else { vec![] },
            details: {
                let mut details = HashMap::new();
                details.insert("old_llm_usage_cleaned".to_string(), serde_json::json!(old_llm_usage));
                details.insert("cutoff_date".to_string(), serde_json::json!(cutoff_date.to_rfc3339()));
                details.insert("dry_run".to_string(), serde_json::json!(dry_run));
                details
            },
        })
    }

    /// Optimize storage
    async fn optimize_storage(&self, config: &crate::maintenance::config::StorageMaintenanceConfig, dry_run: bool) -> Result<MaintenanceResult> {
        // This is a placeholder - actual implementation would depend on file storage structure
        Ok(MaintenanceResult {
            operation: MaintenanceOperation::StorageOptimization,
            success: true,
            items_processed: 0,
            items_cleaned: 0,
            space_reclaimed_mb: 0.0,
            duration_ms: 0,
            errors: vec![],
            warnings: vec!["Storage optimization not fully implemented".to_string()],
            details: HashMap::new(),
        })
    }

    /// Maintain database indexes
    async fn maintain_database_indexes(&self, dry_run: bool) -> Result<MaintenanceResult> {
        if !dry_run {
            sqlx::query("PRAGMA optimize").execute(&self.db).await?;
            sqlx::query("REINDEX").execute(&self.db).await?;
        }

        Ok(MaintenanceResult {
            operation: MaintenanceOperation::IndexMaintenance,
            success: true,
            items_processed: 1,
            items_cleaned: 0,
            space_reclaimed_mb: 0.0,
            duration_ms: 0,
            errors: vec![],
            warnings: if dry_run { vec!["Dry run - no changes made".to_string()] } else { vec![] },
            details: HashMap::new(),
        })
    }

    /// Deduplicate content
    async fn deduplicate_content(&self, dry_run: bool) -> Result<MaintenanceResult> {
        // This would require sophisticated content comparison logic
        Ok(MaintenanceResult {
            operation: MaintenanceOperation::ContentDeduplication,
            success: true,
            items_processed: 0,
            items_cleaned: 0,
            space_reclaimed_mb: 0.0,
            duration_ms: 0,
            errors: vec![],
            warnings: vec!["Content deduplication not fully implemented".to_string()],
            details: HashMap::new(),
        })
    }

    /// Audit file system
    async fn audit_file_system(&self) -> Result<MaintenanceResult> {
        // This would check for file system consistency
        Ok(MaintenanceResult {
            operation: MaintenanceOperation::FileSystemAudit,
            success: true,
            items_processed: 0,
            items_cleaned: 0,
            space_reclaimed_mb: 0.0,
            duration_ms: 0,
            errors: vec![],
            warnings: vec!["File system audit not fully implemented".to_string()],
            details: HashMap::new(),
        })
    }

    /// Helper methods
    async fn get_database_size(&self) -> Result<u64> {
        let result = sqlx::query("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()")
            .fetch_one(&self.db)
            .await?;
        Ok(result.get::<i64, _>("size") as u64)
    }

    async fn calculate_total_storage_size(&self) -> Result<u64> {
        // This would calculate actual storage usage across all data directories
        Ok(0) // Placeholder
    }

    async fn estimate_reclaimable_storage(&self) -> Result<u64> {
        // This would estimate how much space could be reclaimed
        Ok(0) // Placeholder
    }

    async fn emit_progress(&self, progress: MaintenanceProgress) {
        if let Some(callback) = &self.progress_callback {
            callback(progress);
        }
    }
}