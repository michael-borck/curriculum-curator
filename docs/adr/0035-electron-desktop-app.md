# ADR 0035: Electron Desktop App with Embedded Backend

Date: 2026-02-21

## Status

Accepted

## Context

Curriculum Curator runs as a web application (React frontend + FastAPI backend). Some users need to work offline, keep all data on their own machine, or avoid cloud infrastructure entirely. A desktop application addresses these needs while reusing the existing web stack.

Key questions:
- How to package a Python backend for desktop distribution?
- How to handle local AI (Ollama) lifecycle?
- How to deliver cross-platform builds (macOS, Windows, Linux)?

## Decision

Build a desktop application using Electron that embeds the FastAPI backend as a child process, with optional Ollama integration for local AI.

### Architecture

**Dual-process model:**
- Electron main process manages window lifecycle, native dialogs, auto-updates, and child process orchestration
- FastAPI backend compiled via PyInstaller runs as a localhost-only child process
- Renderer process loads the same React frontend, pointed at `http://127.0.0.1:8000`

**Startup sequence:** Ollama (detect/start) → Backend (spawn/health-check) → Window (show UI) → Auto-updater (check)

**LOCAL_MODE:** When `LOCAL_MODE=true`, authentication is bypassed and a default local user is auto-seeded. No login screen, no JWT tokens — single-user by design.

### Ollama Integration

- Detects already-running Ollama instances and reuses them (won't shut down what it didn't start)
- Discovers Ollama binary via `which`/`where` with platform-specific fallback paths
- Auto-starts `ollama serve` if binary found but not running
- Frontend adapts UI based on Electron detection (`window.api?.getOllamaInfo`)

### Resource Bundling

Pandoc and Typst binaries are bundled in `extraResources` for offline document export. Backend binary, Pandoc, and Typst are downloaded/compiled per-platform in CI.

### IPC Bridge

Context-isolated preload script exposes a minimal API: file save dialogs, Ollama info, and auto-updater controls. No direct Node.js access from the renderer.

### Distribution

GitHub Actions builds for macOS (universal binary), Windows (NSIS), and Linux (AppImage). Auto-updater uses GitHub Releases as the update source.

## Consequences

### Positive
- Fully offline operation — no cloud dependency for core features
- Data sovereignty — SQLite database stays on user's machine
- Zero-friction UX — no login, no server setup, double-click to run
- Reuses entire existing web stack without forking code
- Cross-platform from a single codebase

### Negative
- Large app size (~250MB) due to Electron + PyInstaller + Pandoc + Typst
- Complex CI matrix (3 platforms × PyInstaller + binary downloads + Electron packaging)
- Slower startup (~10-30s) while backend initialises
- Single-user only — no multi-device sync or collaboration

### Neutral
- Ollama is optional — local AI quality is lower than cloud APIs, but free and private
- Development mode uses `uv run uvicorn` from source; production uses PyInstaller binary
- Backend listens only on localhost — no network exposure

## Alternatives Considered

### Tauri (Rust-based alternative to Electron)
- Smaller bundle size (~10-20MB for the shell)
- Would require rewriting backend integration in Rust or maintaining a separate sidecar approach
- Less mature ecosystem for complex desktop features (auto-updater, native dialogs)
- Rejected: too much rework for marginal size savings given we already bundle PyInstaller + Pandoc + Typst

### PWA (Progressive Web App)
- No installation required, works in browser
- Cannot manage child processes (Ollama, backend)
- No filesystem access for native save dialogs
- Rejected: cannot deliver offline-first with embedded backend

### Docker Desktop Distribution
- Already works (Docker Compose with Ollama sidecar, ADR-0025/0026)
- Requires Docker installation — high friction for non-technical users
- Rejected as primary desktop strategy, but remains a valid deployment option

## Implementation Notes

- PyInstaller requires explicit `--hidden-import` for dynamically loaded modules (uvicorn, litellm, tiktoken)
- macOS code signing needs JIT and library validation entitlements for Python
- Health check retries differ: 30 in dev (fast feedback), 120 in prod (slower cold starts)
- Backend graceful shutdown: SIGTERM with 3s timeout, then SIGKILL

## References

- [ADR-0024: LOCAL_MODE and PyInstaller Compatibility](0024-local-mode-pyinstaller-compatibility.md)
- [ADR-0025: Ollama Docker Sidecar for Local AI](0025-ollama-docker-sidecar-local-ai.md)
- [ADR-0026: Single-Container Deployment](0026-single-container-deployment.md)
- [ADR-0033: Pandoc + Typst Export Engine](0033-pandoc-typst-export-engine.md)
