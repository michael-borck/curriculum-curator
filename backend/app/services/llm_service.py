import asyncio
import json
from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.system_settings import SystemSettings
from app.models.user import User

# Optional imports for LLM providers
if TYPE_CHECKING:
    from langchain.callbacks import AsyncIteratorCallbackHandler
    from langchain.schema import HumanMessage, SystemMessage
    from langchain_anthropic import ChatAnthropic
    from langchain_openai import ChatOpenAI

has_langchain = False
has_openai = False
has_anthropic = False

try:
    from langchain.callbacks import AsyncIteratorCallbackHandler
    from langchain.schema import HumanMessage, SystemMessage

    has_langchain = True

    try:
        from langchain_openai import ChatOpenAI

        has_openai = True
    except ImportError:
        pass

    try:
        from langchain_anthropic import ChatAnthropic

        has_anthropic = True
    except ImportError:
        pass
except ImportError:
    pass


class LLMService:
    def __init__(self):
        # Don't initialize models here - we'll do it dynamically based on user/system settings
        pass

    def _get_system_settings(self, db: Session) -> dict:
        """Get system-wide LLM settings from database"""
        settings_dict = {}
        system_settings = (
            db.query(SystemSettings)
            .filter(
                SystemSettings.key.in_(
                    [
                        "default_llm_provider",
                        "default_llm_model",
                        "system_openai_api_key",
                        "system_anthropic_api_key",
                        "system_gemini_api_key",
                        "allow_user_api_keys",
                    ]
                )
            )
            .all()
        )

        for setting in system_settings:
            settings_dict[setting.key] = setting.value

        return settings_dict

    def _get_user_api_key(self, provider: str, user_config: dict) -> str | None:
        """Extract API key from user config based on provider"""
        api_key_map = {
            "openai": "openai_api_key",
            "anthropic": "anthropic_api_key",
            "gemini": "gemini_api_key",
        }
        key_name = api_key_map.get(provider)
        return user_config.get(key_name) if key_name else None

    def _get_system_api_key(self, provider: str, system_settings: dict) -> str | None:
        """Get system API key for provider"""
        provider_settings_map = {
            "openai": ("system_openai_api_key", settings.OPENAI_API_KEY),
            "anthropic": ("system_anthropic_api_key", settings.ANTHROPIC_API_KEY),
            "gemini": ("system_gemini_api_key", settings.GEMINI_API_KEY),
        }

        if provider not in provider_settings_map:
            return None

        settings_key, env_key = provider_settings_map[provider]
        return system_settings.get(settings_key) or env_key

    def _get_user_llm_config(
        self, user: User | None
    ) -> tuple[str | None, str | None, str | None]:
        """Extract provider, model, and API key from user config"""
        if not user or not user.llm_config:
            return None, None, None

        user_config = user.llm_config
        if isinstance(user_config, str):
            user_config = json.loads(user_config)

        provider = user_config.get("provider")
        if not provider or provider == "system":
            return None, None, None

        model = user_config.get("model")
        api_key = self._get_user_api_key(provider, user_config)
        return provider, model, api_key

    def _create_llm_client(self, provider: str, api_key: str, model: str | None):
        """Create LLM client for given provider"""
        if provider == "openai" and has_openai:
            return ChatOpenAI(  # type: ignore[name-defined]
                api_key=api_key,
                model=model or "gpt-4",
                streaming=True,
            ), None
        if provider == "anthropic" and has_anthropic:
            return ChatAnthropic(  # type: ignore[name-defined]
                api_key=api_key, model=model or "claude-3-opus-20240229"
            ), None
        if provider == "gemini":
            return None, "Gemini provider not yet implemented"
        return None, f"Provider {provider} not available or not installed"

    def _get_llm_client(self, user: User | None = None, db: Session | None = None):
        """Get appropriate LLM client based on user preferences and system settings"""
        if not has_langchain:
            return None, "LLM service not available - langchain not installed"

        # Get system settings
        system_settings = self._get_system_settings(db) if db else {}

        # Try user config first (BYOK)
        provider, model, api_key = self._get_user_llm_config(user)

        # Fall back to system defaults if needed
        if not provider:
            provider = system_settings.get("default_llm_provider", "openai")
            model = system_settings.get("default_llm_model", "gpt-4")
            api_key = self._get_system_api_key(provider, system_settings)

        # Validate and create client
        if not api_key:
            return None, f"No API key configured for provider {provider}"

        return self._create_llm_client(provider, api_key, model)

    async def generate_content(
        self,
        pedagogy: str,
        topic: str,
        content_type: str,
        user: User | None = None,
        db: Session | None = None,
    ) -> AsyncGenerator[str, None]:
        """Generate educational content using LLM with user/system preferences"""
        llm, error = self._get_llm_client(user, db)
        if not llm:
            yield error or "LLM service not available"
            return

        prompt = self._build_prompt(pedagogy, topic, content_type)

        messages = [
            SystemMessage(content=prompt),  # type: ignore[name-defined]
            HumanMessage(  # type: ignore[name-defined]
                content=f"Create {content_type} content about: {topic}"
            ),
        ]

        callback = AsyncIteratorCallbackHandler()  # type: ignore[name-defined]
        task = asyncio.create_task(llm.ainvoke(messages, callbacks=[callback]))

        try:
            async for token in callback.aiter():
                yield token
        finally:
            await task

    async def enhance_content(
        self,
        content: str,
        enhancement_type: str,
        user: User | None = None,
        db: Session | None = None,
    ) -> str:
        """Enhance existing content with user/system preferences"""
        llm, error = self._get_llm_client(user, db)
        if not llm:
            return error or "LLM service not available"

        # For now, return a simple response
        # In production, this would use the LLM to enhance content
        return f"Enhanced content: {content[:100]}..."

    def _build_prompt(self, pedagogy: str, topic: str, content_type: str) -> str:
        """Build pedagogically-aware prompt"""
        style = pedagogy.lower().replace(" ", "-")
        styles = {
            "traditional": "Focus on direct instruction, clear explanations, and structured practice.",
            "inquiry-based": "Encourage questioning, exploration, and discovery learning.",
            "project-based": "Emphasize real-world applications and hands-on projects.",
            "collaborative": "Promote group work, peer learning, and discussion.",
            "game-based": "Incorporate game elements, challenges, and rewards.",
            "flipped": "Design for self-paced learning with active classroom application.",
            "differentiated": "Provide multiple paths and options for different learners.",
            "constructivist": "Build on prior knowledge and encourage meaning-making.",
            "experiential": "Focus on learning through experience and reflection.",
        }

        return f"""You are an expert educational content creator specializing in {style} learning.
        {styles.get(style, "")}
        Create content that aligns with this pedagogical approach."""


# Create singleton instance
llm_service = LLMService()
