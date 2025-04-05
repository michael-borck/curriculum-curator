# Core API

The Core API is the central component of the Curriculum Curator system, providing the main entry point and orchestration for the various subsystems.

## CurriculumCurator

The `CurriculumCurator` class is the main entry point for using the system programmatically:

```python
from curriculum_curator.core import CurriculumCurator

curator = CurriculumCurator(config)
result = curator.execute_workflow("workflows/my_workflow.yaml", parameters={"topic": "Python"})
```

### Class Definition

```python
class CurriculumCurator:
    """
    Main entry point for the Curriculum Curator system.

    This class provides a simplified interface to the various subsystems,
    allowing users to easily execute workflows and manage educational content.
    """

    def __init__(self, config=None):
        """
        Initialize a new CurriculumCurator instance.

        Args:
            config (dict, optional): Configuration options. If not provided,
                                    the default configuration will be loaded.
        """

    def execute_workflow(self, workflow_path, parameters=None):
        """
        Execute a workflow defined in a YAML file.

        Args:
            workflow_path (str): Path to the workflow YAML file.
            parameters (dict, optional): Parameters to pass to the workflow.

        Returns:
            WorkflowResult: The result of the workflow execution.
        """

    def save_result(self, result, output_path):
        """
        Save a workflow result to a file.

        Args:
            result (WorkflowResult): The result to save.
            output_path (str): The path where to save the result.

        Returns:
            str: The path where the result was saved.
        """

    def load_prompt(self, prompt_path):
        """
        Load a prompt template from a file.

        Args:
            prompt_path (str): Path to the prompt template file.

        Returns:
            str: The prompt template.
        """

    def format_prompt(self, prompt_template, parameters):
        """
        Format a prompt template with parameters.

        Args:
            prompt_template (str): The prompt template.
            parameters (dict): Parameters to fill in the template.

        Returns:
            str: The formatted prompt.
        """

    def generate_content(self, prompt, model=None, parameters=None):
        """
        Generate content using an LLM.

        Args:
            prompt (str): The prompt to send to the LLM.
            model (str, optional): The LLM model to use.
            parameters (dict, optional): Parameters for the LLM.

        Returns:
            str: The generated content.
        """

    def validate_content(self, content, validators=None):
        """
        Validate content using specified validators.

        Args:
            content (str): The content to validate.
            validators (list, optional): List of validators to use.

        Returns:
            ValidationResult: The validation result.
        """

    def remediate_content(self, content, validation_result, remediators=None):
        """
        Remediate content based on validation results.

        Args:
            content (str): The content to remediate.
            validation_result (ValidationResult): The validation result.
            remediators (list, optional): List of remediators to use.

        Returns:
            str: The remediated content.
        """
```

## WorkflowResult

The `WorkflowResult` class represents the result of a workflow execution:

```python
class WorkflowResult:
    """
    Represents the result of a workflow execution.

    Attributes:
        workflow_name (str): Name of the executed workflow.
        content (str): The generated or processed content.
        metadata (dict): Additional metadata about the execution.
        validation_results (ValidationResult, optional): Results of validation.
        remediation_results (RemediationResult, optional): Results of remediation.
    """

    def __init__(self, workflow_name, content, metadata=None):
        """
        Initialize a new WorkflowResult.

        Args:
            workflow_name (str): Name of the executed workflow.
            content (str): The generated or processed content.
            metadata (dict, optional): Additional metadata.
        """

    def to_dict(self):
        """
        Convert the result to a dictionary.

        Returns:
            dict: Dictionary representation of the result.
        """

    @classmethod
    def from_dict(cls, data):
        """
        Create a WorkflowResult from a dictionary.

        Args:
            data (dict): Dictionary representation of a WorkflowResult.

        Returns:
            WorkflowResult: The created instance.
        """
```

## Functions

The core module also provides several utility functions:

### load_config

```python
def load_config(config_path=None):
    """
    Load configuration from a file.

    Args:
        config_path (str, optional): Path to the configuration file.
                                    If not provided, the default configuration is used.

    Returns:
        dict: The loaded configuration.
    """
```

### get_default_config

```python
def get_default_config():
    """
    Get the default configuration.

    Returns:
        dict: The default configuration.
    """
```

### create_workflow

```python
def create_workflow(name, description, stages):
    """
    Create a new workflow definition.

    Args:
        name (str): Name of the workflow.
        description (str): Description of the workflow.
        stages (list): List of stage definitions.

    Returns:
        dict: The created workflow definition.
    """
```

### save_workflow

```python
def save_workflow(workflow, output_path):
    """
    Save a workflow definition to a file.

    Args:
        workflow (dict): The workflow definition.
        output_path (str): Path where to save the workflow.

    Returns:
        str: The path where the workflow was saved.
    """
```

## Examples

### Basic Workflow Execution

```python
from curriculum_curator.core import CurriculumCurator, load_config

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

# Save the result
curator.save_result(result, "output/python_module.md")
```

### Content Generation and Validation

```python
from curriculum_curator.core import CurriculumCurator

curator = CurriculumCurator()

# Load and format a prompt
prompt_template = curator.load_prompt("prompts/module/outline.txt")
prompt = curator.format_prompt(prompt_template, {
    "topic": "Introduction to Python",
    "learning_level": "beginner"
})

# Generate content
content = curator.generate_content(prompt)

# Validate the content
validation_result = curator.validate_content(content, validators=[
    {"name": "readability", "parameters": {"min_score": 70}},
    {"name": "structure", "parameters": {"required_sections": ["objectives", "content"]}}
])

# Remediate the content if needed
if not validation_result.passed:
    content = curator.remediate_content(content, validation_result)

# Save the final content
with open("output/python_module.md", "w") as f:
    f.write(content)
```

### Creating and Saving a Workflow

```python
from curriculum_curator.core import create_workflow, save_workflow

# Define a workflow
workflow = create_workflow(
    name="Basic Module Generation",
    description="Generate a module outline with validation",
    stages=[
        {
            "name": "Generate Module Outline",
            "type": "llm_generation",
            "prompt_template": "module/outline.txt",
            "parameters": {
                "topic": "{topic}",
                "learning_level": "{learning_level}"
            }
        },
        {
            "name": "Validate Module Outline",
            "type": "validation",
            "validators": [
                {
                    "name": "readability",
                    "parameters": {
                        "min_score": 60
                    }
                }
            ]
        }
    ]
)

# Save the workflow
save_workflow(workflow, "workflows/basic_module.yaml")
```
