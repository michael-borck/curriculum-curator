use anyhow::Result;
use serde::{Deserialize, Serialize};
use std::path::{Path, PathBuf};
use dirs;
use uuid::Uuid;
use chrono::{DateTime, Utc, Datelike};
use crate::file_manager::{FileMetadata, FileType, FileOperationType};

/// Storage configuration for file management
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StorageConfig {
    pub default_location: PathBuf,
    pub session_folder: String,
    pub export_folder: String,
    pub backup_folder: String,
    pub template_folder: String,
    pub auto_organize: bool,
    pub max_file_size_mb: usize,
    pub allowed_extensions: Vec<String>,
}

impl Default for StorageConfig {
    fn default() -> Self {
        let app_data_dir = dirs::config_dir()
            .unwrap_or_else(|| dirs::home_dir().unwrap_or_default())
            .join("curriculum-curator");

        Self {
            default_location: app_data_dir,
            session_folder: "sessions".to_string(),
            export_folder: "exports".to_string(),
            backup_folder: "backups".to_string(),
            template_folder: "templates".to_string(),
            auto_organize: true,
            max_file_size_mb: 100,
            allowed_extensions: vec![
                "json".to_string(),
                "md".to_string(),
                "html".to_string(),
                "pdf".to_string(),
                "pptx".to_string(),
                "qmd".to_string(),
                "txt".to_string(),
            ],
        }
    }
}

/// Different storage location types
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum StorageLocation {
    Default,
    Sessions,
    Exports,
    Backups,
    Templates,
    Custom(PathBuf),
}

/// File storage manager
pub struct FileStorage {
    config: StorageConfig,
}

impl FileStorage {
    pub fn new(config: StorageConfig) -> Result<Self> {
        let storage = Self { config };
        storage.ensure_directories_exist()?;
        Ok(storage)
    }

    pub fn new_default() -> Result<Self> {
        Self::new(StorageConfig::default())
    }

    /// Get the path for a specific storage location
    pub fn get_location_path(&self, location: &StorageLocation) -> PathBuf {
        match location {
            StorageLocation::Default => self.config.default_location.clone(),
            StorageLocation::Sessions => {
                self.config.default_location.join(&self.config.session_folder)
            }
            StorageLocation::Exports => {
                self.config.default_location.join(&self.config.export_folder)
            }
            StorageLocation::Backups => {
                self.config.default_location.join(&self.config.backup_folder)
            }
            StorageLocation::Templates => {
                self.config.default_location.join(&self.config.template_folder)
            }
            StorageLocation::Custom(path) => path.clone(),
        }
    }

    /// Generate a unique filename in a specific location
    pub fn generate_unique_filename(
        &self,
        location: &StorageLocation,
        base_name: &str,
        extension: &str,
    ) -> PathBuf {
        let location_path = self.get_location_path(location);
        let mut counter = 0;
        
        loop {
            let filename = if counter == 0 {
                format!("{}.{}", base_name, extension)
            } else {
                format!("{}_{}.{}", base_name, counter, extension)
            };
            
            let full_path = location_path.join(&filename);
            if !full_path.exists() {
                return full_path;
            }
            counter += 1;
        }
    }

    /// Get organized path for a session-related file
    pub fn get_session_file_path(
        &self,
        session_id: Uuid,
        filename: &str,
        auto_organize: Option<bool>,
    ) -> PathBuf {
        let should_organize = auto_organize.unwrap_or(self.config.auto_organize);
        
        if should_organize {
            // Organize by session ID
            let session_dir = self.get_location_path(&StorageLocation::Sessions)
                .join(session_id.to_string());
            session_dir.join(filename)
        } else {
            self.get_location_path(&StorageLocation::Sessions).join(filename)
        }
    }

    /// Get organized path for an export file
    pub fn get_export_file_path(
        &self,
        session_id: Option<Uuid>,
        filename: &str,
        format_folder: Option<&str>,
        auto_organize: Option<bool>,
    ) -> PathBuf {
        let should_organize = auto_organize.unwrap_or(self.config.auto_organize);
        let mut path = self.get_location_path(&StorageLocation::Exports);

        if should_organize {
            // Organize by format if provided
            if let Some(format) = format_folder {
                path = path.join(format);
            }
            
            // Organize by date (YYYY/MM)
            let now = Utc::now();
            path = path.join(format!("{:04}", now.year()))
                      .join(format!("{:02}", now.month()));

            // Optionally organize by session
            if let Some(session_id) = session_id {
                path = path.join(session_id.to_string());
            }
        }

        path.join(filename)
    }

    /// Check if a file extension is allowed
    pub fn is_extension_allowed(&self, extension: &str) -> bool {
        self.config.allowed_extensions.contains(&extension.to_lowercase())
    }

    /// Check if file size is within limits
    pub fn is_file_size_allowed(&self, size_bytes: u64) -> bool {
        let max_bytes = (self.config.max_file_size_mb * 1024 * 1024) as u64;
        size_bytes <= max_bytes
    }

    /// Create a backup filename
    pub fn create_backup_filename(&self, original_path: &Path) -> PathBuf {
        let timestamp = Utc::now().format("%Y%m%d_%H%M%S");
        let backup_location = self.get_location_path(&StorageLocation::Backups);
        
        if let Some(filename) = original_path.file_name().and_then(|n| n.to_str()) {
            let backup_name = format!("{}_{}.bak", filename, timestamp);
            backup_location.join(backup_name)
        } else {
            backup_location.join(format!("backup_{}.bak", timestamp))
        }
    }

    /// Get available disk space for storage location
    pub fn get_available_space(&self, location: &StorageLocation) -> Result<u64> {
        let path = self.get_location_path(location);
        
        // Use statvfs on Unix-like systems, GetDiskFreeSpaceEx on Windows
        #[cfg(unix)]
        {
            use std::os::unix::fs::MetadataExt;
            let metadata = std::fs::metadata(&path)?;
            // This is a simplified approach - in a real implementation,
            // you'd use statvfs or similar system call
            Ok(metadata.size())
        }
        
        #[cfg(windows)]
        {
            // On Windows, you'd use GetDiskFreeSpaceEx
            // For now, return a large number as placeholder
            Ok(u64::MAX)
        }
        
        #[cfg(not(any(unix, windows)))]
        {
            Ok(u64::MAX)
        }
    }

    /// List files in a storage location
    pub async fn list_files(
        &self,
        location: &StorageLocation,
        recursive: bool,
    ) -> Result<Vec<FileMetadata>> {
        let path = self.get_location_path(location);
        let mut files = Vec::new();
        
        if recursive {
            self.collect_files_recursive(&path, &mut files).await?;
        } else {
            self.collect_files_in_directory(&path, &mut files).await?;
        }
        
        Ok(files)
    }

    /// Clean up old files based on age or count
    pub async fn cleanup_old_files(
        &self,
        location: &StorageLocation,
        max_age_days: Option<u32>,
        max_files: Option<usize>,
    ) -> Result<usize> {
        let files = self.list_files(location, false).await?;
        let mut cleaned_count = 0;
        
        // Sort by modification time (oldest first)
        let mut sorted_files = files;
        sorted_files.sort_by_key(|f| f.modified_at);
        
        // Remove files based on age
        if let Some(max_age) = max_age_days {
            let cutoff_date = Utc::now() - chrono::Duration::days(max_age as i64);
            for file in &sorted_files {
                if file.modified_at < cutoff_date {
                    if tokio::fs::remove_file(&file.file_path).await.is_ok() {
                        cleaned_count += 1;
                    }
                }
            }
        }
        
        // Remove excess files based on count
        if let Some(max_count) = max_files {
            if sorted_files.len() > max_count {
                let files_to_remove = sorted_files.len() - max_count;
                for file in sorted_files.iter().take(files_to_remove) {
                    if tokio::fs::remove_file(&file.file_path).await.is_ok() {
                        cleaned_count += 1;
                    }
                }
            }
        }
        
        Ok(cleaned_count)
    }

    /// Update storage configuration
    pub fn update_config(&mut self, new_config: StorageConfig) -> Result<()> {
        self.config = new_config;
        self.ensure_directories_exist()?;
        Ok(())
    }

    /// Get current storage configuration
    pub fn get_config(&self) -> &StorageConfig {
        &self.config
    }

    // Private helper methods

    fn ensure_directories_exist(&self) -> Result<()> {
        let locations = [
            StorageLocation::Default,
            StorageLocation::Sessions,
            StorageLocation::Exports,
            StorageLocation::Backups,
            StorageLocation::Templates,
        ];

        for location in &locations {
            let path = self.get_location_path(location);
            std::fs::create_dir_all(&path)?;
        }

        Ok(())
    }

    fn collect_files_recursive<'a>(
        &'a self,
        dir_path: &'a Path,
        files: &'a mut Vec<FileMetadata>,
    ) -> std::pin::Pin<Box<dyn std::future::Future<Output = Result<()>> + 'a + Send>> {
        Box::pin(async move {
            if let Ok(mut entries) = tokio::fs::read_dir(dir_path).await {
                while let Ok(Some(entry)) = entries.next_entry().await {
                    let path = entry.path();
                    if path.is_dir() {
                        self.collect_files_recursive(&path, files).await?;
                    } else {
                        if let Some(metadata) = self.create_file_metadata(&path).await {
                            files.push(metadata);
                        }
                    }
                }
            }
            Ok(())
        })
    }

    async fn collect_files_in_directory(
        &self,
        dir_path: &Path,
        files: &mut Vec<FileMetadata>,
    ) -> Result<()> {
        if let Ok(mut entries) = tokio::fs::read_dir(dir_path).await {
            while let Ok(Some(entry)) = entries.next_entry().await {
                let path = entry.path();
                if path.is_file() {
                    if let Some(metadata) = self.create_file_metadata(&path).await {
                        files.push(metadata);
                    }
                }
            }
        }
        Ok(())
    }

    async fn create_file_metadata(&self, path: &Path) -> Option<FileMetadata> {
        if let Ok(metadata) = tokio::fs::metadata(path).await {
            if let Ok(modified) = metadata.modified() {
                let modified_dt = DateTime::<Utc>::from(modified);
                let file_type = self.determine_file_type(path);
                
                return Some(FileMetadata {
                    id: Uuid::new_v4(),
                    session_id: Uuid::nil(), // Would need to parse from filename or content
                    file_path: path.to_path_buf(),
                    file_type,
                    size_bytes: metadata.len(),
                    created_at: modified_dt, // Approximation
                    modified_at: modified_dt,
                    checksum: None, // Would calculate if needed
                    operation_type: FileOperationType::Save,
                });
            }
        }
        None
    }

    fn determine_file_type(&self, path: &Path) -> FileType {
        if let Some(ext) = path.extension().and_then(|e| e.to_str()) {
            match ext.to_lowercase().as_str() {
                "json" => FileType::SessionData,
                "md" => FileType::Export(crate::export::ExportFormat::Markdown),
                "html" => FileType::Export(crate::export::ExportFormat::Html),
                "pdf" => FileType::Export(crate::export::ExportFormat::Pdf),
                "pptx" => FileType::Export(crate::export::ExportFormat::PowerPoint),
                "docx" => FileType::Export(crate::export::ExportFormat::Word),
                #[cfg(feature = "quarto-integration")]
                "qmd" => FileType::Export(crate::export::ExportFormat::QuartoHtml),
                "bak" => FileType::Backup,
                _ => FileType::Attachment,
            }
        } else {
            FileType::Attachment
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::TempDir;

    #[test]
    fn test_storage_config_default() {
        let config = StorageConfig::default();
        assert!(config.default_location.to_string_lossy().contains("curriculum-curator"));
        assert_eq!(config.session_folder, "sessions");
        assert_eq!(config.export_folder, "exports");
        assert!(config.auto_organize);
    }

    #[test]
    fn test_get_location_path() {
        let temp_dir = TempDir::new().unwrap();
        let mut config = StorageConfig::default();
        config.default_location = temp_dir.path().to_path_buf();
        
        let storage = FileStorage::new(config).unwrap();
        
        let sessions_path = storage.get_location_path(&StorageLocation::Sessions);
        assert!(sessions_path.to_string_lossy().contains("sessions"));
        
        let exports_path = storage.get_location_path(&StorageLocation::Exports);
        assert!(exports_path.to_string_lossy().contains("exports"));
    }

    #[test]
    fn test_generate_unique_filename() {
        let temp_dir = TempDir::new().unwrap();
        let mut config = StorageConfig::default();
        config.default_location = temp_dir.path().to_path_buf();
        
        let storage = FileStorage::new(config).unwrap();
        
        let filename1 = storage.generate_unique_filename(
            &StorageLocation::Sessions,
            "test",
            "json"
        );
        
        let filename2 = storage.generate_unique_filename(
            &StorageLocation::Sessions,
            "test",
            "json"
        );
        
        assert_ne!(filename1, filename2);
        assert!(filename1.to_string_lossy().contains("test.json"));
    }

    #[test]
    fn test_is_extension_allowed() {
        let storage = FileStorage::new_default().unwrap();
        
        assert!(storage.is_extension_allowed("json"));
        assert!(storage.is_extension_allowed("md"));
        assert!(storage.is_extension_allowed("JSON")); // Case insensitive
        assert!(!storage.is_extension_allowed("exe"));
        assert!(!storage.is_extension_allowed("bat"));
    }
}