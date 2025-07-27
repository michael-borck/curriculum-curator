use keyring::Entry;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use thiserror::Error;

use crate::llm::{ProviderType, LLMError, RecommendationPriority};

/// Errors that can occur during secure storage operations
#[derive(Error, Debug)]
pub enum SecureStorageError {
    #[error("Keyring error: {0}")]
    KeyringError(#[from] keyring::Error),
    #[error("Serialization error: {0}")]
    SerializationError(#[from] serde_json::Error),
    #[error("API key not found for provider: {0:?}")]
    KeyNotFound(ProviderType),
    #[error("Invalid API key format for provider: {0:?}")]
    InvalidKeyFormat(ProviderType),
}

impl From<SecureStorageError> for LLMError {
    fn from(error: SecureStorageError) -> Self {
        LLMError::Auth(error.to_string())
    }
}

/// Configuration for API keys and provider settings
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ApiKeyConfig {
    pub provider_type: ProviderType,
    pub api_key: String,
    pub base_url: Option<String>,
    pub model_overrides: HashMap<String, String>,
    pub rate_limit_override: Option<u32>,
    pub enabled: bool,
}

impl ApiKeyConfig {
    pub fn new(provider_type: ProviderType, api_key: String) -> Self {
        Self {
            provider_type,
            api_key,
            base_url: None,
            model_overrides: HashMap::new(),
            rate_limit_override: None,
            enabled: true,
        }
    }

    pub fn with_base_url(mut self, base_url: String) -> Self {
        self.base_url = Some(base_url);
        self
    }

    pub fn with_rate_limit(mut self, rate_limit: u32) -> Self {
        self.rate_limit_override = Some(rate_limit);
        self
    }

    pub fn enabled(mut self, enabled: bool) -> Self {
        self.enabled = enabled;
        self
    }
}

/// Secure storage manager for API keys and provider configurations
pub struct SecureStorage {
    service_name: String,
}

impl SecureStorage {
    pub fn new() -> Self {
        Self {
            service_name: "curriculum-curator".to_string(),
        }
    }

    pub fn new_with_service(service_name: String) -> Self {
        Self { service_name }
    }

    /// Store an API key securely in the system keyring
    pub fn store_api_key(&self, config: &ApiKeyConfig) -> Result<(), SecureStorageError> {
        let key_name = self.get_key_name(&config.provider_type);
        let entry = Entry::new(&self.service_name, &key_name)?;
        
        // Serialize the entire config (not just the key) for more flexibility
        let config_json = serde_json::to_string(config)?;
        entry.set_password(&config_json)?;
        
        Ok(())
    }

    /// Retrieve an API key configuration from the system keyring
    pub fn get_api_key_config(&self, provider_type: &ProviderType) -> Result<ApiKeyConfig, SecureStorageError> {
        let key_name = self.get_key_name(provider_type);
        let entry = Entry::new(&self.service_name, &key_name)?;
        
        let config_json = entry.get_password()
            .map_err(|e| match e {
                keyring::Error::NoEntry => SecureStorageError::KeyNotFound(*provider_type),
                other => SecureStorageError::KeyringError(other),
            })?;
        
        let config: ApiKeyConfig = serde_json::from_str(&config_json)?;
        Ok(config)
    }

    /// Get just the API key (for backwards compatibility)
    pub fn get_api_key(&self, provider_type: &ProviderType) -> Result<String, SecureStorageError> {
        let config = self.get_api_key_config(provider_type)?;
        Ok(config.api_key)
    }

    /// Remove an API key from the system keyring
    pub fn remove_api_key(&self, provider_type: &ProviderType) -> Result<(), SecureStorageError> {
        let key_name = self.get_key_name(provider_type);
        let entry = Entry::new(&self.service_name, &key_name)?;
        
        entry.delete_credential()
            .map_err(|e| match e {
                keyring::Error::NoEntry => SecureStorageError::KeyNotFound(*provider_type),
                other => SecureStorageError::KeyringError(other),
            })?;
        
        Ok(())
    }

    /// Check if an API key exists for a provider
    pub fn has_api_key(&self, provider_type: &ProviderType) -> bool {
        self.get_api_key_config(provider_type).is_ok()
    }

    /// List all providers that have stored API keys
    pub fn list_configured_providers(&self) -> Result<Vec<ProviderType>, SecureStorageError> {
        let mut providers = Vec::new();
        
        // Check each known provider type
        for provider_type in [ProviderType::OpenAI, ProviderType::Claude, ProviderType::Gemini, ProviderType::Ollama] {
            if self.has_api_key(&provider_type) {
                providers.push(provider_type);
            }
        }
        
        Ok(providers)
    }

    /// Update an existing API key configuration
    pub fn update_api_key_config(&self, config: &ApiKeyConfig) -> Result<(), SecureStorageError> {
        // Check if key exists first
        if !self.has_api_key(&config.provider_type) {
            return Err(SecureStorageError::KeyNotFound(config.provider_type));
        }
        
        // Store the updated config
        self.store_api_key(config)
    }

    /// Validate an API key format for a specific provider
    pub fn validate_api_key_format(&self, provider_type: &ProviderType, api_key: &str) -> Result<(), SecureStorageError> {
        let is_valid = match provider_type {
            ProviderType::OpenAI => {
                // OpenAI keys start with "sk-" and are typically 51 characters
                api_key.starts_with("sk-") && api_key.len() >= 20
            }
            ProviderType::Claude => {
                // Anthropic keys typically start with "sk-ant-"
                api_key.starts_with("sk-ant-") && api_key.len() >= 20
            }
            ProviderType::Gemini => {
                // Google API keys are typically 39 characters
                api_key.len() >= 20 && !api_key.contains(' ')
            }
            ProviderType::Ollama => {
                // Ollama typically doesn't use API keys (local), but allow any format
                true
            }
        };

        if !is_valid {
            return Err(SecureStorageError::InvalidKeyFormat(*provider_type));
        }

        Ok(())
    }

    /// Get provider-specific configuration with sensible defaults
    pub fn get_provider_config_with_defaults(&self, provider_type: &ProviderType) -> ApiKeyConfig {
        // Try to get stored config first
        if let Ok(config) = self.get_api_key_config(provider_type) {
            return config;
        }

        // Return default config if none exists
        let default_config = match provider_type {
            ProviderType::OpenAI => ApiKeyConfig {
                provider_type: *provider_type,
                api_key: String::new(),
                base_url: Some("https://api.openai.com/v1".to_string()),
                model_overrides: HashMap::new(),
                rate_limit_override: Some(3000), // 3000 requests per minute
                enabled: false,
            },
            ProviderType::Claude => ApiKeyConfig {
                provider_type: *provider_type,
                api_key: String::new(),
                base_url: Some("https://api.anthropic.com".to_string()),
                model_overrides: HashMap::new(),
                rate_limit_override: Some(1000), // Conservative rate limit
                enabled: false,
            },
            ProviderType::Gemini => ApiKeyConfig {
                provider_type: *provider_type,
                api_key: String::new(),
                base_url: Some("https://generativelanguage.googleapis.com/v1beta".to_string()),
                model_overrides: HashMap::new(),
                rate_limit_override: Some(1500),
                enabled: false,
            },
            ProviderType::Ollama => ApiKeyConfig {
                provider_type: *provider_type,
                api_key: String::new(), // Ollama doesn't typically use API keys
                base_url: Some("http://localhost:11434".to_string()),
                model_overrides: HashMap::new(),
                rate_limit_override: None, // No rate limit for local
                enabled: true, // Default enabled for local provider
            },
        };

        default_config
    }

    /// Helper method to create standardized key names
    fn get_key_name(&self, provider_type: &ProviderType) -> String {
        format!("llm_provider_{:?}", provider_type).to_lowercase()
    }

    /// Clear all stored API keys (useful for reset/logout)
    pub fn clear_all_api_keys(&self) -> Result<(), SecureStorageError> {
        let providers = self.list_configured_providers()?;
        
        for provider_type in providers {
            if let Err(e) = self.remove_api_key(&provider_type) {
                tracing::warn!("Failed to remove API key for {:?}: {}", provider_type, e);
            }
        }
        
        Ok(())
    }

    /// Import API keys from environment variables (for development/CI)
    pub fn import_from_env(&self) -> Result<Vec<ProviderType>, SecureStorageError> {
        let mut imported = Vec::new();

        let env_mappings = [
            ("OPENAI_API_KEY", ProviderType::OpenAI),
            ("ANTHROPIC_API_KEY", ProviderType::Claude),
            ("GOOGLE_API_KEY", ProviderType::Gemini),
        ];

        for (env_var, provider_type) in env_mappings {
            if let Ok(api_key) = std::env::var(env_var) {
                if !api_key.is_empty() {
                    let config = ApiKeyConfig::new(provider_type, api_key);
                    if let Err(e) = self.store_api_key(&config) {
                        tracing::warn!("Failed to import {} from environment: {}", env_var, e);
                    } else {
                        imported.push(provider_type);
                        tracing::info!("Imported API key for {:?} from environment", provider_type);
                    }
                }
            }
        }

        Ok(imported)
    }

    /// Export configuration for backup (without sensitive data)
    pub fn export_config_template(&self) -> Result<HashMap<String, serde_json::Value>, SecureStorageError> {
        let mut template = HashMap::new();
        
        let providers = self.list_configured_providers()?;
        for provider_type in providers {
            if let Ok(config) = self.get_api_key_config(&provider_type) {
                let safe_config = serde_json::json!({
                    "provider_type": config.provider_type,
                    "base_url": config.base_url,
                    "model_overrides": config.model_overrides,
                    "rate_limit_override": config.rate_limit_override,
                    "enabled": config.enabled,
                    "has_api_key": !config.api_key.is_empty()
                });
                template.insert(format!("{:?}", provider_type), safe_config);
            }
        }
        
        Ok(template)
    }

    /// Verify API key is still valid by making a test request
    pub async fn verify_api_key(&self, provider_type: &ProviderType) -> Result<bool, SecureStorageError> {
        if !self.has_api_key(provider_type) {
            return Err(SecureStorageError::KeyNotFound(*provider_type));
        }

        // For educational privacy, we'll implement a simple format check
        // In production, this could make actual API calls to verify
        let config = self.get_api_key_config(provider_type)?;
        self.validate_api_key_format(provider_type, &config.api_key)?;
        
        // Simple validation - check if key follows expected pattern
        let is_likely_valid = match provider_type {
            ProviderType::OpenAI => config.api_key.len() >= 40 && config.api_key.starts_with("sk-"),
            ProviderType::Claude => config.api_key.len() >= 40 && config.api_key.starts_with("sk-ant-"),
            ProviderType::Gemini => config.api_key.len() >= 30 && !config.api_key.contains(' '),
            ProviderType::Ollama => true, // Local provider, always valid
        };

        Ok(is_likely_valid)
    }

    /// Get usage recommendations for cost-conscious educators
    pub fn get_cost_recommendations(&self) -> Result<Vec<CostRecommendation>, SecureStorageError> {
        let mut recommendations = Vec::new();
        let configured_providers = self.list_configured_providers()?;

        // Always recommend local Ollama first for cost savings
        if !configured_providers.contains(&ProviderType::Ollama) {
            recommendations.push(CostRecommendation {
                priority: RecommendationPriority::High,
                title: "Set up local Ollama for free content generation".to_string(),
                description: "Ollama provides free, local LLM models perfect for educational content. No API costs and complete privacy.".to_string(),
                estimated_savings: EstimatedSavings::Percentage(100), // 100% savings vs paid APIs
                setup_complexity: SetupComplexity::Easy,
            });
        }

        // If multiple paid providers are configured, recommend prioritization
        let paid_providers: Vec<_> = configured_providers.iter()
            .filter(|&&p| p != ProviderType::Ollama)
            .collect();

        if paid_providers.len() > 1 {
            recommendations.push(CostRecommendation {
                priority: RecommendationPriority::Medium,
                title: "Optimize provider selection for different content types".to_string(),
                description: "Use cheaper providers for simple content (worksheets, quizzes) and premium providers only for complex materials.".to_string(),
                estimated_savings: EstimatedSavings::Percentage(40),
                setup_complexity: SetupComplexity::Medium,
            });
        }

        // Recommend budget tracking
        if !configured_providers.is_empty() {
            recommendations.push(CostRecommendation {
                priority: RecommendationPriority::Low,
                title: "Set up usage monitoring and budget alerts".to_string(),
                description: "Track your API usage to avoid unexpected costs and optimize your content generation workflow.".to_string(),
                estimated_savings: EstimatedSavings::DollarsPerMonth(20.0),
                setup_complexity: SetupComplexity::Easy,
            });
        }

        Ok(recommendations)
    }

    /// Educational-specific validation for API keys
    pub fn validate_for_educational_use(&self, provider_type: &ProviderType) -> Result<EducationalValidation, SecureStorageError> {
        let _config = self.get_api_key_config(provider_type)?;
        
        let mut validation = EducationalValidation {
            is_valid: true,
            privacy_level: PrivacyLevel::Unknown,
            cost_level: CostLevel::Unknown,
            recommended_for_education: false,
            warnings: Vec::new(),
            suggestions: Vec::new(),
        };

        match provider_type {
            ProviderType::Ollama => {
                validation.privacy_level = PrivacyLevel::High; // Local processing
                validation.cost_level = CostLevel::Free;
                validation.recommended_for_education = true;
                validation.suggestions.push("Perfect for educational use - completely free and private".to_string());
            }
            ProviderType::OpenAI => {
                validation.privacy_level = PrivacyLevel::Low; // Data sent to OpenAI
                validation.cost_level = CostLevel::Medium;
                validation.recommended_for_education = false;
                validation.warnings.push("Content is sent to OpenAI servers - consider privacy implications".to_string());
                validation.suggestions.push("Review OpenAI's data usage policies for educational content".to_string());
            }
            ProviderType::Claude => {
                validation.privacy_level = PrivacyLevel::Medium; // Anthropic has educational-friendly policies
                validation.cost_level = CostLevel::Medium;
                validation.recommended_for_education = true;
                validation.suggestions.push("Anthropic has educational-friendly data policies".to_string());
            }
            ProviderType::Gemini => {
                validation.privacy_level = PrivacyLevel::Low; // Google services
                validation.cost_level = CostLevel::Low;
                validation.recommended_for_education = false;
                validation.warnings.push("Google may use data for service improvement".to_string());
            }
        }

        // Check for cost concerns
        if validation.cost_level != CostLevel::Free {
            validation.warnings.push("This provider has usage costs - monitor your spending".to_string());
        }

        Ok(validation)
    }

    /// Get security recommendations for the current setup
    pub fn get_security_recommendations(&self) -> Result<Vec<SecurityRecommendation>, SecureStorageError> {
        let mut recommendations = Vec::new();
        let configured_providers = self.list_configured_providers()?;

        // Check if user has any paid providers when free options are available
        let has_ollama = configured_providers.contains(&ProviderType::Ollama);
        let has_paid_providers = configured_providers.iter().any(|&p| p != ProviderType::Ollama);

        if has_paid_providers && !has_ollama {
            recommendations.push(SecurityRecommendation {
                severity: SecuritySeverity::Info,
                title: "Consider local processing for sensitive content".to_string(),
                description: "For maximum privacy, use local Ollama models for sensitive educational content.".to_string(),
                action_required: false,
            });
        }

        // Check for multiple API keys (potential security risk)
        if configured_providers.len() > 2 {
            recommendations.push(SecurityRecommendation {
                severity: SecuritySeverity::Low,
                title: "Multiple API providers configured".to_string(),
                description: "Having many API keys increases your attack surface. Consider using only the providers you actively need.".to_string(),
                action_required: false,
            });
        }

        // Always recommend reviewing permissions
        recommendations.push(SecurityRecommendation {
            severity: SecuritySeverity::Info,
            title: "Regularly review and rotate API keys".to_string(),
            description: "Best practice: rotate API keys periodically and revoke unused keys from provider dashboards.".to_string(),
            action_required: false,
        });

        Ok(recommendations)
    }
}

impl Default for SecureStorage {
    fn default() -> Self {
        Self::new()
    }
}

/// Educational-specific recommendation for cost optimization
#[derive(Debug, Clone)]
pub struct CostRecommendation {
    pub priority: RecommendationPriority,
    pub title: String,
    pub description: String,
    pub estimated_savings: EstimatedSavings,
    pub setup_complexity: SetupComplexity,
}


#[derive(Debug, Clone)]
pub enum EstimatedSavings {
    Percentage(u32),
    DollarsPerMonth(f64),
}

#[derive(Debug, Clone)]
pub enum SetupComplexity {
    Easy,
    Medium,
    Advanced,
}

/// Educational validation result for API providers
#[derive(Debug, Clone)]
pub struct EducationalValidation {
    pub is_valid: bool,
    pub privacy_level: PrivacyLevel,
    pub cost_level: CostLevel,
    pub recommended_for_education: bool,
    pub warnings: Vec<String>,
    pub suggestions: Vec<String>,
}

#[derive(Debug, Clone, PartialEq)]
pub enum PrivacyLevel {
    High,    // Local processing, no data leaves device
    Medium,  // Some data sharing with educational-friendly policies
    Low,     // Data sent to commercial services
    Unknown,
}

#[derive(Debug, Clone, PartialEq)]
pub enum CostLevel {
    Free,
    Low,     // Under $0.01 per 1K tokens
    Medium,  // $0.01-$0.05 per 1K tokens
    High,    // Over $0.05 per 1K tokens
    Unknown,
}

/// Security recommendation for the current setup
#[derive(Debug, Clone)]
pub struct SecurityRecommendation {
    pub severity: SecuritySeverity,
    pub title: String,
    pub description: String,
    pub action_required: bool,
}

#[derive(Debug, Clone)]
pub enum SecuritySeverity {
    Info,
    Low,
    Medium,
    High,
    Critical,
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_api_key_validation() {
        let storage = SecureStorage::new();
        
        // Test OpenAI key validation
        assert!(storage.validate_api_key_format(&ProviderType::OpenAI, "sk-1234567890abcdef1234567890abcdef").is_ok());
        assert!(storage.validate_api_key_format(&ProviderType::OpenAI, "invalid").is_err());
        
        // Test Claude key validation
        assert!(storage.validate_api_key_format(&ProviderType::Claude, "sk-ant-1234567890abcdef").is_ok());
        assert!(storage.validate_api_key_format(&ProviderType::Claude, "sk-1234").is_err());
        
        // Test Ollama (should always pass)
        assert!(storage.validate_api_key_format(&ProviderType::Ollama, "anything").is_ok());
    }

    #[test]
    fn test_config_creation() {
        let config = ApiKeyConfig::new(ProviderType::OpenAI, "test-key".to_string())
            .with_base_url("https://custom.api.com".to_string())
            .with_rate_limit(1000)
            .enabled(false);
        
        assert_eq!(config.provider_type, ProviderType::OpenAI);
        assert_eq!(config.api_key, "test-key");
        assert_eq!(config.base_url.unwrap(), "https://custom.api.com");
        assert_eq!(config.rate_limit_override.unwrap(), 1000);
        assert!(!config.enabled);
    }
}