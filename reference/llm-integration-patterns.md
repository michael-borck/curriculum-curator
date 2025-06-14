# LLM Integration Patterns

## Overview
The LLM integration layer using LiteLLM proved to be highly successful in providing a unified interface across multiple providers while maintaining cost tracking and reliability. This document captures the patterns for transfer to the Tauri implementation.

## Provider Abstraction Architecture

### Multi-Provider Configuration
```yaml
llm:
  default_provider: "ollama"           # Fallback for privacy/cost
  timeout: 30                          # Request timeout in seconds
  max_retries: 3                       # Retry attempts
  
  providers:
    anthropic:
      api_key: "env(ANTHROPIC_API_KEY)"
      default_model: "claude-3-haiku"
      base_url: "https://api.anthropic.com"
      cost_per_1k_tokens:
        input: 0.25
        output: 0.75
      models:
        claude-3-haiku:
          context_window: 200000
          max_output_tokens: 4096
        claude-3-opus:
          context_window: 200000
          max_output_tokens: 4096
          cost_per_1k_tokens:
            input: 15.00
            output: 75.00
    
    openai:
      api_key: "env(OPENAI_API_KEY)"
      default_model: "gpt-3.5-turbo"
      cost_per_1k_tokens:
        input: 0.50
        output: 1.50
      models:
        gpt-3.5-turbo:
          context_window: 16385
          max_output_tokens: 4096
        gpt-4-turbo:
          context_window: 128000
          max_output_tokens: 4096
          cost_per_1k_tokens:
            input: 10.00
            output: 30.00
    
    ollama:
      base_url: "http://localhost:11434"
      default_model: "llama3"
      cost_per_1k_tokens:
        input: 0.00                    # Local models are free
        output: 0.00
      models:
        llama3:
          context_window: 8192
          max_output_tokens: 2048
        mistral:
          context_window: 8192
          max_output_tokens: 2048
    
    groq:
      api_key: "env(GROQ_API_KEY)"
      default_model: "llama3-8b-8192"
      cost_per_1k_tokens:
        input: 0.10
        output: 0.30
      models:
        llama3-8b-8192:
          context_window: 8192
          max_output_tokens: 2048
```

### Model Alias System
**Purpose**: User-friendly model references that map to provider-specific models

```yaml
model_aliases:
  # Cost-optimized aliases
  cheap: "groq/llama3-8b-8192"
  free: "ollama/llama3"
  
  # Performance aliases  
  fast: "groq/llama3-8b-8192"
  smart: "anthropic/claude-3-opus"
  balanced: "anthropic/claude-3-haiku"
  
  # Use-case specific aliases
  default: "anthropic/claude-3-haiku"
  coding: "openai/gpt-4-turbo"
  creative: "anthropic/claude-3-opus"
  local: "ollama/llama3"
```

**Benefits**:
- Users don't need to remember provider-specific model names
- Easy to change underlying models without updating workflows
- Cost/performance optimization through alias updates

## Request Management Patterns

### Async Request Handling
```python
class LLMManager:
    async def generate(self, prompt, model_alias=None, **params):
        # Resolve provider and model from alias
        provider, model = self._resolve_model_alias(model_alias)
        
        # Create tracking request
        request = LLMRequest(
            prompt=prompt,
            provider=provider,
            model=model,
            workflow_id=self.current_workflow_id,
            step_name=self.current_step_name
        )
        
        # Execute with retry logic
        try:
            response = await self._execute_with_retry(request)
            self._calculate_cost(request)
            return response
        except Exception as e:
            self._handle_request_error(request, e)
            raise
```

### Retry Logic with Backoff
```python
@backoff.on_exception(
    backoff.expo,                    # Exponential backoff
    (LLMRequestError, ConnectionError),
    max_tries=3,
    jitter=backoff.full_jitter       # Add randomness to prevent thundering herd
)
async def _execute_with_retry(self, request):
    """Execute LLM request with intelligent retry logic."""
    
    # Try primary provider
    try:
        return await self._call_provider(request)
    except RateLimitError:
        # Wait and retry same provider
        await asyncio.sleep(self._calculate_backoff_delay())
        return await self._call_provider(request)
    except ProviderError:
        # Try fallback provider
        fallback_provider = self._get_fallback_provider(request.provider)
        if fallback_provider:
            request.provider = fallback_provider
            return await self._call_provider(request)
        raise
```

### Provider Fallback Strategy
```yaml
fallback_chains:
  anthropic: ["openai", "groq", "ollama"]
  openai: ["anthropic", "groq", "ollama"]
  groq: ["ollama"]                   # Fast fallback to local
  ollama: []                         # No fallback for local
```

## Cost Tracking and Management

### Request Tracking
```python
class LLMRequest:
    def __init__(self, prompt, provider, model, workflow_id=None, step_name=None):
        self.prompt = prompt
        self.provider = provider
        self.model = model
        self.workflow_id = workflow_id
        self.step_name = step_name
        self.timestamp = datetime.now()
        
        # Populated after execution
        self.input_tokens = None
        self.output_tokens = None
        self.completion = None
        self.duration = None
        self.cost = None
        self.status = "pending"        # pending, success, error
        self.error = None
```

### Cost Calculation
```python
def _calculate_cost(self, request):
    """Calculate cost based on token counts and configured rates."""
    provider_config = self.config["llm"]["providers"][request.provider]
    model_config = provider_config["models"].get(request.model, {})
    
    # Get costs, checking model-specific, then provider default
    input_cost = model_config.get("cost_per_1k_tokens", {}).get(
        "input", provider_config["cost_per_1k_tokens"]["input"]
    )
    output_cost = model_config.get("cost_per_1k_tokens", {}).get(
        "output", provider_config["cost_per_1k_tokens"]["output"]
    )
    
    # Calculate total cost
    request.cost = (
        (request.input_tokens / 1000) * input_cost +
        (request.output_tokens / 1000) * output_cost
    )
    return request.cost
```

### Usage Reporting
```python
def generate_usage_report(self, workflow_id=None, step_name=None):
    """Generate detailed usage and cost analysis."""
    
    # Filter requests by criteria
    requests = [r for r in self.history
               if (workflow_id is None or r.workflow_id == workflow_id)
               and (step_name is None or r.step_name == step_name)]
    
    # Group by provider and model
    by_model = {}
    for request in requests:
        key = f"{request.provider}/{request.model}"
        if key not in by_model:
            by_model[key] = {
                "count": 0,
                "input_tokens": 0,
                "output_tokens": 0,
                "cost": 0,
                "errors": 0,
                "avg_duration": 0,
            }
        
        entry = by_model[key]
        entry["count"] += 1
        if request.status == "error":
            entry["errors"] += 1
        elif request.status == "success":
            entry["input_tokens"] += request.input_tokens or 0
            entry["output_tokens"] += request.output_tokens or 0
            entry["cost"] += request.cost or 0
            entry["avg_duration"] = (
                entry["avg_duration"] * (entry["count"] - 1) + request.duration
            ) / entry["count"]
    
    return {
        "by_model": by_model,
        "totals": {
            "count": sum(m["count"] for m in by_model.values()),
            "input_tokens": sum(m["input_tokens"] for m in by_model.values()),
            "output_tokens": sum(m["output_tokens"] for m in by_model.values()),
            "cost": sum(m["cost"] for m in by_model.values()),
            "errors": sum(m["errors"] for m in by_model.values()),
        },
        "timestamp": datetime.now(),
        "workflow_id": workflow_id,
        "step_name": step_name,
    }
```

## Environment Variable Resolution

### Secure API Key Management
```python
def _resolve_api_key(self, api_key_config):
    """Resolve API key from environment variable reference."""
    if api_key_config.startswith("env(") and api_key_config.endswith(")"):
        env_var = api_key_config[4:-1]
        api_key = os.getenv(env_var)
        if not api_key:
            logger.warning(f"Missing API key for environment variable: {env_var}")
            return None
        return api_key
    return api_key_config
```

### Configuration Validation
```python
def _validate_provider_config(self, provider_name, config):
    """Validate provider configuration at startup."""
    required_fields = ["default_model", "models", "cost_per_1k_tokens"]
    
    for field in required_fields:
        if field not in config:
            raise ConfigurationError(f"Provider {provider_name} missing required field: {field}")
    
    # Validate models exist
    if config["default_model"] not in config["models"]:
        raise ConfigurationError(f"Default model {config['default_model']} not found in models list")
    
    # Test API connectivity (optional)
    if self.test_connections:
        self._test_provider_connection(provider_name, config)
```

## Context Window Management

### Smart Prompt Truncation
```python
def _manage_context_window(self, prompt, model_config):
    """Ensure prompt fits within model's context window."""
    max_tokens = model_config.get("context_window", 4096)
    max_output = model_config.get("max_output_tokens", 1024)
    available_tokens = max_tokens - max_output - 100  # Safety buffer
    
    # Estimate token count (rough approximation)
    estimated_tokens = len(prompt) // 4  # ~4 chars per token
    
    if estimated_tokens > available_tokens:
        # Truncate prompt intelligently
        truncated_prompt = self._truncate_prompt_intelligently(
            prompt, available_tokens
        )
        logger.warning(
            "Prompt truncated for context window",
            original_length=len(prompt),
            truncated_length=len(truncated_prompt),
            model=model_config
        )
        return truncated_prompt
    
    return prompt
```

## Tauri Implementation Strategy

### TypeScript LLM Manager
```typescript
interface LLMConfig {
  providers: Record<string, ProviderConfig>;
  modelAliases: Record<string, string>;
  defaultProvider: string;
  timeout: number;
  maxRetries: number;
}

interface LLMRequest {
  prompt: string;
  provider: string;
  model: string;
  workflowId?: string;
  stepName?: string;
  timestamp: Date;
  inputTokens?: number;
  outputTokens?: number;
  cost?: number;
  status: 'pending' | 'success' | 'error';
  error?: string;
}

class LLMManager {
  private config: LLMConfig;
  private requestHistory: LLMRequest[] = [];
  
  async generate(prompt: string, modelAlias?: string): Promise<string> {
    const [provider, model] = this.resolveModelAlias(modelAlias);
    const request = this.createRequest(prompt, provider, model);
    
    try {
      const response = await this.executeWithRetry(request);
      this.calculateCost(request);
      this.requestHistory.push(request);
      return response;
    } catch (error) {
      this.handleError(request, error);
      throw error;
    }
  }
  
  private async executeWithRetry(request: LLMRequest): Promise<string> {
    // Implementation with fetch API and retry logic
  }
}
```

### Tauri Commands for LLM Operations
```rust
#[tauri::command]
async fn generate_llm_content(
    prompt: String,
    model_alias: Option<String>,
    config: LLMConfig
) -> Result<LLMResponse, String> {
    // Rust implementation calling TypeScript LLM manager
}

#[tauri::command] 
async fn get_usage_report(
    workflow_id: Option<String>,
    step_name: Option<String>
) -> Result<UsageReport, String> {
    // Return usage statistics
}

#[tauri::command]
async fn test_provider_connection(provider: String) -> Result<bool, String> {
    // Test API connectivity
}
```

### Configuration Management
```typescript
// Load and validate LLM configuration
async function loadLLMConfig(): Promise<LLMConfig> {
  const config = await invoke('load_config');
  validateLLMConfig(config.llm);
  return config.llm;
}

// Environment variable resolution in Tauri
async function resolveApiKey(keyConfig: string): Promise<string | null> {
  if (keyConfig.startsWith('env(') && keyConfig.endsWith(')')) {
    const envVar = keyConfig.slice(4, -1);
    return await invoke('get_env_var', { name: envVar });
  }
  return keyConfig;
}
```

## Best Practices Learned

### 1. Provider Reliability
- Always configure fallback providers
- Implement exponential backoff with jitter
- Monitor provider-specific error rates
- Test connections during startup

### 2. Cost Management
- Track all requests with full context
- Implement cost budgets and alerts
- Prefer cheaper models for simple tasks
- Cache results when appropriate

### 3. Performance Optimization
- Use async/await consistently
- Implement request queuing for rate limits
- Pool connections where possible
- Monitor and log performance metrics

### 4. Error Handling
- Distinguish between retryable and fatal errors
- Provide meaningful error messages to users
- Log errors with full context for debugging
- Implement graceful degradation

### 5. Security
- Never log full API keys
- Use environment variables for sensitive data
- Validate all configuration at startup
- Implement request sanitization

This LLM integration pattern proved robust and cost-effective in the Python implementation and should be adapted for the Tauri version while maintaining the core concepts of provider abstraction, cost tracking, and reliability.