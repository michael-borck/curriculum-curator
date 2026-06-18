"""Interactive HTML export adapter (story 19B.1).

Branching cards in a material → one self-contained interactive HTML file,
behind the export seam. Sibling of H5pBranchingExporter, but emits a
standalone web page rather than an .h5p package.
"""

from __future__ import annotations

from io import BytesIO
from typing import TYPE_CHECKING, Any

from app.services.export._gather import load_material
from app.services.export.base import (
    BaseExporter,
    ExportContentError,
    ExportOptions,
    ExportResult,
    ExportScope,
)
from app.services.interactive_html_service import interactive_html_builder
from app.services.unit_export_data import extract_branching_cards, slugify

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


class InteractiveHtmlExporter(BaseExporter):
    """Branching cards in a material → standalone interactive HTML page."""

    supported_scopes = frozenset({ExportScope.MATERIAL})

    async def export_material(
        self, material_id: str, db: Session, options: ExportOptions
    ) -> ExportResult:
        _ = options
        material = load_material(material_id, db)
        cards: list[dict[str, Any]] = (
            extract_branching_cards(material.content_json)
            if material.content_json
            else []
        )
        if not cards:
            raise ExportContentError("No branching cards found in this material")
        html = interactive_html_builder.build(cards, str(material.title))
        buf = BytesIO(html.encode("utf-8"))
        filename = f"{slugify(str(material.title))}_interactive.html"
        return ExportResult(buf=buf, filename=filename, media_type="text/html")
