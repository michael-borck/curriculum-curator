use crate::llm::{
    LLMManager, OllamaProvider, OpenAIProvider, ClaudeProvider, GeminiProvider, 
    LLMProvider, ProviderType, LLMResult, LLMError, SecureStorage
};
use std::sync::Arc;

/// Factory for creating and configuring LLM managers with different provider setups
pub struct LLMFactory;

impl LLMFactory {
    /// Create a new LLM manager with just Ollama (simple setup for basic users)
    pub async fn create_simple() -> LLMResult<LLMManager> {
        let mut manager = LLMManager::new();
        
        // Add Ollama as the default local provider
        let ollama_provider = Arc::new(OllamaProvider::new(None));
        
        // Check if Ollama is available
        match ollama_provider.health_check().await {
            Ok(true) => {
                manager.add_provider(ollama_provider).await;
                manager.set_default_provider(ProviderType::Ollama)?;
                Ok(manager)
            }
            Ok(false) => {
                Err(LLMError::Config("Ollama is not responding properly".to_string()))
            }
            Err(e) => {
                // Still add the provider but warn that it's not available
                manager.add_provider(ollama_provider).await;
                manager.set_default_provider(ProviderType::Ollama)?;
                
                tracing::warn!("Ollama provider added but not available: {}", e);
                Ok(manager)
            }
        }
    }

    /// Create a new LLM manager with custom Ollama configuration
    pub async fn create_with_ollama(base_url: Option<String>) -> LLMResult<LLMManager> {
        let mut manager = LLMManager::new();
        
        let ollama_provider = Arc::new(OllamaProvider::new(base_url));
        manager.add_provider(ollama_provider).await;
        manager.set_default_provider(ProviderType::Ollama)?;
        
        Ok(manager)
    }

    /// Create an empty LLM manager for custom configuration
    pub fn create_empty() -> LLMManager {
        LLMManager::new()
    }

    /// Create an LLM manager with all available providers (advanced setup)
    pub async fn create_with_all_providers() -> LLMResult<LLMManager> {
        let mut manager = LLMManager::new();
        let storage = SecureStorage::new();

        // Always add Ollama (local provider)
        let ollama_provider = Arc::new(OllamaProvider::new(None));
        manager.add_provider(ollama_provider).await;

        // Add external providers if API keys are available
        let configured_providers = storage.list_configured_providers()
            .unwrap_or_else(|_| vec![]);

        for provider_type in configured_providers {
            match Self::create_provider_from_config(&storage, provider_type).await {
                Ok(provider) => {
                    manager.add_provider(provider).await;
                    tracing::info!("Added provider: {:?}", provider_type);
                }
                Err(e) => {
                    tracing::warn!("Failed to add provider {:?}: {}", provider_type, e);
                }
            }
        }

        // Set default provider preference: Ollama > OpenAI > Claude > Gemini
        let provider_preference = [ProviderType::Ollama, ProviderType::OpenAI, ProviderType::Claude, ProviderType::Gemini];
        for preferred in provider_preference {
            if manager.get_provider(&preferred).is_some() {
                manager.set_default_provider(preferred)?;
                break;
            }
        }

        Ok(manager)
    }

    /// Create a specific external provider from stored configuration
    pub async fn create_provider_from_config(
        storage: &SecureStorage,
        provider_type: ProviderType,
    ) -> LLMResult<Arc<dyn LLMProvider>> {
        let config = storage.get_api_key_config(&provider_type)
            .map_err(|e| LLMError::Config(format!("No configuration for {:?}: {}", provider_type, e)))?;

        if !config.enabled {
            return Err(LLMError::Config(format!("Provider {:?} is disabled", provider_type)));
        }

        if config.api_key.is_empty() {
            return Err(LLMError::Auth(format!("No API key configured for {:?}", provider_type)));
        }

        let provider: Arc<dyn LLMProvider> = match provider_type {
            ProviderType::Ollama => {
                Arc::new(OllamaProvider::new(config.base_url))
            }
            ProviderType::OpenAI => {
                Arc::new(OpenAIProvider::new(config.api_key, config.base_url))
            }
            ProviderType::Claude => {
                Arc::new(ClaudeProvider::new(config.api_key, config.base_url))
            }
            ProviderType::Gemini => {
                Arc::new(GeminiProvider::new(config.api_key, config.base_url))
            }
        };

        // Test the provider if it's external
        if provider_type != ProviderType::Ollama {
            match provider.health_check().await {
                Ok(true) => {
                    tracing::info!("Health check passed for {:?}", provider_type);
                }
                Ok(false) => {
                    tracing::warn!("Health check failed for {:?}", provider_type);
                    return Err(LLMError::Provider(format!("Provider {:?} health check failed", provider_type)));
                }
                Err(e) => {
                    tracing::warn!("Health check error for {:?}: {}", provider_type, e);
                    // Still allow the provider to be added, but warn
                }
            }
        }

        Ok(provider)
    }

    /// Create a manager with only external providers (cloud-only setup)
    pub async fn create_cloud_only() -> LLMResult<LLMManager> {
        let mut manager = LLMManager::new();
        let storage = SecureStorage::new();

        let external_providers = [ProviderType::OpenAI, ProviderType::Claude, ProviderType::Gemini];
        let mut added_any = false;

        for provider_type in external_providers {
            if storage.has_api_key(&provider_type) {
                match Self::create_provider_from_config(&storage, provider_type).await {
                    Ok(provider) => {
                        manager.add_provider(provider).await;
                        if !added_any {
                            manager.set_default_provider(provider_type)?;
                            added_any = true;
                        }
                    }
                    Err(e) => {
                        tracing::warn!("Failed to add cloud provider {:?}: {}", provider_type, e);
                    }
                }
            }
        }

        if !added_any {
            return Err(LLMError::Config("No external providers configured".to_string()));
        }

        Ok(manager)
    }

    /// Create a manager with a specific provider only
    pub async fn create_with_provider(provider_type: ProviderType) -> LLMResult<LLMManager> {
        let mut manager = LLMManager::new();
        let storage = SecureStorage::new();

        let provider = Self::create_provider_from_config(&storage, provider_type).await?;
        manager.add_provider(provider).await;
        manager.set_default_provider(provider_type)?;

        Ok(manager)
    }

    /// Check if Ollama is available on the system
    pub async fn is_ollama_available(base_url: Option<String>) -> bool {
        let provider = OllamaProvider::new(base_url);
        provider.health_check().await.unwrap_or(false)
    }

    /// Get the default Ollama URL
    pub fn default_ollama_url() -> String {
        "http://localhost:11434".to_string()
    }

    /// Get common Ollama model recommendations for different use cases
    pub fn get_recommended_models() -> Vec<ModelRecommendation> {
        vec![
            ModelRecommendation {
                model_name: "llama2".to_string(),
                use_case: "General purpose, good balance of speed and quality".to_string(),
                size_gb: 3.8,
                ram_required_gb: 8,
                recommended_for_beginners: true,
            },
            ModelRecommendation {
                model_name: "llama2:13b".to_string(),
                use_case: "Higher quality responses, slower generation".to_string(),
                size_gb: 7.3,
                ram_required_gb: 16,
                recommended_for_beginners: false,
            },
            ModelRecommendation {
                model_name: "codellama".to_string(),
                use_case: "Code generation and explanation".to_string(),
                size_gb: 3.8,
                ram_required_gb: 8,
                recommended_for_beginners: true,
            },
            ModelRecommendation {
                model_name: "mistral".to_string(),
                use_case: "Fast and efficient for educational content".to_string(),
                size_gb: 4.1,
                ram_required_gb: 8,
                recommended_for_beginners: true,
            },
            ModelRecommendation {
                model_name: "neural-chat".to_string(),
                use_case: "Conversational and educational interactions".to_string(),
                size_gb: 4.1,
                ram_required_gb: 8,
                recommended_for_beginners: true,
            },
        ]
    }
}

#[derive(Debug, Clone)]
pub struct ModelRecommendation {
    pub model_name: String,
    pub use_case: String,
    pub size_gb: f64,
    pub ram_required_gb: u32,
    pub recommended_for_beginners: bool,
}

/// Helper functions for Ollama management
pub struct OllamaHelper;

impl OllamaHelper {
    /// Generate installation instructions for Ollama
    pub fn get_installation_instructions() -> InstallationInstructions {
        InstallationInstructions {
            linux: vec![
                "curl -fsSL https://ollama.com/install.sh | sh".to_string(),
                "# Or using package managers:".to_string(),
                "# Ubuntu/Debian: wget -qO- https://ollama.com/install.sh | sh".to_string(),
                "# After installation, start with: ollama serve".to_string(),
            ],
            macos: vec![
                "# Download from https://ollama.com/download".to_string(),
                "# Or using Homebrew:".to_string(),
                "brew install ollama".to_string(),
                "ollama serve".to_string(),
            ],
            windows: vec![
                "# Download the Windows installer from https://ollama.com/download".to_string(),
                "# Run the installer and Ollama will start automatically".to_string(),
            ],
            post_install: vec![
                "# Pull a model to get started:".to_string(),
                "ollama pull llama2".to_string(),
                "# Test the installation:".to_string(),
                "ollama run llama2".to_string(),
            ],
        }
    }

    /// Check system requirements for running Ollama models
    pub fn check_system_requirements(available_ram_gb: u32) -> SystemRequirements {
        let suitable_models = LLMFactory::get_recommended_models()
            .into_iter()
            .filter(|model| model.ram_required_gb <= available_ram_gb)
            .collect();

        SystemRequirements {
            available_ram_gb,
            recommended_models: suitable_models,
            can_run_basic_models: available_ram_gb >= 8,
            can_run_large_models: available_ram_gb >= 16,
            warnings: if available_ram_gb < 8 {
                vec!["Insufficient RAM for recommended models. Consider using cloud providers.".to_string()]
            } else {
                vec![]
            },
        }
    }
}

#[derive(Debug, Clone)]
pub struct InstallationInstructions {
    pub linux: Vec<String>,
    pub macos: Vec<String>,
    pub windows: Vec<String>,
    pub post_install: Vec<String>,
}

#[derive(Debug, Clone)]
pub struct SystemRequirements {
    pub available_ram_gb: u32,
    pub recommended_models: Vec<ModelRecommendation>,
    pub can_run_basic_models: bool,
    pub can_run_large_models: bool,
    pub warnings: Vec<String>,
}