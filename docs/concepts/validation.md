# Validation

Validation is the process of assessing educational content against predetermined quality criteria in the Curriculum Curator system.

## Overview

The validation system in Curriculum Curator provides automated quality checks for educational content. It helps ensure that generated or imported content meets specific standards before being used in educational materials.

## Validation Manager

The Validation Manager orchestrates the validation process by:

1. Loading appropriate validators based on configuration
2. Running validators against content
3. Collecting and organizing validation results
4. Providing feedback on issues found

## Validator Types

The system includes multiple types of validators, each focusing on different aspects of educational content:

### Quality Validators

- **Readability**: Assesses content readability using metrics like Flesch-Kincaid
- **Structure**: Checks for proper hierarchical structure in content
- **Similarity**: Compares content against reference materials to ensure originality

### Language Validators

- **Language Detection**: Ensures content is in the expected language
- **Terminology**: Verifies that domain-specific terminology is used correctly

### Alignment Validators

- **Learning Objective Alignment**: Checks that content aligns with stated learning objectives
- **Curriculum Standards**: Validates against educational standards or frameworks

### Safety Validators

- **Content Safety**: Checks for inappropriate, harmful, or biased content
- **Factual Accuracy**: Flags potentially incorrect information

## Validation Configuration

Validators are configured in workflow YAML files:

```yaml
stages:
  - name: "Validate Module Content"
    type: "validation"
    validators:
      - name: "readability"
        parameters:
          min_score: 60
          target_audience: "undergraduate"
      
      - name: "structure"
        parameters:
          required_sections: ["objectives", "content", "assessment"]
          
      - name: "language_detector"
        parameters:
          expected_language: "en"
```

## Validation Results

Validation produces structured results that include:

- Overall pass/fail status
- Individual validator results
- Specific issues detected
- Severity levels for issues
- Suggestions for improvement

## Custom Validators

The system supports creating custom validators by:

1. Implementing the base Validator interface
2. Registering the validator with the system
3. Configuring the validator in workflows

## Integration with Remediation

Validation results can be directly fed into the remediation system for automatic fixing of detected issues. This creates a powerful pipeline where content can be continuously improved through iterative validation and remediation.

For more information on how validation and remediation work together, see [ADR-0002: Validation and Remediation Design](../adr/0002-validation-remediation-design.md).

## Validation in Workflows

Validation is typically included as a specific stage in workflows, often following content generation and preceding remediation. This ensures that content quality is systematically assessed before proceeding to further processing or delivery stages.