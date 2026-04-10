"""
Server-side ProseMirror/TipTap JSON → HTML / Pandoc-markdown renderer.

Walks the TipTap document tree and produces output strings for export.
No npm dependency — the set of node types is finite and known.

Two render targets are supported:
- "html" (default): produces HTML for editor display and direct HTML export.
- "pandoc": produces HTML with embedded Pandoc fenced divs (e.g. ``::: notes``)
  so the output can be fed to Pandoc as input. Pandoc reads the HTML blocks
  and honours the fenced divs as Pandoc-specific constructs (used to populate
  the PowerPoint speaker notes pane on PPTX export).
"""

import logging
from html import escape
from typing import Any, Literal

logger = logging.getLogger(__name__)

RenderTarget = Literal["html", "pandoc"]


def render_content_json(
    content_json: dict[str, Any], target: RenderTarget = "html"
) -> str:
    """Convert TipTap/ProseMirror JSON to a string in the requested target format.

    Returns empty string for empty or invalid input.
    """
    if not content_json:
        return ""

    top_content = content_json.get("content")
    if not isinstance(top_content, list):
        return ""

    return _render_nodes(top_content, target)


def _render_nodes(nodes: list[dict[str, Any]], target: RenderTarget) -> str:
    """Render a list of ProseMirror nodes to the target format."""
    parts: list[str] = []
    for node in nodes:
        rendered = _render_node(node, target)
        if rendered:
            parts.append(rendered)
    return "".join(parts)


def _render_node(node: dict[str, Any], target: RenderTarget) -> str:  # noqa: PLR0912
    """Render a single ProseMirror node to the target format.

    Node types are dispatched via if/elif chain for clarity — each TipTap
    node type has its own rendering logic.
    """
    node_type = node.get("type", "")
    attrs = node.get("attrs", {})
    content = node.get("content", [])
    children = _render_nodes(content, target) if content else ""

    if node_type == "doc":
        result = children
    elif node_type == "paragraph":
        result = f"<p>{children}</p>"
    elif node_type == "heading":
        level = max(1, min(6, int(attrs.get("level", 1))))
        result = f"<h{level}>{children}</h{level}>"
    elif node_type == "bulletList":
        result = f"<ul>{children}</ul>"
    elif node_type == "orderedList":
        start = attrs.get("start", 1)
        start_attr = f' start="{start}"' if start and int(start) != 1 else ""
        result = f"<ol{start_attr}>{children}</ol>"
    elif node_type == "listItem":
        result = f"<li>{children}</li>"
    elif node_type == "codeBlock":
        result = _render_code_block(attrs, content)
    elif node_type == "blockquote":
        result = f"<blockquote>{children}</blockquote>"
    elif node_type == "table":
        result = f"<table>{children}</table>"
    elif node_type == "tableRow":
        result = f"<tr>{children}</tr>"
    elif node_type in ("tableCell", "tableHeader"):
        result = _render_table_cell(node_type, attrs, children)
    elif node_type == "image":
        result = _render_image(attrs)
    elif node_type == "hardBreak":
        result = "<br>"
    elif node_type == "horizontalRule":
        result = "<hr>"
    elif node_type == "slideBreak":
        result = '<hr data-slide-break="" style="border:none;border-top:2px dashed #94a3b8;margin:1.5rem 0">'
    elif node_type == "speakerNotes":
        result = _render_speaker_notes(children, target)
    elif node_type == "text":
        text = escape(node.get("text", ""))
        result = _apply_marks(text, node.get("marks", []))
    elif node_type in ("mermaid",):
        text = _extract_text(content)
        result = f'<pre class="mermaid">{escape(text)}</pre>'
    elif node_type == "quizQuestion":
        result = _render_quiz_question(attrs)
    elif node_type == "branchingCard":
        result = _render_branching_card(attrs)
    elif node_type == "interactiveVideoEmbed":
        result = _render_interactive_video_embed(attrs)
    elif node_type == "transcriptSegment":
        result = _render_transcript_segment(attrs, children)
    elif node_type == "videoInteraction":
        result = _render_video_interaction(attrs)
    else:
        if node_type:
            logger.warning("Unknown TipTap node type: %s", node_type)
        result = children

    return result


def strip_speaker_notes(content_json: dict[str, Any]) -> dict[str, Any]:
    """Return a copy of content_json with all speakerNotes nodes removed.

    Per ADR-064, speaker notes only belong in PPTX exports (where they
    populate the speaker notes pane). DOCX, PDF, HTML, IMSCC, and SCORM
    exports must strip them before rendering — the slide is for delivery
    in the room, the speaker notes are scaffolding for the educator, and
    student-facing exports should contain neither.

    Walks the document tree and rebuilds it without speakerNotes nodes.
    The original content_json is not mutated.
    """
    if not content_json:
        return content_json

    def _strip(nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        for node in nodes:
            if node.get("type") == "speakerNotes":
                continue
            if "content" in node and isinstance(node["content"], list):
                new_node = {**node, "content": _strip(node["content"])}
                result.append(new_node)
            else:
                result.append(node)
        return result

    top_content = content_json.get("content")
    if not isinstance(top_content, list):
        return content_json

    return {**content_json, "content": _strip(top_content)}


def _render_speaker_notes(children: str, target: RenderTarget) -> str:
    """Render a speakerNotes node.

    HTML target: an <aside> block for editor display and HTML export.
    Pandoc target: a ``::: notes`` fenced div that Pandoc converts to the
    PowerPoint speaker notes pane on PPTX export. The blank lines around the
    fenced div are required by Pandoc's markdown parser to recognise it as a
    block-level construct rather than inline content.

    Per ADR-064 the speakerNotes node only appears in PPTX exports — other
    export targets strip them via ``strip_speaker_notes`` before rendering.
    The HTML target rendering exists for editor display and is also used as
    the inner content of the Pandoc fenced div.
    """
    if target == "pandoc":
        return f"\n\n::: notes\n{children}\n:::\n\n"
    return f'<aside data-type="speaker-notes">{children}</aside>'


def _render_code_block(attrs: dict[str, Any], content: list[dict[str, Any]]) -> str:
    """Render a codeBlock node."""
    lang = attrs.get("language", "")
    text = _extract_text(content)
    if lang == "mermaid":
        return f'<pre class="mermaid">{escape(text)}</pre>'
    lang_attr = f' class="language-{escape(lang)}"' if lang else ""
    return f"<pre><code{lang_attr}>{escape(text)}</code></pre>"


def _render_table_cell(node_type: str, attrs: dict[str, Any], children: str) -> str:
    """Render a tableCell or tableHeader node."""
    tag = "th" if node_type == "tableHeader" else "td"
    colspan = attrs.get("colspan", 1)
    rowspan = attrs.get("rowspan", 1)
    span_attrs = ""
    if colspan and int(colspan) > 1:
        span_attrs += f' colspan="{colspan}"'
    if rowspan and int(rowspan) > 1:
        span_attrs += f' rowspan="{rowspan}"'
    return f"<{tag}{span_attrs}>{children}</{tag}>"


def _render_image(attrs: dict[str, Any]) -> str:
    """Render an image node."""
    src = escape(attrs.get("src", ""))
    alt = escape(attrs.get("alt", ""))
    title = attrs.get("title", "")
    title_attr = f' title="{escape(title)}"' if title else ""
    return f'<img src="{src}" alt="{alt}"{title_attr}>'


def _apply_marks(text: str, marks: list[dict[str, Any]]) -> str:
    """Apply TipTap marks (bold, italic, etc.) to text."""
    for mark in marks:
        mark_type = mark.get("type", "")
        mark_attrs = mark.get("attrs", {})

        if mark_type == "bold":
            text = f"<strong>{text}</strong>"
        elif mark_type == "italic":
            text = f"<em>{text}</em>"
        elif mark_type == "code":
            text = f"<code>{text}</code>"
        elif mark_type == "underline":
            text = f"<u>{text}</u>"
        elif mark_type == "strike":
            text = f"<s>{text}</s>"
        elif mark_type == "highlight":
            text = f"<mark>{text}</mark>"
        elif mark_type == "link":
            href = escape(mark_attrs.get("href", ""))
            target = mark_attrs.get("target", "")
            target_attr = f' target="{escape(target)}"' if target else ""
            text = f'<a href="{href}"{target_attr}>{text}</a>'

    return text


def _extract_text(content: list[dict[str, Any]]) -> str:
    """Extract plain text from a list of nodes (for code blocks)."""
    parts: list[str] = []
    for node in content:
        if node.get("type") == "text":
            parts.append(node.get("text", ""))
        elif "content" in node:
            parts.append(_extract_text(node["content"]))
    return "".join(parts)


def _render_branching_card(attrs: dict[str, Any]) -> str:
    """Render a branchingCard node as a styled HTML block for document exports."""
    card_type = attrs.get("cardType", "content")
    card_title = escape(attrs.get("cardTitle", ""))
    card_content = escape(attrs.get("cardContent", ""))
    choices: list[dict[str, Any]] = attrs.get("choices", [])
    end_score = attrs.get("endScore", 0)
    end_message = attrs.get("endMessage", "")

    type_colors = {
        "content": "#dbeafe",
        "branch": "#fef3c7",
        "ending": "#fce7f3",
    }
    type_labels = {
        "content": "Content",
        "branch": "Branch Point",
        "ending": "Ending",
    }
    bg_color = type_colors.get(card_type, "#f3f4f6")
    type_label = type_labels.get(card_type, card_type)

    parts: list[str] = []
    parts.append(
        f'<div class="branching-card" style="border:1px solid #ddd;'
        f"border-radius:8px;padding:1rem;margin:1rem 0;"
        f'background:{bg_color};">'
    )
    parts.append(
        f'<p style="font-size:0.85rem;color:#666;margin:0 0 0.5rem;">{type_label}</p>'
    )
    if card_title:
        parts.append(f"<p><strong>{card_title}</strong></p>")
    if card_content:
        parts.append(f"<p>{card_content}</p>")

    if card_type == "branch" and choices:
        parts.append("<ul>")
        for choice in choices:
            choice_text = escape(str(choice.get("text", "")))
            parts.append(f"<li>{choice_text}</li>")
        parts.append("</ul>")

    if card_type == "ending":
        parts.append(
            f'<p style="font-size:0.85rem;color:#666;">Score: {end_score}</p>'
        )
        if end_message:
            parts.append(
                f'<p style="font-style:italic;color:#555;">{escape(end_message)}</p>'
            )

    parts.append("</div>")
    return "".join(parts)


def _render_quiz_question(attrs: dict[str, Any]) -> str:
    """Render a quizQuestion node as a styled HTML block for document exports."""
    question_text = escape(attrs.get("questionText", ""))
    question_type = attrs.get("questionType", "multiple_choice")
    options: list[dict[str, Any]] = attrs.get("options", [])
    feedback = attrs.get("feedback", "")
    points = attrs.get("points", 1.0)

    type_labels = {
        "multiple_choice": "Multiple Choice",
        "true_false": "True/False",
        "multi_select": "Multiple Select",
        "short_answer": "Short Answer",
        "fill_in_blank": "Fill in the Blank",
    }
    type_label = type_labels.get(question_type, question_type)

    parts: list[str] = []
    parts.append(
        '<div class="quiz-question" style="border:1px solid #ddd;'
        "border-radius:8px;padding:1rem;margin:1rem 0;"
        'background:#f9f9fb;">'
    )
    parts.append(
        f'<p style="font-size:0.85rem;color:#666;margin:0 0 0.5rem;">'
        f"{type_label} &middot; {points} pt{'s' if float(points) != 1.0 else ''}</p>"
    )
    parts.append(f"<p><strong>{question_text}</strong></p>")

    if options:
        parts.append("<ol>")
        for opt in options:
            opt_text = escape(str(opt.get("text", "")))
            is_correct = opt.get("correct", False)
            marker = ' <span style="color:green;">&#10003;</span>' if is_correct else ""
            parts.append(f"<li>{opt_text}{marker}</li>")
        parts.append("</ol>")

    if feedback:
        parts.append(
            f'<p style="font-style:italic;color:#555;margin-top:0.5rem;">'
            f"Feedback: {escape(feedback)}</p>"
        )

    parts.append("</div>")
    return "".join(parts)


def _render_interactive_video_embed(attrs: dict[str, Any]) -> str:
    """Render an interactiveVideoEmbed node as a link for document exports."""
    url = escape(attrs.get("url", ""))
    title = escape(attrs.get("title", "Interactive Video"))
    platform = escape(attrs.get("platform", ""))
    return (
        f'<div class="video-embed" style="border:1px solid #ddd;'
        f'border-radius:8px;padding:1rem;margin:1rem 0;background:#f0f0ff;">'
        f'<p style="font-size:0.85rem;color:#666;margin:0 0 0.5rem;">'
        f"Interactive Video ({platform})</p>"
        f'<p><a href="{url}">{title or url}</a></p>'
        f"</div>"
    )


def _format_timestamp(seconds: float) -> str:
    """Format seconds as mm:ss."""
    mins = int(seconds) // 60
    secs = int(seconds) % 60
    return f"{mins}:{secs:02d}"


def _render_transcript_segment(attrs: dict[str, Any], children: str) -> str:
    """Render a transcriptSegment node for document exports."""
    start = float(attrs.get("startTime", 0))
    end = float(attrs.get("endTime", 0))
    ts = f"[{_format_timestamp(start)}\u2013{_format_timestamp(end)}]"
    return (
        f'<div class="transcript-segment" style="margin:0.25rem 0;color:#666;">'
        f'<span style="font-family:monospace;font-size:0.8rem;color:#999;">{ts}</span> '
        f"{children}</div>"
    )


def _render_video_interaction(attrs: dict[str, Any]) -> str:
    """Render a videoInteraction node — reuses quiz rendering with a timestamp header."""
    time_val = float(attrs.get("time", 0))
    pause = attrs.get("pause", True)
    ts = _format_timestamp(time_val)
    pause_label = " (pauses)" if pause else ""

    parts: list[str] = []
    parts.append(
        '<div class="video-interaction" style="border:1px solid #93c5fd;'
        "border-left:4px solid #3b82f6;border-radius:8px;padding:1rem;"
        'margin:1rem 0;background:#eff6ff;">'
    )
    parts.append(
        f'<p style="font-size:0.85rem;color:#3b82f6;margin:0 0 0.5rem;">'
        f"Interaction @ {ts}{pause_label}</p>"
    )

    question_text = escape(attrs.get("questionText", ""))
    question_type = attrs.get("questionType", "multiple_choice")
    options: list[dict[str, Any]] = attrs.get("options", [])
    feedback = attrs.get("feedback", "")
    points = attrs.get("points", 1.0)

    type_labels = {
        "multiple_choice": "Multiple Choice",
        "true_false": "True/False",
        "multi_select": "Multiple Select",
        "short_answer": "Short Answer",
        "fill_in_blank": "Fill in the Blank",
    }
    type_label = type_labels.get(question_type, question_type)

    parts.append(
        f'<p style="font-size:0.85rem;color:#666;margin:0 0 0.5rem;">'
        f"{type_label} &middot; {points} pt{'s' if float(points) != 1.0 else ''}</p>"
    )
    parts.append(f"<p><strong>{question_text}</strong></p>")

    if options:
        parts.append("<ol>")
        for opt in options:
            opt_text = escape(str(opt.get("text", "")))
            is_correct = opt.get("correct", False)
            marker = ' <span style="color:green;">&#10003;</span>' if is_correct else ""
            parts.append(f"<li>{opt_text}{marker}</li>")
        parts.append("</ol>")

    if feedback:
        parts.append(
            f'<p style="font-style:italic;color:#555;margin-top:0.5rem;">'
            f"Feedback: {escape(feedback)}</p>"
        )

    parts.append("</div>")
    return "".join(parts)
