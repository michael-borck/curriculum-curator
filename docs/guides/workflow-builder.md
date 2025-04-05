# Workflow Builder Guide

The Curriculum Curator includes an interactive workflow builder to help you create and edit workflow configurations without directly editing YAML files. This guide explains how to use the workflow builder command.

## Getting Started

To launch the workflow builder, use the `build-workflow` command from the CLI:

```bash
# Start with a fresh workflow
curator build-workflow my-workflow.yaml

# Start with an existing workflow as a base
curator build-workflow my-workflow.yaml --base existing-workflow.yaml
```

## Using the Interactive Interface

The workflow builder provides a menu-driven interface to guide you through creating your workflow configuration:

1. **Main Menu** - Navigate to different builder functions
2. **Workflow Metadata** - Set name and description
3. **Default Settings** - Configure defaults for all steps
4. **Steps Management** - Add, edit, remove, and reorder workflow steps
5. **Validation** - Validate your workflow before saving
6. **Save** - Write your workflow to a file

### Setting Workflow Metadata

Every workflow requires a name and description. You can set these by choosing option 1 from the main menu.

### Configuring Default Settings

Default settings apply to all steps in your workflow unless overridden at the step level. Common defaults include:

- `llm_model_alias` - Default LLM model to use
- `output_format` - Default format for generated content

### Adding Steps

The workflow builder supports the following step types:

1. **Prompt Steps** - Generate content using an LLM and a prompt template
2. **Validation Steps** - Check content quality using validators
3. **Remediation Steps** - Fix issues in content
4. **Output Steps** - Save content to files

Each step type has its own guided configuration process.

#### Prompt Steps

Prompt steps generate content using an LLM. When adding a prompt step, you'll need to:

1. Provide a unique name
2. Select a prompt template from available prompts or enter a custom path
3. Specify an output variable name to store generated content
4. Choose an output format (raw, json, list, html)
5. Optionally specify an LLM model alias

#### Validation Steps

Validation steps check content quality. When adding a validation step:

1. Provide a unique name
2. Specify the content variable to validate
3. Specify an output variable for validation issues
4. Select validators to apply from the available list

To see available validators, use:

```bash
curator list-validators
```

#### Remediation Steps

Remediation steps fix issues in content. When adding a remediation step:

1. Provide a unique name
2. Specify the content variable to remediate
3. Specify the variable containing validation issues
4. Specify an output variable for remediated content
5. Optionally specify a variable for remediation actions

To see available remediators, use:

```bash
curator list-remediators
```

#### Output Steps

Output steps save content to files. When adding an output step:

1. Provide a unique name
2. Specify an output directory path
3. Define mappings from variables to output filenames
4. Optionally specify output formats

### Editing and Reordering Steps

You can edit existing steps, remove steps, or change their order using the respective options in the main menu.

### Validating and Saving

Before saving, the workflow builder validates your configuration against the schema. If validation passes, your workflow is saved to the specified file. If there are issues, they will be displayed so you can fix them.

## Example Workflow

Here's an example of a simple workflow you might create with the builder:

1. **Prompt Step** - Generate course overview content
   - Name: `generate_overview`
   - Prompt: `course/overview.txt`
   - Output Variable: `course_overview`
   - Format: `raw`

2. **Validation Step** - Check content quality
   - Name: `validate_overview`
   - Content Variable: `course_overview`
   - Output Variable: `validation_issues`
   - Validators: `readability`, `structure`

3. **Remediation Step** - Fix any issues
   - Name: `fix_overview`
   - Content Variable: `course_overview`
   - Issues Variable: `validation_issues`
   - Output Variable: `fixed_overview`

4. **Output Step** - Save the content
   - Name: `save_overview`
   - Output Directory: `output/`
   - Output Mapping: `fixed_overview` → `course_overview.md`

## Best Practices

1. **Use Descriptive Names** - Give your steps clear, descriptive names.
2. **Variable Naming Conventions** - Establish a convention for variable names (e.g., `original_content`, `validated_content`, etc.).
3. **Review Available Components** - Use the `list-prompts`, `list-validators`, and `list-remediators` commands to see what's available.
4. **Start Simple** - Begin with a minimal workflow and add complexity as needed.
5. **Test Incrementally** - Save and test your workflow after adding each major step.

## Troubleshooting

If you encounter issues with the workflow builder:

- Ensure your configuration file is properly set up.
- Check that prompt templates, validators, and remediators are available in the system.
- Review the validation errors if your workflow fails validation.
- For command syntax help, use `curator build-workflow --help`.

## Next Steps

After creating a workflow with the builder, you can:

1. Run the workflow with `curator run <workflow-name>`
2. Further customize it manually if needed
3. Use it as a base for more complex workflows