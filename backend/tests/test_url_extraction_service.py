"""
Tests for URL extraction service.

Mocks aiohttp (external boundary). Tests:
- Single URL extraction
- Batch with one failure
- Content type classification heuristics
"""

from unittest.mock import AsyncMock, patch

import pytest

from app.services.url_extraction_service import UrlExtractionService
from app.services.web_search_service import WebSearchError


# ──────────────────────────────────────────────────────────────
# Content type classification
# ──────────────────────────────────────────────────────────────


class TestContentClassification:
    def setup_method(self):
        self.service = UrlExtractionService()

    def test_youtube_is_video(self):
        assert (
            self.service._classify_content_type("https://youtube.com/watch?v=abc", "")
            == "video"
        )

    def test_vimeo_is_video(self):
        assert (
            self.service._classify_content_type("https://vimeo.com/12345", "")
            == "video"
        )

    def test_doi_url_is_paper(self):
        assert (
            self.service._classify_content_type("https://doi.org/10.1234/test", "")
            == "paper"
        )

    def test_arxiv_is_paper(self):
        assert (
            self.service._classify_content_type("https://arxiv.org/abs/2024.12345", "")
            == "paper"
        )

    def test_content_with_doi_is_paper(self):
        content = "This paper (doi: 10.1234/test) presents findings..."
        assert (
            self.service._classify_content_type("https://example.com/paper", content)
            == "paper"
        )

    def test_edu_with_syllabus_signals(self):
        content = (
            "Unit outline with learning outcomes and assessment details for week 1"
        )
        assert (
            self.service._classify_content_type(
                "https://university.edu.au/unit", content
            )
            == "syllabus"
        )

    def test_edu_without_syllabus_is_paper(self):
        assert (
            self.service._classify_content_type(
                "https://university.edu/research", "some content"
            )
            == "paper"
        )

    def test_medium_is_blog(self):
        assert (
            self.service._classify_content_type("https://medium.com/article", "content")
            == "blog"
        )

    def test_unknown_default(self):
        assert (
            self.service._classify_content_type(
                "https://example.com", "generic content"
            )
            == "unknown"
        )

    def test_strong_syllabus_signals_override(self):
        content = "syllabus week 1 week 2 learning outcomes assessment credit points"
        assert (
            self.service._classify_content_type("https://example.com", content)
            == "syllabus"
        )


# ──────────────────────────────────────────────────────────────
# URL extraction
# ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_extract_single_url_with_summarize():
    service = UrlExtractionService()

    with (
        patch.object(
            service,
            "_extract_single",
        ) as mock_extract,
    ):
        from app.services.url_extraction_service import ExtractedUrl

        mock_extract.return_value = ExtractedUrl(
            url="https://example.com/paper",
            title="Test Paper",
            summary="A great paper about testing",
            key_points=["Point 1", "Point 2"],
            academic_score=0.8,
            content_type="paper",
        )

        results = await service.extract_urls(
            urls=["https://example.com/paper"],
            summarize=True,
        )

    assert len(results) == 1
    assert results[0].url == "https://example.com/paper"
    assert results[0].summary == "A great paper about testing"
    assert results[0].content_type == "paper"
    assert results[0].error is None


@pytest.mark.asyncio
async def test_extract_batch_with_failure():
    """One URL failing shouldn't block others."""
    service = UrlExtractionService()

    from app.services.url_extraction_service import ExtractedUrl

    async def mock_extract(url, summarize, purpose):
        if "bad" in url:
            return ExtractedUrl(url=url, error="Connection refused")
        return ExtractedUrl(
            url=url,
            title="Good Page",
            summary="Content here",
            academic_score=0.5,
            content_type="unknown",
        )

    with patch.object(service, "_extract_single", side_effect=mock_extract):
        results = await service.extract_urls(
            urls=["https://good.com", "https://bad.com/broken", "https://good2.com"],
            summarize=True,
        )

    assert len(results) == 3
    assert results[0].error is None
    assert results[1].error == "Connection refused"
    assert results[2].error is None


@pytest.mark.asyncio
async def test_extract_without_summarize():
    service = UrlExtractionService()

    with (
        patch(
            "app.services.url_extraction_service.web_search_service.fetch_page_content",
            new_callable=AsyncMock,
            return_value="Some page content about research methodology",
        ),
        patch(
            "app.services.url_extraction_service.web_search_service._calculate_academic_score",
            return_value=0.6,
        ),
    ):
        results = await service.extract_urls(
            urls=["https://example.com"],
            summarize=False,
        )

    assert len(results) == 1
    assert results[0].academic_score == 0.6
    assert results[0].summary is None
    assert results[0].error is None


@pytest.mark.asyncio
async def test_extract_handles_web_search_error():
    service = UrlExtractionService()

    with patch(
        "app.services.url_extraction_service.web_search_service.summarize_url",
        new_callable=AsyncMock,
        side_effect=WebSearchError("Timeout"),
    ):
        results = await service.extract_urls(
            urls=["https://slow-site.com"],
            summarize=True,
        )

    assert len(results) == 1
    assert results[0].error is not None
    assert "Timeout" in results[0].error


# ──────────────────────────────────────────────────────────────
# HTTP endpoint test
# ──────────────────────────────────────────────────────────────


def test_extract_urls_endpoint(client):
    """Test POST /api/research/extract-urls via TestClient."""
    from app.services.url_extraction_service import ExtractedUrl

    mock_results = [
        ExtractedUrl(
            url="https://example.com/paper",
            title="Test Paper",
            summary="Summary",
            key_points=["Point 1"],
            academic_score=0.7,
            content_type="paper",
        )
    ]

    with patch(
        "app.services.url_extraction_service.url_extraction_service.extract_urls",
        new_callable=AsyncMock,
        return_value=mock_results,
    ):
        response = client.post(
            "/api/research/extract-urls",
            json={"urls": ["https://example.com/paper"]},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["successful"] == 1
    assert data["failed"] == 0
