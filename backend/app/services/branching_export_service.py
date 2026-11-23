"""Story health checks and playable exports for branching materials."""

from __future__ import annotations

import json
from html import escape
from typing import Any


def extract_cards(content_json: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not content_json:
        return []
    return [
        node
        for node in content_json.get("content") or []
        if node.get("type") == "branchingCard"
    ]


def story_health(cards: list[dict[str, Any]]) -> dict[str, Any]:
    """Return structural problems that would break a playable story."""
    ids = [str(card.get("attrs", {}).get("cardId") or "") for card in cards]
    id_set = set(ids)
    duplicates = sorted({card_id for card_id in ids if ids.count(card_id) > 1})
    broken: list[str] = []
    dead_ends: list[str] = []
    empty_choices: list[str] = []

    for card in cards:
        attrs = card.get("attrs") or {}
        card_id = str(attrs.get("cardId") or "")
        card_type = attrs.get("cardType") or "content"
        choices = attrs.get("choices") or []
        if card_type != "ending" and not choices:
            dead_ends.append(card_id)
        for choice in choices:
            target = str(choice.get("targetCardId") or "")
            text = str(choice.get("text") or "").strip()
            if not text:
                empty_choices.append(card_id)
            if target and target not in id_set:
                broken.append(f"{card_id} → {target}")
            if not target:
                broken.append(f"{card_id} has a choice with no target")

    endings = [card for card in cards if (card.get("attrs") or {}).get("cardType") == "ending"]
    orphans: list[str] = []
    if cards:
        reachable = {str((cards[0].get("attrs") or {}).get("cardId") or "")}
        changed = True
        while changed:
            changed = False
            for card in cards:
                card_id = str((card.get("attrs") or {}).get("cardId") or "")
                if card_id not in reachable:
                    continue
                for choice in (card.get("attrs") or {}).get("choices") or []:
                    target = str(choice.get("targetCardId") or "")
                    if target and target not in reachable:
                        reachable.add(target)
                        changed = True
        orphans = [card_id for card_id in ids if card_id and card_id not in reachable]

    return {
        "cards": len(cards),
        "endings": len(endings),
        "dead_ends": dead_ends,
        "orphans": orphans,
        "broken_targets": broken,
        "empty_choices": sorted(set(empty_choices)),
        "duplicate_ids": duplicates,
        "ok": not (dead_ends or orphans or broken or empty_choices or duplicates)
        and len(endings) >= 1,
    }


def build_playable_html(material: Any) -> str:
    cards = extract_cards(getattr(material, "content_json", None))
    payload = json.dumps(
        {"title": getattr(material, "title", "Branching story"), "cards": cards},
        ensure_ascii=False,
    ).replace("</", "<\\/")
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>{escape(getattr(material, "title", "Branching story"))}</title>
<style>
  :root {{ --bg:#0f172a; --panel:#111827; --text:#e5e7eb; --muted:#94a3b8; --accent:#a78bfa; }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; min-height:100vh; display:flex; align-items:center; justify-content:center; padding:1.5rem; background:var(--bg); color:var(--text); font-family:system-ui,-apple-system,Segoe UI,sans-serif; }}
  .card {{ width:min(720px,100%); background:var(--panel); border:1px solid #1f2937; border-radius:1rem; padding:1.5rem; box-shadow:0 24px 60px rgba(0,0,0,.35); }}
  h1 {{ font-size:1.2rem; margin:0 0 .25rem; }}
  .meta {{ color:var(--muted); font-size:.8rem; margin-bottom:1rem; }}
  .content {{ white-space:pre-wrap; line-height:1.55; margin-bottom:1.25rem; }}
  button.choice {{ display:block; width:100%; text-align:left; margin:.5rem 0; padding:.75rem .9rem; background:#1f2937; color:var(--text); border:1px solid #374151; border-radius:.6rem; cursor:pointer; }}
  button.choice:hover {{ border-color:var(--accent); }}
  .feedback {{ color:var(--accent); font-size:.9rem; margin-top:.5rem; }}
  .ending {{ margin-top:1rem; padding:1rem; background:#1e1b4b; border:1px solid #4c1d95; border-radius:.75rem; }}
  .actions {{ margin-top:1.25rem; display:flex; gap:.5rem; }}
  .actions button {{ background:#111827; color:var(--muted); border:1px solid #374151; border-radius:.5rem; padding:.4rem .7rem; cursor:pointer; }}
</style>
</head>
<body>
<main class="card">
  <h1 id="title"></h1>
  <div id="meta" class="meta"></div>
  <div id="content" class="content"></div>
  <div id="choices"></div>
  <div id="ending"></div>
  <div class="actions">
    <button id="restart">Restart</button>
    <span id="steps" class="meta" style="margin:0 0 0 auto"></span>
  </div>
</main>
<script>
const STORY = {payload};
const byId = Object.fromEntries(STORY.cards.map(card => [card.attrs.cardId, card]));
let current = STORY.cards[0]?.attrs?.cardId;
let steps = 0;
const titleEl = document.getElementById('title');
const metaEl = document.getElementById('meta');
const contentEl = document.getElementById('content');
const choicesEl = document.getElementById('choices');
const endingEl = document.getElementById('ending');
const stepsEl = document.getElementById('steps');
titleEl.textContent = STORY.title;

function render() {{
  const card = byId[current];
  if (!card) {{
    contentEl.textContent = 'This story is incomplete.';
    choicesEl.innerHTML = '';
    return;
  }}
  const attrs = card.attrs || {{}};
  const type = attrs.cardType || 'content';
  metaEl.textContent = type === 'ending' ? 'Ending' : type === 'branch' ? 'Decision point' : 'Scene';
  contentEl.textContent = attrs.cardContent || attrs.cardTitle || '';
  choicesEl.innerHTML = '';
  endingEl.innerHTML = '';
  stepsEl.textContent = 'Steps: ' + steps;

  if (type === 'ending') {{
    const message = attrs.endMessage || 'The end.';
    const threshold = Number(attrs.stepThreshold || 0);
    let text = message;
    if (threshold > 0) {{
      text = steps <= threshold
        ? (attrs.endMessageEfficient || message)
        : (attrs.endMessageThorough || message);
    }}
    const box = document.createElement('div');
    box.className = 'ending';
    box.textContent = text + (attrs.endScore ? ' (score ' + attrs.endScore + ')' : '');
    endingEl.appendChild(box);
  }}

  for (const choice of attrs.choices || []) {{
    const button = document.createElement('button');
    button.className = 'choice';
    button.textContent = choice.text || '(continue)';
    button.onclick = () => {{
      steps += 1;
      current = choice.targetCardId;
      render();
    }};
    choicesEl.appendChild(button);
  }}
}}
document.getElementById('restart').onclick = () => {{
  current = STORY.cards[0]?.attrs?.cardId;
  steps = 0;
  render();
}};
render();
</script>
</body>
</html>"""


def build_ink_source(material: Any) -> str:
    cards = extract_cards(getattr(material, "content_json", None))
    if not cards:
        return ""
    start = str((cards[0].get("attrs") or {}).get("cardId") or "start")
    lines = [f"-> {start}", ""]
    for card in cards:
        attrs = card.get("attrs") or {}
        card_id = str(attrs.get("cardId") or "card")
        title = str(attrs.get("cardTitle") or "").strip()
        content = str(attrs.get("cardContent") or "").strip()
        type_ = attrs.get("cardType") or "content"
        lines.append(f"=== {card_id} ===")
        if type_ == "ending":
            lines.append(f"# {title or 'Ending'}")
        elif title:
            lines.append(f"# {title}")
        if content:
            lines.append(content)
        choices = attrs.get("choices") or []
        if type_ == "ending":
            message = str(attrs.get("endMessage") or "The end.").strip()
            if message:
                lines.append(message)
            lines.append("-> END")
        else:
            for choice in choices:
                text = str(choice.get("text") or "Continue").strip()
                target = str(choice.get("targetCardId") or "").strip()
                if target:
                    lines.append(f"+ [{text}] -> {target}")
        lines.append("")
    return "\n".join(lines)
