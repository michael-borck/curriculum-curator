"""
AI/LLM API routes for content generation and educational AI features.

This is the unified AI endpoint - all LLM functionality is accessed through /api/ai/*
"""

import json
import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api import deps
from app.models import User
from app.models.system_settings import SystemSettings
from app.schemas.ai import (
    FillGapRequest,
    FillGapResponse,
    GenerateVideoInteractionRequest,
    GenerateVideoInteractionResponse,
    ScaffoldUnitRequest,
    ScaffoldUnitResponse,
    SuggestInteractionPointsRequest,
    SuggestInteractionPointsResponse,
    VisualPromptRequest,
    VisualPromptResponse,
)
from app.schemas.llm import (
    ChatCompletionRequest,
    ChatMessage,
    ContentEnhanceRequest,
    ContentGenerationRequest,
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
    SummaryGenerationRequest,
    ValidationResult,
)
from app.services.ai_prompts import (
    SCAFFOLD_UNIT_SYSTEM,
    SCHEDULE_SYSTEM,
    SUGGEST_POINTS_SYSTEM,
    VALIDATE_SYSTEM,
    VIDEO_INTERACTION_SYSTEM,
    VISUAL_PROMPT_SYSTEM,
    ValidationCheck,
    render_scaffold_unit_prompt,
    render_schedule_prompt,
    render_suggest_points_prompt,
    render_validation_prompt,
    render_video_interaction_prompt,
    render_visual_prompt,
)
from app.services.curriculum_context import build_context
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
    if any(
        kw in error_lower
        for kw in ("auth", "api key", "api_key", "unauthorized", "invalid key")
    ):
        return HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"{operation}: invalid or missing API key",
        )

    # Rate limiting
    if any(
        kw in error_lower
        for kw in ("rate limit", "rate_limit", "too many requests", "429")
    ):
        return HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"{operation}: rate limited by provider",
        )

    # Connection / availability issues
    if any(
        kw in error_lower
        for kw in ("connect", "timeout", "unreachable", "refused", "503", "502")
    ):
        return HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"{operation}: LLM provider unavailable",
        )

    # Input validation
    if isinstance(e, (ValueError, TypeError)):
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"{operation}: {error_msg}"
        )

    # Unexpected errors — log and return 500
    logger.exception("%s failed unexpectedly", operation)
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"{operation} failed: {error_msg}",
    )


router = APIRouter()


# =============================================================================
# Helpers
# =============================================================================


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

        # Assemble the curriculum context (design spec + week + source materials)
        context = await build_context(
            db,
            unit_id=request.unit_id,
            design_id=request.design_id,
            week_number=request.week_number,
            source_material_ids=request.source_material_ids,
        )
        topic = context.prepend_to(topic)

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
) -> dict[str, Any]:
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
) -> dict[str, Any]:
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
) -> dict[str, Any]:
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
) -> dict[str, Any]:
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
    context = await build_context(
        db, unit_id=request.unit_id, design_id=request.design_id
    )
    style_instruction = ""
    if request.teaching_style:
        style_instruction = "\n" + build_pedagogy_instruction(
            fallback_style=request.teaching_style
        )
    design_block = f"\n{context.design_spec}\n" if context.design_spec else ""
    prompt = render_schedule_prompt(request, style_instruction, design_block)

    result, error = await llm_service.generate_structured_content(
        prompt=prompt,
        response_model=GeneratedSchedule,
        system_prompt=SCHEDULE_SYSTEM,
        inject_schema=False,
        user=current_user,
        db=db,
        temperature=0.7,
    )
    if error or result is None:
        logger.error("Schedule generation failed: %s", error)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=error or "Schedule generation failed",
        )
    result.summary = (
        f"Generated {len(result.weeks)}-week schedule for {request.unit_title}"
    )
    return result


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
        prompt = render_validation_prompt(validation_type, request.content)
        if prompt is None:
            continue

        check, error = await llm_service.generate_structured_content(
            prompt=prompt,
            response_model=ValidationCheck,
            system_prompt=VALIDATE_SYSTEM,
            inject_schema=False,
            user=current_user,
            db=db,
            temperature=0.3,
        )

        # Per-type graceful degradation: one type failing doesn't fail the request.
        if error or check is None:
            results.append(
                ValidationResult(
                    validator_name=validation_type.title(),
                    passed=False,
                    message=f"Validation error: {error or 'no result'}",
                )
            )
            continue

        remediation_prompt = None
        if not check.passed:
            if validation_type == "readability":
                remediation_prompt = "Improve the readability for university undergraduate students. Use clearer language, shorter sentences, and Australian/British spelling."
            elif validation_type == "structure":
                remediation_prompt = "Reorganize for better structure with clear sections: Learning Objectives, Content Body, Summary. Add transitions between sections."

        results.append(
            ValidationResult(
                validator_name=validation_type.title(),
                passed=check.passed,
                message=check.message,
                score=check.score,
                suggestions=check.suggestions,
                remediation_prompt=remediation_prompt,
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
    context = await build_context(
        db, unit_id=request.unit_id, design_id=request.design_id
    )
    pedagogy_instruction = build_pedagogy_instruction(
        fallback_style=request.pedagogy_style
    )
    design_block = f"\n{context.design_spec}\n" if context.design_spec else ""
    prompt = render_scaffold_unit_prompt(request, pedagogy_instruction, design_block)

    result, error = await llm_service.generate_structured_content(
        prompt=prompt,
        response_model=ScaffoldUnitResponse,
        system_prompt=SCAFFOLD_UNIT_SYSTEM,
        inject_schema=False,
        user=current_user,
        db=db,
        max_tokens=4096,
    )
    if error or result is None:
        logger.error("Scaffold generation failed: %s", error)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=error or "Scaffold generation failed",
        )
    return result


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

    prompt = render_visual_prompt(request)

    result, error = await llm_service.generate_structured_content(
        prompt=prompt,
        response_model=VisualPromptResponse,
        system_prompt=VISUAL_PROMPT_SYSTEM,
        inject_schema=False,
        user=current_user,
        db=db,
        temperature=0.8,
    )
    if error or result is None:
        logger.error("Visual prompt generation failed: %s", error)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=error or "Visual prompt generation failed",
        )
    return result


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

    context = await build_context(
        db,
        unit_id=request.unit_id,
        design_id=request.design_id,
        week_number=request.week_number,
    )
    context_block = context.as_block(separator="\n")
    context_section = (
        f"\n\nEducational context:\n{context_block}" if context_block else ""
    )
    prompt = render_video_interaction_prompt(request, context_section)

    result, error = await llm_service.generate_structured_content(
        prompt=prompt,
        response_model=GenerateVideoInteractionResponse,
        system_prompt=VIDEO_INTERACTION_SYSTEM,
        inject_schema=False,
        user=current_user,
        db=db,
        temperature=0.7,
    )
    if error or result is None:
        logger.error("Video interaction generation failed: %s", error)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=error or "Video interaction generation failed",
        )
    return result


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
    context = await build_context(
        db,
        unit_id=request.unit_id,
        design_id=request.design_id,
        week_number=request.week_number,
    )
    context_block = context.as_block(separator="\n")
    context_section = (
        f"\n\nEducational context:\n{context_block}" if context_block else ""
    )

    # Format transcript with timestamps
    transcript_lines = "\n".join(
        f"[{s.start:.1f}s - {s.end:.1f}s] {s.text}" for s in request.transcript_segments
    )
    prompt = render_suggest_points_prompt(request, context_section, transcript_lines)

    result, error = await llm_service.generate_structured_content(
        prompt=prompt,
        response_model=SuggestInteractionPointsResponse,
        system_prompt=SUGGEST_POINTS_SYSTEM,
        inject_schema=False,
        user=current_user,
        db=db,
        temperature=0.7,
    )
    if error or result is None:
        logger.error("Interaction suggestion failed: %s", error)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=error or "Interaction suggestion failed",
        )
    return result
