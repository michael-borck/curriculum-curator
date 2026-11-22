"""Search router cache tests."""

from unittest.mock import AsyncMock

import pytest

import app.services.search_router as search_router_module
from app.services.search_router import (
    SearchRouter,
    SearchTier,
    clear_search_cache,
    _CACHE_TTL_SECONDS,
)
from app.services.web_search_service import SearchResult


@pytest.fixture(autouse=True)
def reset_cache():
    clear_search_cache()
    yield
    clear_search_cache()


def _result(title: str = "A paper", url: str = "https://example.org/a"):
    return SearchResult(title=title, url=url, source="openalex")


@pytest.mark.asyncio
async def test_identical_search_is_cached(monkeypatch):
    router = SearchRouter()
    calls = 0

    async def fake_academic(query, max_results, user_settings=None):
        nonlocal calls
        calls += 1
        return [_result()]

    monkeypatch.setattr(router, "_search_academic", fake_academic)

    first, first_tier = await router.search(
        "Feedback literacy", preferred_tier=1, max_results=5
    )
    second, second_tier = await router.search(
        "  feedback   literacy ", preferred_tier=1, max_results=5
    )

    assert calls == 1
    assert first_tier == second_tier == SearchTier.ACADEMIC
    assert [item.url for item in second] == [item.url for item in first]


@pytest.mark.asyncio
async def test_cache_is_isolated_by_api_keys(monkeypatch):
    router = SearchRouter()
    calls = 0

    async def fake_tier3(query, max_results, user_settings):
        nonlocal calls
        calls += 1
        return [_result()]

    monkeypatch.setattr(router, "_search_tier3", fake_tier3)

    await router.search(
        "query",
        preferred_tier=3,
        max_results=5,
        user_settings={"searchApiKeys": {"serperApiKey": "key-a"}},
    )
    await router.search(
        "query",
        preferred_tier=3,
        max_results=5,
        user_settings={"searchApiKeys": {"serperApiKey": "key-b"}},
    )

    assert calls == 2


@pytest.mark.asyncio
async def test_cache_expires_after_ttl(monkeypatch):
    router = SearchRouter()
    calls = 0

    async def fake_academic(query, max_results, user_settings=None):
        nonlocal calls
        calls += 1
        return [_result()]

    monkeypatch.setattr(router, "_search_academic", fake_academic)
    now = [1000.0]
    monkeypatch.setattr(search_router_module.time, "monotonic", lambda: now[0])

    await router.search("query", preferred_tier=1, max_results=5)
    await router.search("query", preferred_tier=1, max_results=5)
    assert calls == 1

    now[0] += _CACHE_TTL_SECONDS + 1
    await router.search("query", preferred_tier=1, max_results=5)
    assert calls == 2


@pytest.mark.asyncio
async def test_empty_results_are_not_cached(monkeypatch):
    router = SearchRouter()
    calls = 0

    async def fake_academic(query, max_results, user_settings=None):
        nonlocal calls
        calls += 1
        return []

    monkeypatch.setattr(router, "_search_academic", fake_academic)

    await router.search("query", preferred_tier=1, max_results=5)
    await router.search("query", preferred_tier=1, max_results=5)

    assert calls == 2


@pytest.mark.asyncio
async def test_searxng_uses_the_users_instance_url(monkeypatch):
    router = SearchRouter()
    seen: dict[str, object] = {}

    async def fake_search(query, **kwargs):
        seen.update(kwargs)
        return [_result()]

    monkeypatch.setattr(search_router_module.web_search_service, "search", fake_search)
    monkeypatch.setattr(search_router_module, "assert_public_url", AsyncMock())

    await router.search(
        "query",
        preferred_tier=4,
        max_results=5,
        user_settings={"searxngUrl": "https://searx.example.org"},
    )

    assert seen["searxng_url"] == "https://searx.example.org"


def test_cache_key_never_contains_raw_api_keys():
    router = SearchRouter()
    key = router._cache_key(
        "query",
        3,
        5,
        {"searchApiKeys": {"serperApiKey": "super-secret-key"}},
    )

    assert "super-secret-key" not in key
    assert len(key) == 64
