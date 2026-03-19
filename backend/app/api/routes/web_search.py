"""
Web Search API routes for academic content research
"""

import ipaddress
import socket
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api import deps
from app.models.user import User
from app.services.web_search_service import web_search_service

router = APIRouter()


def _is_private_url(url: str) -> bool:
    """Check if a URL resolves to a private/internal IP address (SSRF protection)."""
    try:
        from urllib.parse import urlparse  # noqa: PLC0415

        parsed = urlparse(url)
        hostname = parsed.hostname
        if not hostname:
            return True

        # Block obvious private hostnames
        if hostname in ("localhost", "127.0.0.1", "::1", "0.0.0.0"):
            return True

        # Resolve hostname and check all IPs
        addr_infos = socket.getaddrinfo(hostname, parsed.port or 80)
        for _family, _type, _proto, _canonname, sockaddr in addr_infos:
            ip_str = sockaddr[0]
            ip = ipaddress.ip_address(ip_str)
            if (
                ip.is_private
                or ip.is_loopback
                or ip.is_link_local
                or ip.is_reserved
                or ip_str == "169.254.169.254"  # Cloud metadata endpoint
            ):
                return True
    except (socket.gaierror, ValueError, OSError):
        # If we can't resolve, block by default
        return True
    return False


# =============================================================================
# Request/Response Schemas
# =============================================================================


class SearchRequest(BaseModel):
    """Request schema for web search"""

    query: str = Field(..., min_length=3, max_length=500, description="Search query")
    max_results: int = Field(
        default=10, ge=1, le=50, description="Maximum number of results"
    )
    academic_only: bool = Field(
        default=True, description="Filter to academic sources only"
    )
    timeout: int = Field(
        default=30, ge=5, le=120, description="Search timeout in seconds"
    )


class SearchResultResponse(BaseModel):
    """Response schema for a single search result"""

    title: str
    url: str
    content: str | None = None
    description: str | None = None
    source: str | None = None
    published_date: str | None = None
    academic_score: float = Field(ge=0.0, le=1.0)


class SearchResponse(BaseModel):
    """Response schema for search results"""

    query: str
    results: list[SearchResultResponse]
    total_results: int
    academic_filter_applied: bool


class SummarizeRequest(BaseModel):
    """Request schema for URL summarization"""

    url: str = Field(..., description="URL to summarize")
    purpose: str = Field(
        default="general",
        description="Purpose of summarization: 'syllabus_description', 'ulo', 'content', 'assessment', or 'general'",
    )
    max_length: int = Field(
        default=1000, ge=100, le=5000, description="Maximum summary length"
    )
    include_key_points: bool = Field(
        default=True, description="Include key points extraction"
    )


class SummarizeResponse(BaseModel):
    """Response schema for URL summarization"""

    url: str
    summary: str
    key_points: list[str]
    purpose: str
    academic_score: float = Field(ge=0.0, le=1.0)
    content_length: int
    summary_length: int
    timestamp: str


class SearchAndSummarizeRequest(BaseModel):
    """Request schema for search and summarize"""

    query: str = Field(..., min_length=3, max_length=500, description="Search query")
    purpose: str = Field(
        default="general",
        description="Purpose of summarization: 'syllabus_description', 'ulo', 'content', 'assessment', or 'general'",
    )
    max_results: int = Field(
        default=5, ge=1, le=20, description="Maximum search results"
    )
    summarize_top_n: int = Field(
        default=3, ge=1, le=5, description="Number of top results to summarize"
    )


class SearchAndSummarizeResponse(BaseModel):
    """Response schema for search and summarize"""

    query: str
    purpose: str
    search_results: list[SearchResultResponse]
    summaries: list[SummarizeResponse]
    total_results: int
    summarized_count: int


# =============================================================================
# API Endpoints
# =============================================================================


@router.post("/search", response_model=SearchResponse)
async def search_web(
    request: SearchRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Search the web for academic content using SearXNG

    Returns search results filtered for academic relevance.
    """
    try:
        results = await web_search_service.search(
            query=request.query,
            max_results=request.max_results,
            academic_only=request.academic_only,
            timeout=request.timeout,
        )

        return SearchResponse(
            query=request.query,
            results=[SearchResultResponse(**r.to_dict()) for r in results],
            total_results=len(results),
            academic_filter_applied=request.academic_only,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {e!s}",
        )


@router.post("/summarize", response_model=SummarizeResponse)
async def summarize_url(
    request: SummarizeRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Fetch and summarize a webpage for educational purposes

    Uses AI to extract key information suitable for:
    - Syllabus descriptions
    - Learning outcomes
    - Educational content
    - Assessment materials
    """
    # Validate URL
    if not request.url.startswith(("http://", "https://")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="URL must start with http:// or https://",
        )

    # SSRF protection: block private/internal URLs
    if _is_private_url(request.url):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="URL resolves to a private or internal address",
        )

    # Validate purpose
    valid_purposes = ["syllabus_description", "ulo", "content", "assessment", "general"]
    if request.purpose not in valid_purposes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Purpose must be one of: {', '.join(valid_purposes)}",
        )

    try:
        summary = await web_search_service.summarize_url(
            url=request.url,
            purpose=request.purpose,
            max_length=request.max_length,
            include_key_points=request.include_key_points,
        )

        return SummarizeResponse(**summary)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Summarization failed: {e!s}",
        )


@router.post("/search-and-summarize", response_model=SearchAndSummarizeResponse)
async def search_and_summarize(
    request: SearchAndSummarizeRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Search for academic sources and summarize the top results

    Combines web search with AI summarization for research-backed content creation.
    """
    # Validate purpose
    valid_purposes = ["syllabus_description", "ulo", "content", "assessment", "general"]
    if request.purpose not in valid_purposes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Purpose must be one of: {', '.join(valid_purposes)}",
        )

    try:
        result = await web_search_service.search_and_summarize(
            query=request.query,
            purpose=request.purpose,
            max_results=request.max_results,
            summarize_top_n=request.summarize_top_n,
        )

        # Convert results to response models
        search_results = [SearchResultResponse(**r) for r in result["search_results"]]
        summaries = [SummarizeResponse(**s) for s in result["summaries"]]

        return SearchAndSummarizeResponse(
            query=result["query"],
            purpose=result["purpose"],
            search_results=search_results,
            summaries=summaries,
            total_results=result["total_results"],
            summarized_count=result["summarized_count"],
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search and summarize failed: {e!s}",
        )


@router.get("/test-search")
async def test_search(
    query: str = Query(
        default="constructivist learning theory", description="Test search query"
    ),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Test endpoint for web search functionality

    Returns a simple test result to verify SearXNG integration is working.
    """
    try:
        # Simple test search
        results = await web_search_service.search(
            query=query,
            max_results=3,
            academic_only=True,
            timeout=10,
        )

        if not results:
            return {
                "status": "success",
                "message": "Search completed but no results found",
                "query": query,
                "results_count": 0,
                "searxng_url": web_search_service.searxng_url,
            }

        return {
            "status": "success",
            "message": "Search completed successfully",
            "query": query,
            "results_count": len(results),
            "sample_results": [
                {
                    "title": r.title[:100] + "..." if len(r.title) > 100 else r.title,
                    "url": r.url,
                    "academic_score": r.academic_score,
                }
                for r in results[:2]
            ],
            "searxng_url": web_search_service.searxng_url,
        }

    except Exception as e:
        return {
            "status": "error",
            "message": f"Search test failed: {e!s}",
            "query": query,
            "searxng_url": web_search_service.searxng_url,
            "error": str(e),
        }
