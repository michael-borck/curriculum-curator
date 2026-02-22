# Curriculum Curator Documentation

Documentation for Curriculum Curator — an AI-powered tool for creating pedagogically-sound curriculum materials.

For development setup, tooling, and code conventions, see [CLAUDE.md](../CLAUDE.md) (the definitive dev guide).

## Documentation Structure

```
docs/
├── adr/              # Architecture Decision Records (40 ADRs)
├── concepts/         # Conceptual overviews (teaching philosophy, plugin system, IMSCC spec)
├── guides/           # How-to guides (Docker deployment, email, teaching styles)
├── mocks/            # UI mockups from early design
└── archive/          # Historical docs (PRD, FastHTML/NiceGUI/Tauri eras, etc.)
```

## Key Documents

| Document | Description |
|----------|-------------|
| [CLAUDE.md](../CLAUDE.md) | Development setup, architecture, conventions |
| [User Stories](user-stories.md) | Feature tracking by phase |
| [Implementation Plan](implementation-plan.md) | Phase completion tracking |
| [Security](SECURITY.md) | Security architecture, auth, rate limiting, headers |
| [ADR Index](adr/index.md) | All architecture decision records |

## Guides

| Guide | Description |
|-------|-------------|
| [Docker VPS Deployment](guides/docker-vps-deployment.md) | Production deployment with Docker |
| [Email Configuration](guides/email-configuration.md) | SMTP setup for verification/reset |
| [Teaching Styles](guides/teaching-styles.md) | 9 pedagogical approaches overview |
| [Teaching Styles Reference](guides/teaching-styles-reference.md) | Detailed style descriptions and prompts |

## Concepts

| Document | Description |
|----------|-------------|
| [Teaching Philosophy](concepts/teaching-philosophy.md) | Core pedagogy system design |
| [Plugin System](concepts/plugin-system.md) | Content validation/remediation plugins |
| [IMSCC Spec](concepts/imscc-spec.md) | IMS Common Cartridge export spec |

## Other

- [UI Mockups](mocks/) — Early design mockups (PNG + TSX)

## Archive

Historical planning documents preserved in [`archive/`](archive/) for reference. Includes the original PRD (Dec 2024), PRD development process templates, and docs from previous framework eras (FastHTML, NiceGUI, Tauri).
