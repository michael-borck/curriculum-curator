# Interactive Mode Guide

The Curriculum Curator includes a fully interactive mode that provides a menu-driven interface for all operations. This guide explains how to use the interactive mode.

## Getting Started

To launch the interactive mode, use the `interactive` command from the CLI:

```bash
curator interactive
```

This launches a menu interface that serves as a central hub for all Curriculum Curator operations.

## Main Menu

The interactive mode presents a main menu with the following options:

1. **Run a Workflow** - Select and run an existing workflow
2. **Build/Edit Workflow** - Create or modify workflow configurations
3. **Edit Prompts** - Create or edit prompt templates
4. **Initialize Project** - Set up a new project with default configuration
5. **Exit** - Exit interactive mode

Each option leads to a more specific set of menus tailored to that function.

## Running Workflows

Selecting "Run a Workflow" will:

1. Display a list of available workflows from both the configuration file and predefined workflows
2. Let you select a workflow to run
3. Prompt for any variables needed by the workflow
4. Execute the workflow and display the results
5. Show token usage statistics if available

This provides a guided alternative to the `curator run` command.

## Building/Editing Workflows

Choosing "Build/Edit Workflow" will:

1. Prompt for the output file path to save the workflow
2. Ask if you want to start from an existing workflow
3. Launch the interactive workflow builder

This option provides the same functionality as the `curator build-workflow` command. See the [Workflow Builder Guide](workflow-builder.md) for details on using the workflow builder.

## Editing Prompts

The "Edit Prompts" option will:

1. Ask if you want to edit a specific prompt file
2. Launch the interactive prompt editor

This provides the same functionality as the `curator edit-prompt` command. See the [Prompt Editor Guide](prompt-editor.md) for details on using the prompt editor.

## Initializing a Project

Selecting "Initialize Project" will guide you through:

1. Specifying a directory to initialize (defaults to the current directory)
2. Creating the necessary directory structure
3. Creating a default configuration file
4. Optionally installing default prompt templates

This provides an interactive alternative to the `curator init` command.

## Configuration

The interactive mode uses the specified configuration file (default: `config.yaml`) to determine:

- Available workflows
- Prompt directory location
- LLM providers and credentials

If the configuration file is not found, some functionality will be limited, but the system will offer to initialize a new project for you.

## Working Without Configuration

If you start interactive mode without an existing configuration file, you'll still be able to:

1. Initialize a new project
2. Create a default configuration
3. Install prompt templates

Other operations like running workflows will prompt you to initialize the project first.

## Benefits of Interactive Mode

Interactive mode offers several advantages over direct command usage:

1. **No Command Memorization** - You don't need to remember specific commands or parameters
2. **Discoverability** - All available options are presented in menus
3. **Guided Input** - Step-by-step prompts ensure all necessary inputs are provided
4. **Unified Interface** - One entry point for all operations
5. **Error Prevention** - Validation and confirmation prompts prevent common mistakes

## Use Cases

Interactive mode is especially useful for:

- **New Users** getting familiar with Curriculum Curator
- **Occasional Users** who don't remember specific commands
- **Educational Settings** where users may not be comfortable with command lines
- **Quick Exploration** of system capabilities

Advanced users may still prefer direct command usage for scripting and automation.

## Next Steps

After using interactive mode to set up your project, you may want to explore:

1. Creating a comprehensive set of prompts for your curriculum
2. Building workflows that connect multiple prompts together
3. Running workflows to generate educational content
4. Customizing prompt templates to suit your specific needs

For more detailed information on specific features, see the respective guides:
- [Workflow Builder Guide](workflow-builder.md)
- [Prompt Editor Guide](prompt-editor.md)
- [MVP Workflow Guide](mvp-workflow.md)
