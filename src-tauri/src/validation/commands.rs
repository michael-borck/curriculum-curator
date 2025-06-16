use super::factory::ValidatorFactory;
use super::validators::ValidationConfig;
use super::manager::{ValidationReport, ValidationProgress};
use crate::content::{GeneratedContent, ContentType};
use anyhow::Result;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::sync::Arc;
use tokio::sync::{Mutex, mpsc};
use uuid::Uuid;

/// Validation service for managing validation operations
pub struct ValidationService {
    active_validations: Arc<Mutex<HashMap<Uuid, ValidationSession>>>,
}

/// Active validation session
struct ValidationSession {
    content: GeneratedContent,
    config: ValidationConfig,
    progress_receiver: mpsc::UnboundedReceiver<ValidationProgress>,
}

/// Request to start validation
#[derive(Debug, Deserialize)]
pub struct ValidateContentRequest {
    pub content: GeneratedContent,
    pub config: Option<ValidationConfig>,
    pub validator_names: Option<Vec<String>>,
}

/// Response from validation request
#[derive(Debug, Serialize)]
pub struct ValidateContentResponse {
    pub session_id: Uuid,
    pub report: ValidationReport,
}

/// Request to get validation progress
#[derive(Debug, Deserialize)]
pub struct GetValidationProgressRequest {
    pub session_id: Uuid,
}

/// Response with validation progress
#[derive(Debug, Serialize)]
pub struct GetValidationProgressResponse {
    pub progress: Option<ValidationProgress>,
    pub completed: bool,
}

/// Request to list available validators
#[derive(Debug, Deserialize)]
pub struct ListValidatorsRequest;

/// Response with available validators
#[derive(Debug, Serialize)]
pub struct ListValidatorsResponse {
    pub validators: Vec<super::validators::ValidatorPlugin>,
}

/// Request to get validation config for content type
#[derive(Debug, Deserialize)]
pub struct GetValidationConfigRequest {
    pub content_type: ContentType,
    pub validation_level: Option<ValidationLevel>,
}

/// Validation levels
#[derive(Debug, Deserialize)]
pub enum ValidationLevel {
    Minimal,
    Standard,
    Comprehensive,
}

/// Response with validation config
#[derive(Debug, Serialize)]
pub struct GetValidationConfigResponse {
    pub config: ValidationConfig,
}

/// Request to auto-fix validation issues
#[derive(Debug, Deserialize)]
pub struct AutoFixRequest {
    pub content: GeneratedContent,
    pub report: ValidationReport,
    pub config: ValidationConfig,
}

/// Response with auto-fix suggestions
#[derive(Debug, Serialize)]
pub struct AutoFixResponse {
    pub fixes: Vec<String>,
    pub success: bool,
}

impl ValidationService {
    pub fn new() -> Self {
        Self {
            active_validations: Arc::new(Mutex::new(HashMap::new())),
        }
    }

    /// Validate content and return session ID for progress tracking
    pub async fn validate_content(
        &self,
        request: ValidateContentRequest,
    ) -> Result<ValidateContentResponse> {
        let session_id = Uuid::new_v4();
        
        // Create validation config
        let config = request.config.unwrap_or_else(|| {
            match request.validator_names {
                Some(ref names) if !names.is_empty() => {
                    let mut config = ValidationConfig::default();
                    config.enabled_validators = names.clone();
                    config
                }
                _ => ValidatorFactory::create_content_type_config(request.content.content_type.clone()),
            }
        });

        // Create validation manager
        let manager = if let Some(validator_names) = &request.validator_names {
            let names: Vec<&str> = validator_names.iter().map(|s| s.as_str()).collect();
            ValidatorFactory::create_custom_manager(&names)?
        } else {
            ValidatorFactory::create_default_manager()?
        };

        // Set up progress tracking
        let (progress_sender, progress_receiver) = mpsc::unbounded_channel();
        let manager_with_progress = manager.with_progress_tracking(progress_sender);

        // Store session
        {
            let mut sessions = self.active_validations.lock().await;
            sessions.insert(session_id, ValidationSession {
                content: request.content.clone(),
                config: config.clone(),
                progress_receiver,
            });
        }

        // Run validation
        let report = manager_with_progress
            .validate_content(&request.content, &config)
            .await?;

        Ok(ValidateContentResponse { session_id, report })
    }

    /// Get validation progress for a session
    pub async fn get_validation_progress(
        &self,
        request: GetValidationProgressRequest,
    ) -> Result<GetValidationProgressResponse> {
        let sessions = self.active_validations.lock().await;
        
        if let Some(_session) = sessions.get(&request.session_id) {
            // For now, return completed since we run validation synchronously
            // In a real implementation, this would check the progress receiver
            Ok(GetValidationProgressResponse {
                progress: None,
                completed: true,
            })
        } else {
            Ok(GetValidationProgressResponse {
                progress: None,
                completed: true,
            })
        }
    }

    /// List available validators
    pub async fn list_validators(
        &self,
        _request: ListValidatorsRequest,
    ) -> Result<ListValidatorsResponse> {
        let validators = ValidatorFactory::get_available_validators();
        Ok(ListValidatorsResponse { validators })
    }

    /// Get validation config for content type
    pub async fn get_validation_config(
        &self,
        request: GetValidationConfigRequest,
    ) -> Result<GetValidationConfigResponse> {
        let config = match request.validation_level {
            Some(ValidationLevel::Minimal) => ValidatorFactory::create_minimal_config(),
            Some(ValidationLevel::Comprehensive) => ValidatorFactory::create_comprehensive_config(),
            Some(ValidationLevel::Standard) | None => {
                ValidatorFactory::create_content_type_config(request.content_type)
            }
        };

        Ok(GetValidationConfigResponse { config })
    }

    /// Auto-fix validation issues
    pub async fn auto_fix_issues(
        &self,
        request: AutoFixRequest,
    ) -> Result<AutoFixResponse> {
        let manager = ValidatorFactory::create_default_manager()?;
        
        let fixes = manager
            .auto_fix_issues(&request.content, &request.report, &request.config)
            .await?;

        Ok(AutoFixResponse {
            success: !fixes.is_empty(),
            fixes,
        })
    }

    /// Clean up completed validation sessions
    pub async fn cleanup_sessions(&self) {
        let mut sessions = self.active_validations.lock().await;
        // For now, keep all sessions. In production, implement proper cleanup logic
        sessions.clear();
    }
}

impl Default for ValidationService {
    fn default() -> Self {
        Self::new()
    }
}

// Tauri command wrappers
#[tauri::command]
pub async fn validate_content_command(
    service: tauri::State<'_, ValidationService>,
    request: ValidateContentRequest,
) -> Result<ValidateContentResponse, String> {
    service
        .validate_content(request)
        .await
        .map_err(|e| e.to_string())
}

#[tauri::command]
pub async fn get_validation_progress_command(
    service: tauri::State<'_, ValidationService>,
    request: GetValidationProgressRequest,
) -> Result<GetValidationProgressResponse, String> {
    service
        .get_validation_progress(request)
        .await
        .map_err(|e| e.to_string())
}

#[tauri::command]
pub async fn list_validators_command(
    service: tauri::State<'_, ValidationService>,
    request: ListValidatorsRequest,
) -> Result<ListValidatorsResponse, String> {
    service
        .list_validators(request)
        .await
        .map_err(|e| e.to_string())
}

#[tauri::command]
pub async fn get_validation_config_command(
    service: tauri::State<'_, ValidationService>,
    request: GetValidationConfigRequest,
) -> Result<GetValidationConfigResponse, String> {
    service
        .get_validation_config(request)
        .await
        .map_err(|e| e.to_string())
}

#[tauri::command]
pub async fn auto_fix_issues_command(
    service: tauri::State<'_, ValidationService>,
    request: AutoFixRequest,
) -> Result<AutoFixResponse, String> {
    service
        .auto_fix_issues(request)
        .await
        .map_err(|e| e.to_string())
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::content::generator::ContentMetadata;

    fn create_test_content() -> GeneratedContent {
        GeneratedContent {
            content_type: ContentType::Slides,
            title: "Test Content".to_string(),
            content: "# Title\n## Learning Objectives\n- Learn something\n## Content\nSome content\n## Summary\nSummary".to_string(),
            metadata: ContentMetadata {
                word_count: 15,
                estimated_duration: "5 minutes".to_string(),
                difficulty_level: "Beginner".to_string(),
            },
        }
    }

    #[tokio::test]
    async fn test_validate_content_service() {
        let service = ValidationService::new();
        let request = ValidateContentRequest {
            content: create_test_content(),
            config: None,
            validator_names: Some(vec!["structure".to_string()]),
        };

        let response = service.validate_content(request).await.unwrap();
        assert!(!response.report.validator_results.is_empty());
    }

    #[tokio::test]
    async fn test_list_validators_service() {
        let service = ValidationService::new();
        let request = ListValidatorsRequest;

        let response = service.list_validators(request).await.unwrap();
        assert_eq!(response.validators.len(), 4);
    }

    #[tokio::test]
    async fn test_get_validation_config_service() {
        let service = ValidationService::new();
        let request = GetValidationConfigRequest {
            content_type: ContentType::Slides,
            validation_level: Some(ValidationLevel::Comprehensive),
        };

        let response = service.get_validation_config(request).await.unwrap();
        assert!(response.config.enabled_validators.len() >= 3);
    }
}