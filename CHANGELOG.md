# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.1] - 2025-05-04

### Fixed
- Fixed package structure issues with the output directory
- Fixed license format in pyproject.toml from table to string format
- Updated CI workflow to ensure proper directory structure

## [0.2.0] - 2025-05-04

### Added
- Interactive mode (`interactive` command) providing a complete menu-driven interface for all operations
- Interactive prompt editor (`edit-prompt` command) with templates and front matter validation
- Interactive workflow builder CLI command (`build-workflow`) for creating and editing workflow configurations
- New commands to list available validators (`list-validators`) and remediators (`list-remediators`)
- Default prompt templates for common educational content types
- Comprehensive documentation for all interactive features
- Support for loading existing workflows as a base for new workflows
- Real-time validation during workflow building and prompt editing

### Changed
- Updated package structure to include all submodules properly
- Improved README with all new interactive feature documentation
- Extended CLI reference documentation for all commands

### Fixed
- Package installation to include all necessary submodules

## [0.1.0] - 2025-04-20

### Added
- Initial release
- Prompt registry with YAML front matter
- LLM integration with Anthropic, OpenAI, Ollama, Groq, and Gemini
- Content transformation for various formats
- Workflow engine for orchestrating content generation
- Validation framework for quality assurance
- Multiple output format support
- Cost tracking and token usage monitoring
- Session management for saving and resuming workflows
- MVP workflow for educational module generation