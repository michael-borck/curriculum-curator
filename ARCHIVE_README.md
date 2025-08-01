# Tauri Version Archive

This branch contains the Tauri-based implementation of Curriculum Curator.

## Version Info
- **Framework**: Tauri 2.5 + React 19 + TypeScript
- **Backend**: Rust with SQLite
- **Archived Date**: 2025-08-01
- **Status**: Functional desktop application

## Key Features Implemented
- Desktop-first responsive UI
- Multiple LLM provider support (OpenAI, Claude, Gemini, Ollama)
- Document import (.pptx, .docx)
- Content generation with templates
- Session management
- Multiple export formats (PDF, Word, HTML, Quarto)
- Git integration
- Backup system

## Architecture Highlights
- Command-based IPC between frontend and backend
- Service layer architecture in Rust
- Streaming LLM responses
- Secure API key storage
- Built-in validators (no plugin system)

## Why Archived
Transitioning to a Python-based FastHTML web application to:
- Enable easier deployment in university network environment
- Add plugin system for validators and remediators
- Leverage Python ecosystem for faster development
- Support multi-user access without installation

## Lessons Learned
- Tauri provides excellent desktop performance
- Rust backend is fast but slower to develop
- Plugin system would benefit power users
- Web deployment better suits institutional needs

For the new FastHTML implementation, see the main branch.