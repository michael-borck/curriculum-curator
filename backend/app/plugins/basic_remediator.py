"""
Basic Remediator Plugin
Automatically fixes simple content issues
"""

import re

from app.plugins.base import PluginResult, RemediatorPlugin


class BasicRemediator(RemediatorPlugin):
    """Remediates basic content issues automatically"""

    @property
    def name(self) -> str:
        return "basic_remediator"

    @property
    def description(self) -> str:
        return "Automatically fixes basic formatting and style issues"

    def _fix_whitespace(self, content: str) -> tuple[str, list[str]]:
        """Fix whitespace issues"""
        changes = []
        original = content

        # Fix double spaces
        if "  " in content:
            content = re.sub(r"\s{2,}", " ", content)
            changes.append("Fixed multiple spaces")

        # Fix missing spaces after punctuation
        content = re.sub(r"([.!?,;:])([A-Z])", r"\1 \2", content)
        if content != original:
            changes.append("Added missing spaces after punctuation")

        # Fix trailing whitespace
        lines = content.split("\n")
        cleaned_lines = [line.rstrip() for line in lines]
        if lines != cleaned_lines:
            content = "\n".join(cleaned_lines)
            changes.append("Removed trailing whitespace")

        return content, changes

    def _fix_punctuation(self, content: str) -> tuple[str, list[str]]:
        """Fix punctuation issues"""
        changes = []

        # Fix multiple punctuation marks
        if re.search(r"[!?]{2,}", content):
            content = re.sub(r"[!]+", "!", content)
            content = re.sub(r"[?]+", "?", content)
            changes.append("Fixed multiple punctuation marks")

        # Fix ellipsis
        content = re.sub(r"\.{2,}", "...", content)

        # Ensure sentences end with punctuation
        lines = content.split("\n")
        for i, line in enumerate(lines):
            if line and not line.startswith("#") and not line.startswith("-"):
                # Check if line ends with alphanumeric and no punctuation
                if re.match(r".*[a-zA-Z0-9]$", line.strip()):
                    # Skip if it's likely a heading or list item
                    if not re.match(r"^\d+\.", line) and len(line) > 20:
                        lines[i] = line + "."
                        changes.append(f"Added missing period to line {i+1}")

        if changes:
            content = "\n".join(lines)

        return content, changes

    def _fix_common_typos(self, content: str) -> tuple[str, list[str]]:
        """Fix common typos"""
        changes = []

        typo_fixes = {
            r"\bthier\b": "their",
            r"\bteh\b": "the",
            r"\brecieve\b": "receive",
            r"\bseperate\b": "separate",
            r"\boccured\b": "occurred",
            r"\buntill\b": "until",
            r"\bwich\b": "which",
            r"\bbeacuse\b": "because",
            r"\bthat's\b": "that is",
            r"\bwon't\b": "will not",
            r"\bcan't\b": "cannot",
        }

        for pattern, replacement in typo_fixes.items():
            if re.search(pattern, content, re.IGNORECASE):
                # Preserve case
                def replace_preserve_case(match):
                    original = match.group()
                    if original.isupper():
                        return replacement.upper()
                    if original[0].isupper():
                        return replacement.capitalize()
                    return replacement

                new_content = re.sub(pattern, replace_preserve_case, content, flags=re.IGNORECASE)
                if new_content != content:
                    changes.append(f"Fixed typo: '{pattern}' → '{replacement}'")
                    content = new_content

        return content, changes

    def _fix_heading_structure(self, content: str) -> tuple[str, list[str]]:
        """Fix heading structure issues"""
        changes = []
        lines = content.split("\n")

        # Find all headings
        heading_lines = []
        for i, line in enumerate(lines):
            if re.match(r"^#{1,6}\s+", line):
                heading_lines.append((i, line))

        if not heading_lines:
            return content, changes

        # Check for missing H1
        has_h1 = any(line.startswith("# ") for _, line in heading_lines)
        if not has_h1 and heading_lines:
            # Make the first heading an H1
            first_idx, first_heading = heading_lines[0]
            if first_heading.startswith("## "):
                lines[first_idx] = first_heading[1:]  # Remove one #
                changes.append("Promoted first heading to H1")

        # Fix heading level skips
        prev_level = 0
        for i, (line_idx, heading) in enumerate(heading_lines):
            level = len(re.match(r"^(#+)", heading).group(1))

            if prev_level > 0 and level - prev_level > 1:
                # Fix skip by adjusting level
                new_level = prev_level + 1
                new_heading = "#" * new_level + heading[level:]
                lines[line_idx] = new_heading
                changes.append(f"Fixed heading level skip at line {line_idx + 1}")
                level = new_level

            prev_level = level

        if changes:
            content = "\n".join(lines)

        return content, changes

    def _fix_list_formatting(self, content: str) -> tuple[str, list[str]]:
        """Fix list formatting issues"""
        changes = []
        lines = content.split("\n")

        for i, line in enumerate(lines):
            # Fix inconsistent list markers
            if re.match(r"^\s*\*\s+", line):
                # Convert * to - for consistency
                lines[i] = re.sub(r"^(\s*)\*\s+", r"\1- ", line)
                changes.append(f"Standardized list marker at line {i+1}")

            # Fix numbered list formatting
            if re.match(r"^\s*\d+\)\s+", line):
                # Convert 1) to 1.
                lines[i] = re.sub(r"^(\s*)(\d+)\)\s+", r"\1\2. ", line)
                changes.append(f"Fixed numbered list format at line {i+1}")

        if changes:
            content = "\n".join(lines)

        return content, changes

    def _add_missing_alt_text(self, content: str) -> tuple[str, list[str]]:
        """Add generic alt text to images missing it"""
        changes = []

        # Find images without alt text
        image_pattern = r"!\[\]\((.*?)\)"

        def add_alt(match):
            url = match.group(1)
            filename = url.split("/")[-1].split(".")[0] if "/" in url else "image"
            # Convert filename to readable format
            alt_text = filename.replace("-", " ").replace("_", " ").title()
            changes.append(f"Added alt text '{alt_text}' to image")
            return f"![{alt_text}]({url})"

        new_content = re.sub(image_pattern, add_alt, content)

        return new_content, changes

    async def remediate(self, content: str, issues: list) -> PluginResult:
        """Remediate content issues"""
        try:
            all_changes = []
            original_content = content

            # Apply fixes in order
            fixes = [
                self._fix_whitespace,
                self._fix_punctuation,
                self._fix_common_typos,
                self._fix_heading_structure,
                self._fix_list_formatting,
                self._add_missing_alt_text,
            ]

            for fix_func in fixes:
                content, changes = fix_func(content)
                all_changes.extend(changes)

            # Calculate changes
            lines_changed = 0
            if content != original_content:
                original_lines = original_content.split("\n")
                new_lines = content.split("\n")
                lines_changed = sum(
                    1 for i in range(min(len(original_lines), len(new_lines)))
                    if i < len(original_lines) and i < len(new_lines)
                    and original_lines[i] != new_lines[i]
                )

            if all_changes:
                message = f"Applied {len(all_changes)} fixes to content"
                success = True
            else:
                message = "No automatic fixes needed"
                success = True

            return PluginResult(
                success=success,
                message=message,
                data={
                    "content": content,
                    "changes_made": all_changes,
                    "change_count": len(all_changes),
                    "lines_changed": lines_changed,
                    "fixes_applied": [
                        "whitespace",
                        "punctuation",
                        "typos",
                        "headings",
                        "lists",
                        "alt_text",
                    ],
                },
                suggestions=None,
            )

        except Exception as e:
            return PluginResult(
                success=False,
                message=f"Remediation failed: {e!s}",
            )
