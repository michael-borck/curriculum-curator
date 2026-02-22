# 49. Tiered Rate Limiting by Endpoint Classification

Date: 2026-02-23

## Status

Accepted

## Context

The API serves diverse endpoint types with very different abuse profiles: authentication endpoints are high-value targets for brute-force attacks, AI content generation endpoints are expensive per-call, and standard CRUD endpoints need reasonable throughput. A single global rate limit would either be too restrictive for normal use or too permissive for sensitive endpoints.

## Decision

Implement a tiered rate limiting system with endpoint-type classification, dual limiter instances, and environment-aware bypass logic.

### Rate Limit Tiers

| Category | Limit | Rationale |
|----------|-------|-----------|
| `LOGIN` | 5/min | Brute-force protection |
| `REGISTER` | 3/min | Account creation abuse prevention |
| `VERIFY_EMAIL` | 10/min | Retry-friendly but bounded |
| `RESEND_VERIFICATION` | 2/min | Prevent email spam |
| `FORGOT_PASSWORD` | 3/min | Email enumeration protection |
| `RESET_PASSWORD` | 5/min | Token brute-force protection |
| `CONTENT_GENERATE` | 10/min | LLM cost control |
| `CONTENT_ENHANCE` | 15/min | LLM cost control (lighter operations) |
| `FILE_UPLOAD` | 20/min | Storage abuse prevention |
| `API_READ` | 60/min | Normal CRUD throughput |
| `API_WRITE` | 30/min | Write operations bounded |
| `API_DELETE` | 10/min | Destructive operations tightly limited |
| `ADMIN_ACTIONS` | 100/min | Higher throughput for admin workflows |
| `DEFAULT` | 60/min | Fallback for uncategorised endpoints |

### Dual Limiter Instances

1. **IP-based limiter** (`limiter`) — for unauthenticated endpoints (login, register, password reset). Key resolution: `X-Forwarded-For` → `X-Real-IP` → `request.client.host` → `"unknown"`.

2. **User-specific limiter** (`user_limiter`) — for authenticated endpoints. Key combines client IP with an 8-character MD5 hash of the JWT token: `"{ip}:{token_hash}"`. This prevents a single user from exhausting the limit for all users behind the same IP (e.g. university NAT), while still rate-limiting per-session.

### Bypass Logic

- **Test/disabled mode:** When `DISABLE_RATE_LIMIT` or `TESTING` is set, all tier constants are replaced with `10000/minute` at module load time — zero per-request overhead.
- **Health/docs endpoints:** `/health`, `/`, `/docs`, `/redoc` are always exempt.
- **Localhost in debug:** `127.0.0.1`, `::1`, and `localhost` bypass limits when `DEBUG=True`.
- **Conditional limiter:** `create_conditional_limiter()` returns a limiter that checks `should_bypass_rate_limit()` per-request, returning an effectively unlimited rate when bypassed.

### Error Response

HTTP 429 with JSON body: `{ error, message, retry_after, limit }` plus a `Retry-After` header.

## Consequences

### Positive
- Sensitive endpoints (auth, AI generation) are tightly protected without restricting normal CRUD usage
- Per-user+IP keying prevents one user from blocking others behind shared NATs
- Test mode completely disables limits without conditional checks on every request
- Tiered approach makes it easy to tune individual endpoint categories independently

### Negative
- Rate limits are hardcoded in a class — changing them requires a code change and restart (not runtime-configurable)
- MD5 hash of JWT token is not cryptographically meaningful — it's just a bucketing key, but could confuse security reviewers
- IP extraction from `X-Forwarded-For` trusts the first value, which can be spoofed without a trusted proxy

### Neutral
- Uses `slowapi` (built on `limits` library) — standard Python rate limiting, backed by in-memory storage by default
- In-memory storage means limits reset on server restart and aren't shared across workers

## Alternatives Considered

### Single Global Rate Limit
- One limit (e.g. 100/min) for all endpoints
- Rejected: too permissive for auth endpoints, too restrictive for CRUD — a 100/min limit still allows 100 login attempts per minute

### Redis-Backed Distributed Limiting
- Share rate limit state across workers and restarts
- Rejected: adds infrastructure dependency; single-process deployment model (including Electron desktop) doesn't need distributed state

### Token Bucket Algorithm
- Allows bursts while maintaining average rate
- Rejected: `slowapi`/`limits` already supports fixed window and sliding window strategies; token bucket adds complexity for minimal benefit in this use case

## Implementation Notes

- All tiers defined in `RateLimits` class in `backend/app/core/rate_limiter.py`
- Endpoints apply limits via `@limiter.limit(RateLimits.LOGIN)` or `@user_limiter.limit(RateLimits.CONTENT_GENERATE)` decorators
- `rate_limit_exceeded_handler` is registered as a FastAPI exception handler for `RateLimitExceeded`
- The `X-Admin-Override` header is stubbed in code but not functional

## References

- `backend/app/core/rate_limiter.py`
- [ADR-010: Security Hardening](010-security-hardening.md)
- [ADR-017: FastAPI REST Backend](017-fastapi-rest-backend.md)
