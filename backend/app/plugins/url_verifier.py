"""
URL Verifier Plugin
Extracts and verifies URLs from content to prevent hallucinated links
"""

import asyncio
import re
from typing import Any
from urllib.parse import urlparse

import httpx

from app.plugins.base import PluginResult, ValidatorPlugin


class URLVerifier(ValidatorPlugin):
    """Verifies that URLs in content are valid and accessible"""

    def __init__(self):
        super().__init__()
        self._timeout = 10  # seconds
        self._user_agent = "Mozilla/5.0 (Compatible; CurriculumCurator/1.0; +https://example.com/bot)"
        self._max_concurrent = 5  # Max concurrent requests

        # Common URL patterns that are often hallucinated
        self._suspicious_patterns = [
            r"example\.com/docs/.*",  # Generic example URLs
            r"docs\..*\.com/api/v\d+/.*",  # Overly specific API docs
            r"github\.com/.*/.*/blob/master/docs/.*\.md",  # Too specific GitHub paths
            r"medium\.com/@.*/.*-[a-f0-9]{12}$",  # Fake Medium article IDs
            r"stackoverflow\.com/questions/\d{8,}",  # Suspicious SO question IDs
        ]

        # Whitelisted domains that we trust even if temporarily down
        self._trusted_domains = {
            "github.com", "gitlab.com", "bitbucket.org",
            "stackoverflow.com", "developer.mozilla.org", "w3.org",
            "python.org", "nodejs.org", "reactjs.org", "vuejs.org",
            "djangoproject.com", "flask.palletsprojects.com",
            "aws.amazon.com", "cloud.google.com", "azure.microsoft.com",
            "wikipedia.org", "wikimedia.org", "arxiv.org",
            "coursera.org", "udemy.com", "edx.org", "khanacademy.org",
        }

    @property
    def name(self) -> str:
        return "url_verifier"

    @property
    def description(self) -> str:
        return "Verifies URLs are valid and accessible to prevent hallucinated links"

    def _extract_urls(self, content: str) -> list[tuple[str, str]]:
        """Extract URLs from content with their context"""
        urls = []

        # Markdown link pattern: [text](url)
        markdown_links = re.finditer(r"\[([^\]]+)\]\(([^)]+)\)", content)
        for match in markdown_links:
            text, url = match.groups()
            if url.startswith(("http://", "https://")):
                urls.append((url, f"Link text: {text}"))

        # Raw URLs
        raw_urls = re.finditer(r"https?://[^\s<>\"'{}\[\]]+", content)
        for match in raw_urls:
            url = match.group()
            # Clean up common trailing punctuation
            url = re.sub(r"[.,;:!?]+$", "", url)
            # Check if this URL wasn't already captured as markdown
            if not any(url == u[0] for u in urls):
                urls.append((url, "Raw URL"))

        # Deduplicate while preserving order
        seen = set()
        unique_urls = []
        for url, context in urls:
            if url not in seen:
                seen.add(url)
                unique_urls.append((url, context))

        return unique_urls

    def _is_suspicious_url(self, url: str) -> str | None:
        """Check if URL matches suspicious patterns"""
        for pattern in self._suspicious_patterns:
            if re.search(pattern, url, re.IGNORECASE):
                return f"URL matches suspicious pattern: {pattern}"

        # Check for overly long URLs (often hallucinated)
        if len(url) > 200:
            return "URL is suspiciously long (>200 characters)"

        # Check for too many path segments
        parsed = urlparse(url)
        path_segments = [s for s in parsed.path.split("/") if s]
        if len(path_segments) > 8:
            return f"URL has too many path segments ({len(path_segments)})"

        # Check for random-looking strings in URL
        if re.search(r"/[a-f0-9]{32,}/", url):
            return "URL contains suspicious hash-like string"

        return None

    async def _verify_url(self, client: httpx.AsyncClient, url: str) -> dict[str, Any]:
        """Verify a single URL"""
        result = {
            "url": url,
            "valid": False,
            "status_code": None,
            "error": None,
            "suspicious": False,
            "redirect_url": None,
        }

        # Check for suspicious patterns first
        suspicious_reason = self._is_suspicious_url(url)
        if suspicious_reason:
            result["suspicious"] = True
            result["error"] = suspicious_reason
            return result

        # Parse URL
        try:
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                result["error"] = "Invalid URL format"
                return result
        except Exception as e:
            result["error"] = f"URL parsing error: {e!s}"
            return result

        # Check if domain is trusted (skip actual verification for trusted domains)
        domain = parsed.netloc.lower()
        if any(domain.endswith(trusted) for trusted in self._trusted_domains):
            result["valid"] = True
            result["trusted_domain"] = True
            return result

        # Perform actual HTTP request
        try:
            # Use HEAD request first (faster, less resource intensive)
            response = await client.head(
                url,
                follow_redirects=True,
                timeout=self._timeout,
            )

            result["status_code"] = response.status_code
            result["valid"] = response.status_code < 400

            # Check for redirects
            if str(response.url) != url:
                result["redirect_url"] = str(response.url)

            # If HEAD fails with 405, try GET
            if response.status_code == 405:
                response = await client.get(
                    url,
                    follow_redirects=True,
                    timeout=self._timeout,
                )
                result["status_code"] = response.status_code
                result["valid"] = response.status_code < 400

        except httpx.TimeoutException:
            result["error"] = "Request timeout"
        except httpx.ConnectError:
            result["error"] = "Connection failed"
        except httpx.HTTPStatusError as e:
            result["status_code"] = e.response.status_code
            result["error"] = f"HTTP {e.response.status_code}"
        except Exception as e:
            result["error"] = f"Request failed: {e!s}"

        return result

    async def _verify_urls(self, urls: list[tuple[str, str]]) -> list[dict[str, Any]]:
        """Verify multiple URLs concurrently"""
        results = []

        # Create HTTP client with custom headers
        async with httpx.AsyncClient(
            headers={"User-Agent": self._user_agent},
            verify=False,  # Skip SSL verification for flexibility
        ) as client:
            # Process URLs in batches to avoid overwhelming
            for i in range(0, len(urls), self._max_concurrent):
                batch = urls[i:i + self._max_concurrent]
                tasks = [self._verify_url(client, url) for url, _ in batch]
                batch_results = await asyncio.gather(*tasks)

                # Add context to results
                for j, (_url, context) in enumerate(batch):
                    batch_results[j]["context"] = context

                results.extend(batch_results)

        return results

    def _generate_report(self, results: list[dict[str, Any]]) -> tuple[list[str], list[str]]:
        """Generate issues and suggestions from verification results"""
        issues = []
        suggestions = []

        for result in results:
            url = result["url"]
            context = result.get("context", "")

            if result.get("suspicious"):
                issues.append(f"Suspicious URL pattern: {url[:100]}...")
                suggestions.append(f"Verify this URL is correct: {result.get('error', 'Pattern match')}")

            elif not result["valid"]:
                if result.get("error"):
                    if "Connection failed" in result["error"]:
                        issues.append(f"Unreachable URL: {url[:100]}... ({context})")
                        suggestions.append("Check if the URL is correct or if the site is temporarily down")
                    elif "timeout" in result["error"].lower():
                        issues.append(f"URL timeout: {url[:100]}... ({context})")
                        suggestions.append("The URL took too long to respond, verify it's correct")
                    elif "404" in str(result.get("status_code", "")):
                        issues.append(f"Broken link (404): {url[:100]}... ({context})")
                        suggestions.append("This page doesn't exist, find the correct URL or remove the link")
                    elif result.get("status_code") and result["status_code"] >= 500:
                        issues.append(f"Server error ({result['status_code']}): {url[:100]}...")
                        suggestions.append("The server returned an error, the link may be temporarily broken")
                    else:
                        issues.append(f"Invalid URL: {url[:100]}... - {result['error']}")
                        suggestions.append("Verify and correct this URL")

            elif result.get("redirect_url"):
                # Only flag significant redirects (different domain or path)
                original_parsed = urlparse(url)
                redirect_parsed = urlparse(result["redirect_url"])

                if (original_parsed.netloc != redirect_parsed.netloc or
                    original_parsed.path != redirect_parsed.path):
                    issues.append(f"URL redirects: {url[:50]}... → {result['redirect_url'][:50]}...")
                    suggestions.append(f"Update to use the final URL: {result['redirect_url']}")

        return issues, suggestions

    async def validate(self, content: str, metadata: dict[str, Any]) -> PluginResult:
        """Validate URLs in content"""
        try:
            # Extract URLs
            urls = self._extract_urls(content)

            if not urls:
                return PluginResult(
                    success=True,
                    message="No URLs found in content",
                    data={"url_count": 0, "skipped": True},
                )

            # Skip verification in certain modes
            skip_verification = metadata.get("config", {}).get("skip_verification", False)
            if skip_verification:
                return PluginResult(
                    success=True,
                    message=f"Found {len(urls)} URLs (verification skipped)",
                    data={
                        "url_count": len(urls),
                        "urls": [u[0] for u in urls][:10],
                        "skipped": True,
                    },
                )

            # Verify URLs
            results = await self._verify_urls(urls)

            # Generate report
            issues, suggestions = self._generate_report(results)

            # Calculate statistics
            total_urls = len(results)
            valid_urls = sum(1 for r in results if r["valid"])
            suspicious_urls = sum(1 for r in results if r.get("suspicious"))
            broken_urls = total_urls - valid_urls

            # Calculate score
            if total_urls > 0:
                # Suspicious URLs are worse than broken ones
                score = max(0, 100 - (broken_urls * 10) - (suspicious_urls * 20))
            else:
                score = 100

            # Determine pass/fail
            passed = score >= 70 and suspicious_urls == 0

            if passed:
                if broken_urls > 0:
                    message = f"URL check passed with {broken_urls} broken link(s)"
                else:
                    message = f"All {total_urls} URLs verified successfully"
            elif suspicious_urls > 0:
                message = f"Found {suspicious_urls} suspicious URL(s) (possibly hallucinated)"
            else:
                message = f"Found {broken_urls} broken link(s) out of {total_urls}"

            return PluginResult(
                success=passed,
                message=message,
                data={
                    "score": round(score, 2),
                    "url_count": total_urls,
                    "valid_urls": valid_urls,
                    "broken_urls": broken_urls,
                    "suspicious_urls": suspicious_urls,
                    "results": results[:20],  # Limit detailed results
                },
                suggestions=suggestions[:10] if suggestions else None,
            )

        except Exception as e:
            return PluginResult(
                success=False,
                message=f"URL verification failed: {e!s}",
            )

