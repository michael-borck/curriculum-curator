"""Tests for absorbed tool capabilities (ADR-068).

Covers: AI image generation (15.5 — Limn), branching scenario drafting
(19A.7) and quiz generation (19C.6) from Playable Lessons, and lesson-plan
frameworks (5.12/5.13) from Lesson Loom.
"""

import base64
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.api.routes.ai import (
    generate_branching,
    generate_image,
    generate_lesson_plan,
    generate_quiz,
    list_lesson_plan_frameworks,
)
from app.models import Unit, User
from app.models.weekly_material import WeeklyMaterial
from app.schemas.ai import (
    BranchingCardDraft,
    BranchingChoiceDraft,
    GenerateBranchingRequest,
    GenerateBranchingResponse,
    GenerateImageRequest,
    GenerateQuizRequest,
    GenerateQuizResponse,
    LessonPlanRequest,
    LessonPlanObjective,
    LessonPlanResponse,
    LessonPlanSegment,
    QuizOptionDraft,
    QuizQuestionDraft,
)
from app.services.git_content_service import GitContentService
from app.services.material_parsers.persistence import material_images_dir
from app.services.llm_service import llm_service

paragraph = lambda text: {  # noqa: E731
    "type": "paragraph",
    "content": [{"type": "text", "text": text}],
}

PROSE_DOC = {
    "type": "doc",
    "content": [
        paragraph("Phishing attacks trick staff into revealing credentials."),
        paragraph("Training should include simulated phishing exercises."),
    ],
}

TINY_PNG = (
    b"\x89PNG\r\n\x1a\n"
    b"\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx"
    b"\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N\x00"
    b"\x00\x00\x00IEND\xaeB`\x82"
)


@pytest.fixture
def prose_material(test_db: Session, test_unit: Unit) -> WeeklyMaterial:
    material = WeeklyMaterial(
        unit_id=test_unit.id,
        week_number=1,
        title="Security awareness",
        type="lecture",
        content_json=PROSE_DOC,
    )
    test_db.add(material)
    test_db.commit()
    test_db.refresh(material)
    return material


def _mock_llm(response, error=None):
    return patch(
        "app.api.routes.ai.llm_service.generate_structured_content",
        new=AsyncMock(return_value=(response, error)),
    )


# ---------------------------------------------------------------------------
# Branching scenario generation (Playable Lessons capability)
# ---------------------------------------------------------------------------


def _branch_response(**overrides) -> GenerateBranchingResponse:
    cards = [
        BranchingCardDraft(
            card_id="c1",
            card_type="content",
            card_title="The email arrives",
            card_content="You receive an urgent email about your account.",
            choices=[
                BranchingChoiceDraft(
                    id="ch1", text="Click the link", target_card_id="c2"
                ),
                BranchingChoiceDraft(
                    id="ch2", text="Report it", target_card_id="c3"
                ),
            ],
        ),
        BranchingCardDraft(
            card_id="c2",
            card_type="ending",
            card_title="Credentials stolen",
            card_content="You entered credentials on a fake page.",
            end_score=0,
            end_message="Verify sender addresses before clicking.",
        ),
        BranchingCardDraft(
            card_id="c3",
            card_type="ending",
            card_title="Threat reported",
            card_content="IT confirms it was phishing.",
            end_score=10,
            end_message="Reporting stops the attack.",
        ),
    ]
    return GenerateBranchingResponse(cards=cards, **overrides)


@pytest.mark.asyncio
async def test_branching_returns_cards_and_clean_warnings(
    test_db: Session, test_user: User, prose_material: WeeklyMaterial
):
    response = _branch_response()
    with _mock_llm(response) as mock_generate:
        result = await generate_branching(
            request=GenerateBranchingRequest(),
            material=prose_material,
            db=test_db,
            current_user=test_user,
        )

    assert result.start_card_id == "c1"
    assert len(result.cards) == 3
    assert result.warnings == []
    prompt = mock_generate.call_args.kwargs["prompt"]
    assert "phishing" in prompt.lower()


@pytest.mark.asyncio
async def test_branching_flags_broken_structure(
    test_db: Session, test_user: User, prose_material: WeeklyMaterial
):
    cards = _branch_response().cards
    # Break the graph: point c1's second choice at a missing card, add a dead
    # end, and append an orphan.
    cards[0].choices[1].target_card_id = "missing"
    orphan = BranchingCardDraft(
        card_id="c9", card_title="Orphan", card_content="Unreachable."
    )
    broken = GenerateBranchingResponse(cards=[*cards, orphan])
    with _mock_llm(broken):
        result = await generate_branching(
            request=GenerateBranchingRequest(),
            material=prose_material,
            db=test_db,
            current_user=test_user,
        )

    joined = "\n".join(result.warnings)
    assert "points at missing card 'missing'" in joined
    assert "unreachable" in joined.lower()
    # The broken graph leaves c3 unreachable from the start card.
    # Only the non-ending orphan (c9) counts as a dead end.
    assert "'c9' has no choices (dead end)" in joined


@pytest.mark.asyncio
async def test_branching_rejects_empty_material(
    test_db: Session, test_user: User, test_unit: Unit
):
    material = WeeklyMaterial(
        unit_id=test_unit.id,
        week_number=2,
        title="Empty",
        type="lecture",
        content_json={"type": "doc", "content": []},
    )
    test_db.add(material)
    test_db.commit()

    with pytest.raises(HTTPException) as exc_info:
        await generate_branching(
            request=GenerateBranchingRequest(),
            material=material,
            db=test_db,
            current_user=test_user,
        )
    assert exc_info.value.status_code == 422


# ---------------------------------------------------------------------------
# Quiz generation into structured blocks (Playable Lessons capability)
# ---------------------------------------------------------------------------


def _quiz_response() -> GenerateQuizResponse:
    return GenerateQuizResponse(
        questions=[
            QuizQuestionDraft(
                question_type="multiple_choice",
                question_text="What is the safest response to a suspicious email?",
                options=[
                    QuizOptionDraft(id="o1", text="Click the link", correct=False),
                    QuizOptionDraft(id="o2", text="Report to IT", correct=True),
                ],
                feedback="Reporting lets IT block the campaign.",
            ),
            QuizQuestionDraft(
                question_type="true_false",
                question_text="Simulated phishing is used in awareness training.",
                options=[
                    QuizOptionDraft(id="o1", text="True", correct=True),
                    QuizOptionDraft(id="o2", text="False", correct=False),
                ],
            ),
        ]
    )


@pytest.mark.asyncio
async def test_quiz_generates_typed_questions(
    test_db: Session, test_user: User, prose_material: WeeklyMaterial
):
    with _mock_llm(_quiz_response()) as mock_generate:
        result = await generate_quiz(
            request=GenerateQuizRequest(),
            material=prose_material,
            db=test_db,
            current_user=test_user,
        )

    assert len(result.questions) == 2
    assert result.questions[0].question_type == "multiple_choice"
    assert result.questions[0].options[1].correct is True
    prompt = mock_generate.call_args.kwargs["prompt"]
    assert "simulated phishing" in prompt.lower()


@pytest.mark.asyncio
async def test_quiz_rejects_unsupported_question_types(
    test_db: Session, test_user: User, prose_material: WeeklyMaterial
):
    with pytest.raises(HTTPException) as exc_info:
        await generate_quiz(
            request=GenerateQuizRequest(question_types=["drag_and_drop"]),
            material=prose_material,
            db=test_db,
            current_user=test_user,
        )
    assert exc_info.value.status_code == 400
    assert "Unsupported question types" in exc_info.value.detail


@pytest.mark.asyncio
async def test_quiz_surfaces_llm_failure_as_502(
    test_db: Session, test_user: User, prose_material: WeeklyMaterial
):
    with (
        _mock_llm(None, "provider exploded"),
        pytest.raises(HTTPException) as exc_info,
    ):
        await generate_quiz(
            request=GenerateQuizRequest(),
            material=prose_material,
            db=test_db,
            current_user=test_user,
        )
    assert exc_info.value.status_code == 502


# ---------------------------------------------------------------------------
# Lesson-plan frameworks (Lesson Loom capability)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_frameworks_listing_includes_guidance():
    frameworks = await list_lesson_plan_frameworks()
    assert set(frameworks) == {"gagne_nine_events", "bopps", "five_e"}
    for fw in frameworks.values():
        assert fw["when_to_use"]
        assert fw["summary"]
        assert fw["name"]


@pytest.mark.asyncio
async def test_lesson_plan_happy_path(test_db: Session, test_user: User):
    plan = LessonPlanResponse(
        title="Phishing Awareness",
        objectives=[
            LessonPlanObjective(text="Identify phishing cues", bloom_level="analyse")
        ],
        segments=[LessonPlanSegment(name="Engage", minutes=50, description="Hook")],
        formative_checks=[],
        differentiation_notes="",
        materials_checklist=[],
        homework_bridge="",
    )
    with _mock_llm(plan) as mock_generate:
        result = await generate_lesson_plan(
            request=LessonPlanRequest(
                content="Phishing awareness content.",
                framework_id="five_e",
                duration_minutes=50,
            ),
            current_user=test_user,
            db=test_db,
        )

    assert result.title == "Phishing Awareness"
    assert result.objectives[0].bloom_level == "analyse"
    prompt = mock_generate.call_args.kwargs["prompt"]
    assert "Elaborate" in prompt  # 5E phases present
    assert "sum exactly to 50" in prompt


@pytest.mark.asyncio
async def test_lesson_plan_rejects_unknown_framework(
    test_db: Session, test_user: User
):
    with pytest.raises(HTTPException) as exc_info:
        await generate_lesson_plan(
            request=LessonPlanRequest(
                content="Some content.", framework_id="montessori"
            ),
            current_user=test_user,
            db=test_db,
        )
    assert exc_info.value.status_code == 400


# ---------------------------------------------------------------------------
# AI image generation (Limn capability)
# ---------------------------------------------------------------------------


class TestGenerateImageService:
    @pytest.mark.asyncio
    async def test_no_provider_returns_error(self, test_db: Session):
        with patch.object(llm_service, "_get_llm_config", return_value=("", "", None, None)):
            image_bytes, error = await llm_service.generate_image("a fox")
        assert image_bytes is None
        assert "No AI provider configured" in error

    @pytest.mark.asyncio
    async def test_anthropic_has_no_image_model(self, test_db: Session):
        config = ("claude-sonnet-4", "anthropic", "sk-key", None)
        with patch.object(llm_service, "_get_llm_config", return_value=config):
            image_bytes, error = await llm_service.generate_image("a fox")
        assert image_bytes is None
        assert "not available for the 'anthropic' provider" in error

    @pytest.mark.asyncio
    async def test_openai_generation_decodes_base64(self):
        config = ("dall-e-3", "openai", "sk-key", None)
        encoded = base64.b64encode(TINY_PNG).decode()
        fake_response = type(
            "Response", (), {"data": [type("Data", (), {"b64_json": encoded})()]}
        )()
        with (
            patch.object(llm_service, "_get_llm_config", return_value=config),
            patch(
                "litellm.aimage_generation",
                new=AsyncMock(return_value=fake_response),
            ),
        ):
            image_bytes, model_used = await llm_service.generate_image("a fox")
        assert image_bytes == TINY_PNG
        assert model_used == "openai/dall-e-3"


class TestGenerateImageRoute:
    @pytest.fixture
    def image_material(self, test_db: Session, test_unit: Unit) -> WeeklyMaterial:
        material = WeeklyMaterial(
            unit_id=test_unit.id,
            week_number=1,
            title="With images",
            type="lecture",
            content_json=PROSE_DOC,
        )
        test_db.add(material)
        test_db.commit()
        test_db.refresh(material)
        return material

    @pytest.mark.asyncio
    async def test_without_material_returns_data_url(
        self, test_db: Session, test_user: User
    ):
        with patch(
            "app.api.routes.ai.llm_service.generate_image",
            new=AsyncMock(return_value=(TINY_PNG, "openai/dall-e-3")),
        ):
            result = await generate_image(
                request=GenerateImageRequest(prompt="water cycle diagram"),
                current_user=test_user,
                db=test_db,
            )
        assert result.url.startswith("data:image/png;base64,")
        assert result.filename == ""

    @pytest.mark.asyncio
    async def test_with_material_saves_to_library(
        self,
        test_db: Session,
        test_user: User,
        image_material: WeeklyMaterial,
        tmp_path,
    ):
        git = GitContentService(repos_base=str(tmp_path / "repos"))
        with (
            patch(
                "app.api.routes.ai.llm_service.generate_image",
                new=AsyncMock(return_value=(TINY_PNG, "gemini/imagen-3")),
            ),
            patch("app.api.routes.ai.get_git_service", return_value=git),
        ):
            result = await generate_image(
                request=GenerateImageRequest(
                    prompt="phishing email illustration",
                    material_id=str(image_material.id),
                ),
                current_user=test_user,
                db=test_db,
            )

        assert result.url == (
            f"/api/materials/units/{image_material.unit_id}"
            f"/materials/{image_material.id}/images/{result.filename}"
        )
        stored = git.read_binary(
            str(image_material.unit_id),
            f"{material_images_dir(image_material)}/{result.filename}",
        )
        assert stored == TINY_PNG
