use serde::{Deserialize, Serialize};
use std::path::PathBuf;
use chrono::{DateTime, Utc};
use std::collections::HashMap;

pub mod service;
pub mod commands;
pub mod formats;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DataExportConfig {
    pub default_format: ExportFormat,
    pub compression_level: u32,
    pub include_metadata: bool,
    pub include_generated_files: bool,
    pub include_backups: bool,
    pub max_archive_size_mb: u64,
    pub encrypt_exports: bool,
    pub encryption_password: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum ExportFormat {
    Archive(ArchiveFormat),
    Database(DatabaseFormat),
    Portable(PortableFormat),
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum ArchiveFormat {
    Zip,
    Tar,
    TarGz,
    SevenZip,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum DatabaseFormat {
    SqliteBackup,
    JsonExport,
    CsvExport,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum PortableFormat {
    CurriculumPack,  // Custom format for cross-platform sharing
    EducatorBundle,  // Educator-friendly format with documentation
    MinimalExport,   // Lightweight format without media
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ExportRequest {
    pub format: ExportFormat,
    pub sessions: ExportSessionFilter,
    pub content_types: Vec<String>,
    pub include_attachments: bool,
    pub include_history: bool,
    pub output_path: PathBuf,
    pub filename: Option<String>,
    pub options: ExportOptions,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum ExportSessionFilter {
    All,
    SelectedSessions(Vec<String>),
    DateRange { start: DateTime<Utc>, end: DateTime<Utc> },
    RecentSessions(u32),
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ExportOptions {
    pub compress: bool,
    pub compression_level: Option<u32>,
    pub encrypt: bool,
    pub password: Option<String>,
    pub split_large_files: bool,
    pub max_file_size_mb: Option<u64>,
    pub include_thumbnails: bool,
    pub generate_index: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ExportResult {
    pub success: bool,
    pub export_id: String,
    pub output_path: PathBuf,
    pub file_size: u64,
    pub sessions_exported: u32,
    pub content_items_exported: u32,
    pub processing_time_ms: u64,
    pub warnings: Vec<String>,
    pub errors: Vec<String>,
    pub manifest: ExportManifest,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ExportManifest {
    pub export_id: String,
    pub created_at: DateTime<Utc>,
    pub format: ExportFormat,
    pub source_info: SourceInfo,
    pub content_summary: ContentSummary,
    pub file_structure: Vec<FileEntry>,
    pub metadata: HashMap<String, serde_json::Value>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SourceInfo {
    pub application_version: String,
    pub database_version: String,
    pub export_version: String,
    pub platform: String,
    pub total_sessions: u32,
    pub export_timestamp: DateTime<Utc>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ContentSummary {
    pub sessions: Vec<SessionSummary>,
    pub content_types: HashMap<String, u32>,
    pub total_files: u32,
    pub total_size_bytes: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SessionSummary {
    pub id: String,
    pub name: String,
    pub created_at: DateTime<Utc>,
    pub content_count: u32,
    pub content_types: Vec<String>,
    pub size_bytes: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FileEntry {
    pub path: String,
    pub file_type: FileType,
    pub size_bytes: u64,
    pub checksum: Option<String>,
    pub created_at: DateTime<Utc>,
    pub metadata: HashMap<String, serde_json::Value>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum FileType {
    SessionData,
    ContentFile,
    Attachment,
    Metadata,
    Index,
    Backup,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ExportProgress {
    pub current_step: ExportStep,
    pub progress_percentage: f32,
    pub current_item: String,
    pub items_processed: u32,
    pub total_items: u32,
    pub estimated_time_remaining: Option<u32>,
    pub current_file_size: u64,
    pub total_size_estimate: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum ExportStep {
    Initializing,
    CollectingSessions,
    ProcessingContent,
    CreatingArchive,
    CompressingFiles,
    GeneratingManifest,
    Finalizing,
    Complete,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SharingOptions {
    pub method: SharingMethod,
    pub recipients: Vec<String>,
    pub message: Option<String>,
    pub expiration: Option<DateTime<Utc>>,
    pub password_protect: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum SharingMethod {
    Email { smtp_config: SmtpConfig },
    CloudStorage { provider: CloudProvider, config: CloudConfig },
    WebLink { temporary: bool, duration_hours: Option<u32> },
    FileTransfer { service: String, config: HashMap<String, String> },
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SmtpConfig {
    pub server: String,
    pub port: u16,
    pub username: String,
    pub password: String,
    pub use_tls: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum CloudProvider {
    GoogleDrive,
    Dropbox,
    OneDrive,
    Box,
    Custom(String),
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CloudConfig {
    pub api_key: String,
    pub folder_path: Option<String>,
    pub public_sharing: bool,
}

impl Default for DataExportConfig {
    fn default() -> Self {
        Self {
            default_format: ExportFormat::Archive(ArchiveFormat::Zip),
            compression_level: 6,
            include_metadata: true,
            include_generated_files: true,
            include_backups: false,
            max_archive_size_mb: 500,
            encrypt_exports: false,
            encryption_password: None,
        }
    }
}

impl Default for ExportOptions {
    fn default() -> Self {
        Self {
            compress: true,
            compression_level: Some(6),
            encrypt: false,
            password: None,
            split_large_files: true,
            max_file_size_mb: Some(100),
            include_thumbnails: true,
            generate_index: true,
        }
    }
}

impl ExportFormat {
    pub fn extension(&self) -> &'static str {
        match self {
            ExportFormat::Archive(ArchiveFormat::Zip) => "zip",
            ExportFormat::Archive(ArchiveFormat::Tar) => "tar",
            ExportFormat::Archive(ArchiveFormat::TarGz) => "tar.gz",
            ExportFormat::Archive(ArchiveFormat::SevenZip) => "7z",
            ExportFormat::Database(DatabaseFormat::SqliteBackup) => "db",
            ExportFormat::Database(DatabaseFormat::JsonExport) => "json",
            ExportFormat::Database(DatabaseFormat::CsvExport) => "csv",
            ExportFormat::Portable(PortableFormat::CurriculumPack) => "ccpack",
            ExportFormat::Portable(PortableFormat::EducatorBundle) => "edubundle",
            ExportFormat::Portable(PortableFormat::MinimalExport) => "ccmin",
        }
    }

    pub fn display_name(&self) -> &'static str {
        match self {
            ExportFormat::Archive(ArchiveFormat::Zip) => "ZIP Archive",
            ExportFormat::Archive(ArchiveFormat::Tar) => "TAR Archive",
            ExportFormat::Archive(ArchiveFormat::TarGz) => "TAR.GZ Archive",
            ExportFormat::Archive(ArchiveFormat::SevenZip) => "7-Zip Archive",
            ExportFormat::Database(DatabaseFormat::SqliteBackup) => "SQLite Database Backup",
            ExportFormat::Database(DatabaseFormat::JsonExport) => "JSON Data Export",
            ExportFormat::Database(DatabaseFormat::CsvExport) => "CSV Data Export",
            ExportFormat::Portable(PortableFormat::CurriculumPack) => "Curriculum Pack",
            ExportFormat::Portable(PortableFormat::EducatorBundle) => "Educator Bundle",
            ExportFormat::Portable(PortableFormat::MinimalExport) => "Minimal Export",
        }
    }

    pub fn description(&self) -> &'static str {
        match self {
            ExportFormat::Archive(ArchiveFormat::Zip) => "Standard ZIP archive with all content and metadata",
            ExportFormat::Archive(ArchiveFormat::Tar) => "TAR archive for Unix-like systems",
            ExportFormat::Archive(ArchiveFormat::TarGz) => "Compressed TAR archive for efficient storage",
            ExportFormat::Archive(ArchiveFormat::SevenZip) => "High-compression 7-Zip archive",
            ExportFormat::Database(DatabaseFormat::SqliteBackup) => "Complete database backup for restoration",
            ExportFormat::Database(DatabaseFormat::JsonExport) => "Human-readable JSON format for data analysis",
            ExportFormat::Database(DatabaseFormat::CsvExport) => "Spreadsheet-compatible CSV format",
            ExportFormat::Portable(PortableFormat::CurriculumPack) => "Self-contained package for sharing curricula",
            ExportFormat::Portable(PortableFormat::EducatorBundle) => "Educator-friendly bundle with documentation",
            ExportFormat::Portable(PortableFormat::MinimalExport) => "Lightweight export without media files",
        }
    }
}

impl ExportStep {
    pub fn display_name(&self) -> &'static str {
        match self {
            ExportStep::Initializing => "Initializing export",
            ExportStep::CollectingSessions => "Collecting session data",
            ExportStep::ProcessingContent => "Processing content files",
            ExportStep::CreatingArchive => "Creating archive",
            ExportStep::CompressingFiles => "Compressing files",
            ExportStep::GeneratingManifest => "Generating manifest",
            ExportStep::Finalizing => "Finalizing export",
            ExportStep::Complete => "Export complete",
        }
    }

    pub fn progress_weight(&self) -> f32 {
        match self {
            ExportStep::Initializing => 0.05,
            ExportStep::CollectingSessions => 0.15,
            ExportStep::ProcessingContent => 0.30,
            ExportStep::CreatingArchive => 0.25,
            ExportStep::CompressingFiles => 0.15,
            ExportStep::GeneratingManifest => 0.05,
            ExportStep::Finalizing => 0.04,
            ExportStep::Complete => 0.01,
        }
    }
}