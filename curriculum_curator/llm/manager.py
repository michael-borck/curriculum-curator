import os
import time
import asyncio
from datetime import datetime
import backoff
import structlog
import litellm
from typing import Dict, Any, Optional, List, Tuple

from curriculum_curator.utils.exceptions import LLMRequestError

logger = structlog.get_logger()


# We already imported this from utils.exceptions


class LLMRequest:
    """Represents a request to an LLM provider."""
    
    def __init__(self, prompt, provider, model, workflow_id=None, step_name=None):
        """Initialize a new LLM request.
        
        Args:
            prompt (str): The prompt content
            provider (str): The LLM provider name (e.g., 'anthropic', 'openai')
            model (str): The specific model name
            workflow_id (str, optional): ID of the originating workflow
            step_name (str, optional): Name of the originating workflow step
        """
        self.prompt = prompt
        self.provider = provider
        self.model = model
        self.workflow_id = workflow_id
        self.step_name = step_name
        self.timestamp = datetime.now()
        self.input_tokens = None
        self.output_tokens = None
        self.completion = None
        self.duration = None
        self.cost = None
        self.status = "pending"
        self.error = None


class LLMManager:
    """Manages interactions with LLM providers."""
    
    def __init__(self, config):
        """Initialize the LLM manager.
        
        Args:
            config: Configuration (either dict or AppConfig)
        """
        from curriculum_curator.config.models import AppConfig
        
        # Convert dict to AppConfig if needed
        if not isinstance(config, AppConfig):
            from curriculum_curator.config.models import AppConfig
            self.config = AppConfig.model_validate(config)
        else:
            self.config = config
            
        self.history = []
        self.current_workflow_id = None
        self.current_step_name = None
        
        # API keys are already resolved by Pydantic validators
        
        logger.info("llm_manager_initialized", 
                   providers=list(self.config.llm.providers.keys()))
    
    def _configure_api_keys(self):
        """Configure API keys from environment variables."""
        # This is a placeholder - in the full implementation, we'd set up the API keys
        # by reading them from environment variables as specified in the config
        for provider, provider_config in self.config.get("llm", {}).get("providers", {}).items():
            api_key = provider_config.get("api_key", "")
            if api_key and api_key.startswith("env(") and api_key.endswith(")"):
                env_var = api_key[4:-1]
                api_key = os.getenv(env_var, "")
                if provider != "ollama" and not api_key:
                    logger.warning(f"Missing API key for {provider}", env_var=env_var)
    
    def _resolve_model_alias(self, model_alias: Optional[str] = None) -> Tuple[str, str]:
        """Resolve model alias to provider and model.
        
        Args:
            model_alias (str, optional): The model alias to resolve (e.g., 'openai/gpt-4', 'default_smart')
            
        Returns:
            tuple: (provider, model) pair
        """
        # If no model alias is provided, use the default provider and model
        if model_alias is None:
            default_provider = self.config.llm.default_provider
            default_model = self.config.llm.providers[default_provider].default_model
            return default_provider, default_model
        
        # Check if alias directly specifies provider/model format
        if "/" in model_alias:
            provider, model = model_alias.split("/", 1)
            # Verify this provider and model exist in our config
            if (provider in self.config.llm.providers and
                model in self.config.llm.providers[provider].models):
                return provider, model
        
        # Handle named aliases like "default_smart", "fast", etc.
        if model_alias in self.config.llm.aliases:
            alias_value = self.config.llm.aliases[model_alias]
            if "/" in alias_value:
                return alias_value.split("/", 1)
        
        # Search for the model across all providers
        for provider, provider_config in self.config.llm.providers.items():
            if model_alias in provider_config.models:
                return provider, model_alias
        
        # Fall back to default if not found
        default_provider = self.config.llm.default_provider
        default_model = self.config.llm.providers[default_provider].default_model
        
        logger.warning(
            "model_alias_not_resolved",
            model_alias=model_alias,
            using_default=f"{default_provider}/{default_model}"
        )
        
        return default_provider, default_model
    
    @backoff.on_exception(
        backoff.expo,
        (Exception),
        max_tries=3,
        jitter=backoff.full_jitter
    )
    async def generate(self, prompt: str, model_alias: Optional[str] = None, **params) -> str:
        """Generate text using the specified model or defaults via LiteLLM.
        
        Args:
            prompt (str): The prompt to send to the LLM
            model_alias (str, optional): Alias for the model to use
            **params: Additional parameters to pass to the LLM
            
        Returns:
            str: The generated text
            
        Raises:
            LLMRequestError: If the LLM request fails
        """
        # Resolve provider and model from alias or defaults
        provider, model = self._resolve_model_alias(model_alias)
        
        # Create request object for tracking
        request = LLMRequest(
            prompt=prompt, 
            provider=provider, 
            model=model,
            workflow_id=self.current_workflow_id,
            step_name=self.current_step_name
        )
        self.history.append(request)
        
        logger.info(
            "llm_request_started",
            provider=provider,
            model=model,
            workflow_id=self.current_workflow_id,
            step_name=self.current_step_name
        )
        
        start_time = time.time()
        
        try:
            # Get provider-specific configuration
            provider_config = self.config.llm.providers[provider]
            
            # Get API key (already resolved by Pydantic validator)
            api_key = provider_config.api_key
            
            # Configure base URL if needed (for Ollama, etc.)
            base_url = provider_config.base_url
            
            # Default parameters for the request
            default_params = {
                "max_tokens": 2000,
                "temperature": 0.7,
            }
            
            # Merge provided params with defaults
            request_params = {**default_params, **params}
            
            # Use LiteLLM to make the actual request
            # Format model name as provider/model for LiteLLM
            model_name = f"{provider}/{model}"
            
            response = await litellm.acompletion(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                api_key=api_key,
                base_url=base_url,
                **request_params
            )
            
            # Process successful response
            request.status = "success"
            request.completion = response.choices[0].message.content
            request.input_tokens = response.usage.prompt_tokens
            request.output_tokens = response.usage.completion_tokens
            
            logger.info(
                "llm_request_completed",
                provider=provider,
                model=model,
                input_tokens=request.input_tokens,
                output_tokens=request.output_tokens,
                workflow_id=self.current_workflow_id,
                step_name=self.current_step_name
            )
            
        except Exception as e:
            request.status = "error"
            request.error = str(e)
            logger.exception(
                "llm_request_failed",
                provider=provider,
                model=model,
                error=str(e),
                workflow_id=self.current_workflow_id,
                step_name=self.current_step_name
            )
            raise LLMRequestError(f"LLM request failed: {e}")
        finally:
            request.duration = time.time() - start_time
            if request.input_tokens and request.output_tokens:
                self._calculate_cost(request)
        
        return request.completion
    
    def _calculate_cost(self, request):
        """Calculate cost based on token counts and configured rates.
        
        Args:
            request (LLMRequest): The request to calculate cost for
            
        Returns:
            float: The calculated cost
        """
        provider_config = self.config.llm.providers[request.provider]
        model_config = provider_config.models.get(request.model, None)
        
        # Get costs, using model-specific costs if available, falling back to provider default
        provider_cost = provider_config.cost_per_1k_tokens
        
        if model_config and model_config.cost_per_1k_tokens:
            model_cost = model_config.cost_per_1k_tokens
            input_cost = model_cost.input
            output_cost = model_cost.output
        else:
            input_cost = provider_cost.input
            output_cost = provider_cost.output
        
        # Calculate total cost
        request.cost = (
            (request.input_tokens / 1000) * input_cost +
            (request.output_tokens / 1000) * output_cost
        )
        return request.cost
    
    def generate_usage_report(self, workflow_id=None, step_name=None):
        """Generate a usage report for the specified workflow and/or step.
        
        Args:
            workflow_id (str, optional): Filter by workflow ID
            step_name (str, optional): Filter by step name
            
        Returns:
            dict: Usage report
        """
        # Filter history by workflow_id and step_name if provided
        requests = [r for r in self.history 
                if (workflow_id is None or r.workflow_id == workflow_id)
                and (step_name is None or r.step_name == step_name)]
        
        # Group by provider and model
        by_model = {}
        for r in requests:
            key = f"{r.provider}/{r.model}"
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
            if r.status == "error":
                entry["errors"] += 1
            if r.status == "success":
                entry["input_tokens"] += r.input_tokens or 0
                entry["output_tokens"] += r.output_tokens or 0
                entry["cost"] += r.cost or 0
                if entry["count"] > entry["errors"]:
                    entry["avg_duration"] = ((entry["avg_duration"] * (entry["count"] - entry["errors"] - 1)) + r.duration) / (entry["count"] - entry["errors"])
        
        # Calculate totals
        totals = {
            "count": sum(m["count"] for m in by_model.values()),
            "input_tokens": sum(m["input_tokens"] for m in by_model.values()),
            "output_tokens": sum(m["output_tokens"] for m in by_model.values()),
            "cost": sum(m["cost"] for m in by_model.values()),
            "errors": sum(m["errors"] for m in by_model.values()),
        }
        
        return {
            "by_model": by_model,
            "totals": totals,
            "timestamp": datetime.now(),
            "workflow_id": workflow_id,
            "step_name": step_name,
        }