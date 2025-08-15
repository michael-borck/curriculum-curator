"""
Rate limiting configuration and utilities
"""

import hashlib

from fastapi import Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded

from app.core.config import settings


def get_client_identifier(request: Request) -> str:
    """
    Get client identifier for rate limiting
    Uses IP address with forwarded header support
    """
    # Check for forwarded IP (behind proxy/load balancer)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # Take the first IP in the chain (original client)
        return forwarded_for.split(",")[0].strip()

    # Check for real IP header (some proxies use this)
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()

    # Fall back to direct connection IP
    return request.client.host if request.client else "unknown"


# Create limiter instance
limiter = Limiter(key_func=get_client_identifier)


def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    """
    Custom rate limit exceeded handler
    Returns user-friendly JSON response
    """
    retry_after = exc.retry_after if hasattr(exc, "retry_after") else 60

    return JSONResponse(
        status_code=429,
        content={
            "error": "Rate limit exceeded",
            "message": "Too many requests. Please try again later.",
            "retry_after": retry_after,
            "limit": str(exc.detail)
            if hasattr(exc, "detail")
            else "Rate limit exceeded",
        },
        headers={"Retry-After": str(retry_after)},
    )


# Rate limiting decorators for different endpoint types
class RateLimits:
    """Predefined rate limits for different endpoint types"""

    # Check if rate limiting is disabled for testing
    if settings.DISABLE_RATE_LIMIT or settings.TESTING:
        # Set very high limits when testing
        LOGIN = "10000/minute"
        REGISTER = "10000/minute"
        VERIFY_EMAIL = "10000/minute"
        RESEND_VERIFICATION = "10000/minute"
        FORGOT_PASSWORD = "10000/minute"
        RESET_PASSWORD = "10000/minute"
        DEFAULT = "10000/minute"
        API_READ = "10000/minute"
        API_WRITE = "10000/minute"
        API_DELETE = "10000/minute"
        CONTENT_GENERATE = "10000/minute"
        CONTENT_ENHANCE = "10000/minute"
        FILE_UPLOAD = "10000/minute"
        ADMIN_ACTIONS = "10000/minute"
    else:
        # Production rate limits
        # Authentication endpoints (more restrictive)
        LOGIN = "5/minute"  # type: ignore  # 5 login attempts per minute
        REGISTER = "3/minute"  # type: ignore  # 3 registrations per minute
        VERIFY_EMAIL = "10/minute"  # type: ignore  # 10 verification attempts per minute
        RESEND_VERIFICATION = "2/minute"  # type: ignore  # 2 resend requests per minute
        FORGOT_PASSWORD = "3/minute"  # type: ignore  # 3 password reset requests per minute
        RESET_PASSWORD = "5/minute"  # type: ignore  # 5 password reset attempts per minute

        # General API endpoints (less restrictive)
        DEFAULT = "60/minute"  # type: ignore  # Default rate limit
        API_READ = "60/minute"  # type: ignore  # 60 read operations per minute
        API_WRITE = "30/minute"  # type: ignore  # 30 write operations per minute
        API_DELETE = "10/minute"  # type: ignore  # 10 delete operations per minute

        # Content generation (LLM endpoints)
        CONTENT_GENERATE = "10/minute"  # type: ignore  # 10 content generations per minute
        CONTENT_ENHANCE = "15/minute"  # type: ignore  # 15 enhancements per minute

        # File upload
        FILE_UPLOAD = "20/minute"  # type: ignore  # 20 file uploads per minute

        # Administrative endpoints
        ADMIN_ACTIONS = "100/minute"  # type: ignore  # 100 admin actions per minute


def get_user_specific_limiter(request: Request) -> str:
    """
    Get user-specific identifier for authenticated requests
    Combines IP and user ID for more granular rate limiting
    """
    # Try to get user from JWT token in Authorization header
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        try:
            # This is a simplified version - in practice, you'd decode the JWT
            token = auth_header.split(" ")[1]
            # For now, just use IP + token hash for uniqueness
            token_hash = hashlib.md5(token.encode()).hexdigest()[:8]
            return f"{get_client_identifier(request)}:{token_hash}"
        except Exception:
            pass

    # Fall back to IP-based limiting
    return get_client_identifier(request)


# User-specific limiter for authenticated endpoints
user_limiter = Limiter(key_func=get_user_specific_limiter)


# Bypass rate limiting for certain conditions
def should_bypass_rate_limit(request: Request) -> bool:
    """
    Check if request should bypass rate limiting
    For example, internal health checks, admin users, etc.
    """
    # Check if rate limiting is disabled for testing
    if settings.DISABLE_RATE_LIMIT or settings.TESTING:
        return True

    # Allow health check endpoints
    if request.url.path in ["/health", "/", "/docs", "/redoc"]:
        return True

    # Allow localhost/development bypassing (be careful with this in production)
    client_ip = get_client_identifier(request)
    if client_ip in ["127.0.0.1", "::1", "localhost"]:
        # Only bypass in development mode
        return settings.DEBUG

    # Check for admin override header (would require proper admin authentication)
    admin_override = request.headers.get("X-Admin-Override")
    if admin_override == "bypass-rate-limit":
        # In practice, you'd validate this is from an authenticated admin
        # For now, we don't bypass based on headers alone
        pass

    return False


def create_conditional_limiter(rate_limit: str):
    """
    Create a limiter that can be conditionally bypassed
    """

    def conditional_rate_limit(request: Request):
        if should_bypass_rate_limit(request):
            return "999999/second"  # Effectively unlimited
        return get_client_identifier(request)

    return Limiter(key_func=conditional_rate_limit)
