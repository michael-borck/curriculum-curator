"""
Material parser registry — discover and instantiate parsers by id, format,
or content auto-detection.

Mirrors the outline_parsers/ pattern from ADR-063. The two registries are
intentionally independent: outline parsers produce ``OutlineParseResult``
(unit-level metadata) and material parsers produce ``MaterialParseResult``
(per-material content_json + images).

See docs/structured-import-plan.md for the architecture and ADR-065
(forthcoming) for the formal decision record.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.services.material_parsers.base import MaterialParser

# Module-level cache so parser classes are only imported once per process.
_registry_cache: dict[str, type[MaterialParser]] = {}

# Per-format default parser id. The dispatcher consults this when no
# specialised parser is auto-detected for the file. Adding a format here
# requires a registered parser with that id (or the lookup will raise).
DEFAULT_PARSER_BY_FORMAT: dict[str, str] = {
    "pptx": "pptx_structural",
}


def _build_registry() -> dict[str, type[MaterialParser]]:
    # Imports inside the function avoid circular imports during package init
    # and keep the registry lazy — adding a parser only requires editing
    # this function and DEFAULT_PARSER_BY_FORMAT above.
    from app.services.material_parsers.pptx_structural import (  # noqa: PLC0415
        PptxStructuralParser,
    )

    return {
        PptxStructuralParser.name: PptxStructuralParser,
    }


def _registry() -> dict[str, type[MaterialParser]]:
    if not _registry_cache:
        _registry_cache.update(_build_registry())
    return _registry_cache


def get_parser(parser_id: str) -> MaterialParser:
    """Return an instance of the requested parser.

    Raises:
        KeyError: if no parser is registered with that id.
    """
    cls = _registry().get(parser_id)
    if cls is None:
        msg = f"Unknown material parser: {parser_id}"
        raise KeyError(msg)
    return cls()


def get_default_for_format(file_extension: str) -> MaterialParser:
    """Return the registered default parser for a file extension.

    Extension is normalised (lowercased, leading dot stripped) before lookup.

    Raises:
        KeyError: if no default is registered for the extension.
    """
    ext = file_extension.lower().lstrip(".")
    parser_id = DEFAULT_PARSER_BY_FORMAT.get(ext)
    if parser_id is None:
        msg = f"No default material parser registered for format: {ext}"
        raise KeyError(msg)
    return get_parser(parser_id)


def list_parsers(file_format: str | None = None) -> list[dict[str, object]]:
    """Return metadata for registered material parsers.

    If ``file_format`` is given, restrict the result to parsers that
    declare support for it; each entry's ``isDefault`` flag indicates
    whether it's the default parser for that specific format.

    Without a format filter, ``isDefault`` indicates whether the parser
    is the registered default for *any* format it supports — useful for
    "show me all parsers" UIs that want to mark recommended choices.
    """
    ext = file_format.lower().lstrip(".") if file_format else None
    default_for_filter = DEFAULT_PARSER_BY_FORMAT.get(ext) if ext else None
    all_default_ids = set(DEFAULT_PARSER_BY_FORMAT.values())

    result: list[dict[str, object]] = []
    for cls in _registry().values():
        if ext is not None and ext not in cls.supported_formats:
            continue
        if ext is not None:
            is_default = cls.name == default_for_filter
        else:
            is_default = cls.name in all_default_ids
        result.append(
            {
                "id": cls.name,
                "displayName": cls.display_name,
                "description": cls.description,
                "supportedFormats": cls.supported_formats,
                "requiresAi": cls.requires_ai,
                "isDefault": is_default,
            }
        )
    return result


def autodetect(file_content: bytes, filename: str) -> str | None:
    """Inspect file content for a confident dialect signal.

    Returns the parser id to dispatch to, or None when no specialised
    parser matches and the caller should fall back to the format default.

    v1: no specialisations registered, always returns None. The dispatcher
    is wired in early so adding format-dialect parsers (Marp, reveal.js,
    Quarto, etc.) in later phases doesn't require touching the route layer.
    Per the structured-import plan, only YAML front-matter style signals
    qualify as confident in v1 - comment-based directives are too easy
    to false-positive.
    """
    # Args reserved for future dialect detection (Marp/reveal.js/Quarto)
    _ = (file_content, filename)
    return None


__all__ = [
    "autodetect",
    "get_default_for_format",
    "get_parser",
    "list_parsers",
]
