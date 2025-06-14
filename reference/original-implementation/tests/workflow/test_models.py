"""Unit tests for workflow configuration validation models."""

import pytest
from pydantic import ValidationError

from curriculum_curator.workflow.models import (
    OutputStepConfig,
    PromptStepConfig,
    RemediationStepConfig,
    ValidationStepConfig,
    WorkflowConfig,
)

# Valid configuration examples
VALID_PROMPT_STEP = {
    "name": "test_prompt_step",
    "type": "prompt",
    "prompt": "test/prompt.txt",
    "output_variable": "prompt_result",
}

VALID_VALIDATION_STEP = {
    "name": "test_validation_step",
    "type": "validation",
    "content_variable": "content_to_validate",
    "validators": ["readability", "structure"],
    "output_variable": "validation_issues",
}

VALID_REMEDIATION_STEP = {
    "name": "test_remediation_step",
    "type": "remediation",
    "content_variable": "content_to_remediate",
    "issues_variable": "validation_issues",
    "output_variable": "remediated_content",
}

VALID_OUTPUT_STEP = {
    "name": "test_output_step",
    "type": "output",
    "output_mapping": {"variable1": "file1.md", "variable2": "file2.md"},
    "output_dir": "output/test",
}

VALID_WORKFLOW = {
    "name": "test_workflow",
    "description": "A test workflow",
    "steps": [VALID_PROMPT_STEP, VALID_VALIDATION_STEP, VALID_REMEDIATION_STEP, VALID_OUTPUT_STEP],
}


# Test cases for workflow validation
class TestWorkflowConfig:
    """Test cases for workflow configuration validation."""

    def test_valid_workflow(self):
        """Test that a valid workflow configuration passes validation."""
        workflow = WorkflowConfig(**VALID_WORKFLOW)
        assert workflow.name == "test_workflow"
        assert workflow.description == "A test workflow"
        assert len(workflow.steps) == 4

    def test_missing_name(self):
        """Test that a workflow without a name fails validation."""
        invalid_config = VALID_WORKFLOW.copy()
        del invalid_config["name"]

        with pytest.raises(ValidationError) as exc_info:
            WorkflowConfig(**invalid_config)

        error = str(exc_info.value)
        assert "name" in error
        assert "field required" in error

    def test_missing_description(self):
        """Test that a workflow without a description fails validation."""
        invalid_config = VALID_WORKFLOW.copy()
        del invalid_config["description"]

        with pytest.raises(ValidationError) as exc_info:
            WorkflowConfig(**invalid_config)

        error = str(exc_info.value)
        assert "description" in error
        assert "field required" in error

    def test_missing_steps(self):
        """Test that a workflow without steps fails validation."""
        invalid_config = VALID_WORKFLOW.copy()
        del invalid_config["steps"]

        with pytest.raises(ValidationError) as exc_info:
            WorkflowConfig(**invalid_config)

        error = str(exc_info.value)
        assert "steps" in error
        assert "field required" in error

    def test_empty_steps(self):
        """Test that a workflow with empty steps fails validation."""
        invalid_config = VALID_WORKFLOW.copy()
        invalid_config["steps"] = []

        with pytest.raises(ValidationError) as exc_info:
            WorkflowConfig(**invalid_config)

        error = str(exc_info.value)
        assert "steps" in error
        assert "ensure this value has at least 1 item" in error

    def test_workflow_with_defaults(self):
        """Test that a workflow with defaults correctly applies them to steps."""
        config_with_defaults = VALID_WORKFLOW.copy()
        config_with_defaults["defaults"] = {
            "llm_model_alias": "test_model",
            "output_format": "json",
        }

        workflow = WorkflowConfig(**config_with_defaults)

        # First step should have the defaults applied
        prompt_step = workflow.steps[0]
        assert prompt_step.type == "prompt"
        assert prompt_step.llm_model_alias == "test_model"
        assert prompt_step.output_format == "json"


# Test cases for step validation
class TestStepConfigs:
    """Test cases for step configuration validation."""

    def test_valid_prompt_step(self):
        """Test that a valid prompt step passes validation."""
        step = PromptStepConfig(**VALID_PROMPT_STEP)
        assert step.name == "test_prompt_step"
        assert step.type == "prompt"
        assert step.prompt == "test/prompt.txt"
        assert step.output_variable == "prompt_result"
        assert step.output_format == "raw"  # default value

    def test_prompt_step_missing_prompt(self):
        """Test that a prompt step without a prompt fails validation."""
        invalid_step = VALID_PROMPT_STEP.copy()
        del invalid_step["prompt"]

        with pytest.raises(ValidationError) as exc_info:
            PromptStepConfig(**invalid_step)

        error = str(exc_info.value)
        assert "prompt" in error
        assert "field required" in error

    def test_prompt_step_missing_output_variable(self):
        """Test that a prompt step without an output variable fails validation."""
        invalid_step = VALID_PROMPT_STEP.copy()
        del invalid_step["output_variable"]

        with pytest.raises(ValidationError) as exc_info:
            PromptStepConfig(**invalid_step)

        error = str(exc_info.value)
        assert "output_variable" in error
        assert "field required" in error

    def test_prompt_step_invalid_output_format(self):
        """Test that a prompt step with an invalid output format fails validation."""
        invalid_step = VALID_PROMPT_STEP.copy()
        invalid_step["output_format"] = "invalid_format"

        with pytest.raises(ValidationError) as exc_info:
            PromptStepConfig(**invalid_step)

        error = str(exc_info.value)
        assert "output_format" in error
        assert "valid_formats" in error

    def test_valid_validation_step(self):
        """Test that a valid validation step passes validation."""
        step = ValidationStepConfig(**VALID_VALIDATION_STEP)
        assert step.name == "test_validation_step"
        assert step.type == "validation"
        assert step.content_variable == "content_to_validate"
        assert step.validators == ["readability", "structure"]
        assert step.output_variable == "validation_issues"

    def test_validation_step_missing_content_variable(self):
        """Test that a validation step without a content variable fails validation."""
        invalid_step = VALID_VALIDATION_STEP.copy()
        del invalid_step["content_variable"]

        with pytest.raises(ValidationError) as exc_info:
            ValidationStepConfig(**invalid_step)

        error = str(exc_info.value)
        assert "content_variable" in error
        assert "field required" in error

    def test_valid_remediation_step(self):
        """Test that a valid remediation step passes validation."""
        step = RemediationStepConfig(**VALID_REMEDIATION_STEP)
        assert step.name == "test_remediation_step"
        assert step.type == "remediation"
        assert step.content_variable == "content_to_remediate"
        assert step.issues_variable == "validation_issues"
        assert step.output_variable == "remediated_content"

    def test_valid_output_step(self):
        """Test that a valid output step passes validation."""
        step = OutputStepConfig(**VALID_OUTPUT_STEP)
        assert step.name == "test_output_step"
        assert step.type == "output"
        assert step.output_mapping == {"variable1": "file1.md", "variable2": "file2.md"}
        assert step.output_dir == "output/test"

    def test_output_step_missing_output_mapping(self):
        """Test that an output step without an output mapping fails validation."""
        invalid_step = VALID_OUTPUT_STEP.copy()
        del invalid_step["output_mapping"]

        with pytest.raises(ValidationError) as exc_info:
            OutputStepConfig(**invalid_step)

        error = str(exc_info.value)
        assert "output_mapping" in error
        assert "field required" in error
