"""
Tier 3 Search Clients — Google CSE, Brave Search, Tavily.

All require user-provided API keys. Return normalized SearchResult objects.
"""

import logging

import aiohttp

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
