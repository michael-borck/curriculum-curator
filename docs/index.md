# Curriculum Curator

An educational content workflow orchestration tool designed to streamline the creation of comprehensive curriculum materials through Large Language Model (LLM) integration.

<div class="grid cards" markdown>

- :material-playlist-plus: **Workflow-driven content generation**
    
    Create complete educational modules using configurable, automated workflows.

- :material-chat-processing: **Prompt-centric approach**
    
    All content is derived from well-designed prompts managed within the system.

- :material-check-all: **Content validation and remediation**
    
    Ensure quality through automated validation and remediation steps.

- :material-console: **Interactive interfaces**
    
    Build workflows and edit prompts with menu-driven interfaces.

</div>

## Features

- **Prompt Registry**: Manage a collection of prompts with metadata using YAML front matter
- **LLM Integration**: Support for multiple providers (Anthropic, OpenAI, Ollama, Groq, Gemini) via LiteLLM
- **Content Transformation**: Parse and structure raw LLM outputs in various formats
- **Workflow Engine**: Orchestrate the sequence of content generation, validation, and remediation steps
- **Interactive Mode**: Complete menu-driven interface for all operations
- **Interactive Workflow Builder**: Create and edit workflows through a menu-driven interface
- **Interactive Prompt Editor**: Create and edit prompts with templates and front matter validation
- **Validation Framework**: Ensure content quality and consistency through a suite of validators
- **Multiple Output Formats**: Generate HTML, PDF, DOCX, and presentation slide formats
- **Cost Tracking**: Monitor token usage and associated costs
- **Session Management**: Save, resume, and analyze workflow sessions

## Installation

```bash
pip install curriculum-curator
```

## Quick Start

```bash
# Initialize a new project with example prompts
curator init

# Run the minimal educational module workflow
curator run minimal_educational_module \
  --var course_title="Introduction to Python Programming" \
  --var course_slug="intro-python" \
  --var module_id="module1" \
  --var num_modules=4 \
  --var "learning_objectives=Understand Python basics;Write simple programs"

# Launch the interactive mode
curator interactive
```

## Documentation

- [Getting Started](getting-started/installation.md): Installation and quick start guide
- [User Guides](guides/interactive-mode.md): Detailed guides for using the various features
- [Concepts](concepts/architecture.md): Learn about the core concepts and architecture
- [API Reference](api/overview.md): Detailed API documentation
- [Development](development/contributing.md): Contributing guidelines and development process
