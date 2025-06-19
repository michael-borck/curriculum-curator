use tauri::{command, State, Window, Emitter};
use std::sync::Arc;
use tokio::sync::Mutex;
use anyhow::Result;

use crate::maintenance::{
    MaintenanceService, MaintenanceConfig, MaintenanceOperation, 
    MaintenanceResult, MaintenanceIssue, MaintenanceProgress
};

/// Get current maintenance configuration
#[command]
pub async fn get_maintenance_config(
    maintenance_service: State<'_, Arc<Mutex<MaintenanceService>>>,
) -> Result<MaintenanceConfig, String> {
    let service = maintenance_service.lock().await;
    Ok(service.get_config().await)
}

/// Update maintenance configuration
#[command]
pub async fn update_maintenance_config(
    maintenance_service: State<'_, Arc<Mutex<MaintenanceService>>>,
    config: MaintenanceConfig,
) -> Result<(), String> {
    let service = maintenance_service.lock().await;
    service.update_config(config).await
        .map_err(|e| e.to_string())
}

/// Analyze system for maintenance issues
#[command]
pub async fn analyze_maintenance_issues(
    maintenance_service: State<'_, Arc<Mutex<MaintenanceService>>>,
) -> Result<Vec<MaintenanceIssue>, String> {
    let service = maintenance_service.lock().await;
    service.analyze_maintenance_issues().await
        .map_err(|e| e.to_string())
}

/// Perform maintenance operations
#[command]
pub async fn perform_maintenance(
    maintenance_service: State<'_, Arc<Mutex<MaintenanceService>>>,
    operations: Vec<MaintenanceOperation>,
    dry_run: bool,
) -> Result<Vec<MaintenanceResult>, String> {
    let service = maintenance_service.lock().await;
    service.perform_maintenance(operations, dry_run).await
        .map_err(|e| e.to_string())
}

/// Perform maintenance operations with progress updates
#[command]
pub async fn perform_maintenance_with_progress(
    maintenance_service: State<'_, Arc<Mutex<MaintenanceService>>>,
    operations: Vec<MaintenanceOperation>,
    dry_run: bool,
    window: Window,
) -> Result<Vec<MaintenanceResult>, String> {
    let mut service = maintenance_service.lock().await;
    
    // Set progress callback to emit events to frontend
    service.set_progress_callback(move |progress: MaintenanceProgress| {
        let _ = window.emit("maintenance-progress", &progress);
    });
    
    service.perform_maintenance(operations, dry_run).await
        .map_err(|e| e.to_string())
}

/// Get available maintenance operations
#[command]
pub async fn get_available_maintenance_operations() -> Result<Vec<MaintenanceOperationInfo>, String> {
    Ok(vec![
        MaintenanceOperationInfo {
            operation: MaintenanceOperation::DatabaseVacuum,
            display_name: "Database Vacuum".to_string(),
            description: "Reclaim unused database space and defragment".to_string(),
            estimated_duration_minutes: 5,
            requires_backup: true,
            destructive: false,
            can_run_while_active: false,
        },
        MaintenanceOperationInfo {
            operation: MaintenanceOperation::IntegrityCheck,
            display_name: "Integrity Check".to_string(),
            description: "Verify database structure and data integrity".to_string(),
            estimated_duration_minutes: 2,
            requires_backup: false,
            destructive: false,
            can_run_while_active: true,
        },
        MaintenanceOperationInfo {
            operation: MaintenanceOperation::OrphanedDataCleanup,
            display_name: "Orphaned Data Cleanup".to_string(),
            description: "Remove data that references deleted items".to_string(),
            estimated_duration_minutes: 10,
            requires_backup: true,
            destructive: true,
            can_run_while_active: false,
        },
        MaintenanceOperationInfo {
            operation: MaintenanceOperation::RetentionPolicyCleanup,
            display_name: "Retention Policy Cleanup".to_string(),
            description: "Remove old data according to retention policies".to_string(),
            estimated_duration_minutes: 15,
            requires_backup: true,
            destructive: true,
            can_run_while_active: false,
        },
        MaintenanceOperationInfo {
            operation: MaintenanceOperation::StorageOptimization,
            display_name: "Storage Optimization".to_string(),
            description: "Optimize file storage and archive old files".to_string(),
            estimated_duration_minutes: 30,
            requires_backup: false,
            destructive: false,
            can_run_while_active: true,
        },
        MaintenanceOperationInfo {
            operation: MaintenanceOperation::IndexMaintenance,
            display_name: "Index Maintenance".to_string(),
            description: "Rebuild indexes and update query statistics".to_string(),
            estimated_duration_minutes: 5,
            requires_backup: false,
            destructive: false,
            can_run_while_active: false,
        },
        MaintenanceOperationInfo {
            operation: MaintenanceOperation::ContentDeduplication,
            display_name: "Content Deduplication".to_string(),
            description: "Find and merge duplicate content to save space".to_string(),
            estimated_duration_minutes: 20,
            requires_backup: true,
            destructive: true,
            can_run_while_active: false,
        },
        MaintenanceOperationInfo {
            operation: MaintenanceOperation::FileSystemAudit,
            display_name: "File System Audit".to_string(),
            description: "Check file system consistency and repair issues".to_string(),
            estimated_duration_minutes: 15,
            requires_backup: false,
            destructive: false,
            can_run_while_active: true,
        },
    ])
}

/// Get maintenance operation recommendations based on system analysis
#[command]
pub async fn get_maintenance_recommendations(
    maintenance_service: State<'_, Arc<Mutex<MaintenanceService>>>,
) -> Result<Vec<MaintenanceRecommendation>, String> {
    let service = maintenance_service.lock().await;
    let issues = service.analyze_maintenance_issues().await
        .map_err(|e| e.to_string())?;
    
    let mut recommendations = Vec::new();
    
    for issue in issues {
        let priority = match issue.severity {
            crate::maintenance::IssueSeverity::Critical => RecommendationPriority::Critical,
            crate::maintenance::IssueSeverity::High => RecommendationPriority::High,
            crate::maintenance::IssueSeverity::Medium => RecommendationPriority::Medium,
            crate::maintenance::IssueSeverity::Low => RecommendationPriority::Low,
        };
        
        recommendations.push(MaintenanceRecommendation {
            operation: issue.operation,
            priority,
            reason: issue.description,
            estimated_time_minutes: 10, // Default estimate
            estimated_space_savings_mb: issue.estimated_space_savings_mb.unwrap_or(0.0),
            can_auto_execute: issue.can_auto_fix,
            affected_items: issue.affected_items,
        });
    }
    
    // Sort by priority
    recommendations.sort_by(|a, b| {
        match (&a.priority, &b.priority) {
            (RecommendationPriority::Critical, _) => std::cmp::Ordering::Less,
            (_, RecommendationPriority::Critical) => std::cmp::Ordering::Greater,
            (RecommendationPriority::High, RecommendationPriority::Low | RecommendationPriority::Medium) => std::cmp::Ordering::Less,
            (RecommendationPriority::Low | RecommendationPriority::Medium, RecommendationPriority::High) => std::cmp::Ordering::Greater,
            (RecommendationPriority::Medium, RecommendationPriority::Low) => std::cmp::Ordering::Less,
            (RecommendationPriority::Low, RecommendationPriority::Medium) => std::cmp::Ordering::Greater,
            _ => std::cmp::Ordering::Equal,
        }
    });
    
    Ok(recommendations)
}

/// Estimate maintenance operation impact
#[command]
pub async fn estimate_maintenance_impact(
    maintenance_service: State<'_, Arc<Mutex<MaintenanceService>>>,
    operations: Vec<MaintenanceOperation>,
) -> Result<MaintenanceImpactEstimate, String> {
    // This would analyze the impact of the selected operations
    let total_operations = operations.len();
    let estimated_duration_minutes = total_operations as u32 * 10; // Rough estimate
    
    Ok(MaintenanceImpactEstimate {
        total_operations: total_operations as u32,
        estimated_duration_minutes,
        estimated_space_savings_mb: 0.0, // Would be calculated based on actual analysis
        requires_backup: operations.iter().any(|op| matches!(op, 
            MaintenanceOperation::OrphanedDataCleanup | 
            MaintenanceOperation::RetentionPolicyCleanup | 
            MaintenanceOperation::ContentDeduplication
        )),
        can_run_while_active: operations.iter().all(|op| matches!(op,
            MaintenanceOperation::IntegrityCheck |
            MaintenanceOperation::StorageOptimization |
            MaintenanceOperation::FileSystemAudit
        )),
        affected_sessions: 0, // Would be calculated
        affected_content_items: 0, // Would be calculated
    })
}

/// Get system health summary
#[command]
pub async fn get_system_health_summary(
    maintenance_service: State<'_, Arc<Mutex<MaintenanceService>>>,
) -> Result<SystemHealthSummary, String> {
    let service = maintenance_service.lock().await;
    let issues = service.analyze_maintenance_issues().await
        .map_err(|e| e.to_string())?;
    
    let critical_issues = issues.iter().filter(|i| matches!(i.severity, crate::maintenance::IssueSeverity::Critical)).count();
    let high_issues = issues.iter().filter(|i| matches!(i.severity, crate::maintenance::IssueSeverity::High)).count();
    let medium_issues = issues.iter().filter(|i| matches!(i.severity, crate::maintenance::IssueSeverity::Medium)).count();
    let low_issues = issues.iter().filter(|i| matches!(i.severity, crate::maintenance::IssueSeverity::Low)).count();
    
    let overall_score = if critical_issues > 0 {
        20
    } else if high_issues > 2 {
        40
    } else if high_issues > 0 || medium_issues > 3 {
        60
    } else if medium_issues > 0 || low_issues > 5 {
        80
    } else {
        100
    };
    
    Ok(SystemHealthSummary {
        overall_health_score: overall_score,
        critical_issues: critical_issues as u32,
        high_priority_issues: high_issues as u32,
        medium_priority_issues: medium_issues as u32,
        low_priority_issues: low_issues as u32,
        total_issues: issues.len() as u32,
        estimated_space_reclaimable_mb: issues.iter()
            .filter_map(|i| i.estimated_space_savings_mb)
            .sum(),
        last_maintenance_date: None, // Would track this
        next_recommended_maintenance: "Within 7 days".to_string(), // Would calculate this
    })
}

// Supporting types for the commands
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MaintenanceOperationInfo {
    pub operation: MaintenanceOperation,
    pub display_name: String,
    pub description: String,
    pub estimated_duration_minutes: u32,
    pub requires_backup: bool,
    pub destructive: bool,
    pub can_run_while_active: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MaintenanceRecommendation {
    pub operation: MaintenanceOperation,
    pub priority: RecommendationPriority,
    pub reason: String,
    pub estimated_time_minutes: u32,
    pub estimated_space_savings_mb: f64,
    pub can_auto_execute: bool,
    pub affected_items: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum RecommendationPriority {
    Critical,
    High,
    Medium,
    Low,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MaintenanceImpactEstimate {
    pub total_operations: u32,
    pub estimated_duration_minutes: u32,
    pub estimated_space_savings_mb: f64,
    pub requires_backup: bool,
    pub can_run_while_active: bool,
    pub affected_sessions: u32,
    pub affected_content_items: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SystemHealthSummary {
    pub overall_health_score: u32, // 0-100
    pub critical_issues: u32,
    pub high_priority_issues: u32,
    pub medium_priority_issues: u32,
    pub low_priority_issues: u32,
    pub total_issues: u32,
    pub estimated_space_reclaimable_mb: f64,
    pub last_maintenance_date: Option<String>,
    pub next_recommended_maintenance: String,
}