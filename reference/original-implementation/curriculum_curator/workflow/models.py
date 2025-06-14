"""Pydantic models for workflow configuration validation."""

from typing import Any, Literal, Optional, Union

from pydantic import BaseModel, Field, root_validator, validator


# Base models for all steps
class BaseStepConfig(BaseModel):
    """Base configuration for all workflow steps."""

    name: str = Field(..., description="Unique name for this step")
    type: str = Field(..., description="Type of step (prompt, validation, remediation, output)")


# Prompt step specific config
class PromptStepConfig(BaseStepConfig):
    """Configuration for a prompt step that generates content using an LLM."""

    type: Literal["prompt"] = Field("prompt", description="Step type")
    prompt: str = Field(..., description="Path to the prompt template file")
    output_variable: str = Field(..., description="Variable to store the generated content")
    llm_model_alias: Optional[str] = Field(None, description="LLM model alias to use")
    output_format: Optional[str] = Field(
        "raw", description="Format for LLM output (raw, json, list, html)"
    )
    transformation_rules: Optional[dict[str, Any]] = Field(
        None, description="Rules for transforming content"
    )

    @validator("output_format")
    def validate_output_format(cls, v):
        """Validate that output_format is one of the allowed values."""
        valid_formats = ["raw", "json", "list", "html"]
        if v not in valid_formats:
            raise ValueError(f"output_format must be one of {valid_formats}")
        return v


# Validation step specific config
class ValidationStepConfig(BaseStepConfig):
    """Configuration for a validation step that checks content quality."""

    type: Literal["validation"] = Field("validation", description="Step type")
    content_variable: str = Field(..., description="Variable containing content to validate")
    output_variable: str = Field(..., description="Variable to store validation issues")
    validators: list[str] = Field(..., description="List of validators to apply")
    validation_config: Optional[dict[str, Any]] = Field(
        None, description="Additional validator configuration"
    )


# Remediation step specific config
class RemediationStepConfig(BaseStepConfig):
    """Configuration for a remediation step that fixes content issues."""

    type: Literal["remediation"] = Field("remediation", description="Step type")
    content_variable: str = Field(..., description="Variable containing content to remediate")
    issues_variable: str = Field(..., description="Variable containing validation issues")
    output_variable: str = Field(..., description="Variable to store remediated content")
    actions_variable: Optional[str] = Field(
        None, description="Variable to store remediation actions"
    )
    remediation_config: Optional[dict[str, Any]] = Field(
        None, description="Additional remediator configuration"
    )


# Output step specific config
class OutputStepConfig(BaseStepConfig):
    """Configuration for an output step that generates files."""

    type: Literal["output"] = Field("output", description="Step type")
    output_mapping: dict[str, str] = Field(
        ..., description="Maps variable names to output filenames"
    )
    output_dir: str = Field(..., description="Directory path for output files")
    output_variable: Optional[str] = Field(None, description="Variable to store output file paths")
    formats: Optional[list[str]] = Field(None, description="Formats to generate for each content")
    format_options: Optional[dict[str, dict[str, Any]]] = Field(
        None, description="Format-specific options"
    )


# Conditional step (future)
class ConditionalStepConfig(BaseStepConfig):
    """Configuration for a conditional step that executes based on a condition."""

    type: Literal["conditional"] = Field("conditional", description="Step type")
    condition: str = Field(..., description="Condition to evaluate")
    if_steps: list[dict[str, Any]] = Field(..., description="Steps to execute if condition is true")
    else_steps: Optional[list[dict[str, Any]]] = Field(
        None, description="Steps to execute if condition is false"
    )


# Loop step (future)
class LoopStepConfig(BaseStepConfig):
    """Configuration for a loop step that executes steps repeatedly."""

    type: Literal["loop"] = Field("loop", description="Step type")
    items_variable: str = Field(..., description="Variable containing items to iterate over")
    item_variable: str = Field(..., description="Variable to store current item")
    steps: list[dict[str, Any]] = Field(..., description="Steps to execute for each item")


# Parallel step (future)
class ParallelStepConfig(BaseStepConfig):
    """Configuration for a parallel step that executes steps concurrently."""

    type: Literal["parallel"] = Field("parallel", description="Step type")
    steps: list[dict[str, Any]] = Field(..., description="Steps to execute in parallel")
    max_concurrency: Optional[int] = Field(None, description="Maximum number of concurrent steps")


# Union type for any step type
StepConfig = Union[
    PromptStepConfig,
    ValidationStepConfig,
    RemediationStepConfig,
    OutputStepConfig,
    ConditionalStepConfig,
    LoopStepConfig,
    ParallelStepConfig,
]


# The full workflow config
class WorkflowConfig(BaseModel):
    """Configuration for a complete workflow."""

    name: str = Field(..., description="Unique identifier for the workflow")
    description: str = Field(..., description="Description of what the workflow does")
    defaults: Optional[dict[str, Any]] = Field(None, description="Default values for steps")
    steps: list[StepConfig] = Field(..., description="List of steps to execute")

    @root_validator(pre=True)
    def parse_steps(cls, values):
        """Parse steps based on their type before validation."""
        if "steps" not in values:
            return values

        raw_steps = values["steps"]
        parsed_steps = []

        for step in raw_steps:
            if not isinstance(step, dict):
                raise ValueError(f"Step must be a dictionary: {step}")

            # Placeholder for step type detection, will be used in future implementation
            _step_type = step.get("type", "prompt")

            # Apply defaults if they exist
            if "defaults" in values and values["defaults"] is not None:
                effective_step = values["defaults"].copy()
                effective_step.update(step)
            else:
                effective_step = step

            parsed_steps.append(effective_step)

        values["steps"] = parsed_steps
        return values

    # Add min length validator to ensure at least one step
    @validator("steps")
    def validate_steps_not_empty(cls, steps):
        """Validate that the workflow has at least one step."""
        if not steps:
            raise ValueError("Workflow must have at least one step")
        return steps

    class Config:
        """Configuration for the Pydantic model."""

        extra = "forbid"  # Don't allow extra fields
        schema_extra = {
            "example": {
                "name": "minimal_educational_module",
                "description": "Generates a basic educational module",
                "defaults": {"llm_model_alias": "default_smart", "output_format": "raw"},
                "steps": [
                    {
                        "name": "course_overview",
                        "type": "prompt",
                        "prompt": "course/overview.txt",
                        "output_variable": "course_overview",
                    },
                    {
                        "name": "validate_content",
                        "type": "validation",
                        "content_variable": "course_overview",
                        "validators": ["readability", "structure"],
                        "output_variable": "validation_issues",
                    },
                ],
            }
        }
