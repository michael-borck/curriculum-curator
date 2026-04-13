"""
Tier 3 Search Clients — Google CSE, Brave Search, Tavily, DuckDuckGo.

All except DuckDuckGo require user-provided API keys. DuckDuckGo scrapes the
lite HTML endpoint and needs no credentials — it's the always-available
fallback within Tier 3.

All clients return normalized SearchResult objects and never raise on failure
(log + return []).
"""

import logging
from urllib.parse import unquote, urlparse

import aiohttp
from bs4 import BeautifulSoup, Tag

from app.services.web_search_service import SearchResult

logger = logging.getLogger(__name__)


class GoogleCSEClient:
    """Google Custom Search Engine client."""

    BASE_URL = "https://www.googleapis.com/customsearch/v1"

    async def search(
        self,
        query: str,
        api_key: str,
        engine_id: str,
        max_results: int = 10,
    ) -> list[SearchResult]:
        """Search via Google CSE API."""
        params = {
            "key": api_key,
            "cx": engine_id,
            "q": query,
            "num": min(max_results, 10),  # Google CSE max 10 per request
        }

        try:
            async with (
                aiohttp.ClientSession(
                    timeout=aiohttp.ClientTimeout(total=15)
                ) as session,
                session.get(self.BASE_URL, params=params) as response,
            ):
                if response.status != 200:
                    logger.warning("Google CSE returned status %d", response.status)
                    return []

                data = await response.json()
                return [
                    SearchResult(
                        title=item.get("title", ""),
                        url=item.get("link", ""),
                        content=item.get("snippet"),
                        description=item.get("snippet"),
                        source="google_cse",
                    )
                    for item in data.get("items", [])
                ]

        except Exception:
            logger.exception("Google CSE search failed")
            return []


class BraveSearchClient:
    """Brave Search API client."""

    BASE_URL = "https://api.search.brave.com/res/v1/web/search"

    async def search(
        self,
        query: str,
        api_key: str,
        max_results: int = 10,
    ) -> list[SearchResult]:
        """Search via Brave Search API."""
        headers = {
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "X-Subscription-Token": api_key,
        }
        params = {
            "q": query,
            "count": min(max_results, 20),
        }

        try:
            async with (
                aiohttp.ClientSession(
                    timeout=aiohttp.ClientTimeout(total=15)
                ) as session,
                session.get(self.BASE_URL, headers=headers, params=params) as response,
            ):
                if response.status != 200:
                    logger.warning("Brave Search returned status %d", response.status)
                    return []

                data = await response.json()
                return [
                    SearchResult(
                        title=item.get("title", ""),
                        url=item.get("url", ""),
                        content=item.get("description"),
                        description=item.get("description"),
                        source="brave",
                    )
                    for item in data.get("web", {}).get("results", [])
                ]

        except Exception:
            logger.exception("Brave Search failed")
            return []


class TavilyClient:
    """Tavily Search API client."""

    BASE_URL = "https://api.tavily.com/search"

    async def search(
        self,
        query: str,
        api_key: str,
        max_results: int = 10,
    ) -> list[SearchResult]:
        """Search via Tavily API."""
        payload = {
            "api_key": api_key,
            "query": query,
            "max_results": min(max_results, 20),
            "search_depth": "basic",
            "include_answer": False,
        }

        try:
            async with (
                aiohttp.ClientSession(
                    timeout=aiohttp.ClientTimeout(total=15)
                ) as session,
                session.post(self.BASE_URL, json=payload) as response,
            ):
                if response.status != 200:
                    logger.warning("Tavily returned status %d", response.status)
                    return []

                data = await response.json()
                return [
                    SearchResult(
                        title=item.get("title", ""),
                        url=item.get("url", ""),
                        content=item.get("content"),
                        description=item.get("content"),
                        source="tavily",
                    )
                    for item in data.get("results", [])
                ]

        except Exception:
            logger.exception("Tavily search failed")
            return []


class DuckDuckGoClient:
    """DuckDuckGo Lite HTML scraper — no API key required.

    Scrapes https://lite.duckduckgo.com/lite/ and decodes the redirect wrapper
    (duckduckgo.com/l/?uddg=<real_url>) to recover the original link. Designed
    as the always-available fallback within Tier 3 so zero-config users still
    get web results.

    Note: HTML layout can change. Parse errors are logged and return [] — the
    router will surface "no results" rather than an error.
    """

    BASE_URL = "https://lite.duckduckgo.com/lite/"
    TIMEOUT_S = 10
    MIN_TITLE_LEN = 10
    JUNK_TITLE_TOKENS = ("duckduckgo", "next page", "more results")

    HEADERS = {  # noqa: RUF012
        "User-Agent": (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }

    async def search(
        self,
        query: str,
        max_results: int = 10,
    ) -> list[SearchResult]:
        """Fetch DuckDuckGo Lite results. Returns [] on any failure."""
        params = {"q": query, "t": "h_", "ia": "web"}
        try:
            async with (
                aiohttp.ClientSession(
                    timeout=aiohttp.ClientTimeout(total=self.TIMEOUT_S)
                ) as session,
                session.get(
                    self.BASE_URL, params=params, headers=self.HEADERS
                ) as response,
            ):
                if response.status != 200:
                    logger.warning(
                        "DuckDuckGo lite returned status %d", response.status
                    )
                    return []
                html = await response.text()
        except Exception:
            logger.exception("DuckDuckGo lite fetch failed")
            return []

        return self._parse(html, max_results)

    def _parse(self, html: str, max_results: int) -> list[SearchResult]:
        """Extract result links from DuckDuckGo Lite HTML."""
        try:
            soup = BeautifulSoup(html, "html.parser")
        except Exception:
            logger.exception("DuckDuckGo HTML parse failed")
            return []

        results: list[SearchResult] = []
        for anchor in soup.find_all("a", class_="result-link"):
            if not isinstance(anchor, Tag):
                continue
            href = anchor.get("href")
            if not isinstance(href, str) or not href:
                continue
            title = anchor.get_text(strip=True)

            real_url = self._decode_redirect(href)
            if not self._is_acceptable(real_url, title):
                continue

            results.append(
                SearchResult(
                    title=title[:200],
                    url=real_url,
                    source="duckduckgo",
                )
            )
            if len(results) >= max_results:
                break

        if not results:
            logger.info("DuckDuckGo returned zero results — HTML layout may have changed")
        return results

    @staticmethod
    def _decode_redirect(href: str) -> str:
        """Extract the real URL from a DDG redirect link if present."""
        if "duckduckgo.com/l/" not in href or "uddg=" not in href:
            return href
        # Slice out the uddg param value (stops at next & or end)
        after = href.split("uddg=", 1)[1]
        encoded = after.split("&", 1)[0]
        try:
            return unquote(encoded)
        except (ValueError, UnicodeDecodeError):
            return href

    @classmethod
    def _is_acceptable(cls, url: str, title: str) -> bool:
        """Filter out junk rows (navigation, short titles, non-http URLs)."""
        if not url or not title:
            return False
        if len(title) < cls.MIN_TITLE_LEN:
            return False
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return False
        title_lower = title.lower()
        return not any(token in title_lower for token in cls.JUNK_TITLE_TOKENS)
