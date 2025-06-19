use super::{BackupConfig, BackupInterval, BackupType};
use super::service::BackupService;
use std::sync::Arc;
use tokio::sync::Mutex;
use tokio::time::{interval, Duration};
use std::collections::HashMap;
use chrono::{DateTime, Utc};

pub struct BackupScheduler {
    backup_service: Arc<BackupService>,
    active_sessions: Arc<Mutex<HashMap<String, DateTime<Utc>>>>,
    is_running: Arc<Mutex<bool>>,
}

impl BackupScheduler {
    pub fn new(backup_service: Arc<BackupService>) -> Self {
        Self {
            backup_service,
            active_sessions: Arc::new(Mutex::new(HashMap::new())),
            is_running: Arc::new(Mutex::new(false)),
        }
    }

    pub async fn start(&self) -> anyhow::Result<()> {
        let mut is_running = self.is_running.lock().await;
        if *is_running {
            return Ok(());
        }
        *is_running = true;
        drop(is_running);

        let backup_service = Arc::clone(&self.backup_service);
        let active_sessions = Arc::clone(&self.active_sessions);
        let is_running = Arc::clone(&self.is_running);

        tokio::spawn(async move {
            Self::run_scheduler(backup_service, active_sessions, is_running).await;
        });

        Ok(())
    }

    pub async fn stop(&self) {
        *self.is_running.lock().await = false;
    }

    pub async fn register_session_activity(&self, session_id: &str) {
        let mut sessions = self.active_sessions.lock().await;
        sessions.insert(session_id.to_string(), Utc::now());
    }

    pub async fn trigger_session_close_backup(&self, session_id: &str) -> anyhow::Result<()> {
        let config = self.backup_service.get_config().await;
        
        if config.enabled && config.backup_on_session_close {
            self.backup_service.create_backup(session_id, BackupType::OnSessionClose).await?;
        }

        // Remove session from active tracking
        let mut sessions = self.active_sessions.lock().await;
        sessions.remove(session_id);

        Ok(())
    }

    pub async fn trigger_content_generation_backup(&self, session_id: &str) -> anyhow::Result<()> {
        let config = self.backup_service.get_config().await;
        
        if config.enabled && config.backup_on_content_generation {
            self.backup_service.create_backup(session_id, BackupType::OnContentGeneration).await?;
        }

        self.register_session_activity(session_id).await;

        Ok(())
    }

    async fn run_scheduler(
        backup_service: Arc<BackupService>,
        active_sessions: Arc<Mutex<HashMap<String, DateTime<Utc>>>>,
        is_running: Arc<Mutex<bool>>,
    ) {
        let mut check_interval = interval(Duration::from_secs(60)); // Check every minute

        loop {
            check_interval.tick().await;

            // Check if scheduler should continue running
            {
                let running = is_running.lock().await;
                if !*running {
                    break;
                }
            }

            // Get current config
            let config = backup_service.get_config().await;
            
            if !config.enabled {
                continue;
            }

            // Check if it's time for automatic backups
            if let Some(interval_seconds) = config.auto_backup_interval.to_seconds() {
                let sessions = active_sessions.lock().await;
                let now = Utc::now();

                for (session_id, last_activity) in sessions.iter() {
                    let time_since_activity = now.signed_duration_since(*last_activity);
                    
                    if time_since_activity.num_seconds() >= interval_seconds as i64 {
                        // Time for automatic backup
                        if let Err(e) = backup_service.create_backup(session_id, BackupType::Automatic).await {
                            eprintln!("Failed to create automatic backup for session {}: {}", session_id, e);
                        }
                    }
                }
            }

            // Check for session-based backups
            if matches!(config.auto_backup_interval, BackupInterval::EverySession) {
                let sessions = active_sessions.lock().await;
                
                for session_id in sessions.keys() {
                    // Check if this session needs a backup
                    // (Implementation would check last backup time vs session activity)
                    if Self::should_backup_session(&backup_service, session_id).await {
                        if let Err(e) = backup_service.create_backup(session_id, BackupType::Automatic).await {
                            eprintln!("Failed to create session backup for {}: {}", session_id, e);
                        }
                    }
                }
            }
        }
    }

    async fn should_backup_session(backup_service: &BackupService, session_id: &str) -> bool {
        // Get the most recent backup for this session
        if let Ok(backups) = backup_service.list_backups(Some(super::BackupFilter {
            session_id: Some(session_id.to_string()),
            backup_type: None,
            start_date: None,
            end_date: None,
            auto_generated_only: None,
            limit: Some(1),
            offset: None,
        })).await {
            if let Some(latest_backup) = backups.first() {
                let time_since_backup = Utc::now().signed_duration_since(latest_backup.created_at);
                // Backup if more than 5 minutes since last backup
                return time_since_backup.num_minutes() > 5;
            }
        }
        
        // No recent backups found, should backup
        true
    }
}

impl Drop for BackupScheduler {
    fn drop(&mut self) {
        // Ensure scheduler stops when dropped
        let is_running = Arc::clone(&self.is_running);
        tokio::spawn(async move {
            *is_running.lock().await = false;
        });
    }
}