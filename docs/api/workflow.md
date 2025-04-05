# Workflow API

The Workflow API provides the components for defining, building, and executing workflows within the Curriculum Curator system.

## WorkflowEngine

The `WorkflowEngine` class is responsible for executing workflow definitions:

```python
from curriculum_curator.workflow.engine import WorkflowEngine

engine = WorkflowEngine(config)
workflow = engine.load_workflow("workflows/my_workflow.yaml")
result = engine.execute(workflow, parameters={"topic": "Python"})
```

### Class Definition

```python
class WorkflowEngine:
    """
    Engine for executing workflows defined in YAML configurations.

    The WorkflowEngine is responsible for orchestrating the execution of
    multi-stage workflows, including content generation, validation,
    and remediation stages.
    """

    def __init__(self, config=None, llm_manager=None, validation_manager=None,
                 remediation_manager=None, prompt_registry=None):
        """
        Initialize a new WorkflowEngine.

        Args:
            config (dict, optional): Configuration options.
            llm_manager (LLMManager, optional): LLM manager instance.
            validation_manager (ValidationManager, optional): Validation manager instance.
            remediation_manager (RemediationManager, optional): Remediation manager instance.
            prompt_registry (PromptRegistry, optional): Prompt registry instance.
        """

    def load_workflow(self, workflow_path):
        """
        Load a workflow definition from a YAML file.

        Args:
            workflow_path (str): Path to the workflow YAML file.

        Returns:
            Workflow: The loaded workflow object.
        """

    def execute(self, workflow, parameters=None):
        """
        Execute a workflow with optional parameters.

        Args:
            workflow (Workflow): The workflow to execute.
            parameters (dict, optional): Parameters to pass to the workflow.

        Returns:
            WorkflowResult: The result of the workflow execution.
        """

    def execute_stage(self, stage, content=None, parameters=None):
        """
        Execute a single workflow stage.

        Args:
            stage (Stage): The stage to execute.
            content (str, optional): Input content for the stage.
            parameters (dict, optional): Parameters for the stage.

        Returns:
            tuple: (output_content, stage_result)
        """

    def execute_llm_generation_stage(self, stage, parameters=None):
        """
        Execute an LLM generation stage.

        Args:
            stage (Stage): The LLM generation stage to execute.
            parameters (dict, optional): Parameters for the stage.

        Returns:
            tuple: (generated_content, stage_result)
        """

    def execute_validation_stage(self, stage, content, parameters=None):
        """
        Execute a validation stage.

        Args:
            stage (Stage): The validation stage to execute.
            content (str): Content to validate.
            parameters (dict, optional): Parameters for the stage.

        Returns:
            tuple: (content, validation_result)
        """

    def execute_remediation_stage(self, stage, content, validation_results, parameters=None):
        """
        Execute a remediation stage.

        Args:
            stage (Stage): The remediation stage to execute.
            content (str): Content to remediate.
            validation_results (ValidationResult): Validation results.
            parameters (dict, optional): Parameters for the stage.

        Returns:
            tuple: (remediated_content, remediation_result)
        """
```

## WorkflowBuilder

The `WorkflowBuilder` class provides an interactive way to build workflow definitions:

```python
from curriculum_curator.workflow.builder import WorkflowBuilder

builder = WorkflowBuilder()
workflow = builder.build_interactive()
builder.save_workflow(workflow, "workflows/new_workflow.yaml")
```

### Class Definition

```python
class WorkflowBuilder:
    """
    Interactive builder for creating workflow definitions.

    The WorkflowBuilder provides a guided approach to creating workflow
    definitions without requiring manual YAML editing.
    """

    def __init__(self, prompt_registry=None, validator_registry=None,
                 remediator_registry=None):
        """
        Initialize a new WorkflowBuilder.

        Args:
            prompt_registry (PromptRegistry, optional): Prompt registry instance.
            validator_registry (list, optional): List of available validators.
            remediator_registry (list, optional): List of available remediators.
        """

    def build_interactive(self):
        """
        Build a workflow interactively through command-line prompts.

        Returns:
            Workflow: The created workflow.
        """

    def add_stage_interactive(self, workflow):
        """
        Add a stage to a workflow interactively.

        Args:
            workflow (Workflow): The workflow to add a stage to.

        Returns:
            Stage: The added stage.
        """

    def add_llm_stage_interactive(self):
        """
        Add an LLM generation stage interactively.

        Returns:
            Stage: The created LLM generation stage.
        """

    def add_validation_stage_interactive(self):
        """
        Add a validation stage interactively.

        Returns:
            Stage: The created validation stage.
        """

    def add_remediation_stage_interactive(self):
        """
        Add a remediation stage interactively.

        Returns:
            Stage: The created remediation stage.
        """

    def save_workflow(self, workflow, output_path):
        """
        Save a workflow to a YAML file.

        Args:
            workflow (Workflow): The workflow to save.
            output_path (str): Path where to save the workflow.

        Returns:
            str: The path where the workflow was saved.
        """
```

## Workflow Models

### Workflow

```python
class Workflow:
    """
    Represents a workflow definition.

    A workflow consists of metadata and a sequence of stages to be executed
    in order.

    Attributes:
        name (str): Name of the workflow.
        description (str): Description of the workflow.
        stages (list): List of Stage objects.
        metadata (dict): Additional metadata about the workflow.
    """

    def __init__(self, name, description="", stages=None, metadata=None):
        """
        Initialize a new Workflow.

        Args:
            name (str): Name of the workflow.
            description (str, optional): Description of the workflow.
            stages (list, optional): List of Stage objects.
            metadata (dict, optional): Additional metadata.
        """

    def add_stage(self, stage):
        """
        Add a stage to the workflow.

        Args:
            stage (Stage): The stage to add.

        Returns:
            Workflow: Self for chaining.
        """

    def to_dict(self):
        """
        Convert the workflow to a dictionary.

        Returns:
            dict: Dictionary representation of the workflow.
        """

    @classmethod
    def from_dict(cls, data):
        """
        Create a Workflow from a dictionary.

        Args:
            data (dict): Dictionary representation of a workflow.

        Returns:
            Workflow: The created instance.
        """
```

### Stage

```python
class Stage:
    """
    Represents a stage in a workflow.

    A stage is a single step in a workflow, such as content generation,
    validation, or remediation.

    Attributes:
        name (str): Name of the stage.
        type (str): Type of the stage (e.g., "llm_generation", "validation").
        parameters (dict): Parameters for the stage.
    """

    def __init__(self, name, type_, parameters=None):
        """
        Initialize a new Stage.

        Args:
            name (str): Name of the stage.
            type_ (str): Type of the stage.
            parameters (dict, optional): Parameters for the stage.
        """

    def to_dict(self):
        """
        Convert the stage to a dictionary.

        Returns:
            dict: Dictionary representation of the stage.
        """

    @classmethod
    def from_dict(cls, data):
        """
        Create a Stage from a dictionary.

        Args:
            data (dict): Dictionary representation of a stage.

        Returns:
            Stage: The created instance.
        """
```

## Examples

### Defining a Workflow Programmatically

```python
from curriculum_curator.workflow.models import Workflow, Stage

# Create stages
generate_stage = Stage(
    name="Generate Module Outline",
    type_="llm_generation",
    parameters={
        "prompt_template": "module/outline.txt",
        "parameters": {
            "topic": "{topic}",
            "learning_level": "{learning_level}"
        }
    }
)

validate_stage = Stage(
    name="Validate Module Outline",
    type_="validation",
    parameters={
        "validators": [
            {
                "name": "readability",
                "parameters": {
                    "min_score": 60
                }
            }
        ]
    }
)

remediate_stage = Stage(
    name="Auto-Remediate Issues",
    type_="remediation",
    parameters={
        "remediators": [
            {
                "name": "sentence_splitter",
                "parameters": {
                    "max_sentence_length": 25
                }
            }
        ]
    }
)

# Create workflow
workflow = Workflow(
    name="Basic Module Generation",
    description="Generate module outline with validation and remediation",
    stages=[generate_stage, validate_stage, remediate_stage],
    metadata={
        "version": "1.0",
        "author": "Curriculum Curator Team"
    }
)

# Convert to dictionary for serialization
workflow_dict = workflow.to_dict()
```

### Using the Workflow Engine

```python
from curriculum_curator.workflow.engine import WorkflowEngine
from curriculum_curator.llm.manager import LLMManager
from curriculum_curator.validation.manager import ValidationManager
from curriculum_curator.remediation.manager import RemediationManager
from curriculum_curator.prompt.registry import PromptRegistry
from curriculum_curator.config.utils import load_config

# Load configuration
config = load_config("config.yaml")

# Initialize components
llm_manager = LLMManager(config)
validation_manager = ValidationManager(config)
remediation_manager = RemediationManager(config)
prompt_registry = PromptRegistry()

# Initialize the workflow engine
engine = WorkflowEngine(
    config=config,
    llm_manager=llm_manager,
    validation_manager=validation_manager,
    remediation_manager=remediation_manager,
    prompt_registry=prompt_registry
)

# Load a workflow
workflow = engine.load_workflow("workflows/module_generation.yaml")

# Execute the workflow
result = engine.execute(
    workflow,
    parameters={
        "topic": "Machine Learning Basics",
        "learning_level": "intermediate"
    }
)

# Process the result
print(f"Workflow '{result.workflow_name}' executed successfully.")
print(f"Content length: {len(result.content)} characters")
if hasattr(result, 'validation_results'):
    print(f"Validation passed: {result.validation_results.passed}")
```

### Interactive Workflow Building

```python
from curriculum_curator.workflow.builder import WorkflowBuilder
from curriculum_curator.prompt.registry import PromptRegistry

# Initialize components
prompt_registry = PromptRegistry()
builder = WorkflowBuilder(prompt_registry=prompt_registry)

# Build a workflow interactively
workflow = builder.build_interactive()

# Save the workflow
builder.save_workflow(workflow, "workflows/custom_workflow.yaml")
```
