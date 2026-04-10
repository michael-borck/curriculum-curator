"""
Abstract base class and result schema for material parsers.

A material parser converts an uploaded file (PPTX, DOCX, PDF, HTML, MD, ...)
into a structured ``MaterialParseResult`` containing TipTap content_json,
extracted images, and metadata. Parsers are pure transformation layers —
they do not write to the database or filesystem. The route layer takes the
result, persists images via the git content service, rewrites image src
references, and creates the WeeklyMaterial row.

See docs/structured-import-plan.md for the architecture.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, ClassVar

from pydantic import BaseModel, ConfigDict, Field


class ExtractedImage(BaseModel):
    """An image extracted from a source document.

    The parser populates ``filename`` (a sanitisation-friendly name) and
    ``data`` (the raw image bytes). The route layer is responsible for
    persisting the bytes to git and rewriting matching content_json image
    src references to canonical URLs.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    filename: str
    data: bytes
    mime_type: str | None = None


class MaterialParseResult(BaseModel):
    """The structured result of parsing a single source file.

    Pure data — no database or filesystem side effects. The parser
    populates this; the apply route persists it.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    title: str | None = None
    """Best-effort title extracted from the document. The route may
    override with a user-supplied title at apply time."""

    content_json: dict[str, Any]
    """ProseMirror/TipTap document. Image nodes use the bare filename
    as ``src`` (e.g. ``"slide-1-0.png"``); the apply route rewrites
    these to canonical image-serving URLs after persistence."""

    images: list[ExtractedImage] = Field(default_factory=list)
    """Images extracted from the source. Filenames in this list match
    the placeholder ``src`` values used in ``content_json``."""

    warnings: list[str] = Field(default_factory=list)
    """Things the user should know about the import (per ADR-061
    transparent reporting). Examples: dropped equations, deeply
    nested bullets that were flattened, decorative shapes ignored."""

    parser_used: str
    """The ``name`` of the parser that produced this result."""

    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    """Parser self-reported confidence. Informational only — no
    automatic accept/reject threshold."""


class MaterialParser(ABC):
    """Base class for all material parsers.

    Subclasses set the class-level metadata fields and implement
    ``parse``. The dispatcher discovers them via the registry in
    ``material_parsers/__init__.py``.
    """

    name: ClassVar[str] = "base"
    """Stable parser identifier (e.g. ``pptx_structural``). Used in
    the registry, the API, and stored as ``parser_used`` on results."""

    display_name: ClassVar[str] = "Base Parser"
    """Human-readable label for the parser picker UI."""

    description: ClassVar[str] = ""
    """Short description shown in the parser picker."""

    supported_formats: ClassVar[list[str]] = []
    """File extensions (without leading dot, lowercase) this parser
    handles. Used by ``list_parsers(format=...)`` filtering."""

    requires_ai: ClassVar[bool] = False
    """If True, the parser uses an LLM and is gated by ADR-032
    AI assistance level. The route layer hides parsers with
    ``requires_ai=True`` from users whose level disables AI."""

    @abstractmethod
    async def parse(
        self,
        file_content: bytes,
        filename: str,
        *,
        user_context: dict[str, object] | None = None,
    ) -> MaterialParseResult:
        """Parse a document and return a structured result.

        Args:
            file_content: Raw bytes of the uploaded file.
            filename: Original filename (used for title fallback,
                image naming hints, and warning messages).
            user_context: Optional metadata about the requesting user
                (sector, preferences, etc.) for parsers that need it.

        Returns:
            A ``MaterialParseResult`` ready for the apply route to
            persist.
        """
        ...
