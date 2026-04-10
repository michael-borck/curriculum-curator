"""
Slide splitter utility — splits TipTap content_json at slideBreak nodes.

Used by H5P Course Presentation and PPTX export to honour author slide breaks.

Speaker notes (``speakerNotes`` nodes) are kept with their slide regardless
of whether the author placed them before or after the slideBreak. After
splitting, any leading speakerNotes nodes in a segment are moved back to
the previous segment so notes always travel with the slide they describe.
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

    Speaker notes attachment: ``speakerNotes`` nodes are tied to the slide
    they describe, not the slide that follows them. If the author placed
    notes immediately after a slideBreak (a natural cursor position when
    the editor inserts the break), this function moves those leading notes
    back to the previous segment so they travel with the correct slide.
    Notes placed before the slideBreak (the canonical position) are already
    in the right segment and need no adjustment.
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

    # Reattach leading speakerNotes to the previous segment.
    # Walk forward so each segment is fixed up before its neighbour reads it.
    # Only reattach when the previous segment already has non-note content —
    # otherwise (e.g. a leading slideBreak) the notes would populate an
    # empty segment and create a phantom slide.
    for i in range(1, len(segments)):
        leading_notes: list[dict[str, Any]] = []
        while segments[i] and segments[i][0].get("type") == "speakerNotes":
            leading_notes.append(segments[i].pop(0))
        if leading_notes:
            prev_has_content = any(
                n.get("type") != "speakerNotes" for n in segments[i - 1]
            )
            if prev_has_content:
                segments[i - 1].extend(leading_notes)
            else:
                # Previous segment is empty or notes-only — put back
                segments[i] = leading_notes + segments[i]

    # Filter empty segments and wrap as docs
    return [
        {"type": "doc", "content": seg}
        for seg in segments
        if seg
    ]
