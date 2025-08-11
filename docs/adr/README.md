# Architecture Decision Records

This directory contains Architecture Decision Records (ADRs) for the Curriculum Curator FastHTML implementation.

## What are ADRs?

Architecture Decision Records capture important architectural decisions made during the project's development, along with their context and consequences. Each ADR describes a specific choice and the reasoning behind it.

## Why use ADRs?

- **Documentation**: Preserve the context and reasoning behind decisions
- **Communication**: Help new team members understand the architecture
- **History**: Track how the architecture evolved over time
- **Reflection**: Force careful consideration of architectural choices

## ADR Index

- [ADR-0001](0001-record-architecture-decisions.md) - Record Architecture Decisions
- [ADR-0002](0002-fasthtml-web-framework.md) - Use FastHTML as Web Framework
- [ADR-0003](0003-plugin-architecture.md) - Plugin Architecture for Validators and Remediators
- [ADR-0004](0004-teaching-philosophy-system.md) - Teaching Philosophy and Style System
- [ADR-0005](0005-hybrid-storage-approach.md) - Hybrid Database and Filesystem Storage
- [ADR-0006](0006-pure-fasthtml-no-javascript.md) - Pure FastHTML Without JavaScript
- [ADR-0007](0007-simple-authentication-internal-network.md) - Simple Authentication for Internal Network Deployment

## Creating a New ADR

1. Copy the template: `cp template.md NNNN-title-with-hyphens.md`
2. Fill in all sections
3. Set status to "Proposed"
4. Add a link in this README
5. Submit for review
6. Update status to "Accepted" once approved

## ADR Process

1. **Propose**: Create ADR with "Proposed" status
2. **Discuss**: Review with team, gather feedback
3. **Decide**: Accept, reject, or request changes
4. **Document**: Update status and merge

## Guidelines

- Keep ADRs concise but complete
- Focus on the "why" not just the "what"
- Include alternatives considered
- Be honest about trade-offs
- Link to related ADRs
- Use clear, simple language