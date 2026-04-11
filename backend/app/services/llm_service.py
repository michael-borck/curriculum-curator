"""
Unified LLM Service using LiteLLM

Provides a single interface for multiple LLM providers (OpenAI, Anthropic, Ollama, etc.)
with support for:
- BYOK (Bring Your Own Key)
- Streaming responses
- Structured JSON output
- Token estimation and cost tracking
- Educational AI features (pedagogy analysis, question generation, etc.)
"""

import json
from collections.abc import AsyncGenerator
from typing import Any, ClassVar, cast

import litellm
from litellm import acompletion, completion_cost
from pydantic import BaseModel, ValidationError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.system_settings import SystemSettings
from app.models.user import User
from app.schemas.llm import (
    ChatMessage,
    GeneratedFeedback,
    GeneratedQuestion,
    PedagogyAnalysisResponse,
)
from app.services.prompt_templates import PromptTemplate

# Configure LiteLLM
litellm.drop_params = True  # Automatically drop unsupported params per provider


class LLMService:
    """Unified LLM service with multi-provider support and educational AI features"""

    DEFAULT_MODELS: ClassVar[dict[str, str]] = {
        "openai": "gpt-4",
        "anthropic": "claude-3-5-sonnet-20241022",
        "ollama": "ollama/llama3.2",
        "gemini": "gemini/gemini-pro",
    }

    def __init__(self) -> None:
        self.providers: dict[str, bool] = {}
        self._check_providers()

    def _check_providers(self) -> None:
        """Check which providers are available based on environment variables"""
        if settings.OPENAI_API_KEY:
            self.providers["openai"] = True
        if settings.ANTHROPIC_API_KEY:
            self.providers["anthropic"] = True

    # =========================================================================
    # Core LLM Methods
    # =========================================================================

    def _get_system_settings(self, db: Session) -> dict[str, Any]:
        """Get system-wide LLM settings from database"""
        settings_dict: dict[str, Any] = {}
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
                        "ollama_api_base",
                        "allow_user_api_keys",
                    ]
                )
            )
            .all()
        )
        for setting in system_settings:
            settings_dict[setting.key] = setting.value
        return settings_dict

    def _get_user_api_key(self, provider: str, user_config: dict[str, Any]) -> str | None:
        """Extract API key from user config based on provider"""
        key_map = {
            "openai": "openai_api_key",
            "anthropic": "anthropic_api_key",
            "gemini": "gemini_api_key",
        }
        key_name = key_map.get(provider)
        return user_config.get(key_name) if key_name else None

    def _get_system_api_key(self, provider: str, system_settings: dict[str, Any]) -> str | None:
        """Get system API key for provider"""
        provider_map = {
            "openai": ("system_openai_api_key", settings.OPENAI_API_KEY),
            "anthropic": ("system_anthropic_api_key", settings.ANTHROPIC_API_KEY),
            "gemini": (
                "system_gemini_api_key",
                getattr(settings, "GEMINI_API_KEY", None),
            ),
        }
        if provider not in provider_map:
            return None
        settings_key, env_key = provider_map[provider]
        return system_settings.get(settings_key) or env_key

    def _get_user_llm_config(
        self, user: User | None
    ) -> tuple[str | None, str | None, str | None]:
        """Extract provider, model, and API key from user config"""
        if not user or not getattr(user, "llm_config", None):
            return None, None, None

        raw_config = getattr(user, "llm_config", None)
        user_config: dict[str, Any] | None
        if isinstance(raw_config, str):
            user_config = json.loads(raw_config)
        elif isinstance(raw_config, dict):
            user_config = raw_config
        else:
            return None, None, None

        if user_config is None:
            return None, None, None

        provider = user_config.get("provider")
        if not provider or provider == "system":
            return None, None, None

        model = user_config.get("model")
        api_key = self._get_user_api_key(provider, user_config)
        return provider, model, api_key

    def _get_llm_config(
        self, user: User | None = None, db: Session | None = None
    ) -> tuple[str, str, str | None, str | None]:
        """Get LLM configuration based on user preferences and system settings."""
        system_settings = self._get_system_settings(db) if db else {}
        provider, model, api_key = self._get_user_llm_config(user)

        if not provider:
            # Use explicit system default if it has a key
            default_provider = system_settings.get("default_llm_provider")
            if default_provider:
                key = self._get_system_api_key(default_provider, system_settings)
                if key or default_provider == "ollama":
                    provider = default_provider
                    model = system_settings.get("default_llm_model")
                    api_key = key

            # Otherwise, pick the first provider that has an API key
            if not provider:
                for candidate in ("anthropic", "openai", "gemini"):
                    key = self._get_system_api_key(candidate, system_settings)
                    if key:
                        provider = candidate
                        api_key = key
                        break

        if not provider:
            return "", "", None, None

        if not model:
            # If env specifies a default provider+model, use that model
            if provider == settings.DEFAULT_LLM_PROVIDER:
                model = settings.DEFAULT_LLM_MODEL
            else:
                model = self.DEFAULT_MODELS.get(provider, "gpt-4")

        litellm_model = self._format_model_name(model, provider)
        api_base = None
        if provider == "ollama":
            api_base = system_settings.get("ollama_api_base", "http://localhost:11434")

        return litellm_model, provider, api_key, api_base

    def _format_model_name(self, model: str, provider: str) -> str:
        """Format model name for LiteLLM (add provider prefix if needed)"""
        if "/" in model:
            return model
        prefixes = {"anthropic": "", "ollama": "ollama/", "gemini": "gemini/"}
        prefix = prefixes.get(provider, "")
        return f"{prefix}{model}" if prefix else model

    async def generate_text(
        self,
        prompt: str,
        system_prompt: str | None = None,
        user: User | None = None,
        db: Session | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        stream: bool = False,
    ) -> AsyncGenerator[str, None] | str:
        """Generate text from a prompt with optional streaming."""
        model, provider, api_key, api_base = self._get_llm_config(user, db)

        if not provider or (not api_key and provider != "ollama"):
            error_msg = (
                "No AI provider configured. Go to Settings → AI/LLM to add an API key "
                "(OpenAI, Anthropic, or Gemini) or configure a local Ollama server."
            )
            if stream:

                async def error_gen() -> AsyncGenerator[str, None]:
                    yield error_msg

                return error_gen()
            return error_msg

        messages: list[dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            if stream:

                async def stream_gen() -> AsyncGenerator[str, None]:
                    response = await acompletion(
                        model=model,
                        messages=messages,
                        api_key=api_key,
                        api_base=api_base,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        stream=True,
                        stream_options={"include_usage": True},
                    )
                    final_chunk: Any = None
                    async for chunk in cast("Any", response):
                        if hasattr(chunk, "usage") and chunk.usage:
                            final_chunk = chunk
                        if hasattr(chunk, "choices") and chunk.choices:
                            delta = chunk.choices[0].delta
                            if hasattr(delta, "content") and delta.content:
                                yield delta.content
                    if final_chunk:
                        self._log_usage(final_chunk, model, provider or "unknown", "generate_text_stream", user, db)

                return stream_gen()

            response = await acompletion(
                model=model,
                messages=messages,
                api_key=api_key,
                api_base=api_base,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=False,
            )
            result = cast("Any", response)
            self._log_usage(result, model, provider or "unknown", "generate_text", user, db)
            return result.choices[0].message.content or ""

        except Exception as e:
            error_msg = f"Error generating text: {e!s}"
            if stream:

                async def error_gen() -> AsyncGenerator[str, None]:
                    yield error_msg

                return error_gen()
            return error_msg

    async def generate_content(
        self,
        pedagogy: str,
        topic: str,
        content_type: str,
        user: User | None = None,
        db: Session | None = None,
    ) -> AsyncGenerator[str, None]:
        """Generate educational content using LLM with streaming"""
        model, provider, api_key, api_base = self._get_llm_config(user, db)

        if not provider or (not api_key and provider != "ollama"):
            yield (
                "No AI provider configured. Go to Settings → AI/LLM to add an API key "
                "(OpenAI, Anthropic, or Gemini) or configure a local Ollama server."
            )
            return

        prompt = self._build_pedagogy_prompt(pedagogy, topic, content_type)
        messages = [
            {"role": "system", "content": prompt},
            {
                "role": "user",
                "content": f"Create {content_type} content about: {topic}",
            },
        ]

        try:
            response = await acompletion(
                model=model,
                messages=messages,
                api_key=api_key,
                api_base=api_base,
                stream=True,
                stream_options={"include_usage": True},
            )
            final_chunk: Any = None
            async for chunk in cast("Any", response):
                if hasattr(chunk, "usage") and chunk.usage:
                    final_chunk = chunk
                if hasattr(chunk, "choices") and chunk.choices:
                    delta = chunk.choices[0].delta
                    if hasattr(delta, "content") and delta.content:
                        yield delta.content
            if final_chunk:
                self._log_usage(final_chunk, model, provider or "unknown", "generate_content", user, db)
        except Exception as e:
            yield f"Error generating content: {e!s}"

    def _build_pedagogy_prompt(
        self, pedagogy: str, topic: str, content_type: str
    ) -> str:
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
        """Generate structured content with JSON output and Pydantic validation."""
        model, provider, api_key, api_base = self._get_llm_config(user, db)

        if not provider or (not api_key and provider != "ollama"):
            return None, (
                "No AI provider configured. Go to Settings → AI/LLM to add an API key "
                "(OpenAI, Anthropic, or Gemini) or configure a local Ollama server."
            )

        json_schema = response_model.model_json_schema()
        enhanced_prompt = f"""{prompt}

IMPORTANT: You must respond with valid JSON that matches this exact schema:
{json.dumps(json_schema, indent=2)}

Provide ONLY the JSON object, no additional text or markdown formatting."""

        messages = [
            {
                "role": "system",
                "content": "You are an expert curriculum designer. Always respond with valid JSON.",
            },
            {"role": "user", "content": enhanced_prompt},
        ]

        for attempt in range(max_retries):
            try:
                current_temp = max(0.3, temperature - (attempt * 0.1))
                response_format = None
                if provider == "openai" and "gpt-4" in model:
                    response_format = {"type": "json_object"}

                response = await acompletion(
                    model=model,
                    messages=messages,
                    api_key=api_key,
                    api_base=api_base,
                    temperature=current_temp,
                    response_format=response_format,
                )

                result = cast("Any", response)
                self._log_usage(result, model, provider or "unknown", "generate_structured", user, db)
                content = result.choices[0].message.content or ""

                # Clean markdown formatting if present
                content = content.strip()
                if content.startswith("```json"):
                    content = content[7:]
                if content.startswith("```"):
                    content = content[3:]
                if content.endswith("```"):
                    content = content[:-3]
                content = content.strip()

                json_data = json.loads(content)
                return response_model(**json_data), None

            except json.JSONDecodeError as e:
                if attempt < max_retries - 1:
                    messages.append(
                        {
                            "role": "user",
                            "content": f"Your response was not valid JSON. Error: {e!s}. Please provide valid JSON only.",
                        }
                    )
                    continue
                return None, f"JSON parsing failed after {max_retries} attempts: {e!s}"

            except ValidationError as e:
                if attempt < max_retries - 1:
                    messages.append(
                        {
                            "role": "user",
                            "content": f"Your JSON didn't match the required schema. Errors: {e.json()}. Please fix.",
                        }
                    )
                    continue
                return (
                    None,
                    f"Schema validation failed after {max_retries} attempts: {e!s}",
                )

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
        """Generate content using a prompt template."""
        try:
            prompt = template.render(**context)
            if response_model:
                return await self.generate_structured_content(
                    prompt=prompt, response_model=response_model, user=user, db=db
                )
            result = await self.generate_text(prompt=prompt, user=user, db=db)
            if isinstance(result, str):
                return result, None
            return "".join([chunk async for chunk in result]), None
        except ValueError as e:
            return None, f"Template error: {e!s}"
        except Exception as e:
            return None, f"Generation error: {e!s}"

    # =========================================================================
    # Educational AI Methods
    # =========================================================================

    async def enhance_content(
        self,
        content: str,
        enhancement_type: str = "improve",
        pedagogy_style: str | None = None,
        target_level: str | None = None,
        preserve_structure: bool = True,
        focus_areas: list[str] | None = None,
        user: User | None = None,
        db: Session | None = None,
    ) -> str:
        """Enhance educational content with AI assistance."""
        instructions = {
            "improve": "Improve the clarity, engagement, and educational effectiveness",
            "simplify": "Simplify the language and concepts for better understanding",
            "expand": "Expand with more details, examples, and explanations",
            "summarize": "Create a concise summary maintaining key concepts",
        }

        prompt = f"""{instructions.get(enhancement_type, instructions["improve"])} of the following content:

Content:
{content}

Requirements:
{f"- Apply {pedagogy_style} pedagogical style" if pedagogy_style else ""}
{f"- Target education level: {target_level}" if target_level else ""}
{"- Preserve the original structure and formatting" if preserve_structure else "- Reorganize for better flow if needed"}
{f"- Focus on these areas: {', '.join(focus_areas)}" if focus_areas else ""}

Provide the enhanced content maintaining markdown formatting."""

        result = await self.generate_text(
            prompt=prompt,
            system_prompt="You are an expert educational content enhancer.",
            user=user,
            db=db,
        )
        if isinstance(result, str):
            return result
        return "".join([chunk async for chunk in result])

    async def analyze_pedagogy(
        self,
        content: str,
        target_style: str | None = None,
        user: User | None = None,
        db: Session | None = None,
    ) -> PedagogyAnalysisResponse:
        """Analyze content for pedagogical quality and style alignment."""
        prompt = f"""Analyze the following educational content for pedagogical quality:

Content:
{content}

Please provide:
1. The current pedagogical style/approach
2. Confidence score (0-1)
3. Key strengths from a pedagogical perspective
4. Areas for improvement
5. Specific actionable suggestions
{f"6. Alignment with {target_style} style (0-1 score)" if target_style else ""}

Format your response as JSON with keys: current_style, confidence, strengths, weaknesses, suggestions, alignment_score"""

        result = await self.generate_text(
            prompt=prompt,
            system_prompt="You are an expert in educational pedagogy. Always respond with valid JSON.",
            user=user,
            db=db,
        )
        response_text = (
            result
            if isinstance(result, str)
            else "".join([chunk async for chunk in result])
        )

        try:
            data = json.loads(response_text)
            return PedagogyAnalysisResponse(**data)
        except (json.JSONDecodeError, ValueError):
            return PedagogyAnalysisResponse(
                current_style="unknown",
                confidence=0.5,
                strengths=["Content provided"],
                weaknesses=["Analysis failed"],
                suggestions=["Please review content manually"],
            )

    async def generate_questions(
        self,
        content: str,
        question_types: list[str] | None = None,
        count: int = 5,
        difficulty: str = "medium",
        bloom_levels: list[str] | None = None,
        user: User | None = None,
        db: Session | None = None,
    ) -> list[GeneratedQuestion]:
        """Generate assessment questions from content."""
        question_types = question_types or ["multiple_choice", "short_answer"]

        prompt = f"""Generate {count} assessment questions from the following content:

Content:
{content}

Requirements:
- Question types: {", ".join(question_types)}
- Difficulty level: {difficulty}
{f"- Target Bloom taxonomy levels: {', '.join(bloom_levels)}" if bloom_levels else ""}

For each question provide: question text, type, options (for MC), correct answer, explanation, difficulty, Bloom level, points.
Format as JSON array."""

        result = await self.generate_text(
            prompt=prompt,
            system_prompt="You are an expert assessment designer. Always respond with valid JSON.",
            user=user,
            db=db,
        )
        response_text = (
            result
            if isinstance(result, str)
            else "".join([chunk async for chunk in result])
        )

        try:
            questions_data = json.loads(response_text)
            return [GeneratedQuestion(**q) for q in questions_data]
        except (json.JSONDecodeError, ValueError):
            return [
                GeneratedQuestion(
                    question="What are the key concepts discussed in this content?",
                    question_type="short_answer",
                    difficulty=difficulty,
                    bloom_level="comprehension",
                    points=5,
                )
            ]

    async def generate_summary(
        self,
        content: str,
        summary_type: str = "key_points",
        max_length: int | None = None,
        bullet_points: bool = True,
        user: User | None = None,
        db: Session | None = None,
    ) -> str:
        """Generate summary of educational content."""
        format_instruction = "bullet points" if bullet_points else "paragraph form"
        length_instruction = f"Maximum {max_length} words" if max_length else "Concise"

        prompts = {
            "executive": "Create an executive summary suitable for stakeholders",
            "key_points": "Extract and summarize the key learning points",
            "abstract": "Write an academic abstract",
            "tldr": "Create a brief TL;DR summary",
        }

        prompt = f"""{prompts.get(summary_type, prompts["key_points"])} from the following content:

Content:
{content}

Requirements:
- Format: {format_instruction}
- Length: {length_instruction}"""

        result = await self.generate_text(
            prompt=prompt,
            system_prompt="You are an expert at summarizing educational content clearly and concisely.",
            user=user,
            db=db,
        )
        return (
            result
            if isinstance(result, str)
            else "".join([chunk async for chunk in result])
        )

    async def generate_feedback(
        self,
        student_work: str,
        rubric: dict[str, Any] | None = None,
        assignment_context: str | None = None,
        feedback_tone: str = "encouraging",
        user: User | None = None,
        db: Session | None = None,
    ) -> GeneratedFeedback:
        """Generate feedback for student work."""
        tone_instructions = {
            "encouraging": "Be supportive and highlight progress",
            "neutral": "Provide balanced, objective feedback",
            "direct": "Be clear and direct about areas needing improvement",
        }

        prompt = f"""Provide feedback on the following student work:

{f"Assignment: {assignment_context}" if assignment_context else ""}
{f"Rubric: {json.dumps(rubric, indent=2)}" if rubric else ""}

Student Work:
{student_work}

Provide {feedback_tone} feedback with strengths and areas for improvement.
Format as JSON with keys: overall_feedback, strengths, areas_for_improvement, specific_suggestions, grade_suggestion"""

        result = await self.generate_text(
            prompt=prompt,
            system_prompt=f"You are an experienced educator. {tone_instructions.get(feedback_tone, '')} Always respond with valid JSON.",
            user=user,
            db=db,
        )
        response_text = (
            result
            if isinstance(result, str)
            else "".join([chunk async for chunk in result])
        )

        try:
            data = json.loads(response_text)
            return GeneratedFeedback(**data)
        except (json.JSONDecodeError, ValueError):
            return GeneratedFeedback(
                overall_feedback="Thank you for your submission.",
                strengths=["Submission completed"],
                areas_for_improvement=["Please review the assignment requirements"],
                specific_suggestions=["Consider reviewing the course materials"],
            )

    async def translate_content(
        self,
        content: str,
        target_language: str,
        preserve_formatting: bool = True,
        cultural_adaptation: bool = False,
        glossary: dict[str, str] | None = None,
        user: User | None = None,
        db: Session | None = None,
    ) -> str:
        """Translate educational content to another language."""
        prompt = f"""Translate the following educational content to {target_language}:

Content:
{content}

Requirements:
{"- Preserve all markdown formatting" if preserve_formatting else ""}
{"- Adapt examples and references for the target culture" if cultural_adaptation else "- Keep examples as-is"}
{f"- Use these translations for technical terms: {json.dumps(glossary)}" if glossary else ""}
- Maintain educational clarity and accuracy"""

        result = await self.generate_text(
            prompt=prompt,
            system_prompt=f"You are an expert translator specializing in educational content. Translate to {target_language}.",
            user=user,
            db=db,
        )
        return (
            result
            if isinstance(result, str)
            else "".join([chunk async for chunk in result])
        )

    async def generate_learning_path(
        self,
        topic: str,
        current_knowledge: str,
        target_level: str,
        available_time: str,
        learning_style: str | None = None,
        user: User | None = None,
        db: Session | None = None,
    ) -> dict[str, Any]:
        """Generate personalized learning path."""
        prompt = f"""Create a personalized learning path for:

Topic: {topic}
Current Knowledge Level: {current_knowledge}
Target Level: {target_level}
Available Time: {available_time}
{f"Preferred Learning Style: {learning_style}" if learning_style else ""}

Provide: prerequisites, core concepts (in order), exercises, milestones, time estimates, resources.
Format as JSON."""

        result = await self.generate_text(
            prompt=prompt,
            system_prompt="You are an expert learning designer. Always respond with valid JSON.",
            user=user,
            db=db,
        )
        response_text = (
            result
            if isinstance(result, str)
            else "".join([chunk async for chunk in result])
        )

        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            return {
                "prerequisites": [],
                "core_concepts": [topic],
                "exercises": ["Practice exercises"],
                "milestones": ["Complete topic"],
                "estimated_hours": 10,
                "resources": ["Course materials"],
            }

    async def detect_misconceptions(
        self,
        student_response: str,
        correct_concept: str,
        context: str | None = None,
        user: User | None = None,
        db: Session | None = None,
    ) -> dict[str, Any]:
        """Detect and explain student misconceptions."""
        prompt = f"""Analyze the student's response for misconceptions:

{f"Context/Question: {context}" if context else ""}
Correct Concept: {correct_concept}
Student Response: {student_response}

Identify: misconceptions, confusion sources, corrections, remediation suggestions.
Format as JSON."""

        result = await self.generate_text(
            prompt=prompt,
            system_prompt="You are an expert educator skilled at identifying misconceptions. Always respond with valid JSON.",
            user=user,
            db=db,
        )
        response_text = (
            result
            if isinstance(result, str)
            else "".join([chunk async for chunk in result])
        )

        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            return {
                "misconceptions": ["Unable to analyze"],
                "confusion_sources": ["Unknown"],
                "corrections": ["Review the concept"],
                "remediation_suggestions": ["Additional practice recommended"],
            }

    async def get_completion(
        self,
        messages: list[ChatMessage],
        temperature: float = 0.7,
        max_tokens: int | None = None,
        user: User | None = None,
        db: Session | None = None,
    ) -> str:
        """Get chat completion from LLM provider."""
        system_prompt = None
        user_prompt = ""

        for msg in messages:
            if msg.role == "system":
                system_prompt = msg.content
            elif msg.role == "user":
                user_prompt = msg.content

        result = await self.generate_text(
            prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            user=user,
            db=db,
        )
        return (
            result
            if isinstance(result, str)
            else "".join([chunk async for chunk in result])
        )

    # =========================================================================
    # Token Usage Logging
    # =========================================================================

    def _log_usage(
        self,
        response: Any,
        model: str,
        provider: str,
        feature: str,
        user: User | None,
        db: Session | None,
    ) -> None:
        """Write a TokenUsageLog row from an acompletion response."""
        if not db or not user:
            return
        usage = getattr(response, "usage", None)
        if not usage:
            return
        prompt_tokens = getattr(usage, "prompt_tokens", 0) or 0
        completion_tokens = getattr(usage, "completion_tokens", 0) or 0
        if prompt_tokens + completion_tokens == 0:
            return
        try:
            cost = completion_cost(completion_response=response)
        except Exception:
            cost = None
        from app.models.llm_config import TokenUsageLog  # noqa: PLC0415

        try:
            log = TokenUsageLog(
                user_id=user.id,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
                provider=provider,
                model=model,
                cost_estimate=cost,
                feature=feature,
            )
            db.add(log)
            db.commit()
        except Exception:
            db.rollback()

    # =========================================================================
    # Utility Methods
    # =========================================================================

    def estimate_tokens(self, text: str, model: str = "gpt-4") -> int:
        """Estimate token count for text using tiktoken."""
        try:
            import tiktoken  # noqa: PLC0415

            encoding = tiktoken.encoding_for_model(model)
            return len(encoding.encode(text))
        except Exception:
            return len(text) // 4  # Fallback: ~4 chars per token

    def estimate_cost(
        self, input_tokens: int, output_tokens: int, model: str = "gpt-4"
    ) -> float:
        """Estimate cost for token usage."""
        try:
            return completion_cost(
                model=model, prompt="x" * input_tokens, completion="x" * output_tokens
            )
        except Exception:
            pricing = {
                "gpt-4": {"input": 0.03, "output": 0.06},
                "gpt-4-turbo": {"input": 0.01, "output": 0.03},
                "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
                "claude-3-opus": {"input": 0.015, "output": 0.075},
                "claude-3-sonnet": {"input": 0.003, "output": 0.015},
            }
            model_key = next((k for k in pricing if k in model.lower()), "gpt-4")
            p = pricing[model_key]
            return (input_tokens / 1000) * p["input"] + (output_tokens / 1000) * p[
                "output"
            ]

    async def list_available_models(
        self,
        provider: str | None = None,
        api_key: str | None = None,
        api_url: str | None = None,
    ) -> list[str]:
        """List available models for a provider."""
        # For Ollama, query the actual instance
        if provider == "ollama":
            try:
                import httpx  # noqa: PLC0415

                base_url = api_url or "http://localhost:11434"
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        f"{base_url}/api/tags", timeout=10.0
                    )
                    if response.status_code == 200:
                        return [
                            m["name"]
                            for m in response.json().get("models", [])
                        ]
            except Exception:
                pass
            return []

        static_models: dict[str, list[str]] = {
            "openai": [
                "gpt-4",
                "gpt-4-turbo",
                "gpt-4o",
                "gpt-4o-mini",
                "gpt-3.5-turbo",
            ],
            "anthropic": [
                "claude-3-5-sonnet-20241022",
                "claude-3-opus-20240229",
                "claude-3-sonnet-20240229",
            ],
            "gemini": ["gemini/gemini-pro", "gemini/gemini-pro-vision"],
        }
        if provider:
            return static_models.get(provider, [])
        return [m for provider_models in static_models.values() for m in provider_models]

    async def test_connection(
        self,
        provider: str,
        api_key: str | None = None,
        api_url: str | None = None,
        model_name: str | None = None,
    ) -> dict[str, Any]:
        """Test LLM connection with provided configuration."""
        try:
            model = model_name or self.DEFAULT_MODELS.get(provider, "gpt-3.5-turbo")
            litellm_model = self._format_model_name(model, provider)

            available_models: list[str] = []
            if provider == "ollama":
                try:
                    import httpx  # noqa: PLC0415

                    base_url = api_url or "http://localhost:11434"
                    async with httpx.AsyncClient() as client:
                        response = await client.get(
                            f"{base_url}/api/tags", timeout=10.0
                        )
                        if response.status_code == 200:
                            available_models = [
                                m["name"] for m in response.json().get("models", [])
                            ]
                except Exception:
                    pass
            else:
                available_models = await self.list_available_models(provider)

            response = await acompletion(
                model=litellm_model,
                messages=[
                    {
                        "role": "user",
                        "content": "Hello, respond with 'Connection successful!'",
                    }
                ],
                api_key=api_key,
                api_base=api_url,
                max_tokens=50,
            )
            result = cast("Any", response)
            return {
                "success": True,
                "message": "Connection successful",
                "available_models": available_models,
                "response_text": result.choices[0].message.content or "",
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Connection failed: {e!s}",
                "error": str(e),
            }

    def get_token_stats(
        self, db: Session, user_id: str, days: int = 30
    ) -> dict[str, Any]:
        """Get token usage statistics for a user."""
        from datetime import UTC, datetime, timedelta  # noqa: PLC0415

        from app.models.llm_config import TokenUsageLog  # noqa: PLC0415

        start_date = datetime.now(UTC) - timedelta(days=days)
        logs = (
            db.query(TokenUsageLog)
            .filter(
                TokenUsageLog.user_id == user_id,
                TokenUsageLog.created_at >= start_date,
            )
            .all()
        )

        total_tokens = sum(log.total_tokens or 0 for log in logs)
        total_cost = sum(log.cost_estimate or 0 for log in logs)
        by_provider: dict[str, int] = {}
        by_model: dict[str, int] = {}

        for log in logs:
            tokens = log.total_tokens or 0
            by_provider[log.provider or "unknown"] = (
                by_provider.get(log.provider or "unknown", 0) + tokens
            )
            by_model[log.model or "unknown"] = (
                by_model.get(log.model or "unknown", 0) + tokens
            )

        return {
            "user_id": user_id,
            "total_tokens": total_tokens,
            "total_cost": total_cost,
            "by_provider": by_provider,
            "by_model": by_model,
            "period_start": start_date.isoformat(),
            "period_end": datetime.now(UTC).isoformat(),
        }


# Singleton instance
llm_service = LLMService()
