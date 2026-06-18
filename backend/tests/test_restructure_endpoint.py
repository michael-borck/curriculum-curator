"""Tests for POST /ai/materials/{id}/restructure (story 6.16)."""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.api.routes.ai import restructure_material_content
from app.models import Unit, User
from app.models.weekly_material import WeeklyMaterial
from app.schemas.ai import (
    RestructureContentRequest,
    StructuredBlock,
    StructuredDocument,
)


def _para(text: str) -> dict:
    return {"type": "paragraph", "content": [{"type": "text", "text": text}]}


PLAIN_DOC = {
    "type": "doc",
    "content": [
        _para("Introduction to Recursion"),
        _para("Recursion is when a function calls itself."),
        _para("Base case stops the recursion."),
    ],
}


@pytest.fixture
def plain_material(test_db: Session, test_unit: Unit) -> WeeklyMaterial:
    material = WeeklyMaterial(
        unit_id=test_unit.id,
        week_number=1,
        title="Recursion PDF",
        type="reading",
        content_json=PLAIN_DOC,
    )
    test_db.add(material)
    test_db.commit()
    test_db.refresh(material)
    return material


@pytest.mark.asyncio
async def test_restructures_plain_content(
    test_db: Session, test_user: User, plain_material: WeeklyMaterial
):
    structured = StructuredDocument(
        blocks=[
            StructuredBlock(kind="heading", level=1, text="Introduction"),
            StructuredBlock(
                kind="paragraph", text="Recursion is when a function calls itself."
            ),
            StructuredBlock(kind="bullet_list", items=["Base case stops it"]),
        ]
    )
    with patch(
        "app.api.routes.ai.llm_service.generate_structured_content",
        new=AsyncMock(return_value=(structured, None)),
    ) as mock_gen:
        result = await restructure_material_content(
            request=RestructureContentRequest(),
            material=plain_material,
            db=test_db,
            current_user=test_user,
        )

    assert result.heading_count == 1
    assert result.list_count == 1
    assert result.paragraph_count == 1
    types = [n["type"] for n in result.content_json["content"]]
    assert "heading" in types and "bulletList" in types
    # The prompt should carry the material's existing text
    prompt = mock_gen.call_args.kwargs["prompt"]
    assert "Recursion is when a function calls itself." in prompt
    # Endpoint never mutates the material
    assert plain_material.content_json == PLAIN_DOC


@pytest.mark.asyncio
async def test_rejects_empty_material(
    test_db: Session, test_user: User, test_unit: Unit
):
    material = WeeklyMaterial(
        unit_id=test_unit.id,
        week_number=1,
        title="Empty",
        type="reading",
        content_json={"type": "doc", "content": []},
    )
    test_db.add(material)
    test_db.commit()
    test_db.refresh(material)

    with pytest.raises(HTTPException) as exc:
        await restructure_material_content(
            request=RestructureContentRequest(),
            material=material,
            db=test_db,
            current_user=test_user,
        )
    assert exc.value.status_code == 422


@pytest.mark.asyncio
async def test_surfaces_llm_failure_as_502(
    test_db: Session, test_user: User, plain_material: WeeklyMaterial
):
    with (
        patch(
            "app.api.routes.ai.llm_service.generate_structured_content",
            new=AsyncMock(return_value=(None, "model error")),
        ),
        pytest.raises(HTTPException) as exc,
    ):
        await restructure_material_content(
            request=RestructureContentRequest(),
            material=plain_material,
            db=test_db,
            current_user=test_user,
        )
    assert exc.value.status_code == 502
