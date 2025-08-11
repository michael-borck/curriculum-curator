# Architecture Decision Records

This directory contains Architecture Decision Records (ADRs) for the Curriculum Curator project.

## What is an ADR?

An Architecture Decision Record captures an important architectural decision made along with its context and consequences. ADRs help us understand why certain decisions were made and provide a history of the project's evolution.

## ADR Index

### Foundation
- [ADR-0001: Record Architecture Decisions](0001-record-architecture-decisions.md) - Why we use ADRs
- [ADR-0002: FastHTML Web Framework](0002-fasthtml-web-framework.md) - Choice of web framework

### Architecture
- [ADR-0003: Plugin Architecture](0003-plugin-architecture.md) - Extensibility approach
- [ADR-0005: Hybrid Storage Approach](0005-hybrid-storage-approach.md) - Data persistence strategy

### User Experience
- [ADR-0004: Teaching Philosophy System](0004-teaching-philosophy-system.md) - Personalization framework
- [ADR-0006: Pure FastHTML Without JavaScript](0006-pure-fasthtml-no-javascript.md) - No client-side JS

### Authentication & Security
- [ADR-0007: Simple Authentication for Internal Network](0007-simple-authentication-internal-network.md) - Basic auth approach
- [ADR-0008: Email Verification with Cross-Device Support](0008-email-verification-cross-device.md) - Dual-method verification
- [ADR-0009: Self-Service Password Reset](0009-self-service-password-reset.md) - Email-based password recovery
- [ADR-0010: Security Hardening](0010-security-hardening.md) - Comprehensive security measures
- [ADR-0011: Deployment Best Practices](0011-deployment-best-practices.md) - Production deployment guidelines

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