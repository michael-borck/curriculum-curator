use super::*;
use crate::data_export::service::DataExportService;
use tauri::{State, Emitter};
use std::sync::Arc;
use tokio::sync::Mutex;
use anyhow::Result;

#[tauri::command]
pub async fn get_data_export_config(
    export_service: State<'_, Arc<Mutex<DataExportService>>>,
) -> Result<DataExportConfig, String> {
    let service = export_service.lock().await;
    Ok(service.get_config().await)
}

#[tauri::command]
pub async fn update_data_export_config(
    export_service: State<'_, Arc<Mutex<DataExportService>>>,
    config: DataExportConfig,
) -> Result<(), String> {
    let service = export_service.lock().await;
    service.update_config(config).await
        .map_err(|e| e.to_string())
}

#[tauri::command]
pub async fn export_data(
    export_service: State<'_, Arc<Mutex<DataExportService>>>,
    request: ExportRequest,
) -> Result<ExportResult, String> {
    let service = export_service.lock().await;
    service.export_data(request, None).await
        .map_err(|e| e.to_string())
}

#[tauri::command]
pub async fn export_data_with_progress(
    export_service: State<'_, Arc<Mutex<DataExportService>>>,
    request: ExportRequest,
    window: tauri::Window,
) -> Result<ExportResult, String> {
    let service = export_service.lock().await;
    
    // Create progress callback that emits events to frontend
    let progress_callback = Box::new(move |progress: ExportProgress| {
        let _ = window.emit("export-progress", &progress);
    });
    
    service.export_data(request, Some(progress_callback)).await
        .map_err(|e| e.to_string())
}

#[tauri::command]
pub async fn get_export_formats() -> Result<Vec<ExportFormatInfo>, String> {
    Ok(vec![
        ExportFormatInfo {
            format: ExportFormat::Archive(ArchiveFormat::Zip),
            display_name: "ZIP Archive".to_string(),
            description: "Standard ZIP archive with all content and metadata".to_string(),
            extension: "zip".to_string(),
            supports_compression: true,
            supports_encryption: true,
            recommended_for: vec!["General sharing".to_string(), "Cross-platform compatibility".to_string()],
        },
        ExportFormatInfo {
            format: ExportFormat::Archive(ArchiveFormat::TarGz),
            display_name: "TAR.GZ Archive".to_string(),
            description: "Compressed TAR archive for efficient storage".to_string(),
            extension: "tar.gz".to_string(),
            supports_compression: true,
            supports_encryption: false,
            recommended_for: vec!["Unix/Linux systems".to_string(), "Efficient compression".to_string()],
        },
        ExportFormatInfo {
            format: ExportFormat::Database(DatabaseFormat::JsonExport),
            display_name: "JSON Export".to_string(),
            description: "Human-readable JSON format for data analysis".to_string(),
            extension: "json".to_string(),
            supports_compression: false,
            supports_encryption: false,
            recommended_for: vec!["Data analysis".to_string(), "Integration with other tools".to_string()],
        },
        ExportFormatInfo {
            format: ExportFormat::Portable(PortableFormat::CurriculumPack),
            display_name: "Curriculum Pack".to_string(),
            description: "Self-contained package for sharing curricula".to_string(),
            extension: "ccpack".to_string(),
            supports_compression: true,
            supports_encryption: true,
            recommended_for: vec!["Educator sharing".to_string(), "Complete curriculum distribution".to_string()],
        },
        ExportFormatInfo {
            format: ExportFormat::Portable(PortableFormat::EducatorBundle),
            display_name: "Educator Bundle".to_string(),
            description: "Educator-friendly bundle with documentation".to_string(),
            extension: "edubundle".to_string(),
            supports_compression: true,
            supports_encryption: false,
            recommended_for: vec!["Educational institutions".to_string(), "Teaching resource sharing".to_string()],
        },
        ExportFormatInfo {
            format: ExportFormat::Portable(PortableFormat::MinimalExport),
            display_name: "Minimal Export".to_string(),
            description: "Lightweight export without media files".to_string(),
            extension: "ccmin".to_string(),
            supports_compression: true,
            supports_encryption: false,
            recommended_for: vec!["Quick sharing".to_string(), "Text-only content".to_string()],
        },
    ])
}

#[tauri::command]
pub async fn validate_export_request(
    request: ExportRequest,
) -> Result<ExportValidation, String> {
    let mut validation = ExportValidation {
        is_valid: true,
        warnings: vec![],
        errors: vec![],
        estimated_size_mb: 0,
        estimated_time_minutes: 0,
    };

    // Check output path
    if !request.output_path.exists() {
        validation.errors.push("Output directory does not exist".to_string());
        validation.is_valid = false;
    }

    // Check if output path is writable
    if request.output_path.exists() && request.output_path.metadata().map_or(true, |m| m.permissions().readonly()) {
        validation.errors.push("Output directory is not writable".to_string());
        validation.is_valid = false;
    }

    // Validate session filter
    match &request.sessions {
        ExportSessionFilter::SelectedSessions(sessions) if sessions.is_empty() => {
            validation.errors.push("No sessions selected for export".to_string());
            validation.is_valid = false;
        }
        ExportSessionFilter::DateRange { start, end } if start >= end => {
            validation.errors.push("Invalid date range: start date must be before end date".to_string());
            validation.is_valid = false;
        }
        ExportSessionFilter::RecentSessions(count) if *count == 0 => {
            validation.errors.push("Recent sessions count must be greater than 0".to_string());
            validation.is_valid = false;
        }
        _ => {}
    }

    // Check for encryption requirements
    if request.options.encrypt && request.options.password.is_none() {
        validation.errors.push("Password required for encrypted exports".to_string());
        validation.is_valid = false;
    }

    // Estimate size and time (simplified)
    validation.estimated_size_mb = match &request.sessions {
        ExportSessionFilter::All => 50, // Rough estimate
        ExportSessionFilter::SelectedSessions(sessions) => sessions.len() as u64 * 5,
        ExportSessionFilter::DateRange { .. } => 30,
        ExportSessionFilter::RecentSessions(count) => *count as u64 * 5,
    };

    validation.estimated_time_minutes = match request.format {
        ExportFormat::Archive(_) => (validation.estimated_size_mb / 10).max(1),
        ExportFormat::Database(_) => (validation.estimated_size_mb / 20).max(1),
        ExportFormat::Portable(_) => (validation.estimated_size_mb / 15).max(1),
    };

    // Add warnings for large exports
    if validation.estimated_size_mb > 100 {
        validation.warnings.push(format!(
            "Large export estimated: {} MB. Consider using compression or splitting the export.",
            validation.estimated_size_mb
        ));
    }

    if validation.estimated_time_minutes > 10 {
        validation.warnings.push(format!(
            "Long export estimated: {} minutes. Consider exporting in smaller batches.",
            validation.estimated_time_minutes
        ));
    }

    Ok(validation)
}

#[tauri::command]
pub async fn preview_export_contents(
    export_service: State<'_, Arc<Mutex<DataExportService>>>,
    session_filter: ExportSessionFilter,
) -> Result<ExportPreview, String> {
    // This would provide a preview of what will be exported
    // For now, return a basic preview structure
    
    let preview = ExportPreview {
        session_count: match &session_filter {
            ExportSessionFilter::All => 0, // Would need to count actual sessions
            ExportSessionFilter::SelectedSessions(sessions) => sessions.len() as u32,
            ExportSessionFilter::DateRange { .. } => 0, // Would need to query by date
            ExportSessionFilter::RecentSessions(count) => *count,
        },
        content_types: vec!["Slides".to_string(), "InstructorNotes".to_string(), "Worksheets".to_string()],
        estimated_files: 10, // Would be calculated based on actual content
        estimated_size_bytes: 1024 * 1024, // 1MB estimate
        sessions_summary: vec![], // Would contain actual session info
    };

    Ok(preview)
}

#[tauri::command]
pub async fn get_recent_exports() -> Result<Vec<RecentExport>, String> {
    // This would return a list of recent exports
    // For now, return an empty list
    Ok(vec![])
}

#[tauri::command]
pub async fn cleanup_old_exports(
    days_old: u32,
) -> Result<CleanupResult, String> {
    // This would clean up old export files
    // For now, return a basic result
    Ok(CleanupResult {
        files_removed: 0,
        space_freed_bytes: 0,
        errors: vec![],
    })
}

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct ExportFormatInfo {
    pub format: ExportFormat,
    pub display_name: String,
    pub description: String,
    pub extension: String,
    pub supports_compression: bool,
    pub supports_encryption: bool,
    pub recommended_for: Vec<String>,
}

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct ExportValidation {
    pub is_valid: bool,
    pub warnings: Vec<String>,
    pub errors: Vec<String>,
    pub estimated_size_mb: u64,
    pub estimated_time_minutes: u64,
}

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct ExportPreview {
    pub session_count: u32,
    pub content_types: Vec<String>,
    pub estimated_files: u32,
    pub estimated_size_bytes: u64,
    pub sessions_summary: Vec<SessionSummary>,
}

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct RecentExport {
    pub export_id: String,
    pub created_at: chrono::DateTime<chrono::Utc>,
    pub format: ExportFormat,
    pub file_path: PathBuf,
    pub file_size: u64,
    pub sessions_count: u32,
}

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct CleanupResult {
    pub files_removed: u32,
    pub space_freed_bytes: u64,
    pub errors: Vec<String>,
}