# Development Guide

This guide covers the development environment setup, workflows, and current implementation status for Curriculum Curator.

**Last Updated:** 2025-01-19 - Phase 1 Progress: Added testing documentation and fixed console errors

## Development Environment

### Prerequisites

- Node.js 18+ with npm
- Rust 1.70+ with cargo
- System dependencies for Tauri (see [Tauri Prerequisites](https://tauri.app/v1/guides/getting-started/prerequisites))

### Quick Start

1. **Install dependencies:**
   ```bash
   npm install
   ```

2. **Start development server:**
   ```bash
   npm run dev
   ```

3. **For verbose debugging:**
   ```bash
   npm run tauri:dev:verbose
   ```

## Development Scripts

### Core Development
- `npm run dev` - Start Tauri development mode
- `npm run tauri:dev:verbose` - Start with debug logging
- `npm run frontend:dev` - Frontend only (Vite dev server)

### Code Quality
- `npm run dev:check` - Run all checks (TypeScript, ESLint, Rust)
- `npm run dev:format` - Format all code (ESLint + Rustfmt)
- `npm run type-check` - TypeScript type checking
- `npm run lint` / `npm run lint:fix` - ESLint linting

### Rust Backend
- `npm run rust:check` - Cargo check
- `npm run rust:test` - Run Rust tests
- `npm run rust:clippy` - Run Clippy linter
- `npm run rust:fmt` - Format Rust code

### Build & Clean
- `npm run build` - Production build
- `npm run tauri:build:debug` - Debug build
- `npm run tauri:clean` - Clean build artifacts

## Debugging

### VS Code Configuration

The project includes VS Code launch configurations:

1. **Tauri Development Debug** - Launch with debugging enabled
2. **Rust Backend Debug** - Debug the Rust backend with LLDB

### Environment Variables

Development environment variables are configured in `.env.development`:

```bash
# Enable debug features
VITE_DEBUG=true
RUST_BACKTRACE=1
RUST_LOG=curriculum_curator=debug,tauri=debug

# Development server settings
VITE_DEV_SERVER_PORT=5173
TAURI_DEV_WATCHER=true
TAURI_HOTRELOAD=true
```

### Logging

- **Frontend**: Use `console.log()` - logs appear in dev tools
- **Backend**: Use `tracing::debug!()`, `info!()`, etc.
- **Set log levels**: `RUST_LOG=curriculum_curator=debug,tauri=info`

## Hot Reload

The development environment supports hot reload for:

- **Frontend changes**: Vite handles React component updates
- **Backend changes**: Tauri automatically rebuilds and restarts
- **Configuration changes**: Restart required for tauri.conf.json

## Database Development

- **Location**: SQLite database in app data directory
- **Migrations**: Automatically applied on startup
- **Reset**: Delete the database file to reset schema

## LLM Development

### Local Development (Ollama)

1. **Install Ollama**: Follow [Ollama installation guide](https://ollama.ai)

2. **Pull a model**: 
   ```bash
   ollama pull llama3.2:3b
   ```

3. **Verify connection**:
   ```bash
   curl http://localhost:11434/api/tags
   ```

### External Providers

Configure API keys through the application UI or environment variables:

```bash
# In your shell or .env.local (not committed)
OPENAI_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here
GOOGLE_API_KEY=your_key_here
```

## Performance Tips

### Faster Development Builds

Use the optimized development profile:
```bash
cd src-tauri
cargo build --profile dev-opt
```

### Dependency Caching

- Rust dependencies are cached in `target/`
- Node dependencies are cached in `node_modules/`
- Don't commit these directories

## Common Issues

### Build Failures

1. **Rust compilation errors**: Run `npm run rust:check`
2. **TypeScript errors**: Run `npm run type-check`
3. **Missing dependencies**: Run `npm install`

### Runtime Issues

1. **Database errors**: Check SQLite file permissions
2. **LLM connection**: Verify Ollama is running on port 11434
3. **Frontend-backend communication**: Check Tauri command registration

### Hot Reload Not Working

1. Ensure you're using `npm run dev` (not `tauri dev` directly)
2. Check that port 5173 is not blocked
3. Restart the development server

## Testing

### Unit Tests

- **Rust**: `npm run rust:test`
- **Frontend**: Tests not yet configured

### Integration Tests

- **LLM providers**: Use the built-in test commands in the UI
- **Database**: Manual testing through the application

## Contributing

1. **Before committing**: Run `npm run dev:format && npm run dev:check`
2. **Commit style**: Use conventional commits
3. **Pull requests**: Include tests and documentation updates

## Architecture

```
curriculum-curator/
├── src/                    # React frontend
├── src-tauri/             # Rust backend
│   ├── src/
│   │   ├── llm/          # LLM integration
│   │   ├── content/      # Content generation
│   │   ├── session/      # Session management
│   │   ├── validation/   # Content validation
│   │   └── export/       # Export functionality
│   └── migrations/       # Database schema
├── .vscode/              # VS Code configuration
└── package.json          # Node.js configuration
```

For more detailed architecture information, see the individual module documentation in `src-tauri/src/`.

---

## 🚦 Implementation Status & Testing Guide

### Current Development Status

This application is a **sophisticated prototype** with mixed functionality. Some features are fully implemented while others are placeholder/stub implementations designed to support UI development and testing workflows.

### ✅ **Fully Functional Components**

#### Core Infrastructure
- **Database Operations** - SQLite with migrations, session storage works
- **Session Management** - Create, save, load sessions with real persistence  
- **Settings System** - User preferences, content defaults, UI preferences persist
- **File System Operations** - Basic read/write, directory management functional
- **UI Framework** - All React components, responsive design, navigation work

#### Working Integrations
- **Ollama LLM Provider** - Actual content generation if Ollama is running locally
- **PowerPoint Export** - Functional PPTX generation works
- **Basic Import/Export** - File operations with real backend support
- **Validation Framework** - Core validation system architecture in place

### ⚠️ **Partially Functional Components**

#### Content Generation Pipeline
- **UI Workflows** - Complete forms and interfaces ✅
- **Content Planning** - Mock data responses ❌  
- **Material Generation** - Works with Ollama, mock for others ⚠️
- **Quality Review** - Framework exists, limited implementation ⚠️

#### File Operations  
- **Session Backup/Restore** - UI functional, backend partially implemented ⚠️
- **Batch Export** - UI complete, backend stubs ❌
- **Git Integration** - Interface exists, functionality limited ❌

### ❌ **Placeholder/Non-Functional Components**

#### LLM Providers
- **OpenAI** - Stub implementation, returns errors
- **Claude** - Stub implementation, returns errors
- **Gemini** - Partial implementation, streaming not supported  
- **Multi-Provider Routing** - Architecture exists, logic incomplete

#### Advanced Features
- **Batch Content Generation** - UI only, no backend processing
- **Expert Mode Workflows** - Buttons render but don't execute steps
- **Advanced Export Formats** - Most formats are stubs (except PowerPoint)
- **Content Deduplication** - Returns hardcoded success
- **Storage Optimization** - Returns mock results
- **File System Auditing** - Placeholder implementation

### 🔍 **Key Placeholder Functions**

#### Rust Backend (`src-tauri/src/`)

```rust
// commands.rs - Always returns mock responses
test_llm_connection()  // Hardcoded true for Ollama, false for others
generate_content()     // Returns fake JSON content

// maintenance/service.rs - Storage operations return hardcoded values
calculate_total_storage_size()     // Returns Ok(0)
estimate_reclaimable_storage()     // Returns Ok(0)
optimize_storage()                 // "Not fully implemented" comment
deduplicate_content()              // "Not fully implemented" comment  
audit_file_system()                // "Not fully implemented" comment

// llm/providers - Most provider implementations incomplete
gemini::generate_stream()          // "Streaming not yet implemented"
openai::*                         // Most functions return errors
claude::*                         // Most functions return errors
```

#### TypeScript Frontend (`src/`)

```typescript
// utils/generationManager.ts - Mock content generation
getCurrentConfig()           // Returns null - "no config available"
getMockResponse()           // Provides hardcoded mock data when Tauri unavailable
executeFormattingStep()     // Just delays 3 seconds with no actual work
executePackagingStep()      // Just delays 2 seconds with no actual work

// components/ExpertMode.tsx - Non-functional workflows  
handleExport()              // Uses mock session ID
handleSaveSession()         // Uses mock session ID
// All "Run Step" buttons in workflow tab are placeholders

// components/BackupRecovery.tsx - Limited functionality
// Most backup operations use placeholder implementations
```

## 🧪 **Testing Workflows**

### Recommended Testing Scenarios

#### 1. UI/UX Testing (Fully Functional)
- ✅ Navigate through all application modes (Wizard, Expert)
- ✅ Test form inputs and validation  
- ✅ Verify settings persistence across sessions
- ✅ Test responsive design and layout switching
- ✅ Verify error handling and user feedback

#### 2. Basic Content Generation (Requires Ollama)
```bash
# Setup Ollama for testing
ollama serve
ollama pull llama3.2:3b  # or another model
```
- ✅ Test content generation through wizard mode
- ✅ Verify prompt handling and response processing
- ✅ Test session saving and loading

#### 3. Database Operations (Fully Functional)
- ✅ Create multiple sessions and verify persistence
- ✅ Test session metadata and content storage
- ✅ Verify database migrations work correctly
- ✅ Test data export and backup functionality

#### 4. File System Operations (Partially Functional)
- ✅ Test basic file import/export
- ⚠️ Test session backup (UI works, backend limited)
- ⚠️ Test various export formats (PowerPoint works, others limited)

### 🚫 **Known Non-Functional Areas**

Cannot currently test these features:
- Multi-LLM provider switching (only Ollama works)
- Batch content generation workflows  
- Expert mode step-by-step workflow execution
- Advanced maintenance operations
- Git integration features
- Advanced export format generation (except PowerPoint)
- Content optimization and deduplication

## 🗺️ **Development Roadmap**

### Phase 1: Core Functionality (High Priority)
1. **Complete LLM Provider Implementations**
   - Implement OpenAI integration
   - Complete Claude integration
   - Finish Gemini streaming support  
   - Add provider fallback logic

2. **Content Generation Pipeline**
   - Replace mock responses with real content generation
   - Implement content planning algorithms
   - Add quality review automation
   - Complete formatting and packaging steps

### Phase 2: Advanced Features (Medium Priority)
1. **Workflow Execution**
   - Implement Expert Mode step execution
   - Add workflow customization
   - Complete batch processing backend

2. **File Operations**
   - Complete all export format implementations
   - Enhance import capabilities
   - Implement robust backup/restore

### Phase 3: Optimization & Polish (Lower Priority)
1. **Maintenance Features**
   - Implement storage optimization
   - Add content deduplication
   - Complete file system auditing

2. **Advanced Integrations**
   - Complete Git integration
   - Add collaboration features
   - Implement advanced analytics

## 🏗️ **Architecture Notes**

### Strengths
- **Solid Foundation** - Database, session management, UI framework
- **Good Separation of Concerns** - Clear frontend/backend boundaries
- **Extensible Design** - Easy to add new providers and features
- **Type Safety** - Strong TypeScript and Rust type systems
- **Error Handling** - Comprehensive error management

### Areas for Improvement
- **Mock Data Dependencies** - Many features rely on placeholder responses
- **Provider Abstraction** - LLM provider interface needs completion
- **Workflow Engine** - Step execution logic needs implementation
- **Testing Coverage** - Unit tests for core functionality needed

## 🐛 **Troubleshooting**

### Placeholder vs Real Issues
- **Expected**: Mock responses in Expert mode workflows
- **Expected**: Limited LLM provider options (only Ollama fully works)
- **Expected**: Some export formats return placeholder content
- **Issue**: LLM Connection Failures - Ensure Ollama is running locally
- **Issue**: Database Errors - Check file permissions in app data directory
- **Issue**: Build Failures - Verify Rust and Node.js versions

### ✅ **Recent Fixes (Phase 1)**
- **Fixed**: Console errors for backup service - Registered Tauri commands
- **Added**: Comprehensive testing documentation (`TESTING.md`)
- **Added**: Test result tracking system (`TEST_RESULTS.md`)
- **Fixed**: BackupService initialization - Now uses real service instead of PhantomData

### Debug Mode
Set `TAURI_DEBUG=true` for additional logging and error details.

## 📝 **Contributing Guidelines**

When working on this codebase:

1. **Check this status section** before implementing features to avoid duplicating placeholder work
2. **Update placeholder status** when converting stubs to real implementations  
3. **Maintain backwards compatibility** with existing UI interfaces
4. **Add tests** for new functionality
5. **Update this document** when major features are completed

---

*This document will be updated as development progresses. Check git history for recent changes.*