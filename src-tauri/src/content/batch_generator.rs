use serde::{Deserialize, Serialize};
use anyhow::Result;
use std::sync::Arc;
use tokio::sync::{Mutex, mpsc};
use uuid::Uuid;
use std::time::{Duration, Instant};
use crate::llm::LLMManager;
use crate::content::{ContentGenerator, ContentRequest, GeneratedContent};

/// Batch content generation manager
pub struct BatchContentGenerator {
    llm_manager: Arc<Mutex<LLMManager>>,
    progress_sender: Option<mpsc::UnboundedSender<BatchGenerationProgress>>,
}

/// Request for batch content generation
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BatchGenerationRequest {
    pub batch_id: String,
    pub batch_name: String,
    pub items: Vec<BatchContentItem>,
    pub options: BatchGenerationOptions,
}

/// Individual content item in a batch
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BatchContentItem {
    pub id: String,
    pub content_request: ContentRequest,
    pub priority: BatchPriority,
    pub metadata: serde_json::Value,
}

/// Batch generation options
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BatchGenerationOptions {
    pub parallel_generation: bool,
    pub max_parallel_jobs: usize,
    pub continue_on_error: bool,
    pub save_partial_results: bool,
    pub retry_failed_items: bool,
    pub max_retries: u32,
}

impl Default for BatchGenerationOptions {
    fn default() -> Self {
        Self {
            parallel_generation: true,
            max_parallel_jobs: 3,
            continue_on_error: true,
            save_partial_results: true,
            retry_failed_items: true,
            max_retries: 2,
        }
    }
}

/// Priority levels for batch items
#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq, Eq, PartialOrd, Ord)]
pub enum BatchPriority {
    Low = 0,
    Normal = 1,
    High = 2,
    Critical = 3,
}

/// Progress tracking for batch generation
#[derive(Debug, Clone, Serialize)]
pub struct BatchGenerationProgress {
    pub batch_id: String,
    pub total_items: usize,
    pub completed_items: usize,
    pub failed_items: usize,
    pub current_item_id: Option<String>,
    pub current_operation: String,
    pub progress_percent: f32,
    pub elapsed_time: Duration,
    pub estimated_time_remaining: Option<Duration>,
    pub errors: Vec<BatchError>,
}

/// Error information for batch processing
#[derive(Debug, Clone, Serialize)]
pub struct BatchError {
    pub item_id: String,
    pub error_message: String,
    pub error_type: BatchErrorType,
    #[serde(skip_serializing)]
    pub timestamp: Instant,
    pub retryable: bool,
}

#[derive(Debug, Clone, Serialize)]
pub enum BatchErrorType {
    LLMError,
    ValidationError,
    NetworkError,
    RateLimitError,
    UnknownError,
}

/// Result of batch generation
#[derive(Debug, Clone, Serialize)]
pub struct BatchGenerationResult {
    pub batch_id: String,
    pub total_items: usize,
    pub successful_items: usize,
    pub failed_items: usize,
    pub item_results: Vec<BatchItemResult>,
    pub total_elapsed_time: Duration,
    pub errors: Vec<BatchError>,
}

/// Result for individual batch item
#[derive(Debug, Clone, Serialize)]
pub struct BatchItemResult {
    pub item_id: String,
    pub success: bool,
    pub generated_content: Option<Vec<GeneratedContent>>,
    pub error: Option<String>,
    pub elapsed_time: Duration,
    pub retry_count: u32,
}

impl BatchContentGenerator {
    pub fn new(llm_manager: Arc<Mutex<LLMManager>>) -> Self {
        Self {
            llm_manager,
            progress_sender: None,
        }
    }

    pub fn with_progress_tracking(mut self, sender: mpsc::UnboundedSender<BatchGenerationProgress>) -> Self {
        self.progress_sender = Some(sender);
        self
    }

    pub async fn generate_batch(&self, request: BatchGenerationRequest) -> Result<BatchGenerationResult> {
        let start_time = Instant::now();
        let total_items = request.items.len();
        let mut errors = Vec::new();
        let mut item_results = Vec::new();

        // Sort items by priority
        let mut sorted_items = request.items.clone();
        sorted_items.sort_by(|a, b| b.priority.cmp(&a.priority));

        self.send_progress(BatchGenerationProgress {
            batch_id: request.batch_id.clone(),
            total_items,
            completed_items: 0,
            failed_items: 0,
            current_item_id: None,
            current_operation: "Starting batch generation".to_string(),
            progress_percent: 0.0,
            elapsed_time: Duration::from_secs(0),
            estimated_time_remaining: None,
            errors: vec![],
        });

        if request.options.parallel_generation {
            item_results = self.generate_parallel(sorted_items, &request.options, &request.batch_id).await?;
        } else {
            item_results = self.generate_sequential(sorted_items, &request.options, &request.batch_id).await?;
        }

        let successful_items = item_results.iter().filter(|r| r.success).count();
        let failed_items = total_items - successful_items;

        // Collect all errors
        for result in &item_results {
            if let Some(error_msg) = &result.error {
                errors.push(BatchError {
                    item_id: result.item_id.clone(),
                    error_message: error_msg.clone(),
                    error_type: BatchErrorType::UnknownError,
                    timestamp: Instant::now(),
                    retryable: result.retry_count < request.options.max_retries,
                });
            }
        }

        let total_elapsed_time = start_time.elapsed();

        self.send_progress(BatchGenerationProgress {
            batch_id: request.batch_id.clone(),
            total_items,
            completed_items: successful_items,
            failed_items,
            current_item_id: None,
            current_operation: "Batch generation completed".to_string(),
            progress_percent: 100.0,
            elapsed_time: total_elapsed_time,
            estimated_time_remaining: None,
            errors: errors.clone(),
        });

        Ok(BatchGenerationResult {
            batch_id: request.batch_id,
            total_items,
            successful_items,
            failed_items,
            item_results,
            total_elapsed_time,
            errors,
        })
    }

    async fn generate_sequential(
        &self,
        items: Vec<BatchContentItem>,
        options: &BatchGenerationOptions,
        batch_id: &str,
    ) -> Result<Vec<BatchItemResult>> {
        let mut results = Vec::new();
        let total = items.len();

        for (index, item) in items.iter().enumerate() {
            let item_start = Instant::now();
            
            self.send_progress(BatchGenerationProgress {
                batch_id: batch_id.to_string(),
                total_items: total,
                completed_items: index,
                failed_items: results.iter().filter(|r: &&BatchItemResult| !r.success).count(),
                current_item_id: Some(item.id.clone()),
                current_operation: format!("Generating content for: {}", item.content_request.topic),
                progress_percent: (index as f32 / total as f32) * 100.0,
                elapsed_time: item_start.elapsed(),
                estimated_time_remaining: self.estimate_remaining_time(index, total, item_start.elapsed()),
                errors: vec![],
            });

            let result = self.generate_single_item(item, options).await;
            results.push(result);

            if !options.continue_on_error && results.last().map_or(false, |r| !r.success) {
                break;
            }
        }

        Ok(results)
    }

    async fn generate_parallel(
        &self,
        items: Vec<BatchContentItem>,
        options: &BatchGenerationOptions,
        batch_id: &str,
    ) -> Result<Vec<BatchItemResult>> {
        use futures::stream::{self, StreamExt};
        
        let semaphore = Arc::new(tokio::sync::Semaphore::new(options.max_parallel_jobs));
        let total = items.len();
        let completed = Arc::new(Mutex::new(0));
        let start_time = Instant::now();

        let results = stream::iter(items)
            .map(|item| {
                let semaphore = semaphore.clone();
                let completed = completed.clone();
                let batch_id = batch_id.to_string();
                let total = total;
                
                async move {
                    let _permit = semaphore.acquire().await.unwrap();
                    
                    let result = self.generate_single_item(&item, options).await;
                    
                    let mut completed_count = completed.lock().await;
                    *completed_count += 1;
                    
                    self.send_progress(BatchGenerationProgress {
                        batch_id,
                        total_items: total,
                        completed_items: *completed_count,
                        failed_items: 0, // Will be calculated later
                        current_item_id: Some(item.id.clone()),
                        current_operation: format!("Completed: {}", item.content_request.topic),
                        progress_percent: (*completed_count as f32 / total as f32) * 100.0,
                        elapsed_time: start_time.elapsed(),
                        estimated_time_remaining: self.estimate_remaining_time(*completed_count, total, start_time.elapsed()),
                        errors: vec![],
                    });
                    
                    result
                }
            })
            .buffer_unordered(options.max_parallel_jobs)
            .collect::<Vec<_>>()
            .await;

        Ok(results)
    }

    async fn generate_single_item(
        &self,
        item: &BatchContentItem,
        options: &BatchGenerationOptions,
    ) -> BatchItemResult {
        let start_time = Instant::now();
        let mut retry_count = 0;
        let mut last_error = None;

        loop {
            let generator = ContentGenerator::new(self.llm_manager.clone());
            
            match generator.generate(&item.content_request).await {
                Ok(content) => {
                    return BatchItemResult {
                        item_id: item.id.clone(),
                        success: true,
                        generated_content: Some(content),
                        error: None,
                        elapsed_time: start_time.elapsed(),
                        retry_count,
                    };
                }
                Err(e) => {
                    last_error = Some(e.to_string());
                    retry_count += 1;
                    
                    if !options.retry_failed_items || retry_count >= options.max_retries {
                        break;
                    }
                    
                    // Exponential backoff
                    tokio::time::sleep(Duration::from_millis(100 * (2_u64.pow(retry_count)))).await;
                }
            }
        }

        BatchItemResult {
            item_id: item.id.clone(),
            success: false,
            generated_content: None,
            error: last_error,
            elapsed_time: start_time.elapsed(),
            retry_count,
        }
    }

    fn send_progress(&self, progress: BatchGenerationProgress) {
        if let Some(sender) = &self.progress_sender {
            let _ = sender.send(progress);
        }
    }

    fn estimate_remaining_time(&self, completed: usize, total: usize, elapsed: Duration) -> Option<Duration> {
        if completed == 0 {
            return None;
        }
        
        let avg_time_per_item = elapsed.as_secs_f64() / completed as f64;
        let remaining_items = total - completed;
        let estimated_seconds = avg_time_per_item * remaining_items as f64;
        
        Some(Duration::from_secs_f64(estimated_seconds))
    }
}