"""
Web Search Service using SearXNG for academic content research
"""

import re
from datetime import datetime
from typing import Any
from urllib.parse import urlencode

import aiohttp

from app.core.config import settings
from app.services.llm_service import LLMService


class WebSearchError(Exception):
    """Custom exception for web search errors."""



class SearchResult:
    """Represents a single search result"""

    def __init__(
        self,
        title: str,
        url: str,
        content: str | None = None,
        description: str | None = None,
        source: str | None = None,
        published_date: str | None = None,
        academic_score: float = 0.0,
    ):
        self.title = title
        self.url = url
        self.content = content
        self.description = description
        self.source = source
        self.published_date = published_date
        self.academic_score = academic_score  # 0.0-1.0 confidence it's academic

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "url": self.url,
            "content": self.content,
            "description": self.description,
            "source": self.source,
            "published_date": self.published_date,
            "academic_score": self.academic_score,
        }


class WebSearchService:
    """Service for web search and content extraction using SearXNG"""

    def __init__(self, llm_service: LLMService | None = None):
        self.searxng_url = getattr(settings, "SEARXNG_URL", "http://localhost:8080")
        self.timeout = 30  # seconds
        self.llm_service = llm_service or LLMService()

        # Academic domain patterns (higher priority)
        self.academic_domains = [
            r"\.edu$",
            r"\.ac\.[a-z]{2,3}$",  # .ac.uk, .ac.nz, etc.
            r"\.edu\.[a-z]{2,3}$",
            r"arxiv\.org$",
            r"researchgate\.net$",
            r"scholar\.google\.com$",
            r"\.gov$",
            r"\.org$",  # Many academic organizations
        ]

        # Low-quality domain patterns (filter out)
        self.low_quality_domains = [
            r"\.blogspot\.",
            r"\.wordpress\.",
            r"\.wixsite\.",
            r"\.weebly\.",
            r"\.tumblr\.",
            r"\.medium\.com$",
            r"wikipedia\.org$",  # Good for overview, not for citations
        ]

    def _calculate_academic_score(self, url: str, title: str, content: str) -> float:
        """Calculate how academic a source is (0.0-1.0)"""
        score = 0.0

        # Check domain
        for pattern in self.academic_domains:
            if re.search(pattern, url, re.IGNORECASE):
                score += 0.4
                break

        # Check for low-quality domains
        for pattern in self.low_quality_domains:
            if re.search(pattern, url, re.IGNORECASE):
                score -= 0.3
                break

        # Check for academic indicators in title/content
        academic_indicators = [
            r"journal",
            r"review",
            r"study",
            r"research",
            r"article",
            r"paper",
            r"thesis",
            r"dissertation",
            r"conference",
            r"proceedings",
            r"volume",
            r"issue",
            r"doi:",
            r"issn",
            r"peer.?review",
        ]

        text_to_check = f"{title} {content}".lower()
        for indicator in academic_indicators:
            if re.search(indicator, text_to_check, re.IGNORECASE):
                score += 0.1

        # Check for references/citations
        if re.search(
            r"references|bibliography|citations?", text_to_check, re.IGNORECASE
        ):
            score += 0.2

        # Check for author affiliations
        if re.search(
            r"university|college|institute|laboratory|faculty",
            text_to_check,
            re.IGNORECASE,
        ):
            score += 0.1

        return min(max(score, 0.0), 1.0)

    async def search(
        self,
        query: str,
        max_results: int = 10,
        academic_only: bool = True,
        timeout: int = 30,
    ) -> list[SearchResult]:
        """
        Search using SearXNG instance

        Args:
            query: Search query string
            max_results: Maximum number of results to return
            academic_only: Filter to academic sources only
            timeout: Request timeout in seconds

        Returns:
            List of SearchResult objects
        """
        # Build SearXNG API URL
        params = {
            "q": query,
            "format": "json",
            "language": "en",
            "safesearch": 1,  # Moderate safe search
            "categories": "science",  # Focus on science/academic
            "time_range": "year",  # Last year only
        }

        search_url = f"{self.searxng_url}/search?{urlencode(params)}"

        try:
            async with (
                aiohttp.ClientSession(
                    timeout=aiohttp.ClientTimeout(total=timeout)
                ) as session,
                session.get(search_url) as response,
            ):
                if response.status != 200:
                    raise WebSearchError(f"SearXNG returned status {response.status}")

                data = await response.json()

                results = []
                for item in data.get("results", [])[:max_results]:
                    # Extract basic info
                    title = item.get("title", "")
                    url = item.get("url", "")
                    content = item.get("content", "")
                    description = item.get("description", "")

                    # Calculate academic score
                    academic_score = self._calculate_academic_score(url, title, content)

                    # Filter if academic_only is True
                    if academic_only and academic_score < 0.3:
                        continue

                    # Extract source domain
                    source = None
                    if url:
                        try:
                            source = url.split("//")[-1].split("/")[0]
                        except (IndexError, AttributeError):
                            source = url

                    # Extract published date if available
                    published_date = item.get("publishedDate")

                    result = SearchResult(
                        title=title,
                        url=url,
                        content=content,
                        description=description,
                        source=source,
                        published_date=published_date,
                        academic_score=academic_score,
                    )
                    results.append(result)

                return results

        except TimeoutError as e:
            raise WebSearchError("Search request timed out") from e
        except Exception as e:
            raise WebSearchError(f"Search failed: {e!s}") from e

    async def fetch_page_content(self, url: str, timeout: int = 30) -> str:
        """
        Fetch and extract main content from a webpage

        Args:
            url: URL to fetch
            timeout: Request timeout in seconds

        Returns:
            Extracted text content
        """
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

        try:
            async with (
                aiohttp.ClientSession(
                    timeout=aiohttp.ClientTimeout(total=timeout)
                ) as session,
                session.get(url, headers=headers) as response,
            ):
                if response.status != 200:
                    raise WebSearchError(
                        f"Failed to fetch page: HTTP {response.status}"
                    )

                html = await response.text()

                # Simple content extraction (in production, use something like trafilatura or readability)
                # This is a basic implementation
                content = self._extract_content(html)

                if not content or len(content.strip()) < 100:
                    # Fallback: return first 5000 characters of HTML text
                    text = re.sub(r"<[^>]+>", " ", html)
                    text = re.sub(r"\s+", " ", text)
                    content = text[:5000]

                return content.strip()

        except TimeoutError as e:
            raise WebSearchError("Page fetch timed out") from e
        except WebSearchError:
            raise
        except Exception as e:
            raise WebSearchError(f"Failed to fetch page: {e!s}") from e

    def _extract_content(self, html: str) -> str:
        """Basic HTML content extraction."""
        # Remove scripts and styles
        html = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL)
        html = re.sub(r"<style[^>]*>.*?</style>", "", html, flags=re.DOTALL)

        # Try to find main content (common patterns)
        patterns = [
            r"<main[^>]*>(.*?)</main>",
            r"<article[^>]*>(.*?)</article>",
            r'<div[^>]*class="[^"]*content[^"]*"[^>]*>(.*?)</div>',
            r'<div[^>]*id="content"[^>]*>(.*?)</div>',
            r'<div[^>]*class="[^"]*post[^"]*"[^>]*>(.*?)</div>',
        ]

        for pattern in patterns:
            match = re.search(pattern, html, re.DOTALL | re.IGNORECASE)
            if match:
                content_html = match.group(1)
                # Remove all HTML tags
                text = re.sub(r"<[^>]+>", " ", content_html)
                text = re.sub(r"\s+", " ", text)
                return text.strip()

        # Fallback: extract text from body
        body_match = re.search(
            r"<body[^>]*>(.*?)</body>", html, re.DOTALL | re.IGNORECASE
        )
        if body_match:
            body_html = body_match.group(1)
            # Remove all HTML tags
            text = re.sub(r"<[^>]+>", " ", body_html)
            text = re.sub(r"\s+", " ", text)
            return text.strip()

        return ""

    async def summarize_url(
        self,
        url: str,
        purpose: str = "general",
        max_length: int = 1000,
        include_key_points: bool = True,
    ) -> dict[str, Any]:
        """
        Fetch and summarize a webpage for educational purposes

        Args:
            url: URL to summarize
            purpose: "syllabus_description", "ulo", "content", "assessment", or "general"
            max_length: Maximum summary length
            include_key_points: Whether to extract key points

        Returns:
            Dictionary with summary, key points, and metadata
        """
        # Fetch page content
        content = await self.fetch_page_content(url)

        if not content:
            raise WebSearchError("No content extracted from page")

        # Create prompt based on purpose
        purpose_prompts = {
            "syllabus_description": "Summarize this for inclusion in a university course syllabus description. Focus on key concepts, relevance to education, and practical applications.",
            "ulo": "Extract key learning outcomes from this content. Format as bullet points starting with action verbs (e.g., 'Analyze', 'Design', 'Evaluate').",
            "content": "Summarize this for use as educational content. Focus on clarity, structure, and pedagogical value.",
            "assessment": "Extract potential assessment questions or topics from this content. Focus on measurable learning outcomes.",
            "general": "Provide a concise summary of this content for academic reference.",
        }

        prompt = purpose_prompts.get(purpose, purpose_prompts["general"])

        # Prepare LLM prompt
        llm_prompt = f"""{prompt}

Content to summarize:
{content[:8000]}  # Limit content length

Please provide:
1. A concise summary ({max_length} characters max)
2. 3-5 key points (if relevant)
3. Relevance to education/teaching
4. Any limitations or biases to note"""

        # Get summary from LLM (ensure we get string, not generator)
        summary_result = await self.llm_service.generate_text(
            prompt=llm_prompt,
            max_tokens=1500,
            temperature=0.3,  # Lower temperature for more factual output
            stream=False,  # Ensure we get string, not generator
        )

        # Handle both string and generator cases
        if isinstance(summary_result, str):
            summary = summary_result
        else:
            # If it's a generator, collect all chunks
            summary = "".join([chunk async for chunk in summary_result])

        # Extract key points if requested
        key_points: list[str] = []
        if include_key_points:
            key_points_prompt = f"""Extract 3-5 key points from this content for educational purposes:

{content[:4000]}

Format as bullet points starting with action verbs."""

            key_points_result = await self.llm_service.generate_text(
                prompt=key_points_prompt,
                max_tokens=500,
                temperature=0.3,
                stream=False,
            )

            # Handle both string and generator cases
            if isinstance(key_points_result, str):
                key_points_text = key_points_result
            else:
                key_points_text = "".join([chunk async for chunk in key_points_result])

            # Parse bullet points
            points = re.findall(
                r"[-•*]\s*(.+?)(?=\n[-•*]|\n\n|$)", key_points_text, re.DOTALL
            )
            key_points = [p.strip() for p in points if p.strip()]

        # Calculate academic score
        academic_score = self._calculate_academic_score(url, "", content)

        return {
            "url": url,
            "summary": summary.strip(),
            "key_points": key_points[:5],  # Limit to 5 points
            "purpose": purpose,
            "academic_score": academic_score,
            "content_length": len(content),
            "summary_length": len(summary),
            "timestamp": datetime.now().isoformat(),
        }

    async def search_and_summarize(
        self,
        query: str,
        purpose: str = "general",
        max_results: int = 3,
        summarize_top_n: int = 2,
    ) -> dict[str, Any]:
        """
        Search for academic sources and summarize the top results

        Args:
            query: Search query
            purpose: Purpose of summarization
            max_results: Maximum search results to return
            summarize_top_n: Number of top results to summarize

        Returns:
            Dictionary with search results and summaries
        """
        # Perform search
        search_results = await self.search(
            query=query,
            max_results=max_results,
            academic_only=True,
        )

        # Summarize top N results
        summaries = []
        for result in search_results[:summarize_top_n]:
            try:
                summary = await self.summarize_url(
                    url=result.url,
                    purpose=purpose,
                    max_length=800,
                    include_key_points=True,
                )
                summaries.append(summary)
            except Exception:
                # Skip if summarization fails
                continue

        return {
            "query": query,
            "purpose": purpose,
            "search_results": [r.to_dict() for r in search_results],
            "summaries": summaries,
            "total_results": len(search_results),
            "summarized_count": len(summaries),
        }


# Create singleton instance
web_search_service = WebSearchService()
