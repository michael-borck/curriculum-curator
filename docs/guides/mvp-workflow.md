# MVP Workflow Guide

This guide describes the minimal viable product (MVP) workflow for generating educational content with Curriculum Curator.

## Overview

The MVP workflow (`minimal_educational_module`) generates a complete educational module with the following components:
- Course overview
- Module outline
- Lecture content
- Worksheet with practice activities
- Assessment with various question types
- Instructor guide with teaching suggestions and answer keys

The workflow includes validation and remediation steps to ensure content quality. Each component is output as a separate Markdown file.

## Workflow Steps

1. **Generate Course Overview**: Creates a high-level overview of the course
2. **Generate Module Outline**: Creates a structured outline for the module
3. **Generate Lecture Content**: Creates the main lecture content based on the outline
4. **Validate Lecture Content**: Checks for readability and structural issues
5. **Remediate Lecture Content**: Fixes any issues found during validation
6. **Generate Worksheet**: Creates practice activities related to the lecture content
7. **Generate Assessment**: Creates assessment questions to evaluate learning
8. **Generate Instructor Materials**: Creates a guide for instructors with answer keys
9. **Generate Output Files**: Saves all generated content to Markdown files

## Configuration-Based Workflow

The MVP workflow is defined in a YAML configuration file located at `examples/workflows/minimal_module.yaml`. This approach allows for:

- Easy customization without code changes
- Reuse of common steps across different workflows
- Addition of new steps or modification of existing ones
- Simple sharing of workflow configurations

### Workflow Configuration Example

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

## Running the Workflow

### Using the CLI

```bash
# Load workflow config from a file
curator run --config examples/workflows/minimal_module.yaml \
  --var course_title="Introduction to Python Programming" \
  --var course_slug="intro-python" \
  --var num_modules=4 \
  --var module_id="module1" \
  --var "learning_objectives=Understand basic Python syntax and data structures;Write simple Python programs"
```

### Using the Sample Script

We've provided a sample script that runs the workflow from the config file:

```bash
python examples/run_minimal_module.py
```

### Required Context Variables

The workflow requires the following context variables:

- `course_title`: Title of the course
- `course_slug`: URL-friendly version of the course title
- `learning_objectives`: List of learning objectives for the course
- `num_modules`: Number of modules to generate
- `module_id`: ID of the current module being generated

## Output

The workflow generates the following output files in the `output/{course_slug}/{module_id}/` directory:

- `overview.md`: Course overview
- `lecture.md`: Lecture content
- `worksheet.md`: Practice activities worksheet
- `assessment.md`: Assessment questions
- `instructor_guide.md`: Instructor guide with answer keys

## Extending the Workflow

To extend this workflow:

1. Add new prompt templates in the `prompts/` directory
2. Create a copy of the workflow YAML file and modify it
3. Add new steps or modify existing ones in the YAML configuration
4. Update the context variables to include any new required inputs

This config-driven approach allows you to:
- Create specialized workflows for different educational needs
- Share workflow configurations between users
- Version control your workflow definitions
- Experiment with different step sequences without code changes

## Creating Your Own Workflows

1. Start with a copy of an existing workflow YAML file
2. Add or remove steps as needed
3. Configure each step with the appropriate parameters
4. Test with sample inputs
5. Iterate and refine as needed

## Troubleshooting

If you encounter errors:

1. Check that all required context variables are provided
2. Verify that your LLM API credentials are correctly configured
3. Check the logs for detailed error messages
4. Ensure all prompt templates have the correct metadata
5. Validate your workflow YAML configuration for syntax errors