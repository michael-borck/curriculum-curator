# ADR 0024: LOCAL_MODE and PyInstaller Compatibility

## Status

Accepted

## Date

2026-02-20

## Context

We want to offer a privacy-first local version of Curriculum Curator where users download a Docker image (or eventually an Electron app), run it locally, and get auto-logged in as a default user — no registration, no login screen.

Additionally, we need to audit our Python dependencies for future PyInstaller bundling (Electron + PyInstaller backend).

## Decision

### LOCAL_MODE

A single environment variable `LOCAL_MODE=true` controls both backend and frontend behavior:

- **Backend**: Bypasses JWT authentication, seeds a deterministic local admin user on startup, exposes `/api/auth/config` for runtime mode discovery
- **Frontend**: Discovers local mode via `/api/auth/config` (runtime, not build-time), auto-obtains a JWT session via `/api/auth/local-session`
- **Docker**: `LOCAL_MODE` passed through `docker-compose.yml`

The local user uses a well-known UUID (`00000000-0000-0000-0000-000000000001`) and email (`local@curriculum-curator.app`) for deterministic seeding.

### PyInstaller Compatibility Audit

| Dependency | Issue | Workaround |
|---|---|---|
| **pymupdf** | Native binary blocker — MuPDF C library not bundled by PyInstaller | Moved to `[pdf-advanced]` optional extra. pypdf, PyPDF2, and pdfplumber cover the same functionality. |
| **LiteLLM** | Dynamic imports for provider modules | PyInstaller `--hidden-import` flags for each provider |
| **cryptography** | C extensions (OpenSSL bindings) | PyInstaller handles this with `--collect-all cryptography` |
| **tiktoken** | Downloads tokenizer data at runtime, uses hidden imports | `--collect-data tiktoken` + pre-download tokenizer data |
| **uvloop** | C extension, platform-specific | Already conditional (`sys_platform != 'win32'`), excluded on Windows |
| **bcrypt/passlib** | C extension | Standard PyInstaller handling, well-supported |

All issues have known workarounds except pymupdf, which we've moved to an optional dependency group.

## Consequences

- Same Docker image serves both cloud and local deployments
- No separate frontend build needed — mode discovered at runtime
- Local mode users get full admin access with zero setup
- PDF processing still works with 3 remaining libraries (pypdf, PyPDF2, pdfplumber)
- PyInstaller bundling path is clear for future Electron integration
