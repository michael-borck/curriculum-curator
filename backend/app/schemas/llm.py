"""
LLM-related schemas for AI integration
"""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class LLMProvider(str, Enum):
    """Supported LLM providers"""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"
    LOCAL = "local"


class LLMModel(str, Enum):
    """Available LLM models"""

    # OpenAI models
    GPT4 = "gpt-4"
    GPT4_TURBO = "gpt-4-turbo-preview"
    GPT35_TURBO = "gpt-3.5-turbo"

    # Anthropic models
    CLAUDE_3_OPUS = "claude-3-opus-20240229"
    CLAUDE_3_SONNET = "claude-3-sonnet-20240229"
    CLAUDE_3_HAIKU = "claude-3-haiku-20240307"

    # Google models
    GEMINI_PRO = "gemini-pro"
    GEMINI_PRO_VISION = "gemini-pro-vision"


class ContentEnhanceRequest(BaseModel):
    """Request for content enhancement"""

    content: str = Field(..., description="Content to enhance")
    enhancement_type: str = Field(
        "improve",
        description="Type of enhancement: improve, simplify, expand, summarize",
    )
    pedagogy_style: str | None = Field(None, description="Target pedagogy style")
    target_level: str | None = Field(
        None, description="Target education level: elementary, middle, high, university"
    )
    preserve_structure: bool = Field(
        True, description="Whether to preserve the original structure"
    )
    focus_areas: list[str] | None = Field(
        None, description="Specific areas to focus on"
    )


class PedagogyAnalysisRequest(BaseModel):
    """Request for pedagogy analysis"""

    content: str = Field(..., description="Content to analyze")
    check_alignment: bool = Field(
        True, description="Check alignment with stated objectives"
    )
    suggest_improvements: bool = Field(
        True, description="Suggest pedagogical improvements"
    )
    target_style: str | None = Field(
        None, description="Target pedagogy style to evaluate against"
    )


class PedagogyAnalysisResponse(BaseModel):
    """Response from pedagogy analysis"""

    current_style: str = Field(..., description="Detected pedagogy style")
    confidence: float = Field(..., ge=0, le=1, description="Confidence score")
    strengths: list[str] = Field(..., description="Pedagogical strengths")
    weaknesses: list[str] = Field(..., description="Areas for improvement")
    suggestions: list[str] = Field(..., description="Specific suggestions")
    alignment_score: float | None = Field(
        None, ge=0, le=100, description="Alignment with objectives"
    )


class QuestionGenerationRequest(BaseModel):
    """Request for question generation"""

    content: str = Field(..., description="Content to generate questions from")
    question_types: list[str] = Field(
        ["multiple_choice", "short_answer"],
        description="Types of questions to generate",
    )
    count: int = Field(5, ge=1, le=20, description="Number of questions")
    difficulty: str = Field(
        "medium", description="Difficulty level: easy, medium, hard"
    )
    bloom_levels: list[str] | None = Field(
        None, description="Bloom's taxonomy levels to target"
    )


class GeneratedQuestion(BaseModel):
    """A generated question with metadata"""

    question: str = Field(..., description="The question text")
    question_type: str = Field(..., description="Type of question")
    options: list[str] | None = Field(None, description="Options for MCQ")
    correct_answer: str | None = Field(None, description="Correct answer")
    explanation: str | None = Field(None, description="Answer explanation")
    difficulty: str = Field(..., description="Difficulty level")
    bloom_level: str | None = Field(None, description="Bloom's taxonomy level")
    points: int = Field(1, description="Suggested point value")


class ContentTranslationRequest(BaseModel):
    """Request for content translation/adaptation"""

    content: str = Field(..., description="Content to translate")
    target_language: str = Field(..., description="Target language code")
    preserve_formatting: bool = Field(True, description="Preserve markdown formatting")
    cultural_adaptation: bool = Field(
        False, description="Adapt examples for target culture"
    )
    glossary: dict[str, str] | None = Field(
        None, description="Technical term translations"
    )


class SummaryGenerationRequest(BaseModel):
    """Request for summary generation"""

    content: str = Field(..., description="Content to summarize")
    summary_type: str = Field(
        "key_points", description="Type: executive, key_points, abstract, tldr"
    )
    max_length: int | None = Field(None, description="Maximum length in words")
    include_examples: bool = Field(False, description="Include key examples in summary")
    bullet_points: bool = Field(True, description="Format as bullet points")


class FeedbackGenerationRequest(BaseModel):
    """Request for automated feedback generation"""

    student_work: str = Field(..., description="Student submission")
    rubric: dict[str, Any] | None = Field(None, description="Grading rubric")
    assignment_context: str | None = Field(None, description="Assignment description")
    feedback_tone: str = Field(
        "encouraging", description="Tone: encouraging, neutral, direct"
    )
    include_suggestions: bool = Field(
        True, description="Include improvement suggestions"
    )
    highlight_strengths: bool = Field(True, description="Highlight what was done well")


class GeneratedFeedback(BaseModel):
    """Generated feedback response"""

    overall_feedback: str = Field(..., description="Overall feedback message")
    strengths: list[str] = Field(..., description="Identified strengths")
    areas_for_improvement: list[str] = Field(..., description="Areas to improve")
    specific_suggestions: list[str] = Field(..., description="Specific suggestions")
    grade_suggestion: str | None = Field(None, description="Suggested grade")
    rubric_scores: dict[str, float] | None = Field(None, description="Rubric scores")


class LLMResponse(BaseModel):
    """Generic LLM response"""

    content: str = Field(..., description="Generated content")
    model: str = Field(..., description="Model used")
    provider: str = Field(..., description="Provider used")
    tokens_used: int | None = Field(None, description="Tokens consumed")
    processing_time: float | None = Field(
        None, description="Processing time in seconds"
    )


class ChatMessage(BaseModel):
    """Chat message for conversational AI"""

    role: str = Field(..., description="Role: system, user, assistant")
    content: str = Field(..., description="Message content")
    metadata: dict[str, Any] | None = Field(None, description="Additional metadata")


class ChatCompletionRequest(BaseModel):
    """Request for chat completion"""

    messages: list[ChatMessage] = Field(..., description="Conversation history")
    temperature: float = Field(0.7, ge=0, le=2, description="Sampling temperature")
    max_tokens: int | None = Field(None, description="Maximum tokens to generate")
    stream: bool = Field(False, description="Stream the response")
    model: str | None = Field(None, description="Specific model to use")
    provider: str | None = Field(None, description="Specific provider to use")
