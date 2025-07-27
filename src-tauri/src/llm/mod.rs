pub mod providers;
pub mod manager;
pub mod ollama;
pub mod openai;
pub mod claude;
pub mod gemini;
pub mod factory;
pub mod routing;
pub mod rate_limiter;
pub mod secure_storage;
pub mod offline;

pub use manager::{
    LLMManager, RequestRecord, RetryConfig, GenerationOptions, RequestPriority,
    CostAnalysis, ProviderCostBreakdown, OptimizationRecommendation, 
    RecommendationPriority, RecommendationCategory, OptimizationLevel
};
pub use providers::{
    LLMProvider, ProviderType, LLMRequest, LLMResponse, LLMError, LLMResult,
    TokenUsage, FinishReason, ProviderConfig, ModelInfo, ModelCapabilities,
    ProviderUsageStats, UsageWindow, ProviderFeature, ProviderLimits
};
pub use ollama::OllamaProvider;
pub use openai::OpenAIProvider;
pub use claude::ClaudeProvider;
pub use gemini::GeminiProvider;
pub use factory::{LLMFactory, OllamaHelper, ModelRecommendation, InstallationInstructions, SystemRequirements};
pub use routing::{RoutingStrategy, RoutingConfig, ProviderMetrics};
pub use rate_limiter::RateLimiter;
pub use secure_storage::{
    SecureStorage, ApiKeyConfig, SecureStorageError,
    CostRecommendation, EstimatedSavings, SetupComplexity,
    EducationalValidation, PrivacyLevel, CostLevel,
    SecurityRecommendation, SecuritySeverity
};
pub use offline::{
    OfflineManager, ConnectivityStatus, ProviderCapability,
    EmbeddedLLMRecommendations, OfflineModelRecommendation, PerformanceLevel, QualityLevel
};