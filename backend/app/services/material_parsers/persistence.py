"""
Shared persistence helpers for material parser results.

After a parser produces a ``MaterialParseResult``, the route layer must:

1. Persist extracted images to the material's git-backed image directory
2. Rewrite image src placeholders in content_json from bare filenames
   to canonical image-serving URLs

These two operations are identical for every entry point that creates a
WeeklyMaterial from a parser result — Mode A (single-file upload via
material_import route), Mode B (multi-file zip → existing unit, planned),
and Mode C (full course / LMS package → new unit via unified_import).
The helpers live in their own module so each entry point imports the
same code rather than copy-pasting it.

The chicken-and-egg sequencing is the same in all paths: the parser
emits image src as bare filenames (``slide-1-0.png``), the route
creates the WeeklyMaterial row to obtain a material_id, then this
module's helpers persist the images under the material's directory and
return a {filename: canonical_url} map that the caller threads back
into content_json before saving it.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import TYPE_CHECKING, Any

from app.api.routes.materials import (
    _images_dir_for_material,
    _sanitize_filename,
)
from app.services.git_content_service import get_git_service

if TYPE_CHECKING:
    from app.models.weekly_material import WeeklyMaterial
    from app.services.material_parsers.base import ExtractedImage


def persist_extracted_images(
    *,
    images: list[ExtractedImage],
    unit_id: str,
    material: WeeklyMaterial,
    user_email: str,
) -> dict[str, str]:
    """Write extracted images to git and return a {original_filename: url} map.

    The map lets the caller rewrite content_json image src values from
    the parser's placeholder filenames to canonical image-serving URLs.

    Filename collisions inside the same material's image directory are
    resolved with an 8-char SHA256 suffix (matching the convention used
    by ``upload_material_image`` in materials.py for consistency across
    upload paths).
    """
    if not images:
        return {}

    git = get_git_service()
    images_dir = _images_dir_for_material(material)
    existing = set(git.list_directory(unit_id, images_dir))
    rewrites: dict[str, str] = {}

    for image in images:
        original_name = image.filename
        safe_name = _sanitize_filename(original_name)

        if safe_name in existing:
            stem = Path(safe_name).stem
            ext = Path(safe_name).suffix
            content_hash = hashlib.sha256(image.data).hexdigest()[:8]
            safe_name = f"{stem}-{content_hash}{ext}"

        existing.add(safe_name)
        image_path = f"{images_dir}/{safe_name}"

        git.save_binary(
            unit_id=unit_id,
            path=image_path,
            data=image.data,
            user_email=user_email,
            message=f"Imported image {safe_name} for {material.title}",
        )

        url = (
            f"/api/materials/units/{unit_id}/materials/{material.id}"
            f"/images/{safe_name}"
        )
        rewrites[original_name] = url

    return rewrites


def rewrite_image_src(
    content_json: dict[str, Any], rewrites: dict[str, str]
) -> dict[str, Any]:
    """Return a copy of content_json with image src placeholders replaced.

    The parser emits image nodes with ``src`` set to a bare filename
    (e.g. ``"slide-1-0.png"``). After persistence we know the canonical
    URL and walk the tree replacing each match. The original content_json
    is not mutated.
    """
    if not rewrites:
        return content_json

    def _walk(node: dict[str, Any]) -> dict[str, Any]:
        new_node: dict[str, Any] = dict(node)
        if node.get("type") == "image":
            attrs = dict(node.get("attrs", {}))
            src = attrs.get("src", "")
            if src in rewrites:
                attrs["src"] = rewrites[src]
                new_node["attrs"] = attrs
        if "content" in node and isinstance(node["content"], list):
            new_node["content"] = [_walk(child) for child in node["content"]]
        return new_node

    return _walk(content_json)


__all__ = ["persist_extracted_images", "rewrite_image_src"]
