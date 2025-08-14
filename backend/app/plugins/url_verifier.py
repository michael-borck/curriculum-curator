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
        self._user_agent = (
            "Mozilla/5.0 (Compatible; CurriculumCurator/1.0; +https://example.com/bot)"
        )
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
            "github.com",
            "gitlab.com",
            "bitbucket.org",
            "stackoverflow.com",
            "developer.mozilla.org",
            "w3.org",
            "python.org",
            "nodejs.org",
            "reactjs.org",
            "vuejs.org",
            "djangoproject.com",
            "flask.palletsprojects.com",
            "aws.amazon.com",
            "cloud.google.com",
            "azure.microsoft.com",
            "wikipedia.org",
            "wikimedia.org",
            "arxiv.org",
            "coursera.org",
            "udemy.com",
            "edx.org",
            "khanacademy.org",
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
        result = self._init_result(url)

        # Check for suspicious patterns
        suspicious_reason = self._is_suspicious_url(url)
        if suspicious_reason:
            result["suspicious"] = True
            result["error"] = suspicious_reason
            return result

        # Validate URL format
        parsed = self._validate_url_format(url, result)
        if not parsed:
            return result

        # Check trusted domains
        if self._is_trusted_domain(parsed.netloc.lower()):
            result["valid"] = True
            result["trusted_domain"] = True
            return result

        # Perform HTTP verification
        await self._perform_http_verification(client, url, result)
        return result

    def _init_result(self, url: str) -> dict[str, Any]:
        """Initialize result dictionary for URL verification."""
        return {
            "url": url,
            "valid": False,
            "status_code": None,
            "error": None,
            "suspicious": False,
            "redirect_url": None,
            "bot_blocked": False,
        }

    def _validate_url_format(self, url: str, result: dict) -> Any:
        """Validate URL format and parse it."""
        try:
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                result["error"] = "Invalid URL format"
                return None
            return parsed
        except Exception as e:
            result["error"] = f"URL parsing error: {e!s}"
            return None

    def _is_trusted_domain(self, domain: str) -> bool:
        """Check if domain is in trusted list."""
        return any(domain.endswith(trusted) for trusted in self._trusted_domains)

    async def _perform_http_verification(
        self, client: httpx.AsyncClient, url: str, result: dict
    ) -> None:
        """Perform actual HTTP request verification."""
        try:
            # Try HEAD request first
            response = await self._make_request(client, url, "HEAD")
            self._process_response(response, url, result)

            # If HEAD fails with 405, try GET
            if response.status_code == 405:
                response = await self._make_request(client, url, "GET")
                self._process_response(response, url, result)

        except httpx.TimeoutException:
            result["error"] = "Request timeout"
        except httpx.ConnectError:
            result["error"] = "Connection failed"
        except httpx.HTTPStatusError as e:
            result["status_code"] = e.response.status_code
            result["error"] = f"HTTP {e.response.status_code}"
        except Exception as e:
            result["error"] = f"Request failed: {e!s}"

    async def _make_request(
        self, client: httpx.AsyncClient, url: str, method: str
    ) -> httpx.Response:
        """Make HTTP request with specified method."""
        if method == "HEAD":
            return await client.head(
                url, follow_redirects=True, timeout=self._timeout
            )
        return await client.get(
            url, follow_redirects=True, timeout=self._timeout
        )

    def _process_response(
        self, response: httpx.Response, url: str, result: dict
    ) -> None:
        """Process HTTP response and update result."""
        result["status_code"] = response.status_code

        # Check for bot blocking
        bot_block_info = self._check_bot_blocking(response)
        if bot_block_info:
            result["bot_blocked"] = True
            result["error"] = bot_block_info
            result["valid"] = False
        else:
            result["valid"] = response.status_code < 400

        # Check for redirects
        if str(response.url) != url:
            result["redirect_url"] = str(response.url)
            if self._is_captcha_redirect(str(response.url)):
                result["bot_blocked"] = True
                result["error"] = "Redirected to captcha/verification page"
                result["valid"] = False

    def _check_bot_blocking(self, response: httpx.Response) -> str | None:
        """Check if response indicates bot blocking."""
        status_code = response.status_code

        if status_code == 403:
            return "Access forbidden (possible bot blocking)"
        if status_code == 429:
            return "Rate limited (too many requests)"
        if status_code == 406:
            return "Not acceptable (bot detection)"
        if status_code == 503:
            server = response.headers.get("server", "").lower()
            if any(h in server for h in ["cloudflare", "ddos"]):
                return "Bot protection detected (Cloudflare/DDoS protection)"
            return "Service unavailable"

        return None

    def _is_captcha_redirect(self, redirect_url: str) -> bool:
        """Check if URL is a captcha or verification page."""
        captcha_indicators = ["captcha", "challenge", "verify", "bot-check"]
        return any(indicator in redirect_url.lower() for indicator in captcha_indicators)

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
                batch = urls[i : i + self._max_concurrent]
                tasks = [self._verify_url(client, url) for url, _ in batch]
                batch_results = await asyncio.gather(*tasks)

                # Add context to results
                for j, (_url, context) in enumerate(batch):
                    batch_results[j]["context"] = context

                results.extend(batch_results)

        return results

    def _generate_report(
        self, results: list[dict[str, Any]]
    ) -> tuple[list[str], list[str]]:
        """Generate issues and suggestions from verification results"""
        issues = []
        suggestions = []

        for result in results:
            issue, suggestion = self._process_result(result)
            if issue:
                issues.append(issue)
                suggestions.append(suggestion)

        return issues, suggestions

    def _process_result(self, result: dict[str, Any]) -> tuple[str | None, str | None]:
        """Process a single verification result."""
        url = result["url"]
        context = result.get("context", "")

        if result.get("suspicious"):
            return self._handle_suspicious_url(url, result)

        if result.get("bot_blocked"):
            return self._handle_bot_blocked_url(url, result)

        if not result["valid"]:
            return self._handle_invalid_url(url, context, result)

        if result.get("redirect_url"):
            return self._handle_redirect(url, result)

        return None, None

    def _handle_suspicious_url(self, url: str, result: dict) -> tuple[str, str]:
        """Handle suspicious URL."""
        issue = f"Suspicious URL pattern: {url[:100]}..."
        suggestion = f"Verify this URL is correct: {result.get('error', 'Pattern match')}"
        return issue, suggestion

    def _handle_bot_blocked_url(self, url: str, result: dict) -> tuple[str, str]:
        """Handle bot-blocked URL."""
        issue = f"Bot detection: {url[:100]}... - {result['error']}"

        bot_suggestions = {
            403: "This site blocks automated verification. Manual check recommended, or mark as trusted if you know it's valid",
            429: "Rate limited by the site. The URL might be valid but needs manual verification",
        }

        status_code = result.get("status_code")
        if status_code in bot_suggestions:
            suggestion = bot_suggestions[status_code]
        elif "captcha" in result.get("error", "").lower():
            suggestion = "Site requires CAPTCHA verification. URL likely valid but needs manual check"
        else:
            suggestion = "The site has bot protection. Consider manually verifying or whitelisting this domain"

        return issue, suggestion

    def _handle_invalid_url(self, url: str, context: str, result: dict) -> tuple[str, str]:
        """Handle invalid URL."""
        error = result.get("error", "")
        status_code = result.get("status_code")

        error_handlers = {
            "Connection failed": (
                f"Unreachable URL: {url[:100]}... ({context})",
                "Check if the URL is correct or if the site is temporarily down"
            ),
            "timeout": (
                f"URL timeout: {url[:100]}... ({context})",
                "The URL took too long to respond, verify it's correct"
            ),
        }

        # Check error message patterns
        for pattern, (issue_fmt, suggestion) in error_handlers.items():
            if pattern in error.lower():
                return issue_fmt, suggestion

        # Check status codes
        if status_code == 404:
            return (
                f"Broken link (404): {url[:100]}... ({context})",
                "This page doesn't exist, find the correct URL or remove the link"
            )

        if status_code and status_code >= 500:
            return (
                f"Server error ({status_code}): {url[:100]}...",
                "The server returned an error, the link may be temporarily broken"
            )

        # Default case
        return (
            f"Invalid URL: {url[:100]}... - {error}",
            "Verify and correct this URL"
        )

    def _handle_redirect(self, url: str, result: dict) -> tuple[str | None, str | None]:
        """Handle URL redirect."""
        redirect_url = result["redirect_url"]

        # Check if redirect is significant
        original_parsed = urlparse(url)
        redirect_parsed = urlparse(redirect_url)

        if (original_parsed.netloc != redirect_parsed.netloc or
            original_parsed.path != redirect_parsed.path):
            issue = f"URL redirects: {url[:50]}... → {redirect_url[:50]}..."
            suggestion = f"Update to use the final URL: {redirect_url}"
            return issue, suggestion

        return None, None

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
            skip_verification = metadata.get("config", {}).get(
                "skip_verification", False
            )
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
            bot_blocked_urls = sum(1 for r in results if r.get("bot_blocked"))
            broken_urls = total_urls - valid_urls - bot_blocked_urls

            # Calculate score
            if total_urls > 0:
                # Scoring: suspicious URLs are worst, broken are bad, bot-blocked are warnings
                score = max(
                    0,
                    100
                    - (broken_urls * 10)
                    - (suspicious_urls * 20)
                    - (bot_blocked_urls * 3),
                )
            else:
                score = 100

            # Determine pass/fail (bot-blocked URLs don't fail the check, just warn)
            passed = score >= 70 and suspicious_urls == 0

            if passed:
                if broken_urls > 0 or bot_blocked_urls > 0:
                    parts = []
                    if broken_urls > 0:
                        parts.append(f"{broken_urls} broken")
                    if bot_blocked_urls > 0:
                        parts.append(f"{bot_blocked_urls} bot-blocked")
                    message = f"URL check passed with {' and '.join(parts)} link(s)"
                else:
                    message = f"All {total_urls} URLs verified successfully"
            elif suspicious_urls > 0:
                message = (
                    f"Found {suspicious_urls} suspicious URL(s) (possibly hallucinated)"
                )
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
                    "bot_blocked_urls": bot_blocked_urls,
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
