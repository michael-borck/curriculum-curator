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
pub struct ClaudeProvider {
    config: ProviderConfig,
    client: Client,
    usage_stats: ProviderUsageStats,
}

#[derive(Debug, Serialize)]
struct ClaudeRequest {
    model: String,
    max_tokens: u32,
    messages: Vec<ClaudeMessage>,
    #[serde(skip_serializing_if = "Option::is_none")]
    system: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    temperature: Option<f32>,
    #[serde(skip_serializing_if = "Option::is_none")]
    stream: Option<bool>,
}

#[derive(Debug, Serialize, Deserialize)]
struct ClaudeMessage {
    role: String,
    content: String,
}

#[derive(Debug, Deserialize)]
struct ClaudeResponse {
    id: String,
    r#type: String,
    role: String,
    content: Vec<ClaudeContent>,
    model: String,
    stop_reason: Option<String>,
    stop_sequence: Option<String>,
    usage: ClaudeUsage,
}

#[derive(Debug, Deserialize)]
struct ClaudeContent {
    r#type: String,
    text: String,
}

#[derive(Debug, Deserialize)]
struct ClaudeUsage {
    input_tokens: u32,
    output_tokens: u32,
}

#[derive(Debug, Deserialize)]
struct ClaudeErrorResponse {
    r#type: String,
    error: ClaudeError,
}

#[derive(Debug, Deserialize)]
struct ClaudeError {
    r#type: String,
    message: String,
}

#[derive(Debug, Deserialize)]
struct ClaudeStreamResponse {
    r#type: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    message: Option<ClaudeStreamMessage>,
    #[serde(skip_serializing_if = "Option::is_none")]
    delta: Option<ClaudeStreamDelta>,
}

#[derive(Debug, Deserialize)]
struct ClaudeStreamMessage {
    id: String,
    r#type: String,
    role: String,
    content: Vec<ClaudeContent>,
    model: String,
    stop_reason: Option<String>,
    stop_sequence: Option<String>,
    usage: ClaudeUsage,
}

#[derive(Debug, Deserialize)]
struct ClaudeStreamDelta {
    r#type: String,
    text: Option<String>,
    stop_reason: Option<String>,
}

impl ClaudeProvider {
    pub fn new(api_key: String, base_url: Option<String>) -> Self {
        let base_url = base_url.unwrap_or_else(|| "https://api.anthropic.com".to_string());
        
        let config = ProviderConfig {
            name: "Claude (Anthropic)".to_string(),
            base_url: base_url.clone(),
            api_key: Some(api_key),
            default_model: Some("claude-3-haiku-20240307".to_string()),
            max_tokens_per_request: Some(200000), // Claude has high token limits
            rate_limit_requests_per_minute: Some(1000), // Conservative rate limit
            cost_per_input_token: Some(0.25 / 1_000_000.0), // $0.25 per 1M tokens for Haiku
            cost_per_output_token: Some(1.25 / 1_000_000.0), // $1.25 per 1M tokens for Haiku
            supports_streaming: true,
            supports_system_prompt: true,
            supports_function_calling: false, // Claude 3 doesn't have function calling yet
        };

        let client = Client::new();
        let usage_stats = ProviderUsageStats::default();

        Self {
            config,
            client,
            usage_stats,
        }
    }

    fn get_headers(&self) -> Result<HashMap<String, String>, LLMError> {
        let api_key = self.config.api_key.as_ref()
            .ok_or_else(|| LLMError::Auth("No API key configured".to_string()))?;

        let mut headers = HashMap::new();
        headers.insert("x-api-key".to_string(), api_key.clone());
        headers.insert("anthropic-version".to_string(), "2023-06-01".to_string());
        headers.insert("content-type".to_string(), "application/json".to_string());
        
        Ok(headers)
    }

    fn build_messages(&self, request: &LLMRequest) -> Vec<ClaudeMessage> {
        let mut messages = Vec::new();

        // Add context if provided (as assistant message)
        if let Some(context) = &request.context {
            messages.push(ClaudeMessage {
                role: "assistant".to_string(),
                content: context.clone(),
            });
        }

        // Add main user message
        messages.push(ClaudeMessage {
            role: "user".to_string(),
            content: request.prompt.clone(),
        });

        messages
    }

    fn parse_finish_reason(&self, reason: Option<String>) -> FinishReason {
        match reason.as_deref() {
            Some("end_turn") => FinishReason::Stop,
            Some("max_tokens") => FinishReason::Length,
            Some("stop_sequence") => FinishReason::Stop,
            Some(other) => FinishReason::Other(other.to_string()),
            None => FinishReason::Error("No finish reason provided".to_string()),
        }
    }

    fn calculate_cost(&self, usage: &ClaudeUsage, model: &str) -> f64 {
        // Model-specific pricing (as of 2024)
        let (input_cost, output_cost) = match model {
            "claude-3-opus-20240229" => (15.0 / 1_000_000.0, 75.0 / 1_000_000.0),
            "claude-3-sonnet-20240229" => (3.0 / 1_000_000.0, 15.0 / 1_000_000.0),
            "claude-3-haiku-20240307" => (0.25 / 1_000_000.0, 1.25 / 1_000_000.0),
            _ => (self.config.cost_per_input_token.unwrap_or(0.0), 
                  self.config.cost_per_output_token.unwrap_or(0.0)),
        };

        (usage.input_tokens as f64 * input_cost) + (usage.output_tokens as f64 * output_cost)
    }

    fn get_available_models() -> Vec<ModelInfo> {
        vec![
            ModelInfo {
                id: "claude-3-opus-20240229".to_string(),
                name: "Claude 3 Opus".to_string(),
                description: "Most capable model, best for complex reasoning and analysis".to_string(),
                capabilities: ModelCapabilities {
                    supports_streaming: true,
                    supports_chat: true,
                    supports_completion: true,
                    supports_function_calling: false,
                    supports_vision: true,
                    max_output_tokens: Some(4096),
                    max_context_length: 200000,
                    supported_languages: vec!["en".to_string(), "es".to_string(), "fr".to_string(), "de".to_string(), "it".to_string(), "pt".to_string()],
                },
                parameter_count: None,
                context_length: 200000,
                cost_per_1k_prompt_tokens: Some(15.0),
                cost_per_1k_completion_tokens: Some(75.0),
            },
            ModelInfo {
                id: "claude-3-sonnet-20240229".to_string(),
                name: "Claude 3 Sonnet".to_string(),
                description: "Balanced model, good for most tasks with good speed/quality ratio".to_string(),
                capabilities: ModelCapabilities {
                    supports_streaming: true,
                    supports_chat: true,
                    supports_completion: true,
                    supports_function_calling: false,
                    supports_vision: true,
                    max_output_tokens: Some(4096),
                    max_context_length: 200000,
                    supported_languages: vec!["en".to_string(), "es".to_string(), "fr".to_string(), "de".to_string(), "it".to_string(), "pt".to_string()],
                },
                parameter_count: None,
                context_length: 200000,
                cost_per_1k_prompt_tokens: Some(3.0),
                cost_per_1k_completion_tokens: Some(15.0),
            },
            ModelInfo {
                id: "claude-3-haiku-20240307".to_string(),
                name: "Claude 3 Haiku".to_string(),
                description: "Fastest and most cost-effective model, good for simple tasks".to_string(),
                capabilities: ModelCapabilities {
                    supports_streaming: true,
                    supports_chat: true,
                    supports_completion: true,
                    supports_function_calling: false,
                    supports_vision: true,
                    max_output_tokens: Some(4096),
                    max_context_length: 200000,
                    supported_languages: vec!["en".to_string(), "es".to_string(), "fr".to_string(), "de".to_string(), "it".to_string(), "pt".to_string()],
                },
                parameter_count: None,
                context_length: 200000,
                cost_per_1k_prompt_tokens: Some(0.25),
                cost_per_1k_completion_tokens: Some(1.25),
            },
        ]
    }
}

#[async_trait]
impl LLMProvider for ClaudeProvider {
    fn provider_type(&self) -> ProviderType {
        ProviderType::Claude
    }

    fn config(&self) -> &ProviderConfig {
        &self.config
    }

    async fn health_check(&self) -> LLMResult<bool> {
        let headers = self.get_headers()?;

        // Claude doesn't have a dedicated health endpoint, so we'll make a small request
        let claude_request = ClaudeRequest {
            model: "claude-3-haiku-20240307".to_string(),
            max_tokens: 1,
            messages: vec![ClaudeMessage {
                role: "user".to_string(),
                content: "Hi".to_string(),
            }],
            system: None,
            temperature: None,
            stream: None,
        };

        let url = format!("{}/v1/messages", self.config.base_url);
        
        let mut request_builder = self.client.post(&url);
        for (key, value) in headers {
            request_builder = request_builder.header(&key, &value);
        }

        let response = request_builder
            .json(&claude_request)
            .send()
            .await
            .map_err(|e| LLMError::Network(e.to_string()))?;

        Ok(response.status().is_success())
    }

    async fn list_models(&self) -> LLMResult<Vec<ModelInfo>> {
        // Claude doesn't have a models endpoint, so we return the known models
        Ok(Self::get_available_models())
    }

    async fn generate(&self, request: &LLMRequest) -> LLMResult<LLMResponse> {
        let start_time = Instant::now();

        let headers = self.get_headers()?;

        // Validate request
        self.validate_request(request)?;

        let model = request.model.clone()
            .or_else(|| self.config.default_model.clone())
            .ok_or_else(|| LLMError::InvalidRequest("No model specified".to_string()))?;

        let messages = self.build_messages(request);
        let max_tokens = request.max_tokens.unwrap_or(1000);

        let claude_request = ClaudeRequest {
            model: model.clone(),
            max_tokens,
            messages,
            system: request.system_prompt.clone(),
            temperature: request.temperature,
            stream: Some(false),
        };

        let url = format!("{}/v1/messages", self.config.base_url);

        let mut request_builder = self.client.post(&url);
        for (key, value) in headers {
            request_builder = request_builder.header(&key, &value);
        }

        let response = request_builder
            .json(&claude_request)
            .send()
            .await
            .map_err(|e| LLMError::Network(e.to_string()))?;

        let status = response.status();
        let response_time = start_time.elapsed();

        if !status.is_success() {
            let error_text = response.text().await.unwrap_or_else(|_| "Unknown error".to_string());
            
            // Try to parse as Claude error response
            if let Ok(error_response) = serde_json::from_str::<ClaudeErrorResponse>(&error_text) {
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

        let claude_response: ClaudeResponse = response.json().await
            .map_err(|e| LLMError::Provider(format!("Failed to parse response: {}", e)))?;

        let content = claude_response.content.into_iter()
            .map(|c| c.text)
            .collect::<Vec<_>>()
            .join("");

        let finish_reason = self.parse_finish_reason(claude_response.stop_reason);

        let tokens_used = TokenUsage::new(
            claude_response.usage.input_tokens,
            claude_response.usage.output_tokens,
        );

        let cost_usd = self.calculate_cost(&claude_response.usage, &model);

        let mut metadata = HashMap::new();
        metadata.insert("claude_id".to_string(), serde_json::Value::String(claude_response.id));
        metadata.insert("claude_type".to_string(), serde_json::Value::String(claude_response.r#type));
        if let Some(stop_sequence) = claude_response.stop_sequence {
            metadata.insert("claude_stop_sequence".to_string(), serde_json::Value::String(stop_sequence));
        }

        Ok(LLMResponse {
            content,
            model_used: claude_response.model,
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
        let context_limit = 200000; // Claude 3 has 200K context window

        if estimated_tokens + max_tokens as usize > context_limit {
            return Err(LLMError::InvalidRequest(
                format!("Request too long: estimated {} tokens exceeds model limit of {}", 
                    estimated_tokens + max_tokens as usize, context_limit)
            ));
        }

        if let Some(temp) = request.temperature {
            if !(0.0..=1.0).contains(&temp) {
                return Err(LLMError::InvalidRequest("Temperature must be between 0.0 and 1.0".to_string()));
            }
        }

        // Claude has max_tokens requirement
        if request.max_tokens.is_none() {
            return Err(LLMError::InvalidRequest("max_tokens is required for Claude API".to_string()));
        }

        Ok(())
    }

    async fn estimate_cost(&self, request: &LLMRequest) -> LLMResult<f64> {
        let default_model = "claude-3-haiku-20240307".to_string();
        let model = request.model.as_ref()
            .or(self.config.default_model.as_ref())
            .unwrap_or(&default_model);

        // Rough token estimation
        let input_tokens = (request.prompt.len() + 
            request.system_prompt.as_ref().map_or(0, |s| s.len()) +
            request.context.as_ref().map_or(0, |s| s.len())) / 4;
        let output_tokens = request.max_tokens.unwrap_or(500) as usize;

        let (input_cost, output_cost) = match model.as_str() {
            "claude-3-opus-20240229" => (15.0 / 1_000_000.0, 75.0 / 1_000_000.0),
            "claude-3-sonnet-20240229" => (3.0 / 1_000_000.0, 15.0 / 1_000_000.0),
            "claude-3-haiku-20240307" => (0.25 / 1_000_000.0, 1.25 / 1_000_000.0),
            _ => (1.0 / 1_000_000.0, 5.0 / 1_000_000.0), // Default estimate
        };

        Ok((input_tokens as f64 * input_cost) + (output_tokens as f64 * output_cost))
    }

    async fn get_usage_stats(&self) -> LLMResult<ProviderUsageStats> {
        Ok(self.usage_stats.clone())
    }

    async fn generate_stream(&self, request: &LLMRequest) -> LLMResult<Box<dyn futures::Stream<Item = LLMResult<String>> + Send + Unpin>> {
        let headers = self.get_headers()?;

        // Validate request
        self.validate_request(request)?;

        let model = request.model.clone()
            .or_else(|| self.config.default_model.clone())
            .ok_or_else(|| LLMError::InvalidRequest("No model specified".to_string()))?;

        let messages = self.build_messages(request);
        let max_tokens = request.max_tokens.unwrap_or(1000);

        let claude_request = ClaudeRequest {
            model: model.clone(),
            max_tokens,
            messages,
            system: request.system_prompt.clone(),
            temperature: request.temperature,
            stream: Some(true),
        };

        let url = format!("{}/v1/messages", self.config.base_url);

        let mut request_builder = self.client.post(&url);
        for (key, value) in headers {
            request_builder = request_builder.header(&key, &value);
        }

        let response = request_builder
            .json(&claude_request)
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
                    // Claude sends data in the format "data: {json}"
                    if line.starts_with("data: ") {
                        let json_str = &line[6..]; // Remove "data: " prefix
                        
                        // Parse the JSON chunk
                        match serde_json::from_str::<ClaudeStreamResponse>(json_str) {
                            Ok(chunk) => {
                                // Handle different stream event types
                                match chunk.r#type.as_str() {
                                    "content_block_delta" => {
                                        if let Some(delta) = &chunk.delta {
                                            if let Some(text) = &delta.text {
                                                return Some(Ok(text.clone()));
                                            }
                                        }
                                        None
                                    }
                                    "message_stop" => None, // End of stream
                                    _ => None, // Skip other event types
                                }
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
            "claude-3-opus-20240229" => (Some(15.0 / 1000.0), Some(75.0 / 1000.0)),
            "claude-3-sonnet-20240229" => (Some(3.0 / 1000.0), Some(15.0 / 1000.0)),
            "claude-3-haiku-20240307" => (Some(0.25 / 1000.0), Some(1.25 / 1000.0)),
            _ => (Some(1.0 / 1000.0), Some(5.0 / 1000.0)),
        };

        Ok(ModelInfo {
            id: model_id.to_string(),
            name: model_id.to_string(),
            description: format!("Anthropic Claude model: {}", model_id),
            parameter_count: None,
            context_length,
            cost_per_1k_prompt_tokens: cost_prompt,
            cost_per_1k_completion_tokens: cost_completion,
            capabilities: ModelCapabilities {
                supports_streaming: true,
                supports_function_calling: false, // Claude doesn't support function calling
                supports_vision: model_id.contains("claude-3"),
                supports_chat: true,
                supports_completion: true,
                max_output_tokens: Some(4096),
                max_context_length: context_length,
                supported_languages: vec!["en".to_string(), "es".to_string(), "fr".to_string(), "de".to_string()],
            },
        })
    }

    fn supports_feature(&self, feature: ProviderFeature) -> bool {
        use crate::llm::ProviderFeature;
        match feature {
            ProviderFeature::Streaming => true,
            ProviderFeature::FunctionCalling => false, // Claude doesn't support function calling
            ProviderFeature::Vision => true,
            ProviderFeature::SystemPrompt => true,
            ProviderFeature::ContextWindow => true,
            ProviderFeature::CostTracking => true,
            ProviderFeature::RateLimiting => true,
            ProviderFeature::BatchProcessing => false,
            ProviderFeature::JsonMode => false,
        }
    }

    fn default_model(&self) -> Option<String> {
        Some("claude-3-sonnet-20240229".to_string())
    }

    fn get_limits(&self) -> ProviderLimits {
        ProviderLimits {
            max_tokens_per_request: 4096,
            max_requests_per_minute: 1000,
            max_tokens_per_minute: 100000,
            max_context_length: 200000, // Claude 3 max
            max_output_tokens: 4096,
            min_temperature: 0.0,
            max_temperature: 1.0,
        }
    }
}

impl ClaudeProvider {
    fn get_model_context_length(&self, model: &str) -> u32 {
        match model {
            "claude-3-opus-20240229" => 200000,
            "claude-3-sonnet-20240229" => 200000,
            "claude-3-haiku-20240307" => 200000,
            _ => 100000, // Conservative default
        }
    }
}