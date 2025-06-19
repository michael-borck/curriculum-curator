use super::{BackupConfig, BackupMetadata, BackupType, BackupListItem, BackupFilter, BackupStatistics};
use crate::session::{SessionManager, Session};
use crate::content::GeneratedContent;
use crate::file_manager::FileService;
use anyhow::{Result, Context};
use serde_json;
use std::collections::HashMap;
use std::fs;
use std::path::{Path, PathBuf};
use std::sync::Arc;
use tokio::sync::Mutex;
use chrono::{DateTime, Utc};
use uuid::Uuid;
use sha2::{Sha256, Digest};
use std::io::Read;

pub struct BackupService {
    session_manager: Arc<Mutex<SessionManager>>,
    file_service: Arc<Mutex<FileService>>,
    config: Arc<Mutex<BackupConfig>>,
    backup_metadata: Arc<Mutex<HashMap<String, BackupMetadata>>>,
}

impl BackupService {
    pub fn new(
        session_manager: Arc<Mutex<SessionManager>>,
        file_service: Arc<Mutex<FileService>>,
    ) -> Self {
        Self {
            session_manager,
            file_service,
            config: Arc::new(Mutex::new(BackupConfig::default())),
            backup_metadata: Arc::new(Mutex::new(HashMap::new())),
        }
    }

    pub async fn initialize(&self) -> Result<()> {
        // Load existing backup metadata
        self.load_backup_metadata().await?;
        
        // Clean up orphaned backups
        self.cleanup_orphaned_backups().await?;
        
        Ok(())
    }

    async fn load_backup_metadata(&self) -> Result<()> {
        let file_service = self.file_service.lock().await;
        let backup_dir = file_service.get_storage_paths().await?.backups;
        let metadata_file = backup_dir.join("metadata.json");

        if metadata_file.exists() {
            let content = fs::read_to_string(&metadata_file)
                .context("Failed to read backup metadata")?;
            
            let metadata: HashMap<String, BackupMetadata> = serde_json::from_str(&content)
                .context("Failed to parse backup metadata")?;
            
            *self.backup_metadata.lock().await = metadata;
        }

        Ok(())
    }

    async fn save_backup_metadata(&self) -> Result<()> {
        let file_service = self.file_service.lock().await;
        let backup_dir = file_service.get_storage_paths().await?.backups;
        
        // Ensure backup directory exists
        fs::create_dir_all(&backup_dir)
            .context("Failed to create backup directory")?;

        let metadata_file = backup_dir.join("metadata.json");
        let metadata = self.backup_metadata.lock().await;
        
        let content = serde_json::to_string_pretty(&*metadata)
            .context("Failed to serialize backup metadata")?;
        
        fs::write(&metadata_file, content)
            .context("Failed to write backup metadata")?;

        Ok(())
    }

    pub async fn create_backup(
        &self,
        session_id: &str,
        backup_type: BackupType,
    ) -> Result<String> {
        let config = self.config.lock().await;
        if !config.enabled {
            return Err(anyhow::anyhow!("Backup is disabled"));
        }

        // Load session data
        let session_manager = self.session_manager.lock().await;
        let session_uuid = Uuid::parse_str(session_id).context("Invalid session ID format")?;
        let session = session_manager.load_session(session_uuid).await
            .context("Failed to load session for backup")?;

        // Generate backup ID and paths
        let backup_id = Uuid::new_v4().to_string();
        let file_service = self.file_service.lock().await;
        let backup_dir = file_service.get_storage_paths().await?.backups;
        
        let backup_filename = format!(
            "{}_{}_backup_{}.json",
            session.as_ref().map(|s| s.name.replace(" ", "_")).unwrap_or_else(|| "unknown".to_string()),
            session_id,
            backup_id
        );
        let backup_path = backup_dir.join(&backup_filename);

        // Ensure backup directory exists
        fs::create_dir_all(&backup_dir)
            .context("Failed to create backup directory")?;

        // Create backup data structure
        let backup_data = serde_json::json!({
            "backup_id": backup_id,
            "session_id": session_id,
            "session": session,
            "content": session_manager.get_session_content(session_uuid).await?,
            "created_at": Utc::now(),
            "backup_type": &backup_type,
            "version": "1.0"
        });

        // Write backup file
        let backup_content = if config.compress_backups {
            // TODO: Implement compression
            serde_json::to_string_pretty(&backup_data)?
        } else {
            serde_json::to_string_pretty(&backup_data)?
        };

        fs::write(&backup_path, &backup_content)
            .context("Failed to write backup file")?;

        // Calculate file size and checksum
        let file_size = backup_content.len() as u64;
        let checksum = self.calculate_checksum(&backup_path).await?;

        // Create metadata
        let metadata = BackupMetadata {
            id: backup_id.clone(),
            session_id: session_id.to_string(),
            session_name: session.as_ref().map(|s| s.name.clone()).unwrap_or_else(|| "Unknown Session".to_string()),
            created_at: Utc::now(),
            backup_type: backup_type.clone(),
            file_path: backup_path,
            file_size,
            checksum,
            content_count: session_manager.get_session_content(session_uuid).await?.len() as u32,
            auto_generated: matches!(&backup_type, BackupType::Automatic | BackupType::OnSessionClose | BackupType::OnContentGeneration),
        };

        // Store metadata
        self.backup_metadata.lock().await.insert(backup_id.clone(), metadata);
        self.save_backup_metadata().await?;

        // Cleanup old backups if needed
        self.cleanup_old_backups(session_id, &config).await?;

        Ok(backup_id)
    }

    pub async fn restore_backup(&self, backup_id: &str) -> Result<String> {
        let metadata_guard = self.backup_metadata.lock().await;
        let metadata = metadata_guard.get(backup_id)
            .ok_or_else(|| anyhow::anyhow!("Backup not found"))?;

        if !metadata.file_path.exists() {
            return Err(anyhow::anyhow!("Backup file does not exist"));
        }

        // Verify backup integrity
        let current_checksum = self.calculate_checksum(&metadata.file_path).await?;
        if current_checksum != metadata.checksum {
            return Err(anyhow::anyhow!("Backup file is corrupted"));
        }

        // Read and parse backup
        let backup_content = fs::read_to_string(&metadata.file_path)
            .context("Failed to read backup file")?;
        
        let backup_data: serde_json::Value = serde_json::from_str(&backup_content)
            .context("Failed to parse backup file")?;

        // Extract session data
        let session: Session = serde_json::from_value(backup_data["session"].clone())
            .context("Failed to parse session from backup")?;
        let content: Vec<GeneratedContent> = serde_json::from_value(backup_data["content"].clone())
            .context("Failed to parse content from backup")?;

        // Create new session from backup
        let session_manager = self.session_manager.lock().await;
        let new_session_id = session_manager.create_session_from_backup(session, content).await
            .context("Failed to restore session from backup")?;

        Ok(new_session_id.to_string())
    }

    pub async fn list_backups(&self, filter: Option<BackupFilter>) -> Result<Vec<BackupListItem>> {
        let metadata_guard = self.backup_metadata.lock().await;
        let mut backups: Vec<BackupListItem> = metadata_guard
            .values()
            .map(|metadata| BackupListItem {
                id: metadata.id.clone(),
                session_id: metadata.session_id.clone(),
                session_name: metadata.session_name.clone(),
                created_at: metadata.created_at,
                backup_type: metadata.backup_type.clone(),
                file_size: metadata.file_size,
                content_count: metadata.content_count,
                auto_generated: metadata.auto_generated,
                is_recoverable: metadata.file_path.exists(), // Simplified for now - full integrity check would require async context
            })
            .collect();

        // Apply filters and pagination
        if let Some(filter) = filter {
            if let Some(session_id) = &filter.session_id {
                backups.retain(|b| &b.session_id == session_id);
            }
            
            if let Some(backup_type) = &filter.backup_type {
                backups.retain(|b| std::mem::discriminant(&b.backup_type) == std::mem::discriminant(backup_type));
            }
            
            if let Some(start_date) = filter.start_date {
                backups.retain(|b| b.created_at >= start_date);
            }
            
            if let Some(end_date) = filter.end_date {
                backups.retain(|b| b.created_at <= end_date);
            }
            
            if let Some(auto_only) = filter.auto_generated_only {
                backups.retain(|b| b.auto_generated == auto_only);
            }

            // Sort by creation date (newest first)
            backups.sort_by(|a, b| b.created_at.cmp(&a.created_at));

            // Apply pagination
            let offset = filter.offset.unwrap_or(0) as usize;
            let limit = filter.limit.map(|l| l as usize);
            
            if let Some(limit) = limit {
                backups = backups.into_iter().skip(offset).take(limit).collect();
            } else if offset > 0 {
                backups = backups.into_iter().skip(offset).collect();
            }
        } else {
            // Sort by creation date (newest first) even when no filter
            backups.sort_by(|a, b| b.created_at.cmp(&a.created_at));
        }

        Ok(backups)
    }

    pub async fn delete_backup(&self, backup_id: &str) -> Result<()> {
        let mut metadata_guard = self.backup_metadata.lock().await;
        let metadata = metadata_guard.get(backup_id)
            .ok_or_else(|| anyhow::anyhow!("Backup not found"))?
            .clone();

        // Delete backup file
        if metadata.file_path.exists() {
            fs::remove_file(&metadata.file_path)
                .context("Failed to delete backup file")?;
        }

        // Remove from metadata
        metadata_guard.remove(backup_id);
        drop(metadata_guard);

        self.save_backup_metadata().await?;

        Ok(())
    }

    pub async fn get_backup_statistics(&self) -> Result<BackupStatistics> {
        let metadata_guard = self.backup_metadata.lock().await;
        let backups: Vec<&BackupMetadata> = metadata_guard.values().collect();

        let total_backups = backups.len() as u32;
        let total_size = backups.iter().map(|b| b.file_size).sum();
        let automatic_backups = backups.iter().filter(|b| b.auto_generated).count() as u32;
        let manual_backups = total_backups - automatic_backups;
        
        let mut unique_sessions = std::collections::HashSet::new();
        for backup in &backups {
            unique_sessions.insert(&backup.session_id);
        }
        let sessions_with_backups = unique_sessions.len() as u32;

        let oldest_backup = backups.iter().map(|b| b.created_at).min();
        let newest_backup = backups.iter().map(|b| b.created_at).max();

        let average_backup_size = if total_backups > 0 {
            total_size / total_backups as u64
        } else {
            0
        };

        Ok(BackupStatistics {
            total_backups,
            total_size,
            automatic_backups,
            manual_backups,
            sessions_with_backups,
            oldest_backup,
            newest_backup,
            average_backup_size,
        })
    }

    pub async fn get_config(&self) -> BackupConfig {
        self.config.lock().await.clone()
    }

    pub async fn update_config(&self, new_config: BackupConfig) -> Result<()> {
        *self.config.lock().await = new_config;
        // TODO: Save config to persistent storage
        Ok(())
    }

    async fn cleanup_old_backups(&self, session_id: &str, config: &BackupConfig) -> Result<()> {
        let metadata_guard = self.backup_metadata.lock().await;
        let mut session_backups: Vec<&BackupMetadata> = metadata_guard
            .values()
            .filter(|b| b.session_id == session_id)
            .collect();

        // Sort by creation date (newest first)
        session_backups.sort_by(|a, b| b.created_at.cmp(&a.created_at));

        // Remove excess backups for this session
        if session_backups.len() > config.max_backups_per_session as usize {
            let to_remove = &session_backups[config.max_backups_per_session as usize..];
            for backup in to_remove {
                if backup.file_path.exists() {
                    let _ = fs::remove_file(&backup.file_path);
                }
            }
        }

        // Check global backup limit
        let all_backups: Vec<&BackupMetadata> = metadata_guard.values().collect();
        if all_backups.len() > config.max_total_backups as usize {
            let mut sorted_backups = all_backups;
            sorted_backups.sort_by(|a, b| a.created_at.cmp(&b.created_at)); // Oldest first
            
            let to_remove = &sorted_backups[..sorted_backups.len() - config.max_total_backups as usize];
            for backup in to_remove {
                if backup.file_path.exists() {
                    let _ = fs::remove_file(&backup.file_path);
                }
            }
        }

        Ok(())
    }

    async fn cleanup_orphaned_backups(&self) -> Result<()> {
        let file_service = self.file_service.lock().await;
        let backup_dir = file_service.get_storage_paths().await?.backups;

        if !backup_dir.exists() {
            return Ok(());
        }

        let metadata_guard = self.backup_metadata.lock().await;
        let known_files: std::collections::HashSet<PathBuf> = metadata_guard
            .values()
            .map(|m| m.file_path.clone())
            .collect();

        // Find orphaned backup files
        if let Ok(entries) = fs::read_dir(&backup_dir) {
            for entry in entries {
                if let Ok(entry) = entry {
                    let path = entry.path();
                    if path.is_file() && 
                       path.extension().map_or(false, |ext| ext == "json") &&
                       !known_files.contains(&path) &&
                       path.file_name().map_or(false, |name| name.to_string_lossy().contains("backup")) {
                        let _ = fs::remove_file(&path);
                    }
                }
            }
        }

        Ok(())
    }

    async fn calculate_checksum(&self, file_path: &Path) -> Result<String> {
        let mut file = std::fs::File::open(file_path)
            .context("Failed to open file for checksum")?;
        
        let mut hasher = Sha256::new();
        let mut buffer = [0; 8192];
        
        loop {
            let bytes_read = file.read(&mut buffer)
                .context("Failed to read file for checksum")?;
            
            if bytes_read == 0 {
                break;
            }
            
            hasher.update(&buffer[..bytes_read]);
        }

        Ok(format!("{:x}", hasher.finalize()))
    }

    async fn verify_backup_integrity(&self, metadata: &BackupMetadata) -> Result<bool> {
        if !metadata.file_path.exists() {
            return Ok(false);
        }

        let current_checksum = self.calculate_checksum(&metadata.file_path).await?;
        Ok(current_checksum == metadata.checksum)
    }
}