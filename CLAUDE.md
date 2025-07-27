# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build and Development Commands

### Frontend (React + TypeScript)
```bash
# Development
npm run dev              # Run full Tauri app in development mode
npm run frontend:dev     # Run only frontend (Vite) dev server
npm run tauri:dev:verbose # Run with Rust debug logging enabled

# Type checking and linting
npm run type-check       # Check TypeScript types
npm run lint            # Run ESLint
npm run lint:fix        # Auto-fix ESLint issues
npm run dev:check       # Run all checks (type-check + lint + rust:check)

# Building
npm run build           # Build production Tauri app
npm run frontend:build  # Build only frontend
npm run tauri:build:debug # Build Tauri app with debug symbols
```

### Backend (Rust/Tauri)
```bash
# Development
cd src-tauri
cargo check             # Quick compilation check
cargo test              # Run all tests
cargo test test_name    # Run specific test
cargo clippy -- -D warnings  # Run Rust linter
cargo fmt               # Format Rust code

# Features
cargo build --features chrome-pdf    # Build with Chrome PDF support
cargo build --features full         # Build with all optional features
```

### Combined Commands
```bash
npm run dev:format      # Format both JS/TS and Rust code
npm run dev:full        # Run all checks then start dev mode
```

## Architecture Overview

### Technology Stack
- **Frontend**: React 19 with TypeScript, Vite build system
- **Backend**: Tauri 2.5 (Rust) for native desktop functionality
- **Database**: SQLite via sqlx for local session storage
- **Styling**: CSS modules with desktop-first responsive design

### Core Architecture Patterns

#### 1. Command-Based IPC
The app uses Tauri's command system for frontend-backend communication:
- Frontend invokes commands via `@tauri-apps/api`
- Backend handlers in `src-tauri/src/commands.rs` and module-specific command files
- All async operations use Rust's tokio runtime

#### 2. Service Layer Architecture
Backend organized into domain-specific services:
- `SessionService` - Session management and persistence
- `FileService` - File operations and storage management
- `BackupService` - Automated and manual backups
- `ImportService` - Document import functionality
- `GitService` - Version control integration
- `DataExportService` - Export to various formats
- `MaintenanceService` - System health and cleanup
- `ValidationService` - Content validation system

Services are injected via Tauri's state management system and shared across commands.

#### 3. LLM Provider System
Flexible LLM integration supporting multiple providers:
- `LLMManager` orchestrates provider selection and routing
- Provider implementations: `OpenAIProvider`, `ClaudeProvider`, `GeminiProvider`, `OllamaProvider`
- Streaming response support for real-time generation
- Rate limiting and cost tracking built-in
- Secure API key storage via system keyring

#### 4. Content Generation Pipeline
Multi-stage content generation workflow:
1. User input collection (Wizard or Expert mode)
2. Context building with learning objectives
3. Template-based prompt generation
4. LLM provider routing and generation
5. Content validation and enhancement
6. Export to multiple formats

#### 5. Validation System
Comprehensive content validation framework:
- Built-in validators: Structure, Readability, Completeness, Grammar, ContentAlignment
- Validators implement the `Validator` trait
- Configurable per content type and complexity level
- Auto-fix capabilities for certain issues
- No external plugin system - all validators are compiled in

#### 6. Frontend State Management
- React Context API for global state (Settings, User Profile)
- Custom hooks for feature-specific logic (`useLLM`, `useBackup`, etc.)
- Cross-session learning system tracks user preferences
- Status feedback system for user notifications

### Key Design Decisions

1. **Desktop-First**: Built as a native app, not a web service. UI runs in Tauri webview.

2. **Privacy-Focused**: All data stored locally, API keys in system keyring, no telemetry.

3. **Offline Capable**: Supports Ollama for completely offline LLM usage.

4. **Modular Validators**: Validation system uses trait-based design but doesn't support external plugins.

5. **Streaming Architecture**: LLM responses stream in real-time for better UX.

6. **Session-Based**: All work organized into sessions that can be saved, loaded, and versioned.

### Database Schema
SQLite database (`curriculum_curator.db`) with key tables:
- `sessions` - Curriculum generation sessions
- `session_content` - Generated content linked to sessions
- `settings` - User preferences and configuration
- `api_keys` - Encrypted API key storage (backup to keyring)
- `validation_reports` - Content validation history

### Important File Locations
- Frontend entry: `src/main.tsx` and `src/App.tsx`
- Backend entry: `src-tauri/src/main.rs`
- Command handlers: `src-tauri/src/commands.rs` and module-specific commands
- LLM providers: `src-tauri/src/llm/`
- Export formats: `src-tauri/src/export/`
- Validation: `src-tauri/src/validation/`

### Security Considerations
- API keys stored in system keyring via `keyring` crate
- Database encryption not implemented (local-only app)
- No network requests except to LLM providers
- File system access restricted to app directories by default

## Development Workflow

### Task-Based Development
We follow a methodical, task-by-task approach:

1. **One Task at a Time**: Work on single TODO items sequentially
2. **Test Before Proceed**: Run tests after each task completion
3. **Confirmation Required**: Get explicit approval before starting next task
4. **Check off Progress**: Mark tasks as completed in TodoWrite

### Testing Strategy

#### Automated Tests (Rust Backend)
```bash
# Run all backend tests
cd src-tauri && cargo test

# Run specific test module
cargo test import::tests

# Run tests with output
cargo test -- --nocapture

# Run tests for specific feature
cargo test --features import-office-docs
```

#### Frontend Tests (when available)
```bash
# Run React component tests
npm test

# Run with coverage
npm run test:coverage
```

#### Manual Testing (GUI/Integration)
- Import workflow testing with sample files
- UI component interaction testing
- End-to-end workflow validation
- Cross-platform testing (Windows/Mac/Linux)

### Current Phase 1 Implementation Plan

**Phase 1 Goal**: Fix Core Import/Export functionality

**Next Task**: Add XML parsing dependencies to Cargo.toml
- Task ID: Fix XML parsing for Office documents (first subtask)
- Expected outcome: Compilation errors resolved, dependencies available
- Test: `cargo check` should pass without XML-related errors

**Testing for Phase 1**:
- **Backend Tests**: Unit tests for each parser (PowerPoint, Word, Markdown)
- **Integration Tests**: End-to-end import workflow tests
- **Manual Tests**: GUI testing of import/preview/analysis workflow
- **Sample Files**: Use test files in `test_files/` directory

### File Structure for Phase 1
```
src-tauri/src/
├── import/               # New import functionality
│   ├── mod.rs           # Module definitions
│   ├── parsers.rs       # Parser implementations (currently disabled)
│   ├── powerpoint.rs    # PowerPoint parser
│   ├── word.rs          # Word document parser
│   ├── markdown.rs      # Markdown parser
│   ├── analysis.rs      # Content analysis engine
│   ├── errors.rs        # Import error types
│   └── tests.rs         # Import tests
├── commands/
│   └── import.rs        # Tauri commands for import
└── test_files/          # Sample files for testing
    ├── sample.pptx
    ├── sample.docx
    └── sample.md
```

### Development Rules
1. **NEVER** skip tests - always run `cargo test` after changes
2. **ALWAYS** check compilation with `cargo check` before committing
3. **CONFIRM** each task completion before proceeding
4. **UPDATE** TodoWrite to track progress accurately
5. **ASK** before making architectural decisions