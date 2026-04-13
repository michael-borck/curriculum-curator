"""
Tests for Tier 3 search clients.

Currently focused on DuckDuckGoClient (HTML scraping) — the keyed clients
(Google CSE, Brave, Tavily) are simple wrappers already exercised indirectly
via the search router tests.
"""

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.tier3_search_clients import DuckDuckGoClient


def _mock_response(status: int, text: str) -> MagicMock:
    response = MagicMock()
    response.status = status
    response.text = AsyncMock(return_value=text)
    response.__aenter__ = AsyncMock(return_value=response)
    response.__aexit__ = AsyncMock(return_value=False)
    return response


def _mock_session(response: MagicMock) -> MagicMock:
    session = MagicMock()
    session.__aenter__ = AsyncMock(return_value=session)
    session.__aexit__ = AsyncMock(return_value=False)
    session.get = MagicMock(return_value=response)
    return session


def _patch_aiohttp(response: MagicMock) -> Any:
    def _factory(*_args: Any, **_kwargs: Any) -> MagicMock:
        return _mock_session(response)

    return patch("aiohttp.ClientSession", side_effect=_factory)


# ──────────────────────────────────────────────────────────────
# Redirect decoding
# ──────────────────────────────────────────────────────────────


def test_decode_redirect_plain_url():
    assert (
        DuckDuckGoClient._decode_redirect("https://example.com/page")
        == "https://example.com/page"
    )


def test_decode_redirect_uddg_wrapper():
    href = "//duckduckgo.com/l/?uddg=https%3A%2F%2Farxiv.org%2Fabs%2F1234&rut=abc"
    assert DuckDuckGoClient._decode_redirect(href) == "https://arxiv.org/abs/1234"


def test_decode_redirect_uddg_no_trailing_params():
    href = "//duckduckgo.com/l/?uddg=https%3A%2F%2Fexample.edu%2Fpaper"
    assert DuckDuckGoClient._decode_redirect(href) == "https://example.edu/paper"


# ──────────────────────────────────────────────────────────────
# Acceptable-row filter
# ──────────────────────────────────────────────────────────────


def test_is_acceptable_drops_short_title():
    assert not DuckDuckGoClient._is_acceptable("https://a.edu/x", "short")


def test_is_acceptable_drops_non_http():
    assert not DuckDuckGoClient._is_acceptable("ftp://a.edu/x", "A long enough title")


def test_is_acceptable_drops_junk_tokens():
    assert not DuckDuckGoClient._is_acceptable(
        "https://a.edu/x", "Next page of results"
    )
    assert not DuckDuckGoClient._is_acceptable(
        "https://a.edu/x", "About DuckDuckGo search"
    )


def test_is_acceptable_keeps_valid_row():
    assert DuckDuckGoClient._is_acceptable(
        "https://arxiv.org/abs/1234", "Quantum computing survey 2024"
    )


# ──────────────────────────────────────────────────────────────
# HTML parsing end-to-end
# ──────────────────────────────────────────────────────────────


SAMPLE_HTML = """
<html><body>
<table>
  <tr><td>
    <a class="result-link" href="//duckduckgo.com/l/?uddg=https%3A%2F%2Farxiv.org%2Fabs%2F2401.12345&rut=x">
      Attention Is All You Need: A Survey
    </a>
  </td></tr>
  <tr><td>
    <a class="result-link" href="//duckduckgo.com/l/?uddg=https%3A%2F%2Fexample.edu%2Fml-intro">
      Machine Learning Introduction for Educators
    </a>
  </td></tr>
  <tr><td>
    <a class="result-link" href="//duckduckgo.com/l/?uddg=https%3A%2F%2Fspam.com%2Fx">
      short
    </a>
  </td></tr>
  <tr><td>
    <a class="result-link" href="//duckduckgo.com/l/?uddg=https%3A%2F%2Fnav.com">
      Next page of DuckDuckGo results
    </a>
  </td></tr>
  <tr><td>
    <a class="nav-link" href="/about">About</a>
  </td></tr>
</table>
</body></html>
"""


@pytest.mark.asyncio
async def test_search_parses_sample_html():
    client = DuckDuckGoClient()
    response = _mock_response(200, SAMPLE_HTML)

    with _patch_aiohttp(response):
        results = await client.search("transformers")

    assert len(results) == 2
    urls = [r.url for r in results]
    assert "https://arxiv.org/abs/2401.12345" in urls
    assert "https://example.edu/ml-intro" in urls
    # Junk rows filtered out
    assert not any("spam.com" in u for u in urls)
    assert not any("nav.com" in u for u in urls)
    assert all(r.source == "duckduckgo" for r in results)


@pytest.mark.asyncio
async def test_search_respects_max_results():
    client = DuckDuckGoClient()
    response = _mock_response(200, SAMPLE_HTML)

    with _patch_aiohttp(response):
        results = await client.search("transformers", max_results=1)

    assert len(results) == 1


@pytest.mark.asyncio
async def test_search_returns_empty_on_non_200():
    client = DuckDuckGoClient()
    response = _mock_response(500, "")

    with _patch_aiohttp(response):
        results = await client.search("anything")

    assert results == []


@pytest.mark.asyncio
async def test_search_returns_empty_on_network_error():
    client = DuckDuckGoClient()

    def _factory(*_args: Any, **_kwargs: Any) -> MagicMock:
        session = MagicMock()
        session.__aenter__ = AsyncMock(return_value=session)
        session.__aexit__ = AsyncMock(return_value=False)
        session.get = MagicMock(side_effect=OSError("network unreachable"))
        return session

    with patch("aiohttp.ClientSession", side_effect=_factory):
        results = await client.search("anything")

    assert results == []


@pytest.mark.asyncio
async def test_search_returns_empty_on_unparseable_html():
    """If DDG changes layout and there are no result-link anchors, return []."""
    client = DuckDuckGoClient()
    response = _mock_response(200, "<html><body>nothing here</body></html>")

    with _patch_aiohttp(response):
        results = await client.search("anything")

    assert results == []


# ──────────────────────────────────────────────────────────────
# Router integration
# ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_router_uses_ddg_when_no_keys():
    from app.services.search_router import SearchRouter, SearchTier
    from app.services.web_search_service import SearchResult

    router = SearchRouter()

    with patch(
        "app.services.tier3_search_clients.DuckDuckGoClient.search",
        new_callable=AsyncMock,
        return_value=[SearchResult(title="t", url="https://a.edu/x", source="duckduckgo")],
    ) as mock_ddg:
        results, tier = await router.search(
            "test", preferred_tier=3, user_settings={}
        )

    assert tier == SearchTier.GENERAL_WEB
    assert len(results) == 1
    assert results[0].source == "duckduckgo"
    mock_ddg.assert_called_once()


@pytest.mark.asyncio
async def test_router_falls_back_to_ddg_when_keyed_returns_empty():
    from app.services.search_router import SearchRouter, SearchTier
    from app.services.web_search_service import SearchResult

    router = SearchRouter()

    with (
        patch(
            "app.services.tier3_search_clients.BraveSearchClient.search",
            new_callable=AsyncMock,
            return_value=[],
        ) as mock_brave,
        patch(
            "app.services.tier3_search_clients.DuckDuckGoClient.search",
            new_callable=AsyncMock,
            return_value=[
                SearchResult(title="t", url="https://fallback.edu/x", source="duckduckgo")
            ],
        ) as mock_ddg,
    ):
        results, tier = await router.search(
            "test",
            preferred_tier=3,
            user_settings={"searchApiKeys": {"braveSearchApiKey": "k"}},
        )

    assert tier == SearchTier.GENERAL_WEB
    assert len(results) == 1
    assert results[0].url == "https://fallback.edu/x"
    mock_brave.assert_called_once()
    mock_ddg.assert_called_once()


@pytest.mark.asyncio
async def test_router_prefers_keyed_provider_when_it_has_results():
    from app.services.search_router import SearchRouter, SearchTier
    from app.services.web_search_service import SearchResult

    router = SearchRouter()

    with (
        patch(
            "app.services.tier3_search_clients.BraveSearchClient.search",
            new_callable=AsyncMock,
            return_value=[SearchResult(title="brave", url="https://brave.edu/x", source="brave")],
        ),
        patch(
            "app.services.tier3_search_clients.DuckDuckGoClient.search",
            new_callable=AsyncMock,
        ) as mock_ddg,
    ):
        results, tier = await router.search(
            "test",
            preferred_tier=3,
            user_settings={"searchApiKeys": {"braveSearchApiKey": "k"}},
        )

    assert tier == SearchTier.GENERAL_WEB
    assert results[0].source == "brave"
    mock_ddg.assert_not_called()
