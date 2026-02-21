# Architecture Decision Records

This directory contains Architecture Decision Records (ADRs) for the Curriculum Curator project.

## What is an ADR?

An Architecture Decision Record captures an important architectural decision made along with its context and consequences. ADRs help us understand why certain decisions were made and provide a history of the project's evolution.

## ADR Index

### Guiding Principles

| ADR | Title | Status |
|-----|-------|--------|
| [0018](0018-workflow-flexibility-philosophy.md) | **Workflow Flexibility Philosophy** | **Accepted** |
| [0020](0020-ai-optional-user-empowerment.md) | **AI-Optional User Empowerment** | **Accepted** |

> *"Assist any workflow, don't enforce"* - This principle informs all other architectural decisions.
> 
> *"AI assists, never gates"* - Every task achievable with AI must be equally achievable without it.

### Current Stack (Active Decisions)

| ADR | Title | Status |
|-----|-------|--------|
| [0016](0016-react-typescript-frontend.md) | React + TypeScript Frontend | **Accepted** |
| [0017](0017-fastapi-rest-backend.md) | FastAPI REST Backend with JWT Auth | **Accepted** |
| [0019](0019-database-abstraction-sqlalchemy.md) | Database Abstraction with SQLAlchemy | **Accepted** |
| [0021](0021-web-search-citation-integration.md) | Web Search and Citation Integration | **Accepted** |
| [0022](0022-content-type-system-evolution.md) | Content Type System Evolution | **Accepted** |
| [0023](0023-file-import-processing-architecture.md) | File Import and Processing Architecture | **Accepted** |
| [0015](0015-content-format-and-export-strategy.md) | Content Format and Export Strategy | Proposed |
| [0014](0014-litellm-unified-llm-abstraction.md) | LiteLLM for Unified LLM Abstraction | Accepted |
| [0024](0024-local-mode-pyinstaller-compatibility.md) | LOCAL_MODE and PyInstaller Compatibility | Accepted |
| [0025](0025-ollama-docker-sidecar-local-ai.md) | Ollama Docker Sidecar for Local AI | Accepted |
| [0026](0026-single-container-deployment.md) | Single-Container Deployment (FastAPI Serves SPA) | Accepted |
| [0027](0027-camelcase-api-serialization.md) | CamelCase API Serialization Convention | Accepted |
| [0028](0028-australian-university-terminology.md) | Australian University Terminology | Accepted |
| [0029](0029-accreditation-framework-mappings.md) | Accreditation Framework Mappings (AoL, Grad Caps, SDGs) | Accepted |
| [0030](0030-ims-common-cartridge-export.md) | IMS Common Cartridge Export | Accepted |
| [0031](0031-soft-delete-units.md) | Soft-Delete Units | Accepted |
| [0032](0032-ai-assistance-levels.md) | AI Assistance Levels | Accepted |
| [0033](0033-pandoc-typst-export-engine.md) | Pandoc + Typst Export Engine | Accepted |
| [0035](0035-electron-desktop-app.md) | Electron Desktop App with Embedded Backend | Accepted |
| [0036](0036-learning-design-generation-spec.md) | Learning Design as Canonical Generation Spec | Accepted |
| [0013](0013-git-backed-content-storage.md) | Git-Backed Content Storage | Proposed (Phase 2) |

### Foundation
- [ADR-0001: Record Architecture Decisions](0001-record-architecture-decisions.md) - Why we use ADRs

### Architecture
- [ADR-0003: Plugin Architecture](0003-plugin-architecture.md) - Extensibility approach
- [ADR-0005: Hybrid Storage Approach](0005-hybrid-storage-approach.md) - Data persistence strategy
- [ADR-0019: Database Abstraction](0019-database-abstraction-sqlalchemy.md) - SQLAlchemy ORM for portability
- [ADR-0021: Web Search and Citation Integration](0021-web-search-citation-integration.md) - Academic research integration
- [ADR-0023: File Import and Processing Architecture](0023-file-import-processing-architecture.md) - Multi-format document processing
- [ADR-0026: Single-Container Deployment](0026-single-container-deployment.md) - FastAPI serves the React SPA directly
- [ADR-0027: CamelCase API Serialization](0027-camelcase-api-serialization.md) - snake_case Python, camelCase JSON
- [ADR-0030: IMS Common Cartridge Export](0030-ims-common-cartridge-export.md) - CC v1.2 export for LMS interoperability
- [ADR-0035: Electron Desktop App](0035-electron-desktop-app.md) - Embedded backend with optional Ollama for offline use

### Domain Model & User Experience
- [ADR-0004: Teaching Philosophy System](0004-teaching-philosophy-system.md) - Personalization framework
- [ADR-0018: Workflow Flexibility](0018-workflow-flexibility-philosophy.md) - Assist, don't enforce
- [ADR-0020: AI-Optional User Empowerment](0020-ai-optional-user-empowerment.md) - AI assists, never gates
- [ADR-0022: Content Type System Evolution](0022-content-type-system-evolution.md) - Comprehensive content categorization
- [ADR-0028: Australian University Terminology](0028-australian-university-terminology.md) - Unit (not Course) as core entity
- [ADR-0029: Accreditation Framework Mappings](0029-accreditation-framework-mappings.md) - AoL, Graduate Capabilities, UN SDGs
- [ADR-0036: Learning Design as Generation Spec](0036-learning-design-generation-spec.md) - Structured spec feeds all AI generation paths

### Authentication & Security
- [ADR-0007: Simple Authentication for Internal Network](0007-simple-authentication-internal-network.md) - Basic auth approach
- [ADR-0008: Email Verification with Cross-Device Support](0008-email-verification-cross-device.md) - Dual-method verification
- [ADR-0009: Self-Service Password Reset](0009-self-service-password-reset.md) - Email-based password recovery
- [ADR-0010: Security Hardening](0010-security-hardening.md) - Comprehensive security measures
- [ADR-0011: Deployment Best Practices](0011-deployment-best-practices.md) - Production deployment guidelines

### Superseded Decisions (Historical)

These ADRs document previous architectural directions that have since been replaced:

| ADR | Title | Superseded By |
|-----|-------|---------------|
| [0002](0002-fasthtml-web-framework.md) | FastHTML Web Framework | ADR-0016 |
| [0006](0006-pure-fasthtml-no-javascript.md) | Pure FastHTML Without JavaScript | ADR-0016 |
| [0012](0012-framework-migration-fasthtml-to-nicegui.md) | Framework Migration to NiceGUI | ADR-0016 |

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
