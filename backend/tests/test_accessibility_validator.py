"""Tests for the AccessibilityValidator plugin.

Covers both markdown and HTML input, plus media checks.
"""

import pytest

from app.plugins.accessibility_validator import AccessibilityValidator


@pytest.fixture
def validator() -> AccessibilityValidator:
    return AccessibilityValidator()


# ── Image checks ─────────────────────────────────────────────────────


class TestImageChecks:
    """WCAG 1.1.1 — Non-text Content."""

    @pytest.mark.asyncio
    async def test_md_image_missing_alt(
        self, validator: AccessibilityValidator
    ) -> None:
        result = await validator.validate("![](photo.jpg)", {})
        assert not result.success
        assert any("empty alt text" in i for i in result.data["issues"])

    @pytest.mark.asyncio
    async def test_md_image_short_alt(self, validator: AccessibilityValidator) -> None:
        result = await validator.validate("![hi](photo.jpg)", {})
        assert any("insufficient alt text" in i for i in result.data["issues"])

    @pytest.mark.asyncio
    async def test_md_image_generic_alt(
        self, validator: AccessibilityValidator
    ) -> None:
        result = await validator.validate("![image](photo.jpg)", {})
        assert any("generic alt text" in i for i in result.data["issues"])

    @pytest.mark.asyncio
    async def test_md_image_good_alt(self, validator: AccessibilityValidator) -> None:
        result = await validator.validate(
            "# Title\n\n![A student working on a laptop](photo.jpg)", {}
        )
        assert not any("alt text" in i.lower() for i in result.data["issues"])

    @pytest.mark.asyncio
    async def test_html_image_missing_alt_attr(
        self, validator: AccessibilityValidator
    ) -> None:
        result = await validator.validate('<p><img src="photo.jpg"></p>', {})
        assert any("missing the alt attribute" in i for i in result.data["issues"])

    @pytest.mark.asyncio
    async def test_html_image_empty_alt(
        self, validator: AccessibilityValidator
    ) -> None:
        result = await validator.validate('<p><img src="photo.jpg" alt=""></p>', {})
        assert any("empty alt text" in i for i in result.data["issues"])

    @pytest.mark.asyncio
    async def test_html_image_generic_alt(
        self, validator: AccessibilityValidator
    ) -> None:
        result = await validator.validate(
            '<p><img src="photo.jpg" alt="picture"></p>', {}
        )
        assert any("generic alt text" in i for i in result.data["issues"])

    @pytest.mark.asyncio
    async def test_html_image_good_alt(self, validator: AccessibilityValidator) -> None:
        result = await validator.validate(
            '<h1>Title</h1><p><img src="photo.jpg" alt="A student working on a laptop"></p>',
            {},
        )
        assert not any("alt" in i.lower() for i in result.data["issues"])


# ── Heading checks ───────────────────────────────────────────────────


class TestHeadingChecks:
    """WCAG 1.3.1 — Info and Relationships (heading structure)."""

    @pytest.mark.asyncio
    async def test_md_no_headings(self, validator: AccessibilityValidator) -> None:
        result = await validator.validate("Just a paragraph of text.", {})
        assert any("No headings" in i for i in result.data["issues"])

    @pytest.mark.asyncio
    async def test_md_skipped_levels(self, validator: AccessibilityValidator) -> None:
        result = await validator.validate("# Title\n\n### Skipped H2", {})
        assert any("Heading level skip" in i for i in result.data["issues"])

    @pytest.mark.asyncio
    async def test_md_multiple_h1(self, validator: AccessibilityValidator) -> None:
        result = await validator.validate("# First\n\n# Second", {})
        assert any("Multiple H1" in i for i in result.data["issues"])

    @pytest.mark.asyncio
    async def test_md_all_caps_heading(self, validator: AccessibilityValidator) -> None:
        result = await validator.validate("# IMPORTANT HEADING", {})
        assert any("all caps" in i for i in result.data["issues"])

    @pytest.mark.asyncio
    async def test_html_no_headings(self, validator: AccessibilityValidator) -> None:
        result = await validator.validate("<p>Just a paragraph of text.</p>", {})
        assert any("No headings" in i for i in result.data["issues"])

    @pytest.mark.asyncio
    async def test_html_skipped_levels(self, validator: AccessibilityValidator) -> None:
        result = await validator.validate("<h1>Title</h1><h3>Skipped</h3>", {})
        assert any("Heading level skip" in i for i in result.data["issues"])

    @pytest.mark.asyncio
    async def test_html_good_structure(self, validator: AccessibilityValidator) -> None:
        content = "<h1>Title</h1><h2>Section</h2><h3>Subsection</h3>"
        result = await validator.validate(content, {})
        heading_issues = [i for i in result.data["issues"] if "eading" in i]
        assert len(heading_issues) == 0

    @pytest.mark.asyncio
    async def test_html_all_caps_heading(
        self, validator: AccessibilityValidator
    ) -> None:
        result = await validator.validate("<h1>IMPORTANT HEADING</h1>", {})
        assert any("all caps" in i for i in result.data["issues"])


# ── Link checks ──────────────────────────────────────────────────────


class TestLinkChecks:
    """WCAG 2.4.4 — Link Purpose."""

    @pytest.mark.asyncio
    async def test_md_empty_link_text(self, validator: AccessibilityValidator) -> None:
        result = await validator.validate("# Title\n\n[](https://example.com)", {})
        assert any("has no text" in i for i in result.data["issues"])

    @pytest.mark.asyncio
    async def test_md_generic_link_text(
        self, validator: AccessibilityValidator
    ) -> None:
        result = await validator.validate(
            "# Title\n\n[click here](https://example.com)", {}
        )
        assert any("non-descriptive" in i for i in result.data["issues"])

    @pytest.mark.asyncio
    async def test_html_empty_link_text(
        self, validator: AccessibilityValidator
    ) -> None:
        result = await validator.validate(
            '<h1>Title</h1><a href="https://example.com"></a>', {}
        )
        assert any("has no text" in i for i in result.data["issues"])

    @pytest.mark.asyncio
    async def test_html_generic_link_text(
        self, validator: AccessibilityValidator
    ) -> None:
        result = await validator.validate(
            '<h1>Title</h1><a href="https://example.com">click here</a>', {}
        )
        assert any("non-descriptive" in i for i in result.data["issues"])

    @pytest.mark.asyncio
    async def test_html_good_link_text(self, validator: AccessibilityValidator) -> None:
        result = await validator.validate(
            '<h1>Title</h1><a href="https://example.com">Visit the course portal</a>',
            {},
        )
        assert not any("link" in i.lower() for i in result.data["issues"])


# ── Table checks ─────────────────────────────────────────────────────


class TestTableChecks:
    """WCAG 1.3.1 — Tables need headers."""

    @pytest.mark.asyncio
    async def test_html_table_no_headers(
        self, validator: AccessibilityValidator
    ) -> None:
        table = "<h1>Title</h1><table><tr><td>A</td><td>B</td></tr></table>"
        result = await validator.validate(table, {})
        assert any("missing header" in i for i in result.data["issues"])

    @pytest.mark.asyncio
    async def test_html_table_with_headers(
        self, validator: AccessibilityValidator
    ) -> None:
        table = "<h1>Title</h1><table><thead><tr><th>Name</th><th>Score</th></tr></thead><tbody><tr><td>Alice</td><td>95</td></tr></tbody></table>"
        result = await validator.validate(table, {})
        assert not any("header" in i.lower() for i in result.data["issues"])


# ── Media checks ─────────────────────────────────────────────────────


class TestMediaChecks:
    """WCAG 1.2.1 — Audio/Video alternatives."""

    @pytest.mark.asyncio
    async def test_video_without_track(self, validator: AccessibilityValidator) -> None:
        content = '<h1>Lecture</h1><video src="lecture.mp4" controls></video>'
        result = await validator.validate(content, {})
        assert any("captions" in i for i in result.data["issues"])

    @pytest.mark.asyncio
    async def test_self_closing_video(self, validator: AccessibilityValidator) -> None:
        # TipTap renders void video elements
        content = '<h1>Lecture</h1><video src="lecture.mp4" controls />'
        result = await validator.validate(content, {})
        assert any("captions" in i or "transcript" in i for i in result.data["issues"])

    @pytest.mark.asyncio
    async def test_video_with_track(self, validator: AccessibilityValidator) -> None:
        content = (
            "<h1>Lecture</h1>"
            '<video src="lecture.mp4" controls>'
            '<track kind="captions" src="captions.vtt">'
            "</video>"
        )
        result = await validator.validate(content, {})
        assert not any("captions" in i for i in result.data["issues"])

    @pytest.mark.asyncio
    async def test_youtube_no_title(self, validator: AccessibilityValidator) -> None:
        content = (
            "<h1>Lecture</h1>"
            "<div data-youtube-video>"
            '<iframe src="https://www.youtube-nocookie.com/embed/abc123" '
            'width="640" height="360"></iframe>'
            "</div>"
        )
        result = await validator.validate(content, {})
        assert any("title attribute" in i for i in result.data["issues"])

    @pytest.mark.asyncio
    async def test_youtube_with_title(self, validator: AccessibilityValidator) -> None:
        content = (
            "<h1>Lecture</h1>"
            "<div data-youtube-video>"
            '<iframe src="https://www.youtube-nocookie.com/embed/abc123" '
            'title="Introduction to Python" width="640" height="360"></iframe>'
            "</div>"
        )
        result = await validator.validate(content, {})
        assert not any("title attribute" in i for i in result.data["issues"])

    @pytest.mark.asyncio
    async def test_mermaid_no_alternative(
        self, validator: AccessibilityValidator
    ) -> None:
        content = '<h1>Architecture</h1><pre class="mermaid">graph TD\n  A --> B</pre>'
        result = await validator.validate(content, {})
        assert any("Mermaid" in i for i in result.data["issues"])

    @pytest.mark.asyncio
    async def test_no_media_in_markdown(
        self, validator: AccessibilityValidator
    ) -> None:
        """Media checks only run on HTML content."""
        result = await validator.validate("# Title\n\nSome text.", {})
        assert not any("captions" in i or "Mermaid" in i for i in result.data["issues"])


# ── Color and language checks ────────────────────────────────────────


class TestColorAndLanguage:
    @pytest.mark.asyncio
    async def test_color_reference_md(self, validator: AccessibilityValidator) -> None:
        result = await validator.validate("# Title\n\nClick the red button.", {})
        assert any("color" in i.lower() for i in result.data["issues"])

    @pytest.mark.asyncio
    async def test_color_reference_html(
        self, validator: AccessibilityValidator
    ) -> None:
        result = await validator.validate(
            "<h1>Title</h1><p>Click the red button.</p>", {}
        )
        assert any("color" in i.lower() for i in result.data["issues"])

    @pytest.mark.asyncio
    async def test_long_sentence_html(self, validator: AccessibilityValidator) -> None:
        long = " ".join(["word"] * 35)
        result = await validator.validate(f"<h1>Title</h1><p>{long}.</p>", {})
        assert any("long sentence" in i.lower() for i in result.data["issues"])


# ── Overall scoring ──────────────────────────────────────────────────


class TestScoring:
    @pytest.mark.asyncio
    async def test_perfect_score(self, validator: AccessibilityValidator) -> None:
        content = "<h1>Welcome</h1><h2>Section</h2><p>Good content here.</p>"
        result = await validator.validate(content, {})
        assert result.success
        assert result.data["score"] == 100
        assert result.data["severity"] == "pass"

    @pytest.mark.asyncio
    async def test_checks_performed_includes_media(
        self, validator: AccessibilityValidator
    ) -> None:
        result = await validator.validate("<h1>Title</h1>", {})
        assert "media_alternatives" in result.data["checks_performed"]

    @pytest.mark.asyncio
    async def test_score_deduction(self, validator: AccessibilityValidator) -> None:
        # 2 issues: missing alt + generic link → score = 90
        content = '<h1>Title</h1><img src="x.jpg"><a href="http://x">click here</a>'
        result = await validator.validate(content, {})
        assert result.data["score"] <= 90
        assert result.data["issue_count"] >= 2
