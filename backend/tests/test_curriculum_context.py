"""Tests for the CurriculumContextBuilder seam (candidate #4, part of #2)."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, patch

import pytest

from app.services.curriculum_context import (
    CurriculumContext,
    build_context,
    build_source_materials,
    build_week_context,
)

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

    from app.models.unit import Unit
    from app.models.weekly_material import WeeklyMaterial
    from app.models.weekly_topic import WeeklyTopic


# ---------------------------------------------------------------------------
# CurriculumContext — pure dataclass logic
# ---------------------------------------------------------------------------


class TestCurriculumContext:
    def test_as_block_canonical_order(self) -> None:
        ctx = CurriculumContext(
            design_spec="DESIGN", week_context="WEEK", source_materials="SOURCES"
        )
        assert ctx.as_block() == "DESIGN\n\nWEEK\n\nSOURCES"

    def test_as_block_skips_absent_sections(self) -> None:
        ctx = CurriculumContext(design_spec="DESIGN", source_materials="SOURCES")
        assert ctx.as_block() == "DESIGN\n\nSOURCES"

    def test_as_block_custom_separator(self) -> None:
        ctx = CurriculumContext(design_spec="DESIGN", week_context="WEEK")
        assert ctx.as_block(separator="\n") == "DESIGN\nWEEK"

    def test_as_block_empty(self) -> None:
        assert CurriculumContext().as_block() == ""

    def test_prepend_to_empty_is_noop(self) -> None:
        assert CurriculumContext().prepend_to("topic") == "topic"

    def test_prepend_to_with_content(self) -> None:
        ctx = CurriculumContext(design_spec="DESIGN")
        assert ctx.prepend_to("topic") == "DESIGN\n\ntopic"


# ---------------------------------------------------------------------------
# build_week_context (real DB)
# ---------------------------------------------------------------------------


class TestBuildWeekContext:
    def test_includes_topic_and_materials(
        self,
        test_db: Session,
        test_unit: Unit,
        test_weekly_topic: WeeklyTopic,
        test_weekly_material: WeeklyMaterial,
    ) -> None:
        block = build_week_context(test_db, str(test_unit.id), 1)
        assert block is not None
        assert "Week 1 Topic" in block
        assert "HTML Basics" in block  # topic_title (regression: was .title)
        assert "HTML Lecture" in block  # material title

    def test_none_when_no_topic_or_materials(
        self, test_db: Session, test_unit: Unit
    ) -> None:
        assert build_week_context(test_db, str(test_unit.id), 99) is None


# ---------------------------------------------------------------------------
# build_source_materials (real DB)
# ---------------------------------------------------------------------------


class TestBuildSourceMaterials:
    def test_builds_block_with_title_and_description(
        self, test_db: Session, test_weekly_material: WeeklyMaterial
    ) -> None:
        block = build_source_materials(test_db, [str(test_weekly_material.id)])
        assert block is not None
        assert "=== SOURCE MATERIALS ===" in block
        assert "HTML Lecture" in block
        assert "=== END SOURCE MATERIALS ===" in block

    def test_none_when_no_materials_match(self, test_db: Session) -> None:
        import uuid

        assert build_source_materials(test_db, [str(uuid.uuid4())]) is None


# ---------------------------------------------------------------------------
# build_context — orchestration
# ---------------------------------------------------------------------------


class TestBuildContext:
    @pytest.mark.asyncio
    async def test_assembles_all_sections(
        self,
        test_db: Session,
        test_unit: Unit,
        test_weekly_topic: WeeklyTopic,
        test_weekly_material: WeeklyMaterial,
    ) -> None:
        with patch(
            "app.services.curriculum_context.get_design_context",
            new_callable=AsyncMock,
            return_value="=== LEARNING DESIGN SPEC ===\nTopic: X\n=== END SPEC ===",
        ):
            ctx = await build_context(
                test_db,
                unit_id=str(test_unit.id),
                week_number=1,
                source_material_ids=[str(test_weekly_material.id)],
            )
        assert ctx.design_spec is not None
        assert ctx.week_context is not None
        assert ctx.source_materials is not None
        block = ctx.as_block()
        # Canonical order: design → week → sources.
        assert block.index("LEARNING DESIGN SPEC") < block.index("Week 1 Topic")
        assert block.index("Week 1 Topic") < block.index("SOURCE MATERIALS")

    @pytest.mark.asyncio
    async def test_empty_when_no_inputs(self, test_db: Session) -> None:
        ctx = await build_context(test_db)
        assert ctx.design_spec is None
        assert ctx.week_context is None
        assert ctx.source_materials is None
        assert ctx.prepend_to("topic") == "topic"
