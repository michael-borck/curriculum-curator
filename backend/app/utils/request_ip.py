"""Resolve the client IP for security-sensitive uses (rate limiting, lockout,
JWT IP-binding).

``X-Forwarded-For`` / ``X-Real-IP`` are client-controlled and must only be
trusted when the app sits behind a proxy that overwrites them. Gate that on
``settings.TRUST_PROXY_HEADERS`` so the default posture is un-spoofable.
"""

from fastapi import Request

from app.core.config import settings


def get_client_ip(request: Request) -> str:
    """Return the best client IP, honouring proxy headers only when trusted."""
    if settings.TRUST_PROXY_HEADERS:
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()
    return request.client.host if request.client else "unknown"
