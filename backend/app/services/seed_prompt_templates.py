"""
Seed system prompt templates into the database.

Idempotent — checks by name before inserting. Called from main.py lifespan.
"""

import json
import logging
import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.models.prompt_template import PromptTemplate

logger = logging.getLogger(__name__)

SYSTEM_TEMPLATES: list[dict[str, Any]] = [
    {
        "name": "Study Guide Creator",
        "description": "Generate a comprehensive study guide from lecture content or a topic.",
        "type": "lecture",
        "template_content": (
            "Create a comprehensive study guide for {{unit_level}} students based on the following content.\n\n"
            "Include:\n"
            "- Key concepts and definitions\n"
            "- Summary of main ideas\n"
            "- Practice questions (mix of recall and application)\n"
            "- Suggested further reading\n\n"
            "Content:\n{{content}}"
        ),
        "variables": [
            {
                "name": "unit_level",
                "label": "Student Level",
                "default": "undergraduate",
            },
            {"name": "content", "label": "Source Content", "default": ""},
        ],
    },
    {
        "name": "3-Level Exit Tickets",
        "description": "Generate differentiated exit ticket questions at three cognitive levels.",
        "type": "quiz",
        "template_content": (
            "Create three exit ticket questions for {{unit_level}} students on the following learning objective.\n\n"
            "Objective: {{objective}}\n\n"
            "Provide one question at each level:\n"
            "1. **Remember/Understand** — recall or explain a key concept\n"
            "2. **Apply/Analyse** — use knowledge in a new context\n"
            "3. **Evaluate/Create** — critically assess or propose something new\n\n"
            "Base the questions on this content:\n{{content}}"
        ),
        "variables": [
            {
                "name": "unit_level",
                "label": "Student Level",
                "default": "undergraduate",
            },
            {"name": "objective", "label": "Learning Objective", "default": ""},
            {"name": "content", "label": "Source Content", "default": ""},
        ],
    },
    {
        "name": "5-in-1 Lesson Workflow",
        "description": "Generate a complete lesson plan with engage, explore, explain, elaborate, and evaluate phases.",
        "type": "lecture",
        "template_content": (
            "Design a 5E lesson workflow for {{unit_level}} students based on this content.\n\n"
            "Structure the lesson as:\n"
            "1. **Engage** (5 min) — hook activity or question\n"
            "2. **Explore** (15 min) — hands-on or discovery activity\n"
            "3. **Explain** (15 min) — direct instruction of key concepts\n"
            "4. **Elaborate** (10 min) — extension or application activity\n"
            "5. **Evaluate** (5 min) — formative check for understanding\n\n"
            "Content:\n{{content}}"
        ),
        "variables": [
            {
                "name": "unit_level",
                "label": "Student Level",
                "default": "undergraduate",
            },
            {"name": "content", "label": "Topic or Content", "default": ""},
        ],
    },
    {
        "name": "Differentiation Pack",
        "description": "Generate tiered activities for mixed-ability classes.",
        "type": "tutorial",
        "template_content": (
            "Create a differentiation pack for teaching {{skill}} to {{unit_level}} students.\n\n"
            "Provide three tiers:\n"
            "- **Foundation** — scaffolded task with guided steps\n"
            "- **Standard** — independent practice with some guidance\n"
            "- **Extension** — open-ended challenge that deepens understanding\n\n"
            "Each tier should have clear instructions and expected outcomes."
        ),
        "variables": [
            {"name": "skill", "label": "Skill or Topic", "default": ""},
            {
                "name": "unit_level",
                "label": "Student Level",
                "default": "undergraduate",
            },
        ],
    },
    {
        "name": "Accessible Text Rewrite",
        "description": "Rewrite content for improved accessibility, clarity, and plain language.",
        "type": "custom",
        "template_content": (
            "Rewrite the following content for {{unit_level}} students, ensuring:\n\n"
            "- Plain language (aim for a reading level suitable for the audience)\n"
            "- Short paragraphs (3-4 sentences max)\n"
            "- Active voice\n"
            "- Technical terms are defined on first use\n"
            "- Key points are highlighted with bold text\n"
            "- Australian/British English spelling\n\n"
            "Content:\n{{content}}"
        ),
        "variables": [
            {
                "name": "unit_level",
                "label": "Student Level",
                "default": "undergraduate",
            },
            {"name": "content", "label": "Content to Rewrite", "default": ""},
        ],
    },
    {
        "name": "Rubric-to-Feedback Generator",
        "description": "Generate personalised feedback from a rubric for student submissions.",
        "type": "rubric",
        "template_content": (
            "Using the rubric below, generate constructive feedback for a student submission.\n\n"
            "The feedback should:\n"
            "- Identify specific strengths with examples\n"
            "- Highlight areas for improvement with actionable suggestions\n"
            "- Use an encouraging, professional tone\n"
            "- Reference rubric criteria by name\n\n"
            "Rubric:\n{{rubric_content}}"
        ),
        "variables": [
            {"name": "rubric_content", "label": "Rubric", "default": ""},
        ],
    },
    {
        "name": "Weekly Announcement Drafter",
        "description": "Draft a weekly LMS announcement with upcoming deadlines and tips.",
        "type": "custom",
        "template_content": (
            "Draft a weekly announcement for {{unit_code}} students.\n\n"
            "Topic this week: {{topic}}\n"
            "Key deadlines: {{deadlines}}\n\n"
            "The announcement should:\n"
            "- Be warm and encouraging\n"
            "- Summarise what was covered and what's ahead\n"
            "- Highlight important deadlines\n"
            "- Include a study tip or motivational note\n"
            "- Be concise (150-250 words)"
        ),
        "variables": [
            {"name": "unit_code", "label": "Unit Code", "default": ""},
            {"name": "topic", "label": "This Week's Topic", "default": ""},
            {"name": "deadlines", "label": "Upcoming Deadlines", "default": ""},
        ],
    },
    {
        "name": "Assessment Brief Clarity Check",
        "description": "Analyse an assessment brief for clarity, completeness, and student-friendliness.",
        "type": "assignment",
        "template_content": (
            "Review the following assessment brief and provide feedback on:\n\n"
            "1. **Clarity** — Are instructions unambiguous?\n"
            "2. **Completeness** — Are all requirements, criteria, and deadlines specified?\n"
            "3. **Student-friendliness** — Is the language accessible? Are expectations clear?\n"
            "4. **Alignment** — Do the tasks match the stated learning outcomes?\n\n"
            "Suggest specific improvements where needed.\n\n"
            "Assessment Brief:\n{{content}}"
        ),
        "variables": [
            {"name": "content", "label": "Assessment Brief", "default": ""},
        ],
    },
    {
        "name": "Lecture Recap Email",
        "description": "Generate a concise recap email summarising key points from a lecture.",
        "type": "lecture",
        "template_content": (
            "Write a brief recap email for students who attended (or missed) a lecture.\n\n"
            "Include:\n"
            "- 3-5 key takeaways\n"
            "- Any important announcements or reminders\n"
            "- Links or resources mentioned (use placeholders)\n"
            "- A question to encourage reflection\n\n"
            "Keep it under 200 words, warm and professional.\n\n"
            "Lecture content:\n{{content}}"
        ),
        "variables": [
            {"name": "content", "label": "Lecture Content or Notes", "default": ""},
        ],
    },
    {
        "name": "Marking Calibration Companion",
        "description": "Help calibrate marking by generating sample responses at different grade levels.",
        "type": "rubric",
        "template_content": (
            "Using the rubric and submission below, generate three sample responses at different quality levels:\n\n"
            "1. **High Distinction** — exemplary response demonstrating mastery\n"
            "2. **Credit** — competent response meeting most criteria\n"
            "3. **Pass** — adequate response meeting minimum requirements\n\n"
            "For each, explain which rubric criteria are met or not met.\n\n"
            "Rubric:\n{{rubric_content}}\n\n"
            "Student Submission:\n{{submission_content}}"
        ),
        "variables": [
            {"name": "rubric_content", "label": "Rubric", "default": ""},
            {
                "name": "submission_content",
                "label": "Student Submission",
                "default": "",
            },
        ],
    },
]


def seed_system_templates(db: Session) -> None:
    """Insert system prompt templates if they don't already exist (idempotent)."""
    existing_names = {
        name
        for (name,) in db.query(PromptTemplate.name)
        .filter(PromptTemplate.is_system.is_(True))
        .all()
    }

    created = 0
    for tmpl in SYSTEM_TEMPLATES:
        if tmpl["name"] in existing_names:
            continue

        template = PromptTemplate(
            id=str(uuid.uuid4()),
            name=tmpl["name"],
            description=tmpl["description"],
            type=tmpl["type"],
            template_content=tmpl["template_content"],
            variables=json.dumps(tmpl["variables"]),
            status="active",
            owner_id=None,
            is_system=True,
            is_public=True,
        )
        db.add(template)
        created += 1

    if created:
        db.commit()
        logger.info(f"Seeded {created} system prompt templates")
    else:
        logger.info("System prompt templates already seeded")
