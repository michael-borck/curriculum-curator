# Workflow Configuration Validation

Curriculum Curator provides a robust validation system for workflow configurations to catch errors early in the development process.

## Overview

The validation system uses Pydantic models to enforce schema validation for workflow configurations. This ensures that:

1. All required fields are present
2. Field values have the correct types
3. Step-specific fields are used correctly
4. Defaults are applied properly
5. Detailed error messages are provided when validation fails

## Benefits

Using the validation system provides several benefits:

1. **Early Error Detection**: Configuration errors are caught before execution begins
2. **Clear Error Messages**: Detailed error messages identify exactly what's wrong
3. **Better Developer Experience**: Autocomplete and type hints help when writing configurations
4. **Safer Production Deployments**: Validated configurations are less likely to fail at runtime
5. **Reduced LLM Costs**: Catching errors early prevents unnecessary LLM calls for invalid workflows

## Validating Workflows

### Using the Validation Tool

Curriculum Curator includes a validation tool to check workflow configurations:

```bash
# Validate a single workflow file
python -m curriculum_curator.tools.validate_workflow examples/workflows/minimal_module.yaml

# Validate all discovered workflows
python -m curriculum_curator.tools.validate_workflow --all
```

### Programmatic Validation

You can also validate workflows programmatically:

```python
from curriculum_curator.workflow.workflows import load_workflow_config

# Load and validate a workflow
workflow_config = load_workflow_config("examples/workflows/minimal_module.yaml")

if workflow_config:
    print(f"Workflow '{workflow_config.name}' is valid")
else:
    print("Workflow validation failed")
```

## Configuration Schema

The workflow configuration schema is defined using Pydantic models:

### Top-Level Structure

```yaml
name: "workflow_name"  # Required: Unique identifier for the workflow
description: "Description"  # Required: Human-readable description of the workflow

defaults:  # Optional: Defaults to apply to all steps unless overridden
  llm_model_alias: "default_smart"  # Default LLM model for prompt steps
  output_format: "raw"  # Default output format for prompt steps
  validators: ["readability", "structure"]  # Default validators for validation steps

steps:  # Required: List of steps to execute
  - name: "step_name"  # Each step must have a name and type
    type: "prompt"  # Type determines what other fields are required
    # ...additional fields based on step type
```

### Step Types and Required Fields

#### Prompt Step

```yaml
- name: "generate_content"
  type: "prompt"
  prompt: "path/to/prompt.txt"  # Required: Path to prompt template
  output_variable: "result_variable"  # Required: Where to store result
  llm_model_alias: "default_smart"  # Optional: Override default
  output_format: "raw"  # Optional: Override default (raw, json, list, html)
  transformation_rules: {}  # Optional: Additional transformation rules
```

#### Validation Step

```yaml
- name: "validate_content"
  type: "validation"
  content_variable: "content_to_validate"  # Required: Content to validate
  output_variable: "validation_issues"  # Required: Where to store issues
  validators: ["readability", "structure"]  # Required: Validators to apply
  validation_config:  # Optional: Additional validator configuration
    similarity:
      threshold: 0.8
```

#### Remediation Step

```yaml
- name: "fix_issues"
  type: "remediation"
  content_variable: "content_to_fix"  # Required: Content to fix
  issues_variable: "validation_issues"  # Required: Issues to fix
  output_variable: "fixed_content"  # Required: Where to store fixed content
  actions_variable: "remediation_actions"  # Optional: Store remediation actions
  remediation_config: {}  # Optional: Additional remediator configuration
```

#### Output Step

```yaml
- name: "generate_files"
  type: "output"
  output_mapping:  # Required: Maps variables to file names
    variable_name: "output_file.md"
  output_dir: "output/path"  # Required: Output directory
  output_variable: "output_files"  # Optional: Store output file paths
```

## Common Validation Errors

Here are some common validation errors and how to fix them:

### Missing Required Fields

```
validation error: field required (type=value_error.missing)
```

This error means a required field is missing. Check the schema to identify which field is required for the step type.

### Type Errors

```
validation error: value is not a valid dict (type=type_error.dict)
```

This error means a field has the wrong type. Make sure your field values match the expected types in the schema.

### Invalid Enum Values

```
validation error: value is not a valid enumeration member (type=type_error.enum)
```

This error means you're using an invalid value for a field with limited options (like output_format or step type).

### Unknown Fields

```
validation error: extra fields not permitted (type=value_error.extra)
```

This error means you're using fields that aren't defined in the schema. Check for typos or remove the unknown fields.

## Extension and Customization

The validation system is designed to be extended as new step types are added to the workflow engine. When adding a new step type:

1. Define a new Pydantic model for the step type in `models.py`
2. Add the new model to the `StepConfig` union type
3. Update the `parse_steps` method to handle the new step type
4. Update the workflow engine to create and execute the new step type

This ensures that validation remains robust as the system evolves.