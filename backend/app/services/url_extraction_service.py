"""
URL Extraction Service — fetch and classify content from user-provided URLs.

Reuses existing web_search_service.fetch_page_content() and summarize_url().
"""

import asyncio
import logging
import re
from dataclasses import dataclass, field

from app.services.web_search_service import web_search_service

logger = logging.getLogger(__name__)


@dataclass
class ExtractedUrl:
    """Extracted and classified content from a single URL."""

    url: str
    title: str | None = None
    content: str | None = None
    summary: str | None = None
    key_points: list[str] = field(default_factory=list)
    academic_score: float = 0.0
    content_type: str = "unknown"
    error: str | None = None


class UrlExtractionService:
    """Fetches, summarizes, and classifies content from URLs."""

    async def extract_urls(
        self,
        urls: list[str],
        summarize: bool = True,
        purpose: str = "general",
    ) -> list[ExtractedUrl]:
        """Extract content from multiple URLs concurrently.

        One failure doesn't block others.
        """
        tasks = [self._extract_single(url, summarize, purpose) for url in urls]
        return list(await asyncio.gather(*tasks))

    async def _extract_single(
        self, url: str, summarize: bool, purpose: str
    ) -> ExtractedUrl:
        """Extract content from a single URL."""
        try:
            if summarize:
                result = await web_search_service.summarize_url(
                    url=url, purpose=purpose, max_length=1000, include_key_points=True
                )
                content = await web_search_service.fetch_page_content(url)
                content_type = self._classify_content_type(url, content)

                return ExtractedUrl(
                    url=url,
                    title=self._extract_title(content),
                    content=content[:2000] if content else None,
                    summary=result.get("summary"),
                    key_points=result.get("key_points", []),
                    academic_score=result.get("academic_score", 0.0),
                    content_type=content_type,
                )

            content = await web_search_service.fetch_page_content(url)
            # Reuse academic scoring heuristic from web search service
            academic_score = web_search_service._calculate_academic_score(  # pyright: ignore[reportPrivateUsage]
                url, "", content
            )
            content_type = self._classify_content_type(url, content)

            return ExtractedUrl(
                url=url,
                title=self._extract_title(content),
                content=content[:2000] if content else None,
                academic_score=academic_score,
                content_type=content_type,
            )

        except Exception as e:
            logger.warning("Failed to extract URL %s: %s", url, e)
            return ExtractedUrl(url=url, error=str(e))

    def _classify_content_type(self, url: str, content: str) -> str:
        """Classify the content type using URL patterns and content indicators."""
        url_lower = url.lower()
        content_lower = content.lower() if content else ""

        # Video platforms
        video_domains = ("youtube.com", "youtu.be", "vimeo.com", "dailymotion.com")
        if any(d in url_lower for d in video_domains):
            return "video"

        # Academic papers — DOI or known hosts
        is_paper = (
            "doi.org" in url_lower
            or "arxiv.org" in url_lower
            or bool(re.search(r"\bdoi\b.*10\.\d{4,}", content_lower))
            or bool(re.search(r"\babstract\b.*\bintroduction\b", content_lower))
        )
        if is_paper:
            return "paper"

        # Syllabus indicators
        syllabus_signals = [
            "learning outcomes",
            "unit outline",
            "course outline",
            "syllabus",
            "week 1",
            "week 2",
            "assessment",
            "credit points",
        ]
        syllabus_hits = sum(1 for s in syllabus_signals if s in content_lower)
        if syllabus_hits >= 3:
            return "syllabus"

        # Educational domain + content heuristic
        if re.search(r"\.(edu|ac\.[a-z]{2,3})", url_lower):
            return "syllabus" if syllabus_hits >= 1 else "paper"

        # Blog-like URLs
        blog_domains = ("medium.com", "blog", "wordpress", "substack")
        if any(d in url_lower for d in blog_domains):
            return "blog"

        return "unknown"

    def _extract_title(self, content: str | None) -> str | None:
        """Try to extract a title from the first line of content."""
        if not content:
            return None
        first_line = content.strip().split("\n")[0].strip()
        if first_line and len(first_line) < 200:
            return first_line
        return None


# Singleton
url_extraction_service = UrlExtractionService()
