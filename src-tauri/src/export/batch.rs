use super::{ExportManager, BatchExportJob, BatchExportOptions, BatchExportResult, JobResult, ExportOptions, ExportFormat, BatchProgress, NamingStrategy};
use crate::content::GeneratedContent;
use crate::session::SessionManager;
use anyhow::{Result, Context};
use std::path::PathBuf;
use std::sync::{Arc, Mutex};
use std::time::Instant;
use tokio::sync::mpsc;
use uuid::Uuid;
use serde_json;

pub struct BatchExportManager {
    export_manager: ExportManager,
    session_manager: SessionManager,
    progress_sender: Option<mpsc::UnboundedSender<BatchProgress>>,
}

impl BatchExportManager {
    pub fn new(session_manager: SessionManager) -> Self {
        Self {
            export_manager: ExportManager::new(),
            session_manager,
            progress_sender: None,
        }
    }

    pub fn with_progress_tracking(mut self, sender: mpsc::UnboundedSender<BatchProgress>) -> Self {
        self.progress_sender = Some(sender);
        self
    }

    pub async fn execute_batch_export(
        &self,
        jobs: Vec<BatchExportJob>,
        options: BatchExportOptions,
    ) -> Result<BatchExportResult> {
        let start_time = Instant::now();
        let total_jobs = jobs.len();
        
        self.send_progress(BatchProgress {
            total_jobs,
            completed_jobs: 0,
            current_job_id: None,
            current_operation: "Starting batch export".to_string(),
            progress_percent: 0.0,
            estimated_completion: None,
            errors_encountered: 0,
        });

        // Create output directories
        for job in &jobs {
            std::fs::create_dir_all(&job.output_directory)
                .context(format!("Failed to create output directory: {}", job.output_directory.display()))?;
        }

        let job_results = if options.parallel_exports {
            self.execute_parallel_jobs(jobs, &options).await?
        } else {
            self.execute_sequential_jobs(jobs, &options).await?
        };

        let successful_jobs = job_results.iter().filter(|r| r.success).count();
        let failed_jobs = total_jobs - successful_jobs;
        let total_files_created = job_results.iter().map(|r| r.files_created).sum();
        let total_size = job_results.iter().map(|r| r.total_size).sum();
        let elapsed_time = start_time.elapsed();

        // Create manifest if requested
        let manifest_path = if options.create_manifest {
            Some(self.create_manifest(&job_results, &options).await?)
        } else {
            None
        };

        let result = BatchExportResult {
            total_jobs,
            successful_jobs,
            failed_jobs,
            job_results,
            total_files_created,
            total_size,
            elapsed_time,
            manifest_path,
        };

        self.send_progress(BatchProgress {
            total_jobs,
            completed_jobs: total_jobs,
            current_job_id: None,
            current_operation: "Batch export completed".to_string(),
            progress_percent: 100.0,
            estimated_completion: None,
            errors_encountered: failed_jobs,
        });

        Ok(result)
    }

    async fn execute_sequential_jobs(
        &self,
        jobs: Vec<BatchExportJob>,
        options: &BatchExportOptions,
    ) -> Result<Vec<JobResult>> {
        let mut results: Vec<JobResult> = Vec::new();
        let total_jobs = jobs.len();

        for (index, job) in jobs.into_iter().enumerate() {
            self.send_progress(BatchProgress {
                total_jobs,
                completed_jobs: index,
                current_job_id: Some(job.job_id.clone()),
                current_operation: format!("Processing job: {}", job.job_id),
                progress_percent: (index as f32 / total_jobs as f32) * 100.0,
                estimated_completion: None,
                errors_encountered: results.iter().filter(|r| !r.success).count(),
            });

            match self.execute_single_job(job).await {
                Ok(result) => results.push(result),
                Err(e) => {
                    if !options.continue_on_error {
                        return Err(e);
                    }
                    results.push(JobResult {
                        job_id: format!("job_{}", index),
                        success: false,
                        export_results: vec![],
                        error_message: Some(e.to_string()),
                        files_created: 0,
                        total_size: 0,
                    });
                }
            }
        }

        Ok(results)
    }

    async fn execute_parallel_jobs(
        &self,
        jobs: Vec<BatchExportJob>,
        options: &BatchExportOptions,
    ) -> Result<Vec<JobResult>> {
        use tokio::task::JoinSet;

        let mut join_set = JoinSet::new();
        let semaphore = Arc::new(tokio::sync::Semaphore::new(options.max_concurrent_jobs));
        let progress = Arc::new(Mutex::new(0usize));
        let total_jobs = jobs.len();

        // Spawn tasks for parallel execution
        for job in jobs {
            let permit = semaphore.clone().acquire_owned().await.unwrap();
            let progress_clone = Arc::clone(&progress);
            let _job_id = job.job_id.clone();
            let export_manager = ExportManager::new(); // Each task gets its own manager
            let session_manager = self.session_manager.clone();

            join_set.spawn(async move {
                let _permit = permit; // Hold the permit for the duration of the task
                
                let batch_manager = BatchExportManager {
                    export_manager,
                    session_manager,
                    progress_sender: None,
                };

                let result = batch_manager.execute_single_job(job).await;
                
                // Update progress
                {
                    let mut progress_guard = progress_clone.lock().unwrap();
                    *progress_guard += 1;
                }

                result
            });
        }

        // Collect results
        let mut results: Vec<JobResult> = Vec::new();
        while let Some(join_result) = join_set.join_next().await {
            match join_result {
                Ok(job_result) => {
                    match job_result {
                        Ok(result) => results.push(result),
                        Err(e) => {
                            if !options.continue_on_error {
                                return Err(e);
                            }
                            results.push(JobResult {
                                job_id: "unknown".to_string(),
                                success: false,
                                export_results: vec![],
                                error_message: Some(e.to_string()),
                                files_created: 0,
                                total_size: 0,
                            });
                        }
                    }
                }
                Err(e) => {
                    if !options.continue_on_error {
                        return Err(e.into());
                    }
                }
            }

            // Send progress update
            let completed = {
                let progress_guard = progress.lock().unwrap();
                *progress_guard
            };

            self.send_progress(BatchProgress {
                total_jobs,
                completed_jobs: completed,
                current_job_id: None,
                current_operation: format!("Completed {} of {} jobs", completed, total_jobs),
                progress_percent: (completed as f32 / total_jobs as f32) * 100.0,
                estimated_completion: None,
                errors_encountered: results.iter().filter(|r| !r.success).count(),
            });
        }

        Ok(results)
    }

    async fn execute_single_job(&self, job: BatchExportJob) -> Result<JobResult> {
        let job_id = job.job_id.clone();
        
        // Retrieve content for all sessions
        let mut all_content = Vec::new();

        for session_id_str in &job.session_ids {
            let session_uuid = Uuid::parse_str(session_id_str)
                .context(format!("Invalid session ID: {}", session_id_str))?;
            
            let _session = self.session_manager.get_session(session_uuid).await
                .context(format!("Failed to get session: {}", session_id_str))?
                .ok_or_else(|| anyhow::anyhow!("Session not found: {}", session_id_str))?;
            
            let content = self.session_manager.get_session_content(session_uuid).await
                .context(format!("Failed to get content for session: {}", session_id_str))?;
            
            all_content.extend(content);
        }

        // Determine content to export
        let export_content = if job.merge_sessions {
            all_content
        } else {
            // For non-merged sessions, we'll export each session separately
            // For now, we'll merge them but this could be enhanced
            all_content
        };

        if export_content.is_empty() {
            return Ok(JobResult {
                job_id,
                success: false,
                export_results: vec![],
                error_message: Some("No content found for specified sessions".to_string()),
                files_created: 0,
                total_size: 0,
            });
        }

        // Export to all requested formats
        let mut export_results = Vec::new();
        let mut total_size = 0u64;

        for format in &job.formats {
            let filename = self.generate_filename(&job, format, &export_content)?;
            let output_path = job.output_directory.join(filename);

            let options = ExportOptions {
                format: format.clone(),
                output_path: output_path.clone(),
                template_name: job.template_name.clone(),
                include_metadata: job.include_metadata,
                branding_options: job.branding_options.clone(),
            };

            match self.export_manager.export_content(&export_content, &options).await {
                Ok(result) => {
                    if let Some(size) = result.file_size {
                        total_size += size;
                    }
                    export_results.push(result);
                }
                Err(e) => {
                    export_results.push(super::ExportResult {
                        success: false,
                        output_path,
                        file_size: None,
                        error_message: Some(e.to_string()),
                    });
                }
            }
        }

        let files_created = export_results.iter().filter(|r| r.success).count();
        let success = !export_results.is_empty() && export_results.iter().any(|r| r.success);

        Ok(JobResult {
            job_id,
            success,
            export_results,
            error_message: None,
            files_created,
            total_size,
        })
    }

    fn generate_filename(
        &self,
        job: &BatchExportJob,
        format: &ExportFormat,
        content: &[GeneratedContent],
    ) -> Result<String> {
        let extension = self.export_manager.get_default_extension(format);
        
        let base_name = match &job.naming_strategy {
            NamingStrategy::SessionBased => {
                if job.session_ids.len() == 1 {
                    format!("session_{}", job.session_ids[0])
                } else {
                    format!("sessions_{}", job.session_ids.len())
                }
            }
            NamingStrategy::ContentBased => {
                if let Some(first_content) = content.first() {
                    sanitize_filename(&first_content.title)
                } else {
                    "content".to_string()
                }
            }
            NamingStrategy::Sequential => {
                format!("export_{}", chrono::Utc::now().format("%Y%m%d_%H%M%S"))
            }
            NamingStrategy::Custom(pattern) => {
                // Simple placeholder replacement
                let mut result = pattern.clone();
                result = result.replace("{job_id}", &job.job_id);
                result = result.replace("{timestamp}", &chrono::Utc::now().format("%Y%m%d_%H%M%S").to_string());
                result = result.replace("{format}", &format!("{:?}", format).to_lowercase());
                if let Some(first_content) = content.first() {
                    result = result.replace("{title}", &sanitize_filename(&first_content.title));
                }
                result
            }
        };

        Ok(format!("{}.{}", base_name, extension))
    }

    async fn create_manifest(
        &self,
        job_results: &[JobResult],
        _options: &BatchExportOptions,
    ) -> Result<PathBuf> {
        let manifest = serde_json::json!({
            "batch_export_manifest": {
                "created_at": chrono::Utc::now().to_rfc3339(),
                "total_jobs": job_results.len(),
                "successful_jobs": job_results.iter().filter(|r| r.success).count(),
                "failed_jobs": job_results.iter().filter(|r| !r.success).count(),
                "jobs": job_results.iter().map(|job| {
                    serde_json::json!({
                        "job_id": job.job_id,
                        "success": job.success,
                        "files_created": job.files_created,
                        "total_size": job.total_size,
                        "exports": job.export_results.iter().map(|export| {
                            serde_json::json!({
                                "success": export.success,
                                "output_path": export.output_path,
                                "file_size": export.file_size,
                                "error_message": export.error_message
                            })
                        }).collect::<Vec<_>>()
                    })
                }).collect::<Vec<_>>()
            }
        });

        let manifest_path = PathBuf::from("batch_export_manifest.json");
        std::fs::write(&manifest_path, serde_json::to_string_pretty(&manifest)?)?;
        
        Ok(manifest_path)
    }

    fn send_progress(&self, progress: BatchProgress) {
        if let Some(sender) = &self.progress_sender {
            let _ = sender.send(progress);
        }
    }
}

// Utility function to sanitize filenames
fn sanitize_filename(filename: &str) -> String {
    filename
        .chars()
        .map(|c| match c {
            '/' | '\\' | ':' | '*' | '?' | '"' | '<' | '>' | '|' => '_',
            c if c.is_control() => '_',
            c => c,
        })
        .collect::<String>()
        .trim()
        .to_string()
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::content::{ContentType, generator::ContentMetadata};

    fn create_test_content() -> GeneratedContent {
        GeneratedContent {
            content_type: ContentType::Slides,
            title: "Test Content".to_string(),
            content: "Test content body".to_string(),
            metadata: ContentMetadata {
                word_count: 3,
                estimated_duration: "5 minutes".to_string(),
                difficulty_level: "Easy".to_string(),
            },
        }
    }

    #[test]
    fn test_filename_sanitization() {
        assert_eq!(sanitize_filename("Test/File:Name"), "Test_File_Name");
        assert_eq!(sanitize_filename("Normal File"), "Normal File");
        assert_eq!(sanitize_filename("File*With?Special<Chars>"), "File_With_Special_Chars_");
    }

    #[test]
    fn test_naming_strategies() {
        // This would require a more complex test setup with actual BatchExportManager
        // For now, we'll test the basic filename sanitization
        let content = vec![create_test_content()];
        
        // Test content-based naming strategy would generate something like "Test_Content"
        let sanitized = sanitize_filename(&content[0].title);
        assert_eq!(sanitized, "Test Content");
    }
}