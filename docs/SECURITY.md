# Security Overview

Current security architecture for Curriculum Curator.
Last reviewed: 2026-02-22.

For the full decision history, see the related ADRs linked at the bottom.

---

## Two Deployment Modes

| | Multi-User (VPS/Docker) | Single-User (Desktop/Local) |
|---|---|---|
| Auth | JWT with bcrypt passwords | Bypassed (`LOCAL_MODE=true`) |
| Rate limiting | Active (slowapi) | Active |
| Security headers | Active | Active |
| Accounts | Registration with email whitelist | Hardcoded local user, no login |

When `LOCAL_MODE=true`, authentication is skipped entirely. A hardcoded local user is returned for all requests. This is by design for the Electron desktop app and personal Docker containers (see [ADR-037](adr/037-privacy-first-byok-architecture.md)).

---

## Authentication (JWT)

- **Algorithm**: HS256 (HMAC-SHA256)
- **Access token expiry**: 30 minutes (configurable via `ACCESS_TOKEN_EXPIRE_MINUTES`)
- **Refresh token expiry**: 7 days
- **IP binding**: Tokens include the client IP; validation rejects mismatches (mitigates token theft)
- **Token payload**: `sub` (user ID), `exp`, `iat`, `jti` (unique ID), `ip`, `role`, `sid` (session ID)

**Key files**: `core/security.py`, `api/deps.py`, `api/routes/auth.py`

### Dependency chain

1. `get_current_user()` — validates JWT (or returns local user in LOCAL_MODE)
2. `get_current_active_user()` — ensures user account is active
3. `get_current_admin_user()` — enforces admin role
4. `get_user_or_admin_override()` — ownership check with admin bypass

### CSRF

Not implemented. JWT tokens are sent via `Authorization` header (not cookies), so CSRF is not applicable. CORS restricts which origins can make requests.

---

## Password Security

**Hashing**: bcrypt via passlib (`CryptContext(schemes=["bcrypt"])`)

**Validation requirements** (enforced at registration and password change):

- Minimum 8 characters
- Uppercase + lowercase letters
- At least one number
- At least one special character
- Minimum 8 unique characters
- No more than 3 consecutive identical characters
- Not in common password blocklist (~66 entries)
- Cannot contain parts of user's name or email
- Blocks keyboard patterns (qwerty, asdf) and sequential patterns (123456, abcdef)

**Key file**: `core/password_validator.py`

---

## Rate Limiting

**Implementation**: slowapi (IP-based), configured in `core/rate_limiter.py`

| Endpoint Category | Limit | Window |
|---|---|---|
| Login | 5 | per minute |
| Register | 3 | per minute |
| Forgot password | 3 | per minute |
| Reset password | 5 | per minute |
| Verify email | 10 | per minute |
| Resend verification | 2 | per minute |
| API reads | 60 | per minute |
| API writes | 30 | per minute |
| API deletes | 10 | per minute |
| LLM generation | 10 | per minute |
| LLM enhancement | 15 | per minute |
| File upload | 20 | per minute |
| Admin actions | 100 | per minute |

**Account lockout**: After repeated failed logins, the account is locked for 60 minutes. Successful login resets the counter.

**Testing mode**: All limits set to 10,000/minute when `TESTING=true` or `DISABLE_RATE_LIMIT=true`.

---

## Security Headers

Added to all responses via `SecurityHeadersMiddleware`:

| Header | Value |
|--------|-------|
| `Strict-Transport-Security` | `max-age=31536000; includeSubDomains; preload` |
| `X-Frame-Options` | `DENY` |
| `X-Content-Type-Options` | `nosniff` |
| `X-XSS-Protection` | `1; mode=block` |
| `Referrer-Policy` | `strict-origin-when-cross-origin` |
| `Permissions-Policy` | Blocks geolocation, microphone, camera, payment, USB |
| `Content-Security-Policy` | `default-src 'self'` (relaxed for Swagger/ReDoc) |
| `Server` | `Curriculum-Curator` (hides framework) |
| `X-Request-ID` | UUID per request (for tracing) |

**Key file**: `core/security_middleware.py`

---

## Request Validation

The `RequestValidationMiddleware` checks all incoming requests:

- **Max request size**: 10 MB
- **Blocked user agents**: Known scanner tools (sqlmap, nmap, nikto, ZAP, acunetix, etc.)
- **Path traversal**: Rejects paths containing `..` or `//`

A `TrustedProxyMiddleware` validates `X-Forwarded-For` and `X-Real-IP` headers, only trusting configured proxy IPs (Docker bridge networks and localhost by default).

---

## Audit Logging

Security events are logged to the `SecurityLog` database table with:

- Event type, severity, success/failure
- IP address, user agent, request path/method
- User ID, email, role
- Custom details (JSON) and response time

**Tracked events**: failed logins, successful logins, registration, email verification, password reset requests, password changes, rate limit violations, admin actions.

**Key file**: `repositories/security_repo.py`

---

## CORS

Currently configured for development (localhost only):

- `http://localhost:5173` (Vite dev server)
- `http://localhost:3000`, `http://localhost:8000` (alternatives)

**For production**: Configure allowed origins to match your domain. In Docker, the frontend is served by the same origin so CORS is not needed.

---

## Privacy & Data

Curriculum Curator follows a **privacy-first, BYOK** architecture ([ADR-037](adr/037-privacy-first-byok-architecture.md)):

- **No telemetry**: Zero analytics, tracking, or external calls beyond user-initiated AI requests
- **Data stays local**: SQLite on the user's filesystem, no cloud database
- **BYOK**: Users supply their own API keys (or use local Ollama)
- **Air-gapped capable**: Ollama + Local Mode works without internet

---

## Production Checklist

Before deploying to a publicly accessible server:

- [ ] Set a strong `SECRET_KEY` (generate with `openssl rand -hex 32`)
- [ ] Configure CORS `allow_origins` for your actual domain
- [ ] Use HTTPS (required for HSTS header to be effective)
- [ ] Review rate limit thresholds for your expected traffic
- [ ] Set `DEBUG=false`
- [ ] Configure email (Brevo) for verification and password reset
- [ ] Set `ALLOWED_EMAIL_DOMAINS` to restrict registration

---

## Related ADRs

| ADR | Topic | Notes |
|-----|-------|-------|
| [ADR-007](adr/007-simple-authentication-internal-network.md) | Initial auth design | Originally session-based; superseded by JWT in ADR-017 |
| [ADR-008](adr/008-email-verification-cross-device.md) | Email verification | Dual-method: 6-digit code + clickable link |
| [ADR-009](adr/009-self-service-password-reset.md) | Password reset | Token-based via Brevo email |
| [ADR-010](adr/010-security-hardening.md) | Security hardening | Rate limiting, password policy, headers, audit log |
| [ADR-017](adr/017-fastapi-rest-backend.md) | FastAPI + JWT auth | Replaced session-based auth from ADR-007 |
| [ADR-037](adr/037-privacy-first-byok-architecture.md) | Privacy-first BYOK | No telemetry, local data, user-owned keys |
