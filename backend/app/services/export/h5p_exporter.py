"""H5P export adapters — wrap the four H5P builders behind the export seam.

One adapter per H5P variant. (Candidate #6 will collapse the underlying four
builder modules into one deep module; these adapters are the seam in front.)
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.repositories import unit_repo
from app.services.export._gather import gather_unit_quiz_questions, load_material
from app.services.export.base import (
    BaseExporter,
    ExportContentError,
    ExportOptions,
    ExportResult,
    ExportScope,
    ExportUnsupportedError,
)
from app.services.h5p_branching_service import h5p_branching_builder
from app.services.h5p_course_presentation import h5p_course_presentation_builder
from app.services.h5p_interactive_video_service import h5p_interactive_video_builder
from app.services.h5p_service import h5p_builder
from app.services.slide_splitter import has_slide_breaks
from app.services.unit_export_data import (
    extract_branching_cards,
    extract_quiz_nodes,
    extract_video_embed,
    extract_video_interactions,
    slugify,
)

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


class H5pQuestionSetExporter(BaseExporter):
    """Quiz questions → H5P Question Set (.h5p), per unit or material."""

    supported_scopes = frozenset({ExportScope.UNIT, ExportScope.MATERIAL})

    async def export_unit(
        self, unit_id: str, db: Session, options: ExportOptions
    ) -> ExportResult:
        unit = unit_repo.get_unit_by_id(db, unit_id)
        if unit is None:
            raise ExportContentError("Unit not found")
        questions = gather_unit_quiz_questions(unit_id, db)
        if not questions:
            raise ExportContentError("No quiz questions found in this unit")
        buf = h5p_builder.build(questions, f"{unit.code} - Interactive Quiz")
        filename = f"{unit.code}_{slugify(str(unit.title))}_quiz.h5p"
        return ExportResult(buf=buf, filename=filename, media_type="application/zip")

    async def export_material(
        self, material_id: str, db: Session, options: ExportOptions
    ) -> ExportResult:
        material = load_material(material_id, db)
        questions = (
            extract_quiz_nodes(material.content_json) if material.content_json else []
        )
        if not questions:
            raise ExportContentError("No quiz questions found in this material")
        buf = h5p_builder.build(questions, f"{material.title} - Interactive Quiz")
        filename = f"{slugify(str(material.title))}_quiz.h5p"
        return ExportResult(buf=buf, filename=filename, media_type="application/zip")


class H5pCoursePresentationExporter(BaseExporter):
    """Slide-broken material → H5P Course Presentation (.h5p)."""

    supported_scopes = frozenset({ExportScope.MATERIAL})

    async def export_material(
        self, material_id: str, db: Session, options: ExportOptions
    ) -> ExportResult:
        material = load_material(material_id, db)
        if not material.content_json or not has_slide_breaks(material.content_json):
            raise ExportContentError("No slide breaks found in this material")
        buf = h5p_course_presentation_builder.build(
            material.content_json, f"{material.title} - Slides"
        )
        filename = f"{slugify(str(material.title))}_slides.h5p"
        return ExportResult(buf=buf, filename=filename, media_type="application/zip")


class H5pBranchingExporter(BaseExporter):
    """Branching cards in a material → H5P Branching Scenario (.h5p)."""

    supported_scopes = frozenset({ExportScope.MATERIAL})

    async def export_material(
        self, material_id: str, db: Session, options: ExportOptions
    ) -> ExportResult:
        material = load_material(material_id, db)
        cards: list[dict[str, Any]] = (
            extract_branching_cards(material.content_json)
            if material.content_json
            else []
        )
        if not cards:
            raise ExportContentError("No branching cards found in this material")
        buf = h5p_branching_builder.build(
            cards, f"{material.title} - Branching Scenario"
        )
        filename = f"{slugify(str(material.title))}_branching.h5p"
        return ExportResult(buf=buf, filename=filename, media_type="application/zip")


class H5pInteractiveVideoExporter(BaseExporter):
    """Interactive video material → H5P Interactive Video (.h5p)."""

    supported_scopes = frozenset({ExportScope.MATERIAL})

    async def export_material(
        self, material_id: str, db: Session, options: ExportOptions
    ) -> ExportResult:
        material = load_material(material_id, db)
        if not material.content_json:
            raise ExportContentError("No content found in this material")
        embed = extract_video_embed(material.content_json)
        interactions = extract_video_interactions(material.content_json)
        if not embed:
            raise ExportContentError("No video embed found in this material")
        if not interactions:
            raise ExportContentError("No video interactions found in this material")
        try:
            buf = h5p_interactive_video_builder.build(
                embed, interactions, str(material.title)
            )
        except ValueError as exc:
            raise ExportUnsupportedError(str(exc)) from exc
        filename = f"{slugify(str(material.title))}_interactive_video.h5p"
        return ExportResult(buf=buf, filename=filename, media_type="application/zip")
