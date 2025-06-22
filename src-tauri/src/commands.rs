use tauri::command;
use serde::{Deserialize, Serialize};

#[derive(Debug, Serialize, Deserialize)]
pub struct AppError {
    pub message: String,
    pub code: Option<String>,
}

impl From<anyhow::Error> for AppError {
    fn from(error: anyhow::Error) -> Self {
        AppError {
            message: error.to_string(),
            code: None,
        }
    }
}

// Health check command for testing Tauri setup
#[command]
pub async fn health_check() -> Result<String, AppError> {
    Ok("Curriculum Curator backend is running".to_string())
}

// File system commands with proper error handling
#[command]
pub async fn create_project_directory(path: String) -> Result<(), AppError> {
    use std::fs;
    fs::create_dir_all(&path)
        .map_err(|e| AppError {
            message: format!("Failed to create directory: {}", e),
            code: Some("FS_CREATE_DIR_ERROR".to_string()),
        })?;
    Ok(())
}

#[command]
pub async fn check_file_exists(path: String) -> Result<bool, AppError> {
    use std::path::Path;
    Ok(Path::new(&path).exists())
}

// LLM provider configuration commands
#[command]
pub async fn test_llm_connection(provider: String) -> Result<bool, AppError> {
    // Placeholder for LLM connection testing
    // Will be implemented when LLM providers are added
    match provider.as_str() {
        "ollama" => Ok(true), // Assume local Ollama is available
        _ => Ok(false),
    }
}

// Session management commands
#[command]
pub async fn create_new_session(name: String) -> Result<String, AppError> {
    use crate::session::SessionManager;
    
    // Get app data directory for database
    let app_data_dir = dirs::config_dir()
        .ok_or_else(|| AppError {
            message: "Could not get app data directory".to_string(),
            code: Some("CONFIG_DIR_ERROR".to_string()),
        })?
        .join("curriculum-curator");
    
    std::fs::create_dir_all(&app_data_dir)
        .map_err(|e| AppError {
            message: format!("Failed to create app data directory: {}", e),
            code: Some("FS_CREATE_DIR_ERROR".to_string()),
        })?;
    
    let db_path = app_data_dir.join("sessions.db");
    
    // Create shared database
    use crate::database::Database;
    let shared_db = Database::create_shared(db_path.to_str().unwrap()).await
        .map_err(|e| AppError {
            message: format!("Failed to initialize database: {}", e),
            code: Some("DB_INIT_ERROR".to_string()),
        })?;
    
    let session_manager = SessionManager::new(shared_db);
    
    let session = session_manager.create_session(name).await
        .map_err(|e| AppError {
            message: format!("Failed to create session: {}", e),
            code: Some("SESSION_CREATE_ERROR".to_string()),
        })?;
    
    Ok(session.id.to_string())
}


// Content generation commands
#[command]
pub async fn generate_content(
    session_id: String,
    topic: String,
    learning_objectives: Vec<String>,
    duration: String,
    audience: String,
    content_types: Vec<String>,
) -> Result<Vec<serde_json::Value>, AppError> {
    use uuid::Uuid;
    use crate::content::{ContentRequest, ContentType};
    
    // Parse session ID
    let _session_uuid = Uuid::parse_str(&session_id)
        .map_err(|e| AppError {
            message: format!("Invalid session ID: {}", e),
            code: Some("INVALID_SESSION_ID".to_string()),
        })?;

    // Parse content types
    let parsed_content_types: Result<Vec<ContentType>, AppError> = content_types.iter()
        .map(|ct| match ct.as_str() {
            "Slides" => Ok(ContentType::Slides),
            "InstructorNotes" => Ok(ContentType::InstructorNotes),
            "Worksheet" => Ok(ContentType::Worksheet),
            "Quiz" => Ok(ContentType::Quiz),
            "ActivityGuide" => Ok(ContentType::ActivityGuide),
            _ => Err(AppError {
                message: format!("Unknown content type: {}", ct),
                code: Some("INVALID_CONTENT_TYPE".to_string()),
            }),
        })
        .collect();

    let content_request = ContentRequest {
        topic,
        learning_objectives,
        duration,
        audience,
        content_types: parsed_content_types?,
    };

    // Placeholder for actual content generation
    // Will be implemented when LLM integration is complete
    let mock_content = content_request.content_types.iter().map(|ct| {
        serde_json::json!({
            "content_type": format!("{:?}", ct),
            "title": format!("{} for {}", format!("{:?}", ct), content_request.topic),
            "content": format!("Generated {} content for topic: {}", format!("{:?}", ct), content_request.topic),
            "metadata": {
                "word_count": 500,
                "estimated_duration": content_request.duration,
                "difficulty_level": "Intermediate"
            }
        })
    }).collect();

    Ok(mock_content)
}

// Configuration commands
#[command]
pub async fn get_app_config(key: String) -> Result<Option<String>, AppError> {
    use crate::database::Database;
    
    let app_data_dir = dirs::config_dir()
        .ok_or_else(|| AppError {
            message: "Could not get app data directory".to_string(),
            code: Some("CONFIG_DIR_ERROR".to_string()),
        })?
        .join("curriculum-curator");
    
    let db_path = app_data_dir.join("sessions.db");
    let db = Database::new(db_path.to_str().unwrap()).await
        .map_err(|e| AppError {
            message: format!("Failed to initialize database: {}", e),
            code: Some("DB_INIT_ERROR".to_string()),
        })?;
    
    let value = db.get_config(&key).await
        .map_err(|e| AppError {
            message: format!("Failed to get config: {}", e),
            code: Some("CONFIG_GET_ERROR".to_string()),
        })?;
    
    Ok(value)
}

#[command]
pub async fn set_app_config(key: String, value: String) -> Result<(), AppError> {
    use crate::database::Database;
    
    let app_data_dir = dirs::config_dir()
        .ok_or_else(|| AppError {
            message: "Could not get app data directory".to_string(),
            code: Some("CONFIG_DIR_ERROR".to_string()),
        })?
        .join("curriculum-curator");
    
    let db_path = app_data_dir.join("sessions.db");
    let mut db = Database::new(db_path.to_str().unwrap()).await
        .map_err(|e| AppError {
            message: format!("Failed to initialize database: {}", e),
            code: Some("DB_INIT_ERROR".to_string()),
        })?;
    
    db.set_config(&key, &value).await
        .map_err(|e| AppError {
            message: format!("Failed to set config: {}", e),
            code: Some("CONFIG_SET_ERROR".to_string()),
        })?;
    
    Ok(())
}


// Validation commands - now properly implemented
#[command]
pub async fn validate_content(
    content: serde_json::Value,
    validator_names: Option<Vec<String>>,
) -> Result<serde_json::Value, AppError> {
    use crate::validation::{ValidationService, commands::ValidateContentRequest};
    use crate::content::GeneratedContent;
    
    // Parse content from JSON
    let generated_content: GeneratedContent = serde_json::from_value(content)
        .map_err(|e| AppError {
            message: format!("Invalid content format: {}", e),
            code: Some("INVALID_CONTENT_FORMAT".to_string()),
        })?;
    
    let request = ValidateContentRequest {
        content: generated_content,
        config: None,
        validator_names,
    };
    
    let validation_service = ValidationService::new();
    let response = validation_service.validate_content(request).await
        .map_err(|e| AppError {
            message: format!("Validation failed: {}", e),
            code: Some("VALIDATION_ERROR".to_string()),
        })?;
    
    serde_json::to_value(response.report)
        .map_err(|e| AppError {
            message: format!("Failed to serialize validation result: {}", e),
            code: Some("SERIALIZATION_ERROR".to_string()),
        })
}

// LLM provider commands
#[command]
pub async fn get_available_providers() -> Result<Vec<serde_json::Value>, AppError> {
    use crate::llm::LLMFactory;
    
    let mut providers = vec![];
    
    // Check Ollama availability
    let ollama_available = LLMFactory::is_ollama_available(None).await;
    providers.push(serde_json::json!({
        "id": "ollama",
        "name": "Local Ollama",
        "type": "Ollama",
        "is_local": true,
        "requires_api_key": false,
        "status": if ollama_available { "available" } else { "not_installed" },
        "base_url": LLMFactory::default_ollama_url()
    }));
    
    // Add other providers (not implemented yet)
    providers.push(serde_json::json!({
        "id": "openai",
        "name": "OpenAI GPT",
        "type": "OpenAI",
        "is_local": false,
        "requires_api_key": true,
        "status": "not_configured"
    }));
    
    providers.push(serde_json::json!({
        "id": "claude",
        "name": "Anthropic Claude",
        "type": "Claude",
        "is_local": false,
        "requires_api_key": true,
        "status": "not_configured"
    }));
    
    providers.push(serde_json::json!({
        "id": "gemini",
        "name": "Google Gemini",
        "type": "Gemini",
        "is_local": false,
        "requires_api_key": true,
        "status": "not_configured"
    }));
    
    Ok(providers)
}

#[command]
pub async fn get_ollama_models() -> Result<Vec<serde_json::Value>, AppError> {
    use crate::llm::{OllamaProvider, LLMProvider};
    use std::sync::Arc;
    
    let provider = Arc::new(OllamaProvider::new(None));
    
    match provider.list_models().await {
        Ok(models) => {
            let model_list: Vec<serde_json::Value> = models.into_iter().map(|model| {
                serde_json::json!({
                    "id": model.id,
                    "name": model.name,
                    "context_length": model.context_length,
                    "supports_streaming": model.capabilities.supports_streaming,
                    "supports_vision": model.capabilities.supports_vision,
                    "max_output_tokens": model.capabilities.max_output_tokens
                })
            }).collect();
            Ok(model_list)
        }
        Err(e) => Err(AppError {
            message: format!("Failed to get Ollama models: {}", e),
            code: Some("OLLAMA_MODELS_ERROR".to_string()),
        })
    }
}

#[command]
pub async fn get_model_recommendations() -> Result<Vec<serde_json::Value>, AppError> {
    use crate::llm::LLMFactory;
    
    let recommendations = LLMFactory::get_recommended_models();
    let recommendation_list: Vec<serde_json::Value> = recommendations.into_iter().map(|rec| {
        serde_json::json!({
            "model_name": rec.model_name,
            "use_case": rec.use_case,
            "size_gb": rec.size_gb,
            "ram_required_gb": rec.ram_required_gb,
            "recommended_for_beginners": rec.recommended_for_beginners
        })
    }).collect();
    
    Ok(recommendation_list)
}

#[command]
pub async fn get_ollama_installation_instructions() -> Result<serde_json::Value, AppError> {
    use crate::llm::OllamaHelper;
    
    let instructions = OllamaHelper::get_installation_instructions();
    Ok(serde_json::json!({
        "linux": instructions.linux,
        "macos": instructions.macos,
        "windows": instructions.windows,
        "post_install": instructions.post_install
    }))
}

#[command]
pub async fn check_system_requirements(available_ram_gb: u32) -> Result<serde_json::Value, AppError> {
    use crate::llm::OllamaHelper;
    
    let requirements = OllamaHelper::check_system_requirements(available_ram_gb);
    let recommended_models: Vec<serde_json::Value> = requirements.recommended_models.into_iter().map(|model| {
        serde_json::json!({
            "model_name": model.model_name,
            "use_case": model.use_case,
            "size_gb": model.size_gb,
            "ram_required_gb": model.ram_required_gb,
            "recommended_for_beginners": model.recommended_for_beginners
        })
    }).collect();
    
    Ok(serde_json::json!({
        "available_ram_gb": requirements.available_ram_gb,
        "recommended_models": recommended_models,
        "can_run_basic_models": requirements.can_run_basic_models,
        "can_run_large_models": requirements.can_run_large_models,
        "warnings": requirements.warnings
    }))
}

#[command]
pub async fn test_llm_generation(
    prompt: String,
    model: Option<String>,
    temperature: Option<f32>
) -> Result<serde_json::Value, AppError> {
    use crate::llm::{LLMFactory, LLMRequest};
    
    // Create a simple LLM manager with Ollama
    let manager = LLMFactory::create_simple().await
        .map_err(|e| AppError {
            message: format!("Failed to initialize LLM manager: {}", e),
            code: Some("LLM_INIT_ERROR".to_string()),
        })?;
    
    // Build the request
    let mut request = LLMRequest::new(prompt);
    if let Some(model) = model {
        request = request.with_model(model);
    }
    if let Some(temp) = temperature {
        request = request.with_temperature(temp);
    }
    
    // Generate response
    match manager.generate(&request).await {
        Ok(response) => {
            Ok(serde_json::json!({
                "success": true,
                "content": response.content,
                "model_used": response.model_used,
                "tokens_used": {
                    "prompt_tokens": response.tokens_used.prompt_tokens,
                    "completion_tokens": response.tokens_used.completion_tokens,
                    "total_tokens": response.tokens_used.total_tokens
                },
                "response_time_ms": response.response_time_ms,
                "finish_reason": format!("{:?}", response.finish_reason)
            }))
        }
        Err(e) => Err(AppError {
            message: format!("LLM generation failed: {}", e),
            code: Some("LLM_GENERATION_ERROR".to_string()),
        })
    }
}

// Cost tracking commands
#[command]
pub async fn get_session_cost(session_id: String) -> Result<f64, AppError> {
    use uuid::Uuid;
    use crate::database::Database;
    
    let session_uuid = Uuid::parse_str(&session_id)
        .map_err(|e| AppError {
            message: format!("Invalid session ID: {}", e),
            code: Some("INVALID_SESSION_ID".to_string()),
        })?;
    
    let app_data_dir = dirs::config_dir()
        .ok_or_else(|| AppError {
            message: "Could not get app data directory".to_string(),
            code: Some("CONFIG_DIR_ERROR".to_string()),
        })?
        .join("curriculum-curator");
    
    let db_path = app_data_dir.join("sessions.db");
    let db = Database::new(db_path.to_str().unwrap()).await
        .map_err(|e| AppError {
            message: format!("Failed to initialize database: {}", e),
            code: Some("DB_INIT_ERROR".to_string()),
        })?;
    
    let cost = db.get_total_cost(Some(session_uuid)).await
        .map_err(|e| AppError {
            message: format!("Failed to get session cost: {}", e),
            code: Some("COST_ERROR".to_string()),
        })?;
    
    Ok(cost)
}

// Export commands
#[command]
pub async fn export_content(
    session_id: String,
    format: String,
    output_path: String,
    include_metadata: Option<bool>,
    template_name: Option<String>,
    branding_options: Option<serde_json::Value>,
) -> Result<serde_json::Value, AppError> {
    use uuid::Uuid;
    use std::path::PathBuf;
    use crate::export::{ExportManager, ExportOptions, ExportFormat, BrandingOptions};
    use crate::database::Database;
    
    let session_uuid = Uuid::parse_str(&session_id)
        .map_err(|e| AppError {
            message: format!("Invalid session ID: {}", e),
            code: Some("INVALID_SESSION_ID".to_string()),
        })?;
    
    // Parse export format
    let export_format = match format.to_lowercase().as_str() {
        "markdown" | "md" => ExportFormat::Markdown,
        "html" => ExportFormat::Html,
        "pdf" => ExportFormat::Pdf,
        "powerpoint" | "pptx" => ExportFormat::PowerPoint,
        "word" | "docx" => ExportFormat::Word,
        _ => {
            return Err(AppError {
                message: format!("Unsupported export format: {}", format),
                code: Some("UNSUPPORTED_FORMAT".to_string()),
            });
        }
    };
    
    // Parse branding options if provided
    let branding = if let Some(branding_json) = branding_options {
        match serde_json::from_value::<BrandingOptions>(branding_json) {
            Ok(branding) => Some(branding),
            Err(e) => {
                return Err(AppError {
                    message: format!("Invalid branding options: {}", e),
                    code: Some("INVALID_BRANDING_OPTIONS".to_string()),
                });
            }
        }
    } else {
        None
    };

    // Create export options
    let options = ExportOptions {
        format: export_format.clone(),
        output_path: PathBuf::from(output_path),
        template_name,
        include_metadata: include_metadata.unwrap_or(true),
        branding_options: branding,
    };
    
    // Get session content from database
    let app_data_dir = dirs::config_dir()
        .ok_or_else(|| AppError {
            message: "Could not get app data directory".to_string(),
            code: Some("CONFIG_DIR_ERROR".to_string()),
        })?
        .join("curriculum-curator");
    
    let db_path = app_data_dir.join("sessions.db");
    let db = Database::new(db_path.to_str().unwrap()).await
        .map_err(|e| AppError {
            message: format!("Failed to initialize database: {}", e),
            code: Some("DB_INIT_ERROR".to_string()),
        })?;
    
    let content = db.get_session_content(session_uuid).await
        .map_err(|e| AppError {
            message: format!("Failed to get session content: {}", e),
            code: Some("SESSION_CONTENT_ERROR".to_string()),
        })?;
    
    if content.is_empty() {
        return Err(AppError {
            message: "No content available to export for this session".to_string(),
            code: Some("NO_CONTENT_ERROR".to_string()),
        });
    }
    
    // Create export manager and perform export
    let export_manager = ExportManager::new();
    
    // Validate export path
    export_manager.validate_export_path(&options.output_path, &export_format)
        .map_err(|e| AppError {
            message: format!("Invalid export path: {}", e),
            code: Some("INVALID_PATH_ERROR".to_string()),
        })?;
    
    // Perform the export
    let export_result = export_manager.export_content(&content, &options).await
        .map_err(|e| AppError {
            message: format!("Export failed: {}", e),
            code: Some("EXPORT_ERROR".to_string()),
        })?;
    
    if export_result.success {
        Ok(serde_json::json!({
            "success": true,
            "output_path": export_result.output_path.to_string_lossy(),
            "file_size": export_result.file_size,
            "format": format,
            "message": format!("Content exported successfully to {} as {}", export_result.output_path.display(), format)
        }))
    } else {
        Err(AppError {
            message: export_result.error_message.unwrap_or_else(|| "Unknown export error".to_string()),
            code: Some("EXPORT_FAILED".to_string()),
        })
    }
}

#[command]
pub async fn get_supported_export_formats() -> Result<Vec<serde_json::Value>, AppError> {
    use crate::export::ExportManager;
    
    let export_manager = ExportManager::new();
    let supported_formats = export_manager.supported_formats();
    
    let format_info = supported_formats.into_iter().map(|format| {
        let extension = export_manager.get_default_extension(&format);
        serde_json::json!({
            "format": format!("{:?}", format),
            "display_name": match format {
                crate::export::ExportFormat::Markdown => "Markdown",
                crate::export::ExportFormat::Html => "HTML",
                crate::export::ExportFormat::Pdf => "PDF",
                crate::export::ExportFormat::PowerPoint => "PowerPoint",
                crate::export::ExportFormat::Word => "Word Document",
                // Quarto formats
                #[cfg(feature = "quarto-integration")]
                crate::export::ExportFormat::QuartoHtml => "Quarto HTML",
                #[cfg(feature = "quarto-integration")]
                crate::export::ExportFormat::QuartoPdf => "Quarto PDF",
                #[cfg(feature = "quarto-integration")]
                crate::export::ExportFormat::QuartoPowerPoint => "Quarto PowerPoint",
                #[cfg(feature = "quarto-integration")]
                crate::export::ExportFormat::QuartoWord => "Quarto Word",
                #[cfg(feature = "quarto-integration")]
                crate::export::ExportFormat::QuartoBook => "Quarto Book",
                #[cfg(feature = "quarto-integration")]
                crate::export::ExportFormat::QuartoWebsite => "Quarto Website",
            },
            "extension": extension,
            "available": match format {
                crate::export::ExportFormat::Markdown => true,
                crate::export::ExportFormat::Html => true,
                crate::export::ExportFormat::Pdf => true,
                crate::export::ExportFormat::PowerPoint => true,
                crate::export::ExportFormat::Word => false, // Not yet implemented
                // Quarto formats depend on Quarto installation
                #[cfg(feature = "quarto-integration")]
                crate::export::ExportFormat::QuartoHtml => crate::export::QuartoConverter::is_available(),
                #[cfg(feature = "quarto-integration")]
                crate::export::ExportFormat::QuartoPdf => crate::export::QuartoConverter::is_available(),
                #[cfg(feature = "quarto-integration")]
                crate::export::ExportFormat::QuartoPowerPoint => crate::export::QuartoConverter::is_available(),
                #[cfg(feature = "quarto-integration")]
                crate::export::ExportFormat::QuartoWord => crate::export::QuartoConverter::is_available(),
                #[cfg(feature = "quarto-integration")]
                crate::export::ExportFormat::QuartoBook => crate::export::QuartoConverter::is_available(),
                #[cfg(feature = "quarto-integration")]
                crate::export::ExportFormat::QuartoWebsite => crate::export::QuartoConverter::is_available(),
            }
        })
    }).collect();
    
    Ok(format_info)
}

#[command]
pub async fn validate_export_path(path: String, format: String) -> Result<bool, AppError> {
    use std::path::PathBuf;
    use crate::export::{ExportManager, ExportFormat};
    
    let export_format = match format.to_lowercase().as_str() {
        "markdown" | "md" => ExportFormat::Markdown,
        "html" => ExportFormat::Html,
        "pdf" => ExportFormat::Pdf,
        "powerpoint" | "pptx" => ExportFormat::PowerPoint,
        "word" | "docx" => ExportFormat::Word,
        _ => {
            return Err(AppError {
                message: format!("Unsupported export format: {}", format),
                code: Some("UNSUPPORTED_FORMAT".to_string()),
            });
        }
    };
    
    let export_manager = ExportManager::new();
    let path_buf = PathBuf::from(path);
    
    match export_manager.validate_export_path(&path_buf, &export_format) {
        Ok(()) => Ok(true),
        Err(_) => Ok(false),
    }
}

// Batch Export Commands
#[command]
pub async fn batch_export_content(
    jobs: Vec<serde_json::Value>,
    options: Option<serde_json::Value>,
) -> Result<serde_json::Value, AppError> {
    use crate::export::{BatchExportJob, BatchExportOptions, BatchExportManager};
    use crate::session::SessionManager;
    
    // Parse batch export jobs
    let batch_jobs: Vec<BatchExportJob> = jobs.into_iter()
        .map(|job_json| serde_json::from_value(job_json))
        .collect::<Result<Vec<_>, _>>()
        .map_err(|e| AppError {
            message: format!("Invalid batch export job format: {}", e),
            code: Some("INVALID_BATCH_JOB".to_string()),
        })?;

    // Parse batch options
    let batch_options = if let Some(options_json) = options {
        serde_json::from_value::<BatchExportOptions>(options_json)
            .map_err(|e| AppError {
                message: format!("Invalid batch export options: {}", e),
                code: Some("INVALID_BATCH_OPTIONS".to_string()),
            })?
    } else {
        BatchExportOptions::default()
    };

    // Initialize session manager
    let app_data_dir = dirs::config_dir()
        .ok_or_else(|| AppError {
            message: "Could not get app data directory".to_string(),
            code: Some("CONFIG_DIR_ERROR".to_string()),
        })?
        .join("curriculum-curator");

    let db_path = app_data_dir.join("sessions.db");
    
    // Create shared database
    use crate::database::Database;
    let shared_db = Database::create_shared(db_path.to_str().unwrap()).await
        .map_err(|e| AppError {
            message: format!("Failed to initialize database: {}", e),
            code: Some("DB_INIT_ERROR".to_string()),
        })?;
    
    let session_manager = SessionManager::new(shared_db);

    // Create batch export manager
    let batch_manager = BatchExportManager::new(session_manager);

    // Execute batch export
    let result = batch_manager.execute_batch_export(batch_jobs, batch_options).await
        .map_err(|e| AppError {
            message: format!("Batch export failed: {}", e),
            code: Some("BATCH_EXPORT_ERROR".to_string()),
        })?;

    // Convert result to JSON
    serde_json::to_value(result)
        .map_err(|e| AppError {
            message: format!("Failed to serialize batch export result: {}", e),
            code: Some("SERIALIZATION_ERROR".to_string()),
        })
}

#[command]
pub async fn create_batch_export_job(
    job_id: String,
    session_ids: Vec<String>,
    formats: Vec<String>,
    output_directory: String,
    naming_strategy: Option<String>,
    merge_sessions: Option<bool>,
    template_name: Option<String>,
    include_metadata: Option<bool>,
    branding_options: Option<serde_json::Value>,
) -> Result<serde_json::Value, AppError> {
    use crate::export::{BatchExportJob, ExportFormat, NamingStrategy, BrandingOptions};
    
    // Parse export formats
    let export_formats: Result<Vec<ExportFormat>, AppError> = formats.into_iter()
        .map(|format_str| {
            match format_str.to_lowercase().as_str() {
                "markdown" | "md" => Ok(ExportFormat::Markdown),
                "html" => Ok(ExportFormat::Html),
                "pdf" => Ok(ExportFormat::Pdf),
                "powerpoint" | "pptx" => Ok(ExportFormat::PowerPoint),
                "word" | "docx" => Ok(ExportFormat::Word),
                #[cfg(feature = "quarto-integration")]
                "quarto-html" => Ok(ExportFormat::QuartoHtml),
                #[cfg(feature = "quarto-integration")]
                "quarto-pdf" => Ok(ExportFormat::QuartoPdf),
                #[cfg(feature = "quarto-integration")]
                "quarto-powerpoint" => Ok(ExportFormat::QuartoPowerPoint),
                #[cfg(feature = "quarto-integration")]
                "quarto-word" => Ok(ExportFormat::QuartoWord),
                #[cfg(feature = "quarto-integration")]
                "quarto-book" => Ok(ExportFormat::QuartoBook),
                #[cfg(feature = "quarto-integration")]
                "quarto-website" => Ok(ExportFormat::QuartoWebsite),
                _ => Err(AppError {
                    message: format!("Unsupported export format: {}", format_str),
                    code: Some("UNSUPPORTED_FORMAT".to_string()),
                }),
            }
        })
        .collect();

    let export_formats = export_formats?;

    // Parse naming strategy
    let naming_strategy = match naming_strategy.as_deref() {
        Some("session") => NamingStrategy::SessionBased,
        Some("content") => NamingStrategy::ContentBased,
        Some("sequential") => NamingStrategy::Sequential,
        Some(custom) if custom.starts_with("custom:") => {
            NamingStrategy::Custom(custom.strip_prefix("custom:").unwrap().to_string())
        },
        _ => NamingStrategy::default(),
    };

    // Parse branding options
    let branding = if let Some(branding_json) = branding_options {
        match serde_json::from_value::<BrandingOptions>(branding_json) {
            Ok(branding) => Some(branding),
            Err(e) => {
                return Err(AppError {
                    message: format!("Invalid branding options: {}", e),
                    code: Some("INVALID_BRANDING_OPTIONS".to_string()),
                });
            }
        }
    } else {
        None
    };

    let job = BatchExportJob {
        job_id,
        session_ids,
        formats: export_formats,
        output_directory: std::path::PathBuf::from(output_directory),
        naming_strategy,
        merge_sessions: merge_sessions.unwrap_or(false),
        template_name,
        include_metadata: include_metadata.unwrap_or(true),
        branding_options: branding,
    };

    serde_json::to_value(job)
        .map_err(|e| AppError {
            message: format!("Failed to serialize batch export job: {}", e),
            code: Some("SERIALIZATION_ERROR".to_string()),
        })
}

// Secure API Key Management Commands
#[command]
pub async fn store_api_key(
    provider: String,
    api_key: String,
    base_url: Option<String>,
    rate_limit: Option<u32>,
) -> Result<(), AppError> {
    use crate::llm::{SecureStorage, ApiKeyConfig, ProviderType};
    
    let provider_type: ProviderType = provider.parse()
        .map_err(|_| AppError {
            message: format!("Invalid provider type: {}", provider),
            code: Some("INVALID_PROVIDER".to_string()),
        })?;
    
    let storage = SecureStorage::new();
    
    // Validate API key format
    storage.validate_api_key_format(&provider_type, &api_key)
        .map_err(|e| AppError {
            message: format!("Invalid API key format: {}", e),
            code: Some("INVALID_API_KEY_FORMAT".to_string()),
        })?;
    
    let mut config = ApiKeyConfig::new(provider_type, api_key);
    
    if let Some(url) = base_url {
        config = config.with_base_url(url);
    }
    
    if let Some(limit) = rate_limit {
        config = config.with_rate_limit(limit);
    }
    
    storage.store_api_key(&config)
        .map_err(|e| AppError {
            message: format!("Failed to store API key: {}", e),
            code: Some("KEYRING_STORE_ERROR".to_string()),
        })?;
    
    Ok(())
}

#[command]
pub async fn get_api_key_config(provider: String) -> Result<serde_json::Value, AppError> {
    use crate::llm::{SecureStorage, ProviderType};
    
    let provider_type: ProviderType = provider.parse()
        .map_err(|_| AppError {
            message: format!("Invalid provider type: {}", provider),
            code: Some("INVALID_PROVIDER".to_string()),
        })?;
    
    let storage = SecureStorage::new();
    
    match storage.get_api_key_config(&provider_type) {
        Ok(config) => {
            // Return config without exposing the actual API key
            let safe_config = serde_json::json!({
                "provider_type": config.provider_type,
                "base_url": config.base_url,
                "model_overrides": config.model_overrides,
                "rate_limit_override": config.rate_limit_override,
                "enabled": config.enabled,
                "has_api_key": !config.api_key.is_empty()
            });
            Ok(safe_config)
        }
        Err(_) => {
            // Return default config if none exists
            let default_config = storage.get_provider_config_with_defaults(&provider_type);
            let safe_config = serde_json::json!({
                "provider_type": default_config.provider_type,
                "base_url": default_config.base_url,
                "model_overrides": default_config.model_overrides,
                "rate_limit_override": default_config.rate_limit_override,
                "enabled": default_config.enabled,
                "has_api_key": false
            });
            Ok(safe_config)
        }
    }
}

#[command]
pub async fn remove_api_key(provider: String) -> Result<(), AppError> {
    use crate::llm::{SecureStorage, ProviderType};
    
    let provider_type: ProviderType = provider.parse()
        .map_err(|_| AppError {
            message: format!("Invalid provider type: {}", provider),
            code: Some("INVALID_PROVIDER".to_string()),
        })?;
    
    let storage = SecureStorage::new();
    
    storage.remove_api_key(&provider_type)
        .map_err(|e| AppError {
            message: format!("Failed to remove API key: {}", e),
            code: Some("KEYRING_REMOVE_ERROR".to_string()),
        })?;
    
    Ok(())
}

#[command]
pub async fn list_configured_providers() -> Result<Vec<String>, AppError> {
    use crate::llm::SecureStorage;
    
    let storage = SecureStorage::new();
    
    let providers = storage.list_configured_providers()
        .map_err(|e| AppError {
            message: format!("Failed to list providers: {}", e),
            code: Some("KEYRING_LIST_ERROR".to_string()),
        })?;
    
    Ok(providers.iter().map(|p| format!("{:?}", p)).collect())
}

#[command]
pub async fn update_provider_config(
    provider: String,
    base_url: Option<String>,
    rate_limit: Option<u32>,
    enabled: Option<bool>,
) -> Result<(), AppError> {
    use crate::llm::{SecureStorage, ProviderType};
    
    let provider_type: ProviderType = provider.parse()
        .map_err(|_| AppError {
            message: format!("Invalid provider type: {}", provider),
            code: Some("INVALID_PROVIDER".to_string()),
        })?;
    
    let storage = SecureStorage::new();
    
    // Get existing config
    let mut config = storage.get_api_key_config(&provider_type)
        .map_err(|e| AppError {
            message: format!("Provider not configured: {}", e),
            code: Some("PROVIDER_NOT_CONFIGURED".to_string()),
        })?;
    
    // Update fields if provided
    if let Some(url) = base_url {
        config.base_url = Some(url);
    }
    
    if let Some(limit) = rate_limit {
        config.rate_limit_override = Some(limit);
    }
    
    if let Some(enable) = enabled {
        config.enabled = enable;
    }
    
    storage.update_api_key_config(&config)
        .map_err(|e| AppError {
            message: format!("Failed to update config: {}", e),
            code: Some("KEYRING_UPDATE_ERROR".to_string()),
        })?;
    
    Ok(())
}

#[command]
pub async fn validate_api_key_format(provider: String, api_key: String) -> Result<bool, AppError> {
    use crate::llm::{SecureStorage, ProviderType};
    
    let provider_type: ProviderType = provider.parse()
        .map_err(|_| AppError {
            message: format!("Invalid provider type: {}", provider),
            code: Some("INVALID_PROVIDER".to_string()),
        })?;
    
    let storage = SecureStorage::new();
    
    match storage.validate_api_key_format(&provider_type, &api_key) {
        Ok(()) => Ok(true),
        Err(_) => Ok(false),
    }
}

#[command]
pub async fn import_api_keys_from_env() -> Result<Vec<String>, AppError> {
    use crate::llm::SecureStorage;
    
    let storage = SecureStorage::new();
    
    let imported = storage.import_from_env()
        .map_err(|e| AppError {
            message: format!("Failed to import from environment: {}", e),
            code: Some("ENV_IMPORT_ERROR".to_string()),
        })?;
    
    Ok(imported.iter().map(|p| format!("{:?}", p)).collect())
}

#[command]
pub async fn export_provider_config_template() -> Result<serde_json::Value, AppError> {
    use crate::llm::SecureStorage;
    
    let storage = SecureStorage::new();
    
    let template = storage.export_config_template()
        .map_err(|e| AppError {
            message: format!("Failed to export template: {}", e),
            code: Some("EXPORT_TEMPLATE_ERROR".to_string()),
        })?;
    
    Ok(serde_json::Value::Object(template.into_iter().collect()))
}

#[command]
pub async fn clear_all_api_keys() -> Result<(), AppError> {
    use crate::llm::SecureStorage;
    
    let storage = SecureStorage::new();
    
    storage.clear_all_api_keys()
        .map_err(|e| AppError {
            message: format!("Failed to clear API keys: {}", e),
            code: Some("KEYRING_CLEAR_ERROR".to_string()),
        })?;
    
    Ok(())
}

// External Provider Testing Commands
#[command]
pub async fn test_external_provider(provider: String) -> Result<serde_json::Value, AppError> {
    use crate::llm::{SecureStorage, LLMFactory, ProviderType, LLMRequest};
    
    let provider_type: ProviderType = provider.parse()
        .map_err(|_| AppError {
            message: format!("Invalid provider type: {}", provider),
            code: Some("INVALID_PROVIDER".to_string()),
        })?;

    let storage = SecureStorage::new();
    
    // Check if API key is configured
    if !storage.has_api_key(&provider_type) {
        return Ok(serde_json::json!({
            "success": false,
            "error": "No API key configured for provider",
            "configured": false
        }));
    }

    // Try to create and test the provider
    match LLMFactory::create_provider_from_config(&storage, provider_type).await {
        Ok(provider_instance) => {
            // Test with a simple health check
            match provider_instance.health_check().await {
                Ok(true) => {
                    // Try a simple generation test
                    let test_request = LLMRequest::new("Say 'Hello' in one word")
                        .with_max_tokens(10);
                    
                    match provider_instance.generate(&test_request).await {
                        Ok(response) => {
                            Ok(serde_json::json!({
                                "success": true,
                                "configured": true,
                                "health_check": true,
                                "generation_test": true,
                                "response_preview": response.content.chars().take(50).collect::<String>(),
                                "model_used": response.model_used,
                                "tokens_used": response.tokens_used.total_tokens,
                                "cost_usd": response.cost_usd
                            }))
                        }
                        Err(e) => {
                            Ok(serde_json::json!({
                                "success": false,
                                "configured": true,
                                "health_check": true,
                                "generation_test": false,
                                "error": e.to_string()
                            }))
                        }
                    }
                }
                Ok(false) => {
                    Ok(serde_json::json!({
                        "success": false,
                        "configured": true,
                        "health_check": false,
                        "error": "Provider health check failed"
                    }))
                }
                Err(e) => {
                    Ok(serde_json::json!({
                        "success": false,
                        "configured": true,
                        "health_check": false,
                        "error": format!("Health check error: {}", e)
                    }))
                }
            }
        }
        Err(e) => {
            Ok(serde_json::json!({
                "success": false,
                "configured": true,
                "error": format!("Failed to create provider: {}", e)
            }))
        }
    }
}

#[command]
pub async fn get_external_provider_models(provider: String) -> Result<Vec<serde_json::Value>, AppError> {
    use crate::llm::{SecureStorage, LLMFactory, ProviderType};
    
    let provider_type: ProviderType = provider.parse()
        .map_err(|_| AppError {
            message: format!("Invalid provider type: {}", provider),
            code: Some("INVALID_PROVIDER".to_string()),
        })?;

    let storage = SecureStorage::new();
    
    if !storage.has_api_key(&provider_type) {
        return Err(AppError {
            message: format!("No API key configured for {}", provider),
            code: Some("PROVIDER_NOT_CONFIGURED".to_string()),
        });
    }

    let provider_instance = LLMFactory::create_provider_from_config(&storage, provider_type).await
        .map_err(|e| AppError {
            message: format!("Failed to create provider: {}", e),
            code: Some("PROVIDER_CREATION_ERROR".to_string()),
        })?;

    let models = provider_instance.list_models().await
        .map_err(|e| AppError {
            message: format!("Failed to list models: {}", e),
            code: Some("MODEL_LIST_ERROR".to_string()),
        })?;

    let model_info = models.into_iter().map(|model| {
        serde_json::json!({
            "id": model.id,
            "name": model.name,
            "description": model.description,
            "context_length": model.context_length,
            "capabilities": {
                "supports_chat": model.capabilities.supports_chat,
                "supports_completion": model.capabilities.supports_completion,
                "supports_function_calling": model.capabilities.supports_function_calling,
                "supports_vision": model.capabilities.supports_vision,
                "max_context_length": model.capabilities.max_context_length,
                "supported_languages": model.capabilities.supported_languages
            }
        })
    }).collect();

    Ok(model_info)
}

#[command]
pub async fn estimate_external_provider_cost(
    provider: String,
    prompt: String,
    model: Option<String>,
    max_tokens: Option<u32>,
) -> Result<serde_json::Value, AppError> {
    use crate::llm::{SecureStorage, LLMFactory, ProviderType, LLMRequest};
    
    let provider_type: ProviderType = provider.parse()
        .map_err(|_| AppError {
            message: format!("Invalid provider type: {}", provider),
            code: Some("INVALID_PROVIDER".to_string()),
        })?;

    let storage = SecureStorage::new();
    
    if !storage.has_api_key(&provider_type) {
        return Err(AppError {
            message: format!("No API key configured for {}", provider),
            code: Some("PROVIDER_NOT_CONFIGURED".to_string()),
        });
    }

    let provider_instance = LLMFactory::create_provider_from_config(&storage, provider_type).await
        .map_err(|e| AppError {
            message: format!("Failed to create provider: {}", e),
            code: Some("PROVIDER_CREATION_ERROR".to_string()),
        })?;

    let mut request = LLMRequest::new(prompt);
    if let Some(m) = model {
        request = request.with_model(m);
    }
    if let Some(tokens) = max_tokens {
        request = request.with_max_tokens(tokens);
    }

    let estimated_cost = provider_instance.estimate_cost(&request).await
        .map_err(|e| AppError {
            message: format!("Failed to estimate cost: {}", e),
            code: Some("COST_ESTIMATION_ERROR".to_string()),
        })?;

    Ok(serde_json::json!({
        "provider": provider,
        "estimated_cost_usd": estimated_cost,
        "request_details": {
            "prompt_length": request.prompt.len(),
            "estimated_input_tokens": request.prompt.len() / 4,
            "max_output_tokens": request.max_tokens.unwrap_or(500)
        }
    }))
}

#[command]
pub async fn setup_provider_from_wizard(
    provider: String,
    api_key: String,
    base_url: Option<String>,
    test_connection: bool,
) -> Result<serde_json::Value, AppError> {
    use crate::llm::{SecureStorage, ApiKeyConfig, ProviderType, LLMFactory};
    
    let provider_type: ProviderType = provider.parse()
        .map_err(|_| AppError {
            message: format!("Invalid provider type: {}", provider),
            code: Some("INVALID_PROVIDER".to_string()),
        })?;

    let storage = SecureStorage::new();

    // Validate API key format
    storage.validate_api_key_format(&provider_type, &api_key)
        .map_err(|e| AppError {
            message: format!("Invalid API key format: {}", e),
            code: Some("INVALID_API_KEY_FORMAT".to_string()),
        })?;

    // Create configuration
    let mut config = ApiKeyConfig::new(provider_type, api_key);
    if let Some(url) = base_url {
        config = config.with_base_url(url);
    }

    // Test connection if requested
    let mut test_result = None;
    if test_connection {
        // Store temporarily to test
        if let Err(e) = storage.store_api_key(&config) {
            return Err(AppError {
                message: format!("Failed to store API key for testing: {}", e),
                code: Some("STORAGE_ERROR".to_string()),
            });
        }

        match LLMFactory::create_provider_from_config(&storage, provider_type).await {
            Ok(provider_instance) => {
                match provider_instance.health_check().await {
                    Ok(true) => {
                        test_result = Some(serde_json::json!({
                            "success": true,
                            "message": "Connection test successful"
                        }));
                    }
                    Ok(false) => {
                        test_result = Some(serde_json::json!({
                            "success": false,
                            "message": "Connection test failed - provider not responding correctly"
                        }));
                    }
                    Err(e) => {
                        test_result = Some(serde_json::json!({
                            "success": false,
                            "message": format!("Connection test error: {}", e)
                        }));
                    }
                }
            }
            Err(e) => {
                test_result = Some(serde_json::json!({
                    "success": false,
                    "message": format!("Failed to create provider for testing: {}", e)
                }));
            }
        }
    } else {
        // Store the configuration
        storage.store_api_key(&config)
            .map_err(|e| AppError {
                message: format!("Failed to store API key: {}", e),
                code: Some("STORAGE_ERROR".to_string()),
            })?;
    }

    Ok(serde_json::json!({
        "provider": provider,
        "configured": true,
        "test_result": test_result
    }))
}

// Offline Capability Commands
#[command]
pub async fn check_connectivity_status() -> Result<serde_json::Value, AppError> {
    use crate::llm::OfflineManager;
    
    let mut offline_manager = OfflineManager::new();
    
    let status = offline_manager.check_connectivity().await
        .map_err(|e| AppError {
            message: format!("Failed to check connectivity: {}", e),
            code: Some("CONNECTIVITY_CHECK_ERROR".to_string()),
        })?;
    
    Ok(serde_json::json!({
        "status": format!("{:?}", status),
        "online": matches!(status, crate::llm::ConnectivityStatus::Online),
        "limited": matches!(status, crate::llm::ConnectivityStatus::Limited),
        "offline": matches!(status, crate::llm::ConnectivityStatus::Offline)
    }))
}

#[command]
pub async fn get_provider_capabilities() -> Result<Vec<serde_json::Value>, AppError> {
    use crate::llm::{OfflineManager, ProviderType};
    
    let mut offline_manager = OfflineManager::new();
    let providers = vec![ProviderType::Ollama, ProviderType::OpenAI, ProviderType::Claude, ProviderType::Gemini];
    
    let mut capabilities = Vec::new();
    
    for provider_type in providers {
        match offline_manager.check_provider_availability(provider_type).await {
            Ok(capability) => {
                capabilities.push(serde_json::json!({
                    "provider_type": format!("{:?}", capability.provider_type),
                    "is_available": capability.is_available,
                    "requires_internet": capability.requires_internet,
                    "can_run_offline": capability.can_run_offline,
                    "status_message": capability.status_message,
                    "last_checked": capability.last_checked.duration_since(std::time::UNIX_EPOCH).unwrap_or_default().as_secs()
                }));
            }
            Err(e) => {
                capabilities.push(serde_json::json!({
                    "provider_type": format!("{:?}", provider_type),
                    "is_available": false,
                    "requires_internet": provider_type != ProviderType::Ollama,
                    "can_run_offline": provider_type == ProviderType::Ollama,
                    "status_message": format!("Error checking provider: {}", e),
                    "last_checked": 0
                }));
            }
        }
    }
    
    Ok(capabilities)
}

#[command]
pub async fn get_available_providers_by_connectivity() -> Result<serde_json::Value, AppError> {
    use crate::llm::OfflineManager;
    
    let mut offline_manager = OfflineManager::new();
    
    let connectivity = offline_manager.check_connectivity().await
        .map_err(|e| AppError {
            message: format!("Failed to check connectivity: {}", e),
            code: Some("CONNECTIVITY_CHECK_ERROR".to_string()),
        })?;
    
    let available_providers = offline_manager.get_available_providers().await
        .map_err(|e| AppError {
            message: format!("Failed to get available providers: {}", e),
            code: Some("PROVIDER_CHECK_ERROR".to_string()),
        })?;
    
    let offline_providers = offline_manager.get_offline_providers();
    
    Ok(serde_json::json!({
        "connectivity_status": format!("{:?}", connectivity),
        "available_providers": available_providers.iter().map(|p| format!("{:?}", p)).collect::<Vec<_>>(),
        "offline_providers": offline_providers.iter().map(|p| format!("{:?}", p)).collect::<Vec<_>>(),
        "has_offline_capability": offline_manager.has_offline_capability().await
    }))
}

#[command]
pub async fn get_offline_setup_recommendations() -> Result<Vec<String>, AppError> {
    use crate::llm::OfflineManager;
    
    let offline_manager = OfflineManager::new();
    let recommendations = offline_manager.get_offline_setup_recommendations();
    
    Ok(recommendations)
}

#[command]
pub async fn get_embedded_model_recommendations() -> Result<Vec<serde_json::Value>, AppError> {
    use crate::llm::EmbeddedLLMRecommendations;
    
    let recommendations = EmbeddedLLMRecommendations::get_model_recommendations();
    let recommendation_list = recommendations.into_iter().map(|rec| {
        serde_json::json!({
            "model_name": rec.model_name,
            "description": rec.description,
            "use_case": rec.use_case,
            "min_ram_gb": rec.min_ram_gb,
            "typical_ram_gb": rec.typical_ram_gb,
            "performance_level": format!("{:?}", rec.performance_level),
            "quality_level": format!("{:?}", rec.quality_level),
            "educational_focus": rec.educational_focus
        })
    }).collect();
    
    Ok(recommendation_list)
}

#[command]
pub async fn get_ollama_setup_instructions() -> Result<Vec<String>, AppError> {
    use crate::llm::EmbeddedLLMRecommendations;
    
    let instructions = EmbeddedLLMRecommendations::get_setup_instructions();
    Ok(instructions)
}

#[command]
pub async fn refresh_provider_capabilities() -> Result<(), AppError> {
    use crate::llm::OfflineManager;
    
    let mut offline_manager = OfflineManager::new();
    
    offline_manager.refresh_all_capabilities().await
        .map_err(|e| AppError {
            message: format!("Failed to refresh capabilities: {}", e),
            code: Some("CAPABILITY_REFRESH_ERROR".to_string()),
        })?;
    
    Ok(())
}

#[command]
pub async fn get_best_available_provider(prefer_offline: bool) -> Result<serde_json::Value, AppError> {
    use crate::llm::LLMFactory;
    
    let manager = LLMFactory::create_simple().await
        .map_err(|e| AppError {
            message: format!("Failed to create LLM manager: {}", e),
            code: Some("LLM_MANAGER_ERROR".to_string()),
        })?;
    
    match manager.get_best_available_provider(prefer_offline).await {
        Ok(provider_type) => {
            let connectivity = manager.get_connectivity_status().await.unwrap_or(crate::llm::ConnectivityStatus::Unknown);
            
            Ok(serde_json::json!({
                "success": true,
                "provider": format!("{:?}", provider_type),
                "connectivity_status": format!("{:?}", connectivity),
                "prefer_offline": prefer_offline
            }))
        }
        Err(e) => {
            Ok(serde_json::json!({
                "success": false,
                "error": e.to_string(),
                "prefer_offline": prefer_offline,
                "recommendations": manager.get_offline_setup_recommendations().await
            }))
        }
    }
}

#[command]
pub async fn test_offline_generation(prompt: String, prefer_offline: bool) -> Result<serde_json::Value, AppError> {
    use crate::llm::{LLMFactory, LLMRequest};
    
    let manager = LLMFactory::create_simple().await
        .map_err(|e| AppError {
            message: format!("Failed to create LLM manager: {}", e),
            code: Some("LLM_MANAGER_ERROR".to_string()),
        })?;
    
    let request = LLMRequest::new(prompt)
        .with_max_tokens(100)
        .with_temperature(0.7);
    
    match manager.generate_with_auto_provider(&request, prefer_offline).await {
        Ok(response) => {
            Ok(serde_json::json!({
                "success": true,
                "content": response.content,
                "model_used": response.model_used,
                "provider_used": "auto-selected",
                "tokens_used": {
                    "prompt_tokens": response.tokens_used.prompt_tokens,
                    "completion_tokens": response.tokens_used.completion_tokens,
                    "total_tokens": response.tokens_used.total_tokens
                },
                "cost_usd": response.cost_usd,
                "response_time_ms": response.response_time_ms,
                "offline_capable": true
            }))
        }
        Err(e) => {
            let connectivity = manager.get_connectivity_status().await.unwrap_or(crate::llm::ConnectivityStatus::Unknown);
            let recommendations = manager.get_offline_setup_recommendations().await;
            
            Ok(serde_json::json!({
                "success": false,
                "error": e.to_string(),
                "connectivity_status": format!("{:?}", connectivity),
                "prefer_offline": prefer_offline,
                "recommendations": recommendations
            }))
        }
    }
}