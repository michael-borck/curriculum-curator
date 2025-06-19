use super::{FileManager, FileOperation, FileMetadata, SaveOperation, ExportOperation, FileStorage, StorageLocation, StorageConfig};
use crate::session::{SessionManager, Session};
use crate::export::{ExportManager, ExportFormat, ExportOptions};
use anyhow::Result;
use serde::{Deserialize, Serialize};
use std::path::PathBuf;
use tauri::State;
use tokio::sync::Mutex;
use uuid::Uuid;

/// Storage paths structure
#[derive(Debug, Serialize, Deserialize)]
pub struct StoragePaths {
    pub sessions: PathBuf,
    pub exports: PathBuf,
    pub backups: PathBuf,
    pub templates: PathBuf,
}

/// Global file service state
pub struct FileService {
    file_manager: Mutex<FileManager>,
    storage: Mutex<FileStorage>,
    session_manager: Mutex<SessionManager>,
}

impl FileService {
    pub async fn new(db_path: &str, storage_config: Option<StorageConfig>) -> Result<Self> {
        let session_manager = SessionManager::new(db_path).await?;
        let export_manager = ExportManager::new();
        let storage = FileStorage::new(storage_config.unwrap_or_default())?;
        let save_location = storage.get_location_path(&StorageLocation::Sessions);
        let file_manager = FileManager::new(export_manager, save_location);

        Ok(Self {
            file_manager: Mutex::new(file_manager),
            storage: Mutex::new(storage),
            session_manager: Mutex::new(session_manager),
        })
    }

    pub async fn get_storage_paths(&self) -> Result<StoragePaths> {
        let storage = self.storage.lock().await;
        Ok(StoragePaths {
            sessions: storage.get_location_path(&StorageLocation::Sessions),
            exports: storage.get_location_path(&StorageLocation::Exports),
            backups: storage.get_location_path(&StorageLocation::Backups),
            templates: storage.get_location_path(&StorageLocation::Templates),
        })
    }
}

/// Request to save a session
#[derive(Debug, Serialize, Deserialize)]
pub struct SaveSessionRequest {
    pub session_id: String,
    pub file_path: Option<PathBuf>,
    pub include_metadata: Option<bool>,
    pub backup_existing: Option<bool>,
    pub auto_timestamp: Option<bool>,
}

/// Request to export content
#[derive(Debug, Serialize, Deserialize)]
pub struct ExportContentRequest {
    pub session_id: String,
    pub content_ids: Option<Vec<String>>,
    pub format: ExportFormat,
    pub file_path: Option<PathBuf>,
    pub options: Option<ExportOptions>,
    pub open_after_export: Option<bool>,
}

/// Request to load a session from file
#[derive(Debug, Serialize, Deserialize)]
pub struct LoadSessionRequest {
    pub file_path: PathBuf,
}

/// File operation result
#[derive(Debug, Serialize, Deserialize)]
pub struct FileOperationResult {
    pub success: bool,
    pub file_path: PathBuf,
    pub metadata: Option<FileMetadata>,
    pub message: String,
}

/// Storage statistics
#[derive(Debug, Serialize, Deserialize)]
pub struct StorageStats {
    pub total_files: usize,
    pub total_size_bytes: u64,
    pub files_by_type: std::collections::HashMap<String, usize>,
    pub oldest_file: Option<chrono::DateTime<chrono::Utc>>,
    pub newest_file: Option<chrono::DateTime<chrono::Utc>>,
}

/// File listing options
#[derive(Debug, Serialize, Deserialize)]
pub struct ListFilesOptions {
    pub location: StorageLocation,
    pub recursive: Option<bool>,
    pub filter_extension: Option<String>,
    pub sort_by: Option<String>, // "name", "date", "size"
    pub limit: Option<usize>,
}

/// Tauri command to save a session to file
#[tauri::command]
pub async fn save_session_to_file(
    request: SaveSessionRequest,
    service: State<'_, FileService>,
) -> Result<FileOperationResult, String> {
    let session_id = Uuid::parse_str(&request.session_id).map_err(|e| e.to_string())?;
    
    // Load the session
    let session = {
        let session_manager = service.session_manager.lock().await;
        session_manager.load_session(session_id).await
            .map_err(|e| e.to_string())?
            .ok_or("Session not found".to_string())?
    };

    // Determine file path
    let file_path = if let Some(path) = request.file_path {
        path
    } else {
        let storage = service.storage.lock().await;
        let filename = {
            let file_manager = service.file_manager.lock().await;
            file_manager.suggest_filename(&session, None)
        };
        storage.get_session_file_path(session_id, &filename, None)
    };

    // Create save operation
    let save_operation = SaveOperation {
        session_id,
        location: file_path.clone(),
        include_metadata: request.include_metadata.unwrap_or(true),
        backup_existing: request.backup_existing.unwrap_or(true),
        auto_timestamp: request.auto_timestamp.unwrap_or(false),
    };

    // Perform save
    let metadata = {
        let file_manager = service.file_manager.lock().await;
        file_manager.save_session(&session, &save_operation).await
            .map_err(|e| e.to_string())?
    };

    Ok(FileOperationResult {
        success: true,
        file_path,
        metadata: Some(metadata),
        message: "Session saved successfully".to_string(),
    })
}

/// Tauri command to export content to various formats
#[tauri::command]
pub async fn export_session_content(
    request: ExportContentRequest,
    service: State<'_, FileService>,
) -> Result<FileOperationResult, String> {
    let session_id = Uuid::parse_str(&request.session_id).map_err(|e| e.to_string())?;
    
    // Load the session
    let session = {
        let session_manager = service.session_manager.lock().await;
        session_manager.load_session(session_id).await
            .map_err(|e| e.to_string())?
            .ok_or("Session not found".to_string())?
    };

    // Determine file path
    let file_path = if let Some(path) = request.file_path {
        path
    } else {
        let storage = service.storage.lock().await;
        let filename = {
            let file_manager = service.file_manager.lock().await;
            file_manager.suggest_filename(&session, Some(&request.format))
        };
        let format_folder = match &request.format {
            ExportFormat::Markdown => Some("markdown"),
            ExportFormat::Html => Some("html"),
            ExportFormat::Pdf => Some("pdf"),
            ExportFormat::PowerPoint => Some("powerpoint"),
            ExportFormat::Word => Some("word"),
            #[cfg(feature = "quarto-integration")]
            ExportFormat::Quarto => Some("quarto"),
        };
        storage.get_export_file_path(Some(session_id), &filename, format_folder, None)
    };

    // Create export operation
    let export_operation = ExportOperation {
        session_id,
        content_ids: request.content_ids,
        format: request.format,
        destination: file_path.clone(),
        options: request.options.unwrap_or_default(),
        open_after_export: request.open_after_export.unwrap_or(false),
    };

    // Ensure directory exists
    if let Some(parent) = file_path.parent() {
        tokio::fs::create_dir_all(parent).await.map_err(|e| e.to_string())?;
    }

    // Perform export
    let metadata = {
        let file_manager = service.file_manager.lock().await;
        file_manager.export_content(&session, &export_operation).await
            .map_err(|e| e.to_string())?
    };

    Ok(FileOperationResult {
        success: true,
        file_path,
        metadata: Some(metadata),
        message: "Content exported successfully".to_string(),
    })
}

/// Tauri command to load a session from file
#[tauri::command]
pub async fn load_session_from_file(
    request: LoadSessionRequest,
    service: State<'_, FileService>,
) -> Result<Session, String> {
    let file_manager = service.file_manager.lock().await;
    let session = file_manager.load_session(&request.file_path).await
        .map_err(|e| e.to_string())?;
    
    // Optionally save to database for persistence
    drop(file_manager);
    let session_manager = service.session_manager.lock().await;
    session_manager.save_session(&session).await.map_err(|e| e.to_string())?;
    
    Ok(session)
}

/// Tauri command to get suggested filename for a session
#[tauri::command]
pub async fn get_suggested_filename(
    session_id: String,
    format: Option<ExportFormat>,
    service: State<'_, FileService>,
) -> Result<String, String> {
    let session_uuid = Uuid::parse_str(&session_id).map_err(|e| e.to_string())?;
    
    let session = {
        let session_manager = service.session_manager.lock().await;
        session_manager.load_session(session_uuid).await
            .map_err(|e| e.to_string())?
            .ok_or("Session not found".to_string())?
    };

    let filename = {
        let file_manager = service.file_manager.lock().await;
        file_manager.suggest_filename(&session, format.as_ref())
    };

    Ok(filename)
}

/// Tauri command to validate a file path
#[tauri::command]
pub async fn validate_file_path(
    file_path: PathBuf,
    service: State<'_, FileService>,
) -> Result<bool, String> {
    let file_manager = service.file_manager.lock().await;
    file_manager.validate_path(&file_path).await.map_err(|e| e.to_string())
}

/// Tauri command to list files in storage
#[tauri::command]
pub async fn list_storage_files(
    options: ListFilesOptions,
    service: State<'_, FileService>,
) -> Result<Vec<FileMetadata>, String> {
    let storage = service.storage.lock().await;
    let recursive = options.recursive.unwrap_or(false);
    let mut files = storage.list_files(&options.location, recursive).await
        .map_err(|e| e.to_string())?;

    // Apply filters
    if let Some(ext) = &options.filter_extension {
        files.retain(|f| {
            f.file_path.extension()
                .and_then(|e| e.to_str())
                .map(|e| e.eq_ignore_ascii_case(ext))
                .unwrap_or(false)
        });
    }

    // Apply sorting
    if let Some(sort_by) = &options.sort_by {
        match sort_by.as_str() {
            "name" => files.sort_by(|a, b| a.file_path.cmp(&b.file_path)),
            "date" => files.sort_by(|a, b| b.modified_at.cmp(&a.modified_at)),
            "size" => files.sort_by(|a, b| b.size_bytes.cmp(&a.size_bytes)),
            _ => {}
        }
    }

    // Apply limit
    if let Some(limit) = options.limit {
        files.truncate(limit);
    }

    Ok(files)
}

/// Tauri command to get storage statistics
#[tauri::command]
pub async fn get_storage_statistics(
    location: StorageLocation,
    service: State<'_, FileService>,
) -> Result<StorageStats, String> {
    let storage = service.storage.lock().await;
    let files = storage.list_files(&location, true).await.map_err(|e| e.to_string())?;

    let total_files = files.len();
    let total_size_bytes = files.iter().map(|f| f.size_bytes).sum();
    
    let mut files_by_type = std::collections::HashMap::new();
    for file in &files {
        let type_name = format!("{:?}", file.file_type);
        *files_by_type.entry(type_name).or_insert(0) += 1;
    }

    let oldest_file = files.iter().map(|f| f.modified_at).min();
    let newest_file = files.iter().map(|f| f.modified_at).max();

    Ok(StorageStats {
        total_files,
        total_size_bytes,
        files_by_type,
        oldest_file,
        newest_file,
    })
}

/// Tauri command to cleanup old files
#[tauri::command]
pub async fn cleanup_storage(
    location: StorageLocation,
    max_age_days: Option<u32>,
    max_files: Option<usize>,
    service: State<'_, FileService>,
) -> Result<usize, String> {
    let storage = service.storage.lock().await;
    storage.cleanup_old_files(&location, max_age_days, max_files).await
        .map_err(|e| e.to_string())
}

/// Tauri command to get default storage locations
#[tauri::command]
pub async fn get_default_storage_paths(
    service: State<'_, FileService>,
) -> Result<std::collections::HashMap<String, PathBuf>, String> {
    let storage = service.storage.lock().await;
    let mut paths = std::collections::HashMap::new();
    
    paths.insert("default".to_string(), storage.get_location_path(&StorageLocation::Default));
    paths.insert("sessions".to_string(), storage.get_location_path(&StorageLocation::Sessions));
    paths.insert("exports".to_string(), storage.get_location_path(&StorageLocation::Exports));
    paths.insert("backups".to_string(), storage.get_location_path(&StorageLocation::Backups));
    paths.insert("templates".to_string(), storage.get_location_path(&StorageLocation::Templates));
    
    Ok(paths)
}

/// Tauri command to update storage configuration
#[tauri::command]
pub async fn update_storage_config(
    config: StorageConfig,
    service: State<'_, FileService>,
) -> Result<(), String> {
    let mut storage = service.storage.lock().await;
    storage.update_config(config).map_err(|e| e.to_string())?;
    Ok(())
}

/// Tauri command to get current storage configuration
#[tauri::command]
pub async fn get_storage_config(
    service: State<'_, FileService>,
) -> Result<StorageConfig, String> {
    let storage = service.storage.lock().await;
    Ok(storage.get_config().clone())
}

/// Export file command names for registration
pub fn get_file_command_names() -> Vec<&'static str> {
    vec![
        "save_session_to_file",
        "export_session_content",
        "load_session_from_file",
        "get_suggested_filename",
        "validate_file_path",
        "list_storage_files",
        "get_storage_statistics",
        "cleanup_storage",
        "get_default_storage_paths",
        "update_storage_config",
        "get_storage_config",
    ]
}