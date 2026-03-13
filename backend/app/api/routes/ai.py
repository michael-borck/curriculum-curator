"""
AI/LLM API routes for content generation and educational AI features.

This is the unified AI endpoint - all LLM functionality is accessed through /api/ai/*
"""

import json
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api import deps
from app.models import User
from app.models.system_settings import SystemSettings
from app.models.weekly_material import WeeklyMaterial
from app.models.weekly_topic import WeeklyTopic
from app.schemas.ai import (
    FillGapRequest,
    FillGapResponse,
    GenerateVideoInteractionOption,
    GenerateVideoInteractionRequest,
    GenerateVideoInteractionResponse,
    ScaffoldAssessment,
    ScaffoldULO,
    ScaffoldUnitRequest,
    ScaffoldUnitResponse,
    ScaffoldWeek,
    SuggestedInteraction,
    SuggestInteractionPointsRequest,
    SuggestInteractionPointsResponse,
    VisualPromptRequest,
    VisualPromptResponse,
)
from app.schemas.content import ContentGenerationRequest
from app.schemas.llm import (
    ChatCompletionRequest,
    ChatMessage,
    ContentEnhanceRequest,
    ContentRemediationRequest,
    ContentTranslationRequest,
    ContentValidationRequest,
    ContentValidationResponse,
    FeedbackGenerationRequest,
    GeneratedFeedback,
    GeneratedQuestion,
    GeneratedSchedule,
    LLMResponse,
    PedagogyAnalysisRequest,
    PedagogyAnalysisResponse,
    QuestionGenerationRequest,
    ScheduleGenerationRequest,
    ScheduleWeek,
    SummaryGenerationRequest,
    ValidationResult,
)
from app.services.design_context import (
    build_pedagogy_instruction,
    get_design_context,
)
from app.services.llm_service import llm_service

logger = logging.getLogger(__name__)


def _llm_error_response(e: Exception, operation: str) -> HTTPException:
    """Map LLM exceptions to appropriate HTTP status codes."""
    error_msg = str(e)
    error_lower = error_msg.lower()

    # Authentication / API key issues
    if any(kw in error_lower for kw in ("auth", "api key", "api_key", "unauthorized", "invalid key")):
        return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"{operation}: invalid or missing API key")

    # Rate limiting
    if any(kw in error_lower for kw in ("rate limit", "rate_limit", "too many requests", "429")):
        return HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=f"{operation}: rate limited by provider")

    # Connection / availability issues
    if any(kw in error_lower for kw in ("connect", "timeout", "unreachable", "refused", "503", "502")):
        return HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"{operation}: LLM provider unavailable")

    # Input validation
    if isinstance(e, (ValueError, TypeError)):
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"{operation}: {error_msg}")

    # Unexpected errors — log and return 500
    logger.exception("%s failed unexpectedly", operation)
    return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"{operation} failed: {error_msg}")


router = APIRouter()


# =============================================================================
# Helpers
# =============================================================================


def _enrich_with_week_context(
    db: Session, unit_id: str, week_number: int, topic: str
) -> str:
    """Prepend weekly topic title and existing material names to the prompt."""
    weekly_topic = (
        db.query(WeeklyTopic)
        .filter(
            WeeklyTopic.unit_id == unit_id,
            WeeklyTopic.week_number == week_number,
        )
        .first()
    )
    weekly_materials = (
        db.query(WeeklyMaterial)
        .filter(
            WeeklyMaterial.unit_id == unit_id,
            WeeklyMaterial.week_number == week_number,
        )
        .all()
    )
    parts: list[str] = []
    if weekly_topic and weekly_topic.title:
        parts.append(f"Week {week_number} Topic: {weekly_topic.title}")
    if weekly_materials:
        titles = [m.title for m in weekly_materials if m.title]
        if titles:
            parts.append(f"Existing materials for this week: {', '.join(titles)}")
    if parts:
        return "\n".join(parts) + "\n\n" + topic
    return topic


def _strip_markdown_fences(text: str) -> str:
    """Strip markdown code fences from LLM JSON responses."""
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    if text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()


def _inject_source_materials(db: Session, material_ids: list[str], topic: str) -> str:
    """Fetch material descriptions and inject as a source context block."""
    source_materials = (
        db.query(WeeklyMaterial).filter(WeeklyMaterial.id.in_(material_ids[:5])).all()
    )
    if not source_materials:
        return topic
    source_block = "=== SOURCE MATERIALS ===\n"
    for mat in source_materials:
        source_block += f"\n--- {mat.title} ---\n"
        if mat.description:
            source_block += f"{mat.description}\n"
    source_block += "=== END SOURCE MATERIALS ===\n\n"
    return source_block + topic


# =============================================================================
# Content Generation
# =============================================================================


@router.post("/generate")
async def generate_content(
    request: ContentGenerationRequest,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db),
):
    """Generate educational content with AI assistance using streaming."""
    try:
        topic: str = request.topic or request.context or "General educational content"

        # Inject Learning Design context
        design_ctx = None
        if request.unit_id or request.design_id:
            design_ctx = await get_design_context(
                db, request.unit_id or "", request.design_id
            )

        if design_ctx:
            topic = f"{design_ctx}\n\n{topic}"

        # Enrich with weekly context when week_number is provided
        if request.week_number and request.unit_id:
            topic = _enrich_with_week_context(
                db, request.unit_id, request.week_number, topic
            )

        # Inject source materials when provided
        if request.source_material_ids:
            topic = _inject_source_materials(db, request.source_material_ids, topic)

        # Use pedagogy override or design-aware pedagogy
        pedagogy = request.pedagogy_override or request.pedagogy_style

        async def stream_response():
            async for chunk in llm_service.generate_content(
                pedagogy=pedagogy,
                topic=topic,
                content_type=request.content_type,
                user=current_user,
                db=db,
            ):
                yield f"data: {json.dumps({'content': chunk})}\n\n"

        if request.stream:
            return StreamingResponse(stream_response(), media_type="text/event-stream")

        # Non-streaming response
        result = ""
        async for chunk in llm_service.generate_content(
            pedagogy=pedagogy,
            topic=topic,
            content_type=request.content_type,
            user=current_user,
            db=db,
        ):
            result += chunk
        return {"content": result}

    except Exception as e:
        raise _llm_error_response(e, "Content generation")


@router.post("/enhance", response_model=LLMResponse)
async def enhance_content(
    request: ContentEnhanceRequest,
    current_user: User = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db),
) -> LLMResponse:
    """
    Enhance existing content with AI.

    Enhancement types:
    - improve: Improve clarity and engagement
    - simplify: Simplify for better understanding
    - expand: Add more details and examples
    - summarize: Create concise summary
    """
    try:
        # Inject Learning Design context into focus areas
        design_ctx = None
        if request.unit_id or request.design_id:
            design_ctx = await get_design_context(
                db, request.unit_id or "", request.design_id
            )

        focus_areas = list(request.focus_areas) if request.focus_areas else []
        if design_ctx:
            focus_areas.insert(0, f"Align with the following spec:\n{design_ctx}")

        enhanced_content = await llm_service.enhance_content(
            content=request.content,
            enhancement_type=request.enhancement_type,
            pedagogy_style=request.pedagogy_style,
            target_level=request.target_level,
            preserve_structure=request.preserve_structure,
            focus_areas=focus_areas or None,
            user=current_user,
            db=db,
        )
        return LLMResponse(
            content=enhanced_content, model="default", provider="configured"
        )
    except Exception as e:
        raise _llm_error_response(e, "Enhancement")


# =============================================================================
# Pedagogy & Analysis
# =============================================================================


@router.post("/analyze-pedagogy", response_model=PedagogyAnalysisResponse)
async def analyze_pedagogy(
    request: PedagogyAnalysisRequest,
    current_user: User = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db),
) -> PedagogyAnalysisResponse:
    """
    Analyze content for pedagogical quality and alignment.

    Returns current style, confidence score, strengths, weaknesses, and suggestions.
    """
    try:
        return await llm_service.analyze_pedagogy(
            content=request.content,
            target_style=request.target_style,
            user=current_user,
            db=db,
        )
    except Exception as e:
        raise _llm_error_response(e, "Pedagogy analysis")


# =============================================================================
# Assessment & Questions
# =============================================================================


@router.post("/generate-questions", response_model=list[GeneratedQuestion])
async def generate_questions(
    request: QuestionGenerationRequest,
    current_user: User = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db),
) -> list[GeneratedQuestion]:
    """
    Generate assessment questions from content.

    Supports: multiple_choice, short_answer, true_false, essay, fill_blank
    """
    try:
        return await llm_service.generate_questions(
            content=request.content,
            question_types=request.question_types,
            count=request.count,
            difficulty=request.difficulty,
            bloom_levels=request.bloom_levels,
            user=current_user,
            db=db,
        )
    except Exception as e:
        raise _llm_error_response(e, "Question generation")


@router.post("/generate-feedback", response_model=GeneratedFeedback)
async def generate_feedback(
    request: FeedbackGenerationRequest,
    current_user: User = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db),
) -> GeneratedFeedback:
    """Generate feedback for student work with rubric-based assessment."""
    try:
        return await llm_service.generate_feedback(
            student_work=request.student_work,
            rubric=request.rubric,
            assignment_context=request.assignment_context,
            feedback_tone=request.feedback_tone,
            user=current_user,
            db=db,
        )
    except Exception as e:
        raise _llm_error_response(e, "Feedback generation")


# =============================================================================
# Summarization & Translation
# =============================================================================


@router.post("/generate-summary", response_model=LLMResponse)
async def generate_summary(
    request: SummaryGenerationRequest,
    current_user: User = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db),
) -> LLMResponse:
    """
    Generate summary of content.

    Types: executive, key_points, abstract, tldr
    """
    try:
        summary = await llm_service.generate_summary(
            content=request.content,
            summary_type=request.summary_type,
            max_length=request.max_length,
            bullet_points=request.bullet_points,
            user=current_user,
            db=db,
        )
        return LLMResponse(content=summary, model="default", provider="configured")
    except Exception as e:
        raise _llm_error_response(e, "Summary generation")


@router.post("/translate", response_model=LLMResponse)
async def translate_content(
    request: ContentTranslationRequest,
    current_user: User = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db),
) -> LLMResponse:
    """Translate educational content to another language with optional cultural adaptation."""
    try:
        translated = await llm_service.translate_content(
            content=request.content,
            target_language=request.target_language,
            preserve_formatting=request.preserve_formatting,
            cultural_adaptation=request.cultural_adaptation,
            glossary=request.glossary,
            user=current_user,
            db=db,
        )
        return LLMResponse(content=translated, model="default", provider="configured")
    except Exception as e:
        raise _llm_error_response(e, "Translation")


# =============================================================================
# Learning Paths & Misconceptions
# =============================================================================


@router.post("/learning-path")
async def generate_learning_path(
    topic: str,
    current_knowledge: str,
    target_level: str,
    available_time: str,
    learning_style: str | None = None,
    current_user: User = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db),
) -> dict:
    """Generate personalized learning path with prerequisites, milestones, and resources."""
    try:
        return await llm_service.generate_learning_path(
            topic=topic,
            current_knowledge=current_knowledge,
            target_level=target_level,
            available_time=available_time,
            learning_style=learning_style,
            user=current_user,
            db=db,
        )
    except Exception as e:
        raise _llm_error_response(e, "Learning path generation")


@router.post("/detect-misconceptions")
async def detect_misconceptions(
    student_response: str,
    correct_concept: str,
    context: str | None = None,
    current_user: User = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db),
) -> dict:
    """Detect and explain student misconceptions with remediation suggestions."""
    try:
        return await llm_service.detect_misconceptions(
            student_response=student_response,
            correct_concept=correct_concept,
            context=context,
            user=current_user,
            db=db,
        )
    except Exception as e:
        raise _llm_error_response(e, "Misconception detection")


# =============================================================================
# Chat & General Completion
# =============================================================================


@router.post("/chat", response_model=LLMResponse)
async def chat_completion(
    request: ChatCompletionRequest,
    current_user: User = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db),
) -> LLMResponse:
    """General chat completion for educational assistance."""
    try:
        response = await llm_service.get_completion(
            messages=request.messages,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            user=current_user,
            db=db,
        )
        return LLMResponse(
            content=response,
            model=request.model or "default",
            provider=request.provider or "configured",
        )
    except Exception as e:
        raise _llm_error_response(e, "Chat completion")


@router.post("/validate-content")
async def validate_content_with_ai(
    content: str,
    validation_type: str = "comprehensive",
    current_user: User = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db),
) -> dict:
    """
    Validate content using AI for quality checks.

    Types: comprehensive, factual, consistency, completeness
    """
    prompt = f"""Validate the following content for {validation_type} quality:

{content}

Check for:
1. Factual accuracy
2. Internal consistency
3. Completeness of coverage
4. Logical flow
5. Appropriate difficulty level

Return findings as JSON with keys: issues, suggestions, score"""

    messages = [
        ChatMessage(role="system", content="You are an expert content validator."),
        ChatMessage(role="user", content=prompt),
    ]

    try:
        response = await llm_service.get_completion(messages, user=current_user, db=db)
        return {"validation_result": response}
    except Exception as e:
        raise _llm_error_response(e, "Content validation")


# =============================================================================
# Provider Status & Configuration
# =============================================================================


@router.get("/provider-status")
async def get_provider_status(
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db),
):
    """Get the current LLM provider status for the user."""
    user_config = current_user.llm_config or {}
    if isinstance(user_config, str):
        user_config = json.loads(user_config)

    provider = user_config.get("provider", "system")

    # Get system default if using system
    if provider == "system":
        system_provider = (
            db.query(SystemSettings)
            .filter(SystemSettings.key == "default_llm_provider")
            .first()
        )
        actual_provider = system_provider.value if system_provider else "openai"
    else:
        actual_provider = provider

    # Check if API key is configured
    has_api_key = False
    if provider != "system":
        key_map = {
            "openai": "openai_api_key",
            "anthropic": "anthropic_api_key",
            "gemini": "gemini_api_key",
        }
        has_api_key = bool(user_config.get(key_map.get(provider, "")))
    else:
        system_key = (
            db.query(SystemSettings)
            .filter(SystemSettings.key == f"system_{actual_provider}_api_key")
            .first()
        )
        has_api_key = bool(system_key and system_key.value)

    return {
        "provider": provider,
        "actual_provider": actual_provider,
        "has_api_key": has_api_key,
        "model": user_config.get("model"),
        "is_configured": has_api_key,
    }


@router.get("/models")
async def list_available_models(
    current_user: User = Depends(deps.get_current_active_user),
) -> dict:
    """List available AI models and providers."""
    return {
        "providers": {
            "openai": {
                "available": llm_service.providers.get("openai", False),
                "models": ["gpt-4", "gpt-4-turbo", "gpt-4o", "gpt-3.5-turbo"],
                "capabilities": ["chat", "completion", "embedding"],
            },
            "anthropic": {
                "available": llm_service.providers.get("anthropic", False),
                "models": [
                    "claude-3-5-sonnet",
                    "claude-3-opus",
                    "claude-3-sonnet",
                    "claude-3-haiku",
                ],
                "capabilities": ["chat", "completion"],
            },
            "ollama": {
                "available": True,  # Always available if configured
                "models": ["llama3.2", "llama3.1", "mistral", "codellama"],
                "capabilities": ["chat", "completion"],
            },
        },
        "default_model": "gpt-4",
        "features": [
            "content_generation",
            "content_enhancement",
            "pedagogy_analysis",
            "question_generation",
            "summarization",
            "feedback_generation",
            "translation",
            "learning_paths",
            "misconception_detection",
            "schedule_generation",
            "content_validation",
        ],
    }


# =============================================================================
# Schedule Generation (Course Planner)
# =============================================================================


@router.post("/generate-schedule", response_model=GeneratedSchedule)
async def generate_course_schedule(
    request: ScheduleGenerationRequest,
    current_user: User = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db),
) -> GeneratedSchedule:
    """
    Generate a weekly course schedule based on unit information.

    Uses AI to create a logical progression of topics across the specified weeks.
    """
    # Inject Learning Design context
    design_ctx = None
    if request.unit_id or request.design_id:
        design_ctx = await get_design_context(
            db, request.unit_id or "", request.design_id
        )

    outcomes_text = (
        "; ".join(request.learning_outcomes) if request.learning_outcomes else ""
    )

    style_instruction = ""
    if request.teaching_style:
        style_instruction = "\n" + build_pedagogy_instruction(
            fallback_style=request.teaching_style
        )

    design_block = f"\n{design_ctx}\n" if design_ctx else ""

    prompt = f"""Create a {request.duration_weeks}-week university course schedule for:

Title: {request.unit_title}
Description: {request.unit_description}
Learning Outcomes: {outcomes_text}
{style_instruction}{design_block}

For each week, provide:
1. A clear, descriptive title/theme
2. 2-4 key topics to be covered
3. Specific learning objectives for that week

Ensure logical progression from foundational to advanced concepts.
Use Australian/British English conventions.

Return the schedule as a JSON array with this exact structure:
[
  {{
    "week_number": 1,
    "title": "Week title",
    "topics": ["topic1", "topic2"],
    "learning_objectives": ["objective1", "objective2"]
  }}
]"""

    try:
        result = await llm_service.generate_text(
            prompt=prompt,
            system_prompt="You are an expert curriculum designer. Always respond with valid JSON only, no additional text.",
            user=current_user,
            db=db,
            temperature=0.7,
        )

        response_text = (
            result
            if isinstance(result, str)
            else "".join([chunk async for chunk in result])
        )

        # Clean markdown formatting if present
        response_text = response_text.strip()
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        response_text = response_text.strip()

        weeks_data = json.loads(response_text)
        weeks = [ScheduleWeek(**w) for w in weeks_data]

        return GeneratedSchedule(
            weeks=weeks,
            summary=f"Generated {len(weeks)}-week schedule for {request.unit_title}",
        )

    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to parse schedule JSON: {e!s}"
        )
    except Exception as e:
        raise _llm_error_response(e, "Schedule generation")


# =============================================================================
# Content Validation & Remediation
# =============================================================================


@router.post("/validate", response_model=ContentValidationResponse)
async def validate_content(
    request: ContentValidationRequest,
    current_user: User = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db),
) -> ContentValidationResponse:
    """
    Validate content for readability, structure, and quality.

    Returns detailed validation results with suggestions for improvement.
    """
    results: list[ValidationResult] = []

    for validation_type in request.validation_types:
        if validation_type == "readability":
            prompt = f"""Analyze the readability of the following educational content for university undergraduate students.

Content:
{request.content}

Evaluate:
1. Is the language clear and accessible?
2. Are sentences well-structured and not overly complex?
3. Is technical terminology appropriately introduced and explained?
4. Does it use Australian/British English conventions?

Return JSON with:
{{
  "passed": true/false,
  "score": 0-100,
  "message": "brief assessment",
  "suggestions": ["suggestion1", "suggestion2"]
}}"""

        elif validation_type == "structure":
            prompt = f"""Analyze the structure of the following educational content.

Content:
{request.content}

Evaluate:
1. Does it have a logical flow and organization?
2. Are there clear sections (intro, body, conclusion)?
3. Are learning objectives or key points clearly stated?
4. Does it include appropriate examples or explanations?

Return JSON with:
{{
  "passed": true/false,
  "score": 0-100,
  "message": "brief assessment",
  "suggestions": ["suggestion1", "suggestion2"]
}}"""

        else:
            continue

        try:
            result = await llm_service.generate_text(
                prompt=prompt,
                system_prompt="You are an expert educational content reviewer. Always respond with valid JSON only.",
                user=current_user,
                db=db,
                temperature=0.3,
            )

            response_text = (
                result
                if isinstance(result, str)
                else "".join([chunk async for chunk in result])
            )

            # Clean JSON
            response_text = response_text.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            response_text = response_text.strip()

            data = json.loads(response_text)

            remediation_prompt = None
            if not data.get("passed", True):
                if validation_type == "readability":
                    remediation_prompt = "Improve the readability for university undergraduate students. Use clearer language, shorter sentences, and Australian/British spelling."
                elif validation_type == "structure":
                    remediation_prompt = "Reorganize for better structure with clear sections: Learning Objectives, Content Body, Summary. Add transitions between sections."

            results.append(
                ValidationResult(
                    validator_name=validation_type.title(),
                    passed=data.get("passed", True),
                    message=data.get("message", "Validation complete"),
                    score=data.get("score"),
                    suggestions=data.get("suggestions"),
                    remediation_prompt=remediation_prompt,
                )
            )

        except Exception as e:
            results.append(
                ValidationResult(
                    validator_name=validation_type.title(),
                    passed=False,
                    message=f"Validation error: {e!s}",
                )
            )

    overall_passed = all(r.passed for r in results)
    overall_score = (
        sum(r.score for r in results if r.score is not None) / len(results)
        if results and any(r.score is not None for r in results)
        else None
    )

    return ContentValidationResponse(
        results=results,
        overall_passed=overall_passed,
        overall_score=overall_score,
    )


@router.post("/remediate")
async def remediate_content(
    request: ContentRemediationRequest,
    current_user: User = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db),
):
    """
    Auto-remediate content based on validation feedback.

    Streams the remediated content back to the client.
    """
    if request.remediation_type == "readability":
        prompt = f"""Improve the readability of the following content for university undergraduate students.
Use Australian/British spelling. Make sentences clearer and more accessible.
Preserve the educational intent and technical accuracy.

Original content:
{request.content}

Return ONLY the improved content, no explanations."""

    elif request.remediation_type == "structure":
        prompt = f"""Reorganize the following educational content to follow a standard structure:
1. Learning Objectives (2-3 clear objectives)
2. Introduction
3. Main Content with clear sections
4. Summary/Key Takeaways

Preserve the educational content and meaning.

Original content:
{request.content}

Return ONLY the restructured content, no explanations."""

    elif request.custom_prompt:
        prompt = f"""{request.custom_prompt}

Content to improve:
{request.content}

Return ONLY the improved content."""

    else:
        raise HTTPException(
            status_code=400, detail="Invalid remediation type or missing custom prompt"
        )

    async def stream_response():
        result = await llm_service.generate_text(
            prompt=prompt,
            system_prompt="You are an expert educational content editor.",
            user=current_user,
            db=db,
            stream=True,
        )
        if isinstance(result, str):
            yield f"data: {json.dumps({'content': result})}\n\n"
        else:
            async for chunk in result:
                yield f"data: {json.dumps({'content': chunk})}\n\n"

    return StreamingResponse(stream_response(), media_type="text/event-stream")


# =============================================================================
# Scaffold Unit (2B)
# =============================================================================


@router.post("/scaffold-unit", response_model=ScaffoldUnitResponse)
async def scaffold_unit(
    request: ScaffoldUnitRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Generate a complete unit structure from a title + description.

    Returns ULOs, weekly topics, and assessments for human review before saving.
    """
    # Inject Learning Design context
    design_ctx = None
    if request.unit_id or request.design_id:
        design_ctx = await get_design_context(
            db, request.unit_id or "", request.design_id
        )

    pedagogy_instruction = build_pedagogy_instruction(
        fallback_style=request.pedagogy_style
    )
    design_block = f"\n{design_ctx}\n" if design_ctx else ""

    prompt = f"""Generate a complete university unit structure for:

Title: {request.title}
Description: {request.description or "Not provided"}
Duration: {request.duration_weeks} weeks
Pedagogy: {pedagogy_instruction}
{design_block}

Return a JSON object with this exact structure (no markdown, no backticks):
{{
  "title": "{request.title}",
  "description": "...",
  "ulos": [
    {{"code": "ULO1", "description": "...", "bloom_level": "remember|understand|apply|analyze|evaluate|create"}}
  ],
  "weeks": [
    {{"week_number": 1, "topic": "...", "activities": ["lecture", "tutorial"]}}
  ],
  "assessments": [
    {{"title": "...", "category": "quiz|exam|assignment|project|presentation|report", "weight": 20.0, "due_week": 4}}
  ]
}}

Requirements:
- Generate 4-6 ULOs covering different Bloom's levels
- Generate content for all {request.duration_weeks} weeks
- Assessment weights must sum to 100
- Include a mix of formative and summative assessments
- Return ONLY valid JSON, no extra text"""

    result = await llm_service.generate_text(
        prompt=prompt,
        system_prompt="You are an expert university curriculum designer. Return ONLY valid JSON.",
        user=current_user,
        db=db,
        max_tokens=4096,
    )

    # Check for LLM error (generate_text returns error strings instead of raising)
    if isinstance(result, str) and result.startswith(("Error generating text:", "No AI provider")):
        logger.error("Scaffold LLM error: %s", result)
        raise HTTPException(status_code=502, detail=result)

    # Parse the LLM response as JSON
    try:
        text = result.strip() if isinstance(result, str) else result
        # Strip markdown code fences if present
        if isinstance(text, str):
            text = text.strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[1] if "\n" in text else text[3:]
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()
            if text.startswith("json"):
                text = text[4:].strip()
            parsed = json.loads(text)
        else:
            raise TypeError("Expected string from LLM")
    except (json.JSONDecodeError, TypeError) as e:
        logger.error("Scaffold JSON parse error. Raw LLM output: %s", result[:500] if isinstance(result, str) else result)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to parse AI response as structured JSON: {e}",
        )

    # Validate and return typed response
    return ScaffoldUnitResponse(
        title=parsed.get("title", request.title),
        description=parsed.get("description", request.description),
        ulos=[
            ScaffoldULO(
                code=u.get("code", f"ULO{i + 1}"),
                description=u.get("description", ""),
                bloom_level=u.get("bloom_level", "understand"),
            )
            for i, u in enumerate(parsed.get("ulos", []))
        ],
        weeks=[
            ScaffoldWeek(
                week_number=w.get("week_number", i + 1),
                topic=w.get("topic", ""),
                activities=w.get("activities", []),
            )
            for i, w in enumerate(parsed.get("weeks", []))
        ],
        assessments=[
            ScaffoldAssessment(
                title=a.get("title", ""),
                category=a.get("category", "assignment"),
                weight=a.get("weight", 0),
                due_week=a.get("due_week"),
            )
            for a in parsed.get("assessments", [])
        ],
    )


# =============================================================================
# Fill the Gap (2C)
# =============================================================================


@router.post("/fill-gap", response_model=FillGapResponse)
async def fill_gap(
    request: FillGapRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Generate content to fill a specific gap in a unit.

    gap_type can be: ulo, material, assessment
    """
    # Inject Learning Design context
    design_ctx = None
    if request.unit_id or request.design_id:
        design_ctx = await get_design_context(db, request.unit_id, request.design_id)

    gap_prompts = {
        "ulo": "Generate a well-written Unit Learning Outcome (ULO) description. Use Bloom's taxonomy verbs. Be specific and measurable.",
        "material": "Generate a brief content outline for a teaching material. Include key topics, activities, and learning objectives.",
        "assessment": "Suggest an assessment item including: title, description, type (quiz/assignment/project/exam), and recommended weight.",
    }

    base_prompt = gap_prompts.get(request.gap_type, gap_prompts["material"])
    context = f"\n\nAdditional context: {request.context}" if request.context else ""
    design_block = f"\n\n{design_ctx}" if design_ctx else ""

    result = await llm_service.generate_text(
        prompt=f"{base_prompt}{context}{design_block}",
        system_prompt="You are an expert university curriculum designer helping fill gaps in a unit structure.",
        user=current_user,
        db=db,
    )

    content = result if isinstance(result, str) else str(result)

    return FillGapResponse(
        gap_type=request.gap_type,
        generated_content=content,
        suggestions=[],
    )


# =============================================================================
# Visual Prompt Generator (15.9)
# =============================================================================

VISUAL_PROMPT_STYLES = {
    "photographic",
    "illustration",
    "diagram",
    "flat-vector",
    "watercolor",
    "3d-render",
}

VISUAL_PROMPT_ASPECT_RATIOS = {"square", "landscape", "portrait"}


@router.post("/visual-prompt", response_model=VisualPromptResponse)
async def generate_visual_prompt(
    request: VisualPromptRequest,
    current_user: User = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db),
) -> VisualPromptResponse:
    """
    Generate a ready-to-copy image generation prompt from educational content.

    The user selects text in the editor, picks a visual style, and receives
    a detailed prompt they can paste into Midjourney, DALL-E, or similar tools.
    """
    if request.style not in VISUAL_PROMPT_STYLES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid style. Must be one of: {', '.join(sorted(VISUAL_PROMPT_STYLES))}",
        )
    if request.aspect_ratio not in VISUAL_PROMPT_ASPECT_RATIOS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid aspect ratio. Must be one of: {', '.join(sorted(VISUAL_PROMPT_ASPECT_RATIOS))}",
        )

    context_line = f"\nPurpose: {request.context}" if request.context else ""

    prompt = f"""Generate a detailed image-generation prompt based on the following educational content.

Style: {request.style}
Aspect ratio: {request.aspect_ratio}{context_line}

Educational content:
{request.content}

Return a JSON object with exactly these keys:
{{
  "prompt": "A detailed, vivid image generation prompt (1-3 sentences). Be specific about composition, colours, mood, and subject matter. Make it tool-agnostic (works with Midjourney, DALL-E, Stable Diffusion, etc.).",
  "negative_prompt": "A comma-separated list of things to avoid (e.g. text, watermarks, blurry, low quality).",
  "style_notes": "1-2 sentences of practical tips for generating this style of image (e.g. recommended tools, settings, or modifiers)."
}}

Return ONLY valid JSON, no markdown fences or extra text."""

    try:
        result = await llm_service.generate_text(
            prompt=prompt,
            system_prompt=(
                "You are an expert visual prompt engineer for AI image generation tools. "
                "You create detailed, effective prompts that produce high-quality educational imagery. "
                "Always respond with valid JSON only."
            ),
            user=current_user,
            db=db,
            temperature=0.8,
        )

        response_text = (
            result
            if isinstance(result, str)
            else "".join([chunk async for chunk in result])
        )

        # Clean markdown formatting if present
        response_text = response_text.strip()
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        response_text = response_text.strip()

        parsed = json.loads(response_text)

        return VisualPromptResponse(
            prompt=parsed.get("prompt", ""),
            negative_prompt=parsed.get("negative_prompt", ""),
            style_notes=parsed.get("style_notes", ""),
        )

    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to parse AI response as JSON: {e}",
        )
    except Exception as e:
        raise _llm_error_response(e, "Visual prompt generation")


# =============================================================================
# Video Interaction AI Generation (6b-iii)
# =============================================================================

VALID_QUESTION_TYPES = {
    "multiple_choice",
    "true_false",
    "multi_select",
    "short_answer",
    "fill_in_blank",
}


@router.post(
    "/generate-video-interaction",
    response_model=GenerateVideoInteractionResponse,
)
async def generate_video_interaction(
    request: GenerateVideoInteractionRequest,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db),
) -> GenerateVideoInteractionResponse:
    """Generate a single quiz interaction from transcript context."""
    if request.question_type not in VALID_QUESTION_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid question_type. Must be one of: {', '.join(sorted(VALID_QUESTION_TYPES))}",
        )

    # Build context
    context_parts: list[str] = []

    design_ctx = None
    if request.unit_id or request.design_id:
        design_ctx = await get_design_context(
            db, request.unit_id or "", request.design_id
        )
    if design_ctx:
        context_parts.append(design_ctx)

    if request.week_number and request.unit_id:
        enriched = _enrich_with_week_context(
            db, request.unit_id, request.week_number, ""
        )
        if enriched.strip():
            context_parts.append(enriched.strip())

    context_block = "\n".join(context_parts)
    context_section = f"\n\nEducational context:\n{context_block}" if context_block else ""

    prompt = f"""Generate a {request.question_type.replace("_", " ")} quiz question based on the following video transcript segment.

Difficulty: {request.difficulty}
{context_section}

Transcript segment:
{request.segment_text}

Return a JSON object with this exact structure:
{{
  "question_text": "The question to ask the student",
  "question_type": "{request.question_type}",
  "options": [
    {{"text": "Option text", "correct": true}},
    {{"text": "Option text", "correct": false}}
  ],
  "feedback": "Feedback shown after answering",
  "explanation": "Detailed explanation of the correct answer",
  "points": 1
}}

Requirements:
- For multiple_choice: provide 4 options, exactly 1 correct
- For true_false: provide 2 options ("True" and "False"), exactly 1 correct
- For multi_select: provide 4 options, 2-3 correct
- For short_answer or fill_in_blank: provide 1 option with the expected answer, marked correct
- The question should test understanding of the transcript content
- Use Australian/British English
- Return ONLY valid JSON, no markdown fences or extra text"""

    try:
        result = await llm_service.generate_text(
            prompt=prompt,
            system_prompt=(
                "You are an expert educational video interaction designer. "
                "You create engaging quiz questions that test student comprehension of video content. "
                "Always respond with valid JSON only."
            ),
            user=current_user,
            db=db,
            temperature=0.7,
        )

        response_text = (
            result
            if isinstance(result, str)
            else "".join([chunk async for chunk in result])
        )

        response_text = _strip_markdown_fences(response_text)
        parsed = json.loads(response_text)

        return GenerateVideoInteractionResponse(
            question_text=parsed.get("question_text", ""),
            question_type=parsed.get("question_type", request.question_type),
            options=[
                GenerateVideoInteractionOption(
                    text=o.get("text", ""),
                    correct=o.get("correct", False),
                )
                for o in parsed.get("options", [])
            ],
            feedback=parsed.get("feedback", ""),
            explanation=parsed.get("explanation", ""),
            points=parsed.get("points", 1),
        )

    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to parse AI response as JSON: {e}",
        )
    except Exception as e:
        raise _llm_error_response(e, "Video interaction generation")


@router.post(
    "/suggest-interaction-points",
    response_model=SuggestInteractionPointsResponse,
)
async def suggest_interaction_points(
    request: SuggestInteractionPointsRequest,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db),
) -> SuggestInteractionPointsResponse:
    """Scan a full transcript and suggest interaction points with generated questions."""
    # Build context
    context_parts: list[str] = []

    design_ctx = None
    if request.unit_id or request.design_id:
        design_ctx = await get_design_context(
            db, request.unit_id or "", request.design_id
        )
    if design_ctx:
        context_parts.append(design_ctx)

    if request.week_number and request.unit_id:
        enriched = _enrich_with_week_context(
            db, request.unit_id, request.week_number, ""
        )
        if enriched.strip():
            context_parts.append(enriched.strip())

    context_block = "\n".join(context_parts)
    context_section = f"\n\nEducational context:\n{context_block}" if context_block else ""

    # Format transcript with timestamps
    transcript_lines = "\n".join(
        f"[{s.start:.1f}s - {s.end:.1f}s] {s.text}"
        for s in request.transcript_segments
    )

    prompt = f"""Analyze the following video transcript and identify the {request.max_interactions} best points to insert quiz interactions.

Look for:
- Key concept introductions or transitions
- Important definitions or facts
- Points where student comprehension should be checked
- Natural pauses or topic shifts
{context_section}

Transcript:
{transcript_lines}

Return a JSON object with this exact structure:
{{
  "interactions": [
    {{
      "time": 45.0,
      "question_text": "The question to ask",
      "question_type": "multiple_choice",
      "options": [
        {{"text": "Option A", "correct": true}},
        {{"text": "Option B", "correct": false}},
        {{"text": "Option C", "correct": false}},
        {{"text": "Option D", "correct": false}}
      ],
      "feedback": "Feedback shown after answering",
      "explanation": "Why the correct answer is correct",
      "points": 1
    }}
  ]
}}

Requirements:
- Return at most {request.max_interactions} interactions
- Space them evenly through the transcript
- Use a mix of question types (multiple_choice, true_false, multi_select)
- Each interaction time must fall within the transcript time range
- Use Australian/British English
- Return ONLY valid JSON, no markdown fences or extra text"""

    try:
        result = await llm_service.generate_text(
            prompt=prompt,
            system_prompt=(
                "You are an expert educational video interaction designer. "
                "You analyze video transcripts to identify key learning moments and create "
                "engaging quiz questions. Always respond with valid JSON only."
            ),
            user=current_user,
            db=db,
            temperature=0.7,
        )

        response_text = (
            result
            if isinstance(result, str)
            else "".join([chunk async for chunk in result])
        )

        response_text = _strip_markdown_fences(response_text)
        parsed = json.loads(response_text)

        interactions_data = parsed.get("interactions", [])

        return SuggestInteractionPointsResponse(
            interactions=[
                SuggestedInteraction(
                    time=i.get("time", 0.0),
                    question_text=i.get("question_text", ""),
                    question_type=i.get("question_type", "multiple_choice"),
                    options=[
                        GenerateVideoInteractionOption(
                            text=o.get("text", ""),
                            correct=o.get("correct", False),
                        )
                        for o in i.get("options", [])
                    ],
                    feedback=i.get("feedback", ""),
                    explanation=i.get("explanation", ""),
                    points=i.get("points", 1),
                )
                for i in interactions_data
            ]
        )

    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to parse AI response as JSON: {e}",
        )
    except Exception as e:
        raise _llm_error_response(e, "Interaction suggestion")
