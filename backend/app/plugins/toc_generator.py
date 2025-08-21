"""
Table of Contents Generator Plugin.

Automatically generates and updates table of contents from document headings
"""

import re

from app.plugins.base import PluginResult, RemediatorPlugin


class TOCGenerator(RemediatorPlugin):
    """Generates or updates table of contents based on document structure."""

    @property
    def name(self) -> str:
        """Return plugin name."""
        return "toc_generator"

    @property
    def description(self) -> str:
        """Return plugin description."""
        return "Automatically generates table of contents from headings"

    def _extract_headings(self, content: str) -> list[tuple[int, str, str]]:
        """Extract all headings from content.

        Returns:
            List of tuples (level, text, anchor_id)
        """
        headings = []
        lines = content.split("\n")

        for line in lines:
            # Match markdown headings
            match = re.match(r"^(#{1,6})\s+(.+)$", line)
            if match:
                level = len(match.group(1))
                text = match.group(2).strip()

                # Remove any existing anchor tags or formatting
                text_clean = re.sub(r"\{#.*?\}", "", text)  # Remove {#anchor}
                text_clean = re.sub(r"[*_`\[\]()]", "", text_clean)  # Remove formatting
                text_clean = text_clean.strip()

                # Generate anchor ID
                anchor_id = self._generate_anchor_id(text_clean)

                headings.append((level, text_clean, anchor_id))

        return headings

    def _generate_anchor_id(self, text: str) -> str:
        """Generate an anchor ID from heading text."""
        # Convert to lowercase and replace spaces with hyphens
        anchor = text.lower()
        anchor = re.sub(r"[^\w\s-]", "", anchor)  # Remove special chars
        anchor = re.sub(r"\s+", "-", anchor)  # Replace spaces with hyphens
        anchor = re.sub(r"-+", "-", anchor)  # Remove multiple hyphens
        return anchor.strip("-")  # Remove leading/trailing hyphens

    def _generate_toc_markdown(
        self,
        headings: list[tuple[int, str, str]],
        max_depth: int = 3,
        numbered: bool = False,
        skip_first_h1: bool = True,
    ) -> str:
        """Generate markdown for table of contents."""
        if not headings:
            return ""

        toc_lines = ["## Table of Contents\n"]

        # Track numbering for each level
        numbering = [0] * 7  # Support up to h6

        for i, (level, text, anchor_id) in enumerate(headings):
            # Skip first H1 if requested (usually the document title)
            if skip_first_h1 and level == 1 and i == 0:
                continue

            # Skip if beyond max depth
            if level > max_depth:
                continue

            # Calculate indentation
            indent = "  " * (level - 1)

            # Generate numbering if requested
            if numbered:
                numbering[level] += 1
                # Reset deeper levels
                for j in range(level + 1, 7):
                    numbering[j] = 0

                # Build number string (e.g., "1.2.3")
                num_parts = [
                    str(numbering[j]) for j in range(1, level + 1) if numbering[j] > 0
                ]
                num_str = ".".join(num_parts) + ". "
            else:
                num_str = ""

            # Create TOC entry
            toc_entry = f"{indent}- {num_str}[{text}](#{anchor_id})"
            toc_lines.append(toc_entry)

        if len(toc_lines) == 1:  # Only header, no content
            return ""

        return "\n".join(toc_lines) + "\n"

    def _find_existing_toc(self, content: str) -> tuple[int, int] | None:
        """Find existing TOC in content.

        Returns:
            Tuple of (start_index, end_index) or None if not found
        """
        lines = content.split("\n")

        # Try Pattern 1: Markdown TOC header
        result = self._find_markdown_toc(lines)
        if result:
            return result

        # Try Pattern 2: HTML comment markers
        result = self._find_html_toc_markers(lines)
        if result:
            return result

        return None

    def _find_markdown_toc(self, lines: list[str]) -> tuple[int, int] | None:
        """Find TOC marked with markdown header."""
        for i, line in enumerate(lines):
            if re.match(r"^#{1,2}\s*Table of Contents\s*$", line, re.IGNORECASE):
                toc_end = self._find_toc_end(lines, i)
                return (i, toc_end) if toc_end is not None else None
        return None

    def _find_html_toc_markers(self, lines: list[str]) -> tuple[int, int] | None:
        """Find TOC marked with HTML comments."""
        for i, line in enumerate(lines):
            if "<!-- TOC -->" in line or "<!-- toc -->" in line.lower():
                for j in range(i + 1, len(lines)):
                    if (
                        "<!-- /TOC -->" in lines[j]
                        or "<!-- /toc -->" in lines[j].lower()
                    ):
                        return (i, j + 1)
                break
        return None

    def _find_toc_end(self, lines: list[str], start_index: int) -> int | None:
        """Find where TOC ends after a given start index."""
        # Check for next heading or double empty lines
        for j in range(start_index + 1, len(lines)):
            if re.match(r"^#{1,6}\s+", lines[j]) and j > start_index + 1:
                return j
            if j > start_index + 2 and lines[j] == "" and lines[j - 1] == "":
                return j - 1

        # Find last non-empty line of TOC
        for j in range(start_index + 1, min(start_index + 50, len(lines))):
            if lines[j] and not lines[j].startswith(("  - ", "- ")):
                return j

        # Default to a reasonable limit
        return min(start_index + 20, len(lines))

    def _add_anchors_to_headings(
        self, content: str, headings: list[tuple[int, str, str]]
    ) -> str:
        """Add anchor IDs to headings that don't have them."""
        lines = content.split("\n")
        heading_index = 0

        for i, line in enumerate(lines):
            match = re.match(r"^(#{1,6})\s+(.+)$", line)
            if match and heading_index < len(headings):
                len(match.group(1))
                text = match.group(2).strip()

                # Check if this heading already has an anchor
                if not re.search(r"\{#.*?\}$", text):
                    # Add anchor ID
                    _, _, anchor_id = headings[heading_index]
                    lines[i] = f"{match.group(1)} {text} {{#{anchor_id}}}"

                heading_index += 1

        return "\n".join(lines)

    async def remediate(self, content: str, issues: list) -> PluginResult:
        """Generate or update table of contents."""
        try:
            # Parse configuration
            options = self._parse_options(issues)

            # Extract headings
            headings = self._extract_headings(content)
            if not headings:
                return self._no_headings_result()

            # Generate TOC
            toc = self._generate_toc_markdown(
                headings,
                max_depth=options["max_depth"],
                numbered=options["numbered"],
                skip_first_h1=options["skip_first_h1"],
            )
            if not toc:
                return self._no_content_result()

            # Process content with TOC
            new_content, action = self._process_content_with_toc(
                content, toc, options["position"]
            )

            # Add anchors if requested
            if options["add_anchors"]:
                new_content = self._add_anchors_to_headings(new_content, headings)

            # Clean up formatting
            new_content = re.sub(r"\n{3,}", "\n\n", new_content)

            return self._success_result(new_content, action, headings, toc, options)

        except Exception as e:
            return PluginResult(
                success=False,
                message=f"TOC generation failed: {e!s}",
            )

    def _parse_options(self, issues: list) -> dict:
        """Parse configuration options from issues."""
        options = {
            "max_depth": 3,
            "numbered": False,
            "skip_first_h1": True,
            "add_anchors": True,
            "position": "after_first_heading",
        }

        for issue in issues:
            if isinstance(issue, dict):
                options.update(issue)

        return options

    def _no_headings_result(self) -> PluginResult:
        """Return result when no headings are found."""
        return PluginResult(
            success=True,
            message="No headings found to generate TOC",
            data={"skipped": True, "reason": "no_headings"},
        )

    def _no_content_result(self) -> PluginResult:
        """Return result when no TOC content is generated."""
        return PluginResult(
            success=True,
            message="No content for TOC (check max_depth setting)",
            data={"skipped": True, "reason": "no_content"},
        )

    def _process_content_with_toc(
        self, content: str, toc: str, position: str
    ) -> tuple[str, str]:
        """Process content to add or update TOC."""
        existing_toc = self._find_existing_toc(content)
        lines = content.split("\n")

        if existing_toc:
            # Replace existing TOC
            start, end = existing_toc
            new_lines = lines[:start] + toc.split("\n") + lines[end:]
            return "\n".join(new_lines), "updated"

        # Insert new TOC
        if position == "top":
            return toc + "\n" + content, "added"

        # Insert after first heading (default)
        return self._insert_toc_after_first_heading(lines, toc)

    def _insert_toc_after_first_heading(
        self, lines: list[str], toc: str
    ) -> tuple[str, str]:
        """Insert TOC after the first heading."""
        for i, line in enumerate(lines):
            if re.match(r"^#{1,6}\s+", line):
                new_lines = [
                    *lines[: i + 1],
                    "",
                    "",
                    *toc.split("\n"),
                    "",
                    *lines[i + 1 :],
                ]
                return "\n".join(new_lines), "added"

        # No headings found, insert at top
        return toc + "\n" + "\n".join(lines), "added"

    def _success_result(
        self,
        new_content: str,
        action: str,
        headings: list,
        toc: str,
        options: dict,
    ) -> PluginResult:
        """Create successful result with metadata."""
        return PluginResult(
            success=True,
            message=f"Table of contents {action} successfully",
            data={
                "content": new_content,
                "action": action,
                "heading_count": len(headings),
                "toc_depth": options["max_depth"],
                "numbered": options["numbered"],
                "anchors_added": options["add_anchors"],
                "toc_length": len(toc.split("\n")),
            },
            suggestions=None,
        )
