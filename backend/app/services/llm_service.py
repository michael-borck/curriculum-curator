import asyncio
from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING, Any

from app.core.config import settings

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
        self.models = {}
        if settings.OPENAI_API_KEY and has_openai:
            self.models["openai"] = ChatOpenAI(  # type: ignore[name-defined]
                api_key=settings.OPENAI_API_KEY,
                model=settings.DEFAULT_LLM_MODEL,
                streaming=True,
            )
        if settings.ANTHROPIC_API_KEY and has_anthropic:
            self.models["anthropic"] = ChatAnthropic(  # type: ignore[name-defined]
                api_key=settings.ANTHROPIC_API_KEY, model="claude-3-opus-20240229"
            )

    async def generate_content(
        self,
        pedagogy: str,
        topic: str,
        content_type: str,
        provider: str = "openai",
    ) -> AsyncGenerator[str, None]:
        """Generate educational content using LLM"""
        if not has_langchain:
            yield "LLM service not available - langchain not installed"
            return

        if provider not in self.models:
            yield f"Provider {provider} not configured or available"
            return

        llm = self.models[provider]
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
        self, content: str, enhancement_type: str, provider: str = "openai"
    ) -> str:
        """Enhance existing content"""
        if not has_langchain:
            return "LLM service not available - langchain not installed"

        if provider not in self.models:
            return f"Provider {provider} not configured or available"

        # For now, return a simple response
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