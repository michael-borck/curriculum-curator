use std::time::Duration;
use serde::{Deserialize, Serialize};
use crate::llm::{ProviderType, LLMResult};

/// Network connectivity status
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum ConnectivityStatus {
    Online,
    Offline,
    Limited, // Can connect to some services but not others
    Unknown,
}

/// Capability detection for different LLM providers
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ProviderCapability {
    pub provider_type: ProviderType,
    pub is_available: bool,
    pub requires_internet: bool,
    pub can_run_offline: bool,
    pub status_message: String,
    pub last_checked: std::time::SystemTime,
}

/// Manages offline capability detection and embedded LLM options
#[derive(Debug)]
pub struct OfflineManager {
    connectivity_status: ConnectivityStatus,
    provider_capabilities: std::collections::HashMap<ProviderType, ProviderCapability>,
    last_connectivity_check: std::time::SystemTime,
    check_interval: Duration,
}

impl OfflineManager {
    pub fn new() -> Self {
        Self {
            connectivity_status: ConnectivityStatus::Unknown,
            provider_capabilities: std::collections::HashMap::new(),
            last_connectivity_check: std::time::SystemTime::UNIX_EPOCH,
            check_interval: Duration::from_secs(30), // Check every 30 seconds
        }
    }

    /// Check current internet connectivity status
    pub async fn check_connectivity(&mut self) -> LLMResult<ConnectivityStatus> {
        let now = std::time::SystemTime::now();
        
        // Only check if enough time has passed since last check
        if now.duration_since(self.last_connectivity_check).unwrap_or(Duration::MAX) < self.check_interval {
            return Ok(self.connectivity_status.clone());
        }

        self.last_connectivity_check = now;

        // Test connectivity to common endpoints
        let connectivity = self.test_internet_connectivity().await;
        self.connectivity_status = connectivity.clone();
        
        Ok(connectivity)
    }

    /// Test internet connectivity by trying to reach multiple endpoints
    async fn test_internet_connectivity(&self) -> ConnectivityStatus {
        let test_urls = vec![
            "https://www.google.com",
            "https://1.1.1.1", // Cloudflare DNS
            "https://8.8.8.8", // Google DNS
        ];

        let client = reqwest::Client::builder()
            .timeout(Duration::from_secs(5))
            .build()
            .unwrap_or_default();

        let mut successful_connections = 0;
        let total_tests = test_urls.len();

        for url in test_urls {
            match client.head(url).send().await {
                Ok(response) if response.status().is_success() => {
                    successful_connections += 1;
                }
                _ => {
                    // Connection failed
                }
            }
        }

        match successful_connections {
            0 => ConnectivityStatus::Offline,
            n if n == total_tests => ConnectivityStatus::Online,
            _ => ConnectivityStatus::Limited,
        }
    }

    /// Check availability of specific LLM providers
    pub async fn check_provider_availability(&mut self, provider_type: ProviderType) -> LLMResult<ProviderCapability> {
        let _now = std::time::SystemTime::now();
        
        let capability = match provider_type {
            ProviderType::Ollama => self.check_ollama_availability().await,
            ProviderType::OpenAI => self.check_online_provider_availability(
                provider_type, 
                "https://api.openai.com/v1/models"
            ).await,
            ProviderType::Claude => self.check_online_provider_availability(
                provider_type,
                "https://api.anthropic.com/v1/messages"
            ).await,
            ProviderType::Gemini => self.check_online_provider_availability(
                provider_type,
                "https://generativelanguage.googleapis.com/v1beta/models"
            ).await,
        };

        // Update our cache
        self.provider_capabilities.insert(provider_type, capability.clone());
        
        Ok(capability)
    }

    /// Check if Ollama is available locally
    async fn check_ollama_availability(&self) -> ProviderCapability {
        let client = reqwest::Client::builder()
            .timeout(Duration::from_secs(3))
            .build()
            .unwrap_or_default();

        let ollama_url = "http://localhost:11434/api/tags";
        
        match client.get(ollama_url).send().await {
            Ok(response) if response.status().is_success() => {
                ProviderCapability {
                    provider_type: ProviderType::Ollama,
                    is_available: true,
                    requires_internet: false,
                    can_run_offline: true,
                    status_message: "Ollama is running locally and available".to_string(),
                    last_checked: std::time::SystemTime::now(),
                }
            }
            Ok(response) => {
                ProviderCapability {
                    provider_type: ProviderType::Ollama,
                    is_available: false,
                    requires_internet: false,
                    can_run_offline: true,
                    status_message: format!("Ollama server responded with status: {}", response.status()),
                    last_checked: std::time::SystemTime::now(),
                }
            }
            Err(e) => {
                ProviderCapability {
                    provider_type: ProviderType::Ollama,
                    is_available: false,
                    requires_internet: false,
                    can_run_offline: true,
                    status_message: format!("Ollama not available: {}. Install Ollama to use offline LLM capabilities.", e),
                    last_checked: std::time::SystemTime::now(),
                }
            }
        }
    }

    /// Check if an online provider is available
    async fn check_online_provider_availability(&self, provider_type: ProviderType, test_url: &str) -> ProviderCapability {
        // First check internet connectivity
        if self.connectivity_status == ConnectivityStatus::Offline {
            return ProviderCapability {
                provider_type,
                is_available: false,
                requires_internet: true,
                can_run_offline: false,
                status_message: "No internet connection available".to_string(),
                last_checked: std::time::SystemTime::now(),
            };
        }

        let client = reqwest::Client::builder()
            .timeout(Duration::from_secs(5))
            .build()
            .unwrap_or_default();

        match client.head(test_url).send().await {
            Ok(response) if response.status().is_success() || response.status().as_u16() == 401 => {
                // 401 is expected for API endpoints without authentication
                ProviderCapability {
                    provider_type,
                    is_available: true,
                    requires_internet: true,
                    can_run_offline: false,
                    status_message: format!("{:?} API is reachable", provider_type),
                    last_checked: std::time::SystemTime::now(),
                }
            }
            Ok(response) => {
                ProviderCapability {
                    provider_type,
                    is_available: false,
                    requires_internet: true,
                    can_run_offline: false,
                    status_message: format!("{:?} API returned status: {}", provider_type, response.status()),
                    last_checked: std::time::SystemTime::now(),
                }
            }
            Err(e) => {
                ProviderCapability {
                    provider_type,
                    is_available: false,
                    requires_internet: true,
                    can_run_offline: false,
                    status_message: format!("{:?} API unreachable: {}", provider_type, e),
                    last_checked: std::time::SystemTime::now(),
                }
            }
        }
    }

    /// Get all available providers based on current connectivity
    pub async fn get_available_providers(&mut self) -> LLMResult<Vec<ProviderType>> {
        let connectivity = self.check_connectivity().await?;
        let mut available_providers = Vec::new();

        // Always check Ollama since it can work offline
        let ollama_capability = self.check_provider_availability(ProviderType::Ollama).await?;
        if ollama_capability.is_available {
            available_providers.push(ProviderType::Ollama);
        }

        // Check online providers only if we have internet
        if connectivity == ConnectivityStatus::Online || connectivity == ConnectivityStatus::Limited {
            for provider_type in [ProviderType::OpenAI, ProviderType::Claude, ProviderType::Gemini] {
                let capability = self.check_provider_availability(provider_type).await?;
                if capability.is_available {
                    available_providers.push(provider_type);
                }
            }
        }

        Ok(available_providers)
    }

    /// Get offline-capable providers
    pub fn get_offline_providers(&self) -> Vec<ProviderType> {
        vec![ProviderType::Ollama] // Only Ollama can run offline currently
    }

    /// Get current connectivity status
    pub fn get_connectivity_status(&self) -> ConnectivityStatus {
        self.connectivity_status.clone()
    }

    /// Get provider capability information
    pub fn get_provider_capability(&self, provider_type: &ProviderType) -> Option<&ProviderCapability> {
        self.provider_capabilities.get(provider_type)
    }

    /// Get all cached provider capabilities
    pub fn get_all_provider_capabilities(&self) -> &std::collections::HashMap<ProviderType, ProviderCapability> {
        &self.provider_capabilities
    }

    /// Check if any offline-capable provider is available
    pub async fn has_offline_capability(&mut self) -> bool {
        let ollama_capability = self.check_provider_availability(ProviderType::Ollama).await;
        ollama_capability.map(|cap| cap.is_available).unwrap_or(false)
    }

    /// Get recommendations for offline setup
    pub fn get_offline_setup_recommendations(&self) -> Vec<String> {
        let mut recommendations = Vec::new();

        // Check if Ollama is available
        if let Some(ollama_cap) = self.get_provider_capability(&ProviderType::Ollama) {
            if !ollama_cap.is_available {
                recommendations.push(
                    "Install Ollama for offline LLM capabilities. Visit https://ollama.ai to download.".to_string()
                );
                recommendations.push(
                    "Recommended models for education: llama3.2:3b (lightweight), llama3.1:8b (balanced), or codellama:7b (coding focus)".to_string()
                );
                recommendations.push(
                    "After installing Ollama, run 'ollama pull llama3.2:3b' to download a model".to_string()
                );
            }
        } else {
            recommendations.push(
                "Ollama not detected. For offline content generation, install Ollama from https://ollama.ai".to_string()
            );
        }

        if self.connectivity_status == ConnectivityStatus::Offline {
            recommendations.push(
                "No internet connection detected. Only local Ollama models will be available.".to_string()
            );
        }

        recommendations
    }

    /// Force refresh of all capabilities
    pub async fn refresh_all_capabilities(&mut self) -> LLMResult<()> {
        // Reset last check time to force fresh checks
        self.last_connectivity_check = std::time::SystemTime::UNIX_EPOCH;
        self.provider_capabilities.clear();

        // Check connectivity
        self.check_connectivity().await?;

        // Check all providers
        for provider_type in [ProviderType::Ollama, ProviderType::OpenAI, ProviderType::Claude, ProviderType::Gemini] {
            let _ = self.check_provider_availability(provider_type).await;
        }

        Ok(())
    }
}

impl Default for OfflineManager {
    fn default() -> Self {
        Self::new()
    }
}

/// Educational-focused embedded LLM recommendations
pub struct EmbeddedLLMRecommendations;

impl EmbeddedLLMRecommendations {
    /// Get recommended models based on use case and hardware
    pub fn get_model_recommendations() -> Vec<OfflineModelRecommendation> {
        vec![
            OfflineModelRecommendation {
                model_name: "llama3.2:3b".to_string(),
                description: "Lightweight model perfect for basic educational content generation".to_string(),
                use_case: "Basic lesson plans, simple quizzes, worksheet generation".to_string(),
                min_ram_gb: 4,
                typical_ram_gb: 6,
                performance_level: PerformanceLevel::Fast,
                quality_level: QualityLevel::Good,
                educational_focus: true,
            },
            OfflineModelRecommendation {
                model_name: "llama3.1:8b".to_string(),
                description: "Balanced model for comprehensive educational content".to_string(),
                use_case: "Detailed lesson plans, complex assignments, instructor notes".to_string(),
                min_ram_gb: 8,
                typical_ram_gb: 12,
                performance_level: PerformanceLevel::Medium,
                quality_level: QualityLevel::Excellent,
                educational_focus: true,
            },
            OfflineModelRecommendation {
                model_name: "codellama:7b".to_string(),
                description: "Specialized for programming and computer science education".to_string(),
                use_case: "Code examples, programming assignments, technical documentation".to_string(),
                min_ram_gb: 8,
                typical_ram_gb: 10,
                performance_level: PerformanceLevel::Medium,
                quality_level: QualityLevel::Excellent,
                educational_focus: false, // Specialized use case
            },
            OfflineModelRecommendation {
                model_name: "phi3:mini".to_string(),
                description: "Ultra-lightweight model for basic content generation".to_string(),
                use_case: "Simple content generation on low-spec hardware".to_string(),
                min_ram_gb: 2,
                typical_ram_gb: 4,
                performance_level: PerformanceLevel::Fast,
                quality_level: QualityLevel::Basic,
                educational_focus: true,
            },
        ]
    }

    /// Get setup instructions for educational users
    pub fn get_setup_instructions() -> Vec<String> {
        vec![
            "1. Download and install Ollama from https://ollama.ai".to_string(),
            "2. Open terminal/command prompt and run: ollama pull llama3.2:3b".to_string(),
            "3. Wait for download to complete (may take several minutes)".to_string(),
            "4. Test the installation: ollama run llama3.2:3b \"Write a short lesson plan about photosynthesis\"".to_string(),
            "5. Return to Curriculum Curator and refresh the providers list".to_string(),
            "6. For better quality, consider downloading llama3.1:8b if you have 8GB+ RAM".to_string(),
        ]
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OfflineModelRecommendation {
    pub model_name: String,
    pub description: String,
    pub use_case: String,
    pub min_ram_gb: u32,
    pub typical_ram_gb: u32,
    pub performance_level: PerformanceLevel,
    pub quality_level: QualityLevel,
    pub educational_focus: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum PerformanceLevel {
    Fast,
    Medium,
    Slow,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum QualityLevel {
    Basic,
    Good,
    Excellent,
}