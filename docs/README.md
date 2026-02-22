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
├── PRD-Development/  # PRD workflow process docs
└── archive/          # Historical docs from FastHTML/NiceGUI/Tauri eras
```

## Key Documents

| Document | Description |
|----------|-------------|
| [CLAUDE.md](../CLAUDE.md) | Development setup, architecture, conventions |
| [PRD](PRD-Curriculum-Curator.md) | Product requirements document |
| [User Stories](user-stories.md) | Feature tracking by phase |
| [Implementation Plan](implementation-plan.md) | Phase completion tracking |
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
- [PRD Development Process](PRD-Development/) — How we create PRDs and task lists

## Archive

Historical planning documents from previous framework eras (FastHTML, NiceGUI, Tauri) and completed migration plans are preserved in [`archive/`](archive/) for reference.
