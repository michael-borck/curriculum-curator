"""
CrossRef DOI lookup endpoint — free metadata enrichment for captured sources.
"""

import logging
import re

import httpx
from fastapi import APIRouter, HTTPException, status

from app.schemas.capture import CrossRefLookupRequest, CrossRefLookupResponse

logger = logging.getLogger(__name__)

router = APIRouter()

CROSSREF_API = "https://api.crossref.org/works"
# Polite pool — CrossRef asks for a mailto header for better rate limits
CROSSREF_HEADERS = {
    "User-Agent": "CurriculumCurator/1.0 (mailto:support@curriculumcurator.edu.au)",
}
TIMEOUT = 10.0


def _normalise_doi(raw: str) -> str:
    """Strip URL prefix if someone pastes a full DOI link."""
    return re.sub(r"^https?://(dx\.)?doi\.org/", "", raw.strip())


def _parse_crossref_response(data: dict) -> CrossRefLookupResponse:
    """Extract the fields we care about from the CrossRef JSON."""
    msg = data.get("message", {})

    # Title
    titles = msg.get("title", [])
    title = titles[0] if titles else None

    # Authors
    authors: list[str] = []
    for author in msg.get("author", []):
        given = author.get("given", "")
        family = author.get("family", "")
        if given and family:
            authors.append(f"{given} {family}")
        elif family:
            authors.append(family)

    # Publisher / journal
    publisher = msg.get("publisher")
    container = msg.get("container-title", [])
    journal_name = container[0] if container else None

    # Volume / issue / pages
    volume = msg.get("volume")
    issue = msg.get("issue")
    pages_str = msg.get("page")

    # Publication date (prefer published-print, then published-online)
    pub_date = None
    for key in ("published-print", "published-online", "published"):
        date_parts = msg.get(key, {}).get("date-parts", [[]])
        if date_parts and date_parts[0]:
            parts = date_parts[0]
            if len(parts) >= 3:
                pub_date = f"{parts[0]}-{parts[1]:02d}-{parts[2]:02d}"
            elif len(parts) >= 2:
                pub_date = f"{parts[0]}-{parts[1]:02d}"
            elif len(parts) >= 1:
                pub_date = str(parts[0])
            if pub_date:
                break

    # ISBN (for books/chapters)
    isbn_list = msg.get("ISBN", [])
    isbn_val = isbn_list[0] if isbn_list else None

    return CrossRefLookupResponse(
        title=title,
        authors=authors if authors else None,
        publisher=publisher,
        journal_name=journal_name,
        volume=volume,
        issue=issue,
        pages=pages_str,
        publication_date=pub_date,
        isbn=isbn_val,
    )


@router.post("/crossref-lookup", response_model=CrossRefLookupResponse)
async def crossref_lookup(data: CrossRefLookupRequest):
    """
    Look up metadata for a DOI via the CrossRef API.

    Free, no API key required. Returns normalized citation metadata.
    """
    doi = _normalise_doi(data.doi)
    if not doi:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="DOI is required",
        )

    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            resp = await client.get(
                f"{CROSSREF_API}/{doi}",
                headers=CROSSREF_HEADERS,
            )

        if resp.status_code == 404:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"DOI not found: {doi}",
            )

        resp.raise_for_status()
        return _parse_crossref_response(resp.json())

    except httpx.TimeoutException:
        logger.warning(f"CrossRef timeout for DOI: {doi}")
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="CrossRef lookup timed out",
        )
    except HTTPException:
        raise
    except Exception:
        logger.exception(f"CrossRef lookup failed for DOI: {doi}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="CrossRef lookup failed",
        )
