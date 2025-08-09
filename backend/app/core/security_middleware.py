"""
Security middleware for HTTP headers and request validation
"""

import time
import uuid
from collections.abc import Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add security headers to all responses
    """

    def __init__(
        self,
        app,
        hsts_max_age: int = 31536000,  # 1 year in seconds
        csp_policy: str | None = None,
        frame_options: str = "DENY",
        content_type_options: str = "nosniff",
        referrer_policy: str = "strict-origin-when-cross-origin",
        permissions_policy: str | None = None,
    ):
        super().__init__(app)
        self.hsts_max_age = hsts_max_age
        self.csp_policy = csp_policy or self._default_csp_policy()
        self.frame_options = frame_options
        self.content_type_options = content_type_options
        self.referrer_policy = referrer_policy
        self.permissions_policy = (
            permissions_policy or self._default_permissions_policy()
        )

    def _default_csp_policy(self) -> str:
        """Default Content Security Policy"""
        return (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self' https:; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'"
        )

    def _default_permissions_policy(self) -> str:
        """Default Permissions Policy"""
        return (
            "geolocation=(), "
            "microphone=(), "
            "camera=(), "
            "payment=(), "
            "usb=(), "
            "magnetometer=(), "
            "gyroscope=(), "
            "speaker=(), "
            "vibrate=(), "
            "fullscreen=(), "
            "sync-xhr=()"
        )

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Process request
        start_time = time.time()

        # Add request ID for tracing
        request_id = self._generate_request_id()
        request.state.request_id = request_id

        # Call next middleware/route
        response = await call_next(request)

        # Add security headers to response
        self._add_security_headers(response, request, start_time, request_id)

        return response

    def _add_security_headers(
        self, response: Response, request: Request, start_time: float, request_id: str
    ):
        """Add all security headers to the response"""

        # Strict Transport Security (HTTPS only)
        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = (
                f"max-age={self.hsts_max_age}; includeSubDomains; preload"
            )

        # Content Security Policy
        response.headers["Content-Security-Policy"] = self.csp_policy

        # Frame Options
        response.headers["X-Frame-Options"] = self.frame_options

        # Content Type Options
        response.headers["X-Content-Type-Options"] = self.content_type_options

        # Referrer Policy
        response.headers["Referrer-Policy"] = self.referrer_policy

        # Permissions Policy
        response.headers["Permissions-Policy"] = self.permissions_policy

        # XSS Protection (legacy, but still useful)
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Remove server information
        response.headers["Server"] = "Curriculum-Curator"

        # Add custom headers for debugging/monitoring
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time"] = f"{(time.time() - start_time):.3f}s"

        # Remove potentially sensitive headers
        if "X-Powered-By" in response.headers:
            del response.headers["X-Powered-By"]

    def _generate_request_id(self) -> str:
        """Generate unique request ID for tracing"""
        return str(uuid.uuid4())[:8]


class RequestValidationMiddleware(BaseHTTPMiddleware):
    """
    Middleware for basic request validation and security checks
    """

    def __init__(
        self,
        app,
        max_request_size: int = 10 * 1024 * 1024,  # 10MB
        blocked_user_agents: list | None = None,
        blocked_paths: list | None = None,
        require_user_agent: bool = False,
    ):
        super().__init__(app)
        self.max_request_size = max_request_size
        self.blocked_user_agents = (
            blocked_user_agents or self._default_blocked_user_agents()
        )
        self.blocked_paths = blocked_paths or []
        self.require_user_agent = require_user_agent

    def _default_blocked_user_agents(self) -> list:
        """Default list of blocked user agents (basic bot protection)"""
        return [
            # Common malicious scanners
            "sqlmap",
            "nmap",
            "nikto",
            "masscan",
            "zap",
            "w3af",
            "acunetix",
            "nessus",
            # Known malicious bots (but allow legitimate tools like curl, wget, python-requests)
            "dirbuster",
            "gobuster",
            "dirb",
            "wfuzz",
        ]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Validate request before processing
        validation_error = await self._validate_request(request)
        if validation_error:
            return validation_error

        # Process request normally
        return await call_next(request)

    async def _validate_request(self, request: Request) -> Response:
        """Validate incoming request for security issues"""

        # Check request size (basic DoS protection)
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.max_request_size:
            return JSONResponse(
                status_code=413,
                content={
                    "error": "Request too large",
                    "message": f"Request size exceeds {self.max_request_size} bytes",
                },
            )

        # Check for blocked user agents
        user_agent = request.headers.get("user-agent", "").lower()
        if any(
            blocked_agent in user_agent for blocked_agent in self.blocked_user_agents
        ):
            return JSONResponse(
                status_code=403,
                content={"error": "Forbidden", "message": "Access denied"},
            )

        # Require user agent for certain endpoints (optional)
        if (
            self.require_user_agent
            and not user_agent
            and request.url.path.startswith("/api/")
        ):
            return JSONResponse(
                status_code=400,
                content={
                    "error": "Bad Request",
                    "message": "User-Agent header is required",
                },
            )

        # Check for blocked paths
        if any(blocked_path in request.url.path for blocked_path in self.blocked_paths):
            return JSONResponse(
                status_code=404,
                content={
                    "error": "Not Found",
                    "message": "The requested resource was not found",
                },
            )

        # Basic path traversal protection
        if ".." in request.url.path or "//" in request.url.path:
            return JSONResponse(
                status_code=400,
                content={"error": "Bad Request", "message": "Invalid path"},
            )

        return None  # No validation errors


class TrustedProxyMiddleware(BaseHTTPMiddleware):
    """
    Middleware to handle trusted proxy headers safely
    """

    def __init__(self, app, trusted_proxies: list | None = None):
        super().__init__(app)
        self.trusted_proxies = trusted_proxies or ["127.0.0.1", "::1"]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Validate and sanitize proxy headers
        self._process_proxy_headers(request)
        return await call_next(request)

    def _process_proxy_headers(self, request: Request):
        """Process and validate proxy headers"""
        # Only trust proxy headers from known proxy IPs
        client_ip = request.client.host if request.client else None

        if client_ip not in self.trusted_proxies:
            # Remove potentially spoofed headers from untrusted sources
            request.headers.__dict__.get("_list", []).clear()
            return

        # Process X-Forwarded-For header
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            # Take the first IP in the chain (original client)
            original_ip = forwarded_for.split(",")[0].strip()
            # Store in request state for use by rate limiter
            request.state.original_client_ip = original_ip
