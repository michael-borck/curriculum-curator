# Curriculum Curator Documentation

Welcome to the Curriculum Curator documentation. This tool helps educators create high-quality course materials using AI assistance while maintaining pedagogical best practices.

## Quick Links

- [Getting Started](guides/getting-started.md)
- [Architecture Overview](concepts/architecture.md)
- [API Reference](api/README.md)
- [Development Guide](../DEVELOPMENT_GUIDE.md)

## Documentation Structure

### [Architecture Decision Records (ADRs)](adr/)
Important architectural decisions and their rationale.

### [Concepts](concepts/)
- [Architecture Overview](concepts/architecture.md)
- [Teaching Philosophy System](concepts/teaching-philosophy.md)
- [Plugin System](concepts/plugin-system.md)
- [Content Generation Pipeline](concepts/content-generation.md)

### [API Documentation](api/)
- [Core API](api/core.md)
- [Plugin APIs](api/plugins.md)
- [Web Routes](api/routes.md)

### [Guides](guides/)
- [Getting Started](guides/getting-started.md)
- [Creating Custom Validators](guides/custom-validators.md)
- [Teaching Style Configuration](guides/teaching-styles.md)
- [Authentication & Security](guides/authentication-security.md)
- [Deployment Guide](guides/deployment.md)

### [Reference](reference/)
- [Configuration Options](reference/configuration.md)
- [Plugin Catalog](reference/plugin-catalog.md)
- [Teaching Styles Reference](reference/teaching-styles.md)

## Key Features

### 🎯 Teaching Philosophy Aware
- 9 different teaching styles supported
- Adaptive content generation based on pedagogical approach
- Teaching style detection questionnaire

### 🧙 Dual UI Modes
- **Wizard Mode**: Step-by-step guided creation for beginners
- **Expert Mode**: Power user interface with all options visible

### 🔌 Extensible Plugin System
- Custom validators for content quality checks
- Remediators for automatic content improvement
- Easy to add new plugins

### 📚 Comprehensive Course Management
- Multi-course support
- Week-by-week material organization
- Various content types (lectures, worksheets, quizzes, etc.)

### 🤖 LLM Integration
- Multiple provider support (planned)
- Teaching style-aware prompt generation
- Streaming responses for better UX

## Project Status

This is a FastHTML-based reimplementation of the Curriculum Curator, migrated from the original Tauri desktop application. The project aims to make course content creation more accessible through a web interface while maintaining the pedagogical awareness of the original.

## Contributing

See our [Contributing Guide](CONTRIBUTING.md) for information on how to contribute to the project.

## License

[License information]

## Support

[Support information]