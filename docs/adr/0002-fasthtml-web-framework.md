# 2. Use FastHTML as Web Framework

Date: 2025-08-01

## Status

Accepted

## Context

The Curriculum Curator was originally implemented as a desktop application using Tauri (Rust + React). We need to migrate to a web-based solution that is:
- Easier to deploy and maintain
- More accessible to users (no installation required)
- Simpler to develop with a unified tech stack
- Still performant and responsive

## Decision

We will use FastHTML as the web framework for the Curriculum Curator. FastHTML is a Python web framework that:
- Uses HTMX for dynamic interactions without complex JavaScript
- Provides a simple, declarative API for building web applications
- Integrates well with Python's async capabilities
- Allows us to keep all logic in Python

## Consequences

### Positive
- Single language (Python) for entire application
- No build step or complex frontend tooling
- Server-side rendering with HTMX for interactivity
- Easy integration with existing Python ML/NLP libraries
- Simpler deployment (single Python process)
- Better for SEO and accessibility

### Negative
- Less rich UI interactions compared to React
- Smaller ecosystem compared to React/Vue/Angular
- Learning curve for HTMX patterns
- Some complex UI patterns may be harder to implement

### Neutral
- Different mental model from SPA development
- Server-side state management instead of client-side
- Need to adapt UI designs to server-side rendering patterns

## Alternatives Considered

### Continue with Tauri
- Desktop app with Rust backend and React frontend
- Rejected due to deployment complexity and installation barriers

### Django/Flask with React
- Traditional Python backend with React SPA
- Rejected due to complexity of maintaining two codebases

### Next.js/Remix
- Full-stack JavaScript frameworks
- Rejected to leverage Python ecosystem for ML/education tools

### Streamlit/Gradio
- Python frameworks for data apps
- Rejected as too limiting for complex multi-page applications

## Implementation Notes

- Use FastHTML's routing system for different modes (wizard/expert)
- Leverage HTMX for dynamic form updates and content loading
- Implement progressive enhancement for better UX
- Use Tailwind CSS for styling (via CDN initially)

## References

- [FastHTML Documentation](https://www.fastht.ml/)
- [HTMX Documentation](https://htmx.org/)
- [ADR-0003](0003-plugin-architecture.md) - Plugin architecture adapted for FastHTML