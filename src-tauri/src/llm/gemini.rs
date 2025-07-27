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
pub struct GeminiProvider {
    config: ProviderConfig,
    client: Client,
    usage_stats: ProviderUsageStats,
}

#[derive(Debug, Serialize)]
struct GeminiRequest {
    contents: Vec<GeminiContent>,
    #[serde(skip_serializing_if = "Option::is_none")]
    system_instruction: Option<GeminiContent>,
    #[serde(skip_serializing_if = "Option::is_none")]
    generation_config: Option<GeminiGenerationConfig>,
}

#[derive(Debug, Serialize)]
struct GeminiGenerationConfig {
    #[serde(skip_serializing_if = "Option::is_none")]
    temperature: Option<f32>,
    #[serde(skip_serializing_if = "Option::is_none")]
    max_output_tokens: Option<u32>,
}

#[derive(Debug, Serialize, Deserialize)]
struct GeminiContent {
    parts: Vec<GeminiPart>,
    #[serde(skip_serializing_if = "Option::is_none")]
    role: Option<String>,
}

#[derive(Debug, Serialize, Deserialize)]
struct GeminiPart {
    text: String,
}

#[derive(Debug, Deserialize)]
struct GeminiResponse {
    candidates: Vec<GeminiCandidate>,
    usage_metadata: Option<GeminiUsageMetadata>,
}

#[derive(Debug, Deserialize)]
struct GeminiCandidate {
    content: GeminiContent,
    finish_reason: Option<String>,
    index: Option<u32>,
}

#[derive(Debug, Deserialize)]
struct GeminiUsageMetadata {
    prompt_token_count: Option<u32>,
    candidates_token_count: Option<u32>,
    total_token_count: Option<u32>,
}

#[derive(Debug, Deserialize)]
struct GeminiErrorResponse {
    error: GeminiError,
}

#[derive(Debug, Deserialize)]
struct GeminiError {
    code: u32,
    message: String,
    status: String,
}

#[derive(Debug, Deserialize)]
struct GeminiModelsResponse {
    models: Vec<GeminiModel>,
}

#[derive(Debug, Deserialize)]
struct GeminiModel {
    name: String,
    display_name: String,
    description: String,
    input_token_limit: Option<u32>,
    output_token_limit: Option<u32>,
    supported_generation_methods: Vec<String>,
}

impl GeminiProvider {
    pub fn new(api_key: String, base_url: Option<String>) -> Self {
        let base_url = base_url.unwrap_or_else(|| "https://generativelanguage.googleapis.com/v1beta".to_string());
        
        let config = ProviderConfig {
            name: "Gemini (Google)".to_string(),
            base_url: base_url.clone(),
            api_key: Some(api_key),
            default_model: Some("gemini-1.5-flash".to_string()),
            max_tokens_per_request: Some(8192),
            rate_limit_requests_per_minute: Some(1500), // Conservative rate limit
            cost_per_input_token: Some(0.00001875), // $0.000000.1875 per token for Gemini 1.5 Flash
            cost_per_output_token: Some(0.000075), // $0.000.75 per token for Gemini 1.5 Flash
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

    fn get_api_key(&self) -> Result<&str, LLMError> {
        self.config.api_key.as_ref()
            .map(|key| key.as_str())
            .ok_or_else(|| LLMError::Auth("No API key configured".to_string()))
    }

    fn build_contents(&self, request: &LLMRequest) -> Vec<GeminiContent> {
        let mut contents = Vec::new();

        // Add context if provided (as model message)
        if let Some(context) = &request.context {
            contents.push(GeminiContent {
                parts: vec![GeminiPart { text: context.clone() }],
                role: Some("model".to_string()),
            });
        }

        // Add main user message
        contents.push(GeminiContent {
            parts: vec![GeminiPart { text: request.prompt.clone() }],
            role: Some("user".to_string()),
        });

        contents
    }

    fn build_generation_config(&self, request: &LLMRequest) -> GeminiGenerationConfig {
        GeminiGenerationConfig {
            temperature: request.temperature,
            max_output_tokens: request.max_tokens,
        }
    }

    fn build_system_instruction(&self, request: &LLMRequest) -> Option<GeminiContent> {
        request.system_prompt.as_ref().map(|system_prompt| {
            GeminiContent {
                parts: vec![GeminiPart { text: system_prompt.clone() }],
                role: None, // System instructions don't have a role
            }
        })
    }

    fn parse_finish_reason(&self, reason: Option<String>) -> FinishReason {
        match reason.as_deref() {
            Some("STOP") => FinishReason::Stop,
            Some("MAX_TOKENS") => FinishReason::Length,
            Some("SAFETY") => FinishReason::ContentFilter,
            Some("RECITATION") => FinishReason::ContentFilter,
            Some("OTHER") => FinishReason::Other("Other".to_string()),
            Some(other) => FinishReason::Other(other.to_string()),
            None => FinishReason::Error("No finish reason provided".to_string()),
        }
    }

    fn calculate_cost(&self, usage: &GeminiUsageMetadata, model: &str) -> f64 {
        let input_tokens = usage.prompt_token_count.unwrap_or(0);
        let output_tokens = usage.candidates_token_count.unwrap_or(0);

        // Model-specific pricing (as of 2024)
        let (input_cost, output_cost) = match model {
            "gemini-1.5-pro" => (0.0035 / 1000.0, 0.0105 / 1000.0),
            "gemini-1.5-flash" => (0.00001875, 0.000075), // per token
            "gemini-pro" => (0.0005 / 1000.0, 0.0015 / 1000.0),
            _ => (self.config.cost_per_input_token.unwrap_or(0.0), 
                  self.config.cost_per_output_token.unwrap_or(0.0)),
        };

        (input_tokens as f64 * input_cost) + (output_tokens as f64 * output_cost)
    }

    fn get_model_id_from_name(&self, model_name: &str) -> String {
        if model_name.starts_with("models/") {
            model_name.to_string()
        } else {
            format!("models/{}", model_name)
        }
    }
}

#[async_trait]
impl LLMProvider for GeminiProvider {
    fn provider_type(&self) -> ProviderType {
        ProviderType::Gemini
    }

    fn config(&self) -> &ProviderConfig {
        &self.config
    }

    async fn health_check(&self) -> LLMResult<bool> {
        let api_key = self.get_api_key()?;
        let url = format!("{}/models?key={}", self.config.base_url, api_key);
        
        let response = self.client
            .get(&url)
            .header("Content-Type", "application/json")
            .send()
            .await
            .map_err(|e| LLMError::Network(e.to_string()))?;

        Ok(response.status().is_success())
    }

    async fn list_models(&self) -> LLMResult<Vec<ModelInfo>> {
        let api_key = self.get_api_key()?;
        let url = format!("{}/models?key={}", self.config.base_url, api_key);
        
        let response = self.client
            .get(&url)
            .header("Content-Type", "application/json")
            .send()
            .await
            .map_err(|e| LLMError::Network(e.to_string()))?;

        if !response.status().is_success() {
            let error_text = response.text().await.unwrap_or_else(|_| "Unknown error".to_string());
            return Err(LLMError::Provider(format!("Failed to list models: {}", error_text)));
        }

        let models_response: GeminiModelsResponse = response.json().await
            .map_err(|e| LLMError::Provider(format!("Failed to parse models response: {}", e)))?;

        let models = models_response.models
            .into_iter()
            .filter(|model| model.supported_generation_methods.contains(&"generateContent".to_string()))
            .map(|model| {
                let capabilities = ModelCapabilities {
                    supports_streaming: true,
                    supports_chat: true,
                    supports_completion: true,
                    supports_function_calling: model.name.contains("gemini-1.5") || model.name.contains("gemini-pro"),
                    supports_vision: model.name.contains("gemini-pro-vision") || model.name.contains("gemini-1.5"),
                    max_output_tokens: Some(8192),
                    max_context_length: model.input_token_limit.unwrap_or(32768),
                    supported_languages: vec![
                        "en".to_string(), "es".to_string(), "fr".to_string(), "de".to_string(), 
                        "it".to_string(), "pt".to_string(), "ja".to_string(), "ko".to_string(), "zh".to_string()
                    ],
                };

                ModelInfo {
                    id: model.name.clone(),
                    name: model.display_name,
                    description: model.description,
                    capabilities,
                    parameter_count: None, // Google doesn't expose this
                    context_length: model.input_token_limit.unwrap_or(32768),
                    cost_per_1k_prompt_tokens: Some(0.5),
                    cost_per_1k_completion_tokens: Some(1.5),
                }
            })
            .collect();

        Ok(models)
    }

    async fn generate(&self, request: &LLMRequest) -> LLMResult<LLMResponse> {
        let start_time = Instant::now();

        let api_key = self.get_api_key()?;

        // Validate request
        self.validate_request(request)?;

        let model = request.model.clone()
            .or_else(|| self.config.default_model.clone())
            .ok_or_else(|| LLMError::InvalidRequest("No model specified".to_string()))?;

        let model_id = self.get_model_id_from_name(&model);
        let contents = self.build_contents(request);

        let mut gemini_request = GeminiRequest {
            contents,
            system_instruction: None,
            generation_config: None,
        };

        // Add system instruction if provided
        if let Some(system_prompt) = &request.system_prompt {
            gemini_request.system_instruction = Some(GeminiContent {
                parts: vec![GeminiPart { text: system_prompt.clone() }],
                role: None,
            });
        }

        // Add generation config if needed
        if request.temperature.is_some() || request.max_tokens.is_some() {
            gemini_request.generation_config = Some(GeminiGenerationConfig {
                temperature: request.temperature,
                max_output_tokens: request.max_tokens,
            });
        }

        let url = format!("{}/{}:generateContent?key={}", &self.config.base_url, model_id, api_key);

        let response = self.client
            .post(&url)
            .header("Content-Type", "application/json")
            .json(&gemini_request)
            .send()
            .await
            .map_err(|e| LLMError::Network(e.to_string()))?;

        let status = response.status();
        let response_time = start_time.elapsed();

        if !status.is_success() {
            let error_text = response.text().await.unwrap_or_else(|_| "Unknown error".to_string());
            
            // Try to parse as Gemini error response
            if let Ok(error_response) = serde_json::from_str::<GeminiErrorResponse>(&error_text) {
                let error_msg = error_response.error.message;
                return match error_response.error.code {
                    401 | 403 => Err(LLMError::Auth(error_msg)),
                    400 => Err(LLMError::InvalidRequest(error_msg)),
                    429 => Err(LLMError::RateLimit(error_msg)),
                    _ => Err(LLMError::Provider(error_msg)),
                };
            }
            
            return Err(LLMError::Provider(format!("HTTP {}: {}", status, error_text)));
        }

        let gemini_response: GeminiResponse = response.json().await
            .map_err(|e| LLMError::Provider(format!("Failed to parse response: {}", e)))?;

        let candidate = gemini_response.candidates.into_iter().next()
            .ok_or_else(|| LLMError::Provider("No candidates in response".to_string()))?;

        let content = candidate.content.parts.into_iter()
            .map(|part| part.text)
            .collect::<Vec<_>>()
            .join("");

        let finish_reason = self.parse_finish_reason(candidate.finish_reason);

        // Extract token usage
        let (input_tokens, output_tokens, total_tokens) = if let Some(usage) = &gemini_response.usage_metadata {
            (
                usage.prompt_token_count.unwrap_or(0),
                usage.candidates_token_count.unwrap_or(0),
                usage.total_token_count.unwrap_or(0),
            )
        } else {
            // Estimate if not provided
            let estimated_input = (request.prompt.len() + 
                request.system_prompt.as_ref().map_or(0, |s| s.len()) +
                request.context.as_ref().map_or(0, |s| s.len())) / 4;
            let estimated_output = content.len() / 4;
            (estimated_input as u32, estimated_output as u32, (estimated_input + estimated_output) as u32)
        };

        let tokens_used = TokenUsage {
            prompt_tokens: input_tokens,
            completion_tokens: output_tokens,
            total_tokens,
        };

        let cost_usd = if let Some(usage) = &gemini_response.usage_metadata {
            self.calculate_cost(usage, &model)
        } else {
            // Estimate cost
            let (input_cost, output_cost) = match model.as_str() {
                "gemini-1.5-pro" => (0.0035 / 1000.0, 0.0105 / 1000.0),
                "gemini-1.5-flash" => (0.00001875, 0.000075),
                "gemini-pro" => (0.0005 / 1000.0, 0.0015 / 1000.0),
                _ => (0.001 / 1000.0, 0.002 / 1000.0),
            };
            (input_tokens as f64 * input_cost) + (output_tokens as f64 * output_cost)
        };

        let mut metadata = HashMap::new();
        if let Some(index) = candidate.index {
            metadata.insert("gemini_candidate_index".to_string(), serde_json::Value::Number(index.into()));
        }

        Ok(LLMResponse {
            content,
            model_used: model,
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
        let default_model = "gemini-1.5-flash".to_string();
        let model = request.model.as_ref()
            .or(self.config.default_model.as_ref())
            .unwrap_or(&default_model);

        // Rough token estimation
        let input_tokens = (request.prompt.len() + 
            request.system_prompt.as_ref().map_or(0, |s| s.len()) +
            request.context.as_ref().map_or(0, |s| s.len())) / 4;
        let output_tokens = request.max_tokens.unwrap_or(500) as usize;

        let (input_cost, output_cost) = match model.as_str() {
            "gemini-1.5-pro" => (0.0035 / 1000.0, 0.0105 / 1000.0),
            "gemini-1.5-flash" => (0.00001875, 0.000075),
            "gemini-pro" => (0.0005 / 1000.0, 0.0015 / 1000.0),
            _ => (0.001 / 1000.0, 0.002 / 1000.0), // Default estimate
        };

        Ok((input_tokens as f64 * input_cost) + (output_tokens as f64 * output_cost))
    }

    async fn get_usage_stats(&self) -> LLMResult<ProviderUsageStats> {
        Ok(self.usage_stats.clone())
    }

    async fn generate_stream(&self, request: &LLMRequest) -> LLMResult<Box<dyn futures::Stream<Item = LLMResult<String>> + Send + Unpin>> {
        let api_key = self.config.api_key.as_ref()
            .ok_or_else(|| LLMError::Auth("No API key configured".to_string()))?;

        // Validate request
        self.validate_request(request)?;

        let model_id = request.model.clone()
            .or_else(|| self.config.default_model.clone())
            .unwrap_or_else(|| "gemini-1.5-flash".to_string());

        let contents = self.build_contents(request);
        let generation_config = self.build_generation_config(request);
        let system_instruction = self.build_system_instruction(request);

        let gemini_request = GeminiRequest {
            contents,
            system_instruction,
            generation_config: Some(generation_config),
        };

        // Use streamGenerateContent endpoint for streaming
        let url = format!("{}/{}:streamGenerateContent?key={}", &self.config.base_url, model_id, api_key);

        let response = self.client
            .post(&url)
            .header("Content-Type", "application/json")
            .json(&gemini_request)
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
                    // Skip empty lines
                    if line.trim().is_empty() {
                        return None;
                    }
                    
                    // Parse the JSON chunk - Gemini sends one JSON object per line
                    match serde_json::from_str::<GeminiResponse>(&line) {
                        Ok(chunk) => {
                            if let Some(candidate) = chunk.candidates.first() {
                                if let Some(part) = candidate.content.parts.first() {
                                    return Some(Ok(part.text.clone()));
                                }
                            }
                            None // Skip chunks without content
                        }
                        Err(e) => Some(Err(LLMError::Provider(format!("Failed to parse stream chunk: {}", e))))
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
            "gemini-1.5-pro" => (Some(0.0035), Some(0.0105)),
            "gemini-1.5-flash" => (Some(0.00001875 * 1000.0), Some(0.000075 * 1000.0)),
            "gemini-pro" => (Some(0.0005), Some(0.0015)),
            _ => (Some(0.001), Some(0.002)),
        };

        Ok(ModelInfo {
            id: model_id.to_string(),
            name: model_id.to_string(),
            description: format!("Google Gemini model: {}", model_id),
            parameter_count: None,
            context_length,
            cost_per_1k_prompt_tokens: cost_prompt,
            cost_per_1k_completion_tokens: cost_completion,
            capabilities: ModelCapabilities {
                supports_streaming: true,
                supports_function_calling: model_id.contains("1.5"),
                supports_vision: model_id.contains("vision") || model_id.contains("1.5"),
                supports_chat: true,
                supports_completion: true,
                max_output_tokens: Some(8192),
                max_context_length: context_length,
                supported_languages: vec!["en".to_string(), "es".to_string(), "fr".to_string(), "de".to_string(), "zh".to_string()],
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
        Some("gemini-1.5-flash".to_string())
    }

    fn get_limits(&self) -> ProviderLimits {
        ProviderLimits {
            max_tokens_per_request: 8192,
            max_requests_per_minute: 1500,
            max_tokens_per_minute: 32000,
            max_context_length: 2097152, // Gemini 1.5 Pro max
            max_output_tokens: 8192,
            min_temperature: 0.0,
            max_temperature: 2.0,
        }
    }
}

impl GeminiProvider {
    fn get_model_context_length(&self, model: &str) -> u32 {
        match model {
            "gemini-1.5-pro" => 2097152, // 2M tokens
            "gemini-1.5-flash" => 1048576, // 1M tokens
            "gemini-pro" => 32768,
            "gemini-pro-vision" => 16384,
            _ => 32768, // Default fallback
        }
    }
}