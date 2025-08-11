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
        anchor = anchor.strip("-")  # Remove leading/trailing hyphens
        return anchor

    def _generate_toc_markdown(
        self,
        headings: list[tuple[int, str, str]],
        max_depth: int = 3,
        numbered: bool = False,
        skip_first_h1: bool = True
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
                num_parts = []
                for j in range(1, level + 1):
                    if numbering[j] > 0:
                        num_parts.append(str(numbering[j]))
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

        # Look for TOC markers
        toc_start = None
        toc_end = None

        # Pattern 1: ## Table of Contents
        for i, line in enumerate(lines):
            if re.match(r"^#{1,2}\s*Table of Contents\s*$", line, re.IGNORECASE):
                toc_start = i
                # Find where TOC ends (next heading or empty lines)
                for j in range(i + 1, len(lines)):
                    if re.match(r"^#{1,6}\s+", lines[j]) and j > i + 1:
                        toc_end = j
                        break
                    if j > i + 2 and lines[j] == "" and lines[j-1] == "":
                        toc_end = j - 1
                        break
                if toc_end is None:
                    # Find last non-empty line of TOC
                    for j in range(i + 1, min(i + 50, len(lines))):
                        if lines[j] and not lines[j].startswith(("  - ", "- ")):
                            toc_end = j
                            break
                    if toc_end is None:
                        toc_end = min(i + 20, len(lines))
                break

        # Pattern 2: <!-- TOC --> markers
        for i, line in enumerate(lines):
            if "<!-- TOC -->" in line or "<!-- toc -->" in line.lower():
                toc_start = i
                for j in range(i + 1, len(lines)):
                    if "<!-- /TOC -->" in lines[j] or "<!-- /toc -->" in lines[j].lower():
                        toc_end = j + 1
                        break
                break

        if toc_start is not None and toc_end is not None:
            return (toc_start, toc_end)
        return None

    def _add_anchors_to_headings(self, content: str, headings: list[tuple[int, str, str]]) -> str:
        """Add anchor IDs to headings that don't have them."""
        lines = content.split("\n")
        heading_index = 0

        for i, line in enumerate(lines):
            match = re.match(r"^(#{1,6})\s+(.+)$", line)
            if match and heading_index < len(headings):
                level = len(match.group(1))
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
            # Parse options from issues (if any)
            options = {}
            for issue in issues:
                if isinstance(issue, dict):
                    options.update(issue)

            # Get configuration
            max_depth = options.get("max_depth", 3)
            numbered = options.get("numbered", False)
            skip_first_h1 = options.get("skip_first_h1", True)
            add_anchors = options.get("add_anchors", True)
            position = options.get("position", "after_first_heading")  # or "top"

            # Extract headings
            headings = self._extract_headings(content)

            if not headings:
                return PluginResult(
                    success=True,
                    message="No headings found to generate TOC",
                    data={"skipped": True, "reason": "no_headings"},
                )

            # Generate TOC
            toc = self._generate_toc_markdown(
                headings,
                max_depth=max_depth,
                numbered=numbered,
                skip_first_h1=skip_first_h1
            )

            if not toc:
                return PluginResult(
                    success=True,
                    message="No content for TOC (check max_depth setting)",
                    data={"skipped": True, "reason": "no_content"},
                )

            # Check for existing TOC
            existing_toc = self._find_existing_toc(content)

            # Prepare modified content
            lines = content.split("\n")

            if existing_toc:
                # Replace existing TOC
                start, end = existing_toc
                new_lines = lines[:start] + toc.split("\n") + lines[end:]
                new_content = "\n".join(new_lines)
                action = "updated"
            else:
                # Insert new TOC
                if position == "top":
                    # Insert at the very top
                    new_content = toc + "\n" + content
                else:
                    # Insert after first heading (default)
                    first_heading = None
                    for i, line in enumerate(lines):
                        if re.match(r"^#{1,6}\s+", line):
                            first_heading = i
                            break

                    if first_heading is not None:
                        # Insert after first heading with a blank line
                        new_lines = (
                            lines[:first_heading + 1]
                            + ["", ""]
                            + toc.split("\n")
                            + [""]
                            + lines[first_heading + 1:]
                        )
                        new_content = "\n".join(new_lines)
                    else:
                        # No headings found, insert at top
                        new_content = toc + "\n" + content
                action = "added"

            # Add anchors to headings if requested
            if add_anchors:
                new_content = self._add_anchors_to_headings(new_content, headings)

            # Clean up multiple blank lines
            new_content = re.sub(r"\n{3,}", "\n\n", new_content)

            return PluginResult(
                success=True,
                message=f"Table of contents {action} successfully",
                data={
                    "content": new_content,
                    "action": action,
                    "heading_count": len(headings),
                    "toc_depth": max_depth,
                    "numbered": numbered,
                    "anchors_added": add_anchors,
                    "toc_length": len(toc.split("\n")),
                },
                suggestions=None,
            )

        except Exception as e:
            return PluginResult(
                success=False,
                message=f"TOC generation failed: {e!s}",
            )

