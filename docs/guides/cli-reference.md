# Curriculum Curator CLI Reference

This document provides a reference for all available Curriculum Curator command-line interface (CLI) commands and options.

## Command Overview

| Command | Description |
|---------|-------------|
| `interactive` | Launch interactive mode with a menu of common operations |
| `run` | Run a specified workflow |
| `resume` | Resume a previously interrupted workflow session |
| `list-workflows` | List all available workflows |
| `list-prompts` | List available prompts, optionally filtered by tag |
| `list-validators` | List available content validators |
| `list-remediators` | List available content remediators |
| `build-workflow` | Interactive workflow builder for creating/editing workflow configurations |
| `edit-prompt` | Interactive prompt editor for creating/editing prompt templates |
| `init` | Initialize a new project with example configuration and prompts |

## General Options

These options are available in most commands:

| Option | Description |
|--------|-------------|
| `--config`, `-c` | Path to configuration file (default: config.yaml) |
| `--help` | Show help message and exit |

## Command Details

### Run a Workflow

Run a specified workflow with optional variables.

```bash
curator run [OPTIONS] WORKFLOW
```

**Arguments:**
- `WORKFLOW`: Name of the workflow to run (required)

**Options:**
- `--var`, `-v`: Variables in key=value format. Can be used multiple times
- `--session-id`: Specify a session ID to use or resume
- `--config`, `-c`: Path to configuration file (default: config.yaml)
- `--output-json`, `-j`: Output result as JSON instead of rich text format

**Examples:**
```bash
# Run a workflow with variables
curator run minimal_educational_module --var course_title="Python Programming" --var module_id="1"

# Run with custom configuration file
curator run standard_course --config custom_config.yaml

# Run with JSON output
curator run minimal_educational_module --output-json > output.json
```

### Resume a Workflow

Resume a previously interrupted workflow session.

```bash
curator resume [OPTIONS] SESSION_ID
```

**Arguments:**
- `SESSION_ID`: The Session ID of the workflow to resume (required)

**Options:**
- `--from-step`: Specific step name to resume from
- `--config`, `-c`: Path to configuration file (default: config.yaml)
- `--output-json`, `-j`: Output result as JSON

**Examples:**
```bash
# Resume a workflow session
curator resume 2023-04-05-12345-abc123

# Resume from a specific step
curator resume 2023-04-05-12345-abc123 --from-step validate_content
```

### List Workflows

List all available workflows defined in the configuration file and predefined workflows.

```bash
curator list-workflows [OPTIONS]
```

**Options:**
- `--config`, `-c`: Path to configuration file (default: config.yaml)

**Example:**
```bash
curator list-workflows
```

### List Prompts

List available prompts, optionally filtered by tag.

```bash
curator list-prompts [OPTIONS]
```

**Options:**
- `--tag`, `-t`: Filter prompts by tag specified in YAML front matter
- `--config`, `-c`: Path to configuration file (default: config.yaml)

**Examples:**
```bash
# List all prompts
curator list-prompts

# List prompts with a specific tag
curator list-prompts --tag course
```

### List Validators

List available content validators that can be used in workflows.

```bash
curator list-validators
```

**Example:**
```bash
curator list-validators
```

### List Remediators

List available content remediators that can be used in workflows.

```bash
curator list-remediators
```

**Example:**
```bash
curator list-remediators
```

### Build Workflow

Interactive workflow builder to create or edit workflow configurations.

```bash
curator build-workflow [OPTIONS] OUTPUT_FILE
```

**Arguments:**
- `OUTPUT_FILE`: Path to save the workflow configuration (required)

**Options:**
- `--base`, `-b`: Base workflow to start from
- `--config`, `-c`: Path to configuration file (default: config.yaml)

**Examples:**
```bash
# Create a new workflow from scratch
curator build-workflow my-workflow.yaml

# Create a workflow based on an existing one
curator build-workflow new-workflow.yaml --base existing-workflow.yaml
```

### Edit Prompts

Interactive editor for creating and editing prompt templates.

```bash
curator edit-prompt [OPTIONS] [PROMPT_PATH]
```

**Arguments:**
- `PROMPT_PATH`: Path to the prompt file to edit (optional)

**Options:**
- `--config`, `-c`: Path to configuration file (default: config.yaml)

**Examples:**
```bash
# Launch prompt editor menu
curator edit-prompt

# Edit a specific prompt
curator edit-prompt course/overview.txt
```

### Interactive Mode

Launch interactive mode with a menu of common operations.

```bash
curator interactive [OPTIONS]
```

**Options:**
- `--config`, `-c`: Path to configuration file (default: config.yaml)

**Example:**
```bash
curator interactive
```

### Initialize Project

Initialize a new project with example prompts and configuration.

```bash
curator init [OPTIONS] [OUTPUT_DIR]
```

**Arguments:**
- `OUTPUT_DIR`: Directory to initialize with example prompts and configuration (default: current directory)

**Example:**
```bash
# Initialize in current directory
curator init

# Initialize in a specific directory
curator init my-project-dir
```

## Environment Variables

The Curriculum Curator CLI respects the following environment variables:

- `OPENAI_API_KEY`: API key for OpenAI
- `ANTHROPIC_API_KEY`: API key for Anthropic
- `GROQ_API_KEY`: API key for Groq
- `GOOGLE_API_KEY`: API key for Google AI (Gemini)

You can set these in your environment or in the configuration file.

## Error Handling

When an error occurs, the CLI will:
1. Display an error message with details
2. Log additional information (if enabled)
3. Exit with a non-zero exit code

Example error handling:
```bash
# If a workflow is not found
curator run non_existent_workflow
# [bold red]Error running workflow 'non_existent_workflow':[/bold red] Workflow not found
```

## Logging

By default, logs are written to the console. You can configure logging behavior in the configuration file.

## Configuration File

The configuration file (default: `config.yaml`) defines:
- LLM providers and credentials
- Base paths for prompts and output
- Default settings for components
- Custom workflow definitions

See the [Configuration Guide](configuration.md) for detailed information on the configuration file format.

## Further Reading

- [Workflow Builder Guide](workflow-builder.md) - How to use the interactive workflow builder
- [MVP Workflow Guide](mvp-workflow.md) - Details on using the built-in workflows
- [Workflow Validation Guide](workflow-validation.md) - How to validate workflow configurations