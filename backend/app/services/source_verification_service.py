"""Verify that a reading-list source actually exists.

DOIs are checked against Crossref; other URLs get a safe HTTP request that
revalidates every redirect hop (SSRF-safe). The goal is to distinguish
"exists", "exists but restricted", "not found", and "could not check".
"""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import quote

import httpx

from app.utils.url_safety import UrlNotAllowedError, assert_public_url

_DOI_RE = re.compile(r"^10\.\d{4,9}/\S+$")
_CROSSREF = "https://api.crossref.org/works"
_HEADERS = {
    "User-Agent": "CurriculumCurator/1.0 (reading-list verification)",
    "Accept": "application/json, text/html;q=0.9, */*;q=0.8",
}
_MAX_REDIRECTS = 4


def normalise_doi(value: str | None) -> str | None:
    if not value:
        return None
    doi = value.strip()
    for prefix in ("https://doi.org/", "http://doi.org/", "doi:"):
        if doi.lower().startswith(prefix):
            doi = doi[len(prefix) :]
    doi = doi.strip()
    return doi if _DOI_RE.match(doi) else None


async def _verify_doi(client: httpx.AsyncClient, doi: str) -> dict[str, Any]:
    try:
        response = await client.get(f"{_CROSSREF}/{quote(doi, safe='/')}")
    except Exception as exc:  # network/timeout
        return {
            "status": "error",
            "reason": f"Could not reach Crossref: {exc.__class__.__name__}",
            "doi": doi,
            "resolved_url": f"https://doi.org/{doi}",
        }
    if response.status_code == 404:
        return {
            "status": "not_found",
            "reason": "DOI was not found at Crossref",
            "doi": doi,
            "resolved_url": f"https://doi.org/{doi}",
        }
    if response.status_code >= 400:
        return {
            "status": "error",
            "reason": f"Crossref returned HTTP {response.status_code}",
            "doi": doi,
            "resolved_url": f"https://doi.org/{doi}",
        }
    title = ""
    try:
        message = response.json().get("message", {})
        titles = message.get("title") or []
        title = titles[0] if titles else ""
    except Exception:
        pass
    reason = "DOI resolves via Crossref"
    if title:
        reason = f"DOI resolves via Crossref: {title[:160]}"
    return {
        "status": "verified",
        "reason": reason,
        "doi": doi,
        "resolved_url": f"https://doi.org/{doi}",
    }


async def _verify_url(  # noqa: PLR0911 - one clear return per verification outcome
    client: httpx.AsyncClient, url: str
) -> dict[str, Any]:
    current = url
    checked: list[str] = []
    try:
        for _ in range(_MAX_REDIRECTS + 1):
            await assert_public_url(current)
            checked.append(current)
            response = await client.request(
                "HEAD", current, follow_redirects=False
            )
            if response.status_code in (405, 501):
                response = await client.request(
                    "GET", current, follow_redirects=False
                )
            location = response.headers.get("location")
            if response.is_redirect and location:
                current = str(response.url.join(location))
                continue

            if response.status_code in (401, 403, 429):
                return {
                    "status": "restricted",
                    "reason": f"URL exists but is restricted (HTTP {response.status_code})",
                    "checked_url": checked[-1],
                }
            if response.status_code == 404:
                return {
                    "status": "not_found",
                    "reason": "URL returned 404",
                    "checked_url": checked[-1],
                }
            if response.status_code >= 400:
                return {
                    "status": "error",
                    "reason": f"URL returned HTTP {response.status_code}",
                    "checked_url": checked[-1],
                }
            return {
                "status": "verified",
                "reason": "URL responded successfully",
                "checked_url": checked[-1],
            }
    except UrlNotAllowedError:
        return {
            "status": "error",
            "reason": "URL points to a private or internal address",
            "checked_url": current,
        }
    except Exception as exc:
        return {
            "status": "error",
            "reason": f"Could not check URL: {exc.__class__.__name__}",
            "checked_url": current,
        }
    return {
        "status": "error",
        "reason": "Too many redirects",
        "checked_url": current,
    }


async def verify_source(
    title: str, url: str | None, doi: str | None
) -> dict[str, Any]:
    """Return a verification result for one source."""
    normalised = normalise_doi(doi or url)
    async with httpx.AsyncClient(timeout=8.0, headers=_HEADERS) as client:
        if normalised:
            result = await _verify_doi(client, normalised)
        elif url:
            result = await _verify_url(client, url)
        else:
            result = {
                "status": "unchecked",
                "reason": "No DOI or URL to verify",
            }
    return {"title": title, **result}
