"""
Markdown Cleanup Remediator Plugin
Cleans up messy markdown from copy-paste and inconsistent LLM output.
"""

import re

from app.plugins.base import PluginResult, RemediatorPlugin


class MarkdownCleanup(RemediatorPlugin):
    """Cleans up messy markdown formatting from copy-paste and LLM output"""

    @property
    def name(self) -> str:
        return "markdown_cleanup"

    @property
    def description(self) -> str:
        return "Cleans up copy-paste artefacts, fixes heading hierarchy, normalises lists and spacing"

    def _fix_copy_paste_artefacts(self, content: str) -> tuple[str, list[str]]:
        """Fix smart quotes, dashes, invisible characters, and excessive blank lines."""
        changes: list[str] = []
        original = content

        # Smart quotes to straight quotes
        content = content.replace("\u2018", "'").replace("\u2019", "'")  # single
        content = content.replace("\u201c", '"').replace("\u201d", '"')  # double

        # Em/en dashes
        content = content.replace("\u2014", "---")  # em dash
        content = content.replace("\u2013", "--")  # en dash

        # Non-breaking spaces
        content = content.replace("\u00a0", " ")

        # Zero-width characters
        content = re.sub(r"[\u200b\u200c\u200d\ufeff]", "", content)

        if content != original:
            changes.append("Replaced smart quotes, special dashes, and invisible characters")

        # Excessive blank lines (3+ newlines -> 2)
        new_content = re.sub(r"\n{3,}", "\n\n", content)
        if new_content != content:
            changes.append("Collapsed excessive blank lines")
            content = new_content

        return content, changes

    def _detect_and_add_headings(self, content: str) -> tuple[str, list[str]]:
        """Convert ALL-CAPS lines and colon-ending lines to headings."""
        changes: list[str] = []
        lines = content.split("\n")

        for i, line in enumerate(lines):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue

            # ALL-CAPS lines: 3+ words, <80 chars, followed by content
            words = stripped.split()
            if (
                len(words) >= 3
                and len(stripped) < 80
                and stripped == stripped.upper()
                and re.match(r"^[A-Z][A-Z0-9\s,&:'-]+$", stripped)
                and i + 1 < len(lines)
                and lines[i + 1].strip()
            ):
                title_case = stripped.title()
                lines[i] = f"## {title_case}"
                changes.append(f"Converted ALL-CAPS line to heading: {title_case}")
                continue

            # Lines ending with ':' that look like section headers (short, no period)
            if (
                stripped.endswith(":")
                and len(stripped) < 60
                and "." not in stripped
                and len(words) <= 8
                and not re.match(r"^[-*\d]", stripped)
            ):
                heading_text = stripped.rstrip(":")
                lines[i] = f"### {heading_text}"
                changes.append(f"Converted colon-header to heading: {heading_text}")

        if changes:
            content = "\n".join(lines)

        return content, changes

    def _convert_flat_lists(self, content: str) -> tuple[str, list[str]]:
        """Fix list formatting: missing spaces, letter lists."""
        changes: list[str] = []
        lines = content.split("\n")

        for i, line in enumerate(lines):
            # Fix "-item" (dash without space)
            match = re.match(r"^(\s*)-(\S)", line)
            if match:
                lines[i] = f"{match.group(1)}- {match.group(2)}{line[match.end():]}"
                changes.append(f"Added missing space after list dash at line {i + 1}")
                continue

            # Convert letter lists: a) / b) / c) -> bullet
            match = re.match(r"^(\s*)[a-z]\)\s+", line)
            if match:
                lines[i] = re.sub(r"^(\s*)[a-z]\)\s+", r"\1- ", line)
                changes.append(f"Converted letter list to bullet at line {i + 1}")

        if changes:
            content = "\n".join(lines)

        return content, changes

    def _normalise_heading_levels(self, content: str) -> tuple[str, list[str]]:
        """Ensure no heading level skips and proper nesting."""
        changes: list[str] = []
        lines = content.split("\n")

        # Collect heading positions and levels
        headings: list[tuple[int, int]] = []  # (line_index, level)
        for i, line in enumerate(lines):
            match = re.match(r"^(#{1,6})\s+", line)
            if match:
                headings.append((i, len(match.group(1))))

        if not headings:
            return content, changes

        # Ensure first heading is H1 or H2 (not deeper)
        _first_idx, first_level = headings[0]
        if first_level > 2:
            shift = first_level - 2
            for idx, level in headings:
                new_level = max(1, level - shift)
                match = re.match(r"^#{1,6}", lines[idx])
                if match:
                    lines[idx] = "#" * new_level + lines[idx][match.end() :]
            changes.append("Shifted all headings up to start at H2")
            # Recalculate headings
            headings = []
            for i, line in enumerate(lines):
                match = re.match(r"^(#{1,6})\s+", line)
                if match:
                    headings.append((i, len(match.group(1))))

        # Fix level skips
        prev_level = 0
        for idx, level in headings:
            if prev_level > 0 and level - prev_level > 1:
                new_level = prev_level + 1
                match = re.match(r"^#{1,6}", lines[idx])
                if match:
                    lines[idx] = "#" * new_level + lines[idx][match.end() :]
                    changes.append(f"Fixed heading level skip at line {idx + 1} (H{level} -> H{new_level})")
                    prev_level = new_level
                    continue
            prev_level = level

        if changes:
            content = "\n".join(lines)

        return content, changes

    def _add_blank_lines_around_blocks(self, content: str) -> tuple[str, list[str]]:
        """Ensure blank lines before/after headings, code blocks, blockquotes, and list starts."""
        changes: list[str] = []
        lines = content.split("\n")
        result: list[str] = []

        in_code_block = False
        prev_was_list = False

        for i, line in enumerate(lines):
            stripped = line.strip()

            # Track fenced code blocks
            if stripped.startswith("```"):
                in_code_block = not in_code_block

            if in_code_block:
                result.append(line)
                prev_was_list = False
                continue

            is_heading = bool(re.match(r"^#{1,6}\s+", stripped))
            is_fence = stripped.startswith("```")
            is_blockquote = stripped.startswith(">")
            is_list_item = bool(re.match(r"^[-*+]\s|^\d+[.)]\s", stripped))
            is_block_element = is_heading or is_fence or is_blockquote

            # Add blank line before block elements (if previous line is non-empty)
            if is_block_element and result and result[-1].strip():
                result.append("")
                changes.append(f"Added blank line before block element at line {i + 1}")

            # Add blank line before first list item (but not between consecutive items)
            if is_list_item and not prev_was_list and result and result[-1].strip():
                result.append("")
                changes.append(f"Added blank line before list start at line {i + 1}")

            result.append(line)

            # Add blank line after block elements (if next line is non-empty)
            if is_block_element and i + 1 < len(lines) and lines[i + 1].strip():
                next_stripped = lines[i + 1].strip()
                # Don't add after heading if next line is also a block element
                if not (
                    re.match(r"^#{1,6}\s+", next_stripped)
                    or next_stripped.startswith(("```", ">"))
                    or re.match(r"^[-*+]\s|^\d+[.)]\s", next_stripped)
                ):
                    result.append("")
                    changes.append(f"Added blank line after block element at line {i + 1}")

            prev_was_list = is_list_item

        if changes:
            # Collapse any triple+ blank lines we may have introduced
            content = re.sub(r"\n{3,}", "\n\n", "\n".join(result))
        else:
            content = "\n".join(result)

        return content, changes

    def _detect_code_blocks(self, content: str) -> tuple[str, list[str]]:
        """Wrap runs of indented lines (4+ spaces) in fenced code blocks."""
        changes: list[str] = []
        lines = content.split("\n")
        result: list[str] = []
        in_fence = False
        indented_block: list[str] = []

        def detect_language(block: list[str]) -> str:
            """Simple heuristic for code language detection."""
            text = "\n".join(block)
            if re.search(r"\b(def |import |class |print\(|self\.|if __name__)", text):
                return "python"
            if re.search(r"\b(function |const |let |var |=>|console\.log)", text):
                return "javascript"
            if re.search(r"<\/?[a-z]+[\s>]|<!DOCTYPE", text, re.IGNORECASE):
                return "html"
            return ""

        def flush_indented() -> None:
            if len(indented_block) >= 2:
                lang = detect_language(indented_block)
                result.append(f"```{lang}")
                result.extend(bl[4:] if bl.startswith("    ") else bl for bl in indented_block)
                result.append("```")
                changes.append(
                    f"Wrapped {len(indented_block)} indented lines in a code block"
                )
            else:
                result.extend(indented_block)
            indented_block.clear()

        for line in lines:
            if line.strip().startswith("```"):
                flush_indented()
                in_fence = not in_fence
                result.append(line)
                continue

            if in_fence:
                result.append(line)
                continue

            # Check for 4+ space indent (not a list item)
            if re.match(r"^    \S", line) and not re.match(r"^\s*[-*+]\s|^\s*\d+[.)]\s", line):
                indented_block.append(line)
            else:
                flush_indented()
                result.append(line)

        flush_indented()

        if changes:
            content = "\n".join(result)

        return content, changes

    def _fix_broken_links(self, content: str) -> tuple[str, list[str]]:
        """Fix space between ] and ( in markdown links."""
        changes: list[str] = []

        new_content = re.sub(r"\]\s+\(", "](", content)
        if new_content != content:
            changes.append("Fixed broken markdown links (removed space between ] and ()")
            content = new_content

        return content, changes

    async def remediate(self, content: str, issues: list) -> PluginResult:
        """Apply all markdown cleanup fixes."""
        try:
            all_changes: list[str] = []
            original_content = content

            fixes = [
                self._fix_copy_paste_artefacts,
                self._detect_and_add_headings,
                self._convert_flat_lists,
                self._normalise_heading_levels,
                self._add_blank_lines_around_blocks,
                self._detect_code_blocks,
                self._fix_broken_links,
            ]

            for fix_func in fixes:
                content, changes = fix_func(content)
                all_changes.extend(changes)

            lines_changed = 0
            if content != original_content:
                original_lines = original_content.split("\n")
                new_lines = content.split("\n")
                lines_changed = sum(
                    1
                    for i in range(min(len(original_lines), len(new_lines)))
                    if i < len(original_lines)
                    and i < len(new_lines)
                    and original_lines[i] != new_lines[i]
                )

            if all_changes:
                message = f"Applied {len(all_changes)} markdown cleanup fixes"
            else:
                message = "No markdown cleanup needed"

            return PluginResult(
                success=True,
                message=message,
                data={
                    "content": content,
                    "changes_made": all_changes,
                    "change_count": len(all_changes),
                    "lines_changed": lines_changed,
                    "fixes_applied": [
                        "copy_paste_artefacts",
                        "heading_detection",
                        "flat_lists",
                        "heading_levels",
                        "block_spacing",
                        "code_blocks",
                        "broken_links",
                    ],
                },
                suggestions=None,
            )

        except Exception as e:
            return PluginResult(
                success=False,
                message=f"Markdown cleanup failed: {e!s}",
            )
