"""
AI-specific request/response schemas for scaffold, fill-gap, etc.
"""

from pydantic import Field

from app.schemas.base import CamelModel

# =============================================================================
# Scaffold Unit
# =============================================================================


class ScaffoldUnitRequest(CamelModel):
    """Request to generate a full unit structure from a title + description."""

    title: str = Field(..., min_length=1, max_length=500)
    description: str = Field(default="", max_length=5000)
    duration_weeks: int = Field(default=12, ge=1, le=52)
    pedagogy_style: str = Field(default="mixed_approach")
    unit_id: str | None = Field(
        default=None, description="Unit ID for Learning Design lookup"
    )
    design_id: str | None = Field(
        default=None, description="Specific Learning Design ID"
    )


class ScaffoldULO(CamelModel):
    code: str
    description: str
    bloom_level: str


class ScaffoldWeek(CamelModel):
    week_number: int
    topic: str
    activities: list[str] = Field(default_factory=list)


class ScaffoldAssessment(CamelModel):
    title: str
    category: str
    weight: float
    due_week: int | None = None


class ScaffoldUnitResponse(CamelModel):
    """AI-generated unit structure for review before saving."""

    title: str
    description: str
    ulos: list[ScaffoldULO]
    weeks: list[ScaffoldWeek]
    assessments: list[ScaffoldAssessment]


# =============================================================================
# Fill the Gap
# =============================================================================


class FillGapRequest(CamelModel):
    """Request to generate content for a specific gap in a unit."""

    unit_id: str
    gap_type: str = Field(..., description="Type of gap: ulo, material, assessment")
    context: str = Field(default="", description="Additional context for generation")
    design_id: str | None = Field(
        default=None, description="Specific Learning Design ID"
    )


class FillGapResponse(CamelModel):
    """Generated content to fill a gap."""

    gap_type: str
    generated_content: str
    suggestions: list[str] = Field(default_factory=list)


# =============================================================================
# Visual Prompt Generator
# =============================================================================


class VisualPromptRequest(CamelModel):
    """Request to generate an image-generation prompt from educational content."""

    content: str = Field(..., min_length=1, max_length=10000)
    style: str = Field(
        ...,
        description="Image style: photographic, illustration, diagram, flat-vector, watercolor, 3d-render",
    )
    aspect_ratio: str = Field(default="landscape")
    context: str = Field(
        default="", max_length=500, description="What the image is for"
    )


class VisualPromptResponse(CamelModel):
    """Generated image prompt ready to paste into Midjourney/DALL-E/etc."""

    prompt: str
    negative_prompt: str
    style_notes: str


# =============================================================================
# Video Interaction AI Generation
# =============================================================================


class GenerateVideoInteractionRequest(CamelModel):
    """Request to generate a quiz interaction from transcript context."""

    segment_text: str = Field(..., min_length=1, max_length=10000)
    question_type: str = Field(default="multiple_choice")
    unit_id: str | None = None
    design_id: str | None = None
    week_number: int | None = None
    difficulty: str = Field(default="medium")


class GenerateVideoInteractionOption(CamelModel):
    text: str
    correct: bool


class GenerateVideoInteractionResponse(CamelModel):
    question_text: str
    question_type: str
    options: list[GenerateVideoInteractionOption]
    feedback: str
    explanation: str
    points: int = 1


class TranscriptSegmentInput(CamelModel):
    start: float
    end: float
    text: str


class SuggestInteractionPointsRequest(CamelModel):
    """Request to scan a full transcript and suggest interaction points."""

    transcript_segments: list[TranscriptSegmentInput]
    unit_id: str | None = None
    design_id: str | None = None
    week_number: int | None = None
    max_interactions: int = Field(default=5, ge=1, le=20)


class SuggestedInteraction(CamelModel):
    time: float
    question_text: str
    question_type: str
    options: list[GenerateVideoInteractionOption]
    feedback: str
    explanation: str
    points: int = 1


class SuggestInteractionPointsResponse(CamelModel):
    interactions: list[SuggestedInteraction]


# =============================================================================
# Speaker Notes Generation (15.11)
# =============================================================================


class GenerateSpeakerNotesRequest(CamelModel):
    """Request to draft speaker notes for selected slides of a material.

    ``slide_indices`` are zero-based indices into the material's slide
    segments (as produced by the slide splitter). Empty list means all
    slides.
    """

    slide_indices: list[int] = Field(default_factory=list)
    design_id: str | None = None


class SpeakerNotesDraft(CamelModel):
    slide_index: int
    notes: str


class GenerateSpeakerNotesResponse(CamelModel):
    drafts: list[SpeakerNotesDraft]


# =============================================================================
# AI Structure Recovery (6.16) — upgrade plain-paragraph content to structure
# =============================================================================


class StructuredBlock(CamelModel):
    """One block the LLM proposes when recovering structure from plain text.

    Constrained to the block kinds the converter can map to TipTap nodes.
    ``text`` is used by heading/paragraph; ``items`` by the list kinds;
    ``level`` (1-3) by headings only.
    """

    kind: str = Field(
        ...,
        description="One of: heading, paragraph, bullet_list, ordered_list",
    )
    text: str = ""
    level: int = Field(default=2, ge=1, le=3)
    items: list[str] = Field(default_factory=list)


class StructuredDocument(CamelModel):
    """The LLM's structured re-interpretation of plain text (no new content)."""

    blocks: list[StructuredBlock]


class RestructureContentRequest(CamelModel):
    """Improve the structure of a material's existing plain content."""

    design_id: str | None = None


class RestructureContentResponse(CamelModel):
    """Proposed structured content for review (propose/apply — no mutation)."""

    content_json: dict[str, object]
    heading_count: int
    list_count: int
    paragraph_count: int


# =============================================================================
# AI Image Generation (15.5 — Limn capabilities, ADR-068)
# =============================================================================

IMAGE_ASPECT_RATIOS = {"square", "landscape", "portrait"}


class GenerateImageRequest(CamelModel):
    """Request to generate an image from a text prompt."""

    prompt: str = Field(..., min_length=1, max_length=4000)
    aspect_ratio: str = Field(default="landscape")
    material_id: str | None = Field(
        default=None,
        description=(
            "When set (and owned), the image is saved into the material's "
            "image library and a durable URL is returned. Otherwise only a "
            "base64 data URL is returned for preview."
        ),
    )
    style: str = Field(
        default="",
        max_length=200,
        description="Optional style hint appended to the prompt",
    )


class GenerateImageResponse(CamelModel):
    url: str = Field(
        ...,
        description=(
            "Material-library URL when material_id was given, else a base64 data URL"
        ),
    )
    filename: str = ""
    model_used: str = ""


# =============================================================================
# Branching Scenario Generation (19A.7 — Playable Lessons, ADR-068)
# =============================================================================


class BranchingChoiceDraft(CamelModel):
    id: str
    text: str
    target_card_id: str
    feedback: str = ""


class BranchingCardDraft(CamelModel):
    card_id: str
    card_type: str = Field(default="content")  # content | branch | ending
    card_title: str
    card_content: str
    choices: list[BranchingChoiceDraft] = Field(default_factory=list)
    end_score: int = 0
    end_message: str = ""
    step_threshold: int = 0
    end_message_efficient: str = ""
    end_message_thorough: str = ""


class GenerateBranchingRequest(CamelModel):
    """Request to draft a branching scenario from a material's content."""

    card_count: int = Field(default=6, ge=3, le=12)
    audience: str = Field(default="", max_length=300)
    design_id: str | None = None


class GenerateBranchingResponse(CamelModel):
    cards: list[BranchingCardDraft]
    start_card_id: str = ""
    warnings: list[str] = Field(default_factory=list)


# =============================================================================
# Quiz Generation into structured blocks (19C.6 — Playable Lessons, ADR-068)
# =============================================================================

QUIZ_QUESTION_TYPES = {
    "multiple_choice",
    "true_false",
    "multi_select",
    "short_answer",
    "fill_in_blank",
}


class QuizOptionDraft(CamelModel):
    id: str
    text: str
    correct: bool


class QuizQuestionDraft(CamelModel):
    question_type: str
    question_text: str
    options: list[QuizOptionDraft] = Field(default_factory=list)
    feedback: str = ""
    explanation: str = ""
    points: int = Field(default=1, ge=1, le=100)


class GenerateQuizRequest(CamelModel):
    """Request to draft practice questions from a material's content."""

    question_types: list[str] = Field(
        default_factory=lambda: ["multiple_choice", "true_false"],
    )
    count: int = Field(default=5, ge=1, le=20)
    design_id: str | None = None


class GenerateQuizResponse(CamelModel):
    questions: list[QuizQuestionDraft]


# =============================================================================
# Lesson Plan Generation (5.12/5.13 — Lesson Loom frameworks, ADR-068)
# =============================================================================


class LessonPlanObjective(CamelModel):
    text: str
    bloom_level: str


class LessonPlanSegment(CamelModel):
    name: str
    minutes: int
    description: str


class FormativeCheck(CamelModel):
    segment: str
    question: str
    misconceptions: list[str] = Field(default_factory=list)


class LessonPlanRequest(CamelModel):
    """Request to generate a framework-structured lesson plan."""

    content: str = Field(..., min_length=1, max_length=20000)
    framework_id: str
    duration_minutes: int = Field(default=50, ge=10, le=300)
    class_size: int | None = Field(default=None, ge=1, le=1000)
    delivery_mode: str = Field(default="", max_length=100)


class LessonPlanResponse(CamelModel):
    title: str
    objectives: list[LessonPlanObjective]
    segments: list[LessonPlanSegment]
    formative_checks: list[FormativeCheck]
    differentiation_notes: str
    materials_checklist: list[str]
    homework_bridge: str
