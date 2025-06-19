use std::collections::HashMap;
use std::sync::Arc;
use std::time::Duration;
use anyhow::{Result, anyhow};
use chrono::{DateTime, Utc, Duration as ChronoDuration};
use tokio::sync::{Mutex, watch};
use tokio::time::{interval, Interval};
use serde::{Deserialize, Serialize};

use crate::maintenance::{
    MaintenanceService, MaintenanceConfig, MaintenanceOperation, 
    ScheduleConfig, MaintenanceResult
};

/// Automatic maintenance scheduler
pub struct MaintenanceScheduler {
    maintenance_service: Arc<Mutex<MaintenanceService>>,
    config: Arc<Mutex<MaintenanceConfig>>,
    running_tasks: Arc<Mutex<HashMap<String, ScheduledTask>>>,
    shutdown_sender: watch::Sender<bool>,
    shutdown_receiver: watch::Receiver<bool>,
}

/// Scheduled maintenance task
#[derive(Debug, Clone)]
pub struct ScheduledTask {
    pub id: String,
    pub operation: MaintenanceOperation,
    pub config: ScheduleConfig,
    pub next_run: DateTime<Utc>,
    pub last_run: Option<DateTime<Utc>>,
    pub last_result: Option<MaintenanceResult>,
    pub is_running: bool,
}

/// Scheduler status information
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SchedulerStatus {
    pub is_running: bool,
    pub active_tasks: u32,
    pub scheduled_tasks: Vec<ScheduledTaskInfo>,
    pub next_scheduled_task: Option<ScheduledTaskInfo>,
    pub last_maintenance: Option<DateTime<Utc>>,
    pub total_runs_today: u32,
    pub total_runs_this_week: u32,
}

/// Scheduled task information for frontend
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ScheduledTaskInfo {
    pub id: String,
    pub operation: MaintenanceOperation,
    pub enabled: bool,
    pub interval_hours: u32,
    pub next_run: DateTime<Utc>,
    pub last_run: Option<DateTime<Utc>>,
    pub last_success: Option<bool>,
    pub is_running: bool,
    pub max_duration_minutes: u32,
    pub skip_if_active_sessions: bool,
}

impl MaintenanceScheduler {
    /// Create a new maintenance scheduler
    pub fn new(
        maintenance_service: Arc<Mutex<MaintenanceService>>,
        config: Arc<Mutex<MaintenanceConfig>>,
    ) -> Self {
        let (shutdown_sender, shutdown_receiver) = watch::channel(false);

        Self {
            maintenance_service,
            config,
            running_tasks: Arc::new(Mutex::new(HashMap::new())),
            shutdown_sender,
            shutdown_receiver,
        }
    }

    /// Start the maintenance scheduler
    pub async fn start(&self) -> Result<()> {
        let maintenance_service = Arc::clone(&self.maintenance_service);
        let config = Arc::clone(&self.config);
        let running_tasks = Arc::clone(&self.running_tasks);
        let mut shutdown_receiver = self.shutdown_receiver.clone();

        // Initialize scheduled tasks from config
        self.initialize_scheduled_tasks().await?;

        // Start the main scheduler loop
        let scheduler_handle = tokio::spawn(async move {
            let mut check_interval = interval(Duration::from_secs(60)); // Check every minute

            loop {
                tokio::select! {
                    _ = check_interval.tick() => {
                        if let Err(e) = Self::check_and_run_scheduled_tasks(
                            &maintenance_service,
                            &config,
                            &running_tasks,
                        ).await {
                            eprintln!("Error in scheduled maintenance: {}", e);
                        }
                    }
                    _ = shutdown_receiver.changed() => {
                        if *shutdown_receiver.borrow() {
                            break;
                        }
                    }
                }
            }
        });

        Ok(())
    }

    /// Stop the maintenance scheduler
    pub async fn stop(&self) -> Result<()> {
        self.shutdown_sender.send(true)?;
        
        // Wait for running tasks to complete (with timeout)
        let timeout = tokio::time::timeout(
            Duration::from_secs(300), // 5 minute timeout
            self.wait_for_tasks_completion()
        ).await;

        if timeout.is_err() {
            eprintln!("Warning: Some maintenance tasks did not complete within timeout");
        }

        Ok(())
    }

    /// Get current scheduler status
    pub async fn get_status(&self) -> Result<SchedulerStatus> {
        let tasks = self.running_tasks.lock().await;
        let config = self.config.lock().await;

        let scheduled_tasks: Vec<ScheduledTaskInfo> = tasks
            .values()
            .map(|task| ScheduledTaskInfo {
                id: task.id.clone(),
                operation: task.operation.clone(),
                enabled: task.config.enabled,
                interval_hours: task.config.interval_hours,
                next_run: task.next_run,
                last_run: task.last_run,
                last_success: task.last_result.as_ref().map(|r| r.success),
                is_running: task.is_running,
                max_duration_minutes: task.config.max_duration_minutes,
                skip_if_active_sessions: task.config.skip_if_active_sessions,
            })
            .collect();

        let active_tasks = tasks.values().filter(|t| t.is_running).count() as u32;
        
        let next_scheduled_task = scheduled_tasks
            .iter()
            .filter(|t| t.enabled && !t.is_running)
            .min_by_key(|t| t.next_run)
            .cloned();

        let last_maintenance = tasks
            .values()
            .filter_map(|t| t.last_run)
            .max();

        let now = Utc::now();
        let today_start = now.date_naive().and_hms_opt(0, 0, 0).unwrap().and_utc();
        let week_start = now - ChronoDuration::days(7);

        let total_runs_today = tasks
            .values()
            .filter(|t| t.last_run.map_or(false, |lr| lr >= today_start))
            .count() as u32;

        let total_runs_this_week = tasks
            .values()
            .filter(|t| t.last_run.map_or(false, |lr| lr >= week_start))
            .count() as u32;

        Ok(SchedulerStatus {
            is_running: !*self.shutdown_receiver.borrow(),
            active_tasks,
            scheduled_tasks,
            next_scheduled_task,
            last_maintenance,
            total_runs_today,
            total_runs_this_week,
        })
    }

    /// Update scheduler configuration
    pub async fn update_config(&self, new_config: MaintenanceConfig) -> Result<()> {
        // Update the config
        {
            let mut config = self.config.lock().await;
            *config = new_config.clone();
        }

        // Reinitialize scheduled tasks
        self.initialize_scheduled_tasks().await?;

        Ok(())
    }

    /// Manually trigger a maintenance operation
    pub async fn trigger_maintenance(
        &self,
        operation: MaintenanceOperation,
        force: bool,
    ) -> Result<MaintenanceResult> {
        let maintenance_service = self.maintenance_service.lock().await;
        
        // Check if we should skip due to active sessions
        if !force {
            let config = self.config.lock().await;
            if let Some(schedule_config) = config.schedule_configs.values()
                .find(|sc| sc.operation == operation) {
                if schedule_config.skip_if_active_sessions && self.has_active_sessions().await? {
                    return Err(anyhow!("Skipping maintenance due to active sessions"));
                }
            }
        }

        let results = maintenance_service
            .perform_maintenance(vec![operation], false)
            .await?;

        results
            .into_iter()
            .next()
            .ok_or_else(|| anyhow!("No maintenance result returned"))
    }

    /// Initialize scheduled tasks from configuration
    async fn initialize_scheduled_tasks(&self) -> Result<()> {
        let config = self.config.lock().await;
        let mut tasks = self.running_tasks.lock().await;

        tasks.clear();

        for (id, schedule_config) in &config.schedule_configs {
            if schedule_config.enabled {
                let next_run = Utc::now() + ChronoDuration::hours(schedule_config.interval_hours as i64);
                
                let task = ScheduledTask {
                    id: id.clone(),
                    operation: schedule_config.operation.clone(),
                    config: schedule_config.clone(),
                    next_run,
                    last_run: None,
                    last_result: None,
                    is_running: false,
                };

                tasks.insert(id.clone(), task);
            }
        }

        Ok(())
    }

    /// Check and run scheduled tasks
    async fn check_and_run_scheduled_tasks(
        maintenance_service: &Arc<Mutex<MaintenanceService>>,
        config: &Arc<Mutex<MaintenanceConfig>>,
        running_tasks: &Arc<Mutex<HashMap<String, ScheduledTask>>>,
    ) -> Result<()> {
        let now = Utc::now();
        let mut tasks_to_run = Vec::new();

        // Find tasks that are ready to run
        {
            let tasks = running_tasks.lock().await;
            for (id, task) in tasks.iter() {
                if task.config.enabled && !task.is_running && task.next_run <= now {
                    // Check if we should skip due to active sessions
                    if task.config.skip_if_active_sessions {
                        // This would need to check actual session activity
                        // For now, we'll assume no active sessions
                    }

                    tasks_to_run.push((id.clone(), task.operation.clone()));
                }
            }
        }

        // Run the scheduled tasks
        for (task_id, operation) in tasks_to_run {
            Self::run_scheduled_task(
                &task_id,
                operation,
                maintenance_service,
                config,
                running_tasks,
            ).await?;
        }

        Ok(())
    }

    /// Run a scheduled maintenance task
    async fn run_scheduled_task(
        task_id: &str,
        operation: MaintenanceOperation,
        maintenance_service: &Arc<Mutex<MaintenanceService>>,
        config: &Arc<Mutex<MaintenanceConfig>>,
        running_tasks: &Arc<Mutex<HashMap<String, ScheduledTask>>>,
    ) -> Result<()> {
        // Mark task as running
        {
            let mut tasks = running_tasks.lock().await;
            if let Some(task) = tasks.get_mut(task_id) {
                task.is_running = true;
            }
        }

        let start_time = Utc::now();
        let result = {
            let service = maintenance_service.lock().await;
            service.perform_maintenance(vec![operation.clone()], false).await
        };

        let end_time = Utc::now();

        // Update task with results
        {
            let mut tasks = running_tasks.lock().await;
            if let Some(task) = tasks.get_mut(task_id) {
                task.is_running = false;
                task.last_run = Some(end_time);
                
                if let Ok(results) = &result {
                    if let Some(maintenance_result) = results.first() {
                        task.last_result = Some(maintenance_result.clone());
                    }
                }

                // Schedule next run
                task.next_run = end_time + ChronoDuration::hours(task.config.interval_hours as i64);
            }
        }

        match result {
            Ok(results) => {
                if let Some(maintenance_result) = results.first() {
                    if maintenance_result.success {
                        println!("Scheduled maintenance {} completed successfully", task_id);
                    } else {
                        eprintln!("Scheduled maintenance {} completed with errors: {:?}", 
                                task_id, maintenance_result.errors);
                    }
                }
            }
            Err(e) => {
                eprintln!("Scheduled maintenance {} failed: {}", task_id, e);
            }
        }

        Ok(())
    }

    /// Wait for all running tasks to complete
    async fn wait_for_tasks_completion(&self) {
        loop {
            let tasks = self.running_tasks.lock().await;
            let running_count = tasks.values().filter(|t| t.is_running).count();
            
            if running_count == 0 {
                break;
            }

            drop(tasks);
            tokio::time::sleep(Duration::from_secs(1)).await;
        }
    }

    /// Check if there are active sessions (placeholder implementation)
    async fn has_active_sessions(&self) -> Result<bool> {
        // This would check if there are active user sessions
        // For now, return false to allow maintenance
        Ok(false)
    }
}