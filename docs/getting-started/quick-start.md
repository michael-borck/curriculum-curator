# Quick Start Guide

This guide will help you get up and running with Curriculum Curator in just a few minutes. We'll walk through initializing a project, running a simple workflow, and exploring the interactive interface.

## Initialize a Project

After [installing Curriculum Curator](installation.md), the first step is to initialize a project:

```bash
curator init
```

This will create a basic directory structure in your current directory, including:

- `prompts/` - Directory for prompt templates
- `output/` - Directory for generated content
- `config.yaml` - Default configuration file

## Configure LLM Providers

Edit the `config.yaml` file to add your API keys for the LLM providers you want to use. At minimum, you'll need one provider configured:

```yaml
# LLM Configuration
llm:
  default:
    type: openai
    model: gpt-4-turbo
    # Uncomment and add your API key if not set in environment
    # api_key: your-api-key-here
```

You can either add your API key directly in the config file, or set it as an environment variable (recommended):

```bash
export OPENAI_API_KEY=your-api-key-here
```

## Run a Built-in Workflow

Curriculum Curator comes with a few built-in workflows. Let's try the `minimal_educational_module` workflow:

```bash
curator run minimal_educational_module \
  --var course_title="Introduction to Python Programming" \
  --var course_slug="intro-python" \
  --var module_id="module1" \
  --var num_modules=4 \
  --var "learning_objectives=Understand Python basics;Write simple programs"
```

This will:
1. Generate a course overview
2. Create a module outline
3. Produce lecture content for the module
4. Generate a worksheet with practice activities
5. Create an assessment with various question types
6. Build an instructor guide with teaching suggestions

The output files will be saved to the `output/` directory.

## Using the Interactive Mode

For a more user-friendly experience, try the interactive mode:

```bash
curator interactive
```

This launches a menu-driven interface that provides access to all Curriculum Curator functionality, including:

- Running workflows
- Building and editing workflows
- Editing prompts
- Initializing projects

## Exploring Available Workflows

To see which workflows are available:

```bash
curator list-workflows
```

This will show both built-in workflows and any custom workflows defined in your configuration.

## Next Steps

Now that you've got the basics, you might want to explore:

- [How to use the interactive mode](../guides/interactive-mode.md) for a more guided experience
- [Creating workflows with the workflow builder](../guides/workflow-builder.md)
- [Editing and creating prompts](../guides/prompt-editor.md)
- [Understanding the MVP workflow](../guides/mvp-workflow.md)
- [Exploring all CLI commands](../guides/cli-reference.md)