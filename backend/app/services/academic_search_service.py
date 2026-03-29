"""
Academic Search Service — multi-provider academic search with deduplication.

Tier 1 of the tiered research architecture. Always available, no API keys needed.
Providers: OpenAlex, Semantic Scholar, CrossRef, CORE (optional API key).
"""

import asyncio
import logging
from dataclasses import dataclass, field

import aiohttp

from app.services.web_search_service import SearchResult

logger = logging.getLogger(__name__)

# Polite pool identifiers
_OPENALEX_MAILTO = "admin@curriculum-curator.app"
_CROSSREF_MAILTO = "admin@curriculum-curator.app"


@dataclass
class AcademicWork:
    """Normalized academic paper/work from any provider."""

    title: str
    url: str
    doi: str | None = None
    abstract: str | None = None
    authors: list[str] = field(default_factory=list)
    publication_year: int | None = None
    source_name: str | None = None
    citation_count: int | None = None
    provider: str = ""

    def to_search_result(self) -> SearchResult:
        """Convert to the existing SearchResult class used elsewhere."""
        # Build academic score from citation count
        score = 0.3  # Base score for academic sources
        if self.citation_count is not None:
            if self.citation_count >= 100:
                score = 1.0
            elif self.citation_count >= 50:
                score = 0.9
            elif self.citation_count >= 10:
                score = 0.7
            elif self.citation_count >= 1:
                score = 0.5

        description_parts: list[str] = []
        if self.authors:
            description_parts.append(f"Authors: {', '.join(self.authors[:3])}")
        if self.publication_year:
            description_parts.append(f"Year: {self.publication_year}")
        if self.citation_count is not None:
            description_parts.append(f"Citations: {self.citation_count}")

        return SearchResult(
            title=self.title,
            url=self.url,
            content=self.abstract,
            description=" | ".join(description_parts) if description_parts else None,
            source=self.source_name or self.provider,
            published_date=str(self.publication_year)
            if self.publication_year
            else None,
            academic_score=score,
        )


class OpenAlexClient:
    """Client for the OpenAlex API (free, no key required)."""

    BASE_URL = "https://api.openalex.org"

    async def search_works(
        self, query: str, max_results: int = 20
    ) -> list[AcademicWork]:
        """Search OpenAlex for academic works."""
        params = {
            "search": query,
            "per_page": min(max_results, 50),
            "mailto": _OPENALEX_MAILTO,
        }
        url = f"{self.BASE_URL}/works"

        try:
            async with (
                aiohttp.ClientSession(
                    timeout=aiohttp.ClientTimeout(total=15)
                ) as session,
                session.get(url, params=params) as response,
            ):
                if response.status != 200:
                    logger.warning("OpenAlex returned status %d", response.status)
                    return []

                data = await response.json()
                results: list[AcademicWork] = []

                for item in data.get("results", []):
                    # Extract authors
                    authors: list[str] = []
                    for authorship in item.get("authorships", [])[:5]:
                        author = authorship.get("author", {})
                        name = author.get("display_name")
                        if name:
                            authors.append(name)

                    # Extract DOI
                    doi = item.get("doi")
                    if doi and doi.startswith("https://doi.org/"):
                        doi = doi[len("https://doi.org/") :]

                    # Primary URL: prefer DOI link, fall back to OpenAlex landing page
                    landing_url = item.get("doi") or item.get("id", "")

                    # Source/venue name
                    primary_location = item.get("primary_location") or {}
                    source = primary_location.get("source") or {}
                    source_name = source.get("display_name")

                    results.append(
                        AcademicWork(
                            title=item.get("display_name", item.get("title", "")),
                            url=landing_url,
                            doi=doi,
                            abstract=_reconstruct_abstract(
                                item.get("abstract_inverted_index")
                            ),
                            authors=authors,
                            publication_year=item.get("publication_year"),
                            source_name=source_name,
                            citation_count=item.get("cited_by_count"),
                            provider="openalex",
                        )
                    )

                return results

        except Exception:
            logger.exception("OpenAlex search failed")
            return []


class SemanticScholarClient:
    """Client for the Semantic Scholar API (free tier)."""

    BASE_URL = "https://api.semanticscholar.org/graph/v1"

    async def search_papers(
        self, query: str, max_results: int = 20
    ) -> list[AcademicWork]:
        """Search Semantic Scholar for papers."""
        params = {
            "query": query,
            "limit": min(max_results, 100),
            "fields": "title,url,abstract,authors,year,venue,citationCount,externalIds",
        }
        url = f"{self.BASE_URL}/paper/search"

        try:
            async with (
                aiohttp.ClientSession(
                    timeout=aiohttp.ClientTimeout(total=15)
                ) as session,
                session.get(url, params=params) as response,
            ):
                if response.status != 200:
                    logger.warning(
                        "Semantic Scholar returned status %d", response.status
                    )
                    return []

                data = await response.json()
                results: list[AcademicWork] = []

                for item in data.get("data", []):
                    authors = [
                        a.get("name", "")
                        for a in item.get("authors", [])[:5]
                        if a.get("name")
                    ]

                    external_ids = item.get("externalIds") or {}
                    doi = external_ids.get("DOI")

                    results.append(
                        AcademicWork(
                            title=item.get("title", ""),
                            url=item.get("url", ""),
                            doi=doi,
                            abstract=item.get("abstract"),
                            authors=authors,
                            publication_year=item.get("year"),
                            source_name=item.get("venue"),
                            citation_count=item.get("citationCount"),
                            provider="semantic_scholar",
                        )
                    )

                return results

        except Exception:
            logger.exception("Semantic Scholar search failed")
            return []


class CrossRefSearchClient:
    """Client for the CrossRef API (free, no key, polite pool with mailto)."""

    BASE_URL = "https://api.crossref.org"

    async def search_works(
        self, query: str, max_results: int = 20
    ) -> list[AcademicWork]:
        """Search CrossRef for works matching a query."""
        params = {
            "query": query,
            "rows": min(max_results, 50),
            "sort": "relevance",
            "order": "desc",
            "mailto": _CROSSREF_MAILTO,
        }
        url = f"{self.BASE_URL}/works"

        try:
            async with (
                aiohttp.ClientSession(
                    timeout=aiohttp.ClientTimeout(total=15)
                ) as session,
                session.get(url, params=params) as response,
            ):
                if response.status != 200:
                    logger.warning("CrossRef search returned status %d", response.status)
                    return []

                data = await response.json()
                items = data.get("message", {}).get("items", [])
                results: list[AcademicWork] = []

                for item in items:
                    # Title
                    titles = item.get("title", [])
                    title = titles[0] if titles else ""
                    if not title:
                        continue

                    # DOI
                    doi = item.get("DOI")

                    # URL
                    work_url = f"https://doi.org/{doi}" if doi else item.get("URL", "")

                    # Authors
                    authors: list[str] = []
                    for author in item.get("author", [])[:5]:
                        given = author.get("given", "")
                        family = author.get("family", "")
                        if given and family:
                            authors.append(f"{given} {family}")
                        elif family:
                            authors.append(family)

                    # Publication year
                    pub_year = None
                    for date_key in ("published-print", "published-online", "published"):
                        date_parts = item.get(date_key, {}).get("date-parts", [[]])
                        if date_parts and date_parts[0]:
                            pub_year = date_parts[0][0]
                            break

                    # Source/venue
                    container = item.get("container-title", [])
                    source_name = container[0] if container else item.get("publisher")

                    # Citation count
                    citation_count = item.get("is-referenced-by-count")

                    # Abstract (CrossRef sometimes includes it)
                    abstract = item.get("abstract")
                    if abstract:
                        # Strip JATS XML tags if present
                        import re  # noqa: PLC0415

                        abstract = re.sub(r"<[^>]+>", "", abstract).strip()

                    results.append(
                        AcademicWork(
                            title=title,
                            url=work_url,
                            doi=doi,
                            abstract=abstract,
                            authors=authors,
                            publication_year=pub_year,
                            source_name=source_name,
                            citation_count=citation_count,
                            provider="crossref",
                        )
                    )

                return results

        except Exception:
            logger.exception("CrossRef search failed")
            return []


class CORESearchClient:
    """Client for the CORE API (free with registration, 10K results/month)."""

    BASE_URL = "https://api.core.ac.uk/v3"

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key

    async def search_works(
        self, query: str, max_results: int = 20
    ) -> list[AcademicWork]:
        """Search CORE for open access works."""
        if not self.api_key:
            return []

        headers = {"Authorization": f"Bearer {self.api_key}"}
        params = {
            "q": query,
            "limit": min(max_results, 100),
        }
        url = f"{self.BASE_URL}/search/works"

        try:
            async with (
                aiohttp.ClientSession(
                    timeout=aiohttp.ClientTimeout(total=15),
                    headers=headers,
                ) as session,
                session.get(url, params=params) as response,
            ):
                if response.status == 401:
                    logger.warning("CORE API key is invalid or expired")
                    return []
                if response.status != 200:
                    logger.warning("CORE search returned status %d", response.status)
                    return []

                data = await response.json()
                results: list[AcademicWork] = []

                for item in data.get("results", []):
                    title = item.get("title", "")
                    if not title:
                        continue

                    # DOI
                    doi = item.get("doi")
                    if doi and doi.startswith("https://doi.org/"):
                        doi = doi[len("https://doi.org/") :]

                    # URL: prefer download URL, then DOI link, then CORE page
                    download_url = item.get("downloadUrl")
                    work_url = (
                        download_url
                        or (f"https://doi.org/{doi}" if doi else None)
                        or item.get("sourceFulltextUrls", [""])[0]
                        or f"https://core.ac.uk/works/{item.get('id', '')}"
                    )

                    # Authors
                    authors: list[str] = []
                    for author in item.get("authors", [])[:5]:
                        name = author.get("name") if isinstance(author, dict) else author
                        if name:
                            authors.append(str(name))

                    # Year
                    pub_year = item.get("yearPublished")

                    # Abstract
                    abstract = item.get("abstract")

                    # Source
                    source_name = item.get("publisher") or item.get("dataProvider")

                    # Citation count (CORE doesn't always have this)
                    citation_count = item.get("citationCount")

                    results.append(
                        AcademicWork(
                            title=title,
                            url=work_url,
                            doi=doi,
                            abstract=abstract,
                            authors=authors,
                            publication_year=pub_year,
                            source_name=source_name,
                            citation_count=citation_count,
                            provider="core",
                        )
                    )

                return results

        except Exception:
            logger.exception("CORE search failed")
            return []


class AcademicSearchService:
    """Coordinates academic search across providers with deduplication."""

    def __init__(self) -> None:
        self.openalex = OpenAlexClient()
        self.semantic_scholar = SemanticScholarClient()
        self.crossref = CrossRefSearchClient()
        self.core = CORESearchClient()

    async def search(
        self,
        query: str,
        max_results: int = 20,
        core_api_key: str | None = None,
    ) -> list[AcademicWork]:
        """Run all providers concurrently, deduplicate by DOI, rank by citations.

        CORE is only queried if an API key is provided (free registration required).
        """
        # Build the list of coroutines to run
        tasks: list[asyncio.Task[list[AcademicWork]]] = []

        tasks.append(asyncio.ensure_future(self.openalex.search_works(query, max_results)))
        tasks.append(
            asyncio.ensure_future(self.semantic_scholar.search_papers(query, max_results))
        )
        tasks.append(
            asyncio.ensure_future(self.crossref.search_works(query, max_results))
        )

        # CORE: only if API key provided
        if core_api_key:
            core_client = CORESearchClient(api_key=core_api_key)
            tasks.append(
                asyncio.ensure_future(core_client.search_works(query, max_results))
            )

        raw_results = await asyncio.gather(*tasks, return_exceptions=True)

        # Flatten results, handling exceptions gracefully
        provider_names = ["OpenAlex", "Semantic Scholar", "CrossRef"]
        if core_api_key:
            provider_names.append("CORE")

        all_works_flat: list[AcademicWork] = []
        for i, result in enumerate(raw_results):
            if isinstance(result, BaseException):
                logger.warning("%s failed: %s", provider_names[i], result)
            else:
                all_works_flat.extend(result)

        return self._deduplicate_and_rank(all_works_flat, max_results)

    @staticmethod
    def _deduplicate_and_rank(
        works: list[AcademicWork], max_results: int
    ) -> list[AcademicWork]:
        """Deduplicate by DOI (keep richest entry) and rank by citations."""
        seen_dois: dict[str, AcademicWork] = {}
        all_works: list[AcademicWork] = []

        for work in works:
            if work.doi:
                doi_lower = work.doi.lower()
                if doi_lower in seen_dois:
                    existing = seen_dois[doi_lower]
                    # Keep the one with more citations or more complete data
                    if (work.citation_count or 0) > (existing.citation_count or 0):
                        seen_dois[doi_lower] = work
                    continue
                seen_dois[doi_lower] = work
            all_works.append(work)

        # Replace duplicates with best version
        final: list[AcademicWork] = []
        seen_dois_added: set[str] = set()
        for work in all_works:
            if work.doi:
                doi_lower = work.doi.lower()
                if doi_lower in seen_dois_added:
                    continue
                seen_dois_added.add(doi_lower)
                final.append(seen_dois[doi_lower])
            else:
                final.append(work)

        # Sort by citation count (descending), None last
        final.sort(key=lambda w: w.citation_count or 0, reverse=True)

        return final[:max_results]

    def to_search_results(self, works: list[AcademicWork]) -> list[SearchResult]:
        """Convert academic works to SearchResult objects."""
        return [w.to_search_result() for w in works]


def _reconstruct_abstract(inverted_index: dict[str, list[int]] | None) -> str | None:
    """Reconstruct abstract from OpenAlex inverted index format."""
    if not inverted_index:
        return None

    # Build position→word mapping
    words: dict[int, str] = {}
    for word, positions in inverted_index.items():
        for pos in positions:
            words[pos] = word

    if not words:
        return None

    # Reconstruct in order
    max_pos = max(words.keys())
    return " ".join(words.get(i, "") for i in range(max_pos + 1))


# Singleton
academic_search_service = AcademicSearchService()
