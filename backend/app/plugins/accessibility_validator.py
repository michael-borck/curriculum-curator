"""
Accessibility Validator Plugin
Checks content for accessibility issues
"""

import re
from typing import Any

from app.plugins.base import PluginResult, ValidatorPlugin


class AccessibilityValidator(ValidatorPlugin):
    """Validates content for accessibility compliance"""

    @property
    def name(self) -> str:
        return "accessibility_validator"

    @property
    def description(self) -> str:
        return "Checks content for WCAG accessibility compliance"

    def _check_images(self, content: str) -> tuple[list[str], list[str]]:
        """Check images for alt text"""
        issues = []
        suggestions = []

        # Find all markdown images
        image_pattern = r"!\[(.*?)\]\((.*?)\)"
        images = re.findall(image_pattern, content)

        for alt_text, url in images:
            if not alt_text.strip():
                issues.append(f"Image '{url}' is missing alt text")
                suggestions.append(
                    f"Add descriptive alt text for image: ![descriptive text]({url})"
                )
            elif len(alt_text) < 5:
                issues.append(f"Image '{url}' has insufficient alt text: '{alt_text}'")
                suggestions.append(
                    f"Provide more descriptive alt text for '{url}' (current: '{alt_text}')"
                )
            elif alt_text.lower() in ["image", "picture", "photo", "img"]:
                issues.append(f"Image '{url}' has generic alt text: '{alt_text}'")
                suggestions.append(
                    f"Replace generic alt text '{alt_text}' with descriptive text for '{url}'"
                )

        return issues, suggestions

    def _check_headings(self, content: str) -> tuple[list[str], list[str]]:
        """Check heading structure"""
        issues = []
        suggestions = []

        # Find all headings
        heading_pattern = r"^(#{1,6})\s+(.+)$"
        headings = re.findall(heading_pattern, content, re.MULTILINE)

        if not headings:
            issues.append("No headings found in content")
            suggestions.append(
                "Add headings to structure your content (use # for main heading)"
            )
            return issues, suggestions

        # Check heading levels
        levels = [len(h[0]) for h in headings]

        # Check for H1
        if 1 not in levels:
            issues.append("Missing main heading (H1)")
            suggestions.append("Add a main heading using single # at the start")

        # Check for skipped levels
        for i in range(1, len(levels)):
            if levels[i] - levels[i - 1] > 1:
                issues.append(
                    f"Heading level skip: H{levels[i - 1]} followed by H{levels[i]}"
                )
                suggestions.append(
                    f"Use sequential heading levels (H{levels[i - 1]} → H{levels[i - 1] + 1})"
                )

        # Check for multiple H1s
        h1_count = levels.count(1)
        if h1_count > 1:
            issues.append(f"Multiple H1 headings found ({h1_count})")
            suggestions.append("Use only one H1 (main heading) per document")

        # Check heading text
        for _level, text in headings:
            if len(text) > 100:
                issues.append(f"Heading too long: '{text[:50]}...'")
                suggestions.append(
                    f"Shorten heading to under 100 characters: '{text[:50]}...'"
                )
            if text.isupper():
                issues.append(f"Heading in all caps: '{text}'")
                suggestions.append(f"Use sentence case instead of all caps: '{text}'")

        return issues, suggestions

    def _check_links(self, content: str) -> tuple[list[str], list[str]]:
        """Check links for accessibility"""
        issues = []
        suggestions = []

        # Find all markdown links
        link_pattern = r"\[([^\]]*)\]\(([^)]+)\)"
        links = re.findall(link_pattern, content)

        for text, url in links:
            if not text.strip():
                issues.append(f"Link to '{url}' has no text")
                suggestions.append(
                    f"Add descriptive link text: [descriptive text]({url})"
                )
            elif text.lower() in ["click here", "here", "link", "read more"]:
                issues.append(f"Link has non-descriptive text: '{text}'")
                suggestions.append(
                    f"Replace '{text}' with descriptive text that explains the link destination"
                )
            elif len(text) > 100:
                issues.append(f"Link text too long: '{text[:50]}...'")
                suggestions.append("Shorten link text to under 100 characters")

        return issues, suggestions

    def _check_lists(self, content: str) -> tuple[list[str], list[str]]:
        """Check list formatting"""
        issues = []
        suggestions = []

        # Check for improperly formatted lists
        lines = content.split("\n")
        in_list = False
        list_indent = 0

        for i, line in enumerate(lines):
            # Check for list markers
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

    def _check_color_references(self, content: str) -> tuple[list[str], list[str]]:
        """Check for color-only references"""
        issues = []
        suggestions = []

        color_words = [
            "red",
            "green",
            "blue",
            "yellow",
            "orange",
            "purple",
            "pink",
            "brown",
            "gray",
            "grey",
            "black",
            "white",
        ]

        color_pattern = r"\b(" + "|".join(color_words) + r")\b"

        # Look for phrases like "click the red button" or "the green section"
        instruction_pattern = (
            r"(click|press|select|choose|see|look at|refer to|find)\s+the\s+"
            + color_pattern
        )

        if re.search(instruction_pattern, content, re.IGNORECASE):
            issues.append("Content relies on color alone to convey information")
            suggestions.append(
                "Add additional identifiers besides color (e.g., 'the red Submit button' "
                + "instead of 'the red button')"
            )

        return issues, suggestions

    def _check_tables(self, content: str) -> tuple[list[str], list[str]]:
        """Check table accessibility"""
        issues = []
        suggestions = []

        # Simple markdown table detection
        table_pattern = r"\|.*\|.*\|"
        if re.search(table_pattern, content):
            # Check for header row (usually second line is |---|---|)
            lines = content.split("\n")
            table_lines = [i for i, line in enumerate(lines) if "|" in line]

            for i in range(len(table_lines) - 1):
                if table_lines[i + 1] == table_lines[i] + 1:
                    lines[table_lines[i]]
                    separator_line = (
                        lines[table_lines[i + 1]]
                        if table_lines[i + 1] < len(lines)
                        else ""
                    )

                    if not re.match(r"^\|?\s*:?-+:?\s*\|", separator_line):
                        issues.append("Table may be missing header row")
                        suggestions.append(
                            "Ensure tables have header rows with |---|---| separator"
                        )

        return issues, suggestions

    def _check_language(self, content: str) -> tuple[list[str], list[str]]:
        """Check for complex language and jargon"""
        issues = []
        suggestions = []

        # Check for very long sentences
        sentences = re.split(r"[.!?]+", content)
        for sentence in sentences:
            word_count = len(sentence.split())
            if word_count > 30:
                issues.append(
                    f"Very long sentence ({word_count} words): '{sentence[:50]}...'"
                )
                suggestions.append(
                    "Break long sentences into shorter ones for better readability"
                )

        return issues, suggestions

    async def validate(self, content: str, metadata: dict[str, Any]) -> PluginResult:
        """Validate content accessibility"""
        try:
            all_issues = []
            all_suggestions = []

            # Run all checks
            checks = [
                self._check_images,
                self._check_headings,
                self._check_links,
                self._check_lists,
                self._check_color_references,
                self._check_tables,
                self._check_language,
            ]

            for check in checks:
                issues, suggestions = check(content)
                all_issues.extend(issues)
                all_suggestions.extend(suggestions)

            # Calculate accessibility score
            base_score = 100
            deduction_per_issue = 5
            score = max(0, base_score - (len(all_issues) * deduction_per_issue))

            # Determine pass/fail
            passed = len(all_issues) == 0
            severity = "pass"

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
                message = "Content passes accessibility validation"

            return PluginResult(
                success=passed,
                message=message,
                data={
                    "score": score,
                    "issue_count": len(all_issues),
                    "severity": severity,
                    "issues": all_issues[:10]
                    if all_issues
                    else [],  # Limit to first 10
                    "checks_performed": [
                        "images_alt_text",
                        "heading_structure",
                        "link_text",
                        "list_formatting",
                        "color_references",
                        "table_structure",
                        "language_complexity",
                    ],
                },
                suggestions=all_suggestions[:10]
                if all_suggestions
                else None,  # Limit to first 10
            )

        except Exception as e:
            return PluginResult(
                success=False,
                message=f"Accessibility validation failed: {e!s}",
            )
