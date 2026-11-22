"""
Search Router — tiered search dispatch.

Tier 1: Academic (OpenAlex + Semantic Scholar) — always available
Tier 2: LLM-native web search — auto if provider configured (future)
Tier 3: General web (Google CSE, Serper, Brave, Tavily + DuckDuckGo fallback) — keys optional
Tier 4: SearXNG — user's own instance
"""

import hashlib
import json
import logging
import time
from enum import IntEnum
from urllib.parse import urlparse

from app.services.academic_search_service import (
    AcademicWork,
    academic_search_service,
)
from app.services.web_search_service import SearchResult, web_search_service
from app.utils.url_safety import UrlNotAllowedError, assert_public_url

logger = logging.getLogger(__name__)

# Identical searches are expensive (paid APIs and shared quotas), so keep a
# small in-process cache. Keys include a fingerprint of every setting that can
# change the result, never the raw API keys.
_CACHE_TTL_SECONDS = 10 * 60
_CACHE_MAX_ENTRIES = 100
_SEARCH_CACHE: dict[str, tuple[float, list[SearchResult], "SearchTier"]] = {}


def clear_search_cache() -> None:
    """Clear cached search results (tests and manual cache purge)."""
    _SEARCH_CACHE.clear()


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

        # Tier 3: General web — always available via DuckDuckGo fallback.
        # Keyed providers (Google CSE, Brave, Tavily) are tried first if configured.
        tiers.append(TierAvailability(SearchTier.GENERAL_WEB, True))

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
        cache_key = self._cache_key(query, preferred_tier, max_results, user_settings)
        cached = self._cache_get(cache_key)
        if cached is not None:
            cached_results, cached_tier = cached
            logger.debug("search cache hit")
            return list(cached_results), cached_tier

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
            results = await self._search_academic(query, max_results, user_settings)
        elif tier == SearchTier.GENERAL_WEB:
            results = await self._search_tier3(query, max_results, user_settings or {})
        elif tier == SearchTier.SEARXNG:
            results = await self._search_searxng(query, max_results, user_settings)
        else:
            results = await self._search_academic(query, max_results, user_settings)
            tier = SearchTier.ACADEMIC

        filtered = self._filter_excluded(results, user_settings)
        if filtered:
            self._cache_set(cache_key, filtered, tier)
        return filtered, tier

    @staticmethod
    def _fingerprint(value: object) -> str:
        return hashlib.sha256(str(value).encode("utf-8")).hexdigest()

    def _cache_key(
        self,
        query: str,
        preferred_tier: int | None,
        max_results: int,
        user_settings: dict[str, object] | None,
    ) -> str:
        """Build a cache key without storing raw API keys.

        Every input that can change the result is included: the query, tier,
        limit, SearXNG URL, excluded domains, and a digest of each configured
        key. System-level keys/URLs/exclusions are included as well.
        """
        from app.core.config import settings as app_settings  # noqa: PLC0415

        settings_dict = user_settings or {}
        raw_keys = settings_dict.get("searchApiKeys")
        api_keys = raw_keys if isinstance(raw_keys, dict) else {}
        key_fingerprints = {
            name: self._fingerprint(value)
            for name, value in sorted(api_keys.items())
            if isinstance(value, str) and value
        }

        raw_excluded = settings_dict.get("excludedDomains")
        user_excluded = (
            sorted(
                d.strip().lower().lstrip(".")
                for d in raw_excluded
                if isinstance(d, str) and d.strip()
            )
            if isinstance(raw_excluded, list)
            else []
        )

        payload = {
            "query": " ".join(query.lower().split()),
            "preferred_tier": preferred_tier,
            "max_results": max_results,
            "searxng_url": settings_dict.get("searxngUrl") or "",
            "user_excluded": user_excluded,
            "user_keys": key_fingerprints,
            "system_core_key": self._fingerprint(app_settings.CORE_API_KEY or ""),
            "system_searxng_url": app_settings.SEARXNG_URL or "",
            "system_excluded": sorted(app_settings.EXCLUDED_SEARCH_DOMAINS or []),
        }
        encoded = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    @staticmethod
    def _cache_get(
        key: str,
    ) -> tuple[list[SearchResult], SearchTier] | None:
        entry = _SEARCH_CACHE.get(key)
        if entry is None:
            return None
        stored_at, results, tier = entry
        if time.monotonic() - stored_at >= _CACHE_TTL_SECONDS:
            _SEARCH_CACHE.pop(key, None)
            return None
        return results, tier

    @staticmethod
    def _cache_set(
        key: str,
        results: list[SearchResult],
        tier: SearchTier,
    ) -> None:
        now = time.monotonic()
        if len(_SEARCH_CACHE) >= _CACHE_MAX_ENTRIES:
            expired = [
                cache_key
                for cache_key, (stored_at, _, _) in _SEARCH_CACHE.items()
                if now - stored_at >= _CACHE_TTL_SECONDS
            ]
            for cache_key in expired:
                _SEARCH_CACHE.pop(cache_key, None)
            while len(_SEARCH_CACHE) >= _CACHE_MAX_ENTRIES:
                oldest = min(
                    _SEARCH_CACHE,
                    key=lambda cache_key: _SEARCH_CACHE[cache_key][0],
                )
                _SEARCH_CACHE.pop(oldest, None)
        _SEARCH_CACHE[key] = (now, list(results), tier)

    @staticmethod
    def _filter_excluded(
        results: list[SearchResult],
        user_settings: dict[str, object] | None,
    ) -> list[SearchResult]:
        """Drop results whose hostname matches a system or user excluded domain.

        Matches `hostname == domain` or `hostname.endswith("." + domain)` so that
        blocking "youtube.com" also blocks "m.youtube.com" but NOT "notyoutube.com".
        """
        from app.core.config import settings  # noqa: PLC0415

        excluded: set[str] = {
            d.strip().lower().lstrip(".")
            for d in (settings.EXCLUDED_SEARCH_DOMAINS or [])
            if d and d.strip()
        }
        if user_settings:
            user_excluded = user_settings.get("excludedDomains")
            if isinstance(user_excluded, list):
                excluded.update(
                    d.strip().lower().lstrip(".")
                    for d in user_excluded
                    if isinstance(d, str) and d.strip()
                )

        if not excluded:
            return results

        filtered: list[SearchResult] = []
        for r in results:
            host = (urlparse(r.url).hostname or "").lower()
            if not host:
                filtered.append(r)
                continue
            if any(host == d or host.endswith("." + d) for d in excluded):
                continue
            filtered.append(r)
        return filtered

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
        """Tier 3: General web search. Tries keyed providers in order, then
        falls back to DuckDuckGo (always available, no key required)."""
        raw_keys = user_settings.get("searchApiKeys")
        api_keys: dict[str, object] = raw_keys if isinstance(raw_keys, dict) else {}

        for name, attempt in (
            ("Google CSE", self._try_google_cse),
            ("Serper", self._try_serper),
            ("Brave", self._try_brave),
            ("Tavily", self._try_tavily),
        ):
            results = await attempt(query, max_results, api_keys, name)
            if results:
                return results

        # Final fallback: DuckDuckGo Lite (no key required)
        from app.services.tier3_search_clients import (  # noqa: PLC0415
            DuckDuckGoClient,
        )

        try:
            return await DuckDuckGoClient().search(query, max_results)
        except Exception:
            logger.exception("DuckDuckGo fallback failed")
            return []

    @staticmethod
    async def _try_google_cse(
        query: str,
        max_results: int,
        api_keys: dict[str, object],
        name: str,
    ) -> list[SearchResult]:
        key = api_keys.get("googleCseApiKey")
        engine = api_keys.get("googleCseEngineId")
        if not (isinstance(key, str) and isinstance(engine, str) and key and engine):
            return []
        from app.services.tier3_search_clients import GoogleCSEClient  # noqa: PLC0415

        try:
            return await GoogleCSEClient().search(query, key, engine, max_results)
        except Exception:
            logger.exception("%s search failed, trying next", name)
            return []

    @staticmethod
    async def _try_serper(
        query: str,
        max_results: int,
        api_keys: dict[str, object],
        name: str,
    ) -> list[SearchResult]:
        key = api_keys.get("serperApiKey")
        if not (isinstance(key, str) and key):
            return []
        from app.services.tier3_search_clients import SerperClient  # noqa: PLC0415

        try:
            return await SerperClient().search(query, key, max_results)
        except Exception:
            logger.exception("%s search failed, trying next", name)
            return []

    @staticmethod
    async def _try_brave(
        query: str,
        max_results: int,
        api_keys: dict[str, object],
        name: str,
    ) -> list[SearchResult]:
        key = api_keys.get("braveSearchApiKey")
        if not (isinstance(key, str) and key):
            return []
        from app.services.tier3_search_clients import BraveSearchClient  # noqa: PLC0415

        try:
            return await BraveSearchClient().search(query, key, max_results)
        except Exception:
            logger.exception("%s search failed, trying next", name)
            return []

    @staticmethod
    async def _try_tavily(
        query: str,
        max_results: int,
        api_keys: dict[str, object],
        name: str,
    ) -> list[SearchResult]:
        key = api_keys.get("tavilyApiKey")
        if not (isinstance(key, str) and key):
            return []
        from app.services.tier3_search_clients import TavilyClient  # noqa: PLC0415

        try:
            return await TavilyClient().search(query, key, max_results)
        except Exception:
            logger.exception("%s search failed, trying next", name)
            return []

    async def _search_searxng(
        self,
        query: str,
        max_results: int,
        user_settings: dict[str, object] | None = None,
    ) -> list[SearchResult]:
        """Tier 4: SearXNG general web search (user's own instance)."""
        user_url = user_settings.get("searxngUrl") if user_settings else None
        searxng_url = (
            user_url if isinstance(user_url, str) and user_url.strip() else None
        )
        if searxng_url:
            from app.core.config import settings  # noqa: PLC0415

            if not settings.LOCAL_MODE:
                try:
                    await assert_public_url(searxng_url)
                except UrlNotAllowedError:
                    logger.warning(
                        "Refusing user SearXNG URL in a private/internal range"
                    )
                    return []
        return await web_search_service.search(
            query,
            max_results=max_results,
            academic_only=False,
            category="general",
            time_range="",
            searxng_url=searxng_url,
        )


# Singleton
search_router = SearchRouter()
