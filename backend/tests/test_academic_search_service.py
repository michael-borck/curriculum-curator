"""
Tests for academic search service, search router, and research endpoints.

Mocks aiohttp responses (external boundary). Tests:
- OpenAlex result normalization
- Semantic Scholar result normalization
- Deduplication by DOI
- Search router tier selection
- Fallback behavior
"""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.academic_search_service import (
    AcademicSearchService,
    AcademicWork,
    OpenAlexClient,
    SemanticScholarClient,
    _reconstruct_abstract,
)
from app.services.search_router import SearchRouter, SearchTier


# ──────────────────────────────────────────────────────────────
# Helper: mock aiohttp response
# ──────────────────────────────────────────────────────────────


def _mock_aiohttp_response(status: int, json_data: dict):
    """Create a mock aiohttp response with async context manager support."""
    response = AsyncMock()
    response.status = status
    response.json = AsyncMock(return_value=json_data)

    session = AsyncMock()
    session.get = MagicMock(return_value=response)

    # Make response usable as async context manager
    response.__aenter__ = AsyncMock(return_value=response)
    response.__aexit__ = AsyncMock(return_value=False)

    # Make session usable as async context manager
    session.__aenter__ = AsyncMock(return_value=session)
    session.__aexit__ = AsyncMock(return_value=False)

    return session


# ──────────────────────────────────────────────────────────────
# Abstract reconstruction
# ──────────────────────────────────────────────────────────────


def test_reconstruct_abstract_none():
    assert _reconstruct_abstract(None) is None


def test_reconstruct_abstract_empty():
    assert _reconstruct_abstract({}) is None


def test_reconstruct_abstract_basic():
    inverted = {"Hello": [0], "world": [1], "test": [2]}
    assert _reconstruct_abstract(inverted) == "Hello world test"


def test_reconstruct_abstract_out_of_order():
    inverted = {"the": [0, 3], "cat": [1], "sat": [2], "mat": [4]}
    result = _reconstruct_abstract(inverted)
    assert result == "the cat sat the mat"


# ──────────────────────────────────────────────────────────────
# OpenAlex client
# ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_openalex_search_works():
    mock_data = {
        "results": [
            {
                "display_name": "Test Paper",
                "doi": "https://doi.org/10.1234/test",
                "id": "https://openalex.org/W123",
                "abstract_inverted_index": {"Hello": [0], "world": [1]},
                "authorships": [
                    {"author": {"display_name": "Alice Smith"}},
                    {"author": {"display_name": "Bob Jones"}},
                ],
                "publication_year": 2024,
                "cited_by_count": 42,
                "primary_location": {"source": {"display_name": "Nature Education"}},
            }
        ]
    }

    with patch("aiohttp.ClientSession") as mock_session_cls:
        session = _mock_aiohttp_response(200, mock_data)
        mock_session_cls.return_value = session

        client = OpenAlexClient()
        results = await client.search_works("machine learning", max_results=5)

    assert len(results) == 1
    work = results[0]
    assert work.title == "Test Paper"
    assert work.doi == "10.1234/test"
    assert work.abstract == "Hello world"
    assert work.authors == ["Alice Smith", "Bob Jones"]
    assert work.publication_year == 2024
    assert work.citation_count == 42
    assert work.source_name == "Nature Education"
    assert work.provider == "openalex"


@pytest.mark.asyncio
async def test_openalex_handles_error():
    with patch("aiohttp.ClientSession") as mock_session_cls:
        session = _mock_aiohttp_response(500, {})
        mock_session_cls.return_value = session

        client = OpenAlexClient()
        results = await client.search_works("test")

    assert results == []


# ──────────────────────────────────────────────────────────────
# Semantic Scholar client
# ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_semantic_scholar_search():
    mock_data = {
        "data": [
            {
                "title": "Deep Learning Survey",
                "url": "https://www.semanticscholar.org/paper/abc",
                "abstract": "A comprehensive survey",
                "authors": [{"name": "Carol Davis"}],
                "year": 2023,
                "venue": "ICML",
                "citationCount": 150,
                "externalIds": {"DOI": "10.5678/survey"},
            }
        ]
    }

    with patch("aiohttp.ClientSession") as mock_session_cls:
        session = _mock_aiohttp_response(200, mock_data)
        mock_session_cls.return_value = session

        client = SemanticScholarClient()
        results = await client.search_papers("deep learning", max_results=5)

    assert len(results) == 1
    work = results[0]
    assert work.title == "Deep Learning Survey"
    assert work.doi == "10.5678/survey"
    assert work.abstract == "A comprehensive survey"
    assert work.authors == ["Carol Davis"]
    assert work.publication_year == 2023
    assert work.citation_count == 150
    assert work.provider == "semantic_scholar"


# ──────────────────────────────────────────────────────────────
# Deduplication
# ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_deduplication_by_doi():
    service = AcademicSearchService()

    work_a = AcademicWork(
        title="Paper A",
        url="https://a.com",
        doi="10.1234/same",
        citation_count=10,
        provider="openalex",
    )
    work_b = AcademicWork(
        title="Paper A (duplicate)",
        url="https://b.com",
        doi="10.1234/same",
        citation_count=50,  # Higher citations — should win
        provider="semantic_scholar",
    )
    work_c = AcademicWork(
        title="Paper C (unique)",
        url="https://c.com",
        doi="10.9999/unique",
        citation_count=5,
        provider="openalex",
    )

    with (
        patch.object(service.openalex, "search_works", return_value=[work_a, work_c]),
        patch.object(service.semantic_scholar, "search_papers", return_value=[work_b]),
        patch.object(service.crossref, "search_works", return_value=[]),
    ):
        results = await service.search("test")

    # Should have 2 results: the higher-cited duplicate + unique
    assert len(results) == 2
    # Sorted by citation count descending
    assert results[0].citation_count == 50
    assert results[1].citation_count == 5


@pytest.mark.asyncio
async def test_works_without_doi_not_deduplicated():
    service = AcademicSearchService()

    work_a = AcademicWork(
        title="No DOI Paper 1", url="https://a.com", doi=None, provider="openalex"
    )
    work_b = AcademicWork(
        title="No DOI Paper 2",
        url="https://b.com",
        doi=None,
        provider="semantic_scholar",
    )

    with (
        patch.object(service.openalex, "search_works", return_value=[work_a]),
        patch.object(service.semantic_scholar, "search_papers", return_value=[work_b]),
        patch.object(service.crossref, "search_works", return_value=[]),
    ):
        results = await service.search("test")

    assert len(results) == 2


# ──────────────────────────────────────────────────────────────
# AcademicWork → SearchResult conversion
# ──────────────────────────────────────────────────────────────


def test_to_search_result_high_citations():
    work = AcademicWork(
        title="Popular Paper",
        url="https://doi.org/10.1234/pop",
        citation_count=200,
        authors=["Alice"],
        publication_year=2024,
        provider="openalex",
    )
    result = work.to_search_result()
    assert result.title == "Popular Paper"
    assert result.academic_score == 1.0


def test_to_search_result_no_citations():
    work = AcademicWork(
        title="New Paper",
        url="https://example.com",
        citation_count=0,
        provider="semantic_scholar",
    )
    result = work.to_search_result()
    assert result.academic_score == 0.3  # Base score for academic sources


# ──────────────────────────────────────────────────────────────
# Search router — tier selection
# ──────────────────────────────────────────────────────────────


def test_tier_availability_default():
    router = SearchRouter()
    tiers = router.get_available_tiers()

    available = {t.tier: t.available for t in tiers}
    assert available[SearchTier.ACADEMIC] is True
    assert available[SearchTier.LLM_NATIVE] is False
    # Tier 3 is always available via DuckDuckGo fallback
    assert available[SearchTier.GENERAL_WEB] is True


def test_tier_availability_with_api_keys():
    router = SearchRouter()
    tiers = router.get_available_tiers(
        user_settings={"searchApiKeys": {"braveSearchApiKey": "test-key"}}
    )

    available = {t.tier: t.available for t in tiers}
    assert available[SearchTier.GENERAL_WEB] is True


@pytest.mark.asyncio
async def test_search_router_defaults_to_academic():
    router = SearchRouter()

    with patch.object(router, "_search_academic", return_value=[]) as mock_academic:
        _results, tier = await router.search("test query")

    assert tier == SearchTier.ACADEMIC
    mock_academic.assert_called_once_with("test query", 20, None)


@pytest.mark.asyncio
async def test_search_router_preferred_tier():
    router = SearchRouter()

    # Prefer SearXNG but it's available via system config
    with (
        patch.object(router, "_search_searxng", return_value=[]) as mock_searxng,
        patch(
            "app.core.config.settings",
            MagicMock(SEARXNG_URL="http://localhost:8080"),
        ),
    ):
        _results, tier = await router.search("test", preferred_tier=4)

    assert tier == SearchTier.SEARXNG
    mock_searxng.assert_called_once()


# ──────────────────────────────────────────────────────────────
# Search router — excluded domains filter
# ──────────────────────────────────────────────────────────────


def _mk_result(url: str):
    from app.services.web_search_service import SearchResult

    return SearchResult(title=url, url=url)


def test_filter_excluded_drops_system_defaults():
    results = [
        _mk_result("https://www.youtube.com/watch?v=abc"),
        _mk_result("https://arxiv.org/abs/1234.5678"),
        _mk_result("https://m.youtube.com/watch?v=xyz"),
        _mk_result("https://notyoutube.com/legit"),
    ]
    filtered = SearchRouter._filter_excluded(results, None)
    urls = [r.url for r in filtered]
    assert "https://arxiv.org/abs/1234.5678" in urls
    assert "https://notyoutube.com/legit" in urls
    assert not any("//www.youtube.com" in u or "//m.youtube.com" in u for u in urls)


def test_filter_excluded_honours_user_settings():
    results = [
        _mk_result("https://example.com/post"),
        _mk_result("https://keep.me/ok"),
    ]
    filtered = SearchRouter._filter_excluded(
        results, {"excludedDomains": ["example.com"]}
    )
    assert [r.url for r in filtered] == ["https://keep.me/ok"]


def test_filter_excluded_keeps_results_with_missing_hostname():
    results = [_mk_result("not-a-url"), _mk_result("https://arxiv.org/abs/1")]
    filtered = SearchRouter._filter_excluded(results, None)
    assert len(filtered) == 2


@pytest.mark.asyncio
async def test_search_router_applies_excluded_filter():
    router = SearchRouter()
    raw = [
        _mk_result("https://www.youtube.com/watch?v=1"),
        _mk_result("https://arxiv.org/abs/1"),
    ]
    with patch.object(router, "_search_academic", return_value=raw):
        results, _tier = await router.search("q")
    assert len(results) == 1
    assert results[0].url == "https://arxiv.org/abs/1"


# ──────────────────────────────────────────────────────────────
# HTTP endpoint tests (via TestClient)
# ──────────────────────────────────────────────────────────────


def test_search_endpoint(client):
    """Test POST /api/research/search via TestClient."""
    with patch(
        "app.services.search_router.search_router.search",
        new_callable=AsyncMock,
        return_value=([], SearchTier.ACADEMIC),
    ):
        response = client.post(
            "/api/research/search",
            json={"query": "machine learning pedagogy"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["query"] == "machine learning pedagogy"
    assert data["tierUsed"] == 1
    assert data["tierName"] == "Academic"


def test_tiers_endpoint(client):
    """Test GET /api/research/tiers via TestClient."""
    response = client.get("/api/research/tiers")
    assert response.status_code == 200
    data = response.json()
    assert "tiers" in data
    # At minimum, tier 1 (Academic) should always be present
    tier_nums = [t["tier"] for t in data["tiers"]]
    assert 1 in tier_nums
