"""
AI/LLM API routes for content generation and educational AI features.

This is the unified AI endpoint - all LLM functionality is accessed through /api/ai/*
"""

import json

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api import deps
from app.models import User
from app.models.system_settings import SystemSettings
from app.schemas.ai import (
    FillGapRequest,
    FillGapResponse,
    ScaffoldAssessment,
    ScaffoldULO,
    ScaffoldUnitRequest,
    ScaffoldUnitResponse,
    ScaffoldWeek,
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
from app.services.llm_service import llm_service

router = APIRouter()


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

        async def stream_response():
            async for chunk in llm_service.generate_content(
                pedagogy=request.pedagogy_style,
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
            pedagogy=request.pedagogy_style,
            topic=topic,
            content_type=request.content_type,
            user=current_user,
            db=db,
        ):
            result += chunk
        return {"content": result}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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
        enhanced_content = await llm_service.enhance_content(
            content=request.content,
            enhancement_type=request.enhancement_type,
            pedagogy_style=request.pedagogy_style,
            target_level=request.target_level,
            preserve_structure=request.preserve_structure,
            focus_areas=request.focus_areas,
            user=current_user,
            db=db,
        )
        return LLMResponse(
            content=enhanced_content, model="default", provider="configured"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Enhancement failed: {e!s}")


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
        raise HTTPException(status_code=500, detail=f"Analysis failed: {e!s}")


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
        raise HTTPException(
            status_code=500, detail=f"Question generation failed: {e!s}"
        )


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
        raise HTTPException(
            status_code=500, detail=f"Feedback generation failed: {e!s}"
        )


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
        raise HTTPException(status_code=500, detail=f"Summary generation failed: {e!s}")


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
        raise HTTPException(status_code=500, detail=f"Translation failed: {e!s}")


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
        raise HTTPException(
            status_code=500, detail=f"Learning path generation failed: {e!s}"
        )


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
        raise HTTPException(
            status_code=500, detail=f"Misconception detection failed: {e!s}"
        )


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
        raise HTTPException(status_code=500, detail=f"Chat completion failed: {e!s}")


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
        raise HTTPException(status_code=500, detail=f"Validation failed: {e!s}")


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
    outcomes_text = (
        "; ".join(request.learning_outcomes) if request.learning_outcomes else ""
    )
    style_instruction = ""
    if request.teaching_style:
        style_instruction = (
            f"\nAlign the schedule with a {request.teaching_style} teaching approach."
        )

    prompt = f"""Create a {request.duration_weeks}-week university course schedule for:

Title: {request.unit_title}
Description: {request.unit_description}
Learning Outcomes: {outcomes_text}
{style_instruction}

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
        raise HTTPException(
            status_code=500, detail=f"Schedule generation failed: {e!s}"
        )


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
    prompt = f"""Generate a complete university unit structure for:

Title: {request.title}
Description: {request.description or 'Not provided'}
Duration: {request.duration_weeks} weeks
Pedagogy: {request.pedagogy_style}

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
    )

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
    gap_prompts = {
        "ulo": "Generate a well-written Unit Learning Outcome (ULO) description. Use Bloom's taxonomy verbs. Be specific and measurable.",
        "material": "Generate a brief content outline for a teaching material. Include key topics, activities, and learning objectives.",
        "assessment": "Suggest an assessment item including: title, description, type (quiz/assignment/project/exam), and recommended weight.",
    }

    base_prompt = gap_prompts.get(request.gap_type, gap_prompts["material"])
    context = f"\n\nAdditional context: {request.context}" if request.context else ""

    result = await llm_service.generate_text(
        prompt=f"{base_prompt}{context}",
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
