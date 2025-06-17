use serde::{Deserialize, Serialize};
use std::path::PathBuf;
use chrono::{DateTime, Utc};

pub mod service;
pub mod scheduler;
pub mod commands;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BackupConfig {
    pub enabled: bool,
    pub auto_backup_interval: BackupInterval,
    pub backup_on_session_close: bool,
    pub backup_on_content_generation: bool,
    pub max_backups_per_session: u32,
    pub max_total_backups: u32,
    pub compress_backups: bool,
    pub backup_location: Option<PathBuf>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum BackupInterval {
    Never,
    EverySession,
    Every5Minutes,
    Every15Minutes,
    Every30Minutes,
    Hourly,
    Daily,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BackupMetadata {
    pub id: String,
    pub session_id: String,
    pub session_name: String,
    pub created_at: DateTime<Utc>,
    pub backup_type: BackupType,
    pub file_path: PathBuf,
    pub file_size: u64,
    pub checksum: String,
    pub content_count: u32,
    pub auto_generated: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum BackupType {
    Automatic,
    Manual,
    OnSessionClose,
    OnContentGeneration,
    BeforeImport,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BackupListItem {
    pub id: String,
    pub session_id: String,
    pub session_name: String,
    pub created_at: DateTime<Utc>,
    pub backup_type: BackupType,
    pub file_size: u64,
    pub content_count: u32,
    pub auto_generated: bool,
    pub is_recoverable: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BackupFilter {
    pub session_id: Option<String>,
    pub backup_type: Option<BackupType>,
    pub start_date: Option<DateTime<Utc>>,
    pub end_date: Option<DateTime<Utc>>,
    pub auto_generated_only: Option<bool>,
    pub limit: Option<u32>,
    pub offset: Option<u32>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BackupStatistics {
    pub total_backups: u32,
    pub total_size: u64,
    pub automatic_backups: u32,
    pub manual_backups: u32,
    pub sessions_with_backups: u32,
    pub oldest_backup: Option<DateTime<Utc>>,
    pub newest_backup: Option<DateTime<Utc>>,
    pub average_backup_size: u64,
}

impl Default for BackupConfig {
    fn default() -> Self {
        Self {
            enabled: true,
            auto_backup_interval: BackupInterval::Every15Minutes,
            backup_on_session_close: true,
            backup_on_content_generation: true,
            max_backups_per_session: 10,
            max_total_backups: 100,
            compress_backups: true,
            backup_location: None, // Will use default storage location
        }
    }
}

impl BackupInterval {
    pub fn to_seconds(&self) -> Option<u64> {
        match self {
            BackupInterval::Never => None,
            BackupInterval::EverySession => None, // Handled separately
            BackupInterval::Every5Minutes => Some(5 * 60),
            BackupInterval::Every15Minutes => Some(15 * 60),
            BackupInterval::Every30Minutes => Some(30 * 60),
            BackupInterval::Hourly => Some(60 * 60),
            BackupInterval::Daily => Some(24 * 60 * 60),
        }
    }

    pub fn display_name(&self) -> &'static str {
        match self {
            BackupInterval::Never => "Never",
            BackupInterval::EverySession => "Every Session",
            BackupInterval::Every5Minutes => "Every 5 Minutes",
            BackupInterval::Every15Minutes => "Every 15 Minutes",
            BackupInterval::Every30Minutes => "Every 30 Minutes",
            BackupInterval::Hourly => "Hourly",
            BackupInterval::Daily => "Daily",
        }
    }
}

impl BackupType {
    pub fn display_name(&self) -> &'static str {
        match self {
            BackupType::Automatic => "Automatic",
            BackupType::Manual => "Manual",
            BackupType::OnSessionClose => "Session Close",
            BackupType::OnContentGeneration => "Content Generation",
            BackupType::BeforeImport => "Before Import",
        }
    }

    pub fn icon(&self) -> &'static str {
        match self {
            BackupType::Automatic => "🔄",
            BackupType::Manual => "💾",
            BackupType::OnSessionClose => "📤",
            BackupType::OnContentGeneration => "✨",
            BackupType::BeforeImport => "📥",
        }
    }
}