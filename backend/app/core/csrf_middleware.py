"""
CSRF Protection Middleware for API-friendly implementation

This module provides a more nuanced approach to CSRF protection that works well
with modern SPAs and API clients while still maintaining security.

Why this approach:
1. JSON APIs with proper CORS are inherently protected against CSRF
2. Form submissions still need CSRF protection
3. We rely on SameSite cookies + CORS for JSON requests
4. This prevents breaking legitimate API clients while maintaining security

Security considerations:
- CORS must be properly configured (which we have)
- Authentication tokens should be in headers, not cookies only
- SameSite cookie attribute provides additional protection
"""

from fastapi import Request
from fastapi_csrf_protect import CsrfProtect


async def check_csrf_requirement(request: Request, csrf_protect: CsrfProtect) -> bool:
    """
    Determine if CSRF validation is required for this request

    Returns True if CSRF should be checked, False otherwise
    """
    # Get content type
    content_type = request.headers.get("content-type", "").lower()

    # Skip CSRF for:
    # 1. GET, HEAD, OPTIONS requests (safe methods)
    if request.method in ["GET", "HEAD", "OPTIONS"]:
        return False

    # 2. JSON API requests (protected by CORS)
    if "application/json" in content_type:
        return False

    # 3. Requests with API key authentication
    # Require CSRF for:
    # 1. Form submissions
    # 2. Any other POST/PUT/DELETE requests
    return not request.headers.get("x-api-key")


async def validate_csrf_if_required(request: Request, csrf_protect: CsrfProtect):
    """
    Validate CSRF token only when required

    This allows API clients to work without CSRF tokens while maintaining
    protection for form-based submissions
    """
    if await check_csrf_requirement(request, csrf_protect):
        await csrf_protect.validate_csrf(request)
    # else: Skip CSRF validation for JSON APIs
