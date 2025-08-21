"""
Enhanced LLM service with support for multiple providers including Ollama
"""

import json
from collections.abc import AsyncGenerator
from datetime import datetime, timedelta
from typing import Any

import httpx
from sqlalchemy.orm import Session

from app.models.llm_config import LLMConfiguration, TokenUsageLog
from app.models.user import User
from app.schemas.llm_config import LLMProvider

# Optional imports for LLM providers
has_openai = False
has_anthropic = False
openai = None  # type: ignore
anthropic = None  # type: ignore

try:
    import openai

    has_openai = True
except ImportError:
    pass

try:
    import anthropic

    has_anthropic = True
except ImportError:
    pass


class EnhancedLLMService:
    """Enhanced LLM service with multi-provider support"""

    def __init__(self):
        self.providers = {
            LLMProvider.OPENAI: self._openai_generate,
            LLMProvider.ANTHROPIC: self._anthropic_generate,
            LLMProvider.OLLAMA: self._ollama_generate,
            LLMProvider.GEMINI: self._gemini_generate,
        }

    async def test_connection(
        self,
        provider: LLMProvider,
        api_key: str | None = None,
        api_url: str | None = None,
        bearer_token: str | None = None,
        model_name: str | None = None,
        test_prompt: str = "Hello, please respond with 'Connection successful!'",
    ) -> dict[str, Any]:
        """Test LLM connection and optionally list available models"""
        try:
            if provider == LLMProvider.OLLAMA:
                return await self._test_ollama_connection(
                    api_url, bearer_token, model_name, test_prompt
                )
            if provider == LLMProvider.OPENAI:
                return await self._test_openai_connection(
                    api_key, model_name, test_prompt
                )
            if provider == LLMProvider.ANTHROPIC:
                return await self._test_anthropic_connection(
                    api_key, model_name, test_prompt
                )
            return {
                "success": False,
                "message": f"Provider {provider} not yet implemented",
                "error": "Provider not implemented",
            }
        except Exception as e:
            return {"success": False, "message": "Connection failed", "error": str(e)}

    async def _test_ollama_connection(
        self,
        api_url: str | None,
        bearer_token: str | None,
        model_name: str | None,
        test_prompt: str,
    ) -> dict[str, Any]:
        """Test Ollama connection"""
        base_url = api_url or "http://localhost:11434"
        headers = {}
        if bearer_token:
            headers["Authorization"] = f"Bearer {bearer_token}"

        async with httpx.AsyncClient() as client:
            # First, try to list models
            try:
                models_response = await client.get(
                    f"{base_url}/api/tags", headers=headers
                )
                available_models = []
                if models_response.status_code == 200:
                    models_data = models_response.json()
                    available_models = [
                        model["name"] for model in models_data.get("models", [])
                    ]
            except Exception:
                available_models = []

            # Test generation with a model
            test_model = model_name or (
                available_models[0] if available_models else "llama2"
            )

            response = await client.post(
                f"{base_url}/api/generate",
                headers=headers,
                json={"model": test_model, "prompt": test_prompt, "stream": False},
                timeout=30.0,
            )

            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "message": "Connection successful",
                    "available_models": available_models,
                    "response_text": result.get("response", ""),
                }
            return {
                "success": False,
                "message": f"Connection failed with status {response.status_code}",
                "error": response.text,
            }

    async def _test_openai_connection(
        self, api_key: str | None, model_name: str | None, test_prompt: str
    ) -> dict[str, Any]:
        """Test OpenAI connection"""
        if not has_openai:
            return {
                "success": False,
                "message": "OpenAI library not installed",
                "error": "Please install openai package",
            }

        client = openai.AsyncOpenAI(api_key=api_key)

        # List available models
        try:
            models = await client.models.list()
            available_models = [model.id for model in models.data if "gpt" in model.id]
        except Exception:
            available_models = ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo-preview"]

        # Test generation
        test_model = model_name or "gpt-3.5-turbo"
        response = await client.chat.completions.create(
            model=test_model,
            messages=[{"role": "user", "content": test_prompt}],
            max_tokens=50,
        )

        return {
            "success": True,
            "message": "Connection successful",
            "available_models": available_models,
            "response_text": response.choices[0].message.content,
        }

    async def _test_anthropic_connection(
        self, api_key: str | None, model_name: str | None, test_prompt: str
    ) -> dict[str, Any]:
        """Test Anthropic connection"""
        if not has_anthropic:
            return {
                "success": False,
                "message": "Anthropic library not installed",
                "error": "Please install anthropic package",
            }

        client = anthropic.AsyncAnthropic(api_key=api_key)

        available_models = [
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307",
            "claude-2.1",
            "claude-instant-1.2",
        ]

        test_model = model_name or "claude-3-haiku-20240307"
        response = await client.messages.create(
            model=test_model,
            messages=[{"role": "user", "content": test_prompt}],
            max_tokens=50,
        )

        return {
            "success": True,
            "message": "Connection successful",
            "available_models": available_models,
            "response_text": response.content[0].text,
        }

    async def list_models(
        self,
        provider: LLMProvider,
        api_key: str | None = None,
        api_url: str | None = None,
        bearer_token: str | None = None,
    ) -> list[str]:
        """List available models for a provider"""
        if provider == LLMProvider.OLLAMA:
            base_url = api_url or "http://localhost:11434"
            headers = {}
            if bearer_token:
                headers["Authorization"] = f"Bearer {bearer_token}"

            async with httpx.AsyncClient() as client:
                response = await client.get(f"{base_url}/api/tags", headers=headers)
                if response.status_code == 200:
                    models_data = response.json()
                    return [model["name"] for model in models_data.get("models", [])]

        elif provider == LLMProvider.OPENAI and has_openai:
            client = openai.AsyncOpenAI(api_key=api_key)
            models = await client.models.list()
            return [model.id for model in models.data if "gpt" in model.id]

        elif provider == LLMProvider.ANTHROPIC:
            return [
                "claude-3-opus-20240229",
                "claude-3-sonnet-20240229",
                "claude-3-haiku-20240307",
                "claude-2.1",
                "claude-instant-1.2",
            ]

        elif provider == LLMProvider.GEMINI:
            return ["gemini-pro", "gemini-pro-vision"]

        return []

    async def generate(
        self,
        prompt: str,
        config: LLMConfiguration,
        db: Session,
        user: User,
        stream: bool = False,
    ) -> AsyncGenerator[str, None] | str:
        """Generate content using configured LLM"""
        provider = LLMProvider(config.provider)

        if provider not in self.providers:
            raise ValueError(f"Unsupported provider: {provider}")

        # Track token usage
        usage_log = TokenUsageLog(
            user_id=user.id,
            provider=config.provider,
            model=config.model_name or "default",
            feature="content_generation",
        )

        result = await self.providers[provider](prompt, config, stream)

        # Save token usage (simplified - in reality, extract from response)
        if not stream:
            usage_log.prompt_tokens = len(prompt.split())
            usage_log.completion_tokens = len(result.split())
            usage_log.total_tokens = (
                usage_log.prompt_tokens + usage_log.completion_tokens
            )
            db.add(usage_log)
            db.commit()

        return result

    async def _ollama_generate(
        self, prompt: str, config: LLMConfiguration, stream: bool = False
    ) -> AsyncGenerator[str, None] | str:
        """Generate content using Ollama"""
        base_url = config.api_url or "http://localhost:11434"
        headers = {}
        if config.bearer_token:
            headers["Authorization"] = f"Bearer {config.bearer_token}"

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{base_url}/api/generate",
                headers=headers,
                json={
                    "model": config.model_name or "llama2",
                    "prompt": prompt,
                    "stream": stream,
                    "options": {
                        "temperature": config.temperature,
                        "num_predict": config.max_tokens,
                    },
                },
                timeout=120.0,
            )

            if stream:

                async def stream_response():
                    async for line in response.aiter_lines():
                        if line:
                            data = json.loads(line)
                            if "response" in data:
                                yield data["response"]

                return stream_response()
            result = response.json()
            return result.get("response", "")

    async def _openai_generate(
        self, prompt: str, config: LLMConfiguration, stream: bool = False
    ) -> AsyncGenerator[str, None] | str:
        """Generate content using OpenAI"""
        if not has_openai:
            raise ImportError("OpenAI library not installed")

        client = openai.AsyncOpenAI(api_key=config.api_key)

        response = await client.chat.completions.create(
            model=config.model_name or "gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            stream=stream,
        )

        if stream:

            async def stream_response():
                async for chunk in response:
                    if chunk.choices[0].delta.content:
                        yield chunk.choices[0].delta.content

            return stream_response()
        return response.choices[0].message.content

    async def _anthropic_generate(
        self, prompt: str, config: LLMConfiguration, stream: bool = False
    ) -> AsyncGenerator[str, None] | str:
        """Generate content using Anthropic"""
        if not has_anthropic:
            raise ImportError("Anthropic library not installed")

        client = anthropic.AsyncAnthropic(api_key=config.api_key)

        response = await client.messages.create(
            model=config.model_name or "claude-3-haiku-20240307",
            messages=[{"role": "user", "content": prompt}],
            temperature=config.temperature,
            max_tokens=config.max_tokens or 1000,
            stream=stream,
        )

        if stream:

            async def stream_response():
                async for chunk in response:
                    if hasattr(chunk, "delta") and hasattr(chunk.delta, "text"):
                        yield chunk.delta.text

            return stream_response()
        return response.content[0].text

    async def _gemini_generate(
        self, prompt: str, config: LLMConfiguration, stream: bool = False
    ) -> AsyncGenerator[str, None] | str:
        """Generate content using Google Gemini"""
        # Placeholder for Gemini implementation
        raise NotImplementedError("Gemini support coming soon")

    def get_token_stats(
        self, db: Session, user_id: str, days: int = 30
    ) -> dict[str, Any]:
        """Get token usage statistics for a user"""
        start_date = datetime.utcnow() - timedelta(days=days)

        logs = (
            db.query(TokenUsageLog)
            .filter(
                TokenUsageLog.user_id == user_id, TokenUsageLog.created_at >= start_date
            )
            .all()
        )

        total_tokens = sum(log.total_tokens for log in logs)
        total_cost = sum(log.cost_estimate or 0 for log in logs)

        by_provider = {}
        by_model = {}

        for log in logs:
            by_provider[log.provider] = (
                by_provider.get(log.provider, 0) + log.total_tokens
            )
            by_model[log.model] = by_model.get(log.model, 0) + log.total_tokens

        return {
            "user_id": user_id,
            "total_tokens": total_tokens,
            "total_cost": total_cost,
            "by_provider": by_provider,
            "by_model": by_model,
            "period_start": start_date.isoformat(),
            "period_end": datetime.utcnow().isoformat(),
        }
