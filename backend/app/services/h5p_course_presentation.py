"""
H5P Course Presentation package builder.

Generates .h5p (ZIP) archives containing a Course Presentation from
slide-break-delimited content. Each slide contains a single H5P.AdvancedText
element with the rendered HTML for that segment.
"""

import json
import uuid
import zipfile
from io import BytesIO
from typing import Any

from app.services.content_json_renderer import render_content_json
from app.services.slide_splitter import split_at_slide_breaks

# H5P library version dicts
_COURSE_PRESENTATION_LIB: dict[str, Any] = {
    "machineName": "H5P.CoursePresentation",
    "majorVersion": 1,
    "minorVersion": 22,
}
_ADVANCED_TEXT_LIB: dict[str, Any] = {
    "machineName": "H5P.AdvancedText",
    "majorVersion": 1,
    "minorVersion": 1,
}


def _extract_first_heading(segment: dict[str, Any]) -> str:
    """Extract text from the first heading node in a segment, or empty string."""
    for node in segment.get("content", []):
        if node.get("type") == "heading":
            return _extract_text(node)
    return ""


def _extract_text(node: dict[str, Any]) -> str:
    """Recursively extract plain text from a ProseMirror node."""
    if node.get("type") == "text":
        return node.get("text", "")
    return "".join(_extract_text(child) for child in node.get("content", []))


class H5PCoursePresentationBuilder:
    """Builds an H5P Course Presentation package (.h5p ZIP) from content_json."""

    def build(self, content_json: dict[str, Any], title: str) -> BytesIO:
        """Create .h5p ZIP with content.json + h5p.json.

        Args:
            content_json: TipTap document JSON with slideBreak nodes.
            title: Title for the presentation.

        Returns:
            BytesIO containing the .h5p ZIP archive.
        """
        segments = split_at_slide_breaks(content_json)

        slides: list[dict[str, Any]] = []
        for seg in segments:
            html = render_content_json(seg)
            keyword = _extract_first_heading(seg)

            slide = self._build_slide(html, keyword)
            slides.append(slide)

        content = self._build_content_json(slides)
        h5p_json = self._build_h5p_json(title)

        buf = BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("h5p.json", json.dumps(h5p_json, indent=2))
            zf.writestr("content/content.json", json.dumps(content, indent=2))
        buf.seek(0)
        return buf

    def _build_slide(self, html: str, keyword: str) -> dict[str, Any]:
        """Build a single slide with an AdvancedText element."""
        lib_string = (
            f"{_ADVANCED_TEXT_LIB['machineName']} "
            f"{_ADVANCED_TEXT_LIB['majorVersion']}.{_ADVANCED_TEXT_LIB['minorVersion']}"
        )

        element: dict[str, Any] = {
            "x": 0,
            "y": 0,
            "width": 100,
            "height": 100,
            "action": {
                "library": lib_string,
                "params": {"text": html},
                "subContentId": str(uuid.uuid4()),
                "metadata": {"contentType": "Text"},
            },
        }

        return {
            "elements": [element],
            "keywords": [{"main": keyword}] if keyword else [],
        }

    def _build_content_json(self, slides: list[dict[str, Any]]) -> dict[str, Any]:
        """Build the content/content.json structure."""
        return {
            "presentation": {
                "slides": slides,
                "keywordListEnabled": True,
                "globalBackgroundSelector": {},
                "keywordListAlwaysShow": False,
                "keywordListAutoHide": False,
                "keywordListOpacity": 90,
            },
            "override": {
                "activeSurface": False,
                "hideSummarySlide": False,
                "summarySlideSolutionButton": True,
                "summarySlideRetryButton": False,
            },
            "l10n": {
                "slide": "Slide",
                "yourScore": "Your Score",
                "maxScore": "Max Score",
                "goodScore": "Congratulations! You got @percent correct!",
                "okScore": "Nice effort! You got @percent correct!",
                "badScore": "You got @percent correct.",
                "total": "Total",
                "showSolutions": "Show solutions",
                "retry": "Retry",
                "exportAnswers": "Export text",
                "hideKeywords": "Hide sidebar navigation",
                "showKeywords": "Show sidebar navigation",
            },
        }

    def _build_h5p_json(self, title: str) -> dict[str, Any]:
        """Build the h5p.json manifest."""
        return {
            "title": title,
            "mainLibrary": "H5P.CoursePresentation",
            "language": "en",
            "embedTypes": ["div", "iframe"],
            "preloadedDependencies": [
                _COURSE_PRESENTATION_LIB,
                _ADVANCED_TEXT_LIB,
            ],
        }


# Module-level singleton
h5p_course_presentation_builder = H5PCoursePresentationBuilder()
