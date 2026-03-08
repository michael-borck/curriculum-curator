"""
Outline parser registry — discover and instantiate parsers by ID.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.services.outline_parsers.base import OutlineParser

# Module-level cache
_registry_cache: dict[str, type[OutlineParser]] = {}


def _build_registry() -> dict[str, type[OutlineParser]]:
    from app.services.outline_parsers.curtin_parser import CurtinOutlineParser  # noqa: PLC0415, I001
    from app.services.outline_parsers.generic_parser import GenericOutlineParser  # noqa: PLC0415

    return {
        GenericOutlineParser.name: GenericOutlineParser,
        CurtinOutlineParser.name: CurtinOutlineParser,
    }


def _registry() -> dict[str, type[OutlineParser]]:
    if not _registry_cache:
        _registry_cache.update(_build_registry())
    return _registry_cache


def get_parser(parser_id: str) -> OutlineParser:
    """Return an instance of the requested parser (raises KeyError if unknown)."""
    cls = _registry().get(parser_id)
    if cls is None:
        raise KeyError(f"Unknown parser: {parser_id}")
    return cls()


def list_parsers() -> list[dict[str, object]]:
    """Return metadata for all registered parsers."""
    return [
        {
            "id": cls.name,
            "displayName": cls.display_name,
            "description": cls.description,
            "supportedFormats": cls.supported_formats,
        }
        for cls in _registry().values()
    ]


__all__ = ["get_parser", "list_parsers"]
