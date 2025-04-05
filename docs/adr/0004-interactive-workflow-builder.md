# 4. Interactive Workflow Builder

## Status

Accepted

## Context

Building and editing workflows in the Curriculum Curator system requires creating and modifying YAML configuration files. This presents several challenges:

1. **High barrier to entry**: Users who are unfamiliar with YAML syntax face difficulties when creating or modifying workflows.
2. **Error-prone**: Manual editing of YAML files can lead to syntax errors, invalid configurations, and difficult-to-debug issues.
3. **Discoverability**: Users may not be aware of all available components (prompts, validators, remediators) that can be used in workflows.
4. **Validation delay**: Errors in the workflow configurations are only discovered when the workflow is run, leading to a longer feedback cycle.

We need a way to make workflow creation more accessible to users who aren't familiar with YAML syntax or the full system architecture, while ensuring valid configurations.

## Decision

We will implement an interactive, menu-driven workflow builder as a CLI subcommand (`build-workflow`) that allows users to create and edit workflow configurations through a guided process. The builder will:

1. Provide a structured interface for all workflow components (prompt steps, validation steps, remediation steps, output steps)
2. Query the system for available components (prompts, validators, remediators) and present them as options
3. Validate the workflow in real-time as it's being built
4. Allow loading existing workflows as a base for creating new ones
5. Implement workflow editing capabilities (add, remove, modify, reorder steps)
6. Save valid configurations to YAML files

This approach offers a middle ground between direct YAML editing and a full web/TUI interface, making the system more accessible without requiring extensive UI development.

## Consequences

### Positive

1. **Reduced learning curve**: Users can create workflows without needing to understand YAML syntax or the full configuration schema.
2. **Improved discoverability**: Available components are presented as menu options, making them more discoverable.
3. **Immediate validation**: Errors are caught during the building process rather than at runtime.
4. **Quicker onboarding**: New users can more quickly become productive with the system.
5. **Extensibility**: The builder can be extended as new step types or features are added to the system.

### Negative

1. **CLI limitations**: The CLI interface has inherent limitations compared to a full GUI/TUI.
2. **Added complexity**: We now have two ways to create workflows (direct YAML editing and the builder), which increases the surface area for bugs.
3. **Maintenance overhead**: Changes to the workflow configuration schema will require updates to both the schema validation and the builder interface.

## Alternatives Considered

1. **Web UI**: A browser-based interface would provide a richer user experience but would require significant additional infrastructure, dependencies, and maintenance.

2. **Full TUI (Terminal User Interface)**: A more comprehensive terminal UI using libraries like Textual could provide a richer experience but would require more development effort and introduce additional dependencies.

3. **Configuration generator scripts**: We could provide helper scripts to generate workflow YAML files, but these would be less interactive and flexible than a full builder.

4. **No builder**: Continue requiring users to edit YAML files directly with improved documentation and examples. This would not address the accessibility concerns.

We chose the interactive CLI builder approach because it strikes a good balance between accessibility and development cost. It addresses the immediate need without overcommitting to a specific UI technology. This approach also allows us to gather user feedback before potentially investing in a more comprehensive web or TUI solution in the future.