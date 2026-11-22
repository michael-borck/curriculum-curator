"""AUDIT.md Step 10 regression tests: per-provider academic search consent."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

import app.services.search_router as search_router_module
from app.services.academic_search_service import AcademicSearchService
from app.services.search_router import SearchRouter


@pytest.mark.asyncio
async def test_no_providers_queries_nothing() -> None:
    service = AcademicSearchService()
    service.openalex.search_works = AsyncMock(return_value=[])  # type: ignore[method-assign]
    service.semantic_scholar.search_papers = AsyncMock(return_value=[])  # type: ignore[method-assign]
    service.crossref.search_works = AsyncMock(return_value=[])  # type: ignore[method-assign]

    result = await service.search("query", 5, providers=[])

    assert result == []
    service.openalex.search_works.assert_not_awaited()
    service.semantic_scholar.search_papers.assert_not_awaited()
    service.crossref.search_works.assert_not_awaited()


@pytest.mark.asyncio
async def test_only_selected_provider_is_queried() -> None:
    service = AcademicSearchService()
    service.openalex.search_works = AsyncMock(return_value=[])  # type: ignore[method-assign]
    service.semantic_scholar.search_papers = AsyncMock(return_value=[])  # type: ignore[method-assign]
    service.crossref.search_works = AsyncMock(return_value=[])  # type: ignore[method-assign]

    await service.search("query", 5, providers=["crossref"])

    service.openalex.search_works.assert_not_awaited()
    service.semantic_scholar.search_papers.assert_not_awaited()
    service.crossref.search_works.assert_awaited_once()


@pytest.mark.asyncio
async def test_router_passes_saved_provider_selection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    async def fake_search(query, max_results, core_api_key=None, providers=None):
        captured["providers"] = providers
        return []

    monkeypatch.setattr(
        search_router_module.academic_search_service, "search", fake_search
    )

    await SearchRouter()._search_academic(
        "query", 5, {"academicProviders": ["openalex"]}
    )

    assert captured["providers"] == ["openalex"]


@pytest.mark.asyncio
async def test_router_omits_selection_for_legacy_settings(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    async def fake_search(query, max_results, core_api_key=None, providers=None):
        captured["providers"] = providers
        return []

    monkeypatch.setattr(
        search_router_module.academic_search_service, "search", fake_search
    )

    await SearchRouter()._search_academic("query", 5, {})

    assert captured["providers"] is None
