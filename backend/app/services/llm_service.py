import asyncio
import json
from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING, Optional

from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import get_db
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
        system_settings = db.query(SystemSettings).filter(
            SystemSettings.key.in_([
                'default_llm_provider',
                'default_llm_model',
                'system_openai_api_key',
                'system_anthropic_api_key',
                'system_gemini_api_key',
                'allow_user_api_keys'
            ])
        ).all()
        
        for setting in system_settings:
            settings_dict[setting.key] = setting.value
        
        return settings_dict
    
    def _get_llm_client(self, user: Optional[User] = None, db: Optional[Session] = None):
        """Get appropriate LLM client based on user preferences and system settings"""
        if not has_langchain:
            return None, "LLM service not available - langchain not installed"
        
        # Get system settings
        system_settings = {}
        if db:
            system_settings = self._get_system_settings(db)
        
        # Determine provider and API key
        provider = None
        api_key = None
        model = None
        
        # Check user preferences first (BYOK)
        if user and user.llm_config:
            user_config = user.llm_config
            if isinstance(user_config, str):
                user_config = json.loads(user_config)
            
            # If user has selected a specific provider (not 'system')
            if user_config.get('provider') and user_config['provider'] != 'system':
                provider = user_config['provider']
                model = user_config.get('model')
                
                # Get user's API key for the selected provider
                if provider == 'openai' and user_config.get('openai_api_key'):
                    api_key = user_config['openai_api_key']
                elif provider == 'anthropic' and user_config.get('anthropic_api_key'):
                    api_key = user_config['anthropic_api_key']
                elif provider == 'gemini' and user_config.get('gemini_api_key'):
                    api_key = user_config['gemini_api_key']
        
        # Fall back to system defaults if no user preference or user selected 'system'
        if not provider or provider == 'system':
            provider = system_settings.get('default_llm_provider', 'openai')
            model = system_settings.get('default_llm_model', 'gpt-4')
            
            # Get system API key
            if provider == 'openai':
                api_key = system_settings.get('system_openai_api_key') or settings.OPENAI_API_KEY
            elif provider == 'anthropic':
                api_key = system_settings.get('system_anthropic_api_key') or settings.ANTHROPIC_API_KEY
            elif provider == 'gemini':
                api_key = system_settings.get('system_gemini_api_key') or settings.GEMINI_API_KEY
        
        # Create the appropriate LLM client
        if not api_key:
            return None, f"No API key configured for provider {provider}"
        
        if provider == 'openai' and has_openai:
            return ChatOpenAI(  # type: ignore[name-defined]
                api_key=api_key,
                model=model or 'gpt-4',
                streaming=True,
            ), None
        elif provider == 'anthropic' and has_anthropic:
            return ChatAnthropic(  # type: ignore[name-defined]
                api_key=api_key,
                model=model or 'claude-3-opus-20240229'
            ), None
        elif provider == 'gemini':
            # Gemini support would need to be added
            return None, "Gemini provider not yet implemented"
        else:
            return None, f"Provider {provider} not available or not installed"

    async def generate_content(
        self,
        pedagogy: str,
        topic: str,
        content_type: str,
        user: Optional[User] = None,
        db: Optional[Session] = None,
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
        user: Optional[User] = None,
        db: Optional[Session] = None
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
