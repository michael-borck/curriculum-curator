"""
Search Router — tiered search dispatch.

Tier 1: Academic (OpenAlex + Semantic Scholar) — always available
Tier 2: LLM-native web search — auto if provider configured (future)
Tier 3: General web APIs (Google CSE, Brave, Tavily) — user adds key
Tier 4: SearXNG — user's own instance
"""

import logging
from enum import IntEnum

from app.services.academic_search_service import (
    AcademicWork,
    academic_search_service,
)
from app.services.web_search_service import SearchResult, web_search_service

logger = logging.getLogger(__name__)


class SearchTier(IntEnum):
    ACADEMIC = 1
    LLM_NATIVE = 2
    GENERAL_WEB = 3
    SEARXNG = 4


class TierAvailability:
    """Describes whether a tier is available and why."""

    def __init__(self, tier: SearchTier, available: bool, reason: str | None = None):
        self.tier = tier
        self.available = available
        self.reason = reason


class SearchRouter:
    """Routes search queries to the best available tier."""

    def get_available_tiers(
        self, user_settings: dict[str, object] | None = None
    ) -> list[TierAvailability]:
        """Return availability status for each tier."""
        tiers: list[TierAvailability] = []

        # Tier 1: Always available
        tiers.append(TierAvailability(SearchTier.ACADEMIC, True))

        # Tier 2: LLM-native — not yet implemented
        tiers.append(
            TierAvailability(
                SearchTier.LLM_NATIVE, False, "LLM-native search not yet implemented"
            )
        )

        # Tier 3: General web APIs — check for user API keys
        user_settings = user_settings or {}
        api_keys = user_settings.get("searchApiKeys")
        has_tier3 = False
        if isinstance(api_keys, dict):
            has_tier3 = bool(
                api_keys.get("googleCseApiKey")
                or api_keys.get("braveSearchApiKey")
                or api_keys.get("tavilyApiKey")
            )

        if has_tier3:
            tiers.append(TierAvailability(SearchTier.GENERAL_WEB, True))
        else:
            tiers.append(
                TierAvailability(
                    SearchTier.GENERAL_WEB,
                    False,
                    "No web search API keys configured",
                )
            )

        # Tier 4: SearXNG — check for URL
        searxng_url = user_settings.get("searxngUrl") if user_settings else None
        from app.core.config import settings  # noqa: PLC0415

        system_url = getattr(settings, "SEARXNG_URL", "")
        has_searxng = bool(searxng_url or system_url)
        if has_searxng:
            tiers.append(TierAvailability(SearchTier.SEARXNG, True))
        else:
            tiers.append(
                TierAvailability(SearchTier.SEARXNG, False, "No SearXNG URL configured")
            )

        return tiers

    async def search(
        self,
        query: str,
        preferred_tier: int | None = None,
        max_results: int = 20,
        user_settings: dict[str, object] | None = None,
    ) -> tuple[list[SearchResult], SearchTier]:
        """Execute search on the best available tier.

        Returns (results, tier_used).
        Falls back to lower tiers if preferred tier is unavailable.
        """
        tiers = self.get_available_tiers(user_settings)
        available = {t.tier: t for t in tiers if t.available}

        # Determine which tier to use
        if preferred_tier and SearchTier(preferred_tier) in available:
            tier = SearchTier(preferred_tier)
        elif SearchTier.ACADEMIC in available:
            tier = SearchTier.ACADEMIC
        else:
            # Should never happen since Tier 1 is always available
            return [], SearchTier.ACADEMIC

        # Dispatch to the appropriate tier
        if tier == SearchTier.ACADEMIC:
            return await self._search_academic(query, max_results, user_settings), tier
        if tier == SearchTier.GENERAL_WEB:
            return await self._search_tier3(
                query, max_results, user_settings or {}
            ), tier
        if tier == SearchTier.SEARXNG:
            return await self._search_searxng(query, max_results), tier

        # Fallback
        return (
            await self._search_academic(query, max_results, user_settings),
            SearchTier.ACADEMIC,
        )

    async def _search_academic(
        self,
        query: str,
        max_results: int,
        user_settings: dict[str, object] | None = None,
    ) -> list[SearchResult]:
        """Tier 1: Academic search via OpenAlex + Semantic Scholar + CrossRef + CORE."""
        # Check for CORE API key in user settings or system config
        core_api_key: str | None = None
        if user_settings:
            api_keys = user_settings.get("searchApiKeys")
            if isinstance(api_keys, dict):
                key = api_keys.get("coreApiKey")
                if isinstance(key, str) and key:
                    core_api_key = key

        if not core_api_key:
            from app.core.config import settings  # noqa: PLC0415

            core_api_key = settings.CORE_API_KEY

        works: list[AcademicWork] = await academic_search_service.search(
            query, max_results, core_api_key=core_api_key
        )
        return academic_search_service.to_search_results(works)

    async def _search_tier3(
        self,
        query: str,
        max_results: int,
        user_settings: dict[str, object],
    ) -> list[SearchResult]:
        """Tier 3: General web API search. Tries available clients in order."""
        api_keys = user_settings.get("searchApiKeys")
        if not isinstance(api_keys, dict):
            return await self._search_academic(query, max_results)

        # Import tier3 clients lazily
        from app.services.tier3_search_clients import (  # noqa: PLC0415
            BraveSearchClient,
            GoogleCSEClient,
            TavilyClient,
        )

        # Try Google CSE first
        google_key = api_keys.get("googleCseApiKey")
        google_engine = api_keys.get("googleCseEngineId")
        if isinstance(google_key, str) and isinstance(google_engine, str):
            try:
                client = GoogleCSEClient()
                return await client.search(
                    query, google_key, google_engine, max_results
                )
            except Exception:
                logger.exception("Google CSE search failed, trying next")

        # Try Brave
        brave_key = api_keys.get("braveSearchApiKey")
        if isinstance(brave_key, str):
            try:
                client = BraveSearchClient()
                return await client.search(query, brave_key, max_results)
            except Exception:
                logger.exception("Brave search failed, trying next")

        # Try Tavily
        tavily_key = api_keys.get("tavilyApiKey")
        if isinstance(tavily_key, str):
            try:
                client = TavilyClient()
                return await client.search(query, tavily_key, max_results)
            except Exception:
                logger.exception("Tavily search failed, falling back to academic")

        return await self._search_academic(query, max_results)

    async def _search_searxng(self, query: str, max_results: int) -> list[SearchResult]:
        """Tier 4: SearXNG search using existing service."""
        return await web_search_service.search(
            query, max_results=max_results, academic_only=True
        )


# Singleton
search_router = SearchRouter()
