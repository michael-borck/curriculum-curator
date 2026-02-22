# ADR-037: Privacy-First, Local-First, BYOK Architecture

Date: 2026-02-21

## Status

Accepted

## Context

Curriculum Curator includes AI-powered features (content generation, pedagogy analysis, schedule planning) that require LLM access. The conventional approach is to host a backend service that proxies LLM calls through the developer's API keys, charging users via subscription.

This model has significant drawbacks for our target users (university lecturers):

- **Data sensitivity**: Course materials, assessment designs, and pedagogical strategies are intellectual property. Routing them through third-party infrastructure creates privacy and IP concerns.
- **Vendor lock-in**: A hosted service ties users to our availability, pricing, and provider choices. If the service shuts down, users lose access to AI features entirely.
- **Institutional barriers**: Many universities have strict procurement and data-sovereignty policies that prohibit sending academic content to external SaaS platforms without formal review.
- **Cost opacity**: Subscription pricing obscures the actual cost of AI usage, which varies dramatically by model and usage pattern.

We already maintain a VPS/self-hosted version with user accounts and authentication. However, the primary distribution targets are a **single-user Electron desktop app** (ADR-035) and a **single-user Docker container**, both designed to run entirely on the user's own hardware.

## Decision

Adopt a **privacy-first, local-first, Bring Your Own Key (BYOK)** architecture as the foundational design principle. All architectural choices must satisfy three constraints:

### 1. Local-First Data

- All user data (SQLite database, content files, Git repositories) lives on the user's filesystem.
- No mandatory cloud sync, no remote database, no server-side storage of user content.
- Uninstalling the app removes the data. Backing up is copying a directory.
- No user accounts required for single-user deployments (Electron, Docker).

### 2. No Telemetry, No Call-Home

- Zero analytics, usage tracking, or crash reporting sent to any external service.
- No network requests except those explicitly initiated by the user (LLM API calls, web search).
- The application must function fully offline when using local models.
- Open source and fully auditable — privacy is a structural property, not a policy claim.

### 3. BYOK AI Provider Model

- Users configure their own LLM access via one of two paths:
  - **Local**: Point to an Ollama installation running open-weight models on their own hardware. Data never leaves the machine.
  - **Cloud BYOK**: Supply their own API keys for OpenAI, Anthropic, Google, or other providers. The app calls the provider directly — we are not a proxy or middleman.
- The LLM provider abstraction (`LLMService`) must support multiple backends with a unified interface.
- Provider selection and API keys are stored locally in the app's configuration, never transmitted.
- The user controls which models they use, where their data flows, and how much they spend.

## Consequences

### Positive

- **Full data sovereignty**: Users own their data with no ambiguity. No terms of service govern their content.
- **Institutional compatibility**: Universities can approve the tool without data-sovereignty concerns, since nothing leaves the user's machine (with local models).
- **Offline capability**: Core editing, organisation, and local AI features work without any internet connection.
- **Cost transparency**: Users see exactly what they spend on AI (their own API bills) or spend nothing (Ollama).
- **Longevity**: The app doesn't depend on our continued operation. If we stop development, existing installs keep working.
- **Trust through verification**: Open source + local-first means users (or their IT departments) can audit exactly what the software does.

### Negative

- **No seamless multi-device sync**: Local-first means no built-in cross-device access. Users must manually transfer data (or use their own sync solution like Syncthing/Dropbox on the data directory).
- **User setup burden**: BYOK requires users to either install Ollama or obtain API keys — more friction than "click Start" on a hosted service.
- **Electron footprint**: Desktop distribution via Electron carries a larger install size and memory footprint than a browser tab.
- **Support complexity**: Multiple LLM providers and local model configurations create a wider surface area for troubleshooting.
- **No shared state**: Collaboration features (shared units, team review) are out of scope for single-user deployments.

### Neutral

- The VPS/self-hosted version with accounts continues to exist for users who prefer that model, but it is not the primary distribution target.
- The Learning Design context system (ADR-036) is specifically designed to compensate for smaller local models by providing rich structured context that frontier models can infer from sparse input.

## Alternatives Considered

### Hosted SaaS with Managed API Keys

- We proxy all LLM calls through our infrastructure, billing users via subscription.
- Rejected: contradicts privacy-first principle, creates vendor lock-in, introduces data-sovereignty concerns for institutional users, and makes us a cost middleman.

### Hybrid Cloud with Optional Sync

- Local-first with an optional cloud sync layer for multi-device access.
- Not rejected outright, but deferred. Could be added later as an opt-in feature without compromising the local-first default. User would need to provide their own sync backend.

### Browser-Only PWA

- Ship as a Progressive Web App to avoid Electron overhead.
- Rejected: PWAs have limited filesystem access, cannot run Ollama locally, and cannot guarantee offline capability as reliably. Does not satisfy the local-first constraint for AI features.

## Implementation Notes

- `backend/app/services/llm_service.py` implements the multi-provider abstraction (OpenAI, Anthropic, Ollama).
- `backend/app/services/ollama_service.py` handles local model discovery and management.
- API keys are stored in the local SQLite database (`system_config` table), never transmitted.
- The Electron app (ADR-035) embeds the FastAPI backend, making the entire stack a single desktop application.
- Docker distribution bundles the same backend + frontend, exposing only `localhost`.

## References

- [ADR-035: Electron Desktop App](035-electron-desktop-app.md)
- [ADR-036: Learning Design as Canonical Generation Spec](036-learning-design-generation-spec.md)
- [Privacy-First, BYOK: Building Software That Respects Its Users](/Users/michael/Downloads/privacy-first-byok-apps.md) — original concept article
