use super::*;
use crate::session::SessionManager;
use crate::import::service::ImportService;
use tauri::{State, Emitter};
use std::sync::Arc;
use tokio::sync::Mutex;
use std::path::PathBuf;
use anyhow::Result;

#[tauri::command]
pub async fn get_import_config(
    import_service: State<'_, Arc<Mutex<ImportService>>>,
) -> Result<ImportConfig, String> {
    let service = import_service.lock().await;
    Ok(service.get_config().await)
}

#[tauri::command]
pub async fn update_import_config(
    import_service: State<'_, Arc<Mutex<ImportService>>>,
    config: ImportConfig,
) -> Result<(), String> {
    let service = import_service.lock().await;
    service.update_config(config).await
        .map_err(|e| e.to_string())
}

#[tauri::command]
pub async fn preview_import_file(
    import_service: State<'_, Arc<Mutex<ImportService>>>,
    file_path: String,
) -> Result<ImportPreview, String> {
    let service = import_service.lock().await;
    let path = PathBuf::from(file_path);
    
    service.preview_import(&path).await
        .map_err(|e| e.to_string())
}

#[tauri::command]
pub async fn import_file(
    import_service: State<'_, Arc<Mutex<ImportService>>>,
    file_path: String,
    settings: Option<ImportSettings>,
) -> Result<ImportResult, String> {
    let service = import_service.lock().await;
    let path = PathBuf::from(file_path);
    
    service.import_file(&path, settings, None).await
        .map_err(|e| e.to_string())
}

#[tauri::command]
pub async fn import_file_with_progress(
    import_service: State<'_, Arc<Mutex<ImportService>>>,
    file_path: String,
    settings: Option<ImportSettings>,
    window: tauri::Window,
) -> Result<ImportResult, String> {
    let service = import_service.lock().await;
    let path = PathBuf::from(file_path);
    
    // Create progress callback that emits events to frontend
    let progress_callback = Box::new(move |progress: ImportProgress| {
        let _ = window.emit("import-progress", &progress);
    });
    
    service.import_file(&path, settings, Some(progress_callback)).await
        .map_err(|e| e.to_string())
}

#[tauri::command]
pub async fn get_supported_file_types() -> Result<Vec<SupportedFileTypeInfo>, String> {
    Ok(vec![
        SupportedFileTypeInfo {
            file_type: SupportedFileType::PowerPoint,
            display_name: "PowerPoint Presentation".to_string(),
            extensions: vec!["pptx".to_string()],
            icon: "📊".to_string(),
            description: "Import slides and speaker notes from PowerPoint presentations".to_string(),
        },
        SupportedFileTypeInfo {
            file_type: SupportedFileType::Word,
            display_name: "Word Document".to_string(),
            extensions: vec!["docx".to_string()],
            icon: "📝".to_string(),
            description: "Import content from Word documents, including lesson plans and worksheets".to_string(),
        },
    ])
}

#[tauri::command]
pub async fn analyze_imported_content(
    imported_content: Vec<ImportedContent>,
) -> Result<crate::import::analysis::AnalysisResult, String> {
    use crate::import::analysis::ContentAnalyzer;
    
    ContentAnalyzer::analyze(&imported_content)
        .map_err(|e| e.to_string())
}

#[tauri::command]
pub async fn generate_enhancement_suggestions(
    imported_content: Vec<ImportedContent>,
    analysis_result: crate::import::analysis::AnalysisResult,
    llm_provider_id: String,
) -> Result<crate::import::enhancement::EnhancementSuggestions, String> {
    use crate::import::enhancement::EnhancementEngine;
    
    // For Phase 2, we'll use a mock provider
    // In production, this would use the actual LLM manager
    // TODO: Integrate with real LLM providers when ready
    let llm_provider = Box::new(MockLLMProvider::new());
    
    let engine = EnhancementEngine::new(llm_provider);
    engine.generate_suggestions(&imported_content, &analysis_result)
        .await
        .map_err(|e| e.to_string())
}

#[tauri::command]
pub async fn create_content_comparison(
    original_content: Vec<ImportedContent>,
    enhanced_content: Vec<ImportedContent>,
) -> Result<crate::import::enhancement::ContentComparison, String> {
    use crate::import::analysis::ContentAnalyzer;
    use crate::import::enhancement::ContentComparison;
    
    // Analyze both versions
    let original_analysis = ContentAnalyzer::analyze(&original_content)
        .map_err(|e| e.to_string())?;
    let enhanced_analysis = ContentAnalyzer::analyze(&enhanced_content)
        .map_err(|e| e.to_string())?;
    
    Ok(ContentComparison::new(
        &original_content,
        &enhanced_content,
        &original_analysis,
        &enhanced_analysis,
    ))
}

#[tauri::command]
pub async fn validate_import_file(
    file_path: String,
) -> Result<FileValidationResult, String> {
    let path = PathBuf::from(&file_path);
    
    // Check if file exists
    if !path.exists() {
        return Ok(FileValidationResult {
            is_valid: false,
            error_message: Some("File does not exist".to_string()),
            file_info: None,
        });
    }
    
    // Check if it's a file
    if !path.is_file() {
        return Ok(FileValidationResult {
            is_valid: false,
            error_message: Some("Path is not a file".to_string()),
            file_info: None,
        });
    }
    
    // Check file extension
    let extension = path.extension()
        .and_then(|ext| ext.to_str())
        .unwrap_or("");
    
    let file_type = match SupportedFileType::from_extension(extension) {
        Some(ft) => ft,
        None => {
            return Ok(FileValidationResult {
                is_valid: false,
                error_message: Some(format!("Unsupported file type: .{}. Supported types: .pptx, .docx", extension)),
                file_info: None,
            });
        }
    };
    
    // Get file metadata
    let metadata = std::fs::metadata(&path)
        .map_err(|e| format!("Failed to read file metadata: {}", e))?;
    
    let file_info = BasicFileInfo {
        filename: path.file_name()
            .and_then(|name| name.to_str())
            .unwrap_or("unknown")
            .to_string(),
        file_size: metadata.len(),
        file_type,
        last_modified: metadata.modified().ok()
            .map(|time| chrono::DateTime::<chrono::Utc>::from(time)),
    };
    
    // Check file size (50MB limit)
    const MAX_FILE_SIZE: u64 = 50 * 1024 * 1024;
    if metadata.len() > MAX_FILE_SIZE {
        return Ok(FileValidationResult {
            is_valid: false,
            error_message: Some(format!(
                "File size ({} MB) exceeds maximum allowed size (50 MB)",
                metadata.len() / (1024 * 1024)
            )),
            file_info: Some(file_info),
        });
    }
    
    Ok(FileValidationResult {
        is_valid: true,
        error_message: None,
        file_info: Some(file_info),
    })
}

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct SupportedFileTypeInfo {
    pub file_type: SupportedFileType,
    pub display_name: String,
    pub extensions: Vec<String>,
    pub icon: String,
    pub description: String,
}

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct FileValidationResult {
    pub is_valid: bool,
    pub error_message: Option<String>,
    pub file_info: Option<BasicFileInfo>,
}

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct BasicFileInfo {
    pub filename: String,
    pub file_size: u64,
    pub file_type: SupportedFileType,
    pub last_modified: Option<chrono::DateTime<chrono::Utc>>,
}

// Temporary mock LLM provider for Phase 2 development
struct MockLLMProvider {
    config: crate::llm::ProviderConfig,
}

impl MockLLMProvider {
    fn new() -> Self {
        Self {
            config: crate::llm::ProviderConfig {
                api_key: None,
                base_url: None,
                timeout_seconds: 30,
                max_retries: 3,
                custom_headers: std::collections::HashMap::new(),
            },
        }
    }
}

#[async_trait::async_trait]
impl crate::llm::LLMProvider for MockLLMProvider {
    fn provider_type(&self) -> crate::llm::ProviderType {
        crate::llm::ProviderType::Ollama
    }
    
    fn config(&self) -> &crate::llm::ProviderConfig {
        &self.config
    }

    async fn health_check(&self) -> crate::llm::LLMResult<bool> {
        Ok(true)
    }

    async fn list_models(&self) -> crate::llm::LLMResult<Vec<crate::llm::ModelInfo>> {
        Ok(vec![])
    }
    
    async fn generate(&self, _request: &crate::llm::LLMRequest) -> crate::llm::LLMResult<crate::llm::LLMResponse> {
        Ok(crate::llm::LLMResponse {
            content: "Mock response for content enhancement".to_string(),
            model: "mock".to_string(),
            finish_reason: crate::llm::FinishReason::Stop,
            usage: crate::llm::TokenUsage {
                prompt_tokens: 10,
                completion_tokens: 10,
                total_tokens: 20,
            },
        })
    }
    
    async fn generate_stream(&self, _request: &crate::llm::LLMRequest) -> crate::llm::LLMResult<Box<dyn futures::Stream<Item = crate::llm::LLMResult<String>> + Send + Unpin>> {
        Err(crate::llm::LLMError::Config("Streaming not supported in mock provider".to_string()))
    }
    
    async fn estimate_cost(&self, _request: &crate::llm::LLMRequest) -> crate::llm::LLMResult<f64> {
        Ok(0.0)
    }
    
    fn get_limits(&self) -> crate::llm::ProviderLimits {
        crate::llm::ProviderLimits {
            requests_per_minute: 60,
            tokens_per_minute: 10000,
            requests_per_day: Some(10000),
            context_window: 4096,
        }
    }
    
    fn get_model_info(&self, _model: &str) -> Option<crate::llm::ModelInfo> {
        None
    }
    
    fn count_tokens(&self, text: &str) -> usize {
        text.len() / 4
    }
    
    async fn get_usage_stats(&self, _window: crate::llm::UsageWindow) -> crate::llm::LLMResult<crate::llm::ProviderUsageStats> {
        Ok(crate::llm::ProviderUsageStats {
            provider: crate::llm::ProviderType::Ollama,
            window: crate::llm::UsageWindow::Today,
            total_requests: 0,
            successful_requests: 0,
            failed_requests: 0,
            total_tokens: 0,
            total_cost_usd: 0.0,
            average_response_time_ms: 0,
            error_rate: 0.0,
            last_24h: None,
            last_7d: None,
        })
    }
}