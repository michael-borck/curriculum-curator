# 25. Ollama Docker Sidecar for Local AI

Date: 2026-02-20

## Status

Accepted

## Context

The LOCAL_MODE deployment (ADR-0024) gives users a privacy-first, self-hosted Curriculum Curator. However, AI content generation still requires external API keys (OpenAI, Anthropic, etc.), which creates friction for local users who want to try AI features without signing up for third-party services or sending data off-machine.

We need a way for local users to run AI models entirely on their own hardware with minimal setup effort. The solution must:

1. **Not require API keys** — the whole point is zero-config local AI
2. **Not break the existing stack** — users without local AI should be unaffected
3. **Leverage existing infrastructure** — LiteLLM already supports Ollama via `ollama/model_name` format (ADR-0014)
4. **Be resource-aware** — not all machines can run large models

## Decision

We run **Ollama as an optional Docker sidecar** using Docker Compose profiles, with a backend management service and a frontend setup wizard.

### Architecture

```
┌─────────────────────────────────────────────────┐
│            docker compose up                     │
│  ┌───────────────────┐  ┌────────────────────┐  │
│  │  app (backend +   │  │  ollama (sidecar)   │  │
│  │  frontend)        │◄─┤  profile: local-ai  │  │
│  │                   │  │  port 11434         │  │
│  │  OllamaService ───┤  │  ollama_data volume │  │
│  └───────────────────┘  └────────────────────┘  │
└─────────────────────────────────────────────────┘
```

- **Docker Compose profile** (`local-ai`): Ollama only starts when explicitly requested via `docker compose --profile local-ai up`. Without the profile flag, the app starts normally with no Ollama dependency.
- **OllamaService** (backend): Thin wrapper around Ollama's HTTP API for status checks, model pulls (streamed as SSE), deletions, and test generation. Uses `psutil` (already a dependency) to recommend models based on available RAM.
- **Setup wizard** (frontend): 4-step flow — check connection, select model (RAM-aware recommendations), download with progress bar, test and activate. Only visible in LOCAL_MODE.
- **Seeded config**: On LOCAL_MODE startup, the backend seeds an inactive `LLMConfiguration` record with `provider=ollama`. The wizard activates it after a successful model pull and test.

### Model Recommendations

| System RAM | Recommended Model | Size |
|------------|------------------|------|
| < 8 GB     | TinyLlama (1.1B) | ~637 MB |
| 8-16 GB    | Llama 3.2 (3B)   | ~2 GB |
| 16+ GB     | Mistral (7B)     | ~4.1 GB |

### Key Design Choices

1. **Profile-gated, not always-on**: Ollama is a ~1 GB image and reserves GPU/RAM. Gating it behind a profile prevents resource waste for users who don't want local AI.
2. **User-initiated download**: Models are pulled on-demand via the wizard, not pre-loaded. This avoids multi-GB downloads on first startup and lets users choose the model that fits their hardware.
3. **SSE progress streaming**: Model pulls can take minutes. We stream Ollama's pull progress to the frontend as Server-Sent Events, reusing the same SSE pattern used for AI content generation.
4. **Inactive until tested**: The seeded Ollama config stays `is_active=False` until the user completes the wizard (model downloaded + test generation passes). This prevents broken AI calls if Ollama isn't ready.

## Consequences

### Positive

- Local users can generate content with zero external dependencies or API keys
- All data stays on the user's machine — true privacy-first AI
- Leverages existing LiteLLM integration — no changes to `llm_service.py`
- Graceful degradation: if Ollama is down, the app works normally without AI
- RAM-based recommendations prevent users from pulling models that won't run
- Docker volume persists downloaded models across container restarts

### Negative

- Ollama Docker image adds ~1 GB to the local deployment footprint
- Local models produce lower-quality output than GPT-4/Claude, which may disappoint users expecting cloud-tier results
- GPU passthrough in Docker requires additional configuration (`--gpus` flag) that we don't set up automatically
- First model download requires internet access (subsequent runs are offline)

### Neutral

- Users with their own Ollama installation (not via Docker) can point `OLLAMA_BASE_URL` to their instance and skip the sidecar entirely
- The wizard UX only appears in LOCAL_MODE; cloud deployments are unaffected
- Model management (pull/delete) is manual via the wizard — no auto-updates

## Alternatives Considered

### Bundling a model in the Docker image

- Pre-bake a small model into the image so AI works immediately on first start
- **Rejected**: Would add 2-5 GB to the image size, and users with more RAM would want a larger model anyway. On-demand pull is more flexible.

### llama.cpp directly (no Ollama)

- Embed llama.cpp as a Python binding (e.g., `llama-cpp-python`)
- **Rejected**: More integration work, no HTTP API, harder to manage models, less community support. Ollama provides a well-maintained HTTP API and model registry for free.

### LocalAI / LM Studio

- Alternative local inference servers
- **Rejected**: Ollama has the best Docker story, the simplest API, and LiteLLM already has native support for it via the `ollama/` model prefix.

### Always-on Ollama (no profile gating)

- Start Ollama with every `docker compose up`
- **Rejected**: Wastes resources for users who don't want local AI. Profiles make it opt-in.

## Implementation Notes

### Files Changed

| File | Change |
|------|--------|
| `backend/app/core/config.py` | Added `OLLAMA_BASE_URL` setting |
| `backend/app/services/ollama_service.py` | New — Ollama HTTP API wrapper |
| `backend/app/api/routes/ollama.py` | New — 5 management endpoints |
| `backend/app/main.py` | Route registration + config seeding |
| `docker-compose.yml` | Ollama sidecar with `profiles: [local-ai]` |
| `frontend/src/types/ollama.ts` | New — TypeScript interfaces |
| `frontend/src/services/ollamaApi.ts` | New — API client with SSE streaming |
| `frontend/src/features/settings/LocalAISetup.tsx` | New — 4-step setup wizard |
| `frontend/src/features/settings/LLMSettings.tsx` | Local AI card integration |

### Docker Usage

```bash
# Without local AI (default)
docker compose up

# With local AI sidecar
docker compose --profile local-ai up

# With local AI + environment override for Docker networking
OLLAMA_BASE_URL=http://ollama:11434 docker compose --profile local-ai up
```

## References

- [ADR-0014: LiteLLM Unified LLM Abstraction](0014-litellm-unified-llm-abstraction.md) — Ollama support via `ollama/model_name`
- [ADR-0020: AI-Optional User Empowerment](0020-ai-optional-user-empowerment.md) — AI assists, never gates
- [ADR-0024: LOCAL_MODE and PyInstaller Compatibility](0024-local-mode-pyinstaller-compatibility.md) — Privacy-first local deployment
- [Ollama API Documentation](https://github.com/ollama/ollama/blob/main/docs/api.md)
- [Docker Compose Profiles](https://docs.docker.com/compose/profiles/)
