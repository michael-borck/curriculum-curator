"""
Tests for Learning Design context builder — uses real in-memory SQLite (no mocks).
"""

import uuid

import pytest
from sqlalchemy.orm import Session

from app.models.learning_design import DesignStatus, LearningDesign
from app.models.unit import Unit
from app.services.design_context import (
    build_pedagogy_instruction,
    format_design_context,
    get_design_context,
)


# ──────────────────────────────────────────────────────────────
# format_design_context — pure function tests (no DB needed)
# ──────────────────────────────────────────────────────────────


class TestFormatDesignContext:
    def test_full_content(self):
        content = {
            "topic": "Web Development",
            "duration": "12 weeks",
            "teachingPhilosophy": "INQUIRY_BASED",
            "objectives": ["Understand HTML", "Apply CSS"],
            "learningOutcomes": ["Build a website", "Debug code"],
            "prerequisites": ["Basic computing"],
            "pedagogyNotes": "Encourage exploration",
            "differentiation": "Scaffold for weaker students",
            "assessment": {
                "type": "Project",
                "weight": "40%",
                "description": "Build a portfolio site",
                "criteria": ["Responsiveness", "Accessibility"],
            },
            "structure": {
                "preClass": {
                    "activities": ["Watch video"],
                    "duration": "1h",
                    "materials": [],
                },
                "inClass": {
                    "activities": ["Group coding", "Discussion"],
                    "duration": "2h",
                    "materials": [],
                },
                "postClass": {
                    "activities": ["Reflection journal"],
                    "duration": "30min",
                    "materials": [],
                },
            },
        }
        result = format_design_context(content)

        assert result.startswith("=== LEARNING DESIGN SPEC ===")
        assert result.endswith("=== END SPEC ===")
        assert "Topic: Web Development" in result
        assert "Duration: 12 weeks" in result
        assert "Teaching Philosophy: INQUIRY_BASED" in result
        assert "Understand HTML" in result
        assert "Build a website" in result
        assert "Basic computing" in result
        assert "Encourage exploration" in result
        assert "Scaffold for weaker students" in result
        assert "Project" in result
        assert "Responsiveness" in result
        assert "Pre-Class: Watch video" in result
        assert "In-Class: Group coding, Discussion" in result
        assert "Post-Class: Reflection journal" in result

    def test_partial_content(self):
        content = {
            "topic": "Databases",
            "objectives": ["Learn SQL"],
        }
        result = format_design_context(content)

        assert "Topic: Databases" in result
        assert "Learn SQL" in result
        # Sections that weren't provided should not appear
        assert "Duration" not in result
        assert "Teaching Philosophy" not in result
        assert "Assessment" not in result

    def test_empty_dict(self):
        result = format_design_context({})
        assert result == ""

    def test_pedagogy_fallback(self):
        content = {"topic": "Testing"}
        result = format_design_context(content, pedagogy_fallback="project-based")

        assert "Teaching Philosophy: project-based" in result

    def test_pedagogy_fallback_ignored_when_philosophy_present(self):
        content = {"topic": "Testing", "teachingPhilosophy": "COLLABORATIVE"}
        result = format_design_context(content, pedagogy_fallback="project-based")

        assert "COLLABORATIVE" in result
        assert "project-based" not in result

    def test_empty_arrays_skipped(self):
        content = {
            "topic": "Minimal",
            "objectives": [],
            "learningOutcomes": [""],
            "prerequisites": [""],
        }
        result = format_design_context(content)

        assert "Objectives" not in result
        assert "Learning Outcomes" not in result
        assert "Prerequisites" not in result


# ──────────────────────────────────────────────────────────────
# build_pedagogy_instruction — pure function tests
# ──────────────────────────────────────────────────────────────


class TestBuildPedagogyInstruction:
    def test_with_design_content(self):
        content = {
            "teachingPhilosophy": "INQUIRY_BASED",
            "pedagogyNotes": "Use Socratic method",
            "differentiation": "Provide extension activities",
        }
        result = build_pedagogy_instruction(content)

        assert "INQUIRY_BASED" in result
        assert "Socratic method" in result
        assert "extension activities" in result

    def test_with_design_no_notes(self):
        content = {"teachingPhilosophy": "collaborative"}
        result = build_pedagogy_instruction(content)

        assert "collaborative" in result
        assert "group work" in result.lower()

    def test_fallback_style(self):
        result = build_pedagogy_instruction(None, fallback_style="project-based")

        assert "project-based" in result
        assert "real-world" in result.lower()

    def test_default_fallback(self):
        result = build_pedagogy_instruction(None)

        assert "inquiry-based" in result

    def test_empty_design_uses_fallback(self):
        result = build_pedagogy_instruction({}, fallback_style="traditional")

        assert "traditional" in result


# ──────────────────────────────────────────────────────────────
# get_design_context — DB-backed tests
# ──────────────────────────────────────────────────────────────


class TestGetDesignContext:
    @pytest.mark.asyncio
    async def test_with_explicit_design_id(
        self, test_db: Session, test_design: LearningDesign
    ):
        result = await get_design_context(
            test_db, str(test_design.unit_id), design_id=str(test_design.id)
        )
        assert result is not None
        assert "=== LEARNING DESIGN SPEC ===" in result
        assert "Web Development Fundamentals" in result

    @pytest.mark.asyncio
    async def test_approved_preferred_over_draft(
        self, test_db: Session, test_unit: Unit
    ):
        # Create a draft
        draft = LearningDesign(
            id=str(uuid.uuid4()),
            unit_id=test_unit.id,
            version="1.0",
            status=DesignStatus.DRAFT.value,
            content={"topic": "Draft Topic"},
        )
        test_db.add(draft)
        test_db.commit()

        # Create an approved design
        approved = LearningDesign(
            id=str(uuid.uuid4()),
            unit_id=test_unit.id,
            version="2.0",
            status=DesignStatus.APPROVED.value,
            content={"topic": "Approved Topic"},
        )
        test_db.add(approved)
        test_db.commit()

        result = await get_design_context(test_db, str(test_unit.id))
        assert result is not None
        assert "Approved Topic" in result

    @pytest.mark.asyncio
    async def test_draft_fallback(self, test_db: Session, test_design: LearningDesign):
        # test_design fixture is a draft
        result = await get_design_context(test_db, str(test_design.unit_id))
        assert result is not None
        assert "Web Development Fundamentals" in result

    @pytest.mark.asyncio
    async def test_no_design_returns_none(self, test_db: Session, test_unit: Unit):
        result = await get_design_context(test_db, str(test_unit.id))
        assert result is None

    @pytest.mark.asyncio
    async def test_nonexistent_design_id_returns_none(
        self, test_db: Session, test_unit: Unit
    ):
        result = await get_design_context(
            test_db,
            str(test_unit.id),
            design_id="00000000-0000-0000-0000-000000000000",
        )
        assert result is None
