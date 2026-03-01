"""Tests for AI video interaction generation endpoints."""

import json
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def mock_generate_text():
    """Patch llm_service.generate_text to return a controlled string."""
    with patch(
        "app.api.routes.ai.llm_service.generate_text",
        new_callable=AsyncMock,
    ) as mock:
        yield mock


# =============================================================================
# POST /ai/generate-video-interaction
# =============================================================================


def test_generate_interaction_valid_json(
    client: TestClient, mock_generate_text: AsyncMock
):
    """LLM returns valid JSON → parsed into response schema."""
    mock_generate_text.return_value = json.dumps(
        {
            "question_text": "What is the main topic discussed?",
            "question_type": "multiple_choice",
            "options": [
                {"text": "Machine learning", "correct": True},
                {"text": "Web development", "correct": False},
                {"text": "Database design", "correct": False},
                {"text": "Networking", "correct": False},
            ],
            "feedback": "The segment focuses on machine learning concepts.",
            "explanation": "The speaker introduces ML fundamentals in this segment.",
            "points": 1,
        }
    )

    resp = client.post(
        "/api/ai/generate-video-interaction",
        json={
            "segmentText": "Today we will discuss machine learning and its applications.",
            "questionType": "multiple_choice",
            "difficulty": "medium",
        },
    )

    assert resp.status_code == 200
    data = resp.json()
    assert data["questionText"] == "What is the main topic discussed?"
    assert data["questionType"] == "multiple_choice"
    assert len(data["options"]) == 4
    assert data["feedback"] != ""
    assert data["explanation"] != ""
    assert data["points"] == 1

    # Verify the prompt contains the segment text
    call_kwargs = mock_generate_text.call_args
    assert "machine learning" in call_kwargs.kwargs.get(
        "prompt", call_kwargs.args[0] if call_kwargs.args else ""
    )


def test_generate_interaction_strips_markdown_fences(
    client: TestClient, mock_generate_text: AsyncMock
):
    """LLM wraps response in ```json ... ``` → still parsed correctly."""
    inner = json.dumps(
        {
            "question_text": "What is discussed?",
            "question_type": "true_false",
            "options": [
                {"text": "True", "correct": True},
                {"text": "False", "correct": False},
            ],
            "feedback": "Correct!",
            "explanation": "The statement is true.",
            "points": 1,
        }
    )
    mock_generate_text.return_value = f"```json\n{inner}\n```"

    resp = client.post(
        "/api/ai/generate-video-interaction",
        json={
            "segmentText": "Neural networks mimic the human brain.",
            "questionType": "true_false",
        },
    )

    assert resp.status_code == 200
    assert resp.json()["questionText"] == "What is discussed?"


def test_generate_interaction_with_design_context(
    client: TestClient, mock_generate_text: AsyncMock
):
    """When unit_id is provided, design context is injected into the prompt."""
    mock_generate_text.return_value = json.dumps(
        {
            "question_text": "Q?",
            "question_type": "multiple_choice",
            "options": [{"text": "A", "correct": True}],
            "feedback": "F",
            "explanation": "E",
            "points": 1,
        }
    )

    with patch(
        "app.api.routes.ai.get_design_context",
        new_callable=AsyncMock,
        return_value="Learning Design: constructive alignment required",
    ):
        resp = client.post(
            "/api/ai/generate-video-interaction",
            json={
                "segmentText": "Some transcript text here.",
                "questionType": "multiple_choice",
                "unitId": "unit-123",
            },
        )

    assert resp.status_code == 200
    prompt = mock_generate_text.call_args.kwargs.get(
        "prompt", mock_generate_text.call_args.args[0] if mock_generate_text.call_args.args else ""
    )
    assert "constructive alignment" in prompt


def test_generate_interaction_invalid_question_type(
    client: TestClient, mock_generate_text: AsyncMock
):
    """Invalid question type returns 400."""
    resp = client.post(
        "/api/ai/generate-video-interaction",
        json={
            "segmentText": "Some text.",
            "questionType": "essay",
        },
    )

    assert resp.status_code == 400
    assert "Invalid question_type" in resp.json()["detail"]
    mock_generate_text.assert_not_called()


# =============================================================================
# POST /ai/suggest-interaction-points
# =============================================================================


def test_suggest_points_valid_json(
    client: TestClient, mock_generate_text: AsyncMock
):
    """LLM returns valid JSON array → parsed into response schema."""
    mock_generate_text.return_value = json.dumps(
        {
            "interactions": [
                {
                    "time": 30.0,
                    "question_text": "What concept was just introduced?",
                    "question_type": "multiple_choice",
                    "options": [
                        {"text": "Recursion", "correct": True},
                        {"text": "Iteration", "correct": False},
                    ],
                    "feedback": "Recursion was the topic.",
                    "explanation": "The lecturer defined recursion.",
                    "points": 1,
                },
                {
                    "time": 90.0,
                    "question_text": "True or false: recursion requires a base case?",
                    "question_type": "true_false",
                    "options": [
                        {"text": "True", "correct": True},
                        {"text": "False", "correct": False},
                    ],
                    "feedback": "Every recursive function needs a base case.",
                    "explanation": "Without a base case, recursion would be infinite.",
                    "points": 1,
                },
            ]
        }
    )

    resp = client.post(
        "/api/ai/suggest-interaction-points",
        json={
            "transcriptSegments": [
                {"start": 0.0, "end": 30.0, "text": "Today we introduce recursion."},
                {
                    "start": 30.0,
                    "end": 60.0,
                    "text": "Recursion is when a function calls itself.",
                },
                {
                    "start": 60.0,
                    "end": 120.0,
                    "text": "Every recursive function needs a base case to terminate.",
                },
            ],
            "maxInteractions": 3,
        },
    )

    assert resp.status_code == 200
    data = resp.json()
    assert len(data["interactions"]) == 2
    assert data["interactions"][0]["time"] == 30.0
    assert data["interactions"][1]["questionType"] == "true_false"


def test_suggest_points_max_interactions_in_prompt(
    client: TestClient, mock_generate_text: AsyncMock
):
    """max_interactions value appears in the LLM prompt."""
    mock_generate_text.return_value = json.dumps({"interactions": []})

    resp = client.post(
        "/api/ai/suggest-interaction-points",
        json={
            "transcriptSegments": [
                {"start": 0.0, "end": 10.0, "text": "Hello world."},
            ],
            "maxInteractions": 7,
        },
    )

    assert resp.status_code == 200
    prompt = mock_generate_text.call_args.kwargs.get(
        "prompt", mock_generate_text.call_args.args[0] if mock_generate_text.call_args.args else ""
    )
    assert "7" in prompt


def test_suggest_points_strips_markdown_fences(
    client: TestClient, mock_generate_text: AsyncMock
):
    """Markdown fences around JSON are stripped before parsing."""
    inner = json.dumps(
        {
            "interactions": [
                {
                    "time": 15.0,
                    "question_text": "What is X?",
                    "question_type": "multiple_choice",
                    "options": [{"text": "A", "correct": True}],
                    "feedback": "F",
                    "explanation": "E",
                    "points": 1,
                }
            ]
        }
    )
    mock_generate_text.return_value = f"```json\n{inner}\n```"

    resp = client.post(
        "/api/ai/suggest-interaction-points",
        json={
            "transcriptSegments": [
                {"start": 0.0, "end": 30.0, "text": "Some content."},
            ],
        },
    )

    assert resp.status_code == 200
    assert len(resp.json()["interactions"]) == 1
