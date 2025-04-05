# API Overview

This section provides an overview of the Curriculum Curator API, its main components, and how they interact.

## Core Components

The Curriculum Curator API is organized into several core modules:

1. **Core**: Central orchestration and workflow execution
2. **Config**: Configuration management and validation
3. **Workflow**: Workflow definition and execution
4. **Prompt**: Prompt template management
5. **LLM**: Language model integration
6. **Validation**: Content validation framework
7. **Remediation**: Content remediation framework
8. **Persistence**: Data storage and retrieval
9. **Content**: Content transformation utilities

## API Structure

The API follows a modular design that separates concerns:

```
curriculum_curator/
├── core.py          # Core orchestration
├── config/          # Configuration management
├── workflow/        # Workflow engine
├── prompt/          # Prompt management
├── llm/             # LLM integration
├── validation/      # Content validation
├── remediation/     # Content remediation
├── persistence/     # Data persistence
└── utils/           # Utility functions
```

## Key Interfaces

### WorkflowEngine

The `WorkflowEngine` is the central component that orchestrates the execution of workflows:

```python
class WorkflowEngine:
    def __init__(self, config, llm_manager=None):
        """Initialize a workflow engine with configuration."""

    def load_workflow(self, workflow_path):
        """Load a workflow definition from a file."""

    def execute(self, workflow, parameters=None):
        """Execute a workflow with optional parameters."""

    def execute_stage(self, stage, content=None):
        """Execute a single workflow stage."""
```

### ValidationManager

The `ValidationManager` handles content validation:

```python
class ValidationManager:
    def __init__(self, config=None):
        """Initialize the validation manager."""

    def validate(self, content, validators=None):
        """Validate content using specified validators."""

    def get_validator(self, name):
        """Get a validator by name."""
```

### RemediationManager

The `RemediationManager` handles automatic content remediation:

```python
class RemediationManager:
    def __init__(self, config=None):
        """Initialize the remediation manager."""

    def remediate(self, content, validation_results, remediators=None):
        """Remediate content based on validation results."""

    def get_remediator(self, name):
        """Get a remediator by name."""
```

### PromptRegistry

The `PromptRegistry` manages prompt templates:

```python
class PromptRegistry:
    def __init__(self, prompt_dirs=None):
        """Initialize the prompt registry."""

    def get_prompt(self, template_name):
        """Get a prompt template by name."""

    def format_prompt(self, template_name, parameters):
        """Format a prompt template with parameters."""
```

### LLMManager

The `LLMManager` provides a unified interface to language models:

```python
class LLMManager:
    def __init__(self, config=None):
        """Initialize the LLM manager."""

    def generate(self, prompt, model=None, parameters=None):
        """Generate content using the specified LLM."""

    def get_model(self, name):
        """Get a specific LLM model."""
```

## Using the API

### Basic Usage

Here's a simple example of using the Curriculum Curator API:

```python
from curriculum_curator.core import CurriculumCurator
from curriculum_curator.config.utils import load_config

# Load configuration
config = load_config("config.yaml")

# Initialize the curator
curator = CurriculumCurator(config)

# Execute a workflow
result = curator.execute_workflow(
    "workflows/generate_module.yaml",
    parameters={
        "topic": "Introduction to Python",
        "learning_level": "beginner"
    }
)

# Access the generated content
module_outline = result.content

# Save the result
curator.save_result(result, "output/python_module.md")
```

### Advanced Usage

For more advanced usage, you can interact with the individual components directly:

```python
from curriculum_curator.workflow.engine import WorkflowEngine
from curriculum_curator.llm.manager import LLMManager
from curriculum_curator.prompt.registry import PromptRegistry

# Initialize components
llm_manager = LLMManager(config)
prompt_registry = PromptRegistry()
workflow_engine = WorkflowEngine(config, llm_manager=llm_manager)

# Load and execute a workflow
workflow = workflow_engine.load_workflow("workflows/custom_workflow.yaml")
result = workflow_engine.execute(workflow, {"topic": "Machine Learning"})

# Validate content separately
from curriculum_curator.validation.manager import ValidationManager
validation_manager = ValidationManager(config)
validation_results = validation_manager.validate(
    result.content,
    validators=[
        {"name": "readability", "parameters": {"min_score": 70}}
    ]
)

# Remediate content based on validation results
from curriculum_curator.remediation.manager import RemediationManager
remediation_manager = RemediationManager(config)
remediated_content = remediation_manager.remediate(
    result.content,
    validation_results,
    remediators=[
        {"name": "sentence_splitter", "parameters": {"max_length": 25}}
    ]
)
```

## Extension Points

The API is designed to be extensible through several key extension points:

1. **Custom Validators**: Create your own validators by extending the base `Validator` class
2. **Custom Remediators**: Create your own remediators by extending the base `Remediator` class
3. **Custom LLM Providers**: Add support for new LLM providers by implementing the `LLMProvider` interface
4. **Custom Storage Backends**: Implement custom storage solutions by extending the `StorageProvider` interface

For more detailed information on specific API components, refer to the dedicated API reference pages.
