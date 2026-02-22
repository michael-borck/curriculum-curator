# 26. Single-Container Deployment (FastAPI Serves SPA)

Date: 2026-02-20

## Status

Accepted (supersedes deployment approach in ADR-011)

## Context

ADR-011 recommended a two-service Docker deployment: Gunicorn/Uvicorn running the FastAPI backend behind an Nginx reverse proxy that also serves the React frontend's static files. This is a standard production pattern.

In practice, the Nginx layer created significant deployment friction:

1. **Configuration complexity** — Nginx config needed to proxy API routes while serving static files, handle WebSocket upgrades for SSE, and manage CORS headers (duplicating what FastAPI already handles)
2. **Debugging difficulty** — Multiple commits (`316e0587`, `a7f226c1`, `ed3d8c11`, `4562f0e2`) show back-and-forth issues with API URL routing between the two services
3. **Docker image bloat** — Two services meant either a multi-container `docker-compose.yml` or a multi-process supervisor inside one container
4. **LOCAL_MODE incompatibility** — The privacy-first local deployment (ADR-024) targets users who run `docker compose up` and expect things to just work. A two-service setup adds unnecessary complexity for this audience

The backend already has full middleware for security headers, CORS, trusted hosts, and rate limiting (ADR-017). Nginx was duplicating these capabilities rather than adding new ones.

## Decision

**FastAPI serves everything in a single container**: the REST API, SSE streaming, and the built React SPA as static files.

### Architecture

```
┌────────────────────────────────────────────┐
│          Single Docker Container            │
│                                             │
│  Uvicorn (FastAPI)                          │
│  ├── /api/*          → API routes           │
│  ├── /assets/*       → StaticFiles(dist/)   │
│  └── /*              → index.html (SPA)     │
│                                             │
│  Port 8000                                  │
└────────────────────────────────────────────┘

External (optional):
  Caddy / Nginx / Cloudflare → TLS termination, caching
```

### Implementation

```python
# main.py — static file serving (after all API routes)
frontend_path = Path("/app/frontend/dist")

if frontend_path.exists():
    app.mount("/assets", StaticFiles(directory=str(frontend_path / "assets")))

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        if full_path.startswith("api/"):
            return {"detail": "Not Found"}
        return FileResponse(str(frontend_path / "index.html"))
```

### TLS and Edge Caching

TLS termination moves to an external reverse proxy (Caddy, Nginx, Cloudflare Tunnel) that sits in front of the container. This is a cleaner separation of concerns: FastAPI handles application logic, the edge proxy handles TLS and caching.

The current production deployment uses Caddy on the same VPS, configured via a `caddy_default` Docker network.

## Consequences

### Positive

- **Simpler deployment**: One container, one port, one process — `docker compose up` and it works
- **Fewer moving parts**: Eliminated an entire service and its configuration
- **Consistent behaviour**: No discrepancies between what Nginx and FastAPI think the CORS/security policy is
- **LOCAL_MODE friendly**: Users download one image and run it
- **Easier debugging**: All request handling in one place with one set of logs
- **Dev/prod parity**: Development (`uvicorn`) and production (`docker`) serve files the same way

### Negative

- **No static file caching at the app layer**: FastAPI's `StaticFiles` doesn't add `Cache-Control` headers by default (mitigated by Vite's content-hashed filenames and Caddy's caching)
- **No gzip at the app layer**: Compression is left to the edge proxy (Caddy handles this automatically)
- **Single process**: No worker pool unless Gunicorn is added in front of Uvicorn (current traffic levels don't require this)
- **Not suitable for high-traffic CDN patterns**: If the app ever needed a CDN for static assets, the edge proxy would need to split traffic

### Neutral

- **Reverse proxy still recommended**: For TLS termination, Caddy or similar is still used in production — just not for routing API vs static traffic
- **Same Dockerfile**: The build stage compiles the React frontend, the run stage copies it into the FastAPI container

## Alternatives Considered

### Keep Nginx in the container (multi-process)

- Run both Nginx and Uvicorn via supervisord inside one container
- **Rejected**: Violates Docker's one-process-per-container principle, harder to debug, and supervisord adds complexity

### Keep Nginx as a separate service

- Two containers in docker-compose.yml
- **Rejected**: The original approach. Too much configuration friction for the benefit provided, especially for LOCAL_MODE users

### Use WhiteNoise (Python static file middleware)

- Django-ecosystem library for serving static files with proper caching headers
- **Rejected**: FastAPI's built-in `StaticFiles` is sufficient, and Caddy handles caching at the edge

## References

- [ADR-011: Deployment Best Practices](011-deployment-best-practices.md) — Original two-service recommendation (deployment guidelines still valid, architecture simplified)
- [ADR-017: FastAPI REST Backend](017-fastapi-rest-backend.md) — Security middleware stack
- [ADR-024: LOCAL_MODE](024-local-mode-pyinstaller-compatibility.md) — Privacy-first local deployment
- Relevant commits: `316e0587`, `7cb7d463`, `a5bfa32c`
