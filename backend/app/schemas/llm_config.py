"""
Schemas for LLM configuration management
"""

from enum import Enum

from pydantic import BaseModel, Field


class LLMProvider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"
    OLLAMA = "ollama"
    CUSTOM = "custom"


class LLMConfigBase(BaseModel):
    provider: LLMProvider
    api_key: str | None = Field(None, description="API key for the provider")
    api_url: str | None = Field(
        None, description="Custom API URL (for Ollama or custom endpoints)"
    )
    bearer_token: str | None = Field(
        None, description="Bearer token for authentication (Ollama)"
    )
    model_name: str | None = Field(None, description="Model to use")
    temperature: float = Field(0.7, ge=0.0, le=2.0)
    max_tokens: int | None = Field(None, ge=1)
    is_default: bool = False


class LLMConfigCreate(LLMConfigBase):
    pass


class LLMConfigUpdate(BaseModel):
    provider: LLMProvider | None = None
    api_key: str | None = None
    api_url: str | None = None
    bearer_token: str | None = None
    model_name: str | None = None
    temperature: float | None = Field(None, ge=0.0, le=2.0)
    max_tokens: int | None = Field(None, ge=1)
    is_default: bool | None = None


class LLMConfig(LLMConfigBase):
    id: str
    user_id: str | None = None  # None for system-wide config
    is_active: bool = True

    class Config:
        from_attributes = True


class LLMModelInfo(BaseModel):
    """Information about an available model"""

    id: str
    name: str
    provider: LLMProvider
    context_window: int | None = None
    supports_vision: bool = False
    supports_functions: bool = False


class LLMTestRequest(BaseModel):
    """Request to test LLM connection"""

    provider: LLMProvider
    api_key: str | None = None
    api_url: str | None = None
    bearer_token: str | None = None
    model_name: str | None = None
    test_prompt: str = "Hello, please respond with 'Connection successful!'"


class LLMTestResponse(BaseModel):
    """Response from LLM connection test"""

    success: bool
    message: str
    available_models: list[str] | None = None
    response_text: str | None = None
    error: str | None = None


class TokenUsage(BaseModel):
    """Token usage tracking"""

    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    model: str
    provider: LLMProvider
    cost_estimate: float | None = None


class UserTokenStats(BaseModel):
    """User token usage statistics"""

    user_id: str
    total_tokens: int
    total_cost: float
    by_provider: dict[str, int]
    by_model: dict[str, int]
    period_start: str
    period_end: str
