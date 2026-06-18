"""Helpers for AI structure recovery (story 6.16).

Two pure transforms with no I/O:
- ``flatten_content_to_text``: collapse a TipTap content_json document to
  the plain text an LLM should re-structure.
- ``structured_document_to_content_json``: map the LLM's validated
  ``StructuredDocument`` back into TipTap content_json.

Kept separate from the route so both directions are unit-testable without
a database or an LLM.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.schemas.ai import StructuredDocument


def _node_text(node: dict[str, Any]) -> str:
    """Recursively gather the text of a single ProseMirror node."""
    if "text" in node:
        return str(node["text"])
    children = node.get("content") or []
    parts = [_node_text(child) for child in children]
    return " ".join(p for p in parts if p)


def flatten_content_to_text(content_json: dict[str, Any] | None) -> str:
    """Collapse a content_json document to newline-separated block text.

    Each top-level block becomes one line; list items are kept on their own
    lines. Empty blocks are dropped. This is the input the restructure
    prompt re-segments.
    """
    if not content_json:
        return ""
    top = content_json.get("content")
    if not isinstance(top, list):
        return ""

    lines: list[str] = []
    for node in top:
        node_type = node.get("type")
        if node_type in ("bulletList", "orderedList"):
            for item in node.get("content") or []:
                text = _node_text(item).strip()
                if text:
                    lines.append(text)
        else:
            text = _node_text(node).strip()
            if text:
                lines.append(text)
    return "\n".join(lines)


def _text_node(text: str) -> dict[str, Any]:
    return {"type": "text", "text": text}


def _paragraph(text: str) -> dict[str, Any]:
    return {"type": "paragraph", "content": [_text_node(text)] if text else []}


def _list(kind: str, items: list[str]) -> dict[str, Any]:
    list_type = "bulletList" if kind == "bullet_list" else "orderedList"
    return {
        "type": list_type,
        "content": [
            {"type": "listItem", "content": [_paragraph(item)]}
            for item in items
            if item.strip()
        ],
    }


def structured_document_to_content_json(
    doc: StructuredDocument,
) -> tuple[dict[str, Any], int, int, int]:
    """Convert a validated StructuredDocument to content_json.

    Returns ``(content_json, heading_count, list_count, paragraph_count)``.
    Unknown block kinds degrade to paragraphs so a stray LLM kind never
    drops content.
    """
    nodes: list[dict[str, Any]] = []
    headings = 0
    lists = 0
    paragraphs = 0

    for block in doc.blocks:
        kind = block.kind
        if kind == "heading" and block.text.strip():
            nodes.append(
                {
                    "type": "heading",
                    "attrs": {"level": block.level},
                    "content": [_text_node(block.text.strip())],
                }
            )
            headings += 1
        elif kind in ("bullet_list", "ordered_list"):
            list_node = _list(kind, block.items)
            if list_node["content"]:
                nodes.append(list_node)
                lists += 1
        else:
            text = block.text.strip()
            if text:
                nodes.append(_paragraph(text))
                paragraphs += 1

    # Never return an empty document — a no-op result is better than wiping
    # the material's content on an unexpectedly empty LLM response.
    if not nodes:
        nodes.append(_paragraph(""))

    return {"type": "doc", "content": nodes}, headings, lists, paragraphs
