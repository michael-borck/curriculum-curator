use crate::llm::{
    LLMProvider, LLMRequest, LLMResponse, LLMError, LLMResult, ProviderType,
    TokenUsage, FinishReason, ProviderConfig, ModelInfo, ModelCapabilities, ProviderUsageStats,
    ProviderFeature, ProviderLimits
};
use async_trait::async_trait;
use reqwest::Client;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::time::Instant;
use futures::{Stream, StreamExt};
use std::pin::Pin;
use tokio_stream::wrappers::LinesStream;
use tokio::io::{AsyncBufReadExt, BufReader};
use tokio_util::io::StreamReader;

#[derive(Debug, Clone)]
pub struct OpenAIProvider {
    config: ProviderConfig,
    client: Client,
    usage_stats: ProviderUsageStats,
}

#[derive(Debug, Serialize)]
struct OpenAIRequest {
    model: String,
    messages: Vec<OpenAIMessage>,
    temperature: Option<f32>,
    max_tokens: Option<u32>,
    stream: bool,
}

#[derive(Debug, Serialize, Deserialize)]
struct OpenAIMessage {
    role: String,
    content: String,
}

#[derive(Debug, Deserialize)]
struct OpenAIResponse {
    id: String,
    object: String,
    created: u64,
    model: String,
    choices: Vec<OpenAIChoice>,
    usage: OpenAIUsage,
}

#[derive(Debug, Deserialize)]
struct OpenAIChoice {
    index: u32,
    message: OpenAIMessage,
    finish_reason: Option<String>,
}

#[derive(Debug, Deserialize)]
struct OpenAIUsage {
    prompt_tokens: u32,
    completion_tokens: u32,
    total_tokens: u32,
}

#[derive(Debug, Deserialize)]
struct OpenAIErrorResponse {
    error: OpenAIError,
}

#[derive(Debug, Deserialize)]
struct OpenAIError {
    message: String,
    r#type: Option<String>,
    code: Option<String>,
}

#[derive(Debug, Deserialize)]
struct OpenAIModelsResponse {
    data: Vec<OpenAIModel>,
}

#[derive(Debug, Deserialize)]
struct OpenAIModel {
    id: String,
    object: String,
    created: u64,
    owned_by: String,
}

#[derive(Debug, Deserialize)]
struct OpenAIStreamResponse {
    id: String,
    object: String,
    created: u64,
    model: String,
    choices: Vec<OpenAIStreamChoice>,
}

#[derive(Debug, Deserialize)]
struct OpenAIStreamChoice {
    index: u32,
    delta: OpenAIStreamDelta,
    finish_reason: Option<String>,
}

#[derive(Debug, Deserialize)]
struct OpenAIStreamDelta {
    content: Option<String>,
    role: Option<String>,
}

impl OpenAIProvider {
    pub fn new(api_key: String, base_url: Option<String>) -> Self {
        let base_url = base_url.unwrap_or_else(|| "https://api.openai.com/v1".to_string());
        
        let config = ProviderConfig {
            name: "OpenAI".to_string(),
            base_url: base_url.clone(),
            api_key: Some(api_key),
            default_model: Some("gpt-3.5-turbo".to_string()),
            max_tokens_per_request: Some(4096),
            rate_limit_requests_per_minute: Some(3500),
            cost_per_input_token: Some(0.0015 / 1000.0), // $0.0015 per 1K tokens for gpt-3.5-turbo
            cost_per_output_token: Some(0.002 / 1000.0), // $0.002 per 1K tokens for gpt-3.5-turbo
            supports_streaming: true,
            supports_system_prompt: true,
            supports_function_calling: true,
        };

        let client = Client::new();
        let usage_stats = ProviderUsageStats::default();

        Self {
            config,
            client,
            usage_stats,
        }
    }

    fn get_authorization_header(&self) -> Option<String> {
        self.config.api_key.as_ref().map(|key| format!("Bearer {}", key))
    }

    fn build_messages(&self, request: &LLMRequest) -> Vec<OpenAIMessage> {
        let mut messages = Vec::new();

        // Add system message if provided
        if let Some(system_prompt) = &request.system_prompt {
            messages.push(OpenAIMessage {
                role: "system".to_string(),
                content: system_prompt.clone(),
            });
        }

        // Add context if provided (as assistant message)
        if let Some(context) = &request.context {
            messages.push(OpenAIMessage {
                role: "assistant".to_string(),
                content: context.clone(),
            });
        }

        // Add main user message
        messages.push(OpenAIMessage {
            role: "user".to_string(),
            content: request.prompt.clone(),
        });

        messages
    }

    fn parse_finish_reason(&self, reason: Option<String>) -> FinishReason {
        match reason.as_deref() {
            Some("stop") => FinishReason::Stop,
            Some("length") => FinishReason::Length,
            Some("content_filter") => FinishReason::ContentFilter,
            Some("function_call") => FinishReason::FunctionCall,
            Some(other) => FinishReason::Other(other.to_string()),
            None => FinishReason::Error("No finish reason provided".to_string()),
        }
    }

    fn calculate_cost(&self, usage: &OpenAIUsage, model: &str) -> f64 {
        // Model-specific pricing (as of 2024)
        let (input_cost, output_cost) = match model {
            "gpt-4" => (0.03 / 1000.0, 0.06 / 1000.0),
            "gpt-4-turbo" | "gpt-4-turbo-preview" => (0.01 / 1000.0, 0.03 / 1000.0),
            "gpt-3.5-turbo" => (0.0015 / 1000.0, 0.002 / 1000.0),
            "gpt-3.5-turbo-16k" => (0.003 / 1000.0, 0.004 / 1000.0),
            _ => (self.config.cost_per_input_token.unwrap_or(0.0), 
                  self.config.cost_per_output_token.unwrap_or(0.0)),
        };

        (usage.prompt_tokens as f64 * input_cost) + (usage.completion_tokens as f64 * output_cost)
    }
}

#[async_trait]
impl LLMProvider for OpenAIProvider {
    fn provider_type(&self) -> ProviderType {
        ProviderType::OpenAI
    }

    fn config(&self) -> &ProviderConfig {
        &self.config
    }

    async fn health_check(&self) -> LLMResult<bool> {
        let auth_header = self.get_authorization_header()
            .ok_or_else(|| LLMError::Auth("No API key configured".to_string()))?;

        let url = format!("{}/models", self.config.base_url);
        
        let response = self.client
            .get(&url)
            .header("Authorization", auth_header)
            .header("Content-Type", "application/json")
            .send()
            .await
            .map_err(|e| LLMError::Network(e.to_string()))?;

        Ok(response.status().is_success())
    }

    async fn list_models(&self) -> LLMResult<Vec<ModelInfo>> {
        let auth_header = self.get_authorization_header()
            .ok_or_else(|| LLMError::Auth("No API key configured".to_string()))?;

        let url = format!("{}/models", self.config.base_url);
        
        let response = self.client
            .get(&url)
            .header("Authorization", auth_header)
            .header("Content-Type", "application/json")
            .send()
            .await
            .map_err(|e| LLMError::Network(e.to_string()))?;

        if !response.status().is_success() {
            let error_text = response.text().await.unwrap_or_else(|_| "Unknown error".to_string());
            return Err(LLMError::Provider(format!("Failed to list models: {}", error_text)));
        }

        let models_response: OpenAIModelsResponse = response.json().await
            .map_err(|e| LLMError::Provider(format!("Failed to parse models response: {}", e)))?;

        let models = models_response.data
            .into_iter()
            .filter(|model| model.id.starts_with("gpt-")) // Only include chat models
            .map(|model| {
                let capabilities = ModelCapabilities {
                    supports_streaming: true,
                    supports_chat: true,
                    supports_completion: true,
                    supports_function_calling: model.id.contains("gpt-4") || model.id.contains("gpt-3.5-turbo"),
                    supports_vision: model.id.contains("vision"),
                    max_output_tokens: Some(4096),
                    max_context_length: self.get_model_context_length(&model.id),
                    supported_languages: vec!["en".to_string(), "es".to_string(), "fr".to_string(), "de".to_string()], // OpenAI supports many languages
                };

                ModelInfo {
                    id: model.id.clone(),
                    name: model.id.clone(),
                    description: format!("OpenAI model owned by {}", model.owned_by),
                    capabilities,
                    parameter_count: None, // OpenAI doesn't expose this
                    context_length: self.get_model_context_length(&model.id),
                    cost_per_1k_prompt_tokens: Some(0.03),
                    cost_per_1k_completion_tokens: Some(0.06),
                }
            })
            .collect();

        Ok(models)
    }

    async fn generate(&self, request: &LLMRequest) -> LLMResult<LLMResponse> {
        let start_time = Instant::now();

        let auth_header = self.get_authorization_header()
            .ok_or_else(|| LLMError::Auth("No API key configured".to_string()))?;

        // Validate request
        self.validate_request(request)?;

        let model = request.model.clone()
            .or_else(|| self.config.default_model.clone())
            .ok_or_else(|| LLMError::InvalidRequest("No model specified".to_string()))?;

        let messages = self.build_messages(request);

        let openai_request = OpenAIRequest {
            model: model.clone(),
            messages,
            temperature: request.temperature,
            max_tokens: request.max_tokens,
            stream: false,
        };

        let url = format!("{}/chat/completions", self.config.base_url);

        let response = self.client
            .post(&url)
            .header("Authorization", auth_header)
            .header("Content-Type", "application/json")
            .json(&openai_request)
            .send()
            .await
            .map_err(|e| LLMError::Network(e.to_string()))?;

        let status = response.status();
        let response_time = start_time.elapsed();

        if !status.is_success() {
            let error_text = response.text().await.unwrap_or_else(|_| "Unknown error".to_string());
            
            // Try to parse as OpenAI error response
            if let Ok(error_response) = serde_json::from_str::<OpenAIErrorResponse>(&error_text) {
                let error_msg = error_response.error.message;
                return match status.as_u16() {
                    401 => Err(LLMError::Auth(error_msg)),
                    400 => Err(LLMError::InvalidRequest(error_msg)),
                    429 => Err(LLMError::RateLimit(error_msg)),
                    _ => Err(LLMError::Provider(error_msg)),
                };
            }
            
            return Err(LLMError::Provider(format!("HTTP {}: {}", status, error_text)));
        }

        let openai_response: OpenAIResponse = response.json().await
            .map_err(|e| LLMError::Provider(format!("Failed to parse response: {}", e)))?;

        let choice = openai_response.choices.into_iter().next()
            .ok_or_else(|| LLMError::Provider("No choices in response".to_string()))?;

        let content = choice.message.content;
        let finish_reason = self.parse_finish_reason(choice.finish_reason);

        let tokens_used = TokenUsage::new(
            openai_response.usage.prompt_tokens,
            openai_response.usage.completion_tokens,
        );

        let cost_usd = self.calculate_cost(&openai_response.usage, &model);

        let mut metadata = HashMap::new();
        metadata.insert("openai_id".to_string(), serde_json::Value::String(openai_response.id));
        metadata.insert("openai_object".to_string(), serde_json::Value::String(openai_response.object));
        metadata.insert("openai_created".to_string(), serde_json::Value::Number(openai_response.created.into()));

        Ok(LLMResponse {
            content,
            model_used: openai_response.model,
            tokens_used,
            cost_usd: Some(cost_usd),
            finish_reason,
            response_time_ms: response_time.as_millis() as u64,
            metadata,
        })
    }

    fn validate_request(&self, request: &LLMRequest) -> LLMResult<()> {
        if request.prompt.is_empty() {
            return Err(LLMError::InvalidRequest("Prompt cannot be empty".to_string()));
        }

        // Estimate token count (rough approximation: 4 characters per token)
        let estimated_tokens = (request.prompt.len() + 
            request.system_prompt.as_ref().map_or(0, |s| s.len()) +
            request.context.as_ref().map_or(0, |s| s.len())) / 4;

        let max_tokens = request.max_tokens.unwrap_or(1000);
        let model = request.model.as_ref()
            .or(self.config.default_model.as_ref())
            .ok_or_else(|| LLMError::InvalidRequest("No model specified".to_string()))?;

        let context_limit = self.get_model_context_length(model);
        
        if estimated_tokens + max_tokens as usize > context_limit as usize {
            return Err(LLMError::InvalidRequest(
                format!("Request too long: estimated {} tokens exceeds model limit of {}", 
                    estimated_tokens + max_tokens as usize, context_limit)
            ));
        }

        if let Some(temp) = request.temperature {
            if !(0.0..=2.0).contains(&temp) {
                return Err(LLMError::InvalidRequest("Temperature must be between 0.0 and 2.0".to_string()));
            }
        }

        Ok(())
    }

    async fn estimate_cost(&self, request: &LLMRequest) -> LLMResult<f64> {
        let default_model = "gpt-3.5-turbo".to_string();
        let model = request.model.as_ref()
            .or(self.config.default_model.as_ref())
            .unwrap_or(&default_model);

        // Rough token estimation
        let input_tokens = (request.prompt.len() + 
            request.system_prompt.as_ref().map_or(0, |s| s.len()) +
            request.context.as_ref().map_or(0, |s| s.len())) / 4;
        let output_tokens = request.max_tokens.unwrap_or(500) as usize;

        let (input_cost, output_cost) = match model.as_str() {
            "gpt-4" => (0.03 / 1000.0, 0.06 / 1000.0),
            "gpt-4-turbo" | "gpt-4-turbo-preview" => (0.01 / 1000.0, 0.03 / 1000.0),
            "gpt-3.5-turbo" => (0.0015 / 1000.0, 0.002 / 1000.0),
            "gpt-3.5-turbo-16k" => (0.003 / 1000.0, 0.004 / 1000.0),
            _ => (0.002 / 1000.0, 0.002 / 1000.0), // Default estimate
        };

        Ok((input_tokens as f64 * input_cost) + (output_tokens as f64 * output_cost))
    }

    async fn get_usage_stats(&self) -> LLMResult<ProviderUsageStats> {
        Ok(self.usage_stats.clone())
    }

    async fn generate_stream(&self, request: &LLMRequest) -> LLMResult<Box<dyn futures::Stream<Item = LLMResult<String>> + Send + Unpin>> {
        let auth_header = self.get_authorization_header()
            .ok_or_else(|| LLMError::Auth("No API key configured".to_string()))?;

        // Validate request
        self.validate_request(request)?;

        let model = request.model.clone()
            .or_else(|| self.config.default_model.clone())
            .ok_or_else(|| LLMError::InvalidRequest("No model specified".to_string()))?;

        let messages = self.build_messages(request);

        let openai_request = OpenAIRequest {
            model: model.clone(),
            messages,
            temperature: request.temperature,
            max_tokens: request.max_tokens,
            stream: true,
        };

        let url = format!("{}/chat/completions", self.config.base_url);

        let response = self.client
            .post(&url)
            .header("Authorization", auth_header)
            .header("Content-Type", "application/json")
            .json(&openai_request)
            .send()
            .await
            .map_err(|e| LLMError::Network(e.to_string()))?;

        let status = response.status();
        if !status.is_success() {
            let error_text = response.text().await.unwrap_or_else(|_| "Unknown error".to_string());
            return Err(LLMError::Provider(format!("HTTP {}: {}", status, error_text)));
        }

        // Convert the response body to a stream of lines
        let byte_stream = response.bytes_stream();
        let stream_reader = StreamReader::new(byte_stream.map(|chunk| {
            chunk.map_err(|e| std::io::Error::new(std::io::ErrorKind::Other, e))
        }));
        let buf_reader = BufReader::new(stream_reader);
        let lines_stream = LinesStream::new(buf_reader.lines());

        let processed_stream = lines_stream.filter_map(|line_result| async move {
            match line_result {
                Ok(line) => {
                    // OpenAI sends data in the format "data: {json}" or "data: [DONE]"
                    if line.starts_with("data: ") {
                        let json_str = &line[6..]; // Remove "data: " prefix
                        
                        if json_str == "[DONE]" {
                            return None; // End of stream
                        }
                        
                        // Parse the JSON chunk
                        match serde_json::from_str::<OpenAIStreamResponse>(json_str) {
                            Ok(chunk) => {
                                if let Some(choice) = chunk.choices.first() {
                                    if let Some(content) = &choice.delta.content {
                                        return Some(Ok(content.clone()));
                                    }
                                }
                                None // Skip chunks without content
                            }
                            Err(e) => Some(Err(LLMError::Provider(format!("Failed to parse stream chunk: {}", e))))
                        }
                    } else {
                        None // Skip non-data lines
                    }
                }
                Err(e) => Some(Err(LLMError::Network(format!("Stream error: {}", e))))
            }
        });

        Ok(Box::new(Box::pin(processed_stream)))
    }

    async fn count_tokens(&self, text: &str, _model: Option<&str>) -> LLMResult<u32> {
        // Simple estimation: ~4 characters per token
        Ok((text.len() / 4) as u32)
    }

    async fn get_model_info(&self, model_id: &str) -> LLMResult<ModelInfo> {
        let context_length = self.get_model_context_length(model_id);
        
        let (cost_prompt, cost_completion) = match model_id {
            "gpt-4" => (Some(0.03), Some(0.06)),
            "gpt-4-turbo" | "gpt-4-turbo-preview" => (Some(0.01), Some(0.03)),
            "gpt-3.5-turbo" => (Some(0.0015), Some(0.002)),
            "gpt-3.5-turbo-16k" => (Some(0.003), Some(0.004)),
            _ => (Some(0.002), Some(0.002)), // Default estimate
        };

        Ok(ModelInfo {
            id: model_id.to_string(),
            name: model_id.to_string(),
            description: format!("OpenAI model: {}", model_id),
            parameter_count: None,
            context_length,
            cost_per_1k_prompt_tokens: cost_prompt,
            cost_per_1k_completion_tokens: cost_completion,
            capabilities: ModelCapabilities {
                supports_streaming: true,
                supports_function_calling: model_id.contains("gpt-4") || model_id.contains("gpt-3.5-turbo"),
                supports_vision: model_id.contains("vision") || model_id.contains("gpt-4-turbo"),
                supports_chat: true,
                supports_completion: true,
                max_output_tokens: Some(4096),
                max_context_length: context_length,
                supported_languages: vec!["en".to_string(), "es".to_string(), "fr".to_string()],
            },
        })
    }

    fn supports_feature(&self, feature: ProviderFeature) -> bool {
        use crate::llm::ProviderFeature;
        match feature {
            ProviderFeature::Streaming => true,
            ProviderFeature::FunctionCalling => true,
            ProviderFeature::Vision => true,
            ProviderFeature::SystemPrompt => true,
            ProviderFeature::ContextWindow => true,
            ProviderFeature::CostTracking => true,
            ProviderFeature::RateLimiting => true,
            ProviderFeature::BatchProcessing => false,
            ProviderFeature::JsonMode => true,
        }
    }

    fn default_model(&self) -> Option<String> {
        Some("gpt-3.5-turbo".to_string())
    }

    fn get_limits(&self) -> ProviderLimits {
        ProviderLimits {
            max_tokens_per_request: 4096,
            max_requests_per_minute: 3000,
            max_tokens_per_minute: 150000,
            max_context_length: 128000, // GPT-4 Turbo max
            max_output_tokens: 4096,
            min_temperature: 0.0,
            max_temperature: 2.0,
        }
    }
}

impl OpenAIProvider {
    fn get_model_context_length(&self, model: &str) -> u32 {
        match model {
            "gpt-4" => 8192,
            "gpt-4-32k" => 32768,
            "gpt-4-turbo" | "gpt-4-turbo-preview" => 128000,
            "gpt-3.5-turbo" => 4096,
            "gpt-3.5-turbo-16k" => 16384,
            _ => 4096, // Default fallback
        }
    }
}