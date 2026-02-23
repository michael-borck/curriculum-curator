"""
Accessibility Validator Plugin

Checks content for WCAG accessibility issues.
Handles both markdown and HTML content (TipTap editor outputs HTML).
"""

import re
from typing import Any

from app.plugins.base import PluginResult, ValidatorPlugin

# Generic alt text values that don't provide useful descriptions
_GENERIC_ALT = {"image", "picture", "photo", "img", "icon", "graphic", "logo"}

# Non-descriptive link text
_GENERIC_LINK_TEXT = {"click here", "here", "link", "read more", "more", "this"}


def _strip_html_tags(html: str) -> str:
    """Remove HTML tags to get plain text for language checks."""
    return re.sub(r"<[^>]+>", " ", html)


def _is_html(content: str) -> bool:
    """Detect whether content is HTML (vs markdown)."""
    return bool(re.search(r"<(?:p|h[1-6]|div|table|img|a|ul|ol)\b", content))


class AccessibilityValidator(ValidatorPlugin):
    """Validates content for WCAG accessibility compliance.

    Supports both markdown and HTML input — auto-detects format.
    """

    @property
    def name(self) -> str:
        return "accessibility_validator"

    @property
    def description(self) -> str:
        return "Checks content for WCAG accessibility compliance"

    # ------------------------------------------------------------------
    # Image checks (WCAG 1.1.1 — Non-text Content)
    # ------------------------------------------------------------------

    def _check_images(self, content: str) -> tuple[list[str], list[str]]:
        """Check images for alt text in both markdown and HTML."""
        issues: list[str] = []
        suggestions: list[str] = []

        if _is_html(content):
            self._check_images_html(content, issues, suggestions)
        else:
            self._check_images_md(content, issues, suggestions)

        return issues, suggestions

    def _check_images_md(
        self, content: str, issues: list[str], suggestions: list[str]
    ) -> None:
        for alt_text, url in re.findall(r"!\[(.*?)\]\((.*?)\)", content):
            self._evaluate_alt_text(alt_text, url, issues, suggestions)

    def _check_images_html(
        self, content: str, issues: list[str], suggestions: list[str]
    ) -> None:
        for tag in re.findall(r"<img\b[^>]*>", content, re.IGNORECASE):
            src_match = re.search(r'src=["\']([^"\']*)["\']', tag)
            alt_match = re.search(r'alt=["\']([^"\']*)["\']', tag)
            src = src_match.group(1) if src_match else "unknown"
            alt = alt_match.group(1) if alt_match else ""

            if not alt_match:
                issues.append(f"Image '{src}' is missing the alt attribute")
                suggestions.append(
                    f'Add an alt attribute to <img src="{src}"> with a meaningful description'
                )
            else:
                self._evaluate_alt_text(alt, src, issues, suggestions)

    @staticmethod
    def _evaluate_alt_text(
        alt_text: str, src: str, issues: list[str], suggestions: list[str]
    ) -> None:
        alt = alt_text.strip()
        if not alt:
            issues.append(f"Image '{src}' has empty alt text")
            suggestions.append(f"Add descriptive alt text for image: {src}")
        elif len(alt) < 5:
            issues.append(f"Image '{src}' has insufficient alt text: '{alt}'")
            suggestions.append(
                f"Provide more descriptive alt text for '{src}' (current: '{alt}')"
            )
        elif alt.lower() in _GENERIC_ALT:
            issues.append(f"Image '{src}' has generic alt text: '{alt}'")
            suggestions.append(
                f"Replace generic alt text '{alt}' with a description of '{src}'"
            )

    # ------------------------------------------------------------------
    # Heading checks (WCAG 1.3.1 — Info and Relationships)
    # ------------------------------------------------------------------

    def _check_headings(self, content: str) -> tuple[list[str], list[str]]:
        """Check heading structure in both markdown and HTML."""
        if _is_html(content):
            headings = [
                (int(m.group(1)), m.group(2))
                for m in re.finditer(
                    r"<h([1-6])\b[^>]*>(.*?)</h\1>", content, re.DOTALL | re.IGNORECASE
                )
            ]
        else:
            headings = [
                (len(m.group(1)), m.group(2))
                for m in re.finditer(r"^(#{1,6})\s+(.+)$", content, re.MULTILINE)
            ]

        issues: list[str] = []
        suggestions: list[str] = []

        if not headings:
            issues.append("No headings found in content")
            suggestions.append(
                "Add headings to structure your content for screen readers"
            )
            return issues, suggestions

        levels = [h[0] for h in headings]

        if 1 not in levels:
            issues.append("Missing main heading (H1)")
            suggestions.append("Add a main heading (H1) at the start of your content")

        for i in range(1, len(levels)):
            if levels[i] - levels[i - 1] > 1:
                issues.append(
                    f"Heading level skip: H{levels[i - 1]} followed by H{levels[i]}"
                )
                suggestions.append(
                    f"Use sequential heading levels (H{levels[i - 1]} → H{levels[i - 1] + 1})"
                )

        h1_count = levels.count(1)
        if h1_count > 1:
            issues.append(f"Multiple H1 headings found ({h1_count})")
            suggestions.append("Use only one H1 (main heading) per document")

        for _level, text in headings:
            plain = _strip_html_tags(text).strip()
            if len(plain) > 100:
                issues.append(f"Heading too long: '{plain[:50]}...'")
                suggestions.append(
                    f"Shorten heading to under 100 characters: '{plain[:50]}...'"
                )
            if plain.isupper() and len(plain) > 3:
                issues.append(f"Heading in all caps: '{plain}'")
                suggestions.append(f"Use sentence case instead of all caps: '{plain}'")

        return issues, suggestions

    # ------------------------------------------------------------------
    # Link checks (WCAG 2.4.4 — Link Purpose)
    # ------------------------------------------------------------------

    def _check_links(self, content: str) -> tuple[list[str], list[str]]:
        """Check links for descriptive text in both markdown and HTML."""
        issues: list[str] = []
        suggestions: list[str] = []

        if _is_html(content):
            for m in re.finditer(
                r'<a\b[^>]*href=["\']([^"\']*)["\'][^>]*>(.*?)</a>',
                content,
                re.DOTALL | re.IGNORECASE,
            ):
                url, text = m.group(1), _strip_html_tags(m.group(2)).strip()
                self._evaluate_link_text(text, url, issues, suggestions)
        else:
            for text, url in re.findall(r"\[([^\]]*)\]\(([^)]+)\)", content):
                self._evaluate_link_text(text.strip(), url, issues, suggestions)

        return issues, suggestions

    @staticmethod
    def _evaluate_link_text(
        text: str, url: str, issues: list[str], suggestions: list[str]
    ) -> None:
        if not text:
            issues.append(f"Link to '{url}' has no text")
            suggestions.append(f"Add descriptive link text for: {url}")
        elif text.lower() in _GENERIC_LINK_TEXT:
            issues.append(f"Link has non-descriptive text: '{text}'")
            suggestions.append(
                f"Replace '{text}' with text that explains the link destination"
            )
        elif len(text) > 100:
            issues.append(f"Link text too long: '{text[:50]}...'")
            suggestions.append("Shorten link text to under 100 characters")

    # ------------------------------------------------------------------
    # Table checks (WCAG 1.3.1 — Tables need headers)
    # ------------------------------------------------------------------

    def _check_tables(self, content: str) -> tuple[list[str], list[str]]:
        """Check tables for header rows in both markdown and HTML."""
        issues: list[str] = []
        suggestions: list[str] = []

        if _is_html(content):
            # Each <table> should contain at least one <th> or <thead>
            for table in re.findall(
                r"<table\b[^>]*>(.*?)</table>", content, re.DOTALL | re.IGNORECASE
            ):
                if not re.search(r"<th\b", table, re.IGNORECASE):
                    issues.append("Table is missing header cells (<th>)")
                    suggestions.append(
                        "Add <th> elements to the first row so screen readers identify columns"
                    )
        else:
            # Markdown tables: look for |---|---| separator after header row
            table_pattern = r"\|.*\|.*\|"
            if re.search(table_pattern, content):
                lines = content.split("\n")
                table_lines = [i for i, line in enumerate(lines) if "|" in line]
                for i in range(len(table_lines) - 1):
                    if table_lines[i + 1] == table_lines[i] + 1:
                        sep = (
                            lines[table_lines[i + 1]]
                            if table_lines[i + 1] < len(lines)
                            else ""
                        )
                        if not re.match(r"^\|?\s*:?-+:?\s*\|", sep):
                            issues.append("Table may be missing header row")
                            suggestions.append(
                                "Ensure tables have header rows with |---|---| separator"
                            )

        return issues, suggestions

    # ------------------------------------------------------------------
    # List checks (WCAG 1.3.1 — consistent structure)
    # ------------------------------------------------------------------

    def _check_lists(self, content: str) -> tuple[list[str], list[str]]:
        """Check list formatting (markdown only — HTML lists are structural)."""
        issues: list[str] = []
        suggestions: list[str] = []

        # HTML lists (<ul>/<ol>) are inherently well-structured, skip them
        if _is_html(content):
            return issues, suggestions

        lines = content.split("\n")
        in_list = False
        list_indent = 0

        for i, line in enumerate(lines):
            if re.match(r"^\s*[-*+]\s+", line) or re.match(r"^\s*\d+\.\s+", line):
                current_indent = len(line) - len(line.lstrip())
                if not in_list:
                    in_list = True
                    list_indent = current_indent
                elif abs(current_indent - list_indent) % 2 != 0:
                    issues.append(f"Inconsistent list indentation at line {i + 1}")
                    suggestions.append(
                        "Use consistent indentation (2 or 4 spaces) for list items"
                    )
            else:
                in_list = False

        return issues, suggestions

    # ------------------------------------------------------------------
    # Color reference checks (WCAG 1.4.1 — Use of Color)
    # ------------------------------------------------------------------

    def _check_color_references(self, content: str) -> tuple[list[str], list[str]]:
        """Check for color-only references."""
        issues: list[str] = []
        suggestions: list[str] = []

        plain = _strip_html_tags(content) if _is_html(content) else content

        color_words = (
            "red|green|blue|yellow|orange|purple|pink|brown|gray|grey|black|white"
        )
        instruction_pattern = (
            r"(click|press|select|choose|see|look at|refer to|find)\s+the\s+"
            + r"\b("
            + color_words
            + r")\b"
        )

        if re.search(instruction_pattern, plain, re.IGNORECASE):
            issues.append("Content relies on color alone to convey information")
            suggestions.append(
                "Add additional identifiers besides color (e.g., 'the red Submit button' "
                "instead of 'the red button')"
            )

        return issues, suggestions

    # ------------------------------------------------------------------
    # Language complexity (WCAG 3.1.5 — Reading Level)
    # ------------------------------------------------------------------

    def _check_language(self, content: str) -> tuple[list[str], list[str]]:
        """Check for overly complex language."""
        issues: list[str] = []
        suggestions: list[str] = []

        plain = _strip_html_tags(content) if _is_html(content) else content

        sentences = re.split(r"[.!?]+", plain)
        for sentence in sentences:
            word_count = len(sentence.split())
            if word_count > 30:
                preview = sentence.strip()[:50]
                issues.append(
                    f"Very long sentence ({word_count} words): '{preview}...'"
                )
                suggestions.append(
                    "Break long sentences into shorter ones for better readability"
                )

        return issues, suggestions

    # ------------------------------------------------------------------
    # Media checks (WCAG 1.2.1 — Audio/Video alternatives)
    # ------------------------------------------------------------------

    def _check_media(self, content: str) -> tuple[list[str], list[str]]:
        """Check video/audio embeds and diagrams for accessibility."""
        issues: list[str] = []
        suggestions: list[str] = []

        if not _is_html(content):
            return issues, suggestions

        # <video> without <track> for captions
        for tag in re.finditer(
            r"<video\b[^>]*>.*?</video>", content, re.DOTALL | re.IGNORECASE
        ):
            if not re.search(r"<track\b", tag.group(), re.IGNORECASE):
                issues.append("Video element is missing captions (<track>)")
                suggestions.append(
                    'Add a <track kind="captions"> element or provide a text transcript'
                )

        # Self-closing <video> tags (TipTap renders these as void elements)
        for tag in re.finditer(r"<video\b[^>]*/?>", content, re.IGNORECASE):
            if "</video>" not in content[
                tag.start() : tag.start() + 200
            ] and "video element" not in " ".join(issues):
                issues.append("Video element is missing captions (<track>)")
                suggestions.append(
                    "Consider providing a text transcript alongside the video"
                )

        # YouTube iframes without title attribute
        for tag in re.finditer(r"<iframe\b[^>]*>", content, re.IGNORECASE):
            iframe = tag.group()
            if re.search(r"youtube", iframe, re.IGNORECASE) and not re.search(
                r'title=["\']', iframe, re.IGNORECASE
            ):
                issues.append("YouTube embed is missing a title attribute")
                suggestions.append(
                    "Add a title attribute to the iframe describing the video content"
                )

        # Mermaid diagrams (<pre class="mermaid">) have no text alternative
        if re.search(r'<pre\b[^>]*class=["\'][^"\']*mermaid', content, re.IGNORECASE):
            issues.append("Mermaid diagram has no text alternative")
            suggestions.append(
                "Add a text description before or after the diagram explaining what it shows"
            )

        return issues, suggestions

    # ------------------------------------------------------------------
    # Main validation entry point
    # ------------------------------------------------------------------

    async def validate(self, content: str, metadata: dict[str, Any]) -> PluginResult:
        """Validate content accessibility."""
        try:
            all_issues: list[str] = []
            all_suggestions: list[str] = []

            checks = [
                self._check_images,
                self._check_headings,
                self._check_links,
                self._check_lists,
                self._check_color_references,
                self._check_tables,
                self._check_language,
                self._check_media,
            ]

            for check in checks:
                issues, suggestions = check(content)
                all_issues.extend(issues)
                all_suggestions.extend(suggestions)

            # Calculate accessibility score
            score = max(0, 100 - len(all_issues) * 5)

            passed = len(all_issues) == 0

            if len(all_issues) > 10:
                severity = "critical"
                message = (
                    f"Critical accessibility issues found ({len(all_issues)} issues)"
                )
            elif len(all_issues) > 5:
                severity = "major"
                message = f"Major accessibility issues found ({len(all_issues)} issues)"
            elif len(all_issues) > 0:
                severity = "minor"
                message = f"Minor accessibility issues found ({len(all_issues)} issues)"
            else:
                severity = "pass"
                message = "Content passes accessibility validation"

            return PluginResult(
                success=passed,
                message=message,
                data={
                    "score": score,
                    "issue_count": len(all_issues),
                    "severity": severity,
                    "issues": all_issues[:20],
                    "checks_performed": [
                        "images_alt_text",
                        "heading_structure",
                        "link_text",
                        "list_formatting",
                        "color_references",
                        "table_structure",
                        "language_complexity",
                        "media_alternatives",
                    ],
                },
                suggestions=all_suggestions[:20] if all_suggestions else None,
            )

        except Exception as e:
            return PluginResult(
                success=False,
                message=f"Accessibility validation failed: {e!s}",
            )
