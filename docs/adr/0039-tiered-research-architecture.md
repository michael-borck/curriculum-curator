# ADR-0039: Tiered Research Architecture with Propose/Apply Workflows

Date: 2026-02-22

## Status

Accepted (supersedes search provider strategy in ADR-0021)

## Context

ADR-0021 established the Web Search and Citation Integration system with SearXNG as the sole search provider. The backend is fully implemented (search service, research source library, citation formatting, content synthesis) but has two critical issues:

1. **SearXNG is a hard dependency.** It requires a separately-hosted instance. Google actively blocks SearXNG instances (only 25/91 public instances had working Google results as of January 2025). The current instance runs on a private Tailscale network, making it inaccessible to other users or deployments.

2. **No frontend exists.** The entire research backend is API-complete but user-invisible — there are no React components, pages, routes, or navigation for research features.

Additionally, two distinct research workflows have been identified through user analysis:

- **Workflow A ("What should this unit look like?"):** An educator starting a new unit wants to discover what other universities teach for a similar topic, select relevant outlines, and have the AI merge them into a 12-week scaffold.

- **Workflow B ("Here are URLs I found"):** An educator pastes URLs they've already found (syllabi, blogs, videos, papers) and wants the app to extract content, classify it, and propose how it maps to their unit structure — with the ability to review and correct before committing.

Both workflows require search capabilities that work across different deployment contexts (Ollama-only, frontier API, power users with SearXNG).

### Research Findings on Search APIs

Investigation of the current landscape revealed:

- **Free academic APIs** exist with excellent coverage: OpenAlex (260M+ works, CC0 data, no key needed), Semantic Scholar (200M+ papers, free tier), CrossRef (150M+ records), CORE (300M+ with full-text)
- **Frontier LLM providers** (OpenAI, Anthropic, Gemini) now offer programmatic web search at ~$10/1,000 queries via their APIs
- **General web search APIs** have viable free/cheap tiers: Google Custom Search (100 free/day), Brave ($5/month credit), Tavily (1,000 free/month)
- **Bing API was retired** in August 2025
- **Headless browser scraping** of Google is a losing battle (CAPTCHAs, AI overviews, behavioural detection)
- **DuckDuckGo** has no official API; the unofficial library is fragile and rate-limited
- **Ollama models** cannot perform web search on their own — they can make tool calls, but the search backend must be provided externally

## Decision

### 1. Tiered Search Architecture

Replace the single-provider SearXNG dependency with a four-tier search system, ordered by availability:

| Tier | Provider | Config Required | Availability |
|------|----------|----------------|--------------|
| **1 — Academic** | OpenAlex + Semantic Scholar | None (free public APIs) | Always |
| **2 — LLM-native** | OpenAI/Anthropic/Gemini web search tool | None (automatic if frontier key configured) | Frontier API users |
| **3 — General web** | Google CSE, Brave, or Tavily | User adds API key in settings | Opt-in |
| **4 — SearXNG** | User's own instance | User provides instance URL | Power users |

A `SearchRouter` service selects the best available tier based on the user's configuration, with graceful fallback.

**Tier 1 is always available with zero configuration.** This is critical for the BYOK philosophy (ADR-0037): even an Ollama-only user with no API keys gets academic search capability. OpenAlex requires no authentication — just an HTTP request with a `mailto` parameter for the polite pool.

**Tier 2 is automatic.** If a user has already configured an OpenAI, Anthropic, or Gemini API key for content generation, web search is available through the same key at marginal cost (~$0.01-0.05 per search). No additional configuration needed.

### 2. Two-Phase Propose/Apply Pattern

All research synthesis operations follow a propose-then-apply contract:

- **Propose** (`POST /api/research/{action}`): Takes input data, calls LLM, returns a structured proposal. **No database writes.** The full proposal JSON is returned to the client.

- **Review**: The frontend renders an editable UI where the user can correct the AI's suggestions (reassign resources to different weeks, remove items, edit topics, reorder weeks).

- **Apply** (`POST /api/research/{action}/apply`): Takes the user-corrected proposal and commits it to the database.

This pattern ensures the AI is a **suggestion engine** — the educator always has final say. A bad LLM extraction cannot silently corrupt a unit structure.

Three actions are supported:

| Action | Input | Propose Output | Apply Effect |
|--------|-------|---------------|--------------|
| **Scaffold** | Selected sources + unit title | `ScaffoldUnitResponse` (reuses existing schema) | Creates Unit + ULOs + WeeklyTopics + Assessments |
| **Compare** | Selected sources + existing unit ID | `ComparisonProposal` (gaps, overlaps, suggestions) | Adds selected topics to existing unit |
| **Match reading list** | Selected sources + existing unit ID | `ReadingListProposal` (resource → week mapping with confidence) | Creates ResearchSource entries + optional WeeklyMaterial links |

### 3. URL Import as First-Class Workflow

Rather than forcing users through our search for everything, provide a "paste URLs" input alongside search. Educators already know how to use a browser — our value-add is **processing** what they find, not replacing their browser.

The `UrlExtractionService` batch-fetches user-provided URLs, extracts content, classifies them (syllabus, paper, blog, video), and feeds them into the same propose/apply flow as search results.

### 4. Existing Code Preserved

The existing research backend (ADR-0021) remains intact:

- `web_search_service.py` — SearXNG integration becomes Tier 4; `fetch_page_content()` and `summarize_url()` reused by the URL extraction service
- `research_sources.py` routes — CRUD, citations, synthesis at `/api/sources` unchanged
- `citation_service.py` — 6 citation styles unchanged
- `ResearchSource` + `ContentCitation` models — unchanged

New code is additive: new services, new schemas, new route file at `/api/research`.

## Consequences

### Positive

- **Zero-config search**: Academic search works out of the box for all deployment types, including Ollama-only
- **BYOK-aligned**: Each tier respects the user's infrastructure choices — no hidden API calls or forced dependencies
- **Graceful degradation**: If a tier is unavailable, the router falls back to the next available tier
- **User agency**: Propose/apply pattern means AI never makes unsupervised changes to unit structure
- **Practical UX**: URL paste acknowledges that educators often find resources via their browser, not our search
- **Existing code preserved**: ADR-0021's implementation continues to work; this extends rather than replaces

### Negative

- **Academic search limitations**: OpenAlex indexes scholarly works, not university course websites. Searching for "Data Structures syllabus" may return papers about data structures, not actual course outlines. URL paste is the mitigation for this gap.
- **Extraction quality varies**: Extracting structured outlines from arbitrary web pages is LLM-dependent. Smaller Ollama models may produce lower quality extraction than frontier models.
- **Multiple HTTP clients**: Four tiers means four external API integrations to maintain (though Tier 1 APIs are very stable — OpenAlex hasn't changed its API in years).
- **No offline search**: All tiers require internet access. Ollama-only users working offline lose search functionality (but URL import works if they pre-download content).

### Neutral

- **SearXNG is demoted, not removed.** It becomes Tier 4 for power users who want to run their own instance. Not bundled in Docker Compose, not required.
- **LLM-native search cost** is marginal (~$0.01-0.05 per search) on top of generation costs users are already paying.
- **Google Custom Search free tier** (100 queries/day) is sufficient for the typical educator use case — they aren't searching hundreds of times per session.

## Alternatives Considered

### Single Provider (keep SearXNG only)

- Rejected: Creates a hard dependency that breaks in most deployment contexts. Google actively blocks SearXNG instances. Not viable for Electron desktop or standard Docker deployment.

### Academic APIs Only (no general web search)

- Partially adopted as Tier 1. General web search is available as Tier 2-4 but not required. The academic APIs cover the primary use case (finding scholarly references) but miss course outlines on university websites — URL paste covers that gap.

### Playwright/Headless Browser Scraping

- Rejected: Google's anti-bot detection is aggressive (CAPTCHAs, behavioural analysis, IP reputation). AI overviews and sponsored content bury organic results. Maintenance burden is high. Every other option is more reliable.

### Bundled SearXNG in Docker Compose

- Rejected: Adds operational complexity (another container, another service to configure), Google blocking makes results unreliable, and it contradicts the simplicity principle for self-hosted deployments.

## Implementation Notes

### Services Architecture

```
search_router.py          → Picks best available tier, normalises results
academic_search_service.py → OpenAlex + Semantic Scholar clients
url_extraction_service.py  → Batch URL fetch/extract, reuses web_search_service
outline_synthesis_service.py → Scaffold/compare/match proposals via LLM
tier3_search_clients.py    → Google CSE, Brave, Tavily clients
web_search_service.py      → Existing SearXNG (Tier 4)
```

### Endpoints

All new endpoints at `/api/research`:

| Endpoint | Purpose |
|----------|---------|
| `POST /search` | Unified search (router picks tier) |
| `GET /tiers` | Which search tiers are available |
| `POST /extract-urls` | Batch fetch + classify URLs |
| `POST /scaffold` | Propose scaffold from sources |
| `POST /scaffold/apply` | Commit user-corrected scaffold |
| `POST /compare` | Propose comparison to existing unit |
| `POST /compare/apply` | Apply selected suggestions |
| `POST /match-reading-list` | Propose resource → week mapping |
| `POST /match-reading-list/apply` | Save matched readings |
| `PUT /settings` | Update search preferences |

### User Preferences

Stored in `user.teaching_preferences.research` (JSON column, no migration needed):

```json
{
  "preferredTier": 1,
  "searchApiKeys": { "googleCseApiKey": "...", "braveSearchApiKey": "..." },
  "searxngUrl": "http://my-instance:8080"
}
```

## References

- [ADR-0021: Web Search and Citation Integration](0021-web-search-citation-integration.md) — original search/citation design (search strategy superseded by this ADR)
- [ADR-0037: Privacy-First, Local-First, BYOK Architecture](0037-privacy-first-byok-architecture.md) — tiered approach aligns with BYOK principle
- [ADR-0036: Learning Design as Canonical Generation Spec](0036-learning-design-generation-spec.md) — design context injected into synthesis prompts
- [OpenAlex API Documentation](https://docs.openalex.org/)
- [Semantic Scholar API Documentation](https://api.semanticscholar.org/api-docs)
