# Configuration System

## Overview

Curriculum Curator uses [Pydantic](https://docs.pydantic.dev/) for configuration validation and type safety. Pydantic is a data validation library that uses Python type annotations to validate data structures and provide helpful error messages.

## Configuration Models

The configuration system is built around a hierarchy of Pydantic models, with `AppConfig` as the root model. These models define the expected structure of the configuration and provide automatic validation.

### How Pydantic Models Work

Pydantic models are similar to database schemas or TypeScript interfaces - they define the shape and constraints of data. They:

- Enforce types and validation rules
- Generate clear error messages when data doesn't match expectations
- Provide automatic conversion between types when possible (e.g., string to int)
- Allow for default values and optional fields

### Core Configuration Models

#### AppConfig

The root configuration model that contains all other configuration sections:

```python
class AppConfig(BaseModel):
    """Overall application configuration."""

    system: SystemConfig = Field(default_factory=SystemConfig)
    llm: LLMConfig = Field(...)  # Required
    prompts: PromptConfig = Field(default_factory=PromptConfig)
    validation: Optional[ValidationConfig] = None
    remediation: Optional[RemediationConfig] = None
    output: Optional[OutputConfig] = None
    workflows: Dict[str, WorkflowConfig] = Field(
        default_factory=dict, description="Available workflows"
    )
```

#### LLM Configuration

Models for LLM provider configuration:

```python
class LLMConfig(BaseModel):
    """LLM configuration."""

    default_provider: str = Field(..., description="Default LLM provider to use")
    aliases: Dict[str, str] = Field(
        default_factory=dict, description="Model aliases for easier reference"
    )
    providers: Dict[str, LLMProviderConfig] = Field(
        default_factory=dict, description="LLM provider configurations"
    )
```

#### Workflow Configuration

Models for workflow definitions:

```python
class WorkflowConfig(BaseModel):
    """Configuration for a workflow."""

    description: str = Field(..., description="Description of the workflow")
    steps: List[WorkflowStepConfig] = Field(
        default_factory=list, description="Steps in the workflow"
    )
```

## Loading Configuration

Configuration can be loaded from YAML files using the `load_config` function:

```python
from curriculum_curator.config.utils import load_config

# Load config from a file
config = load_config("config.yaml")

# Access configuration values with type safety
provider = config.llm.default_provider
workflow_names = list(config.workflows.keys())
```

## Benefits of Pydantic for Configuration

1. **Type Safety**: Configuration errors are caught early with clear error messages
2. **Self-Documenting**: Models make it clear what configuration options are available
3. **IDE Support**: Type hints enable autocomplete and inline documentation
4. **Validation**: Complex validation rules ensure configuration correctness
5. **Default Values**: Less configuration required for common use cases

## Example Configuration

Here's an example of a minimal YAML configuration file:

```yaml
llm:
  default_provider: openai
  providers:
    openai:
      api_key: env(OPENAI_API_KEY)
      default_model: gpt-4
      models:
        gpt-4: {}
        gpt-3.5-turbo: {}

workflows:
  generate_module:
    description: Generate a learning module
    steps:
      - name: outline
        type: prompt
        prompt: module/outline.txt
        output_variable: module_outline
      - name: validate_outline
        type: validation
        validators: [structure]
        targets: [module_outline]
```

## Environment Variable Resolution

LLM API keys can be specified as environment variables using the `env()` syntax:

```yaml
llm:
  providers:
    openai:
      api_key: env(OPENAI_API_KEY)
```

The Pydantic validator will automatically resolve these references to the actual environment variable values.
