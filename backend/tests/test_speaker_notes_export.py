"""
Tests that speaker notes survive the export pipeline correctly.

These tests verify the markdown / HTML that the export service produces
*before* it reaches Pandoc. We don't actually invoke Pandoc — that requires
the binary at test time and is not in CI. Instead we patch the conversion
step to capture its input and assert on what would be sent.

Per ADR-064:
- PPTX exports must preserve speaker notes via Pandoc ``::: notes`` fenced
  divs (which Pandoc routes into PowerPoint's speaker notes pane)
- All other export formats must strip speaker notes — they are scaffolding
  for the educator's delivery, never student-facing content
"""

from __future__ import annotations

import uuid
from io import BytesIO
from typing import TYPE_CHECKING, Any

import pytest

from app.models.weekly_material import WeeklyMaterial
from app.services.export_service import ExportFormat, ExportService

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

    from app.models.unit import Unit


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _para(text: str) -> dict[str, Any]:
    return {"type": "paragraph", "content": [{"type": "text", "text": text}]}


def _heading(level: int, text: str) -> dict[str, Any]:
    return {
        "type": "heading",
        "attrs": {"level": level},
        "content": [{"type": "text", "text": text}],
    }


def _slide_break() -> dict[str, Any]:
    return {"type": "slideBreak"}


def _notes(text: str) -> dict[str, Any]:
    return {
        "type": "speakerNotes",
        "content": [
            {
                "type": "paragraph",
                "content": [{"type": "text", "text": text}],
            }
        ],
    }


def _doc(*nodes: dict[str, Any]) -> dict[str, Any]:
    return {"type": "doc", "content": list(nodes)}


@pytest.fixture
def export_svc() -> ExportService:
    return ExportService()


@pytest.fixture
def material_with_notes(test_db: Session, test_unit: Unit) -> WeeklyMaterial:
    """A multi-slide material with speaker notes on every slide."""
    content_json = _doc(
        _heading(1, "Slide 1: Introduction"),
        _para("Welcome to the lecture."),
        _notes("Open with the analogy from last week. Pause for questions."),
        _slide_break(),
        _heading(1, "Slide 2: Core Concept"),
        _para("Here is the main idea."),
        _notes("Spend 5 minutes here. Watch for puzzled faces."),
        _slide_break(),
        _heading(1, "Slide 3: Conclusion"),
        _para("Recap and next steps."),
        _notes("Tie back to the unit learning outcomes."),
    )
    mat = WeeklyMaterial(
        id=str(uuid.uuid4()),
        unit_id=test_unit.id,
        week_number=1,
        title="Slide Lecture With Notes",
        type="lecture",
        description="",
        content_json=content_json,
        order_index=0,
    )
    test_db.add(mat)
    test_db.commit()
    test_db.refresh(mat)
    return mat


@pytest.fixture
def single_slide_material_with_notes(
    test_db: Session, test_unit: Unit
) -> WeeklyMaterial:
    """A single-slide material (no slide breaks) with notes."""
    content_json = _doc(
        _heading(1, "Single Slide"),
        _para("All the content."),
        _notes("Note for the only slide."),
    )
    mat = WeeklyMaterial(
        id=str(uuid.uuid4()),
        unit_id=test_unit.id,
        week_number=1,
        title="Single Slide Material",
        type="lecture",
        description="",
        content_json=content_json,
        order_index=0,
    )
    test_db.add(mat)
    test_db.commit()
    test_db.refresh(mat)
    return mat


# ---------------------------------------------------------------------------
# PPTX export — notes must reach Pandoc as ::: notes fenced divs
# ---------------------------------------------------------------------------


class TestPPTXExportPreservesNotes:
    @pytest.mark.asyncio
    async def test_pptx_with_slide_breaks_passes_notes_to_pandoc(
        self,
        export_svc: ExportService,
        test_db: Session,
        material_with_notes: WeeklyMaterial,
    ) -> None:
        captured: dict[str, Any] = {}

        def fake_convert(
            *,
            markdown: str,
            fmt: ExportFormat,
            title: str | None = None,
            author: str | None = None,
            reference_doc: object | None = None,
        ) -> BytesIO:
            captured["markdown"] = markdown
            captured["fmt"] = fmt
            return BytesIO(b"fake pptx bytes")

        export_svc._convert = fake_convert  # type: ignore[method-assign]

        await export_svc.export_material(
            material_id=str(material_with_notes.id),
            db=test_db,
            fmt=ExportFormat.PPTX,
        )

        md = captured["markdown"]
        assert captured["fmt"] == ExportFormat.PPTX
        # Each slide's notes appear in a Pandoc fenced div
        assert md.count("::: notes") == 3
        assert "Open with the analogy from last week" in md
        assert "Spend 5 minutes here" in md
        assert "Tie back to the unit learning outcomes" in md
        # Slide titles still emitted as H1 per slide segment
        assert "<h1>Slide 1: Introduction</h1>" in md
        assert "<h1>Slide 2: Core Concept</h1>" in md
        assert "<h1>Slide 3: Conclusion</h1>" in md

    @pytest.mark.asyncio
    async def test_pptx_without_slide_breaks_still_preserves_notes(
        self,
        export_svc: ExportService,
        test_db: Session,
        single_slide_material_with_notes: WeeklyMaterial,
    ) -> None:
        captured: dict[str, Any] = {}

        def fake_convert(**kwargs: Any) -> BytesIO:
            captured.update(kwargs)
            return BytesIO(b"fake pptx bytes")

        export_svc._convert = fake_convert  # type: ignore[method-assign]

        await export_svc.export_material(
            material_id=str(single_slide_material_with_notes.id),
            db=test_db,
            fmt=ExportFormat.PPTX,
        )

        md = captured["markdown"]
        assert "::: notes" in md
        assert "Note for the only slide" in md

    @pytest.mark.asyncio
    async def test_pandoc_fenced_divs_have_required_blank_lines(
        self,
        export_svc: ExportService,
        test_db: Session,
        material_with_notes: WeeklyMaterial,
    ) -> None:
        """Pandoc requires blank lines around fenced divs to recognise them
        as block-level constructs. Without the surrounding newlines the
        ``::: notes`` syntax becomes inline text and the notes leak into
        the slide body instead of the speaker notes pane."""
        captured: dict[str, Any] = {}

        def fake_convert(**kwargs: Any) -> BytesIO:
            captured.update(kwargs)
            return BytesIO(b"")

        export_svc._convert = fake_convert  # type: ignore[method-assign]

        await export_svc.export_material(
            material_id=str(material_with_notes.id),
            db=test_db,
            fmt=ExportFormat.PPTX,
        )

        md = captured["markdown"]
        # Each fenced div must be preceded and followed by a blank line.
        # The renderer emits "\n\n::: notes\n...\n:::\n\n" so a substring
        # search for the bracketing newlines is enough.
        assert "\n\n::: notes\n" in md
        assert "\n:::\n\n" in md


# ---------------------------------------------------------------------------
# Other export formats — notes must be stripped
# ---------------------------------------------------------------------------


class TestNonPPTXExportsStripNotes:
    @pytest.mark.asyncio
    async def test_html_export_does_not_contain_notes(
        self,
        export_svc: ExportService,
        test_db: Session,
        material_with_notes: WeeklyMaterial,
    ) -> None:
        # HTML export does not invoke Pandoc — runs the full real path
        buf, _filename, _media = await export_svc.export_material(
            material_id=str(material_with_notes.id),
            db=test_db,
            fmt=ExportFormat.HTML,
        )
        html = buf.read().decode("utf-8")

        # Body content survives
        assert "Welcome to the lecture" in html
        assert "Slide 1: Introduction" in html

        # Notes do not — neither the text nor the wrapping markup
        assert "Open with the analogy" not in html
        assert "Spend 5 minutes here" not in html
        assert "Tie back to the unit learning outcomes" not in html
        assert "speaker-notes" not in html
        assert "::: notes" not in html

    @pytest.mark.asyncio
    async def test_docx_export_strips_notes(
        self,
        export_svc: ExportService,
        test_db: Session,
        material_with_notes: WeeklyMaterial,
    ) -> None:
        captured: dict[str, Any] = {}

        def fake_convert(**kwargs: Any) -> BytesIO:
            captured.update(kwargs)
            return BytesIO(b"fake docx bytes")

        export_svc._convert = fake_convert  # type: ignore[method-assign]

        await export_svc.export_material(
            material_id=str(material_with_notes.id),
            db=test_db,
            fmt=ExportFormat.DOCX,
        )

        md = captured["markdown"]
        # Body content survives
        assert "Welcome to the lecture" in md
        # Notes are stripped before reaching pandoc
        assert "Open with the analogy" not in md
        assert "::: notes" not in md
        assert "speaker-notes" not in md

    @pytest.mark.asyncio
    async def test_pdf_export_strips_notes(
        self,
        export_svc: ExportService,
        test_db: Session,
        material_with_notes: WeeklyMaterial,
    ) -> None:
        captured: dict[str, Any] = {}

        def fake_convert(**kwargs: Any) -> BytesIO:
            captured.update(kwargs)
            return BytesIO(b"fake pdf bytes")

        export_svc._convert = fake_convert  # type: ignore[method-assign]

        await export_svc.export_material(
            material_id=str(material_with_notes.id),
            db=test_db,
            fmt=ExportFormat.PDF,
        )

        md = captured["markdown"]
        assert "Welcome to the lecture" in md
        assert "Open with the analogy" not in md
        assert "::: notes" not in md
