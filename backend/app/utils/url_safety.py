"""SSRF protection for outbound fetches of user-supplied URLs.

Any endpoint that fetches a URL the user provided (URL extraction, page
summarisation) must route through :func:`assert_public_url` before the request
and on every redirect hop, so an attacker cannot reach internal services,
loopback, link-local (incl. cloud metadata at 169.254.169.254), or other
private address ranges.
"""

import asyncio
import ipaddress
import socket
from urllib.parse import urlparse

__all__ = ["UrlNotAllowedError", "assert_public_url"]


class UrlNotAllowedError(Exception):
    """Raised when a URL is not permitted for outbound fetching."""


_ALLOWED_SCHEMES = frozenset({"http", "https"})


def _ip_is_blocked(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    """True if the address is in a range we must never fetch from."""
    if ip.version == 6 and ip.ipv4_mapped is not None:
        ip = ip.ipv4_mapped
    return (
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local  # covers 169.254.0.0/16 cloud metadata
        or ip.is_multicast
        or ip.is_reserved
        or ip.is_unspecified
    )


async def assert_public_url(url: str) -> None:
    """Validate that ``url`` is safe to fetch, else raise ``UrlNotAllowedError``.

    Enforces an http(s) scheme and resolves the host, rejecting the request if
    the literal host or *any* resolved address falls in a private/reserved
    range. Because DNS can resolve to multiple records, every returned address
    is checked (defends against DNS-rebinding to a degree; callers should also
    re-validate on redirects).
    """
    parsed = urlparse(url)
    if parsed.scheme.lower() not in _ALLOWED_SCHEMES:
        raise UrlNotAllowedError(f"URL scheme not allowed: {parsed.scheme!r}")

    host = parsed.hostname
    if not host:
        raise UrlNotAllowedError("URL has no host")

    # Host given as an IP literal — check directly.
    try:
        literal_ip = ipaddress.ip_address(host)
    except ValueError:
        pass
    else:
        if _ip_is_blocked(literal_ip):
            raise UrlNotAllowedError(f"URL host resolves to a blocked address: {host}")
        return

    # Hostname — resolve all addresses and reject if any is blocked.
    port = parsed.port or (443 if parsed.scheme.lower() == "https" else 80)
    loop = asyncio.get_running_loop()
    try:
        infos = await loop.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise UrlNotAllowedError(f"Could not resolve host: {host}") from exc

    if not infos:
        raise UrlNotAllowedError(f"Could not resolve host: {host}")

    for info in infos:
        addr = info[4][0]
        try:
            ip = ipaddress.ip_address(addr)
        except ValueError:
            continue
        if _ip_is_blocked(ip):
            raise UrlNotAllowedError(
                f"URL host resolves to a blocked address: {host} -> {addr}"
            )
