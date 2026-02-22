"""
Academic Search Service — OpenAlex + Semantic Scholar clients with deduplication.

Tier 1 of the tiered research architecture. Always available, no API keys needed.
"""

import asyncio
import logging
from dataclasses import dataclass, field

import aiohttp

from app.services.web_search_service import SearchResult

logger = logging.getLogger(__name__)

# Polite pool identifier for OpenAlex
_OPENALEX_MAILTO = "admin@curriculum-curator.app"


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


class AcademicSearchService:
    """Coordinates academic search across providers with deduplication."""

    def __init__(self) -> None:
        self.openalex = OpenAlexClient()
        self.semantic_scholar = SemanticScholarClient()

    async def search(self, query: str, max_results: int = 20) -> list[AcademicWork]:
        """Run both clients concurrently, deduplicate by DOI, rank by citations."""
        openalex_results, s2_results = await asyncio.gather(
            self.openalex.search_works(query, max_results),
            self.semantic_scholar.search_papers(query, max_results),
            return_exceptions=True,
        )

        # Handle exceptions gracefully
        if isinstance(openalex_results, BaseException):
            logger.warning("OpenAlex failed: %s", openalex_results)
            openalex_results = []
        if isinstance(s2_results, BaseException):
            logger.warning("Semantic Scholar failed: %s", s2_results)
            s2_results = []

        # Deduplicate by DOI (prefer the entry with more info)
        seen_dois: dict[str, AcademicWork] = {}
        all_works: list[AcademicWork] = []

        for work in [*openalex_results, *s2_results]:
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
