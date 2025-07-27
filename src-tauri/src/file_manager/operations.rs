use anyhow::Result;
use serde::{Deserialize, Serialize};
use std::path::{Path, PathBuf};
use chrono::{DateTime, Utc};
use uuid::Uuid;
use crate::content::GeneratedContent;
use crate::session::Session;
use crate::export::{ExportFormat, ExportOptions, ExportManager};

/// File operation types
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum FileOperation {
    Save(SaveOperation),
    Export(ExportOperation),
    AutoSave(SaveOperation),
}

/// Save operation configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SaveOperation {
    pub session_id: Uuid,
    pub location: PathBuf,
    pub include_metadata: bool,
    pub backup_existing: bool,
    pub auto_timestamp: bool,
}

/// Export operation configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ExportOperation {
    pub session_id: Uuid,
    pub content_ids: Option<Vec<String>>, // None = export all content
    pub format: ExportFormat,
    pub destination: PathBuf,
    pub options: ExportOptions,
    pub open_after_export: bool,
}

/// File metadata for tracking operations
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FileMetadata {
    pub id: Uuid,
    pub session_id: Uuid,
    pub file_path: PathBuf,
    pub file_type: FileType,
    pub size_bytes: u64,
    pub created_at: DateTime<Utc>,
    pub modified_at: DateTime<Utc>,
    pub checksum: Option<String>,
    pub operation_type: FileOperationType,
}

/// Types of files managed by the system
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum FileType {
    SessionData,      // .json session files
    Export(ExportFormat), // Exported content files
    Backup,          // Backup files
    Template,        // Custom templates
    Attachment,      // User-uploaded files
}

/// Types of file operations for tracking
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum FileOperationType {
    Save,
    Export,
    AutoSave,
    Backup,
    Import,
}

/// Main file manager for handling all file operations
pub struct FileManager {
    export_manager: ExportManager,
    default_save_location: PathBuf,
    auto_backup_enabled: bool,
    max_backup_versions: usize,
}

impl FileManager {
    pub fn new(export_manager: ExportManager, save_location: PathBuf) -> Self {
        Self {
            export_manager,
            default_save_location: save_location,
            auto_backup_enabled: true,
            max_backup_versions: 5,
        }
    }

    /// Save a session to a file
    pub async fn save_session(
        &self,
        session: &Session,
        operation: &SaveOperation,
    ) -> Result<FileMetadata> {
        let file_path = if operation.auto_timestamp {
            self.add_timestamp_to_path(&operation.location)?
        } else {
            operation.location.clone()
        };

        // Create backup if requested and file exists
        if operation.backup_existing && file_path.exists() {
            self.create_backup(&file_path).await?;
        }

        // Prepare session data
        let session_data = if operation.include_metadata {
            serde_json::to_string_pretty(session)?
        } else {
            // Create a simplified version without internal metadata
            let simplified = self.create_simplified_session(session);
            serde_json::to_string_pretty(&simplified)?
        };

        // Ensure directory exists
        if let Some(parent) = file_path.parent() {
            tokio::fs::create_dir_all(parent).await?;
        }

        // Write file
        tokio::fs::write(&file_path, session_data).await?;

        // Calculate file size and checksum
        let metadata = tokio::fs::metadata(&file_path).await?;
        let checksum = self.calculate_checksum(&file_path).await?;

        Ok(FileMetadata {
            id: Uuid::new_v4(),
            session_id: session.id,
            file_path,
            file_type: FileType::SessionData,
            size_bytes: metadata.len(),
            created_at: Utc::now(),
            modified_at: Utc::now(),
            checksum: Some(checksum),
            operation_type: match operation {
                _ if matches!(session.name.as_str(), x if x.contains("autosave")) => FileOperationType::AutoSave,
                _ => FileOperationType::Save,
            },
        })
    }

    /// Export session content to various formats
    pub async fn export_content(
        &self,
        session: &Session,
        operation: &ExportOperation,
    ) -> Result<FileMetadata> {
        // Filter content if specific IDs provided
        let content_to_export = if let Some(content_ids) = &operation.content_ids {
            session.generated_content
                .iter()
                .filter(|c| content_ids.contains(&c.title)) // Using title as ID for now
                .cloned()
                .collect()
        } else {
            session.generated_content.clone()
        };

        // Ensure destination directory exists
        if let Some(parent) = operation.destination.parent() {
            tokio::fs::create_dir_all(parent).await?;
        }

        // Perform export using the export manager
        let mut export_options = operation.options.clone();
        export_options.format = operation.format.clone();
        
        let export_result = self.export_manager.export_content(
            &content_to_export,
            &export_options,
        ).await?;

        // Open file after export if requested
        if operation.open_after_export {
            self.open_file(&operation.destination).await?;
        }

        // Get file metadata
        let metadata = tokio::fs::metadata(&operation.destination).await?;
        let checksum = self.calculate_checksum(&operation.destination).await?;

        Ok(FileMetadata {
            id: Uuid::new_v4(),
            session_id: session.id,
            file_path: operation.destination.clone(),
            file_type: FileType::Export(operation.format.clone()),
            size_bytes: metadata.len(),
            created_at: Utc::now(),
            modified_at: Utc::now(),
            checksum: Some(checksum),
            operation_type: FileOperationType::Export,
        })
    }

    /// Load a session from a file
    pub async fn load_session(&self, file_path: &Path) -> Result<Session> {
        let content = tokio::fs::read_to_string(file_path).await?;
        let session: Session = serde_json::from_str(&content)?;
        Ok(session)
    }

    /// Get default save location for sessions
    pub fn get_default_save_location(&self) -> &Path {
        &self.default_save_location
    }

    /// Create a suggested filename for a session
    pub fn suggest_filename(&self, session: &Session, format: Option<&ExportFormat>) -> String {
        let safe_name = session.name
            .chars()
            .map(|c| if c.is_alphanumeric() || c == ' ' || c == '-' || c == '_' { c } else { '_' })
            .collect::<String>()
            .replace(' ', "_");

        let timestamp = session.created_at.format("%Y%m%d_%H%M");
        
        match format {
            Some(ExportFormat::Markdown) => format!("{}_{}.md", safe_name, timestamp),
            Some(ExportFormat::Html) => format!("{}_{}.html", safe_name, timestamp),
            Some(ExportFormat::Pdf) => format!("{}_{}.pdf", safe_name, timestamp),
            Some(ExportFormat::PowerPoint) => format!("{}_{}.pptx", safe_name, timestamp),
            Some(ExportFormat::Word) => format!("{}_{}.docx", safe_name, timestamp),
            #[cfg(feature = "quarto-integration")]
            Some(ExportFormat::QuartoHtml) => format!("{}_{}.html", safe_name, timestamp),
            #[cfg(feature = "quarto-integration")]
            Some(ExportFormat::QuartoPdf) => format!("{}_{}.pdf", safe_name, timestamp),
            #[cfg(feature = "quarto-integration")]
            Some(ExportFormat::QuartoPowerPoint) => format!("{}_{}.pptx", safe_name, timestamp),
            #[cfg(feature = "quarto-integration")]
            Some(ExportFormat::QuartoWord) => format!("{}_{}.docx", safe_name, timestamp),
            #[cfg(feature = "quarto-integration")]
            Some(ExportFormat::QuartoBook) => format!("{}_{}.html", safe_name, timestamp),
            #[cfg(feature = "quarto-integration")]
            Some(ExportFormat::QuartoWebsite) => format!("{}_{}.html", safe_name, timestamp),
            None => format!("{}_{}.json", safe_name, timestamp), // Session file
        }
    }

    /// Check if a file path is valid and writable
    pub async fn validate_path(&self, path: &Path) -> Result<bool> {
        // Check if parent directory exists or can be created
        if let Some(parent) = path.parent() {
            if !parent.exists() {
                tokio::fs::create_dir_all(parent).await?;
            }
        }

        // Check write permissions by creating a temporary file
        let temp_path = path.with_extension("tmp");
        match tokio::fs::write(&temp_path, b"test").await {
            Ok(_) => {
                // Clean up test file
                let _ = tokio::fs::remove_file(&temp_path).await;
                Ok(true)
            }
            Err(_) => Ok(false),
        }
    }

    /// Get file operation history for a session
    pub async fn get_file_history(&self, session_id: Uuid) -> Result<Vec<FileMetadata>> {
        // This would typically query a database or file system
        // For now, return empty vector as placeholder
        Ok(vec![])
    }

    /// Clean up old backup files
    pub async fn cleanup_backups(&self) -> Result<usize> {
        let mut cleaned_count = 0;
        
        if let Ok(entries) = tokio::fs::read_dir(&self.default_save_location).await {
            let mut entries = entries;
            while let Ok(Some(entry)) = entries.next_entry().await {
                let path = entry.path();
                if let Some(name) = path.file_name().and_then(|n| n.to_str()) {
                    if name.contains(".backup.") || name.contains(".bak") {
                        // Check if backup is old enough to clean up
                        if let Ok(metadata) = entry.metadata().await {
                            if let Ok(modified) = metadata.modified() {
                                let age = std::time::SystemTime::now()
                                    .duration_since(modified)
                                    .unwrap_or_default();
                                
                                // Clean up backups older than 30 days
                                if age.as_secs() > (30 * 24 * 60 * 60) {
                                    if tokio::fs::remove_file(&path).await.is_ok() {
                                        cleaned_count += 1;
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        
        Ok(cleaned_count)
    }

    // Private helper methods

    fn add_timestamp_to_path(&self, path: &Path) -> Result<PathBuf> {
        let timestamp = Utc::now().format("%Y%m%d_%H%M%S");
        
        if let Some(stem) = path.file_stem().and_then(|s| s.to_str()) {
            if let Some(ext) = path.extension().and_then(|e| e.to_str()) {
                let new_name = format!("{}_{}.{}", stem, timestamp, ext);
                Ok(path.with_file_name(new_name))
            } else {
                let new_name = format!("{}_{}", stem, timestamp);
                Ok(path.with_file_name(new_name))
            }
        } else {
            Ok(path.with_file_name(format!("file_{}", timestamp)))
        }
    }

    async fn create_backup(&self, file_path: &Path) -> Result<()> {
        if file_path.exists() {
            let backup_path = file_path.with_extension(
                format!("backup.{}.{}", 
                    Utc::now().format("%Y%m%d_%H%M%S"),
                    file_path.extension().and_then(|e| e.to_str()).unwrap_or("bak")
                )
            );
            tokio::fs::copy(file_path, backup_path).await?;
        }
        Ok(())
    }

    fn create_simplified_session(&self, session: &Session) -> serde_json::Value {
        serde_json::json!({
            "id": session.id,
            "name": session.name,
            "created_at": session.created_at,
            "updated_at": session.updated_at,
            "content_request": session.content_request,
            "generated_content": session.generated_content,
            "config": session.config
        })
    }

    async fn calculate_checksum(&self, file_path: &Path) -> Result<String> {
        use sha2::{Sha256, Digest};
        
        let content = tokio::fs::read(file_path).await?;
        let mut hasher = Sha256::new();
        hasher.update(&content);
        let result = hasher.finalize();
        Ok(format!("{:x}", result))
    }

    async fn open_file(&self, file_path: &Path) -> Result<()> {
        #[cfg(target_os = "windows")]
        {
            std::process::Command::new("cmd")
                .args(["/C", "start", "", file_path.to_str().unwrap_or("")])
                .spawn()?;
        }
        #[cfg(target_os = "macos")]
        {
            std::process::Command::new("open")
                .arg(file_path)
                .spawn()?;
        }
        #[cfg(target_os = "linux")]
        {
            std::process::Command::new("xdg-open")
                .arg(file_path)
                .spawn()?;
        }
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::TempDir;

    #[tokio::test]
    async fn test_suggest_filename() {
        let temp_dir = TempDir::new().unwrap();
        let export_manager = ExportManager::new();
        let file_manager = FileManager::new(export_manager, temp_dir.path().to_path_buf());
        
        let session = Session {
            id: Uuid::new_v4(),
            name: "Test Session!@#".to_string(),
            created_at: Utc::now(),
            updated_at: Utc::now(),
            content_request: None,
            generated_content: vec![],
            config: Default::default(),
        };

        let filename = file_manager.suggest_filename(&session, Some(&ExportFormat::Markdown));
        assert!(filename.contains("Test_Session___"));
        assert!(filename.ends_with(".md"));
    }

    #[tokio::test]
    async fn test_validate_path() {
        let temp_dir = TempDir::new().unwrap();
        let export_manager = ExportManager::new();
        let file_manager = FileManager::new(export_manager, temp_dir.path().to_path_buf());
        
        let valid_path = temp_dir.path().join("test.json");
        let result = file_manager.validate_path(&valid_path).await;
        assert!(result.is_ok());
        assert!(result.unwrap());
    }
}