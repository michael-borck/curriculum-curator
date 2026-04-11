"""
Structural HTML parser — converts an HTML document into TipTap content_json.

Phase 2 default for ``.html`` and ``.htm`` files. Walks the DOM with
BeautifulSoup and maps each element to its TipTap node equivalent.

Per ADR-038 the parser deliberately discards anything that isn't content:
scripts, styles, iframes, forms, and other non-textual decoration.
Per ADR-061 the parser emits warnings for ambiguous or unsupported
constructs rather than silently dropping them.

reveal.js conventions are honoured for free: ``<section>`` boundaries
become ``slideBreak`` nodes, and ``<aside class="notes">`` becomes a
structured ``speakerNotes`` node — so a reveal.js deck imports as a
sliced material with notes intact, exactly like a PPTX.

Used as the underlying engine for ``md_structural`` (Markdown converts
to HTML via the ``markdown`` library, then runs through here) and for
``docx_pandoc`` indirectly (DOCX → markdown → here).
"""

from __future__ import annotations

import base64
import logging
import re
from typing import Any, ClassVar
from urllib.parse import unquote

from bs4 import BeautifulSoup, NavigableString, Tag

from app.services.material_parsers.base import (
    ExtractedImage,
    MaterialParser,
    MaterialParseResult,
)

logger = logging.getLogger(__name__)


# HTML elements we drop entirely (along with their contents). Anything not
# in this set and not explicitly handled below is treated as a transparent
# wrapper — its children are processed but the wrapper itself is dropped.
_DROPPED_TAGS = frozenset(
    {
        "script",
        "style",
        "iframe",
        "form",
        "input",
        "button",
        "noscript",
        "head",
        "meta",
        "link",
        "title",
    }
)

_HEADING_TAGS = frozenset({"h1", "h2", "h3", "h4", "h5", "h6"})

_INLINE_MARK_TAGS = {
    "strong": "bold",
    "b": "bold",
    "em": "italic",
    "i": "italic",
    "u": "underline",
    "s": "strike",
    "strike": "strike",
    "del": "strike",
    "code": "code",
    "mark": "highlight",
}


class HtmlStructuralParser(MaterialParser):
    """Convert an HTML document into TipTap content_json."""

    name: ClassVar[str] = "html_structural"
    display_name: ClassVar[str] = "HTML (structural)"
    description: ClassVar[str] = (
        "Default HTML importer. Walks the DOM and maps headings, paragraphs, "
        "lists, tables, blockquotes, code, images, and inline marks to "
        "editable structured content. Recognises reveal.js section/notes "
        "conventions for slide decks. Discards scripts, styles, iframes, "
        "forms, and other non-content."
    )
    supported_formats: ClassVar[list[str]] = ["html", "htm"]
    requires_ai: ClassVar[bool] = False

    async def parse(
        self,
        file_content: bytes,
        filename: str,
        *,
        user_context: dict[str, object] | None = None,
    ) -> MaterialParseResult:
        _ = user_context

        text = file_content.decode("utf-8", errors="replace")
        soup = BeautifulSoup(text, "html.parser")

        # Title preference: <title> > first <h1> > filename stem
        doc_title: str | None = None
        title_tag = soup.find("title")
        if title_tag and title_tag.get_text(strip=True):
            doc_title = title_tag.get_text(strip=True)

        # Walk the body if present, otherwise the whole soup
        root = soup.body or soup

        warnings: list[str] = []
        images: list[ExtractedImage] = []
        image_counter = [0]

        nodes = self._walk_block_children(
            root, warnings=warnings, images=images, image_counter=image_counter
        )

        # Fallback title from first heading
        if doc_title is None:
            first_heading = next(
                (n for n in nodes if n.get("type") == "heading"), None
            )
            if first_heading:
                doc_title = self._node_text(first_heading)

        # Last-resort title: filename stem
        if not doc_title:
            from pathlib import Path  # noqa: PLC0415

            doc_title = Path(filename).stem or "Untitled"

        return MaterialParseResult(
            title=doc_title,
            content_json={"type": "doc", "content": nodes},
            images=images,
            warnings=warnings,
            parser_used=self.name,
        )

    # ------------------------------------------------------------------
    # Block-level walking
    # ------------------------------------------------------------------

    def _walk_block_children(
        self,
        parent: Tag,
        *,
        warnings: list[str],
        images: list[ExtractedImage],
        image_counter: list[int],
    ) -> list[dict[str, Any]]:
        """Walk a parent element and emit block-level TipTap nodes for its children."""
        nodes: list[dict[str, Any]] = []
        for child in parent.children:
            block_nodes = self._element_to_block_nodes(
                child,
                warnings=warnings,
                images=images,
                image_counter=image_counter,
            )
            nodes.extend(block_nodes)
        return self._coalesce_inline_into_paragraphs(nodes)

    def _element_to_block_nodes(  # noqa: PLR0911, PLR0912
        self,
        element: Any,
        *,
        warnings: list[str],
        images: list[ExtractedImage],
        image_counter: list[int],
    ) -> list[dict[str, Any]]:
        """Convert a single DOM element/text node into zero or more block-level nodes."""
        if isinstance(element, NavigableString):
            text = str(element)
            # Bare text at the block level becomes a transient inline node;
            # the coalescer will wrap consecutive inline nodes into a paragraph
            if text.strip():
                return [{"_inline": True, "node": {"type": "text", "text": text}}]
            return []

        if not isinstance(element, Tag):
            return []

        tag_name = (element.name or "").lower()

        if tag_name in _DROPPED_TAGS:
            return []

        if tag_name in _HEADING_TAGS:
            level = int(tag_name[1])
            inline = self._inline_children(element, images, image_counter)
            return [
                {
                    "type": "heading",
                    "attrs": {"level": level},
                    "content": inline or [{"type": "text", "text": ""}],
                }
            ]

        if tag_name == "p":
            inline = self._inline_children(element, images, image_counter)
            if not inline:
                return []
            return [{"type": "paragraph", "content": inline}]

        if tag_name == "ul":
            return [self._list_to_node(element, ordered=False, warnings=warnings,
                                       images=images, image_counter=image_counter)]

        if tag_name == "ol":
            return [self._list_to_node(element, ordered=True, warnings=warnings,
                                       images=images, image_counter=image_counter)]

        if tag_name == "blockquote":
            inner = self._walk_block_children(
                element,
                warnings=warnings,
                images=images,
                image_counter=image_counter,
            )
            if not inner:
                return []
            return [{"type": "blockquote", "content": inner}]

        if tag_name == "pre":
            # <pre><code class="language-X">…</code></pre> is the canonical
            # markdown→HTML codeblock shape; bare <pre> is also accepted
            code_elem = element.find("code")
            language = ""
            if code_elem and isinstance(code_elem, Tag):
                cls = code_elem.get("class") or []
                for c in cls:
                    if c.startswith("language-"):
                        language = c.removeprefix("language-")
                        break
                code_text = code_elem.get_text()
            else:
                code_text = element.get_text()
            attrs: dict[str, Any] = {}
            if language:
                attrs["language"] = language
            return [
                {
                    "type": "codeBlock",
                    "attrs": attrs,
                    "content": [{"type": "text", "text": code_text}],
                }
            ]

        if tag_name == "table":
            return [self._table_to_node(element)]

        if tag_name in ("hr",):
            return [{"type": "horizontalRule"}]

        if tag_name == "section":
            # reveal.js convention: top-level <section> elements are slides.
            # Emit a slideBreak before each section after the first, then
            # walk the section's contents inline. The caller (parser top
            # level) is responsible for stripping a leading slideBreak if
            # the document opens with one.
            inner = self._walk_block_children(
                element,
                warnings=warnings,
                images=images,
                image_counter=image_counter,
            )
            return [{"type": "slideBreak"}, *inner]

        if tag_name == "aside":
            classes = element.get("class") or []
            if "notes" in classes:
                # reveal.js speaker notes convention
                inner = self._walk_block_children(
                    element,
                    warnings=warnings,
                    images=images,
                    image_counter=image_counter,
                )
                if not inner:
                    return []
                return [{"type": "speakerNotes", "content": inner}]
            # Other asides → transparent wrapper
            return self._walk_block_children(
                element,
                warnings=warnings,
                images=images,
                image_counter=image_counter,
            )

        if tag_name == "img":
            return [
                {
                    "_inline": True,
                    "node": self._image_to_node(element, images, image_counter),
                }
            ]

        if tag_name == "br":
            return [{"_inline": True, "node": {"type": "hardBreak"}}]

        # Inline mark wrappers and links: emit as inline nodes for the coalescer
        if tag_name in _INLINE_MARK_TAGS or tag_name == "a":
            inline = self._inline_children(element, images, image_counter)
            if not inline:
                return []
            mark_type = _INLINE_MARK_TAGS.get(tag_name)
            if mark_type:
                return [
                    {"_inline": True, "node": n}
                    for n in self._apply_mark_to_text_nodes(inline, mark_type)
                ]
            if tag_name == "a":
                href = str(element.get("href", ""))
                marked = self._apply_link_to_text_nodes(inline, href)
                return [{"_inline": True, "node": n} for n in marked]

        # Unknown / transparent wrappers (div, span, article, main, header,
        # footer, nav, etc.) — descend into children but emit no wrapper.
        return self._walk_block_children(
            element,
            warnings=warnings,
            images=images,
            image_counter=image_counter,
        )

    @staticmethod
    def _coalesce_inline_into_paragraphs(
        mixed: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Wrap consecutive inline nodes (marked with ``_inline``) in paragraphs.

        Block-level nodes pass through unchanged. Inline nodes that bubbled
        up from elements like <img>, <br>, or unwrapped text inside a
        transparent container get gathered into a paragraph so the resulting
        content_json is schema-valid.
        """
        result: list[dict[str, Any]] = []
        pending_inline: list[dict[str, Any]] = []

        def _flush() -> None:
            if pending_inline:
                result.append({"type": "paragraph", "content": pending_inline.copy()})
                pending_inline.clear()

        for entry in mixed:
            if entry.get("_inline"):
                pending_inline.append(entry["node"])
            else:
                _flush()
                result.append(entry)
        _flush()
        return result

    # ------------------------------------------------------------------
    # Inline-level walking
    # ------------------------------------------------------------------

    def _inline_children(
        self,
        parent: Tag,
        images: list[ExtractedImage],
        image_counter: list[int],
    ) -> list[dict[str, Any]]:
        """Walk a parent for inline children only (text nodes + marks + images)."""
        nodes: list[dict[str, Any]] = []
        for child in parent.children:
            nodes.extend(self._inline_element(child, images, image_counter))
        return nodes

    def _inline_element(  # noqa: PLR0911
        self,
        element: Any,
        images: list[ExtractedImage],
        image_counter: list[int],
    ) -> list[dict[str, Any]]:
        if isinstance(element, NavigableString):
            text = str(element)
            if text:
                return [{"type": "text", "text": text}]
            return []

        if not isinstance(element, Tag):
            return []

        tag_name = (element.name or "").lower()

        if tag_name in _DROPPED_TAGS:
            return []

        if tag_name == "br":
            return [{"type": "hardBreak"}]

        if tag_name == "img":
            return [self._image_to_node(element, images, image_counter)]

        if tag_name in _INLINE_MARK_TAGS:
            inner = self._inline_children(element, images, image_counter)
            return self._apply_mark_to_text_nodes(inner, _INLINE_MARK_TAGS[tag_name])

        if tag_name == "a":
            inner = self._inline_children(element, images, image_counter)
            href = str(element.get("href", ""))
            return self._apply_link_to_text_nodes(inner, href)

        # Transparent inline wrapper (span, etc.) — descend
        return self._inline_children(element, images, image_counter)

    @staticmethod
    def _apply_mark_to_text_nodes(
        nodes: list[dict[str, Any]], mark_type: str
    ) -> list[dict[str, Any]]:
        """Add a mark to every text node in a list (recursive into nested marks)."""
        result: list[dict[str, Any]] = []
        for n in nodes:
            if n.get("type") == "text":
                marks: list[dict[str, Any]] = list(n.get("marks", []))
                if not any(m.get("type") == mark_type for m in marks):
                    marks.append({"type": mark_type})
                new_node = dict(n)
                new_node["marks"] = marks
                result.append(new_node)
            else:
                result.append(n)
        return result

    @staticmethod
    def _apply_link_to_text_nodes(
        nodes: list[dict[str, Any]], href: str
    ) -> list[dict[str, Any]]:
        if not href:
            return nodes
        result: list[dict[str, Any]] = []
        for n in nodes:
            if n.get("type") == "text":
                marks: list[dict[str, Any]] = list(n.get("marks", []))
                marks.append({"type": "link", "attrs": {"href": href}})
                new_node = dict(n)
                new_node["marks"] = marks
                result.append(new_node)
            else:
                result.append(n)
        return result

    # ------------------------------------------------------------------
    # Lists
    # ------------------------------------------------------------------

    def _list_to_node(
        self,
        element: Tag,
        *,
        ordered: bool,
        warnings: list[str],
        images: list[ExtractedImage],
        image_counter: list[int],
    ) -> dict[str, Any]:
        items: list[dict[str, Any]] = []
        for child in element.children:
            if isinstance(child, Tag) and child.name == "li":
                # Each list item's content can be a mix of inline text and
                # nested blocks (e.g. nested lists). Walk as block children
                # and let the coalescer handle inline runs.
                inner = self._walk_block_children(
                    child,
                    warnings=warnings,
                    images=images,
                    image_counter=image_counter,
                )
                if not inner:
                    inner = [{"type": "paragraph", "content": []}]
                items.append({"type": "listItem", "content": inner})
        node_type = "orderedList" if ordered else "bulletList"
        return {"type": node_type, "content": items}

    # ------------------------------------------------------------------
    # Tables
    # ------------------------------------------------------------------

    def _table_to_node(self, element: Tag) -> dict[str, Any]:
        rows: list[dict[str, Any]] = []
        # Walk thead and tbody if present, otherwise just direct tr children
        row_elements: list[Tag] = []
        thead = element.find("thead")
        if thead and isinstance(thead, Tag):
            row_elements.extend(
                tr for tr in thead.find_all("tr") if isinstance(tr, Tag)
            )
        tbody = element.find("tbody")
        if tbody and isinstance(tbody, Tag):
            row_elements.extend(
                tr for tr in tbody.find_all("tr") if isinstance(tr, Tag)
            )
        if not row_elements:
            row_elements = [
                tr
                for tr in element.find_all("tr", recursive=False)
                if isinstance(tr, Tag)
            ]
            if not row_elements:
                row_elements = [
                    tr for tr in element.find_all("tr") if isinstance(tr, Tag)
                ]

        for row in row_elements:
            cells: list[dict[str, Any]] = []
            for cell in row.find_all(["td", "th"], recursive=False):
                if not isinstance(cell, Tag):
                    continue
                cell_type = "tableHeader" if cell.name == "th" else "tableCell"
                inner = self._walk_block_children(
                    cell,
                    warnings=[],
                    images=[],
                    image_counter=[0],
                )
                if not inner:
                    inner = [{"type": "paragraph", "content": []}]
                cells.append({"type": cell_type, "content": inner})
            if cells:
                rows.append({"type": "tableRow", "content": cells})

        return {"type": "table", "content": rows}

    # ------------------------------------------------------------------
    # Images
    # ------------------------------------------------------------------

    def _image_to_node(
        self,
        element: Tag,
        images: list[ExtractedImage],
        image_counter: list[int],
    ) -> dict[str, Any]:
        src = str(element.get("src", ""))
        alt = str(element.get("alt", ""))

        # data: URL → extract bytes into ExtractedImage and rewrite src to
        # a placeholder filename. The persistence layer will resolve the
        # placeholder to a canonical URL after the material is created.
        if src.startswith("data:"):
            extracted = self._extract_data_url(src, image_counter[0])
            if extracted is not None:
                images.append(extracted)
                src = extracted.filename
                image_counter[0] += 1

        node: dict[str, Any] = {
            "type": "image",
            "attrs": {"src": src, "alt": alt},
        }
        title = element.get("title")
        if title:
            node["attrs"]["title"] = str(title)
        return node

    @staticmethod
    def _extract_data_url(data_url: str, idx: int) -> ExtractedImage | None:
        """Parse a ``data:`` URL and return an ExtractedImage, or None on failure."""
        match = re.match(r"data:([^;,]+)(;base64)?,(.*)$", data_url, re.DOTALL)
        if not match:
            return None
        mime = match.group(1) or "application/octet-stream"
        is_base64 = bool(match.group(2))
        payload = match.group(3)

        try:
            data = (
                base64.b64decode(payload)
                if is_base64
                else unquote(payload).encode("utf-8")
            )
        except Exception:
            return None

        ext_map = {
            "image/png": "png",
            "image/jpeg": "jpg",
            "image/gif": "gif",
            "image/svg+xml": "svg",
            "image/webp": "webp",
        }
        ext = ext_map.get(mime, "bin")
        return ExtractedImage(
            filename=f"embedded-{idx}.{ext}",
            data=data,
            mime_type=mime,
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _node_text(node: dict[str, Any]) -> str:
        if node.get("type") == "text":
            return str(node.get("text", ""))
        return "".join(
            HtmlStructuralParser._node_text(child)
            for child in node.get("content", [])
            if isinstance(child, dict)
        )
