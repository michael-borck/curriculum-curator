use crate::llm::{LLMRequest, LLMResponse, LLMError, LLMResult, ProviderType};
use crate::llm::manager::RequestPriority;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::time::{Duration, Instant};

/// Advanced routing strategy for LLM requests
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum RoutingStrategy {
    /// Always use the specified provider
    Fixed(ProviderType),
    /// Route based on cost optimization
    CostOptimal,
    /// Route based on speed/latency
    FastestFirst,
    /// Route based on provider reliability
    HighestReliability,
    /// Load balance across available providers
    RoundRobin,
    /// Route based on model capabilities required
    CapabilityBased,
    /// Custom routing based on request characteristics
    Smart,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RoutingConfig {
    pub strategy: RoutingStrategy,
    pub fallback_enabled: bool,
    pub max_cost_threshold: Option<f64>,
    pub max_latency_threshold: Option<Duration>,
    pub preferred_providers: Vec<ProviderType>,
    pub blocked_providers: Vec<ProviderType>,
    pub model_preferences: HashMap<String, ProviderType>,
}

impl Default for RoutingConfig {
    fn default() -> Self {
        Self {
            strategy: RoutingStrategy::Smart,
            fallback_enabled: true,
            max_cost_threshold: Some(0.10), // 10 cents max per request
            max_latency_threshold: Some(Duration::from_secs(30)),
            preferred_providers: vec![ProviderType::Ollama], // Prefer local first
            blocked_providers: vec![],
            model_preferences: HashMap::new(),
        }
    }
}

#[derive(Debug, Clone)]
pub struct ProviderMetrics {
    pub provider_type: ProviderType,
    pub average_latency_ms: f64,
    pub success_rate: f64,
    pub average_cost_per_token: f64,
    pub requests_last_hour: u32,
    pub last_error_time: Option<Instant>,
    pub consecutive_failures: u32,
    pub total_requests: u64,
    pub total_tokens: u64,
    pub total_cost: f64,
}

impl ProviderMetrics {
    pub fn new(provider_type: ProviderType) -> Self {
        Self {
            provider_type,
            average_latency_ms: 0.0,
            success_rate: 1.0,
            average_cost_per_token: 0.0,
            requests_last_hour: 0,
            last_error_time: None,
            consecutive_failures: 0,
            total_requests: 0,
            total_tokens: 0,
            total_cost: 0.0,
        }
    }

    pub fn record_success(&mut self, latency_ms: u64, tokens: u32, cost: f64) {
        self.total_requests += 1;
        self.total_tokens += tokens as u64;
        self.total_cost += cost;
        self.consecutive_failures = 0;
        
        // Update running averages
        self.average_latency_ms = if self.total_requests == 1 {
            latency_ms as f64
        } else {
            (self.average_latency_ms * 0.9) + (latency_ms as f64 * 0.1)
        };
        
        if tokens > 0 {
            self.average_cost_per_token = self.total_cost / self.total_tokens as f64;
        }
        
        self.success_rate = if self.total_requests == 1 {
            1.0
        } else {
            (self.success_rate * 0.95) + 0.05 // Slight boost for success
        };
    }

    pub fn record_failure(&mut self) {
        self.total_requests += 1;
        self.consecutive_failures += 1;
        self.last_error_time = Some(Instant::now());
        self.success_rate = (self.success_rate * 0.95).max(0.0); // Slight penalty
    }

    pub fn is_healthy(&self) -> bool {
        self.consecutive_failures < 3 && 
        self.success_rate > 0.5 &&
        self.last_error_time.map_or(true, |t| t.elapsed() > <Duration as DurationExt>::from_mins(5))
    }
}

pub struct RequestRouter {
    metrics: HashMap<ProviderType, ProviderMetrics>,
    config: RoutingConfig,
    round_robin_index: usize,
}

impl RequestRouter {
    pub fn new(config: RoutingConfig) -> Self {
        Self {
            metrics: HashMap::new(),
            config,
            round_robin_index: 0,
        }
    }

    pub fn add_provider(&mut self, provider_type: ProviderType) {
        self.metrics.insert(provider_type, ProviderMetrics::new(provider_type));
    }

    pub fn route_request(
        &mut self,
        request: &LLMRequest,
        available_providers: &[ProviderType],
        priority: RequestPriority,
    ) -> LLMResult<Vec<ProviderType>> {
        // Filter out blocked providers
        let filtered_providers: Vec<ProviderType> = available_providers
            .iter()
            .filter(|&p| !self.config.blocked_providers.contains(p))
            .filter(|&p| self.is_provider_healthy(p))
            .copied()
            .collect();

        if filtered_providers.is_empty() {
            return Err(LLMError::Config("No healthy providers available".to_string()));
        }

        let primary_provider = match &self.config.strategy {
            RoutingStrategy::Fixed(provider) => {
                if filtered_providers.contains(provider) {
                    *provider
                } else {
                    return Err(LLMError::Config(format!("Fixed provider {:?} not available", provider)));
                }
            }
            RoutingStrategy::CostOptimal => {
                self.select_cheapest_provider(&filtered_providers, request)?
            }
            RoutingStrategy::FastestFirst => {
                self.select_fastest_provider(&filtered_providers)?
            }
            RoutingStrategy::HighestReliability => {
                self.select_most_reliable_provider(&filtered_providers)?
            }
            RoutingStrategy::RoundRobin => {
                self.select_round_robin_provider(&filtered_providers)
            }
            RoutingStrategy::CapabilityBased => {
                self.select_capability_based_provider(&filtered_providers, request)?
            }
            RoutingStrategy::Smart => {
                self.select_smart_provider(&filtered_providers, request, priority)?
            }
        };

        // Build routing order with fallbacks
        let mut routing_order = vec![primary_provider];
        
        if self.config.fallback_enabled {
            let fallbacks = self.get_fallback_providers(&filtered_providers, primary_provider);
            routing_order.extend(fallbacks);
        }

        Ok(routing_order)
    }

    fn select_cheapest_provider(
        &self,
        providers: &[ProviderType],
        request: &LLMRequest,
    ) -> LLMResult<ProviderType> {
        let estimated_tokens = self.estimate_request_tokens(request);
        
        providers
            .iter()
            .min_by(|&a, &b| {
                let cost_a = self.estimate_provider_cost(*a, estimated_tokens);
                let cost_b = self.estimate_provider_cost(*b, estimated_tokens);
                cost_a.partial_cmp(&cost_b).unwrap_or(std::cmp::Ordering::Equal)
            })
            .copied()
            .ok_or_else(|| LLMError::Config("No providers available for cost optimization".to_string()))
    }

    fn select_fastest_provider(&self, providers: &[ProviderType]) -> LLMResult<ProviderType> {
        providers
            .iter()
            .min_by(|&a, &b| {
                let latency_a = self.metrics.get(a).map(|m| m.average_latency_ms).unwrap_or(f64::MAX);
                let latency_b = self.metrics.get(b).map(|m| m.average_latency_ms).unwrap_or(f64::MAX);
                latency_a.partial_cmp(&latency_b).unwrap_or(std::cmp::Ordering::Equal)
            })
            .copied()
            .ok_or_else(|| LLMError::Config("No providers available for speed optimization".to_string()))
    }

    fn select_most_reliable_provider(&self, providers: &[ProviderType]) -> LLMResult<ProviderType> {
        providers
            .iter()
            .max_by(|&a, &b| {
                let reliability_a = self.metrics.get(a).map(|m| m.success_rate).unwrap_or(0.0);
                let reliability_b = self.metrics.get(b).map(|m| m.success_rate).unwrap_or(0.0);
                reliability_a.partial_cmp(&reliability_b).unwrap_or(std::cmp::Ordering::Equal)
            })
            .copied()
            .ok_or_else(|| LLMError::Config("No providers available for reliability optimization".to_string()))
    }

    fn select_round_robin_provider(&mut self, providers: &[ProviderType]) -> ProviderType {
        let provider = providers[self.round_robin_index % providers.len()];
        self.round_robin_index += 1;
        provider
    }

    fn select_capability_based_provider(
        &self,
        providers: &[ProviderType],
        request: &LLMRequest,
    ) -> LLMResult<ProviderType> {
        // For now, simple capability routing based on model preferences
        if let Some(model) = &request.model {
            if let Some(&preferred_provider) = self.config.model_preferences.get(model) {
                if providers.contains(&preferred_provider) {
                    return Ok(preferred_provider);
                }
            }
        }

        // Fallback to preferred providers
        for &provider in &self.config.preferred_providers {
            if providers.contains(&provider) {
                return Ok(provider);
            }
        }

        providers.first().copied()
            .ok_or_else(|| LLMError::Config("No capable providers available".to_string()))
    }

    fn select_smart_provider(
        &self,
        providers: &[ProviderType],
        request: &LLMRequest,
        priority: RequestPriority,
    ) -> LLMResult<ProviderType> {
        // Smart routing considers multiple factors
        let mut scores: Vec<(ProviderType, f64)> = providers
            .iter()
            .map(|&provider| {
                let score = self.calculate_provider_score(provider, request, priority.clone());
                (provider, score)
            })
            .collect();

        scores.sort_by(|a, b| b.1.partial_cmp(&a.1).unwrap_or(std::cmp::Ordering::Equal));
        
        scores.first()
            .map(|(provider, _)| *provider)
            .ok_or_else(|| LLMError::Config("No providers available for smart routing".to_string()))
    }

    fn calculate_provider_score(
        &self,
        provider: ProviderType,
        request: &LLMRequest,
        priority: RequestPriority,
    ) -> f64 {
        let metrics = self.metrics.get(&provider);
        let estimated_tokens = self.estimate_request_tokens(request);
        
        let mut score = 100.0; // Base score

        if let Some(m) = metrics {
            // Reliability factor (0-50 points)
            score += m.success_rate * 50.0;
            
            // Speed factor (0-30 points, inverse of latency)
            let latency_score = if m.average_latency_ms > 0.0 {
                (30.0 / (1.0 + m.average_latency_ms / 1000.0)).min(30.0)
            } else {
                30.0
            };
            score += latency_score;
            
            // Cost factor (0-20 points, inverse of cost)
            let estimated_cost = self.estimate_provider_cost(provider, estimated_tokens);
            if let Some(max_cost) = self.config.max_cost_threshold {
                if estimated_cost > max_cost {
                    score -= 50.0; // Heavy penalty for exceeding cost threshold
                }
            }
            
            let cost_score = if estimated_cost > 0.0 {
                (20.0 / (1.0 + estimated_cost * 100.0)).min(20.0)
            } else {
                20.0 // Free providers get full points
            };
            score += cost_score;
        }

        // Priority adjustments
        match priority {
            RequestPriority::Critical => {
                // Prioritize reliability and speed over cost
                if provider == ProviderType::Ollama {
                    score += 20.0; // Local is most reliable
                }
            }
            RequestPriority::High => {
                if provider == ProviderType::Ollama {
                    score += 10.0;
                }
            }
            RequestPriority::Low => {
                // Prioritize cost over speed
                if provider == ProviderType::Ollama {
                    score += 30.0; // Free is best for low priority
                }
            }
            RequestPriority::Normal => {
                // Balanced approach
            }
        }

        // Preferred provider bonus
        if self.config.preferred_providers.contains(&provider) {
            score += 15.0;
        }

        score
    }

    fn get_fallback_providers(
        &self,
        available_providers: &[ProviderType],
        primary: ProviderType,
    ) -> Vec<ProviderType> {
        available_providers
            .iter()
            .filter(|&&p| p != primary)
            .sorted_by(|&a, &b| {
                let score_a = self.calculate_fallback_score(*a);
                let score_b = self.calculate_fallback_score(*b);
                score_b.partial_cmp(&score_a).unwrap_or(std::cmp::Ordering::Equal)
            })
            .into_iter().copied()
            .collect()
    }

    fn calculate_fallback_score(&self, provider: ProviderType) -> f64 {
        let mut score = 0.0;
        
        if let Some(metrics) = self.metrics.get(&provider) {
            score += metrics.success_rate * 100.0;
            score += (1.0 / (1.0 + metrics.consecutive_failures as f64)) * 50.0;
        }
        
        // Prefer local providers for fallback
        if provider == ProviderType::Ollama {
            score += 25.0;
        }
        
        score
    }

    fn is_provider_healthy(&self, provider: &ProviderType) -> bool {
        self.metrics
            .get(provider)
            .map_or(true, |m| m.is_healthy())
    }

    fn estimate_request_tokens(&self, request: &LLMRequest) -> u32 {
        // Simple estimation: ~4 characters per token
        let prompt_chars = request.prompt.len() + 
            request.system_prompt.as_ref().map_or(0, |s| s.len()) +
            request.context.as_ref().map_or(0, |s| s.len());
        
        let estimated_prompt_tokens = (prompt_chars as f32 / 4.0).ceil() as u32;
        let estimated_completion_tokens = request.max_tokens.unwrap_or(estimated_prompt_tokens);
        
        estimated_prompt_tokens + estimated_completion_tokens
    }

    fn estimate_provider_cost(&self, provider: ProviderType, tokens: u32) -> f64 {
        match provider {
            ProviderType::Ollama => 0.0, // Local is free
            ProviderType::OpenAI => tokens as f64 * 0.00002, // Rough estimate
            ProviderType::Claude => tokens as f64 * 0.00003, // Rough estimate  
            ProviderType::Gemini => tokens as f64 * 0.00001, // Rough estimate
        }
    }

    pub fn record_success(
        &mut self,
        provider: ProviderType,
        response: &LLMResponse,
    ) {
        if let Some(metrics) = self.metrics.get_mut(&provider) {
            metrics.record_success(
                response.response_time_ms,
                response.tokens_used.total_tokens,
                response.cost_usd.unwrap_or(0.0),
            );
        }
    }

    pub fn record_failure(&mut self, provider: ProviderType) {
        if let Some(metrics) = self.metrics.get_mut(&provider) {
            metrics.record_failure();
        }
    }

    pub fn get_metrics(&self) -> &HashMap<ProviderType, ProviderMetrics> {
        &self.metrics
    }

    pub fn update_config(&mut self, config: RoutingConfig) {
        self.config = config;
    }
}

// Helper trait for sorting
trait SortedBy<T> {
    fn sorted_by<F>(self, compare: F) -> Vec<T>
    where
        F: FnMut(&T, &T) -> std::cmp::Ordering;
}

impl<I, T> SortedBy<T> for I
where
    I: Iterator<Item = T>,
{
    fn sorted_by<F>(self, mut compare: F) -> Vec<T>
    where
        F: FnMut(&T, &T) -> std::cmp::Ordering,
    {
        let mut vec: Vec<T> = self.collect();
        vec.sort_by(&mut compare);
        vec
    }
}

trait DurationExt {
    fn from_mins(mins: u64) -> Duration;
}

impl DurationExt for Duration {
    fn from_mins(mins: u64) -> Duration {
        Duration::from_secs(mins * 60)
    }
}