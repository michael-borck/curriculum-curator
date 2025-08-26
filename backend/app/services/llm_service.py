import asyncio
import json
from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, ValidationError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.system_settings import SystemSettings
from app.models.user import User
from app.services.prompt_templates import PromptTemplate

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

    async def generate_structured_content(
        self,
        prompt: str,
        response_model: type[BaseModel],
        user: User | None = None,
        db: Session | None = None,
        temperature: float = 0.7,
        max_retries: int = 3,
    ) -> tuple[BaseModel | None, str | None]:
        """
        Generate structured content with JSON output

        Args:
            prompt: The prompt to send to the LLM
            response_model: Pydantic model class for response validation
            user: User making the request (for API key selection)
            db: Database session
            temperature: LLM temperature (0-1)
            max_retries: Number of retries for parsing failures

        Returns:
            Tuple of (parsed_model, error_message)
        """
        llm, error = self._get_llm_client(user, db)
        if not llm:
            return None, error or "LLM service not available"

        # Get JSON schema from Pydantic model
        json_schema = response_model.model_json_schema()

        # Enhance prompt with JSON instructions
        enhanced_prompt = f"""{prompt}

IMPORTANT: You must respond with valid JSON that matches this exact schema:
{json.dumps(json_schema, indent=2)}

Provide ONLY the JSON object, no additional text or markdown formatting."""

        messages = [
            SystemMessage(
                content="You are an expert curriculum designer. Always respond with valid JSON."
            ),  # type: ignore[name-defined]
            HumanMessage(content=enhanced_prompt),  # type: ignore[name-defined]
        ]

        # Try to get structured response
        for attempt in range(max_retries):
            try:
                # Adjust temperature for retries
                current_temp = max(0.3, temperature - (attempt * 0.1))

                # Configure LLM for JSON output
                if hasattr(llm, "model_kwargs"):
                    # OpenAI-style
                    llm.model_kwargs = {
                        "temperature": current_temp,
                        "response_format": {"type": "json_object"},
                    }
                elif hasattr(llm, "temperature"):
                    llm.temperature = current_temp

                # Generate response
                response = await llm.ainvoke(messages)
                content = (
                    response.content if hasattr(response, "content") else str(response)
                )

                # Clean response (remove markdown if present)
                content = content.strip()
                if content.startswith("```json"):
                    content = content[7:]
                if content.startswith("```"):
                    content = content[3:]
                if content.endswith("```"):
                    content = content[:-3]
                content = content.strip()

                # Parse JSON
                json_data = json.loads(content)

                # Validate with Pydantic
                result = response_model(**json_data)
                return result, None

            except json.JSONDecodeError as e:
                error_msg = (
                    f"JSON parsing failed (attempt {attempt + 1}/{max_retries}): {e!s}"
                )
                if attempt < max_retries - 1:
                    # Add error feedback to conversation
                    messages.append(
                        HumanMessage(  # type: ignore[name-defined]
                            content=f"Your response was not valid JSON. Error: {e!s}. Please provide valid JSON only."
                        )
                    )
                    await asyncio.sleep(1)  # Brief delay before retry
                    continue
                return None, error_msg

            except ValidationError as e:
                error_msg = f"Schema validation failed (attempt {attempt + 1}/{max_retries}): {e!s}"
                if attempt < max_retries - 1:
                    # Add validation feedback
                    messages.append(
                        HumanMessage(  # type: ignore[name-defined]
                            content=f"Your JSON didn't match the required schema. Errors: {e.json()}. Please fix and provide valid JSON."
                        )
                    )
                    await asyncio.sleep(1)
                    continue
                return None, error_msg

            except Exception as e:
                return None, f"Unexpected error: {e!s}"

        return None, f"Failed after {max_retries} attempts"

    async def generate_with_template(
        self,
        template: PromptTemplate,
        context: dict[str, Any],
        response_model: type[BaseModel] | None = None,
        user: User | None = None,
        db: Session | None = None,
    ) -> tuple[Any, str | None]:
        """
        Generate content using a prompt template

        Args:
            template: PromptTemplate instance
            context: Context variables for template
            response_model: Optional Pydantic model for structured output
            user: User making the request
            db: Database session

        Returns:
            Tuple of (result, error_message)
        """
        try:
            # Render the template
            prompt = template.render(**context)

            # Generate structured or unstructured response
            if response_model:
                return await self.generate_structured_content(
                    prompt=prompt,
                    response_model=response_model,
                    user=user,
                    db=db,
                )
            # Use existing streaming generation for unstructured
            result = ""
            async for chunk in self.generate_content(
                pedagogy="",  # Not used when we have full prompt
                topic="",
                content_type="",
                user=user,
                db=db,
            ):
                result += chunk
            return result, None

        except ValueError as e:
            return None, f"Template error: {e!s}"
        except Exception as e:
            return None, f"Generation error: {e!s}"

    def estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for a text
        Rough estimation: ~4 characters per token
        """
        return len(text) // 4

    def estimate_cost(
        self,
        input_tokens: int,
        output_tokens: int,
        model: str = "gpt-4",
    ) -> float:
        """
        Estimate cost for token usage

        Returns:
            Estimated cost in USD
        """
        # Rough pricing estimates (update as needed)
        pricing = {
            "gpt-4": {"input": 0.03, "output": 0.06},  # per 1K tokens
            "gpt-3.5-turbo": {"input": 0.001, "output": 0.002},
            "claude-3-opus": {"input": 0.015, "output": 0.075},
            "claude-3-sonnet": {"input": 0.003, "output": 0.015},
        }

        model_pricing = pricing.get(model, pricing["gpt-4"])
        input_cost = (input_tokens / 1000) * model_pricing["input"]
        output_cost = (output_tokens / 1000) * model_pricing["output"]

        return input_cost + output_cost


# Create singleton instance
llm_service = LLMService()
