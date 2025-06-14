# Remediation

Remediation is the process of automatically fixing or improving educational content based on validation results in the Curriculum Curator system.

## Overview

The remediation system in Curriculum Curator provides automated correction of content issues detected during validation. It helps improve content quality without manual intervention, streamlining the content creation pipeline.

## Remediation Manager

The Remediation Manager orchestrates the remediation process by:

1. Loading appropriate remediators based on configuration
2. Applying remediators to content with validation issues
3. Tracking changes made to the content
4. Providing detailed reports on remediation actions

## Remediator Types

The system includes multiple types of remediators, each addressing different aspects of content improvement:

### AutoFix Remediators

- **Format Corrector**: Fixes formatting issues like inconsistent headers, lists, and spacing
- **Sentence Splitter**: Breaks long sentences into shorter, more readable ones
- **Terminology Enforcer**: Ensures consistent use of terminology according to glossaries

### Language Remediators

- **Translator**: Translates content to a different language
- **Style Adjuster**: Modifies writing style to match target audience

### Rewrite Remediators

- **Rephrasing Prompter**: Uses LLMs to rewrite problematic sections while preserving meaning
- **Simplifier**: Reduces complexity for specified reading levels

### Workflow Remediators

- **Flag for Review**: Marks content for human review when automated fixes aren't possible
- **Escalation**: Routes content to specialized workflows based on specific issues

## Remediation Configuration

Remediators are configured in workflow YAML files:

```yaml
stages:
  - name: "Auto-Remediate Content Issues"
    type: "remediation"
    remediators:
      - name: "sentence_splitter"
        parameters:
          max_sentence_length: 25
          preserve_technical_terms: true

      - name: "format_corrector"
        parameters:
          fix_headers: true
          fix_lists: true

      - name: "rephrasing_prompter"
        parameters:
          severity_threshold: "high"
          preserve_technical_accuracy: true
```

## Remediation Process

When remediation is triggered:

1. The system analyzes validation results to identify issues
2. It selects appropriate remediators based on the issue types
3. Remediators are applied in a configured order
4. Changes are tracked and recorded
5. Content is optionally re-validated to ensure issues are resolved

## Custom Remediators

The system supports creating custom remediators by:

1. Implementing the base Remediator interface
2. Registering the remediator with the system
3. Configuring the remediator in workflows

## Integration with Validation

Remediation works closely with the validation system, using validation results to target specific issues. This creates a powerful pipeline where content can be continuously improved through iterative validation and remediation.

For more information on how validation and remediation work together, see [ADR-0002: Validation and Remediation Design](../adr/0002-validation-remediation-design.md).

## Remediation in Workflows

Remediation is typically included as a specific stage in workflows, often following validation. This ensures that content issues are systematically addressed before proceeding to further processing or delivery stages.

## Human-in-the-Loop Remediation

For complex issues that can't be fully automated, the system supports human-in-the-loop remediation where:

1. Automated fixes are applied where possible
2. Complex issues are flagged for human review
3. Suggestions are provided to guide human editors
4. Manual changes are recorded for future learning
