# Search Tier Hardening Plan

Inspired by review of study-buddy's 6-engine search dispatcher (`/Users/michael/Projects/study-buddy/app/api/getSources/route.ts`). The four improvements worth borrowing, ordered small → large.

## Current state (verified 2026-04-14)

- `backend/app/services/tier3_search_clients.py` has `GoogleCSEClient`, `BraveSearchClient`, `TavilyClient`.
- `search_router.SearchRouter._search_tier3` tries them in order.
- `_search_searxng` delegates to `web_search_service.search()` with `academic_only=True` — **bug**: Tier 4 general web search is being filtered to academic-only.
- `web_search_service.search()` hardcodes `categories=science`, `time_range=year`, no retries, no rate limiting, minimal headers.
- No excluded-sites filter anywhere in the pipeline.

## Step 1 — Excluded-sites filter (router-level normalization)

**Files**: `backend/app/services/search_router.py`, `backend/app/core/config.py`

- Add `DEFAULT_EXCLUDED_DOMAINS: list[str] = ["youtube.com", "pinterest.com", "quora.com"]` to `config.py` (env-overridable via `EXCLUDED_SEARCH_DOMAINS` comma-separated).
- Add private helper `SearchRouter._filter_excluded(results, user_settings)`:
  - Reads system defaults + `user_settings.get("excludedDomains", [])`.
  - Drops any `SearchResult` whose `urlparse(url).hostname` matches/endswith any excluded domain (case-insensitive). **Do not** use raw substring match — it blocks `notyoutube.com`.
- Call it at the end of `SearchRouter.search()` before returning — single normalization point, applies to every tier.
- Test: `tests/test_search_router.py` — pass in results with excluded URLs, verify filtered.

## Step 2 — Harden SearXNG in `web_search_service.py`

**File**: `backend/app/services/web_search_service.py`

`search()` is dual-purpose (Tier 4 general + academic `search_and_summarize`). Preserve existing callers via defaults.

1. Class-level rate-limit state:
   - `_last_global_request: float = 0.0`
   - `_request_tracker: dict[str, float] = {}`
   - `GLOBAL_RATE_LIMIT_S = 0.5`, `PER_SERVER_RATE_LIMIT_S = 2.0`
2. `_rate_limit_searxng(server_url)` async helper — respects both limits, prunes tracker if >50.
3. New `search()` signature:
   ```python
   async def search(
       self,
       query: str,
       max_results: int = 10,
       academic_only: bool = True,
       category: str = "science",   # NEW — "general" for Tier 4
       time_range: str = "year",    # NEW — "" for Tier 4
       timeout: int = 30,
   ) -> list[SearchResult]:
   ```
4. Retry + multi-endpoint:
   - Try `["/search", "/"]` in sequence.
   - Retry up to 3× with exponential backoff + jitter (`1s * 2^n + random(0,1s)`, cap 8s) for HTTP 429 / `TimeoutError` / `EAI_AGAIN`.
   - Browser-like headers in `_searxng_headers()` helper (User-Agent, Accept, Accept-Language, Referer=searxng_url, Sec-Ch-Ua, etc.) borrowed from study-buddy.
5. Classify final-failure errors (timeout / DNS / SSL / generic) in the `WebSearchError` message.
6. Fix Tier 4 caller in `search_router._search_searxng`:
   ```python
   return await web_search_service.search(
       query, max_results=max_results,
       academic_only=False, category="general", time_range=""
   )
   ```

Tests (`tests/test_web_search_service.py`): mock `aiohttp`, verify 429→retry→success, all-fail classification, rate-limit sleep, `category`/`time_range` wiring.

## Step 3 — DuckDuckGo client (Tier 3, no API key)

**File**: `backend/app/services/tier3_search_clients.py`

New class `DuckDuckGoClient`:
- GET `https://lite.duckduckgo.com/lite/?q={query}&t=h_&ia=web` with browser UA, 10s timeout.
- Parse HTML with **BeautifulSoup** (already a dep via `html_structural.py`), not regex.
- Look for `<a class="result-link">`; if `href` contains `duckduckgo.com/l/?uddg=`, URL-decode the `uddg` param.
- Drop results where title <10 chars, URL not `http*`, title contains "duckduckgo"/"next page".
- Return up to `max_results` `SearchResult(source="duckduckgo")`.
- On failure: log + return `[]`.

Wire into `search_router._search_tier3` as the **final fallback within Tier 3** (after all keyed providers). This makes Tier 3 always viable — presence of keys just changes priority order.

Update `get_available_tiers`: Tier 3 becomes always-available via DDG fallback; key presence is just a UI hint.

Tests (`tests/test_tier3_search_clients.py`): stub HTML response, verify `uddg` decoding and junk filtering.

## Step 4 — Serper client (Tier 3, single-key Google)

**File**: `backend/app/services/tier3_search_clients.py`

New class `SerperClient`:
- POST `https://google.serper.dev/search`, headers `{"X-API-KEY": key, "Content-Type": "application/json"}`, body `{"q": query, "num": max_results}`.
- Parse `organic[].{title, link, snippet}` → `SearchResult(source="serper")`.
- Error handling: log + `[]`.

Wire into `_search_tier3`: Google CSE → Serper → Brave → Tavily → DuckDuckGo. Read from `api_keys.get("serperApiKey")`.

Tests: mock POST, verify request shape + parsing.

## Step 5 — Frontend settings (optional, after backend)

`frontend/src/features/settings/`:
- Add `serperApiKey` field.
- Add `excludedDomains` textarea → serialize as array in `user_settings`.
- Add `allowDuckDuckGo` toggle (default on, cosmetic).
- Update `SearchSettings`/`UserSettings` TypeScript interfaces.

Skip if backend-only is enough for now — frontend can catch up later.

## Risks / non-obvious points

1. **Dual-purpose `search()`** — verify no other callers break. Grep `web_search_service.search(`.
2. **Class-level rate-limit state** — fine for single-process FastAPI; each worker has its own state under multiple workers (acceptable for politeness, not hard quotas).
3. **DDG HTML fragile** — catch parse exceptions, log zero-result cases, don't alert users.
4. **Serper is paid third party** — same trust model as Brave/Tavily.
5. **Hostname match, not substring** — use `urlparse(url).hostname`, endswith check.

## Verification after each step

```bash
cd backend && .venv/bin/ruff check . && .venv/bin/basedpyright && \
  .venv/bin/pytest tests/test_search_router.py tests/test_tier3_search_clients.py tests/test_web_search_service.py -v
```

Zero errors before moving on.

## Commit sequence

1. `feat(search): add excluded-domains filter to search router`
2. `fix(search): harden SearXNG client with retries, rate limiting, browser headers`
3. `feat(search): add DuckDuckGo fallback client (no API key required)`
4. `feat(search): add Serper.dev client as Google alternative`
5. `feat(settings): expose serper key, excluded domains in user settings` *(optional / frontend)*
