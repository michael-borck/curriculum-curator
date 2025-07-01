use crate::state::AppState;
use crate::commands::AppError;
use crate::content::{
    BatchContentGenerator, BatchGenerationRequest, BatchContentItem, BatchGenerationOptions,
    BatchPriority, BatchGenerationProgress, BatchGenerationResult,
    ContentRequest, ContentType
};
use crate::session::SessionManager;
use std::sync::Arc;
use tokio::sync::{Mutex, mpsc};
use tauri::State;
use serde::{Deserialize, Serialize};
use uuid::Uuid;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CreateBatchRequest {
    pub batch_name: String,
    pub items: Vec<BatchItemInput>,
    pub options: Option<BatchGenerationOptions>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BatchItemInput {
    pub topic: String,
    pub learning_objectives: Vec<String>,
    pub duration: String,
    pub audience: String,
    pub content_types: Vec<String>,
    pub priority: Option<String>,
    pub metadata: Option<serde_json::Value>,
}

#[tauri::command]
pub async fn create_batch_generation(
    request: CreateBatchRequest,
    state: State<'_, AppState>,
) -> Result<String, AppError> {
    let batch_id = Uuid::new_v4().to_string();
    
    // Convert input items to BatchContentItems
    let items: Vec<BatchContentItem> = request.items.into_iter()
        .enumerate()
        .map(|(index, item)| {
            let content_types: Vec<ContentType> = item.content_types.into_iter()
                .filter_map(|ct| serde_json::from_value(serde_json::Value::String(ct)).ok())
                .collect();
            
            let priority = match item.priority.as_deref() {
                Some("critical") => BatchPriority::Critical,
                Some("high") => BatchPriority::High,
                Some("low") => BatchPriority::Low,
                _ => BatchPriority::Normal,
            };
            
            BatchContentItem {
                id: format!("item_{}", index),
                content_request: ContentRequest {
                    topic: item.topic,
                    learning_objectives: item.learning_objectives,
                    duration: item.duration,
                    audience: item.audience,
                    content_types,
                },
                priority,
                metadata: item.metadata.unwrap_or_else(|| serde_json::json!({})),
            }
        })
        .collect();
    
    let batch_request = BatchGenerationRequest {
        batch_id: batch_id.clone(),
        batch_name: request.batch_name,
        items,
        options: request.options.unwrap_or_default(),
    };
    
    // Store batch request in app state for later execution
    // For now, we'll just return the batch ID
    Ok(batch_id)
}

#[tauri::command]
pub async fn execute_batch_generation(
    batch_id: String,
    batch_request: BatchGenerationRequest,
    state: State<'_, AppState>,
) -> Result<BatchGenerationResult, AppError> {
    let llm_manager = state.llm_manager.clone();
    
    // Create progress channel
    let (tx, mut rx) = mpsc::unbounded_channel::<BatchGenerationProgress>();
    
    // Create batch generator with progress tracking
    let generator = BatchContentGenerator::new(llm_manager)
        .with_progress_tracking(tx);
    
    // Spawn a task to handle progress updates
    let batch_id_clone = batch_id.clone();
    tokio::spawn(async move {
        while let Some(progress) = rx.recv().await {
            // In a real implementation, you would emit these progress updates
            // to the frontend via Tauri events
            println!("Batch {} progress: {}%", batch_id_clone, progress.progress_percent);
        }
    });
    
    // Execute batch generation
    let result = generator.generate_batch(batch_request).await
        .map_err(|e| AppError::GenerationError(e.to_string()))?;
    
    Ok(result)
}

#[tauri::command]
pub async fn get_batch_status(
    batch_id: String,
    _state: State<'_, AppState>,
) -> Result<serde_json::Value, AppError> {
    // In a real implementation, this would retrieve the status of an ongoing batch
    // For now, return a mock status
    Ok(serde_json::json!({
        "batch_id": batch_id,
        "status": "pending",
        "total_items": 0,
        "completed_items": 0,
        "failed_items": 0,
        "progress_percent": 0.0,
    }))
}

#[tauri::command]
pub async fn cancel_batch_generation(
    batch_id: String,
    _state: State<'_, AppState>,
) -> Result<bool, AppError> {
    // In a real implementation, this would cancel an ongoing batch generation
    // For now, just return success
    Ok(true)
}

#[tauri::command]
pub async fn list_batch_generations(
    _state: State<'_, AppState>,
) -> Result<Vec<serde_json::Value>, AppError> {
    // In a real implementation, this would list all batch generations
    // For now, return an empty list
    Ok(vec![])
}

#[tauri::command]
pub async fn export_batch_results(
    batch_id: String,
    format: String,
    output_directory: String,
    _state: State<'_, AppState>,
) -> Result<serde_json::Value, AppError> {
    // In a real implementation, this would export batch results
    // For now, return a mock result
    Ok(serde_json::json!({
        "success": true,
        "batch_id": batch_id,
        "format": format,
        "output_directory": output_directory,
        "files_created": 0,
    }))
}