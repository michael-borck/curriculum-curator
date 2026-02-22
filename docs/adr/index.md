# Architecture Decision Records

This directory contains Architecture Decision Records (ADRs) for the Curriculum Curator project.

## What is an ADR?

An Architecture Decision Record captures an important architectural decision made along with its context and consequences. ADRs help us understand why certain decisions were made and provide a history of the project's evolution.

## ADR Index

### Guiding Principles

| ADR | Title | Status |
|-----|-------|--------|
| [018](018-workflow-flexibility-philosophy.md) | **Workflow Flexibility Philosophy** | **Accepted** |
| [020](020-ai-optional-user-empowerment.md) | **AI-Optional User Empowerment** | **Accepted** |
| [037](037-privacy-first-byok-architecture.md) | **Privacy-First, Local-First, BYOK** | **Accepted** |
| [040](040-ambient-context-pattern.md) | **Ambient Context — Best Guess + Human Override** | **Accepted** |

> *"Assist any workflow, don't enforce"* - This principle informs all other architectural decisions.
>
> *"AI assists, never gates"* - Every task achievable with AI must be equally achievable without it.
>
> *"You own everything"* - Local data, open source, bring your own AI keys. No middleman.
>
> *"Best guess + human override"* - Infer context automatically, but the user can always change or clear it.

### Current Stack (Active Decisions)

| ADR | Title | Status |
|-----|-------|--------|
| [016](016-react-typescript-frontend.md) | React + TypeScript Frontend | **Accepted** |
| [017](017-fastapi-rest-backend.md) | FastAPI REST Backend with JWT Auth | **Accepted** |
| [019](019-database-abstraction-sqlalchemy.md) | Database Abstraction with SQLAlchemy | **Accepted** |
| [021](021-web-search-citation-integration.md) | Web Search and Citation Integration | **Accepted** |
| [022](022-content-type-system-evolution.md) | Content Type System Evolution | **Accepted** |
| [023](023-file-import-processing-architecture.md) | File Import and Processing Architecture | **Accepted** |
| [015](015-content-format-and-export-strategy.md) | Content Format and Export Strategy | Proposed |
| [014](014-litellm-unified-llm-abstraction.md) | LiteLLM for Unified LLM Abstraction | Accepted |
| [024](024-local-mode-pyinstaller-compatibility.md) | LOCAL_MODE and PyInstaller Compatibility | Accepted |
| [025](025-ollama-docker-sidecar-local-ai.md) | Ollama Docker Sidecar for Local AI | Accepted |
| [026](026-single-container-deployment.md) | Single-Container Deployment (FastAPI Serves SPA) | Accepted |
| [027](027-camelcase-api-serialization.md) | CamelCase API Serialization Convention | Accepted |
| [028](028-australian-university-terminology.md) | Australian University Terminology | Accepted |
| [029](029-accreditation-framework-mappings.md) | Accreditation Framework Mappings (AoL, Grad Caps, SDGs) | Accepted |
| [030](030-ims-common-cartridge-export.md) | IMS Common Cartridge Export | Accepted |
| [031](031-soft-delete-units.md) | Soft-Delete Units | Accepted |
| [032](032-ai-assistance-levels.md) | AI Assistance Levels | Accepted |
| [033](033-pandoc-typst-export-engine.md) | Pandoc + Typst Export Engine | Accepted |
| [035](035-electron-desktop-app.md) | Electron Desktop App with Embedded Backend | Accepted |
| [036](036-learning-design-generation-spec.md) | Learning Design as Canonical Generation Spec | Accepted |
| [037](037-privacy-first-byok-architecture.md) | Privacy-First, Local-First, BYOK Architecture | Accepted |
| [038](038-content-not-presentation.md) | Content Curation, Not Presentation Design | Accepted |
| [039](039-tiered-research-architecture.md) | Tiered Research Architecture with Propose/Apply Workflows | Accepted |
| [013](013-git-backed-content-storage.md) | Git-Backed Content Storage | Proposed (Phase 2) |

### Foundation
- [ADR-001: Record Architecture Decisions](001-record-architecture-decisions.md) - Why we use ADRs

### Architecture
- [ADR-003: Plugin Architecture](003-plugin-architecture.md) - Extensibility approach
- [ADR-005: Hybrid Storage Approach](005-hybrid-storage-approach.md) - Data persistence strategy
- [ADR-019: Database Abstraction](019-database-abstraction-sqlalchemy.md) - SQLAlchemy ORM for portability
- [ADR-021: Web Search and Citation Integration](021-web-search-citation-integration.md) - Academic research integration
- [ADR-023: File Import and Processing Architecture](023-file-import-processing-architecture.md) - Multi-format document processing
- [ADR-026: Single-Container Deployment](026-single-container-deployment.md) - FastAPI serves the React SPA directly
- [ADR-027: CamelCase API Serialization](027-camelcase-api-serialization.md) - snake_case Python, camelCase JSON
- [ADR-030: IMS Common Cartridge Export](030-ims-common-cartridge-export.md) - CC v1.2 export for LMS interoperability
- [ADR-035: Electron Desktop App](035-electron-desktop-app.md) - Embedded backend with optional Ollama for offline use
- [ADR-037: Privacy-First, BYOK Architecture](037-privacy-first-byok-architecture.md) - Local data, no telemetry, user-configured AI providers
- [ADR-038: Content Curation, Not Presentation Design](038-content-not-presentation.md) - Strip on import, theme on export, semantic editing
- [ADR-039: Tiered Research Architecture](039-tiered-research-architecture.md) - Four-tier search (academic→LLM→web API→SearXNG) with propose/apply synthesis

### Domain Model & User Experience
- [ADR-004: Teaching Philosophy System](004-teaching-philosophy-system.md) - Personalization framework
- [ADR-018: Workflow Flexibility](018-workflow-flexibility-philosophy.md) - Assist, don't enforce
- [ADR-020: AI-Optional User Empowerment](020-ai-optional-user-empowerment.md) - AI assists, never gates
- [ADR-022: Content Type System Evolution](022-content-type-system-evolution.md) - Comprehensive content categorization
- [ADR-028: Australian University Terminology](028-australian-university-terminology.md) - Unit (not Course) as core entity
- [ADR-029: Accreditation Framework Mappings](029-accreditation-framework-mappings.md) - AoL, Graduate Capabilities, UN SDGs
- [ADR-036: Learning Design as Generation Spec](036-learning-design-generation-spec.md) - Structured spec feeds all AI generation paths
- [ADR-040: Ambient Context](040-ambient-context-pattern.md) - Best guess + human override for working context

### Authentication & Security
- [ADR-007: Simple Authentication for Internal Network](007-simple-authentication-internal-network.md) - Basic auth approach
- [ADR-008: Email Verification with Cross-Device Support](008-email-verification-cross-device.md) - Dual-method verification
- [ADR-009: Self-Service Password Reset](009-self-service-password-reset.md) - Email-based password recovery
- [ADR-010: Security Hardening](010-security-hardening.md) - Comprehensive security measures
- [ADR-011: Deployment Best Practices](011-deployment-best-practices.md) - Production deployment guidelines

### Superseded Decisions (Historical)

These ADRs document previous architectural directions that have since been replaced:

| ADR | Title | Superseded By |
|-----|-------|---------------|
| [002](002-fasthtml-web-framework.md) | FastHTML Web Framework | ADR-016 |
| [006](006-pure-fasthtml-no-javascript.md) | Pure FastHTML Without JavaScript | ADR-016 |
| [012](012-framework-migration-fasthtml-to-nicegui.md) | Framework Migration to NiceGUI | ADR-016 |

**Evolution Summary**: The project started with FastHTML (server-rendered Python), planned a migration to NiceGUI (never implemented), and ultimately adopted React + TypeScript frontend with FastAPI backend for the production stack.

## ADR Status

- **Accepted**: The decision is accepted and implemented
- **Proposed**: The decision is under consideration
- **Deprecated**: The decision has been superseded by another ADR
- **Superseded**: The decision has been replaced (links to replacement)

## Creating New ADRs

Use the [template.md](template.md) to create new ADRs. Number them sequentially and use descriptive titles.

## Best Practices

1. **Immutability**: Once accepted, ADRs should not be edited except for:
   - Minor typo fixes
   - Adding links to related ADRs
   - Updating status when superseded

2. **Cross-References**: Link related ADRs to show how decisions build on each other

3. **Context is Key**: Explain WHY the decision was made, not just what was decided

4. **Consider Alternatives**: Document what other options were considered and why they were rejected
