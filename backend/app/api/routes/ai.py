"""
AI/LLM API routes for advanced content generation and analysis
"""

from fastapi import APIRouter, Depends, HTTPException

from app.api import deps
from app.models import User
from app.schemas.llm import (
    ChatCompletionRequest,
    ContentEnhanceRequest,
    ContentTranslationRequest,
    FeedbackGenerationRequest,
    GeneratedFeedback,
    GeneratedQuestion,
    LLMResponse,
    PedagogyAnalysisRequest,
    PedagogyAnalysisResponse,
    QuestionGenerationRequest,
    SummaryGenerationRequest,
)
from app.services.advanced_llm_service import advanced_llm_service

router = APIRouter()


@router.post("/enhance", response_model=LLMResponse)
async def enhance_content(
    request: ContentEnhanceRequest,
    current_user: User = Depends(deps.get_current_active_user),
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
        enhanced_content = await advanced_llm_service.enhance_content(
            content=request.content,
            enhancement_type=request.enhancement_type,
            pedagogy_style=request.pedagogy_style,
            target_level=request.target_level,
            preserve_structure=request.preserve_structure,
            focus_areas=request.focus_areas,
        )

        return LLMResponse(
            content=enhanced_content,
            model="gpt-3.5-turbo",
            provider="openai",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Enhancement failed: {e!s}")


@router.post("/analyze-pedagogy", response_model=PedagogyAnalysisResponse)
async def analyze_pedagogy(
    request: PedagogyAnalysisRequest,
    current_user: User = Depends(deps.get_current_active_user),
) -> PedagogyAnalysisResponse:
    """
    Analyze content for pedagogical quality and alignment.

    Returns:
    - Current pedagogical style
    - Confidence score
    - Strengths and weaknesses
    - Improvement suggestions
    - Alignment score (if target style provided)
    """
    try:
        return await advanced_llm_service.analyze_pedagogy(
            content=request.content,
            check_alignment=request.check_alignment,
            suggest_improvements=request.suggest_improvements,
            target_style=request.target_style,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {e!s}")


@router.post("/generate-questions", response_model=list[GeneratedQuestion])
async def generate_questions(
    request: QuestionGenerationRequest,
    current_user: User = Depends(deps.get_current_active_user),
) -> list[GeneratedQuestion]:
    """
    Generate assessment questions from content.

    Supports multiple question types:
    - multiple_choice
    - short_answer
    - true_false
    - essay
    - fill_blank
    """
    try:
        return await advanced_llm_service.generate_questions(
            content=request.content,
            question_types=request.question_types,
            count=request.count,
            difficulty=request.difficulty,
            bloom_levels=request.bloom_levels,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Question generation failed: {e!s}"
        )


@router.post("/generate-summary", response_model=LLMResponse)
async def generate_summary(
    request: SummaryGenerationRequest,
    current_user: User = Depends(deps.get_current_active_user),
) -> LLMResponse:
    """
    Generate summary of content.

    Summary types:
    - executive: High-level overview for stakeholders
    - key_points: Main learning points
    - abstract: Academic abstract
    - tldr: Brief summary
    """
    try:
        summary = await advanced_llm_service.generate_summary(
            content=request.content,
            summary_type=request.summary_type,
            max_length=request.max_length,
            include_examples=request.include_examples,
            bullet_points=request.bullet_points,
        )

        return LLMResponse(
            content=summary,
            model="gpt-3.5-turbo",
            provider="openai",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Summary generation failed: {e!s}")


@router.post("/generate-feedback", response_model=GeneratedFeedback)
async def generate_feedback(
    request: FeedbackGenerationRequest,
    current_user: User = Depends(deps.get_current_active_user),
) -> GeneratedFeedback:
    """
    Generate feedback for student work.

    Features:
    - Rubric-based assessment
    - Customizable tone (encouraging, neutral, direct)
    - Strength highlighting
    - Improvement suggestions
    """
    try:
        return await advanced_llm_service.generate_feedback(
            student_work=request.student_work,
            rubric=request.rubric,
            assignment_context=request.assignment_context,
            feedback_tone=request.feedback_tone,
            include_suggestions=request.include_suggestions,
            highlight_strengths=request.highlight_strengths,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Feedback generation failed: {e!s}"
        )


@router.post("/translate", response_model=LLMResponse)
async def translate_content(
    request: ContentTranslationRequest,
    current_user: User = Depends(deps.get_current_active_user),
) -> LLMResponse:
    """
    Translate educational content to another language.

    Features:
    - Preserves formatting
    - Cultural adaptation option
    - Technical term glossary support
    """
    try:
        translated = await advanced_llm_service.translate_content(
            content=request.content,
            target_language=request.target_language,
            preserve_formatting=request.preserve_formatting,
            cultural_adaptation=request.cultural_adaptation,
            glossary=request.glossary,
        )

        return LLMResponse(
            content=translated,
            model="gpt-3.5-turbo",
            provider="openai",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Translation failed: {e!s}")


@router.post("/learning-path")
async def generate_learning_path(
    topic: str,
    current_knowledge: str,
    target_level: str,
    available_time: str,
    learning_style: str | None = None,
    current_user: User = Depends(deps.get_current_active_user),
) -> dict:
    """
    Generate personalized learning path.

    Creates a structured learning journey with:
    - Prerequisites
    - Core concepts in sequence
    - Practical exercises
    - Assessment milestones
    - Time estimates
    - Resource recommendations
    """
    try:
        return await advanced_llm_service.generate_learning_path(
            topic=topic,
            current_knowledge=current_knowledge,
            target_level=target_level,
            available_time=available_time,
            learning_style=learning_style,
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
) -> dict:
    """
    Detect and explain student misconceptions.

    Analyzes student responses to identify:
    - Specific misconceptions
    - Sources of confusion
    - Correction strategies
    - Remediation suggestions
    """
    try:
        return await advanced_llm_service.detect_misconceptions(
            student_response=student_response,
            correct_concept=correct_concept,
            context=context,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Misconception detection failed: {e!s}"
        )


@router.post("/chat", response_model=LLMResponse)
async def chat_completion(
    request: ChatCompletionRequest,
    current_user: User = Depends(deps.get_current_active_user),
) -> LLMResponse:
    """
    General chat completion for educational assistance.

    Supports:
    - Multi-turn conversations
    - Temperature control
    - Token limits
    - Streaming responses
    """
    try:
        # Convert to service format
        messages = request.messages

        response = await advanced_llm_service.get_completion(
            messages=messages,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
        )

        return LLMResponse(
            content=response,
            model=request.model or "gpt-3.5-turbo",
            provider=request.provider or "openai",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat completion failed: {e!s}")


@router.get("/models")
async def list_available_models(
    current_user: User = Depends(deps.get_current_active_user),
) -> dict:
    """
    List available AI models and providers.

    Returns configured models with their capabilities.
    """
    return {
        "providers": {
            "openai": {
                "available": hasattr(advanced_llm_service.providers, "openai"),
                "models": ["gpt-4", "gpt-3.5-turbo"],
                "capabilities": ["chat", "completion", "embedding"],
            },
            "anthropic": {
                "available": hasattr(advanced_llm_service.providers, "anthropic"),
                "models": ["claude-3-opus", "claude-3-sonnet", "claude-3-haiku"],
                "capabilities": ["chat", "completion"],
            },
        },
        "default_model": "gpt-3.5-turbo",
        "features": [
            "content_enhancement",
            "pedagogy_analysis",
            "question_generation",
            "summarization",
            "feedback_generation",
            "translation",
            "learning_paths",
            "misconception_detection",
        ],
    }


@router.post("/validate-content")
async def validate_content_with_ai(
    content: str,
    validation_type: str = "comprehensive",
    current_user: User = Depends(deps.get_current_active_user),
) -> dict:
    """
    Validate content using AI for various quality checks.

    Validation types:
    - comprehensive: All checks
    - factual: Fact checking
    - consistency: Internal consistency
    - completeness: Coverage of topic
    """
    # This would integrate with the plugin system
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
        {"role": "system", "content": "You are an expert content validator."},
        {"role": "user", "content": prompt},
    ]

    try:
        response = await advanced_llm_service.get_completion(messages)
        return {"validation_result": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Validation failed: {e!s}")
