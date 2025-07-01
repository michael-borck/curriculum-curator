use crate::llm::{LLMProvider, LLMResponse, LLMError, LLMRequest, LLMResult, ProviderType, ProviderUsageStats};
use crate::llm::routing::{RequestRouter, RoutingConfig, RoutingStrategy};
use crate::llm::rate_limiter::RateLimiter;
use crate::llm::offline::{OfflineManager, ConnectivityStatus, ProviderCapability};
use std::collections::HashMap;
use std::sync::Arc;
use tokio::sync::{RwLock, Mutex};
use std::time::{Duration, Instant};

pub struct LLMManager {
    providers: HashMap<ProviderType, Arc<dyn LLMProvider>>,
    default_provider: ProviderType,
    request_history: Arc<RwLock<Vec<RequestRecord>>>,
    router: Arc<Mutex<RequestRouter>>,
    retry_config: RetryConfig,
    rate_limiters: HashMap<ProviderType, Arc<Mutex<RateLimiter>>>,
    offline_manager: Arc<Mutex<OfflineManager>>,
}

impl std::fmt::Debug for LLMManager {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("LLMManager")
            .field("providers", &self.providers.keys().collect::<Vec<_>>())
            .field("default_provider", &self.default_provider)
            .field("retry_config", &self.retry_config)
            .finish()
    }
}

#[derive(Debug, Clone)]
pub struct RequestRecord {
    pub timestamp: Instant,
    pub provider_type: ProviderType,
    pub model: String,
    pub tokens_used: u32,
    pub cost_usd: Option<f64>,
    pub success: bool,
    pub error: Option<String>,
    pub response_time_ms: u64,
}

#[derive(Debug, Clone)]
pub struct RetryConfig {
    pub max_retries: u32,
    pub initial_delay_ms: u64,
    pub max_delay_ms: u64,
    pub backoff_multiplier: f64,
}

impl Default for RetryConfig {
    fn default() -> Self {
        Self {
            max_retries: 3,
            initial_delay_ms: 1000,
            max_delay_ms: 30000,
            backoff_multiplier: 2.0,
        }
    }
}

#[derive(Debug, Clone)]
pub struct GenerationOptions {
    pub provider_type: Option<ProviderType>,
    pub enable_fallback: bool,
    pub timeout_seconds: Option<u64>,
    pub priority: RequestPriority,
}

#[derive(Debug, Clone)]
pub enum RequestPriority {
    Low,
    Normal, 
    High,
    Critical,
}

impl Default for GenerationOptions {
    fn default() -> Self {
        Self {
            provider_type: None,
            enable_fallback: true,
            timeout_seconds: None,
            priority: RequestPriority::Normal,
        }
    }
}

#[derive(Debug, Clone)]
pub struct CostAnalysis {
    pub time_window: Duration,
    pub total_cost: f64,
    pub total_tokens: u32,
    pub total_requests: usize,
    pub successful_requests: usize,
    pub average_cost_per_request: f64,
    pub cost_per_token: f64,
    pub success_rate: f64,
    pub provider_breakdown: HashMap<ProviderType, ProviderCostBreakdown>,
}

#[derive(Debug, Clone)]
pub struct ProviderCostBreakdown {
    pub total_cost: f64,
    pub total_tokens: u32,
    pub total_requests: usize,
    pub successful_requests: usize,
    pub average_response_time_ms: f64,
}

#[derive(Debug, Clone)]
pub struct OptimizationRecommendation {
    pub priority: RecommendationPriority,
    pub category: RecommendationCategory,
    pub title: String,
    pub description: String,
    pub potential_savings: Option<f64>,
}

#[derive(Debug, Clone)]
pub enum RecommendationPriority {
    Low,
    Medium,
    High,
    Critical,
}

#[derive(Debug, Clone)]
pub enum RecommendationCategory {
    Cost,
    Speed,
    Quality,
    Reliability,
    Efficiency,
}

#[derive(Debug, Clone)]
pub enum OptimizationLevel {
    Cost,    // Minimize cost, prefer free local models
    Speed,   // Minimize latency, use fastest available
    Quality, // Maximize quality, use best models available
}

impl LLMManager {
    pub fn new() -> Self {
        let routing_config = RoutingConfig::default();
        let router = RequestRouter::new(routing_config);
        
        Self {
            providers: HashMap::new(),
            default_provider: ProviderType::Ollama,
            request_history: Arc::new(RwLock::new(Vec::new())),
            router: Arc::new(Mutex::new(router)),
            retry_config: RetryConfig::default(),
            rate_limiters: HashMap::new(),
            offline_manager: Arc::new(Mutex::new(OfflineManager::new())),
        }
    }

    pub fn new_with_routing_config(routing_config: RoutingConfig) -> Self {
        let router = RequestRouter::new(routing_config);
        
        Self {
            providers: HashMap::new(),
            default_provider: ProviderType::Ollama,
            request_history: Arc::new(RwLock::new(Vec::new())),
            router: Arc::new(Mutex::new(router)),
            retry_config: RetryConfig::default(),
            rate_limiters: HashMap::new(),
            offline_manager: Arc::new(Mutex::new(OfflineManager::new())),
        }
    }

    pub async fn add_provider(&mut self, provider: Arc<dyn LLMProvider>) {
        let provider_type = provider.provider_type();
        
        // Add to router
        {
            let mut router = self.router.lock().await;
            router.add_provider(provider_type);
        }
        
        // Set up rate limiter based on provider config
        let rate_limiter = if let Some(rate_limit) = provider.config().rate_limit_requests_per_minute {
            Arc::new(Mutex::new(RateLimiter::new(rate_limit)))
        } else {
            Arc::new(Mutex::new(RateLimiter::new_unlimited()))
        };
        
        self.rate_limiters.insert(provider_type, rate_limiter);
        self.providers.insert(provider_type, provider);
    }

    pub fn remove_provider(&mut self, provider_type: &ProviderType) {
        self.providers.remove(provider_type);
    }

    pub fn set_default_provider(&mut self, provider_type: ProviderType) -> LLMResult<()> {
        if !self.providers.contains_key(&provider_type) {
            return Err(LLMError::Config(format!("Provider {:?} not registered", provider_type)));
        }
        self.default_provider = provider_type;
        Ok(())
    }

    pub fn get_provider(&self, provider_type: &ProviderType) -> Option<&Arc<dyn LLMProvider>> {
        self.providers.get(provider_type)
    }

    pub fn list_providers(&self) -> Vec<ProviderType> {
        self.providers.keys().cloned().collect()
    }

    pub async fn health_check_all(&self) -> HashMap<ProviderType, LLMResult<bool>> {
        let mut results = HashMap::new();
        
        for (provider_type, provider) in &self.providers {
            let health = provider.health_check().await;
            results.insert(*provider_type, health);
        }
        
        results
    }

    pub async fn generate(&self, request: &LLMRequest) -> LLMResult<LLMResponse> {
        self.generate_with_options(request, &GenerationOptions::default()).await
    }

    pub async fn generate_with_options(
        &self,
        request: &LLMRequest,
        options: &GenerationOptions,
    ) -> LLMResult<LLMResponse> {
        // Get routing order from router
        let available_providers: Vec<ProviderType> = self.providers.keys().copied().collect();
        let routing_order = {
            let mut router = self.router.lock().await;
            router.route_request(request, &available_providers, options.priority.clone())?
        };

        if routing_order.is_empty() {
            return Err(LLMError::Config("No providers available for routing".to_string()));
        }

        let mut last_error = None;

        // Try providers in routing order
        for (index, provider_type) in routing_order.iter().enumerate() {
            // Check rate limiting
            if let Some(rate_limiter) = self.rate_limiters.get(provider_type) {
                let mut limiter = rate_limiter.lock().await;
                if !limiter.try_acquire(1.0) {
                    let wait_time = limiter.time_until_available(1.0);
                    if wait_time > Duration::from_secs(5) {
                        // Skip provider if wait time is too long
                        continue;
                    }
                    // Wait for rate limit to reset
                    tokio::time::sleep(wait_time).await;
                    if !limiter.try_acquire(1.0) {
                        continue; // Still can't acquire, skip
                    }
                }
            }

            match self.try_generate_with_provider(request, provider_type).await {
                Ok(response) => {
                    // Record success in router
                    {
                        let mut router = self.router.lock().await;
                        router.record_success(*provider_type, &response);
                    }
                    
                    self.record_request(provider_type, request, &response, None).await;
                    return Ok(response);
                }
                Err(error) => {
                    // Record failure in router
                    {
                        let mut router = self.router.lock().await;
                        router.record_failure(*provider_type);
                    }
                    
                    self.record_request(provider_type, request, &LLMResponse::default(), Some(error.to_string())).await;
                    last_error = Some(error);
                    
                    // If not using fallback or this is the last provider, return error
                    if !options.enable_fallback || index == routing_order.len() - 1 {
                        break;
                    }
                }
            }
        }

        // All providers failed
        Err(last_error.unwrap_or_else(|| LLMError::Provider("All providers failed".to_string())))
    }

    async fn try_generate_with_provider(
        &self,
        request: &LLMRequest,
        provider_type: &ProviderType,
    ) -> LLMResult<LLMResponse> {
        let provider = self.providers.get(provider_type)
            .ok_or_else(|| LLMError::Config(format!("Provider {:?} not configured", provider_type)))?;
        
        // Validate request
        provider.validate_request(request)?;
        
        // Retry logic with exponential backoff
        let mut delay = self.retry_config.initial_delay_ms;
        
        for attempt in 0..=self.retry_config.max_retries {
            match provider.generate(request).await {
                Ok(response) => return Ok(response),
                Err(error) => {
                    // Don't retry on certain errors
                    match error {
                        LLMError::Auth(_) | LLMError::InvalidRequest(_) | LLMError::ContentFilter(_) => {
                            return Err(error);
                        }
                        _ => {
                            if attempt < self.retry_config.max_retries {
                                tokio::time::sleep(Duration::from_millis(delay)).await;
                                delay = (delay as f64 * self.retry_config.backoff_multiplier) as u64;
                                delay = delay.min(self.retry_config.max_delay_ms);
                            } else {
                                return Err(error);
                            }
                        }
                    }
                }
            }
        }
        
        unreachable!()
    }

    async fn try_fallback(
        &self,
        request: &LLMRequest,
        failed_provider: &ProviderType,
    ) -> LLMResult<LLMResponse> {
        // Try other providers in order of preference
        let fallback_order = self.get_fallback_order(failed_provider);
        
        for provider_type in fallback_order {
            if let Ok(response) = self.try_generate_with_provider(request, &provider_type).await {
                return Ok(response);
            }
        }
        
        Err(LLMError::Provider("All providers failed".to_string()))
    }

    fn get_fallback_order(&self, failed_provider: &ProviderType) -> Vec<ProviderType> {
        let mut order = vec![];
        
        // Prioritize local providers for fallback
        for provider_type in [ProviderType::Ollama, ProviderType::OpenAI, ProviderType::Claude, ProviderType::Gemini] {
            if provider_type != *failed_provider && self.providers.contains_key(&provider_type) {
                order.push(provider_type);
            }
        }
        
        order
    }

    pub async fn estimate_cost(&self, request: &LLMRequest, provider_type: Option<ProviderType>) -> LLMResult<f64> {
        let provider_type = provider_type.unwrap_or(self.default_provider);
        let provider = self.providers.get(&provider_type)
            .ok_or_else(|| LLMError::Config(format!("Provider {:?} not configured", provider_type)))?;
        
        provider.estimate_cost(request).await
    }

    pub async fn get_usage_stats(&self, provider_type: Option<ProviderType>) -> LLMResult<ProviderUsageStats> {
        if let Some(provider_type) = provider_type {
            let provider = self.providers.get(&provider_type)
                .ok_or_else(|| LLMError::Config(format!("Provider {:?} not configured", provider_type)))?;
            provider.get_usage_stats().await
        } else {
            // Aggregate stats across all providers
            self.get_aggregate_stats().await
        }
    }

    async fn get_aggregate_stats(&self) -> LLMResult<ProviderUsageStats> {
        // Implementation would aggregate stats from all providers
        // For now, return default stats
        Ok(ProviderUsageStats::default())
    }

    async fn record_request(
        &self,
        provider_type: &ProviderType,
        request: &LLMRequest,
        response: &LLMResponse,
        error: Option<String>,
    ) {
        let record = RequestRecord {
            timestamp: Instant::now(),
            provider_type: *provider_type,
            model: request.model.clone().unwrap_or_else(|| "unknown".to_string()),
            tokens_used: response.tokens_used.total_tokens,
            cost_usd: response.cost_usd,
            success: error.is_none(),
            error,
            response_time_ms: response.response_time_ms,
        };

        let mut history = self.request_history.write().await;
        history.push(record);
        
        // Keep only last 1000 requests
        if history.len() > 1000 {
            let len = history.len();
            history.drain(0..len - 1000);
        }
    }

    // Failover is now handled by the routing system
    // pub fn set_failover_enabled(&mut self, enabled: bool) {
    //     // Failover is controlled via routing config
    // }

    pub fn set_retry_config(&mut self, config: RetryConfig) {
        self.retry_config = config;
    }

    pub async fn update_routing_config(&self, config: RoutingConfig) {
        let mut router = self.router.lock().await;
        router.update_config(config);
    }

    pub async fn get_routing_metrics(&self) -> HashMap<ProviderType, serde_json::Value> {
        let router = self.router.lock().await;
        let metrics = router.get_metrics();
        
        metrics.iter().map(|(&provider_type, metrics)| {
            let json_metrics = serde_json::json!({
                "provider_type": format!("{:?}", provider_type),
                "average_latency_ms": metrics.average_latency_ms,
                "success_rate": metrics.success_rate,
                "average_cost_per_token": metrics.average_cost_per_token,
                "requests_last_hour": metrics.requests_last_hour,
                "consecutive_failures": metrics.consecutive_failures,
                "total_requests": metrics.total_requests,
                "total_tokens": metrics.total_tokens,
                "total_cost": metrics.total_cost,
                "is_healthy": metrics.is_healthy()
            });
            (provider_type, json_metrics)
        }).collect()
    }

    pub async fn set_routing_strategy(&self, strategy: RoutingStrategy) {
        let mut router = self.router.lock().await;
        // Update routing strategy directly
        // For now, create a new config with the strategy
        let new_config = RoutingConfig {
            strategy,
            ..RoutingConfig::default()
        };
        router.update_config(new_config);
    }

    pub async fn get_rate_limit_status(&self) -> HashMap<ProviderType, serde_json::Value> {
        let mut status = HashMap::new();
        
        for (&provider_type, rate_limiter) in &self.rate_limiters {
            let mut limiter = rate_limiter.lock().await;
            let status_info = serde_json::json!({
                "provider_type": format!("{:?}", provider_type),
                "requests_in_window": limiter.requests_in_current_window(),
                "is_unlimited": limiter.is_unlimited(),
                "time_until_next_request": limiter.time_until_available(1.0).as_millis()
            });
            status.insert(provider_type, status_info);
        }
        
        status
    }

    /// Get detailed cost analysis for educational content generation
    pub async fn get_cost_analysis(&self, time_window: Duration) -> LLMResult<CostAnalysis> {
        let cutoff_time = Instant::now() - time_window;
        let history = self.request_history.read().await;
        
        let recent_requests: Vec<&RequestRecord> = history
            .iter()
            .filter(|record| record.timestamp >= cutoff_time)
            .collect();
        
        let total_cost = recent_requests
            .iter()
            .filter_map(|record| record.cost_usd)
            .sum::<f64>();
        
        let total_tokens = recent_requests
            .iter()
            .map(|record| record.tokens_used)
            .sum::<u32>();
        
        let successful_requests = recent_requests
            .iter()
            .filter(|record| record.success)
            .count();
        
        let total_requests = recent_requests.len();
        
        let average_cost_per_request = if total_requests > 0 {
            total_cost / total_requests as f64
        } else {
            0.0
        };
        
        let cost_per_token = if total_tokens > 0 {
            total_cost / total_tokens as f64
        } else {
            0.0
        };
        
        let success_rate = if total_requests > 0 {
            successful_requests as f64 / total_requests as f64
        } else {
            1.0
        };
        
        // Analyze by provider
        let mut provider_breakdown = HashMap::new();
        for provider_type in [ProviderType::Ollama, ProviderType::OpenAI, ProviderType::Claude, ProviderType::Gemini] {
            let provider_requests: Vec<&RequestRecord> = recent_requests
                .iter()
                .filter(|record| record.provider_type == provider_type)
                .cloned()
                .collect();
            
            if !provider_requests.is_empty() {
                let provider_cost = provider_requests
                    .iter()
                    .filter_map(|record| record.cost_usd)
                    .sum::<f64>();
                
                let provider_tokens = provider_requests
                    .iter()
                    .map(|record| record.tokens_used)
                    .sum::<u32>();
                
                let provider_success = provider_requests
                    .iter()
                    .filter(|record| record.success)
                    .count();
                
                provider_breakdown.insert(provider_type, ProviderCostBreakdown {
                    total_cost: provider_cost,
                    total_tokens: provider_tokens,
                    total_requests: provider_requests.len(),
                    successful_requests: provider_success,
                    average_response_time_ms: provider_requests
                        .iter()
                        .map(|record| record.response_time_ms)
                        .sum::<u64>() as f64 / provider_requests.len() as f64,
                });
            }
        }
        
        Ok(CostAnalysis {
            time_window,
            total_cost,
            total_tokens,
            total_requests,
            successful_requests,
            average_cost_per_request,
            cost_per_token,
            success_rate,
            provider_breakdown,
        })
    }

    /// Get recommendations for optimizing costs in educational content generation
    pub async fn get_optimization_recommendations(&self) -> Vec<OptimizationRecommendation> {
        let mut recommendations = Vec::new();
        
        // Analyze recent usage patterns
        let cost_analysis = self.get_cost_analysis(Duration::from_secs(24 * 60 * 60)).await.ok();
        
        if let Some(analysis) = cost_analysis {
            // Recommend using local providers if costs are high
            if analysis.total_cost > 1.0 { // More than $1 per day
                recommendations.push(OptimizationRecommendation {
                    priority: RecommendationPriority::High,
                    category: RecommendationCategory::Cost,
                    title: "Consider using local Ollama models".to_string(),
                    description: "Your current daily costs are high. Local Ollama models can generate educational content for free.".to_string(),
                    potential_savings: Some(analysis.total_cost * 0.8), // Assume 80% savings
                });
            }
            
            // Recommend better model selection based on content type
            if analysis.cost_per_token > 0.00005 { // High cost per token
                recommendations.push(OptimizationRecommendation {
                    priority: RecommendationPriority::Medium,
                    category: RecommendationCategory::Efficiency,
                    title: "Optimize model selection for content types".to_string(),
                    description: "Use smaller, faster models for simple content like worksheets and larger models only for complex content.".to_string(),
                    potential_savings: Some(analysis.total_cost * 0.3),
                });
            }
            
            // Recommend using routing strategies
            if analysis.success_rate < 0.95 {
                recommendations.push(OptimizationRecommendation {
                    priority: RecommendationPriority::High,
                    category: RecommendationCategory::Reliability,
                    title: "Enable provider fallback".to_string(),
                    description: "Your success rate is low. Enable fallback to secondary providers to improve reliability.".to_string(),
                    potential_savings: None,
                });
            }
        }
        
        recommendations
    }

    /// Batch generate content with cost optimization
    pub async fn batch_generate(
        &self,
        requests: Vec<(LLMRequest, String)>, // (request, content_type)
        optimization_level: OptimizationLevel,
    ) -> LLMResult<Vec<(String, LLMResult<LLMResponse>)>> {
        let mut results = Vec::new();
        
        // Sort requests by cost optimization strategy
        let mut sorted_requests = requests;
        match optimization_level {
            OptimizationLevel::Cost => {
                // Use cheapest providers first
                sorted_requests.sort_by(|a, b| {
                    self.estimate_content_complexity(&a.1)
                        .cmp(&self.estimate_content_complexity(&b.1))
                });
            }
            OptimizationLevel::Speed => {
                // Use fastest providers first
                // Keep original order but use fast routing
            }
            OptimizationLevel::Quality => {
                // Use highest quality providers
                sorted_requests.sort_by(|a, b| {
                    self.estimate_content_complexity(&b.1)
                        .cmp(&self.estimate_content_complexity(&a.1))
                });
            }
        }
        
        for (request, content_type) in sorted_requests {
            let options = self.get_optimized_options(&content_type, optimization_level.clone());
            let result = self.generate_with_options(&request, &options).await;
            results.push((content_type, result));
        }
        
        Ok(results)
    }

    fn estimate_content_complexity(&self, content_type: &str) -> u8 {
        match content_type.to_lowercase().as_str() {
            "quiz" | "worksheet" => 1, // Simple content
            "slides" | "notes" => 2,   // Medium content
            "lecture" | "course" => 3, // Complex content
            _ => 2, // Default to medium
        }
    }

    fn get_optimized_options(&self, content_type: &str, optimization_level: OptimizationLevel) -> GenerationOptions {
        let complexity = self.estimate_content_complexity(content_type);
        
        match optimization_level {
            OptimizationLevel::Cost => GenerationOptions {
                provider_type: Some(ProviderType::Ollama), // Always prefer free local
                enable_fallback: false,
                timeout_seconds: Some(120),
                priority: RequestPriority::Low,
            },
            OptimizationLevel::Speed => GenerationOptions {
                provider_type: if complexity <= 2 { Some(ProviderType::Ollama) } else { None },
                enable_fallback: true,
                timeout_seconds: Some(30),
                priority: RequestPriority::High,
            },
            OptimizationLevel::Quality => GenerationOptions {
                provider_type: if complexity >= 3 { Some(ProviderType::Claude) } else { None },
                enable_fallback: true,
                timeout_seconds: Some(180),
                priority: RequestPriority::Normal,
            },
        }
    }

    /// Check current connectivity status
    pub async fn get_connectivity_status(&self) -> LLMResult<ConnectivityStatus> {
        let mut offline_manager = self.offline_manager.lock().await;
        offline_manager.check_connectivity().await
    }

    /// Get all available providers based on connectivity
    pub async fn get_available_providers_by_connectivity(&self) -> LLMResult<Vec<ProviderType>> {
        let mut offline_manager = self.offline_manager.lock().await;
        offline_manager.get_available_providers().await
    }

    /// Check if offline capability is available
    pub async fn has_offline_capability(&self) -> bool {
        let mut offline_manager = self.offline_manager.lock().await;
        offline_manager.has_offline_capability().await
    }

    /// Get provider capability information
    pub async fn get_provider_capability(&self, provider_type: ProviderType) -> LLMResult<ProviderCapability> {
        let mut offline_manager = self.offline_manager.lock().await;
        offline_manager.check_provider_availability(provider_type).await
    }

    /// Get offline setup recommendations
    pub async fn get_offline_setup_recommendations(&self) -> Vec<String> {
        let offline_manager = self.offline_manager.lock().await;
        offline_manager.get_offline_setup_recommendations()
    }

    /// Force refresh all provider capabilities
    pub async fn refresh_provider_capabilities(&self) -> LLMResult<()> {
        let mut offline_manager = self.offline_manager.lock().await;
        offline_manager.refresh_all_capabilities().await
    }

    /// Get the best available provider based on connectivity and requirements
    pub async fn get_best_available_provider(&self, prefer_offline: bool) -> LLMResult<ProviderType> {
        let mut offline_manager = self.offline_manager.lock().await;
        let connectivity = offline_manager.check_connectivity().await?;
        
        match connectivity {
            ConnectivityStatus::Offline => {
                // Only local providers available
                let ollama_capability = offline_manager.check_provider_availability(ProviderType::Ollama).await?;
                if ollama_capability.is_available {
                    Ok(ProviderType::Ollama)
                } else {
                    Err(LLMError::Provider("No offline providers available. Please install Ollama.".to_string()))
                }
            }
            ConnectivityStatus::Online | ConnectivityStatus::Limited => {
                if prefer_offline {
                    // Check if Ollama is available first
                    let ollama_capability = offline_manager.check_provider_availability(ProviderType::Ollama).await?;
                    if ollama_capability.is_available {
                        return Ok(ProviderType::Ollama);
                    }
                }
                
                // Try online providers in order of preference
                for provider_type in [ProviderType::Claude, ProviderType::OpenAI, ProviderType::Gemini] {
                    let capability = offline_manager.check_provider_availability(provider_type).await?;
                    if capability.is_available {
                        return Ok(provider_type);
                    }
                }
                
                // Fall back to Ollama if no online providers work
                let ollama_capability = offline_manager.check_provider_availability(ProviderType::Ollama).await?;
                if ollama_capability.is_available {
                    Ok(ProviderType::Ollama)
                } else {
                    Err(LLMError::Provider("No providers available".to_string()))
                }
            }
            ConnectivityStatus::Unknown => {
                // Default to trying Ollama first
                let ollama_capability = offline_manager.check_provider_availability(ProviderType::Ollama).await?;
                if ollama_capability.is_available {
                    Ok(ProviderType::Ollama)
                } else {
                    Err(LLMError::Provider("Unable to determine connectivity and no offline providers available".to_string()))
                }
            }
        }
    }

    /// Generate content with automatic provider selection based on connectivity
    pub async fn generate_with_auto_provider(&self, request: &LLMRequest, prefer_offline: bool) -> LLMResult<LLMResponse> {
        let best_provider = self.get_best_available_provider(prefer_offline).await?;
        
        if let Some(provider) = self.providers.get(&best_provider) {
            provider.generate(request).await
        } else {
            Err(LLMError::Config(format!("Provider {:?} not configured", best_provider)))
        }
    }
}


impl Default for LLMResponse {
    fn default() -> Self {
        use crate::llm::{TokenUsage, FinishReason};
        Self {
            content: String::new(),
            model_used: String::new(),
            tokens_used: TokenUsage::new(0, 0),
            cost_usd: None,
            finish_reason: FinishReason::Error("Default response".to_string()),
            response_time_ms: 0,
            metadata: HashMap::new(),
        }
    }
}