"""Tests for POST /ai/materials/{id}/generate-speaker-notes (15.11)."""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.api.routes.ai import generate_speaker_notes
from app.models import Unit, User
from app.models.weekly_material import WeeklyMaterial
from app.schemas.ai import (
    GenerateSpeakerNotesRequest,
    GenerateSpeakerNotesResponse,
    SpeakerNotesDraft,
)

paragraph = lambda text: {  # noqa: E731
    "type": "paragraph",
    "content": [{"type": "text", "text": text}],
}

SLIDE_DOC = {
    "type": "doc",
    "content": [
        paragraph("Slide one: recursion basics"),
        {"type": "slideBreak"},
        paragraph("Slide two: base cases"),
        {
            "type": "speakerNotes",
            "content": [paragraph("Existing notes for slide two")],
        },
        {"type": "slideBreak"},
        paragraph("Slide three: recursive cases"),
    ],
}


@pytest.fixture
def slide_material(test_db: Session, test_unit: Unit) -> WeeklyMaterial:
    material = WeeklyMaterial(
        unit_id=test_unit.id,
        week_number=1,
        title="Recursion slides",
        type="lecture",
        content_json=SLIDE_DOC,
    )
    test_db.add(material)
    test_db.commit()
    test_db.refresh(material)
    return material


def _mock_llm(drafts: list[SpeakerNotesDraft]):
    return patch(
        "app.api.routes.ai.llm_service.generate_structured_content",
        new=AsyncMock(return_value=(GenerateSpeakerNotesResponse(drafts=drafts), None)),
    )


@pytest.mark.asyncio
async def test_generates_drafts_for_all_slides(
    test_db: Session, test_user: User, slide_material: WeeklyMaterial
):
    drafts = [
        SpeakerNotesDraft(slide_index=0, notes="Welcome the class."),
        SpeakerNotesDraft(slide_index=1, notes="Stress the base case."),
        SpeakerNotesDraft(slide_index=2, notes="Walk through an example."),
    ]
    with _mock_llm(drafts) as mock_generate:
        result = await generate_speaker_notes(
            request=GenerateSpeakerNotesRequest(),
            material=slide_material,
            db=test_db,
            current_user=test_user,
        )

    assert [d.slide_index for d in result.drafts] == [0, 1, 2]
    prompt = mock_generate.call_args.kwargs["prompt"]
    assert "recursion basics" in prompt
    assert "Existing notes for slide two" in prompt


@pytest.mark.asyncio
async def test_respects_slide_index_selection(
    test_db: Session, test_user: User, slide_material: WeeklyMaterial
):
    drafts = [
        SpeakerNotesDraft(slide_index=0, notes="Only slide one."),
        # A stray draft for an unrequested slide must be filtered out
        SpeakerNotesDraft(slide_index=2, notes="Not requested."),
    ]
    with _mock_llm(drafts) as mock_generate:
        result = await generate_speaker_notes(
            request=GenerateSpeakerNotesRequest(slide_indices=[0]),
            material=slide_material,
            db=test_db,
            current_user=test_user,
        )

    assert [d.slide_index for d in result.drafts] == [0]
    prompt = mock_generate.call_args.kwargs["prompt"]
    assert "base cases" not in prompt


@pytest.mark.asyncio
async def test_rejects_material_without_slide_breaks(
    test_db: Session, test_user: User, test_unit: Unit
):
    material = WeeklyMaterial(
        unit_id=test_unit.id,
        week_number=1,
        title="Plain prose",
        type="lecture",
        content_json={"type": "doc", "content": [paragraph("No slides here")]},
    )
    test_db.add(material)
    test_db.commit()
    test_db.refresh(material)

    with pytest.raises(HTTPException) as exc_info:
        await generate_speaker_notes(
            request=GenerateSpeakerNotesRequest(),
            material=material,
            db=test_db,
            current_user=test_user,
        )
    assert exc_info.value.status_code == 422


@pytest.mark.asyncio
async def test_surfaces_llm_failure_as_502(
    test_db: Session, test_user: User, slide_material: WeeklyMaterial
):
    with (
        patch(
            "app.api.routes.ai.llm_service.generate_structured_content",
            new=AsyncMock(return_value=(None, "provider exploded")),
        ),
        pytest.raises(HTTPException) as exc_info,
    ):
        await generate_speaker_notes(
            request=GenerateSpeakerNotesRequest(),
            material=slide_material,
            db=test_db,
            current_user=test_user,
        )
    assert exc_info.value.status_code == 502
