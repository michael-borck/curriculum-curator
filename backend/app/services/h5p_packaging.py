"""Shared H5P packaging — manifest + .h5p zip assembly.

The four H5P builders (question set, course presentation, branching scenario,
interactive video) each produce a variant-specific ``content.json``; the
``h5p.json`` manifest structure and the zip layout are identical across all of
them, so they live here once. (Candidate #6 in docs/architecture-deepening.md.)
"""

from __future__ import annotations

import json
import zipfile
from io import BytesIO
from typing import Any


def build_manifest(
    title: str,
    main_library: str,
    dependencies: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build the h5p.json manifest. Only main_library + dependencies vary by type."""
    return {
        "title": title,
        "mainLibrary": main_library,
        "language": "en",
        "embedTypes": ["div", "iframe"],
        "preloadedDependencies": dependencies,
    }


def pack_h5p(content_json: dict[str, Any], manifest: dict[str, Any]) -> BytesIO:
    """Assemble a .h5p ZIP (h5p.json + content/content.json) and rewind it."""
    buf = BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("h5p.json", json.dumps(manifest, indent=2))
        zf.writestr("content/content.json", json.dumps(content_json, indent=2))
    buf.seek(0)
    return buf
