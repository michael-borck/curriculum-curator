"""Tests for AI video interaction generation endpoints.

These endpoints now route through ``llm_service.generate_structured_content``
(strict Pydantic + retry), so tests mock that seam and supply the parsed model.
Fence-stripping / JSON parsing is the engine's responsibility and is covered by
the engine's own tests, not here.
"""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.schemas.ai import (
    GenerateVideoInteractionOption,
    GenerateVideoInteractionResponse,
    SuggestedInteraction,
    SuggestInteractionPointsResponse,
)


@pytest.fixture
def mock_generate_structured():
    """Patch generate_structured_content to return a controlled (model, error)."""
    with patch(
        "app.api.routes.ai.llm_service.generate_structured_content",
        new_callable=AsyncMock,
    ) as mock:
        yield mock


# =============================================================================
# POST /ai/generate-video-interaction
# =============================================================================


def test_generate_interaction_valid_json(
    client: TestClient, mock_generate_structured: AsyncMock
):
    """Engine returns a validated model → serialized into the response schema."""
    mock_generate_structured.return_value = (
        GenerateVideoInteractionResponse(
            question_text="What is the main topic discussed?",
            question_type="multiple_choice",
            options=[
                GenerateVideoInteractionOption(text="Machine learning", correct=True),
                GenerateVideoInteractionOption(text="Web development", correct=False),
                GenerateVideoInteractionOption(text="Database design", correct=False),
                GenerateVideoInteractionOption(text="Networking", correct=False),
            ],
            feedback="The segment focuses on machine learning concepts.",
            explanation="The speaker introduces ML fundamentals in this segment.",
            points=1,
        ),
        None,
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
    assert data["points"] == 1

    # The prompt passed to the engine includes the segment text.
    prompt = mock_generate_structured.call_args.kwargs["prompt"]
    assert "machine learning" in prompt


def test_generate_interaction_with_design_context(
    client: TestClient, mock_generate_structured: AsyncMock
):
    """When unit_id is provided, design context is injected into the prompt."""
    mock_generate_structured.return_value = (
        GenerateVideoInteractionResponse(
            question_text="Q?",
            question_type="multiple_choice",
            options=[GenerateVideoInteractionOption(text="A", correct=True)],
            feedback="F",
            explanation="E",
            points=1,
        ),
        None,
    )

    with patch(
        "app.services.curriculum_context.get_design_context",
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
    prompt = mock_generate_structured.call_args.kwargs["prompt"]
    assert "constructive alignment" in prompt


def test_generate_interaction_invalid_question_type(
    client: TestClient, mock_generate_structured: AsyncMock
):
    """Invalid question type returns 400 before any LLM call."""
    resp = client.post(
        "/api/ai/generate-video-interaction",
        json={
            "segmentText": "Some text.",
            "questionType": "essay",
        },
    )

    assert resp.status_code == 400
    assert "Invalid question_type" in resp.json()["detail"]
    mock_generate_structured.assert_not_called()


def test_generate_interaction_llm_error_returns_502(
    client: TestClient, mock_generate_structured: AsyncMock
):
    """Engine error (None, message) surfaces as a 502."""
    mock_generate_structured.return_value = (None, "No AI provider configured")

    resp = client.post(
        "/api/ai/generate-video-interaction",
        json={"segmentText": "x", "questionType": "multiple_choice"},
    )

    assert resp.status_code == 502


# =============================================================================
# POST /ai/suggest-interaction-points
# =============================================================================


def test_suggest_points_valid_json(
    client: TestClient, mock_generate_structured: AsyncMock
):
    """Engine returns a validated model → serialized into the response schema."""
    mock_generate_structured.return_value = (
        SuggestInteractionPointsResponse(
            interactions=[
                SuggestedInteraction(
                    time=30.0,
                    question_text="What concept was just introduced?",
                    question_type="multiple_choice",
                    options=[
                        GenerateVideoInteractionOption(text="Recursion", correct=True),
                        GenerateVideoInteractionOption(text="Iteration", correct=False),
                    ],
                    feedback="Recursion was the topic.",
                    explanation="The lecturer defined recursion.",
                    points=1,
                ),
                SuggestedInteraction(
                    time=90.0,
                    question_text="True or false: recursion requires a base case?",
                    question_type="true_false",
                    options=[
                        GenerateVideoInteractionOption(text="True", correct=True),
                        GenerateVideoInteractionOption(text="False", correct=False),
                    ],
                    feedback="Every recursive function needs a base case.",
                    explanation="Without a base case, recursion would be infinite.",
                    points=1,
                ),
            ]
        ),
        None,
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
    client: TestClient, mock_generate_structured: AsyncMock
):
    """max_interactions value appears in the LLM prompt."""
    mock_generate_structured.return_value = (
        SuggestInteractionPointsResponse(interactions=[]),
        None,
    )

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
    prompt = mock_generate_structured.call_args.kwargs["prompt"]
    assert "7" in prompt
