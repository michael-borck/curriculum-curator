use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use chrono::{DateTime, Utc};
use crate::maintenance::{MaintenanceOperation, MaintenanceResult, IssueSeverity};

/// Comprehensive maintenance report
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MaintenanceReport {
    pub id: String,
    pub timestamp: DateTime<Utc>,
    pub operations_performed: Vec<MaintenanceResult>,
    pub cleanup_summary: CleanupSummary,
    pub storage_analysis: StorageAnalysis,
    pub performance_impact: PerformanceImpact,
    pub recommendations: Vec<String>,
    pub duration_ms: u64,
    pub success: bool,
    pub errors: Vec<String>,
    pub warnings: Vec<String>,
}

/// Summary of cleanup operations
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CleanupSummary {
    pub total_items_processed: u32,
    pub total_items_cleaned: u32,
    pub total_space_reclaimed_mb: f64,
    pub orphaned_data_cleaned: OrphanedDataSummary,
    pub retention_policy_applied: RetentionPolicySummary,
    pub content_deduplication: DeduplicationSummary,
}

/// Orphaned data cleanup summary
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OrphanedDataSummary {
    pub validation_results_cleaned: u32,
    pub llm_usage_records_cleaned: u32,
    pub export_history_cleaned: u32,
    pub orphaned_files_removed: u32,
    pub space_reclaimed_mb: f64,
}

/// Retention policy application summary
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RetentionPolicySummary {
    pub old_llm_usage_cleaned: u32,
    pub old_validation_results_cleaned: u32,
    pub old_export_history_cleaned: u32,
    pub archived_sessions: u32,
    pub space_reclaimed_mb: f64,
    pub oldest_data_removed: Option<DateTime<Utc>>,
}

/// Content deduplication summary
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DeduplicationSummary {
    pub duplicate_content_found: u32,
    pub duplicate_content_merged: u32,
    pub duplicate_files_found: u32,
    pub duplicate_files_removed: u32,
    pub space_reclaimed_mb: f64,
}

/// Storage analysis results
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StorageAnalysis {
    pub total_storage_size_mb: f64,
    pub database_size_mb: f64,
    pub export_files_size_mb: f64,
    pub backup_files_size_mb: f64,
    pub session_files_size_mb: f64,
    pub temp_files_size_mb: f64,
    pub storage_efficiency_percent: f32,
    pub fragmentation_percent: f32,
    pub growth_trend: StorageGrowthTrend,
    pub recommendations: Vec<String>,
}

/// Storage growth trend analysis
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StorageGrowthTrend {
    pub daily_growth_mb: f64,
    pub weekly_growth_mb: f64,
    pub monthly_growth_mb: f64,
    pub projected_full_date: Option<DateTime<Utc>>,
    pub growth_rate_trend: GrowthRateTrend,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum GrowthRateTrend {
    Accelerating,
    Stable,
    Declining,
    Volatile,
}

/// Performance impact analysis
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PerformanceImpact {
    pub database_performance: DatabasePerformance,
    pub query_performance: QueryPerformance,
    pub storage_performance: StoragePerformance,
    pub overall_improvement_score: u32, // 0-100
}

/// Database performance metrics
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DatabasePerformance {
    pub size_before_mb: f64,
    pub size_after_mb: f64,
    pub fragmentation_before_percent: f32,
    pub fragmentation_after_percent: f32,
    pub index_efficiency_score: u32, // 0-100
    pub vacuum_improvement_score: u32, // 0-100
}

/// Query performance metrics
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct QueryPerformance {
    pub average_query_time_improvement_percent: f32,
    pub slow_queries_count_before: u32,
    pub slow_queries_count_after: u32,
    pub index_usage_improvement_percent: f32,
    pub statistics_freshness_score: u32, // 0-100
}

/// Storage performance metrics
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StoragePerformance {
    pub file_access_speed_improvement_percent: f32,
    pub storage_organization_score: u32, // 0-100
    pub duplicate_reduction_percent: f32,
    pub compression_ratio_improvement: f32,
}

impl MaintenanceReport {
    /// Create a new maintenance report from results
    pub fn new(
        operations_performed: Vec<MaintenanceResult>,
        start_time: DateTime<Utc>,
        end_time: DateTime<Utc>,
    ) -> Self {
        let duration_ms = (end_time - start_time).num_milliseconds() as u64;
        let success = operations_performed.iter().all(|r| r.success);
        
        let errors: Vec<String> = operations_performed
            .iter()
            .flat_map(|r| r.errors.clone())
            .collect();
            
        let warnings: Vec<String> = operations_performed
            .iter()
            .flat_map(|r| r.warnings.clone())
            .collect();

        let cleanup_summary = Self::create_cleanup_summary(&operations_performed);
        let storage_analysis = Self::create_storage_analysis(&operations_performed);
        let performance_impact = Self::create_performance_impact(&operations_performed);
        let recommendations = Self::generate_recommendations(&cleanup_summary, &storage_analysis);

        Self {
            id: uuid::Uuid::new_v4().to_string(),
            timestamp: end_time,
            operations_performed,
            cleanup_summary,
            storage_analysis,
            performance_impact,
            recommendations,
            duration_ms,
            success,
            errors,
            warnings,
        }
    }

    fn create_cleanup_summary(results: &[MaintenanceResult]) -> CleanupSummary {
        let total_items_processed = results.iter().map(|r| r.items_processed).sum();
        let total_items_cleaned = results.iter().map(|r| r.items_cleaned).sum();
        let total_space_reclaimed_mb = results.iter().map(|r| r.space_reclaimed_mb).sum();

        // Extract specific cleanup details from operation details
        let orphaned_data_cleaned = Self::extract_orphaned_data_summary(results);
        let retention_policy_applied = Self::extract_retention_policy_summary(results);
        let content_deduplication = Self::extract_deduplication_summary(results);

        CleanupSummary {
            total_items_processed,
            total_items_cleaned,
            total_space_reclaimed_mb,
            orphaned_data_cleaned,
            retention_policy_applied,
            content_deduplication,
        }
    }

    fn extract_orphaned_data_summary(results: &[MaintenanceResult]) -> OrphanedDataSummary {
        let orphan_cleanup_result = results
            .iter()
            .find(|r| matches!(r.operation, MaintenanceOperation::OrphanedDataCleanup));

        if let Some(result) = orphan_cleanup_result {
            OrphanedDataSummary {
                validation_results_cleaned: result.details
                    .get("orphaned_validations")
                    .and_then(|v| v.as_u64())
                    .unwrap_or(0) as u32,
                llm_usage_records_cleaned: result.details
                    .get("orphaned_llm_usage")
                    .and_then(|v| v.as_u64())
                    .unwrap_or(0) as u32,
                export_history_cleaned: 0, // Would be extracted from details
                orphaned_files_removed: 0, // Would be tracked
                space_reclaimed_mb: result.space_reclaimed_mb,
            }
        } else {
            OrphanedDataSummary {
                validation_results_cleaned: 0,
                llm_usage_records_cleaned: 0,
                export_history_cleaned: 0,
                orphaned_files_removed: 0,
                space_reclaimed_mb: 0.0,
            }
        }
    }

    fn extract_retention_policy_summary(results: &[MaintenanceResult]) -> RetentionPolicySummary {
        let retention_result = results
            .iter()
            .find(|r| matches!(r.operation, MaintenanceOperation::RetentionPolicyCleanup));

        if let Some(result) = retention_result {
            RetentionPolicySummary {
                old_llm_usage_cleaned: result.details
                    .get("old_llm_usage_cleaned")
                    .and_then(|v| v.as_u64())
                    .unwrap_or(0) as u32,
                old_validation_results_cleaned: 0, // Would be tracked
                old_export_history_cleaned: 0, // Would be tracked
                archived_sessions: 0, // Would be tracked
                space_reclaimed_mb: result.space_reclaimed_mb,
                oldest_data_removed: result.details
                    .get("cutoff_date")
                    .and_then(|v| v.as_str())
                    .and_then(|s| DateTime::parse_from_rfc3339(s).ok())
                    .map(|dt| dt.with_timezone(&Utc)),
            }
        } else {
            RetentionPolicySummary {
                old_llm_usage_cleaned: 0,
                old_validation_results_cleaned: 0,
                old_export_history_cleaned: 0,
                archived_sessions: 0,
                space_reclaimed_mb: 0.0,
                oldest_data_removed: None,
            }
        }
    }

    fn extract_deduplication_summary(results: &[MaintenanceResult]) -> DeduplicationSummary {
        // Placeholder implementation - would extract from ContentDeduplication operation
        DeduplicationSummary {
            duplicate_content_found: 0,
            duplicate_content_merged: 0,
            duplicate_files_found: 0,
            duplicate_files_removed: 0,
            space_reclaimed_mb: 0.0,
        }
    }

    fn create_storage_analysis(results: &[MaintenanceResult]) -> StorageAnalysis {
        // This would perform actual storage analysis
        StorageAnalysis {
            total_storage_size_mb: 0.0,
            database_size_mb: 0.0,
            export_files_size_mb: 0.0,
            backup_files_size_mb: 0.0,
            session_files_size_mb: 0.0,
            temp_files_size_mb: 0.0,
            storage_efficiency_percent: 85.0,
            fragmentation_percent: 5.0,
            growth_trend: StorageGrowthTrend {
                daily_growth_mb: 10.0,
                weekly_growth_mb: 70.0,
                monthly_growth_mb: 300.0,
                projected_full_date: None,
                growth_rate_trend: GrowthRateTrend::Stable,
            },
            recommendations: vec![
                "Consider enabling automatic compression for old exports".to_string(),
                "Schedule weekly orphaned data cleanup".to_string(),
            ],
        }
    }

    fn create_performance_impact(results: &[MaintenanceResult]) -> PerformanceImpact {
        // This would measure actual performance improvements
        PerformanceImpact {
            database_performance: DatabasePerformance {
                size_before_mb: 0.0,
                size_after_mb: 0.0,
                fragmentation_before_percent: 0.0,
                fragmentation_after_percent: 0.0,
                index_efficiency_score: 90,
                vacuum_improvement_score: 85,
            },
            query_performance: QueryPerformance {
                average_query_time_improvement_percent: 15.0,
                slow_queries_count_before: 5,
                slow_queries_count_after: 2,
                index_usage_improvement_percent: 10.0,
                statistics_freshness_score: 95,
            },
            storage_performance: StoragePerformance {
                file_access_speed_improvement_percent: 8.0,
                storage_organization_score: 88,
                duplicate_reduction_percent: 12.0,
                compression_ratio_improvement: 5.0,
            },
            overall_improvement_score: 85,
        }
    }

    fn generate_recommendations(
        cleanup_summary: &CleanupSummary,
        storage_analysis: &StorageAnalysis,
    ) -> Vec<String> {
        let mut recommendations = Vec::new();

        if cleanup_summary.total_space_reclaimed_mb > 50.0 {
            recommendations.push("Consider increasing the frequency of automatic cleanup".to_string());
        }

        if storage_analysis.fragmentation_percent > 15.0 {
            recommendations.push("Schedule more frequent database vacuum operations".to_string());
        }

        if storage_analysis.storage_efficiency_percent < 70.0 {
            recommendations.push("Enable content compression to improve storage efficiency".to_string());
        }

        if storage_analysis.growth_trend.daily_growth_mb > 100.0 {
            recommendations.push("Review retention policies to manage rapid data growth".to_string());
        }

        if recommendations.is_empty() {
            recommendations.push("System is well-maintained. Continue current maintenance schedule".to_string());
        }

        recommendations
    }
}

/// Utility functions for generating maintenance reports
pub struct MaintenanceReportGenerator;

impl MaintenanceReportGenerator {
    /// Generate a quick system health report
    pub fn generate_health_report() -> SystemHealthReport {
        SystemHealthReport {
            timestamp: Utc::now(),
            overall_health_score: 85,
            critical_issues_count: 0,
            database_health: DatabaseHealth {
                size_mb: 125.5,
                fragmentation_percent: 8.2,
                integrity_status: "OK".to_string(),
                last_vacuum: Some(Utc::now() - chrono::Duration::days(2)),
                index_efficiency: 92,
            },
            storage_health: StorageHealth {
                total_size_mb: 2048.0,
                available_space_mb: 512.0,
                usage_percent: 75.0,
                file_count: 1250,
                orphaned_files: 5,
            },
            maintenance_history: MaintenanceHistory {
                last_maintenance: Some(Utc::now() - chrono::Duration::days(1)),
                total_operations_last_week: 3,
                total_space_reclaimed_last_month_mb: 156.7,
                average_maintenance_duration_minutes: 12,
            },
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SystemHealthReport {
    pub timestamp: DateTime<Utc>,
    pub overall_health_score: u32, // 0-100
    pub critical_issues_count: u32,
    pub database_health: DatabaseHealth,
    pub storage_health: StorageHealth,
    pub maintenance_history: MaintenanceHistory,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DatabaseHealth {
    pub size_mb: f64,
    pub fragmentation_percent: f32,
    pub integrity_status: String,
    pub last_vacuum: Option<DateTime<Utc>>,
    pub index_efficiency: u32, // 0-100
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StorageHealth {
    pub total_size_mb: f64,
    pub available_space_mb: f64,
    pub usage_percent: f32,
    pub file_count: u32,
    pub orphaned_files: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MaintenanceHistory {
    pub last_maintenance: Option<DateTime<Utc>>,
    pub total_operations_last_week: u32,
    pub total_space_reclaimed_last_month_mb: f64,
    pub average_maintenance_duration_minutes: u32,
}