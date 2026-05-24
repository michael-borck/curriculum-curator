"""Prompts for /generate-video-interaction and /suggest-interaction-points."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.schemas.ai import (
        GenerateVideoInteractionRequest,
        SuggestInteractionPointsRequest,
    )

VIDEO_INTERACTION_SYSTEM = (
    "You are an expert educational video interaction designer. "
    "You create engaging quiz questions that test student comprehension of video "
    "content. Always respond with valid JSON only."
)

SUGGEST_POINTS_SYSTEM = (
    "You are an expert educational video interaction designer. "
    "You analyze video transcripts to identify key learning moments and create "
    "engaging quiz questions. Always respond with valid JSON only."
)


def render_video_interaction_prompt(
    request: GenerateVideoInteractionRequest, context_section: str
) -> str:
    """Render the single video-interaction prompt. ``context_section`` is the
    pre-formatted educational-context block (may be empty)."""
    return f"""Generate a {request.question_type.replace("_", " ")} quiz question based on the following video transcript segment.

Difficulty: {request.difficulty}
{context_section}

Transcript segment:
{request.segment_text}

Return a JSON object with this exact structure:
{{
  "question_text": "The question to ask the student",
  "question_type": "{request.question_type}",
  "options": [
    {{"text": "Option text", "correct": true}},
    {{"text": "Option text", "correct": false}}
  ],
  "feedback": "Feedback shown after answering",
  "explanation": "Detailed explanation of the correct answer",
  "points": 1
}}

Requirements:
- For multiple_choice: provide 4 options, exactly 1 correct
- For true_false: provide 2 options ("True" and "False"), exactly 1 correct
- For multi_select: provide 4 options, 2-3 correct
- For short_answer or fill_in_blank: provide 1 option with the expected answer, marked correct
- The question should test understanding of the transcript content
- Use Australian/British English
- Return ONLY valid JSON, no markdown fences or extra text"""


def render_suggest_points_prompt(
    request: SuggestInteractionPointsRequest,
    context_section: str,
    transcript_lines: str,
) -> str:
    """Render the suggest-interaction-points prompt."""
    return f"""Analyze the following video transcript and identify the {request.max_interactions} best points to insert quiz interactions.

Look for:
- Key concept introductions or transitions
- Important definitions or facts
- Points where student comprehension should be checked
- Natural pauses or topic shifts
{context_section}

Transcript:
{transcript_lines}

Return a JSON object with this exact structure:
{{
  "interactions": [
    {{
      "time": 45.0,
      "question_text": "The question to ask",
      "question_type": "multiple_choice",
      "options": [
        {{"text": "Option A", "correct": true}},
        {{"text": "Option B", "correct": false}},
        {{"text": "Option C", "correct": false}},
        {{"text": "Option D", "correct": false}}
      ],
      "feedback": "Feedback shown after answering",
      "explanation": "Why the correct answer is correct",
      "points": 1
    }}
  ]
}}

Requirements:
- Return at most {request.max_interactions} interactions
- Space them evenly through the transcript
- Use a mix of question types (multiple_choice, true_false, multi_select)
- Each interaction time must fall within the transcript time range
- Use Australian/British English
- Return ONLY valid JSON, no markdown fences or extra text"""
