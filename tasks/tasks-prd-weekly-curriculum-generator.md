# Task List: Weekly Curriculum Content Generator

Based on PRD: `prd-weekly-curriculum-generator.md`

## Relevant Files

- `src-tauri/src/main.rs` - Main Tauri application entry point and command registration (CREATED)
- `src-tauri/src/lib.rs` - Library exports and module declarations (CREATED)
- `src-tauri/Cargo.toml` - Rust dependencies and project configuration (CREATED)
- `src-tauri/tauri.conf.json` - Tauri application configuration with plugin fixes (ENHANCED)
- `.env` - Environment variables for SQLx compilation (CREATED)
- `src-tauri/migrations/001_initial_schema.sql` - SQLite database schema (VERIFIED)
- `src-tauri/build.rs` - Build script for Tauri (CREATED)
- `package.json` - Node.js dependencies and scripts with Tauri integration (MODIFIED)
- `src/App.tsx` - Main React application component (CREATED)
- `index.html` - HTML entry point (CREATED)
- `vite.config.ts` - Vite configuration (CREATED)
- `tsconfig.json` - TypeScript configuration (CREATED)
- `src-tauri/src/llm/mod.rs` - LLM integration module with provider abstractions (ENHANCED)
- `src-tauri/src/llm/providers.rs` - LLM provider trait with complete interface definitions (ENHANCED)
- `src-tauri/src/llm/manager.rs` - LLM manager for request routing, retry logic, and cost tracking (ENHANCED)
- `src-tauri/src/llm/ollama.rs` - Ollama provider implementation with enhanced capabilities (ENHANCED)
- `src-tauri/src/llm/openai.rs` - OpenAI provider implementation with full trait support (ENHANCED)
- `src-tauri/src/llm/claude.rs` - Claude provider implementation with educational focus (ENHANCED)
- `src-tauri/src/llm/gemini.rs` - Gemini provider implementation with cost optimization (ENHANCED)
- `src-tauri/src/llm/secure_storage.rs` - Secure API key storage with educational recommendations (ENHANCED)
- `src-tauri/src/llm/factory.rs` - LLM provider factory for dynamic instantiation (CREATED)
- `src-tauri/src/llm/routing.rs` - Request routing and load balancing (CREATED)
- `src-tauri/src/llm/rate_limiter.rs` - Rate limiting for API requests (CREATED)
- `src-tauri/src/llm/offline.rs` - Offline capability detection and embedded LLM support (CREATED)
- `src-tauri/src/database.rs` - SQLite database operations with runtime queries (ENHANCED)
- `src-tauri/src/content/mod.rs` - Content generation engine module (ENHANCED)
- `src-tauri/src/content/generator.rs` - Core content generation logic
- `src-tauri/src/content/templates.rs` - Template management and processing
- `src-tauri/src/content/workflow.rs` - Step-based workflow execution engine (CREATED)
- `src-tauri/src/content/workflow_steps.rs` - Concrete workflow step implementations (CREATED)
- `src-tauri/src/content/prompt_templates.rs` - Educational prompt template system with Handlebars (CREATED)
- `src-tauri/src/content/pedagogical.rs` - Pedagogical methodology framework with Gagne's Nine Events and Bloom's Taxonomy (CREATED)
- `src-tauri/src/content/module_generator.rs` - Content type selection and module organization system (CREATED)
- `src-tauri/src/content/learning_objectives.rs` - Learning objective generation with Bloom's Taxonomy and user verification workflow (CREATED)
- `src-tauri/src/content/context_manager.rs` - Context management for multi-step content generation with state persistence and error recovery (CREATED)
- `src-tauri/src/content/progress_tracker.rs` - Real-time progress tracking and user feedback system with milestone tracking (CREATED)
- `src-tauri/src/validation/mod.rs` - Validation framework module
- `src-tauri/src/validation/validators.rs` - Individual validator implementations
- `src-tauri/src/export/mod.rs` - Export system module
- `src-tauri/src/export/converters.rs` - Format conversion implementations
- `src-tauri/src/session/mod.rs` - Session management module
- `src-tauri/src/session/storage.rs` - SQLite database operations
- `src-tauri/Cargo.toml` - Rust dependencies and project configuration
- `src/App.tsx` - Main React application component
- `src/components/Wizard.tsx` - Wizard interface for basic users
- `src/components/ExpertMode.tsx` - Expert interface for power users
- `src/components/ContentPreview.tsx` - Live content preview component
- `src/components/ProgressIndicator.tsx` - Progress tracking during generation
- `src/hooks/useLLM.ts` - React hook for LLM operations
- `src/hooks/useSession.ts` - React hook for session management
- `src/types/index.ts` - TypeScript type definitions\n- `src/types/settings.ts` - Comprehensive settings and user profile type definitions (CREATED)
- `src/utils/validation.ts` - Frontend validation utilities\n- `src/utils/settingsStorage.ts` - Settings persistence and storage utilities with validation (CREATED)\n- `src/contexts/SettingsContext.tsx` - React context for settings state management with hooks (CREATED)\n- `src/components/SettingsPanel.tsx` - Settings UI panel with profile, defaults, and preferences tabs (CREATED)
- `src/styles/globals.css` - Global application styles
- `package.json` - Node.js dependencies and scripts
- `src-tauri/tauri.conf.json` - Tauri application configuration

### Notes

- Unit tests should be placed alongside code files (e.g., `generator.rs` and `generator_test.rs`)
- Use `cargo test` for Rust backend tests and `npm test` for frontend tests
- Tauri commands bridge Rust backend with TypeScript frontend
- SQLite database will be embedded for session storage

## Tasks

- [x] 1.0 Setup Tauri Project Foundation and Core Architecture
  - [x] 1.1 Initialize new Tauri project with React and TypeScript frontend
  - [x] 1.2 Configure Cargo.toml with required Rust dependencies (tokio, serde, sqlx, etc.)
  - [x] 1.3 Set up project structure with modules for llm, content, validation, export, session
  - [x] 1.4 Configure Tauri permissions and security settings for file operations
  - [x] 1.5 Set up SQLite database schema for session and configuration storage
  - [x] 1.6 Create basic Tauri commands for frontend-backend communication
  - [x] 1.7 Configure development environment with hot reload and debugging

- [x] 2.0 Implement LLM Integration with Progressive Complexity
  - [x] 2.1 Design LLM provider trait/interface for consistent API across providers
  - [x] 2.2 Implement local Ollama provider as the default simple option
  - [x] 2.3 Create LLM manager for request routing, retry logic, and cost tracking
  - [x] 2.4 Implement secure storage for API keys using Tauri's keyring integration
  - [x] 2.5 Add external provider support (OpenAI, Claude, Gemini) behind advanced settings
  - [x] 2.6 Implement token counting and cost calculation per provider
  - [x] 2.7 Create fallback mechanisms and error handling for provider failures
  - [x] 2.8 Add offline capability detection and basic embedded LLM option

- [x] 3.0 Build Content Generation Engine with Template System
  - [x] 3.1 Create content generation workflow engine with step-based execution
  - [x] 3.2 Implement prompt template system with variable substitution
  - [x] 3.3 Design educational content templates (slides, instructor notes, worksheets)
  - [x] 3.4 Create pedagogical methodology integration (Gagne's Nine Events, etc.)
  - [x] 3.5 Implement content type selection with optional module generation
  - [x] 3.6 Add learning objective generation and user verification workflow
  - [x] 3.7 Create context management for multi-step content generation
  - [x] 3.8 Implement progress tracking and user feedback during generation

- [ ] 4.0 Develop User Interface with Wizard and Expert Modes
  - [x] 4.1 Create main application layout with mode switching (Wizard/Expert)
  - [x] 4.2 Implement wizard interface with step-by-step guided content creation
  - [x] 4.3 Build expert mode interface with direct workflow control
  - [x] 4.4 Design content input forms with progressive disclosure of advanced options
  - [ ] 4.5 Enhanced Content Types & User Personalization
    - [x] 4.5.1 Implement basic settings storage and user profiles
    - [x] 4.5.2 Expand Quiz content type with multiple assessment options
    - [x] 4.5.3 Add automatic answer key and instructor guide generation
    - [x] 4.5.4 Implement teaching style detection and preferences
    - [x] 4.5.5 Create AI integration preference system
    - [x] 4.5.6 Add smart defaults with "Use Settings" functionality
    - [x] 4.5.7 Implement content-specific AI enhancement options
    - [x] 4.5.8 Create custom content type framework
    - [x] 4.5.9 Build advanced template editor for power users
    - [x] 4.5.10 Add settings persistence and cross-session learning
  - [x] 4.6 Create live content preview component with real-time updates
  - [x] 4.7 Implement progress indicators and status feedback during generation
  - [x] 4.8 Add settings panel with three-tier complexity (Essential/Enhanced/Advanced)
  - [x] 4.9 Create desktop layout optimization for various screen sizes
  - [x] 4.10 Connect UI to LLM backend for real content generation (bridge frontend to existing LLM infrastructure)

- [x] 5.0 Create Export System with Built-in Format Conversion
  - [x] 5.1 Implement Markdown export as the baseline format
  - [x] 5.2 Create built-in HTML conversion with professional templates
  - [x] 5.3 Add PDF generation using headless browser or PDF libraries
  - [x] 5.4 Implement basic PowerPoint (.pptx) export functionality
  - [x] 5.5 Design professional templates for educational content presentation
  - [x] 5.6 Add optional Quarto integration for advanced users
  - [x] 5.7 Create template customization with branding options (colors, logos)
  - [x] 5.8 Implement batch export for multiple content types

- [x] 6.0 Implement Validation and Quality Assurance Framework
  - [x] 6.1 Create validation plugin architecture with base validator trait
  - [x] 6.2 Implement readability validator with configurable thresholds
  - [x] 6.3 Add structure validator for educational content organization
  - [x] 6.4 Create content alignment validator (worksheets match lectures)
  - [x] 6.5 Implement automatic remediation suggestions with user approval workflow
  - [x] 6.6 Add validation configuration with smart defaults for basic users
  - [x] 6.7 Create clear, non-technical feedback system for validation results
  - [x] 6.8 Implement "dry run" mode for reviewing changes before application

- [ ] 7.0 Add Session Management and File Operations
  - [x] 7.1 Implement session creation, saving, and loading functionality
  - [x] 7.2 Create file management with simple save/export operations
  - [x] 7.3 Add session history and project organization features
  - [x] 7.4 Implement automatic session backup and recovery
  - [x] 7.5 Create import functionality for existing PowerPoint and Word files
  - [x] 7.6 Add optional Git integration detection and basic version control
  - [ ] 7.7 Implement data export for external sharing and backup
  - [ ] 7.8 Create cleanup and maintenance tools for session data