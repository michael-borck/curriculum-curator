"""
Slide splitter utility — splits TipTap content_json at slideBreak nodes.

Used by H5P Course Presentation and PPTX export to honour author slide breaks.
"""

from typing import Any


def has_slide_breaks(content_json: dict[str, Any] | None) -> bool:
    """Return True if content_json contains at least one slideBreak node."""
    if not content_json:
        return False
    top_content = content_json.get("content")
    if not isinstance(top_content, list):
        return False
    return any(node.get("type") == "slideBreak" for node in top_content)


def split_at_slide_breaks(content_json: dict[str, Any]) -> list[dict[str, Any]]:
    """Split content_json into segments at slideBreak boundaries.

    Returns a list of ``{"type": "doc", "content": [...]}`` fragments.
    Empty leading segments (e.g. a slideBreak at the very start) are filtered.
    If there are no slide breaks, the entire document is returned as a single
    segment.
    """
    top_content = content_json.get("content")
    if not isinstance(top_content, list):
        return [{"type": "doc", "content": []}]

    segments: list[list[dict[str, Any]]] = []
    current: list[dict[str, Any]] = []

    for node in top_content:
        if node.get("type") == "slideBreak":
            segments.append(current)
            current = []
        else:
            current.append(node)

    # Append the trailing segment
    segments.append(current)

    # Filter empty segments and wrap as docs
    return [
        {"type": "doc", "content": seg}
        for seg in segments
        if seg
    ]
