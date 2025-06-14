# ADR 0003: Workflow Configuration Format

## Status

Accepted

## Context

The Curriculum Curator system relies on a workflow engine to orchestrate the generation, validation, remediation, and output of educational content. We need a standardized format for defining these workflows that is:

1. Human-readable and easy to edit
2. Extensible to accommodate future workflow patterns
3. Capable of being loaded dynamically at runtime
4. Provides defaults and overrides for common properties

## Decision

We will use YAML as the configuration format for workflow definitions with a standardized schema that supports defaults and step-specific overrides. Workflow definitions will be stored in standalone files that can be discovered at runtime.

### Schema

The workflow configuration format will follow this structure:

```yaml
# Top-level workflow definition
name: "workflow_name"  # Required: Unique identifier for the workflow (should follow snake_case)
description: "Workflow description"  # Required: Human-readable description of the workflow

# Optional global defaults that apply to all steps unless overridden
defaults:
  llm_model_alias: "default_smart"  # Default LLM model to use for all prompt steps
  output_format: "raw"  # Default output format for all prompt steps
  validators: ["readability", "structure"]  # Default validators for all validation steps
  remediators: ["format_corrector", "sentence_splitter"]  # Default remediators

# Required: List of steps defining the workflow execution
steps:
  # Each step defines an action in the workflow
  - name: "step_name"  # Required: Unique name for this step
    type: "prompt"  # Required: Step type (prompt, validation, remediation, output)
    # Additional parameters based on step type...
```

### Step Types and Parameters

#### Prompt Step
Used to generate content by executing a prompt with an LLM.

```yaml
- name: "generate_overview"
  type: "prompt"
  prompt: "course/overview.txt"  # Required: Path to the prompt template
  llm_model_alias: "default_smart"  # Optional: LLM model to use
  output_format: "raw"  # Optional: Format for output (raw, json, list, html)
  output_variable: "course_overview"  # Required: Variable to store the result
  transformation_rules: {}  # Optional: Special rules for content transformation
```

#### Validation Step
Used to validate content against a set of rules.

```yaml
- name: "validate_lecture"
  type: "validation"
  content_variable: "lecture_content"  # Required: Content to validate
  validators: ["readability", "structure"]  # Required: Validators to apply
  output_variable: "validation_issues"  # Required: Variable to store issues
  validation_config:  # Optional: Additional configuration for validators
    similarity:
      threshold: 0.8
    structure:
      required_sections: ["introduction", "conclusion"]
```

#### Remediation Step
Used to fix issues found during validation.

```yaml
- name: "remediate_lecture"
  type: "remediation"
  content_variable: "lecture_content"  # Required: Content to remediate
  issues_variable: "validation_issues"  # Required: Issues to fix
  output_variable: "remediated_lecture"  # Required: Variable to store fixed content
  actions_variable: "remediation_actions"  # Optional: Variable to store actions taken
  remediation_config:  # Optional: Additional configuration for remediators
    format_corrector:
      aggressive: true
```

#### Output Step
Used to generate output files from content.

```yaml
- name: "generate_outputs"
  type: "output"
  output_mapping:  # Required: Maps variables to output filenames
    course_overview: "overview.md"
    remediated_lecture: "lecture.md"
  output_dir: "output/{course_slug}/{module_id}"  # Required: Output directory
  output_variable: "output_files"  # Optional: Variable to store output file paths
```

### Future Step Types (Planned)

#### Conditional Step
Executes steps conditionally based on a condition.

```yaml
- name: "conditional_step"
  type: "conditional"
  condition: "validation_issues|length > 0"  # Required: Condition to evaluate
  if_steps:  # Required: Steps to execute if condition is true
    - name: "remediate_content"
      type: "remediation"
      # ...
  else_steps:  # Optional: Steps to execute if condition is false
    - name: "skip_remediation"
      type: "prompt"
      # ...
```

#### Loop Step
Executes steps repeatedly for each item in a collection.

```yaml
- name: "process_modules"
  type: "loop"
  items_variable: "modules"  # Required: Variable containing items to iterate over
  item_variable: "current_module"  # Required: Variable to store current item
  steps:  # Required: Steps to execute for each item
    - name: "process_module"
      type: "prompt"
      # ...
```

#### Parallel Step
Executes steps in parallel.

```yaml
- name: "parallel_processing"
  type: "parallel"
  max_concurrency: 3  # Optional: Maximum number of concurrent tasks
  steps:  # Required: Steps to execute in parallel
    - name: "task1"
      type: "prompt"
      # ...
    - name: "task2"
      type: "prompt"
      # ...
```

## Discovery Mechanism

Workflow configurations will be discovered from files in the following locations:
1. `/examples/workflows/` - For built-in example workflows
2. `/workflows/` - For user-defined workflows

YAML files in these directories will be loaded automatically when the application starts.

## Implementation Details

1. The workflow engine will support defaults by merging workflow-level defaults with step-specific configurations.
2. Step-specific configurations will override workflow-level defaults.
3. The system will validate workflow configurations against a schema to catch errors early.
4. Workflow configurations will be versionable and shareable between users.

## Consequences

### Positive
- Users can create and modify workflows without changing code
- Workflows can be easily shared and versioned
- Common configurations can be defaulted at the workflow level
- New step types can be added without breaking existing workflows

### Negative
- Additional complexity in the workflow execution engine
- Need for backwards compatibility when changing the schema
- Potential for configuration errors if not validated properly

## References
- [YAML Specification](https://yaml.org/spec/1.2.2/)
- [Configuration-Driven Workflow Design](/docs/design-addendum.md)
