import asyncio
from collections.abc import AsyncGenerator
from typing import Any

from app.core.config import settings

# Optional imports for LLM providers
HAS_LANGCHAIN = False
HAS_OPENAI = False
HAS_ANTHROPIC = False

try:
    from langchain.callbacks import AsyncIteratorCallbackHandler
    from langchain.schema import HumanMessage, SystemMessage

    HAS_LANGCHAIN = True

    try:
        from langchain_openai import ChatOpenAI

        HAS_OPENAI = True
    except ImportError:
        pass

    try:
        from langchain_anthropic import ChatAnthropic

        HAS_ANTHROPIC = True
    except ImportError:
        pass
except ImportError:
    pass


class LLMService:
    def __init__(self):
        self.models = {}
        if settings.OPENAI_API_KEY and HAS_OPENAI:
            self.models["openai"] = ChatOpenAI(
                api_key=settings.OPENAI_API_KEY,
                model=settings.DEFAULT_LLM_MODEL,
                streaming=True,
            )
        if settings.ANTHROPIC_API_KEY and HAS_ANTHROPIC:
            self.models["anthropic"] = ChatAnthropic(
                api_key=settings.ANTHROPIC_API_KEY, model="claude-3-opus-20240229"
            )

    async def generate_content(
        self,
        content_type: str,
        pedagogy_style: str,
        context: dict[str, Any],
        stream: bool = False,
    ) -> AsyncGenerator[str, None]:
        """Generate content with pedagogical awareness"""

        # If no LLM providers are available, return a placeholder
        if not self.models:
            yield "[LLM Service Not Available - Install langchain_openai or langchain_anthropic]\n\n"
            yield f"Content Type: {content_type}\n"
            yield f"Pedagogy Style: {pedagogy_style}\n"
            yield f"Context: {context}\n"
            return

        system_prompt = self._build_pedagogy_prompt(pedagogy_style)
        user_prompt = self._build_content_prompt(content_type, context)

        if not HAS_LANGCHAIN:
            yield "[Langchain not installed - LLM features disabled]"
            return

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]

        # Get first available model
        model = next(iter(self.models.values())) if self.models else None
        if not model:
            yield "[No LLM model available]"
            return

        if stream:
            callback = AsyncIteratorCallbackHandler()
            model.callbacks = [callback]

            task = asyncio.create_task(model.agenerate(messages=[messages]))

            async for token in callback.aiter():
                yield token

            await task
        else:
            response = await model.agenerate(messages=[messages])
            yield response.generations[0][0].text

    def _build_pedagogy_prompt(self, style: str) -> str:
        """Build system prompt based on pedagogical style"""
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

    def _build_content_prompt(self, content_type: str, context: dict) -> str:
        """Build user prompt for specific content type"""

        prompts = {
            "lecture": f"""Create a lecture on {context.get("topic", "the topic")}.
                Learning objectives: {context.get("objectives", [])}
                Duration: {context.get("duration", "50 minutes")}
                Include: introduction, main content, examples, and summary.""",
            "worksheet": f"""Create a worksheet on {context.get("topic", "the topic")}.
                Difficulty: {context.get("difficulty", "intermediate")}
                Question types: {context.get("question_types", [])}
                Number of questions: {context.get("num_questions", 10)}""",
            "quiz": f"""Create a quiz on {context.get("topic", "the topic")}.
                Format: {context.get("format", "multiple choice")}
                Questions: {context.get("num_questions", 10)}
                Include answer key.""",
        }

        return prompts.get(content_type, "Create educational content.")


llm_service = LLMService()
