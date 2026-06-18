"""Standalone interactive HTML export for branching scenarios (story 19B.1).

Emits a single self-contained HTML file — inline CSS and a small vanilla-JS
runtime, with the branching card graph embedded as JSON. It opens in any
browser, embeds in an LMS, or is shareable as a link, with no dependencies
and no H5P player required.

Mirrors h5p_branching_service's builder shape but produces HTML text rather
than a .h5p package. Card navigation is by id, so multiple choices may
converge on the same card (19A.6) and a choice may target an ending card.
"""

from __future__ import annotations

import json
from typing import Any


class InteractiveHtmlBuilder:
    """Build a self-contained interactive HTML page from branching cards."""

    def build(self, cards: list[dict[str, Any]], title: str) -> str:
        """Return one HTML document string for the branching scenario."""
        scenario = self._build_scenario(cards, title)
        # Embed JSON safely inside a <script> tag: a literal "</script>" (or
        # any "</") in the data would otherwise close the tag early.
        scenario_json = json.dumps(scenario, ensure_ascii=False).replace("</", "<\\/")
        safe_title = self._escape_html(title)
        return _TEMPLATE.replace("__TITLE__", safe_title).replace(
            "__SCENARIO__", scenario_json
        )

    def _build_scenario(
        self, cards: list[dict[str, Any]], title: str
    ) -> dict[str, Any]:
        card_map: dict[str, dict[str, Any]] = {}
        first_id = ""
        for card in cards:
            card_id = str(card.get("cardId", ""))
            if not card_id:
                continue
            if not first_id:
                first_id = card_id
            choices = [
                {
                    "text": str(ch.get("text", "")),
                    "target": str(ch.get("targetCardId", "")),
                    "feedback": str(ch.get("feedback", "")),
                }
                for ch in card.get("choices", [])
                if isinstance(ch, dict)
            ]
            card_map[card_id] = {
                "type": str(card.get("cardType", "content")),
                "title": str(card.get("cardTitle", "")),
                "content": str(card.get("cardContent", "")),
                "choices": choices,
                "endMessage": str(card.get("endMessage", "")),
                "endScore": int(card.get("endScore", 0) or 0),
            }
        return {
            "title": title,
            "startCardId": first_id,
            "cards": card_map,
        }

    @staticmethod
    def _escape_html(text: str) -> str:
        return (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
        )


# The runtime sets all author text via textContent (never innerHTML), so
# scenario data can't inject markup. white-space: pre-wrap preserves the
# line breaks authors typed into card content.
_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__</title>
<style>
  :root { --accent: #6d28d9; }
  body { font-family: system-ui, sans-serif; max-width: 640px; margin: 2rem auto;
         padding: 0 1rem; line-height: 1.6; color: #1f2937; }
  h1 { font-size: 1.25rem; color: #111827; }
  #card-title { font-size: 1.1rem; font-weight: 600; margin: 1.5rem 0 0.5rem; }
  #card-content { white-space: pre-wrap; }
  .choice { display: block; width: 100%; text-align: left; margin: 0.5rem 0;
            padding: 0.75rem 1rem; border: 1px solid #d1d5db; border-radius: 0.5rem;
            background: #fff; cursor: pointer; font: inherit; }
  .choice:hover { border-color: var(--accent); background: #f5f3ff; }
  .feedback { background: #f5f3ff; border-left: 3px solid var(--accent);
              padding: 0.5rem 0.75rem; margin: 0.75rem 0; white-space: pre-wrap; }
  .ending { background: #ecfdf5; border: 1px solid #a7f3d0; border-radius: 0.5rem;
            padding: 1rem; white-space: pre-wrap; }
  button.primary { margin-top: 1rem; padding: 0.6rem 1.1rem; border: none;
                   border-radius: 0.5rem; background: var(--accent); color: #fff;
                   font: inherit; cursor: pointer; }
  .muted { color: #6b7280; font-size: 0.85rem; }
</style>
</head>
<body>
<h1>__TITLE__</h1>
<div id="scenario"></div>
<script>
const SCENARIO = __SCENARIO__;

function el(tag, opts) {
  const node = document.createElement(tag);
  if (opts && opts.text) node.textContent = opts.text;
  if (opts && opts.className) node.className = opts.className;
  return node;
}

function render(cardId) {
  const root = document.getElementById('scenario');
  root.innerHTML = '';
  const card = SCENARIO.cards[cardId];
  if (!card) {
    root.appendChild(el('p', { text: 'This path is incomplete.', className: 'muted' }));
    return;
  }

  if (card.title) {
    const t = el('div', { text: card.title });
    t.id = 'card-title';
    root.appendChild(t);
  }
  if (card.content) {
    const c = el('div', { text: card.content });
    c.id = 'card-content';
    root.appendChild(c);
  }

  const isEnding = card.type === 'ending';
  const hasChoices = card.choices && card.choices.length > 0;

  if (isEnding || !hasChoices) {
    const box = el('div', { className: 'ending' });
    box.textContent = card.endMessage || (isEnding ? 'The end.' : 'End of this path.');
    root.appendChild(box);
    root.appendChild(restartButton());
    return;
  }

  card.choices.forEach(function (choice) {
    const btn = el('button', { text: choice.text || '(continue)', className: 'choice' });
    btn.addEventListener('click', function () { choose(choice); });
    root.appendChild(btn);
  });
}

function choose(choice) {
  if (choice.feedback) {
    const root = document.getElementById('scenario');
    root.innerHTML = '';
    root.appendChild(el('div', { text: choice.feedback, className: 'feedback' }));
    const cont = el('button', { text: 'Continue', className: 'primary' });
    cont.addEventListener('click', function () { render(choice.target); });
    root.appendChild(cont);
  } else {
    render(choice.target);
  }
}

function restartButton() {
  const btn = el('button', { text: 'Start again', className: 'primary' });
  btn.addEventListener('click', function () { render(SCENARIO.startCardId); });
  return btn;
}

render(SCENARIO.startCardId);
</script>
</body>
</html>"""


interactive_html_builder = InteractiveHtmlBuilder()
"""Module-level singleton, matching the other export builders."""
