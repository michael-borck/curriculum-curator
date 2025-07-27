use crate::llm::{
    LLMProvider, LLMRequest, LLMResponse, LLMError, LLMResult, ProviderType, 
    ProviderConfig, ModelInfo, ModelCapabilities, TokenUsage, FinishReason,
    ProviderUsageStats, ProviderFeature, ProviderLimits
};
use reqwest::Client;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::time::{Duration, Instant};
use futures::Stream;

pub struct OllamaProvider {
    config: ProviderConfig,
    client: Client,
    usage_stats: ProviderUsageStats,
}

#[derive(Debug, Deserialize)]
struct OllamaModelsResponse {
    models: Vec<OllamaModel>,
}

#[derive(Debug, Deserialize)]
struct OllamaModel {
    name: String,
    model: String,
    modified_at: String,
    size: u64,
    digest: String,
    details: OllamaModelDetails,
}

#[derive(Debug, Deserialize)]
struct OllamaModelDetails {
    parent_model: Option<String>,
    format: String,
    family: String,
    families: Option<Vec<String>>,
    parameter_size: String,
    quantization_level: String,
}

#[derive(Debug, Serialize)]
struct OllamaGenerateRequest {
    model: String,
    prompt: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    system: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    context: Option<Vec<i32>>,
    #[serde(skip_serializing_if = "Option::is_none")]
    options: Option<OllamaOptions>,
    stream: bool,
}

#[derive(Debug, Serialize)]
struct OllamaOptions {
    #[serde(skip_serializing_if = "Option::is_none")]
    temperature: Option<f32>,
    #[serde(skip_serializing_if = "Option::is_none")]
    num_predict: Option<u32>,
    #[serde(skip_serializing_if = "Option::is_none")]
    top_k: Option<u32>,
    #[serde(skip_serializing_if = "Option::is_none")]
    top_p: Option<f32>,
    #[serde(skip_serializing_if = "Option::is_none")]
    frequency_penalty: Option<f32>,
    #[serde(skip_serializing_if = "Option::is_none")]
    presence_penalty: Option<f32>,
    #[serde(skip_serializing_if = "Option::is_none")]
    stop: Option<Vec<String>>,
}

#[derive(Debug, Deserialize)]
struct OllamaGenerateResponse {
    model: String,
    created_at: String,
    response: String,
    done: bool,
    #[serde(skip_serializing_if = "Option::is_none")]
    context: Option<Vec<i32>>,
    #[serde(skip_serializing_if = "Option::is_none")]
    total_duration: Option<u64>,
    #[serde(skip_serializing_if = "Option::is_none")]
    load_duration: Option<u64>,
    #[serde(skip_serializing_if = "Option::is_none")]
    prompt_eval_count: Option<u32>,
    #[serde(skip_serializing_if = "Option::is_none")]
    prompt_eval_duration: Option<u64>,
    #[serde(skip_serializing_if = "Option::is_none")]
    eval_count: Option<u32>,
    #[serde(skip_serializing_if = "Option::is_none")]
    eval_duration: Option<u64>,
}

impl OllamaProvider {
    pub fn new(base_url: Option<String>) -> Self {
        let base_url = base_url.unwrap_or_else(|| "http://localhost:11434".to_string());
        
        let config = ProviderConfig {
            name: "Ollama".to_string(),
            base_url: base_url.clone(),
            api_key: None, // Ollama doesn't require API keys
            default_model: Some("llama3.2:3b".to_string()), // Updated default model for better performance
            max_tokens_per_request: Some(4096),
            rate_limit_requests_per_minute: None, // No rate limiting for local
            cost_per_input_token: None, // Local is free
            cost_per_output_token: None, // Local is free
            supports_streaming: true,
            supports_system_prompt: true,
            supports_function_calling: false,
        };

        let client = Client::builder()
            .timeout(Duration::from_secs(120))
            .build()
            .expect("Failed to create HTTP client");

        Self {
            config,
            client,
            usage_stats: ProviderUsageStats::default(),
        }
    }

    fn get_base_url(&self) -> &str {
        &self.config.base_url
    }

    fn build_ollama_request(&self, request: &LLMRequest) -> OllamaGenerateRequest {
        let model = request.model.clone().unwrap_or_else(|| self.config.default_model.clone().unwrap_or_else(|| "llama3.2:3b".to_string()));
        
        let has_options = request.temperature.is_some() || 
                         request.max_tokens.is_some() || 
                         request.top_p.is_some() ||
                         request.frequency_penalty.is_some() ||
                         request.presence_penalty.is_some() ||
                         request.stop_sequences.is_some();
        
        let options = if has_options {
            Some(OllamaOptions {
                temperature: request.temperature,
                num_predict: request.max_tokens,
                top_k: None, // Ollama doesn't directly support top_k in our interface
                top_p: request.top_p,
                frequency_penalty: request.frequency_penalty,
                presence_penalty: request.presence_penalty,
                stop: request.stop_sequences.clone(),
            })
        } else {
            None
        };

        OllamaGenerateRequest {
            model,
            prompt: request.prompt.clone(),
            system: request.system_prompt.clone(),
            context: None, // Could be implemented for conversation context
            options,
            stream: request.stream,
        }
    }

    fn parse_ollama_response(&self, ollama_response: OllamaGenerateResponse, start_time: Instant) -> LLMResponse {
        let response_time_ms = start_time.elapsed().as_millis() as u64;
        
        let tokens_used = TokenUsage::new(
            ollama_response.prompt_eval_count.unwrap_or(0),
            ollama_response.eval_count.unwrap_or(0),
        );

        let mut metadata = HashMap::new();
        if let Some(total_duration) = ollama_response.total_duration {
            metadata.insert("total_duration_ns".to_string(), serde_json::Value::Number(serde_json::Number::from(total_duration)));
        }
        if let Some(load_duration) = ollama_response.load_duration {
            metadata.insert("load_duration_ns".to_string(), serde_json::Value::Number(serde_json::Number::from(load_duration)));
        }

        LLMResponse {
            content: ollama_response.response,
            model_used: ollama_response.model,
            tokens_used,
            cost_usd: None, // Local models have no cost
            finish_reason: if ollama_response.done { FinishReason::Stop } else { FinishReason::Length },
            response_time_ms,
            metadata,
        }
    }

    fn estimate_tokens(&self, text: &str) -> u32 {
        // Simple estimation: ~4 characters per token for English text
        // This is a rough approximation; real tokenization would be more accurate
        (text.len() as f32 / 4.0).ceil() as u32
    }
}

#[async_trait::async_trait]
impl LLMProvider for OllamaProvider {
    fn provider_type(&self) -> ProviderType {
        ProviderType::Ollama
    }

    fn config(&self) -> &ProviderConfig {
        &self.config
    }

    async fn health_check(&self) -> LLMResult<bool> {
        let url = format!("{}/api/tags", self.get_base_url());
        
        match self.client.get(&url).send().await {
            Ok(response) => {
                if response.status().is_success() {
                    Ok(true)
                } else {
                    Err(LLMError::Provider(format!("Ollama health check failed with status: {}", response.status())))
                }
            }
            Err(e) => {
                if e.is_connect() {
                    Err(LLMError::Network("Cannot connect to Ollama server. Is Ollama running?".to_string()))
                } else if e.is_timeout() {
                    Err(LLMError::Timeout("Ollama health check timed out".to_string()))
                } else {
                    Err(LLMError::Network(format!("Ollama health check failed: {}", e)))
                }
            }
        }
    }

    async fn list_models(&self) -> LLMResult<Vec<ModelInfo>> {
        let url = format!("{}/api/tags", self.get_base_url());
        
        let response = self.client.get(&url).send().await
            .map_err(|e| LLMError::Network(format!("Failed to fetch models: {}", e)))?;

        if !response.status().is_success() {
            return Err(LLMError::Provider(format!("Failed to list models: {}", response.status())));
        }

        let ollama_response: OllamaModelsResponse = response.json().await
            .map_err(|e| LLMError::Provider(format!("Failed to parse models response: {}", e)))?;

        let models = ollama_response.models.into_iter().map(|model| {
            // Extract context length from parameter size and model name
            let context_length = match model.details.parameter_size.as_str() {
                s if s.contains("7B") => 8192, // Modern 7B models often have larger context
                s if s.contains("13B") => 8192,
                s if s.contains("34B") => 8192,
                s if s.contains("70B") => 8192,
                s if s.contains("3B") => 8192, // Llama 3.2 3B has good context length
                _ => match model.name.as_str() {
                    name if name.contains("llama3") => 8192, // Llama 3 models
                    name if name.contains("codellama") => 16384, // Code models
                    name if name.contains("mistral") => 8192, // Mistral models
                    _ => 4096, // Conservative default for unknown models
                },
            };

            ModelInfo {
                id: model.name.clone(),
                name: model.model.clone(),
                description: format!("Ollama model: {}", model.model),
                parameter_count: None, // Ollama doesn't expose parameter count
                context_length,
                cost_per_1k_prompt_tokens: None, // Local models are free
                cost_per_1k_completion_tokens: None,
                capabilities: ModelCapabilities {
                    supports_streaming: true,
                    supports_function_calling: false, // Most Ollama models don't support this
                    supports_vision: model.details.family.contains("vision") || model.details.family.contains("llava"),
                    supports_chat: true,
                    supports_completion: true,
                    max_output_tokens: Some(context_length / 2), // Conservative estimate
                    max_context_length: context_length,
                    supported_languages: vec!["en".to_string()], // Most models support English
                },
            }
        }).collect();

        Ok(models)
    }

    async fn generate(&self, request: &LLMRequest) -> LLMResult<LLMResponse> {
        let start_time = Instant::now();
        let url = format!("{}/api/generate", self.get_base_url());
        let ollama_request = self.build_ollama_request(request);

        let response = self.client
            .post(&url)
            .json(&ollama_request)
            .send()
            .await
            .map_err(|e| {
                if e.is_connect() {
                    LLMError::Network("Cannot connect to Ollama server. Is Ollama running?".to_string())
                } else if e.is_timeout() {
                    LLMError::Timeout("Request to Ollama timed out".to_string())
                } else {
                    LLMError::Network(format!("Request failed: {}", e))
                }
            })?;

        if !response.status().is_success() {
            let status = response.status();
            let error_text = response.text().await.unwrap_or_else(|_| "Unknown error".to_string());
            return Err(LLMError::Provider(format!("Ollama returned error {}: {}", status, error_text)));
        }

        let ollama_response: OllamaGenerateResponse = response.json().await
            .map_err(|e| LLMError::Provider(format!("Failed to parse response: {}", e)))?;

        Ok(self.parse_ollama_response(ollama_response, start_time))
    }

    async fn generate_stream(&self, request: &LLMRequest) -> LLMResult<Box<dyn Stream<Item = LLMResult<String>> + Send + Unpin>> {
        let url = format!("{}/api/generate", self.get_base_url());
        let mut ollama_request = self.build_ollama_request(request);
        ollama_request.stream = true;

        let response = self.client
            .post(&url)
            .json(&ollama_request)
            .send()
            .await
            .map_err(|e| LLMError::Network(format!("Stream request failed: {}", e)))?;

        if !response.status().is_success() {
            return Err(LLMError::Provider(format!("Ollama stream failed with status: {}", response.status())));
        }

        // Convert reqwest's stream to our stream type
        let stream = response.bytes_stream();
        let mapped_stream = futures::stream::unfold(stream, |mut stream| async move {
            use futures::StreamExt;
            match stream.next().await {
                Some(Ok(bytes)) => {
                    // Parse each line as JSON
                    let text = String::from_utf8_lossy(&bytes);
                    for line in text.lines() {
                        if !line.trim().is_empty() {
                            if let Ok(response) = serde_json::from_str::<OllamaGenerateResponse>(line) {
                                return Some((Ok(response.response), stream));
                            }
                        }
                    }
                    Some((Err(LLMError::Provider("Invalid stream response".to_string())), stream))
                }
                Some(Err(e)) => Some((Err(LLMError::Network(format!("Stream error: {}", e))), stream)),
                None => None,
            }
        });

        Ok(Box::new(Box::pin(mapped_stream)))
    }

    async fn estimate_cost(&self, _request: &LLMRequest) -> LLMResult<f64> {
        // Local Ollama models are free
        Ok(0.0)
    }

    async fn count_tokens(&self, text: &str, _model: Option<&str>) -> LLMResult<u32> {
        // Simple estimation for now
        // In a production implementation, we might use a tokenizer library
        Ok(self.estimate_tokens(text))
    }

    fn validate_request(&self, request: &LLMRequest) -> LLMResult<()> {
        if request.prompt.is_empty() {
            return Err(LLMError::InvalidRequest("Prompt cannot be empty".to_string()));
        }

        if let Some(max_tokens) = request.max_tokens {
            if max_tokens == 0 {
                return Err(LLMError::InvalidRequest("Max tokens must be greater than 0".to_string()));
            }
        }

        if let Some(temperature) = request.temperature {
            if !(0.0..=2.0).contains(&temperature) {
                return Err(LLMError::InvalidRequest("Temperature must be between 0.0 and 2.0".to_string()));
            }
        }

        Ok(())
    }

    async fn get_usage_stats(&self) -> LLMResult<ProviderUsageStats> {
        // Return current usage stats
        // In a production implementation, this would be tracked in a database
        Ok(self.usage_stats.clone())
    }
    
    async fn get_model_info(&self, model_id: &str) -> LLMResult<ModelInfo> {
        // First try to get from the full model list
        let models = self.list_models().await?;
        
        if let Some(model) = models.into_iter().find(|m| m.id == model_id || m.name == model_id) {
            return Ok(model);
        }
        
        // If not found in list, create a basic model info
        // This might happen if the model exists but isn't currently downloaded
        let context_length = match model_id {
            id if id.contains("7b") || id.contains("7B") => 4096,
            id if id.contains("13b") || id.contains("13B") => 4096,
            id if id.contains("34b") || id.contains("34B") => 8192,
            id if id.contains("70b") || id.contains("70B") => 8192,
            id if id.contains("codellama") => 16384,
            _ => 2048,
        };
        
        Ok(ModelInfo {
            id: model_id.to_string(),
            name: model_id.to_string(),
            description: format!("Ollama model: {}", model_id),
            parameter_count: None,
            context_length,
            cost_per_1k_prompt_tokens: None,
            cost_per_1k_completion_tokens: None,
            capabilities: ModelCapabilities {
                supports_streaming: true,
                supports_function_calling: false,
                supports_vision: model_id.contains("vision") || model_id.contains("llava"),
                supports_chat: true,
                supports_completion: true,
                max_output_tokens: Some(context_length / 2),
                max_context_length: context_length,
                supported_languages: vec!["en".to_string()],
            },
        })
    }
    
    fn supports_feature(&self, feature: ProviderFeature) -> bool {
        match feature {
            ProviderFeature::Streaming => true,
            ProviderFeature::SystemPrompt => true,
            ProviderFeature::ContextWindow => true,
            ProviderFeature::FunctionCalling => false, // Most Ollama models don't support this
            ProviderFeature::Vision => false, // Depends on specific model
            ProviderFeature::CostTracking => false, // Local models are free
            ProviderFeature::RateLimiting => false, // No rate limiting for local
            ProviderFeature::BatchProcessing => false, // Not implemented
            ProviderFeature::JsonMode => false, // Not commonly supported
        }
    }
    
    fn default_model(&self) -> Option<String> {
        self.config.default_model.clone()
    }
    
    fn get_limits(&self) -> ProviderLimits {
        ProviderLimits {
            max_tokens_per_request: 4096,
            max_requests_per_minute: u32::MAX, // No rate limiting for local
            max_tokens_per_minute: u32::MAX,
            max_context_length: 4096, // Default, varies by model
            max_output_tokens: 2048,
            min_temperature: 0.0,
            max_temperature: 2.0,
        }
    }
}