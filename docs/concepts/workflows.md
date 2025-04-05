# Workflows

Workflows are the central concept in Curriculum Curator, representing a sequence of processing steps applied to educational content.

## Overview

A workflow is a configurable pipeline of operations that can transform, validate, and remediate educational content. Workflows allow you to define how content moves through your educational content creation pipeline, from initial drafts to final publication.

## Key Components

### Workflow Definition

Workflows are defined using YAML configuration files. A typical workflow includes:

- **Metadata**: Information about the workflow itself
- **Stages**: Ordered sequence of processing steps
- **Validation Rules**: Criteria for content quality assessment
- **Remediation Actions**: Automatic fixes for common issues

Example workflow configuration:

```yaml
name: "Basic Module Generation"
description: "Generate module outline with validation"

stages:
  - name: "Generate Module Outline"
    type: "llm_generation"
    prompt_template: "module/outline.txt"
    parameters:
      topic: "{topic}"
      learning_level: "{learning_level}"
      
  - name: "Validate Module Outline"
    type: "validation"
    validators:
      - name: "readability"
        parameters:
          min_score: 60
          
  - name: "Auto-Remediate Issues"
    type: "remediation"
    remediators:
      - name: "sentence_splitter"
        parameters:
          max_sentence_length: 25
```

## Workflow Execution

When a workflow is executed:

1. Each stage is processed in order
2. Content flows from one stage to the next
3. Validation stages check content against rules
4. Remediation stages attempt to fix detected issues
5. Results are stored according to the configuration

## Interactive Workflow Builder

The Curriculum Curator provides an interactive workflow builder tool that allows you to create and edit workflows through a guided interface without manually editing YAML files. For more information, see the [Workflow Builder Guide](../guides/workflow-builder.md).

## Pre-defined Workflows

The system comes with several pre-defined workflows that address common education content creation needs:

- **Minimal Module Workflow**: Basic module generation with minimal validation
- **Comprehensive Course Workflow**: Complete course creation with all content types
- **Assessment Generation Workflow**: Focused on creating varied assessments

## Custom Workflows

You can create custom workflows by:

1. Starting with an existing workflow template
2. Creating a new workflow from scratch
3. Using the interactive workflow builder
4. Manually creating a workflow YAML file

For more information on creating a basic workflow, see the [MVP Workflow Guide](../guides/mvp-workflow.md).