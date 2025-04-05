# Configuration-Driven Workflow Design

This document describes the configuration-driven workflow design pattern implemented in Curriculum Curator.

## Overview

The Curriculum Curator system uses a configuration-driven approach to defining workflows. In this pattern, the workflow logic and execution engine are separated from the workflow definitions, which are stored in external configuration files. This approach has several advantages:

1. **Flexibility**: Workflows can be modified without changing code
2. **Reusability**: Common steps can be reused across different workflows
3. **Shareability**: Workflow definitions can be easily shared between users
4. **Version Control**: Workflows can be versioned independently of the core code
5. **Extensibility**: New step types can be added without breaking existing workflows

## Workflow Configuration Structure

Workflows are defined in YAML files that specify the sequence of steps to be executed:

```yaml
name: minimal_educational_module
description: "Generates a complete educational module with basic components"
steps:
  - name: course_overview
    type: prompt
    prompt: course/overview.txt
    llm_model_alias: default_smart
    output_format: raw
    output_variable: course_overview

  # Additional steps...

  - name: generate_outputs
    type: output
    output_mapping:
      course_overview: overview.md
      remediated_lecture: lecture.md
      worksheet: worksheet.md
      assessment: assessment.md
      instructor_materials: instructor_guide.md
    output_dir: output/{course_slug}/{module_id}
```

Each workflow configuration includes:
- **name**: Unique identifier for the workflow
- **description**: Human-readable description of the workflow's purpose
- **steps**: Array of step configurations, each with:
  - **name**: Unique identifier for the step
  - **type**: Step type (prompt, validation, remediation, output, etc.)
  - **step-specific parameters**: Parameters specific to the step type

## Workflow Discovery

Workflows are discovered dynamically at runtime:

1. The system looks for workflow configurations in predefined directories:
   - `examples/workflows/`
   - `workflows/`

2. All YAML files in these directories are loaded and indexed by name

3. When a user requests a workflow by name, the system:
   - Searches for a matching workflow in the loaded configurations
   - If found, loads the configuration and executes the workflow
   - If not found, returns an error

This approach allows users to add new workflows simply by adding new YAML files to the appropriate directory.

## Execution Engine

The workflow execution engine is responsible for:

1. Loading the workflow configuration
2. Creating step instances based on the step type
3. Executing each step in sequence
4. Managing the context shared between steps
5. Handling errors and recovering from failures
6. Persisting the state of the workflow for potential resumption

The execution engine provides a uniform interface for all workflows, regardless of their specific steps or configurations.

## Context Sharing

Steps in a workflow share a common context dictionary that allows them to pass data to subsequent steps:

1. The initial context contains variables provided by the user
2. Each step can read values from the context and add new values to it
3. Output variables from one step can be used as input for subsequent steps
4. The final context contains all intermediate results and the final outputs

This pattern allows complex workflows to be built from simple steps that each perform a specific task.

## Benefits of Configuration-Driven Workflows

The configuration-driven approach provides several benefits:

1. **Separation of Concerns**: Core logic remains stable while workflows can evolve
2. **Reduced Code Duplication**: Common patterns are encapsulated in the engine
3. **Lower Barrier to Entry**: Users can create workflows without coding
4. **Flexibility**: Workflows can be adapted to different use cases without code changes
5. **Testing Simplicity**: Workflows can be tested independently of the core code

## Implementation

The workflow system is implemented in the following components:

1. **WorkflowStep**: Base class for all step types
2. **Workflow**: Class that manages the execution of a sequence of steps
3. **Step Type Implementations**: Specialized classes for each step type (PromptStep, ValidationStep, etc.)
4. **Workflow Configuration Loader**: Utilities for loading workflow configurations from files

This implementation allows for easy extension with new step types and workflow patterns.

## Future Enhancements

The configuration-driven workflow system can be extended in several ways:

1. **Conditional Steps**: Steps that execute based on conditions
2. **Loop Steps**: Steps that repeat a sequence for each item in a collection
3. **Parallel Steps**: Steps that execute in parallel for improved performance
4. **Custom Step Types**: Support for user-defined step types
5. **Visual Workflow Editor**: A graphical interface for building workflows
