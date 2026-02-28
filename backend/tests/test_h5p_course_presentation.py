"""
Tests for the H5P Course Presentation builder.

Covers:
- ZIP has h5p.json + content/content.json
- Main library is H5P.CoursePresentation
- Slide count matches segment count
- Slides contain rendered HTML in AdvancedText elements
- Headings extracted as keywords; no heading → empty keywords
- Dependencies include AdvancedText
"""

from __future__ import annotations

import json
import zipfile
from io import BytesIO
from typing import Any

from app.services.h5p_course_presentation import (
    H5PCoursePresentationBuilder,
    h5p_course_presentation_builder,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _para(text: str) -> dict[str, Any]:
    return {
        "type": "paragraph",
        "content": [{"type": "text", "text": text}],
    }


def _heading(text: str, level: int = 1) -> dict[str, Any]:
    return {
        "type": "heading",
        "attrs": {"level": level},
        "content": [{"type": "text", "text": text}],
    }


def _slide_break() -> dict[str, Any]:
    return {"type": "slideBreak"}


def _doc(*nodes: dict[str, Any]) -> dict[str, Any]:
    return {"type": "doc", "content": list(nodes)}


def _unpack_h5p(buf: BytesIO) -> tuple[dict[str, Any], dict[str, Any]]:
    """Unpack h5p.json and content/content.json from a .h5p ZIP."""
    buf.seek(0)
    with zipfile.ZipFile(buf, "r") as zf:
        h5p_json = json.loads(zf.read("h5p.json"))
        content_json = json.loads(zf.read("content/content.json"))
    return h5p_json, content_json


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestPackageStructure:
    def test_zip_contains_required_files(self) -> None:
        doc = _doc(_para("Hello"), _slide_break(), _para("World"))
        buf = h5p_course_presentation_builder.build(doc, "Test Slides")
        buf.seek(0)
        with zipfile.ZipFile(buf, "r") as zf:
            names = zf.namelist()
        assert "h5p.json" in names
        assert "content/content.json" in names

    def test_h5p_json_main_library(self) -> None:
        doc = _doc(_para("Hello"))
        buf = h5p_course_presentation_builder.build(doc, "My Slides")
        h5p_json, _ = _unpack_h5p(buf)

        assert h5p_json["mainLibrary"] == "H5P.CoursePresentation"
        assert h5p_json["title"] == "My Slides"
        assert h5p_json["language"] == "en"

    def test_dependencies_include_advanced_text(self) -> None:
        doc = _doc(_para("Hello"))
        buf = h5p_course_presentation_builder.build(doc, "Test")
        h5p_json, _ = _unpack_h5p(buf)

        deps = h5p_json["preloadedDependencies"]
        machine_names = [d["machineName"] for d in deps]
        assert "H5P.CoursePresentation" in machine_names
        assert "H5P.AdvancedText" in machine_names


class TestSlideCount:
    def test_no_breaks_one_slide(self) -> None:
        doc = _doc(_para("All in one"))
        buf = h5p_course_presentation_builder.build(doc, "Test")
        _, content = _unpack_h5p(buf)

        slides = content["presentation"]["slides"]
        assert len(slides) == 1

    def test_one_break_two_slides(self) -> None:
        doc = _doc(_para("Slide 1"), _slide_break(), _para("Slide 2"))
        buf = h5p_course_presentation_builder.build(doc, "Test")
        _, content = _unpack_h5p(buf)

        slides = content["presentation"]["slides"]
        assert len(slides) == 2

    def test_three_breaks_four_slides(self) -> None:
        doc = _doc(
            _para("A"),
            _slide_break(),
            _para("B"),
            _slide_break(),
            _para("C"),
            _slide_break(),
            _para("D"),
        )
        buf = h5p_course_presentation_builder.build(doc, "Test")
        _, content = _unpack_h5p(buf)

        slides = content["presentation"]["slides"]
        assert len(slides) == 4


class TestSlideContent:
    def test_slides_contain_html(self) -> None:
        doc = _doc(_para("Hello world"), _slide_break(), _para("Second slide"))
        buf = h5p_course_presentation_builder.build(doc, "Test")
        _, content = _unpack_h5p(buf)

        slides = content["presentation"]["slides"]
        # First slide should contain the paragraph HTML
        text_html = slides[0]["elements"][0]["action"]["params"]["text"]
        assert "<p>Hello world</p>" in text_html

        text_html_2 = slides[1]["elements"][0]["action"]["params"]["text"]
        assert "<p>Second slide</p>" in text_html_2

    def test_advanced_text_library(self) -> None:
        doc = _doc(_para("Test"))
        buf = h5p_course_presentation_builder.build(doc, "Test")
        _, content = _unpack_h5p(buf)

        slide = content["presentation"]["slides"][0]
        lib = slide["elements"][0]["action"]["library"]
        assert lib == "H5P.AdvancedText 1.1"

    def test_element_full_width(self) -> None:
        doc = _doc(_para("Test"))
        buf = h5p_course_presentation_builder.build(doc, "Test")
        _, content = _unpack_h5p(buf)

        element = content["presentation"]["slides"][0]["elements"][0]
        assert element["width"] == 100
        assert element["height"] == 100


class TestKeywords:
    def test_heading_extracted_as_keyword(self) -> None:
        doc = _doc(
            _heading("Introduction"),
            _para("Content here"),
            _slide_break(),
            _heading("Methods"),
            _para("More content"),
        )
        buf = h5p_course_presentation_builder.build(doc, "Test")
        _, content = _unpack_h5p(buf)

        slides = content["presentation"]["slides"]
        assert slides[0]["keywords"][0]["main"] == "Introduction"
        assert slides[1]["keywords"][0]["main"] == "Methods"

    def test_no_heading_empty_keywords(self) -> None:
        doc = _doc(_para("No heading here"))
        buf = h5p_course_presentation_builder.build(doc, "Test")
        _, content = _unpack_h5p(buf)

        slide = content["presentation"]["slides"][0]
        assert slide["keywords"] == []

    def test_h2_heading_also_extracted(self) -> None:
        doc = _doc(
            _heading("Sub heading", level=2),
            _para("Content"),
        )
        buf = h5p_course_presentation_builder.build(doc, "Test")
        _, content = _unpack_h5p(buf)

        slide = content["presentation"]["slides"][0]
        assert slide["keywords"][0]["main"] == "Sub heading"


class TestSingleton:
    def test_singleton_is_instance(self) -> None:
        assert isinstance(h5p_course_presentation_builder, H5PCoursePresentationBuilder)
