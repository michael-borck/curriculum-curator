# Prompt Editor Guide

The Curriculum Curator includes an interactive prompt editor to help you create and edit prompt templates with proper front matter. This guide explains how to use the prompt editor command.

## Getting Started

To launch the prompt editor, use the `edit-prompt` command from the CLI:

```bash
# Start the prompt editor
curator edit-prompt

# Edit a specific prompt directly
curator edit-prompt course/overview.txt
```

## Using the Interactive Interface

The prompt editor provides a menu-driven interface to guide you through creating and editing prompts:

1. **Main Menu** - Navigate to different editor functions
2. **List and Edit** - Browse and select existing prompts to edit
3. **Create New** - Create a new prompt using a template
4. **Install Templates** - Install default prompt templates for different content types
5. **System Editor** - Your preferred text editor (via EDITOR environment variable) will be used for editing prompts

### Listing and Editing Prompts

Selecting "List and edit existing prompts" from the main menu shows all available prompts in the prompt directory, including metadata from the YAML front matter like title and description.

### Creating New Prompts

When creating a new prompt, the editor offers templates for different content types:

1. Course Overview
2. Module Outline
3. Lecture Content
4. Assessment Questions
5. Custom

Each template includes appropriate front matter with:
- Title
- Tags
- Description
- Variable placeholders

### Installing Default Templates

The "Install default templates" option creates all standard templates in the prompt directory, organized in subdirectories by content type:

- `course/overview.txt`
- `module/outline.txt`
- `lecture/content.txt`
- `assessment/questions.txt`

### Front Matter Validation

After editing a prompt, the editor validates the front matter to ensure it includes required fields like title and description. If fields are missing, it will display a warning.

## Front Matter Structure

Prompts in Curriculum Curator use YAML front matter to provide metadata. A typical front matter section looks like:

```yaml
---
title: Course Overview
tags: [course, overview]
description: Generate a course overview with objectives, topics, and prerequisites
variables:
  - course_title
  - target_audience
---
```

The front matter provides:
- **title**: Title of the prompt (required)
- **tags**: Tags for categorizing prompts
- **description**: Brief description of what the prompt does (required)
- **variables**: List of variables expected in the prompt

## Default Prompt Structure

Each prompt follows a standard structure:

1. **YAML Front Matter** - Metadata about the prompt
2. **System Message** - Instructions for the LLM about its role (e.g., "You are an expert curriculum designer.")
3. **Task Description** - Clear description of what to generate
4. **Outline/Requirements** - Structured list of what to include
5. **Format Instructions** - How to format the output (usually markdown)

## Using Variables in Prompts

Variables are placeholders in prompts that get replaced with actual values when the workflow runs. They use double curly braces:

```
You are an expert curriculum designer. Your task is to create a comprehensive overview for a course titled "{{course_title}}".

The target audience for this course is {{target_audience}}.
```

## Best Practices

1. **Use Descriptive Titles** - Make prompt titles clear and specific
2. **Add Comprehensive Tags** - Tags help with filtering and organization
3. **List All Variables** - Include all variables in the front matter
4. **Structure Prompts Consistently** - Keep a consistent format across prompts
5. **Include Format Instructions** - Always specify how output should be formatted

## Example Workflow

Here's a typical workflow for creating a new prompt:

1. Launch the prompt editor: `curator edit-prompt`
2. Select "Create a new prompt" from the menu
3. Choose a template type (e.g., "course/overview")
4. Specify the prompt file path (e.g., "course/my-new-course.txt")
5. Edit the prompt in your system text editor
6. Save and close the editor
7. Review the front matter validation results

## Using the Prompt Editor with Workflow Builder

The prompt editor and workflow builder work together seamlessly:

1. Create prompts with the editor
2. Reference them in workflow configurations via the workflow builder
3. Run the workflow using the CLI

## Next Steps

After creating prompts with the editor, you can:

1. Build a workflow that uses your prompts
2. Test your prompts with different variables
3. Create additional prompts for other content types
4. Organize your prompts into a comprehensive curriculum structure

For a complete guide to building workflows, see the [Workflow Builder Guide](workflow-builder.md).