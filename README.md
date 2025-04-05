# Curriculum Curator

An educational content workflow orchestration tool designed to streamline the creation of comprehensive curriculum materials through Large Language Model (LLM) integration.

## Core Philosophy

Curriculum Curator is designed around two fundamental principles:

1. **Prompt-centric Content Generation**: All content is derived from well-designed prompts managed within the system.
2. **Workflow-driven Process**: Content creation follows configurable, automated educational workflows.

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

# Or run the standard course generation workflow
curator run standard_course --var course_title="Introduction to Python Programming"

# List available prompts
curator list-prompts

# List available workflows
curator list-workflows

# Create a new workflow with the interactive builder
curator build-workflow my-workflow.yaml

# Edit prompts interactively with templates
curator edit-prompt

# Launch the fully interactive mode for all operations
curator interactive

# List available validators and remediators
curator list-validators
curator list-remediators
```

## MVP Workflow Ready!

We've completed our first MVP workflow that generates a complete educational module with:

- Course overview
- Module outline
- Lecture content with validation and remediation
- Worksheet with practice activities
- Assessment with various question types
- Instructor guide with teaching suggestions and answer keys

This workflow is fully configuration-driven and validates against a robust schema to catch errors early. See our guides for more details:

- [MVP Workflow Guide](docs/guides/mvp-workflow.md) - Details on using and extending the workflow
- [Workflow Validation Guide](docs/guides/workflow-validation.md) - How to validate workflow configurations
- [Workflow Builder Guide](docs/guides/workflow-builder.md) - How to use the interactive workflow builder

## Development

### Setting up the development environment

```bash
# Clone the repository
git clone https://github.com/teaching-repositories/curriculum-curator.git
cd curriculum-curator

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pip install pre-commit
pre-commit install
```

### Running tests

```bash
# Run all tests
pytest

# Run tests with coverage report
pytest --cov=curriculum_curator
```

## Documentation

For detailed documentation, visit the [Curriculum Curator Docs](https://example.com/docs).

## License

MIT License