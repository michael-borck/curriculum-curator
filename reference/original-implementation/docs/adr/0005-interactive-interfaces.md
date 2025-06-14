# 5. Interactive Interfaces

## Status

Accepted

## Context

Following the implementation of the interactive workflow builder (ADR-0004), we recognized an opportunity to further improve the user experience by creating additional interactive interfaces for other system components. Specifically:

1. **Prompt Management**: Creating and editing prompts required direct file editing with a potentially steep learning curve for YAML front matter.
2. **Command Discoverability**: Users needed to remember CLI commands and parameters for different operations.
3. **Context Switching**: Moving between different tasks like running workflows, editing prompts, and building workflows required different command syntax.

In educational content creation contexts, many potential users may not be comfortable with command-line interfaces and direct file editing, which could limit adoption.

## Decision

We will implement a comprehensive suite of interactive interfaces to make the system more accessible:

1. **Interactive Prompt Editor**: A menu-driven interface for creating and editing prompts, with:
   - Template selection for different content types
   - Front matter validation
   - System editor integration
   - Directory structure management

2. **Top-Level Interactive Mode**: A unified menu interface that provides access to all system functionality:
   - Running workflows
   - Building/editing workflows
   - Editing prompts
   - Initializing projects

3. **Consistent UI Components**: Standardize on the Rich library for all interactive interfaces, providing:
   - Colored output with consistent styling
   - Tables for structured information
   - Confirmation prompts for potentially destructive actions
   - Progress indicators

This approach builds on the success of the interactive workflow builder while extending the same user experience paradigm to other parts of the system.

## Consequences

### Positive

1. **Reduced Learning Curve**: Users can accomplish tasks without needing to know specific command syntax or file formats.
2. **Guided Workflows**: Step-by-step menus guide users through complex processes like prompt creation.
3. **Better Prompt Quality**: Templates and validation ensure that prompts include all necessary components.
4. **Unified Experience**: The interactive mode provides a single entry point for all operations.
5. **Progressive Disclosure**: Complex options are revealed only when needed, reducing cognitive load.

### Negative

1. **Interface Maintenance**: Multiple interfaces require consistent maintenance as the underlying functionality evolves.
2. **Increased Code Complexity**: Interactive interfaces add more code paths to maintain and test.
3. **Terminal Limitations**: Terminal-based interfaces have inherent limitations compared to web or native GUIs.
4. **Documentation Overhead**: We must document both the CLI commands and the interactive interfaces.

## Alternatives Considered

1. **Web Interface**: A browser-based UI would provide a richer experience but require significantly more infrastructure.
2. **GUI Application**: A native GUI application could offer a polished experience but would add platform dependencies and complexity.
3. **Direct File Editing Only**: We could focus solely on improving documentation for direct file editing, but this would maintain a high barrier to entry.
4. **Configuration Generation Scripts**: Simple scripts to generate configurations would be easier to implement but less flexible.

We chose the interactive CLI approach because it strikes the right balance between usability and implementation complexity. It addresses immediate user needs without overcommitting to a specific UI technology, allowing us to gather user feedback before potentially investing in a more sophisticated interface in the future.
