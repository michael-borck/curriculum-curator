"""
Structural Markdown parser — converts Markdown into TipTap content_json.

Phase 2 default for ``.md`` files. Implementation strategy: convert
Markdown to HTML using the ``markdown`` library (already a project
dependency) and run the result through ``html_structural``. This avoids
maintaining a parallel AST walker for two formats with overlapping
semantics, and keeps both code paths in sync — a fix to the HTML
structural mapping automatically benefits Markdown imports.

Per docs/structured-import-plan.md, top-level ``---`` thematic breaks
are recognised as slide separators (Markdown's "horizontal rule" doubles
as a slide break in author conventions like Marp and reveal.js). The
``markdown`` library renders these as ``<hr>``, which the HTML parser
emits as ``horizontalRule``; we post-process them into ``slideBreak``
nodes since the structural intent in a Markdown deck is "next slide,"
not "decorative divider."

Marp/reveal.js/Quarto dialect specialisations are deferred to Phase 5 —
they live as separate parsers and override the default via the registry's
``autodetect`` dispatch when the file content has a confident dialect
signal (YAML front-matter ``marp: true``, ``format: revealjs``, etc.).
"""

from __future__ import annotations

import logging
from typing import ClassVar

import markdown

from app.services.material_parsers.base import (
    MaterialParser,
    MaterialParseResult,
)
from app.services.material_parsers.html_structural import HtmlStructuralParser

logger = logging.getLogger(__name__)


# Markdown extensions to enable. ``tables`` covers GFM tables, ``fenced_code``
# covers ``` blocks, ``codehilite`` is intentionally NOT enabled — it adds
# pygments-specific class names that the HTML walker doesn't need.
_MD_EXTENSIONS: list[str] = [
    "tables",
    "fenced_code",
    "footnotes",
]


class MdStructuralParser(MaterialParser):
    """Convert a Markdown document into TipTap content_json."""

    name: ClassVar[str] = "md_structural"
    display_name: ClassVar[str] = "Markdown (structural)"
    description: ClassVar[str] = (
        "Default Markdown importer. Converts Markdown to HTML via the "
        "standard library and runs it through the HTML structural parser. "
        "Supports CommonMark plus tables, fenced code blocks, and "
        "footnotes. Recognises top-level --- as slide breaks."
    )
    supported_formats: ClassVar[list[str]] = ["md"]
    requires_ai: ClassVar[bool] = False

    def __init__(self) -> None:
        # Reuse a single HtmlStructuralParser instance — it's stateless
        self._html_parser = HtmlStructuralParser()

    async def parse(
        self,
        file_content: bytes,
        filename: str,
        *,
        user_context: dict[str, object] | None = None,
    ) -> MaterialParseResult:
        _ = user_context

        text = file_content.decode("utf-8", errors="replace")

        # Strip YAML front-matter if present so the body parses cleanly.
        # The first line must be exactly --- and we look for the next ---
        # on its own line; anything between is metadata that doesn't
        # belong in the rendered content.
        body = self._strip_front_matter(text)

        html = markdown.markdown(body, extensions=_MD_EXTENSIONS)

        # Delegate to the HTML parser for the heavy lifting
        result = await self._html_parser.parse(
            html.encode("utf-8"), filename
        )

        # Post-process: top-level <hr> rendered from --- becomes a slideBreak.
        # The HTML parser emits horizontalRule for <hr>; we walk the top
        # level of the document and rewrite each one. Nested horizontal
        # rules (e.g. inside a blockquote) stay as horizontalRule because
        # they aren't slide separators in any markdown convention.
        rewritten_content = [
            {"type": "slideBreak"} if n.get("type") == "horizontalRule" else n
            for n in result.content_json.get("content", [])
        ]

        return MaterialParseResult(
            title=result.title,
            content_json={"type": "doc", "content": rewritten_content},
            images=result.images,
            warnings=result.warnings,
            parser_used=self.name,
        )

    @staticmethod
    def _strip_front_matter(text: str) -> str:
        """Strip a leading YAML front-matter block if present.

        Front-matter is metadata, not content. Removing it before the
        markdown render avoids the front-matter showing up as a stray
        paragraph in the output.
        """
        if not text.startswith("---"):
            return text
        lines = text.splitlines(keepends=True)
        if len(lines) < 2:
            return text
        # First line is "---"; find the closing "---"
        for idx in range(1, len(lines)):
            if lines[idx].strip() == "---":
                return "".join(lines[idx + 1 :])
        return text
