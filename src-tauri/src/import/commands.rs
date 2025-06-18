use super::*;
use crate::session::SessionManager;
use crate::backup::BackupService;
use tauri::State;
use std::sync::Arc;
use tokio::sync::Mutex;
use std::path::PathBuf;
use anyhow::Result;

#[tauri::command]
pub async fn get_import_config(
    import_service: State<'_, Arc<Mutex<ImportService>>>,
) -> Result<ImportConfig, String> {
    let service = import_service.lock().await;
    Ok(service.get_config().await)
}

#[tauri::command]
pub async fn update_import_config(
    import_service: State<'_, Arc<Mutex<ImportService>>>,
    config: ImportConfig,
) -> Result<(), String> {
    let service = import_service.lock().await;
    service.update_config(config).await
        .map_err(|e| e.to_string())
}

#[tauri::command]
pub async fn preview_import_file(
    import_service: State<'_, Arc<Mutex<ImportService>>>,
    file_path: String,
) -> Result<ImportPreview, String> {
    let service = import_service.lock().await;
    let path = PathBuf::from(file_path);
    
    service.preview_import(&path).await
        .map_err(|e| e.to_string())
}

#[tauri::command]
pub async fn import_file(
    import_service: State<'_, Arc<Mutex<ImportService>>>,
    file_path: String,
    settings: Option<ImportSettings>,
) -> Result<ImportResult, String> {
    let service = import_service.lock().await;
    let path = PathBuf::from(file_path);
    
    service.import_file(&path, settings, None).await
        .map_err(|e| e.to_string())
}

#[tauri::command]
pub async fn import_file_with_progress(
    import_service: State<'_, Arc<Mutex<ImportService>>>,
    file_path: String,
    settings: Option<ImportSettings>,
    window: tauri::Window,
) -> Result<ImportResult, String> {
    let service = import_service.lock().await;
    let path = PathBuf::from(file_path);
    
    // Create progress callback that emits events to frontend
    let progress_callback = Box::new(move |progress: ImportProgress| {
        let _ = window.emit("import-progress", &progress);
    });
    
    service.import_file(&path, settings, Some(progress_callback)).await
        .map_err(|e| e.to_string())
}

#[tauri::command]
pub async fn get_supported_file_types() -> Result<Vec<SupportedFileTypeInfo>, String> {
    Ok(vec![
        SupportedFileTypeInfo {
            file_type: SupportedFileType::PowerPoint,
            display_name: "PowerPoint Presentation".to_string(),
            extensions: vec!["pptx".to_string()],
            icon: "📊".to_string(),
            description: "Import slides and speaker notes from PowerPoint presentations".to_string(),
        },
        SupportedFileTypeInfo {
            file_type: SupportedFileType::Word,
            display_name: "Word Document".to_string(),
            extensions: vec!["docx".to_string()],
            icon: "📝".to_string(),
            description: "Import content from Word documents, including lesson plans and worksheets".to_string(),
        },
    ])
}

#[tauri::command]
pub async fn validate_import_file(
    file_path: String,
) -> Result<FileValidationResult, String> {
    let path = PathBuf::from(&file_path);
    
    // Check if file exists
    if !path.exists() {
        return Ok(FileValidationResult {
            is_valid: false,
            error_message: Some("File does not exist".to_string()),
            file_info: None,
        });
    }
    
    // Check if it's a file
    if !path.is_file() {
        return Ok(FileValidationResult {
            is_valid: false,
            error_message: Some("Path is not a file".to_string()),
            file_info: None,
        });
    }
    
    // Check file extension
    let extension = path.extension()
        .and_then(|ext| ext.to_str())
        .unwrap_or("");
    
    let file_type = match SupportedFileType::from_extension(extension) {
        Some(ft) => ft,
        None => {
            return Ok(FileValidationResult {
                is_valid: false,
                error_message: Some(format!("Unsupported file type: .{}. Supported types: .pptx, .docx", extension)),
                file_info: None,
            });
        }
    };
    
    // Get file metadata
    let metadata = std::fs::metadata(&path)
        .map_err(|e| format!("Failed to read file metadata: {}", e))?;
    
    let file_info = BasicFileInfo {
        filename: path.file_name()
            .and_then(|name| name.to_str())
            .unwrap_or("unknown")
            .to_string(),
        file_size: metadata.len(),
        file_type,
        last_modified: metadata.modified().ok()
            .map(|time| chrono::DateTime::<chrono::Utc>::from(time)),
    };
    
    // Check file size (50MB limit)
    const MAX_FILE_SIZE: u64 = 50 * 1024 * 1024;
    if metadata.len() > MAX_FILE_SIZE {
        return Ok(FileValidationResult {
            is_valid: false,
            error_message: Some(format!(
                "File size ({} MB) exceeds maximum allowed size (50 MB)",
                metadata.len() / (1024 * 1024)
            )),
            file_info: Some(file_info),
        });
    }
    
    Ok(FileValidationResult {
        is_valid: true,
        error_message: None,
        file_info: Some(file_info),
    })
}

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct SupportedFileTypeInfo {
    pub file_type: SupportedFileType,
    pub display_name: String,
    pub extensions: Vec<String>,
    pub icon: String,
    pub description: String,
}

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct FileValidationResult {
    pub is_valid: bool,
    pub error_message: Option<String>,
    pub file_info: Option<BasicFileInfo>,
}

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct BasicFileInfo {
    pub filename: String,
    pub file_size: u64,
    pub file_type: SupportedFileType,
    pub last_modified: Option<chrono::DateTime<chrono::Utc>>,
}