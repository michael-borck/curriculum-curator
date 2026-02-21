"""
Standalone HTML export service for units.

Exports a Unit as a single HTML file with inline styles, suitable for
opening in a browser or pasting into an LMS content editor.
"""

from sqlalchemy.orm import Session

from app.services.unit_export_data import (
    HTML_TEMPLATE,
    escape_html,
    gather_unit_export_data,
    mermaid_head,
    slugify,
)


def export_unit_html(unit_id: str, db: Session) -> tuple[str, str]:
    """Export a unit as a standalone HTML document.

    Returns (html_string, filename).
    """
    data = gather_unit_export_data(unit_id, db)
    sections: list[str] = []

    # Unit description
    if data.unit.description:
        sections.append(f"<p>{data.unit.description}</p>")

    # Learning outcomes
    if data.learning_outcomes:
        sections.append("<h2>Learning Outcomes</h2>")
        sections.append("<table>")
        sections.append("<tr><th>Code</th><th>Description</th><th>Bloom's Level</th></tr>")
        for lo in data.learning_outcomes:
            code = lo.outcome_code or ""
            sections.append(
                f"<tr><td>{escape_html(code)}</td>"
                f"<td>{escape_html(str(lo.outcome_text))}</td>"
                f"<td>{escape_html(str(lo.bloom_level))}</td></tr>"
            )
        sections.append("</table>")

    # Weekly materials grouped by week
    topic_map = {int(t.week_number): t for t in data.weekly_topics}
    for week_num in sorted(data.materials_by_week.keys()):
        topic = topic_map.get(week_num)
        week_title = f"Week {week_num}"
        if topic and topic.topic_title:
            week_title = f"Week {week_num}: {escape_html(str(topic.topic_title))}"

        sections.append(f"<h2>{week_title}</h2>")
        for mat in data.materials_by_week[week_num]:
            sections.append(f"<h3>{escape_html(str(mat.title))}</h3>")
            content = str(mat.description or "")
            sections.append(content if content else "<p>No content available.</p>")

    # Assessments
    if data.assessments:
        sections.append("<h2>Assessments</h2>")
        sections.append("<table>")
        sections.append(
            "<tr><th>Title</th><th>Type</th><th>Weight</th>"
            "<th>Due Week</th><th>ULOs</th></tr>"
        )
        for assessment in data.assessments:
            # Get mapped ULO codes
            ulo_codes: list[str] = []
            if hasattr(assessment, "learning_outcomes") and assessment.learning_outcomes:
                ulo_codes = [
                    str(ulo.outcome_code or ulo.id)
                    for ulo in assessment.learning_outcomes
                ]
            ulo_str = ", ".join(ulo_codes) if ulo_codes else ""

            due_week = str(assessment.due_week) if assessment.due_week else ""
            sections.append(
                f"<tr><td>{escape_html(str(assessment.title))}</td>"
                f"<td>{escape_html(str(assessment.type))}</td>"
                f"<td>{assessment.weight}%</td>"
                f"<td>{escape_html(due_week)}</td>"
                f"<td>{escape_html(ulo_str)}</td></tr>"
            )
        sections.append("</table>")

    title = f"{data.unit.code} — {data.unit.title}"
    full_content = "\n".join(sections)
    html = HTML_TEMPLATE.format(
        title=escape_html(str(title)),
        content=full_content,
        extra_head=mermaid_head(full_content),
    )

    title_slug = slugify(str(data.unit.title))
    filename = f"{data.unit.code}_{title_slug}.html"
    return html, filename
