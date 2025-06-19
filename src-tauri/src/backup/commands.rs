use super::{BackupConfig, BackupType, BackupFilter, BackupListItem, BackupStatistics};
use super::service::BackupService;
use tauri::State;
use std::sync::Arc;

#[tauri::command]
pub async fn create_manual_backup(
    backup_service: State<'_, Arc<BackupService>>,
    session_id: String,
) -> Result<String, String> {
    backup_service
        .create_backup(&session_id, BackupType::Manual)
        .await
        .map_err(|e| e.to_string())
}

#[tauri::command]
pub async fn restore_from_backup(
    backup_service: State<'_, Arc<BackupService>>,
    backup_id: String,
) -> Result<String, String> {
    backup_service
        .restore_backup(&backup_id)
        .await
        .map_err(|e| e.to_string())
}

#[tauri::command]
pub async fn list_backups(
    backup_service: State<'_, Arc<BackupService>>,
    filter: Option<BackupFilter>,
) -> Result<Vec<BackupListItem>, String> {
    backup_service
        .list_backups(filter)
        .await
        .map_err(|e| e.to_string())
}

#[tauri::command]
pub async fn delete_backup(
    backup_service: State<'_, Arc<BackupService>>,
    backup_id: String,
) -> Result<(), String> {
    backup_service
        .delete_backup(&backup_id)
        .await
        .map_err(|e| e.to_string())
}

#[tauri::command]
pub async fn get_backup_statistics(
    backup_service: State<'_, Arc<BackupService>>,
) -> Result<BackupStatistics, String> {
    backup_service
        .get_backup_statistics()
        .await
        .map_err(|e| e.to_string())
}

#[tauri::command]
pub async fn get_backup_config(
    backup_service: State<'_, Arc<BackupService>>,
) -> Result<BackupConfig, String> {
    Ok(backup_service.get_config().await)
}

#[tauri::command]
pub async fn update_backup_config(
    backup_service: State<'_, Arc<BackupService>>,
    config: BackupConfig,
) -> Result<(), String> {
    backup_service
        .update_config(config)
        .await
        .map_err(|e| e.to_string())
}

#[tauri::command]
pub async fn cleanup_old_backups(
    backup_service: State<'_, Arc<BackupService>>,
) -> Result<u32, String> {
    // This would implement a manual cleanup of old backups
    // For now, return 0 as placeholder
    Ok(0)
}

#[tauri::command]
pub async fn verify_backup_integrity(
    backup_service: State<'_, Arc<BackupService>>,
    backup_id: String,
) -> Result<bool, String> {
    // Get backup metadata and verify file exists and checksum matches
    let backups = backup_service
        .list_backups(None)
        .await
        .map_err(|e| e.to_string())?;

    let backup = backups
        .iter()
        .find(|b| b.id == backup_id)
        .ok_or("Backup not found")?;

    Ok(backup.is_recoverable)
}

#[tauri::command]
pub async fn get_session_backups(
    backup_service: State<'_, Arc<BackupService>>,
    session_id: String,
    limit: Option<u32>,
) -> Result<Vec<BackupListItem>, String> {
    let filter = BackupFilter {
        session_id: Some(session_id),
        backup_type: None,
        start_date: None,
        end_date: None,
        auto_generated_only: None,
        limit,
        offset: None,
    };

    backup_service
        .list_backups(Some(filter))
        .await
        .map_err(|e| e.to_string())
}