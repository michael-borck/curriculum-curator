use anyhow::Result;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;

#[derive(Debug, Clone, Copy, Serialize, Deserialize, Eq, Hash, PartialEq)]
pub enum ProviderType {
    Ollama,
    OpenAI,
    Claude,
    Gemini,
}

impl std::str::FromStr for ProviderType {
    type Err = String;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        match s.to_lowercase().as_str() {
            "ollama" => Ok(ProviderType::Ollama),
            "openai" => Ok(ProviderType::OpenAI),
            "claude" => Ok(ProviderType::Claude),
            "gemini" => Ok(ProviderType::Gemini),
            _ => Err(format!("Unknown provider type: {}", s)),
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LLMRequest {
    pub prompt: String,
    pub model: Option<String>,
    pub temperature: Option<f32>,
    pub max_tokens: Option<u32>,
    pub system_prompt: Option<String>,
    pub context: Option<String>,
    pub top_p: Option<f32>,
    pub frequency_penalty: Option<f32>,
    pub presence_penalty: Option<f32>,
    pub stop_sequences: Option<Vec<String>>,
    pub stream: bool,
    pub json_mode: bool,
    pub seed: Option<u32>,
    pub metadata: HashMap<String, serde_json::Value>,
}

impl LLMRequest {
    pub fn new(prompt: impl Into<String>) -> Self {
        Self {
            prompt: prompt.into(),
            model: None,
            temperature: None,
            max_tokens: None,
            system_prompt: None,
            context: None,
            top_p: None,
            frequency_penalty: None,
            presence_penalty: None,
            stop_sequences: None,
            stream: false,
            json_mode: false,
            seed: None,
            metadata: HashMap::new(),
        }
    }

    pub fn with_model(mut self, model: impl Into<String>) -> Self {
        self.model = Some(model.into());
        self
    }

    pub fn with_temperature(mut self, temperature: f32) -> Self {
        self.temperature = Some(temperature);
        self
    }

    pub fn with_max_tokens(mut self, max_tokens: u32) -> Self {
        self.max_tokens = Some(max_tokens);
        self
    }

    pub fn with_system_prompt(mut self, system_prompt: impl Into<String>) -> Self {
        self.system_prompt = Some(system_prompt.into());
        self
    }

    pub fn with_context(mut self, context: impl Into<String>) -> Self {
        self.context = Some(context.into());
        self
    }

    pub fn with_top_p(mut self, top_p: f32) -> Self {
        self.top_p = Some(top_p);
        self
    }

    pub fn with_frequency_penalty(mut self, penalty: f32) -> Self {
        self.frequency_penalty = Some(penalty);
        self
    }

    pub fn with_presence_penalty(mut self, penalty: f32) -> Self {
        self.presence_penalty = Some(penalty);
        self
    }

    pub fn with_stop_sequences(mut self, stops: Vec<String>) -> Self {
        self.stop_sequences = Some(stops);
        self
    }

    pub fn with_streaming(mut self, stream: bool) -> Self {
        self.stream = stream;
        self
    }

    pub fn with_json_mode(mut self, json_mode: bool) -> Self {
        self.json_mode = json_mode;
        self
    }

    pub fn with_seed(mut self, seed: u32) -> Self {
        self.seed = Some(seed);
        self
    }

    pub fn with_metadata(mut self, key: impl Into<String>, value: serde_json::Value) -> Self {
        self.metadata.insert(key.into(), value);
        self
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LLMResponse {
    pub content: String,
    pub model_used: String,
    pub tokens_used: TokenUsage,
    pub cost_usd: Option<f64>,
    pub finish_reason: FinishReason,
    pub response_time_ms: u64,
    pub metadata: HashMap<String, serde_json::Value>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TokenUsage {
    pub prompt_tokens: u32,
    pub completion_tokens: u32,
    pub total_tokens: u32,
}

impl TokenUsage {
    pub fn new(prompt_tokens: u32, completion_tokens: u32) -> Self {
        Self {
            prompt_tokens,
            completion_tokens,
            total_tokens: prompt_tokens + completion_tokens,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum FinishReason {
    Stop,
    Length,
    ContentFilter,
    ToolCalls,
    FunctionCall,
    Other(String),
    Error(String),
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ProviderConfig {
    pub name: String,
    pub base_url: String,
    pub api_key: Option<String>,
    pub default_model: Option<String>,
    pub max_tokens_per_request: Option<u32>,
    pub rate_limit_requests_per_minute: Option<u32>,
    pub cost_per_input_token: Option<f64>,
    pub cost_per_output_token: Option<f64>,
    pub supports_streaming: bool,
    pub supports_system_prompt: bool,
    pub supports_function_calling: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ModelInfo {
    pub id: String,
    pub name: String,
    pub description: String,
    pub context_length: u32,
    pub parameter_count: Option<u64>,
    pub cost_per_1k_prompt_tokens: Option<f64>,
    pub cost_per_1k_completion_tokens: Option<f64>,
    pub capabilities: ModelCapabilities,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ModelCapabilities {
    pub supports_streaming: bool,
    pub supports_function_calling: bool,
    pub supports_vision: bool,
    pub supports_chat: bool,
    pub supports_completion: bool,
    pub max_output_tokens: Option<u32>,
    pub max_context_length: u32,
    pub supported_languages: Vec<String>,
}

#[derive(Debug, thiserror::Error)]
pub enum LLMError {
    #[error("Network error: {0}")]
    Network(String),
    #[error("Authentication failed: {0}")]
    Auth(String),
    #[error("Rate limit exceeded: {0}")]
    RateLimit(String),
    #[error("Invalid request: {0}")]
    InvalidRequest(String),
    #[error("Model not found: {0}")]
    ModelNotFound(String),
    #[error("Content filtered: {0}")]
    ContentFilter(String),
    #[error("Token limit exceeded: {0}")]
    TokenLimit(String),
    #[error("Provider error: {0}")]
    Provider(String),
    #[error("Configuration error: {0}")]
    Config(String),
    #[error("Timeout error: {0}")]
    Timeout(String),
}

pub type LLMResult<T> = Result<T, LLMError>;

#[async_trait::async_trait]
pub trait LLMProvider: Send + Sync {
    /// Get the provider type
    fn provider_type(&self) -> ProviderType;
    
    /// Get provider configuration
    fn config(&self) -> &ProviderConfig;
    
    /// Check if the provider is available and configured
    async fn health_check(&self) -> LLMResult<bool>;
    
    /// Get available models for this provider
    async fn list_models(&self) -> LLMResult<Vec<ModelInfo>>;
    
    /// Generate text completion
    async fn generate(&self, request: &LLMRequest) -> LLMResult<LLMResponse>;
    
    /// Generate streaming completion (returns async stream)
    async fn generate_stream(&self, request: &LLMRequest) -> LLMResult<Box<dyn futures::Stream<Item = LLMResult<String>> + Send + Unpin>>;
    
    /// Estimate cost for a request
    async fn estimate_cost(&self, request: &LLMRequest) -> LLMResult<f64>;
    
    /// Count tokens in text (provider-specific tokenization)
    async fn count_tokens(&self, text: &str, model: Option<&str>) -> LLMResult<u32>;
    
    /// Validate a request before sending
    fn validate_request(&self, request: &LLMRequest) -> LLMResult<()>;
    
    /// Get usage statistics
    async fn get_usage_stats(&self) -> LLMResult<ProviderUsageStats>;
    
    /// Get information about a specific model
    async fn get_model_info(&self, model_id: &str) -> LLMResult<ModelInfo>;
    
    /// Check if the provider supports a specific feature
    fn supports_feature(&self, feature: ProviderFeature) -> bool;
    
    /// Get the default model for this provider
    fn default_model(&self) -> Option<String>;
    
    /// Get provider-specific limits
    fn get_limits(&self) -> ProviderLimits;
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ProviderUsageStats {
    pub total_requests: u64,
    pub total_tokens: u64,
    pub total_cost_usd: f64,
    pub average_response_time_ms: f64,
    pub error_rate: f64,
    pub last_24h: UsageWindow,
    pub last_7d: UsageWindow,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UsageWindow {
    pub requests: u64,
    pub tokens: u64,
    pub cost_usd: f64,
    pub errors: u64,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ProviderFeature {
    Streaming,
    FunctionCalling,
    Vision,
    SystemPrompt,
    ContextWindow,
    CostTracking,
    RateLimiting,
    BatchProcessing,
    JsonMode,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ProviderLimits {
    pub max_tokens_per_request: u32,
    pub max_requests_per_minute: u32,
    pub max_tokens_per_minute: u32,
    pub max_context_length: u32,
    pub max_output_tokens: u32,
    pub min_temperature: f32,
    pub max_temperature: f32,
}

impl Default for ProviderLimits {
    fn default() -> Self {
        Self {
            max_tokens_per_request: 4096,
            max_requests_per_minute: 60,
            max_tokens_per_minute: 10000,
            max_context_length: 4096,
            max_output_tokens: 2048,
            min_temperature: 0.0,
            max_temperature: 2.0,
        }
    }
}

impl Default for ProviderUsageStats {
    fn default() -> Self {
        Self {
            total_requests: 0,
            total_tokens: 0,
            total_cost_usd: 0.0,
            average_response_time_ms: 0.0,
            error_rate: 0.0,
            last_24h: UsageWindow::default(),
            last_7d: UsageWindow::default(),
        }
    }
}

impl Default for UsageWindow {
    fn default() -> Self {
        Self {
            requests: 0,
            tokens: 0,
            cost_usd: 0.0,
            errors: 0,
        }
    }
}