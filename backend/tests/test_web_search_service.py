"""
Tests for WebSearchService SearXNG hardening:
- Rate limiting (global + per-server)
- Retry with exponential backoff on 429/timeout
- Multi-endpoint fallback (/search → /)
- Browser-like headers
- Error classification
- category/time_range parameter wiring
"""

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
import pytest

from app.services.web_search_service import WebSearchError, WebSearchService


def _resp(status: int, json_data: dict[str, Any] | None = None) -> MagicMock:
    """Build one response object for a single mocked aiohttp call."""
    response = MagicMock()
    response.status = status
    response.json = AsyncMock(return_value=json_data or {"results": []})
    response.__aenter__ = AsyncMock(return_value=response)
    response.__aexit__ = AsyncMock(return_value=False)
    return response


def _session_with_responses(*responses: MagicMock) -> MagicMock:
    """Build a ClientSession mock that returns the given responses in sequence."""
    session = MagicMock()
    session.__aenter__ = AsyncMock(return_value=session)
    session.__aexit__ = AsyncMock(return_value=False)
    session.get = MagicMock(side_effect=list(responses))
    return session


def _session_class_mock(*responses: MagicMock) -> MagicMock:
    """Patch target for aiohttp.ClientSession() — each call returns a fresh session
    that yields the next response in the sequence."""
    iterator = iter(responses)

    def _factory(*_args: Any, **_kwargs: Any) -> MagicMock:
        response = next(iterator)
        return _session_with_responses(response)

    return MagicMock(side_effect=_factory)


@pytest.fixture(autouse=True)
def _reset_rate_limit_state():
    """Each test starts with a clean throttle state."""
    WebSearchService._last_global_request = 0.0
    WebSearchService._request_tracker.clear()
    yield
    WebSearchService._last_global_request = 0.0
    WebSearchService._request_tracker.clear()


@pytest.fixture(autouse=True)
def _no_real_sleep():
    """Don't actually sleep during retries / throttle waits."""
    with patch("app.services.web_search_service.asyncio.sleep", new=AsyncMock()):
        yield


def _make_service() -> WebSearchService:
    return WebSearchService(llm_service=MagicMock())


# ──────────────────────────────────────────────────────────────
# Category + time_range param wiring
# ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_search_passes_category_and_time_range():
    svc = _make_service()
    svc.searxng_url = "http://searx.test"

    data = {
        "results": [
            {
                "title": "General result",
                "url": "https://example.com/a",
                "content": "",
                "description": "",
            }
        ]
    }
    response = _resp(200, data)
    cls = _session_class_mock(response)

    with patch("aiohttp.ClientSession", cls):
        results = await svc.search(
            "quantum",
            academic_only=False,
            category="general",
            time_range="",
        )

    # Capture the URL that was passed to session.get
    captured_session = cls.call_args_list[0]  # first ClientSession() call
    assert captured_session is not None
    # Inspect what .get received
    # We built sessions via the factory, so the session mock is inside the factory closure.
    # Easier: inspect the raw call on the response factory via the iter() — instead, re-run
    # with a spy on a single session.

    assert len(results) == 1
    assert results[0].url == "https://example.com/a"


@pytest.mark.asyncio
async def test_search_builds_url_with_category():
    """Verify category + time_range make it into the actual URL query string."""
    svc = _make_service()
    svc.searxng_url = "http://searx.test"

    captured_urls: list[str] = []

    def _factory(*_args: Any, **_kwargs: Any) -> MagicMock:
        response = _resp(200, {"results": []})
        session = MagicMock()
        session.__aenter__ = AsyncMock(return_value=session)
        session.__aexit__ = AsyncMock(return_value=False)

        def _get(url: str, **_kw: Any) -> MagicMock:
            captured_urls.append(url)
            return response

        session.get = MagicMock(side_effect=_get)
        return session

    with patch("aiohttp.ClientSession", side_effect=_factory):
        await svc.search("physics", category="general", time_range="")

    assert len(captured_urls) == 1
    assert "categories=general" in captured_urls[0]
    assert "time_range" not in captured_urls[0]  # empty → omitted
    assert captured_urls[0].startswith("http://searx.test/search?")


@pytest.mark.asyncio
async def test_search_academic_default_preserves_legacy_behavior():
    """Existing academic callers (no kwargs) should still get science + year."""
    svc = _make_service()
    svc.searxng_url = "http://searx.test"

    captured_urls: list[str] = []

    def _factory(*_args: Any, **_kwargs: Any) -> MagicMock:
        response = _resp(200, {"results": []})
        session = MagicMock()
        session.__aenter__ = AsyncMock(return_value=session)
        session.__aexit__ = AsyncMock(return_value=False)

        def _get(url: str, **_kw: Any) -> MagicMock:
            captured_urls.append(url)
            return response

        session.get = MagicMock(side_effect=_get)
        return session

    with patch("aiohttp.ClientSession", side_effect=_factory):
        await svc.search("quantum computing")

    assert "categories=science" in captured_urls[0]
    assert "time_range=year" in captured_urls[0]


# ──────────────────────────────────────────────────────────────
# Browser headers
# ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_search_sends_browser_headers():
    svc = _make_service()
    svc.searxng_url = "http://searx.test"

    captured_headers: list[dict[str, str]] = []

    def _factory(*_args: Any, **_kwargs: Any) -> MagicMock:
        response = _resp(200, {"results": []})
        session = MagicMock()
        session.__aenter__ = AsyncMock(return_value=session)
        session.__aexit__ = AsyncMock(return_value=False)

        def _get(_url: str, headers: dict[str, str] | None = None, **_kw: Any) -> MagicMock:
            captured_headers.append(headers or {})
            return response

        session.get = MagicMock(side_effect=_get)
        return session

    with patch("aiohttp.ClientSession", side_effect=_factory):
        await svc.search("test")

    assert len(captured_headers) == 1
    h = captured_headers[0]
    assert "User-Agent" in h
    assert "Mozilla" in h["User-Agent"]
    assert h["Referer"] == "http://searx.test"
    assert "Sec-Ch-Ua" in h


# ──────────────────────────────────────────────────────────────
# 429 retry + backoff
# ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_search_retries_on_429_then_succeeds():
    svc = _make_service()
    svc.searxng_url = "http://searx.test"

    responses = [
        _resp(429),
        _resp(429),
        _resp(200, {"results": [{"title": "ok", "url": "https://a.edu/x", "content": "", "description": ""}]}),
    ]
    cls = _session_class_mock(*responses)

    with patch("aiohttp.ClientSession", cls):
        results = await svc.search("test", academic_only=False)

    assert len(results) == 1
    assert results[0].url == "https://a.edu/x"
    # 3 session creations = 3 attempts (first + 2 retries)
    assert cls.call_count == 3


@pytest.mark.asyncio
async def test_search_falls_through_to_second_endpoint():
    """When /search exhausts retries on non-429, try / next."""
    svc = _make_service()
    svc.searxng_url = "http://searx.test"

    captured_urls: list[str] = []

    iterator = iter(
        [
            _resp(500),  # /search fails hard
            _resp(
                200,
                {
                    "results": [
                        {"title": "ok", "url": "https://b.edu/x", "content": "", "description": ""}
                    ]
                },
            ),  # / succeeds
        ]
    )

    def _factory(*_args: Any, **_kwargs: Any) -> MagicMock:
        response = next(iterator)
        session = MagicMock()
        session.__aenter__ = AsyncMock(return_value=session)
        session.__aexit__ = AsyncMock(return_value=False)

        def _get(url: str, **_kw: Any) -> MagicMock:
            captured_urls.append(url)
            return response

        session.get = MagicMock(side_effect=_get)
        return session

    with patch("aiohttp.ClientSession", side_effect=_factory):
        results = await svc.search("test", academic_only=False)

    assert len(results) == 1
    assert any("/search?" in u for u in captured_urls)
    assert any(u.endswith("/?q=test") or "/?q=" in u for u in captured_urls)


@pytest.mark.asyncio
async def test_search_429_exhausted_raises_classified_error():
    svc = _make_service()
    svc.searxng_url = "http://searx.test"

    # Every attempt returns 429 on both endpoints: 4 per endpoint * 2 endpoints = 8
    responses = [_resp(429) for _ in range(10)]
    cls = _session_class_mock(*responses)

    with patch("aiohttp.ClientSession", cls), pytest.raises(WebSearchError) as exc_info:
        await svc.search("test")

    assert "429" in str(exc_info.value)


# ──────────────────────────────────────────────────────────────
# Error classification
# ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_search_timeout_classified():
    svc = _make_service()
    svc.searxng_url = "http://searx.test"

    def _factory(*_args: Any, **_kwargs: Any) -> MagicMock:
        session = MagicMock()
        session.__aenter__ = AsyncMock(return_value=session)
        session.__aexit__ = AsyncMock(return_value=False)
        session.get = MagicMock(side_effect=TimeoutError("slow"))
        return session

    with patch("aiohttp.ClientSession", side_effect=_factory), pytest.raises(WebSearchError) as exc_info:
        await svc.search("test")

    assert "timed out" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_search_dns_error_classified():
    svc = _make_service()
    svc.searxng_url = "http://nonexistent.test"

    def _factory(*_args: Any, **_kwargs: Any) -> MagicMock:
        session = MagicMock()
        session.__aenter__ = AsyncMock(return_value=session)
        session.__aexit__ = AsyncMock(return_value=False)
        session.get = MagicMock(
            side_effect=aiohttp.ClientError("nodename nor servname provided")
        )
        return session

    with patch("aiohttp.ClientSession", side_effect=_factory), pytest.raises(WebSearchError) as exc_info:
        await svc.search("test")

    assert "resolve" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_search_ssl_error_classified():
    svc = _make_service()
    svc.searxng_url = "https://searx.test"

    def _factory(*_args: Any, **_kwargs: Any) -> MagicMock:
        session = MagicMock()
        session.__aenter__ = AsyncMock(return_value=session)
        session.__aexit__ = AsyncMock(return_value=False)
        session.get = MagicMock(
            side_effect=aiohttp.ClientError("SSL certificate verify failed")
        )
        return session

    with patch("aiohttp.ClientSession", side_effect=_factory), pytest.raises(WebSearchError) as exc_info:
        await svc.search("test")

    assert "ssl" in str(exc_info.value).lower()


# ──────────────────────────────────────────────────────────────
# Rate limiting
# ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_rate_limit_sleeps_on_rapid_calls(monkeypatch: pytest.MonkeyPatch):
    """Second rapid call should trigger a sleep for the per-server throttle."""
    svc = _make_service()
    svc.searxng_url = "http://searx.test"

    # Seed the tracker as if we just made a request to this server
    import time as _time

    WebSearchService._request_tracker["http://searx.test"] = _time.monotonic()
    WebSearchService._last_global_request = _time.monotonic()

    sleep_calls: list[float] = []

    async def _fake_sleep(seconds: float) -> None:
        sleep_calls.append(seconds)

    monkeypatch.setattr(
        "app.services.web_search_service.asyncio.sleep", _fake_sleep
    )

    await svc._rate_limit_searxng("http://searx.test")

    # Should have slept at least once (per-server throttle kicks in)
    assert len(sleep_calls) >= 1
    assert any(s > 0 for s in sleep_calls)


@pytest.mark.asyncio
async def test_rate_limit_prunes_tracker_when_large():
    svc = _make_service()
    # Fill tracker past the prune threshold (50)
    for i in range(55):
        WebSearchService._request_tracker[f"http://server-{i}.test"] = float(i)

    await svc._rate_limit_searxng("http://new-server.test")

    # After pruning, should be 25 kept + 1 new = 26 (or thereabouts, not > 55)
    assert len(WebSearchService._request_tracker) <= 30
