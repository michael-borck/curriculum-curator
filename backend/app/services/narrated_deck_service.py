"""Build a self-contained narrated HTML deck from a material.

Slides are split at slide breaks; speaker notes become the narration. Playback
uses the browser's SpeechSynthesis API, so no audio leaves the machine and no
TTS dependency is required. This is the first step before optional MP4 export.
"""

from __future__ import annotations

import json
from typing import Any

from app.services.content_json_renderer import (
    render_content_json,
    strip_speaker_notes,
)
from app.services.slide_splitter import split_at_slide_breaks


def _node_text(node: dict[str, Any]) -> str:
    if node.get("type") == "speakerNotes":
        return ""
    if "text" in node and isinstance(node["text"], str):
        return node["text"]
    children = node.get("content") or []
    return " ".join(filter(None, (_node_text(child) for child in children)))


def _plain_text(segment: dict[str, Any]) -> str:
    return " ".join(
        filter(None, (_node_text(node) for node in segment.get("content") or []))
    ).strip()


def _notes_text(segment: dict[str, Any]) -> str:
    parts: list[str] = []
    for node in segment.get("content") or []:
        if node.get("type") != "speakerNotes":
            continue
        text = " ".join(
            filter(None, (_node_text(child) for child in node.get("content") or []))
        )
        if text.strip():
            parts.append(text.strip())
    return "\n\n".join(parts)


def _title_for(segment: dict[str, Any], index: int, fallback: str) -> str:
    for node in segment.get("content") or []:
        if node.get("type") == "heading":
            text = _node_text(node).strip()
            if text:
                return text
    return f"{fallback} — slide {index + 1}"


def build_narrated_deck(material: Any) -> str:
    """Return a complete HTML document for a narrated material deck."""
    content_json = getattr(material, "content_json", None) or {}
    segments = split_at_slide_breaks(content_json) if content_json else []
    if not segments:
        segments = [{"type": "doc", "content": []}]

    slides: list[dict[str, Any]] = []
    for index, segment in enumerate(segments):
        narration = _notes_text(segment) or _plain_text(segment)
        slides.append(
            {
                "title": _title_for(segment, index, getattr(material, "title", "Deck")),
                "html": render_content_json(strip_speaker_notes(segment)),
                "narration": narration,
            }
        )

    payload = json.dumps(
        {"title": getattr(material, "title", "Narrated deck"), "slides": slides},
        ensure_ascii=False,
    ).replace("</", "<\\/")

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>{getattr(material, "title", "Narrated deck")}</title>
<style>
  :root {{ --bg:#0f172a; --panel:#111827; --text:#e5e7eb; --muted:#94a3b8; --accent:#a78bfa; }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; font-family:system-ui,-apple-system,Segoe UI,sans-serif; background:var(--bg); color:var(--text); min-height:100vh; display:flex; flex-direction:column; }}
  header {{ display:flex; align-items:center; gap:1rem; padding:.75rem 1rem; background:var(--panel); border-bottom:1px solid #1f2937; }}
  header h1 {{ font-size:1rem; margin:0; flex:1; }}
  button {{ background:#1f2937; color:var(--text); border:1px solid #374151; border-radius:.5rem; padding:.4rem .7rem; cursor:pointer; }}
  button:hover {{ border-color:var(--accent); }}
  button:disabled {{ opacity:.45; cursor:default; }}
  main {{ flex:1; display:flex; flex-direction:column; align-items:center; justify-content:center; padding:1.25rem; gap:1rem; }}
  .slide {{ width:min(1100px,100%); aspect-ratio:16/9; background:#fff; color:#111827; border-radius:1rem; padding:clamp(1.2rem,3vw,2.5rem); overflow:auto; box-shadow:0 20px 50px rgba(0,0,0,.35); }}
  .slide h1,.slide h2,.slide h3 {{ line-height:1.15; }}
  .slide img {{ max-width:100%; height:auto; }}
  .narration {{ width:min(1100px,100%); background:var(--panel); border:1px solid #1f2937; border-radius:.75rem; padding:1rem; color:var(--muted); min-height:4.5rem; white-space:pre-wrap; }}
  footer {{ display:flex; align-items:center; gap:.75rem; padding:.75rem 1rem; background:var(--panel); border-top:1px solid #1f2937; }}
  .progress {{ flex:1; height:.4rem; background:#1f2937; border-radius:999px; overflow:hidden; }}
  .progress > div {{ height:100%; width:0; background:var(--accent); transition:width .2s; }}
  .counter {{ font-variant-numeric:tabular-nums; color:var(--muted); font-size:.85rem; }}
</style>
</head>
<body>
<header>
  <h1 id="deck-title"></h1>
  <button id="prev" title="Previous slide">←</button>
  <button id="next" title="Next slide">→</button>
  <button id="play">Play narration</button>
</header>
<main>
  <section id="slide" class="slide" aria-live="polite"></section>
  <section id="narration" class="narration" aria-live="polite"></section>
</main>
<footer>
  <div class="progress"><div id="bar"></div></div>
  <span id="counter" class="counter"></span>
</footer>
<script>
const DECK = {payload};
let index = 0;
let playing = false;
const slideEl = document.getElementById('slide');
const narrationEl = document.getElementById('narration');
const bar = document.getElementById('bar');
const counter = document.getElementById('counter');
const playBtn = document.getElementById('play');
document.getElementById('deck-title').textContent = DECK.title;

function render() {{
  const slide = DECK.slides[index];
  slideEl.innerHTML = slide.html || '<p><em>Empty slide</em></p>';
  narrationEl.textContent = slide.narration || 'No narration for this slide.';
  counter.textContent = (index + 1) + ' / ' + DECK.slides.length;
  bar.style.width = ((index + 1) / DECK.slides.length * 100) + '%';
}}

function stop() {{
  playing = false;
  window.speechSynthesis.cancel();
  playBtn.textContent = 'Play narration';
}}

function speak() {{
  const slide = DECK.slides[index];
  if (!('speechSynthesis' in window) || !slide.narration) {{
    playing = false;
    playBtn.textContent = 'Play narration';
    return;
  }}
  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(slide.narration);
  utterance.rate = 1;
  utterance.onend = () => {{
    if (!playing) return;
    if (index < DECK.slides.length - 1) {{
      index += 1;
      render();
      speak();
    }} else {{
      stop();
    }}
  }};
  window.speechSynthesis.speak(utterance);
}}

document.getElementById('prev').onclick = () => {{
  stop();
  index = Math.max(0, index - 1);
  render();
}};
document.getElementById('next').onclick = () => {{
  stop();
  index = Math.min(DECK.slides.length - 1, index + 1);
  render();
}};
playBtn.onclick = () => {{
  if (playing) {{
    stop();
    return;
  }}
  playing = true;
  playBtn.textContent = 'Pause narration';
  speak();
}};
document.addEventListener('keydown', (event) => {{
  if (event.key === 'ArrowRight' || event.key === ' ') document.getElementById('next').click();
  if (event.key === 'ArrowLeft') document.getElementById('prev').click();
}});
render();
</script>
</body>
</html>"""
