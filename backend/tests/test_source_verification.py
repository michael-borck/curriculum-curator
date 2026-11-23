"""Reading-list source verification."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, patch

if TYPE_CHECKING:
    from fastapi.testclient import TestClient

from app.services.source_verification_service import normalise_doi


def test_normalise_doi() -> None:
    assert normalise_doi("https://doi.org/10.1000/xyz123") == "10.1000/xyz123"
    assert normalise_doi("doi:10.1000/xyz123") == "10.1000/xyz123"
    assert normalise_doi("not-a-doi") is None


def test_verify_endpoint_batches_results(client: TestClient) -> None:
    fake = AsyncMock(
        side_effect=[
            {"title": "A", "status": "verified", "reason": "ok"},
            {"title": "B", "status": "not_found", "reason": "404"},
        ]
    )
    with patch("app.api.routes.research.verify_source", fake):
        response = client.post(
            "/api/research/verify",
            json={
                "items": [
                    {"title": "A", "doi": "10.1000/abc"},
                    {"title": "B", "url": "https://example.com/missing"},
                ]
            },
        )
    assert response.status_code == 200, response.text
    results = response.json()["results"]
    assert [item["status"] for item in results] == ["verified", "not_found"]
