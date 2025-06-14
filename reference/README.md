# Reference Materials from Python/Electron Implementation

This directory contains extracted knowledge and reference materials from the original Python/Electron implementation of Curriculum Curator. These materials inform the new Tauri implementation while preserving valuable architectural insights and lessons learned.

## Directory Structure

### `/docs/`
- `original-readme.md` - Original project README
- `design.md` - Comprehensive system design document
- `adr/` - Architecture Decision Records showing evolution of thinking

### `/prompt-templates/`
- `prompts/` - Complete collection of working prompt templates
  - `assessment/` - Assessment and quiz generation prompts
  - `course/` - Course overview and structure prompts
  - `instructor/` - Instructor guide and teaching note prompts
  - `lecture/` - Lecture content generation prompts
  - `module/` - Module outline and organization prompts
  - `worksheet/` - Activity and worksheet prompts

### `/config-examples/`
- `original-config.yaml` - Full system configuration example
- `minimal_module.yaml` - Working workflow configuration

### Knowledge Extraction Documents

#### `architecture-insights.md`
**Key architectural patterns and design decisions that worked well:**
- Plugin-based validation/remediation system design
- Workflow engine architecture patterns
- LLM provider abstraction strategies
- Prompt registry design principles
- Anti-patterns and lessons learned
- Technology mapping recommendations for Tauri

#### `validation-plugins-design.md`
**Comprehensive guide to the validation and remediation plugin system:**
- Base validator and remediator interfaces
- Implemented validator types (similarity, structure, readability)
- Remediation strategies and algorithms
- Configuration-driven plugin selection
- Manager coordination patterns
- Tauri implementation strategy
- Extension points for custom plugins

#### `workflow-patterns.md`
**Successful workflow configuration and execution patterns:**
- YAML workflow definition structures
- Step types and their use cases (prompt, validation, remediation, output)
- Context management and variable flow
- Advanced patterns (conditional, parallel, error recovery)
- Configuration inheritance and templating
- Session and state management
- Performance optimization strategies
- Tauri command mapping approaches

#### `llm-integration-patterns.md`
**Multi-provider LLM integration architecture:**
- Provider abstraction and configuration
- Model alias system for user experience
- Async request handling with retry logic
- Cost tracking and usage reporting
- Environment variable resolution for API keys
- Context window management
- Provider fallback strategies
- Tauri implementation patterns

#### `lessons-learned.md`
**Critical insights from the implementation experience:**
- Major successes (plugin architecture, workflow flexibility)
- Major challenges (scope creep, performance issues)
- User experience insights and preferences
- Technical architecture lessons
- Performance and resource usage findings
- Development process insights
- Strategic recommendations for Tauri implementation

## How to Use These Materials

### For PRD Creation
1. Review `lessons-learned.md` for scope and user requirements insights
2. Extract user stories and requirements from the design documents
3. Use architectural insights to inform technical requirements
4. Reference config examples for feature specifications

### For Architecture Design
1. Study `architecture-insights.md` for proven patterns
2. Adapt `validation-plugins-design.md` concepts for Tauri
3. Reference `workflow-patterns.md` for workflow engine design
4. Use `llm-integration-patterns.md` for provider integration

### For Implementation
1. Reference prompt templates as high-value assets to preserve
2. Use configuration examples as starting points
3. Adapt validation and remediation concepts to TypeScript/Rust
4. Follow workflow patterns for step execution design

## Key Insights for Tauri Implementation

### Preserve These Successful Patterns
- **Plugin architecture** for validation and remediation
- **YAML-driven workflows** with step-based execution
- **Multi-provider LLM integration** with cost tracking
- **Filesystem-based prompts** with YAML front matter
- **Context management** across workflow steps

### Avoid These Pitfalls
- **Scope creep** - Focus on weekly content generation
- **Multiple interfaces** - Desktop-first from the start
- **Over-engineering** - Simple, guided workflows preferred
- **Complex configuration** - Hide complexity behind presets
- **Heavy runtimes** - Leverage Rust performance benefits

### Technology Mapping
- **SQLite** instead of filesystem for session management
- **Tauri commands** instead of REST API for workflow execution
- **Native TypeScript/Rust** instead of Python/Electron stack
- **Built-in Tauri capabilities** instead of external dependencies

## Archive Reference

The complete original implementation is preserved in the `archive/python-electron-version` branch for detailed code reference if needed. However, these extracted knowledge documents should provide sufficient guidance for the Tauri implementation without requiring direct code copying.

This reference collection represents the distilled wisdom from a comprehensive implementation effort and should inform architectural decisions while avoiding the pitfalls discovered during the original development process.