"""Tests for the configuration models."""

import os
import tempfile
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from curriculum_curator.config.models import (
    AppConfig,
    LLMConfig,
    LLMProviderConfig,
    WorkflowStepConfig,
)


class TestLLMProviderConfig:
    """Tests for the LLMProviderConfig model."""

    def test_api_key_resolution(self):
        """Test API key resolution from environment variables."""
        # Set an environment variable for testing
        os.environ["TEST_API_KEY"] = "test_key_value"

        # Create a configuration with an environment variable reference
        config = LLMProviderConfig(
            api_key="env(TEST_API_KEY)",
            default_model="test_model",
        )

        # Check if the API key was resolved correctly
        assert config.api_key == "test_key_value"

    def test_default_cost(self):
        """Test default cost per 1k tokens."""
        config = LLMProviderConfig(
            default_model="test_model",
        )

        # Check if default costs are set
        assert config.cost_per_1k_tokens.input == 0.0
        assert config.cost_per_1k_tokens.output == 0.0


class TestWorkflowStepConfig:
    """Tests for the WorkflowStepConfig model."""

    def test_prompt_step_validation(self):
        """Test validation of prompt steps."""
        # Valid prompt step
        valid_step = WorkflowStepConfig(
            name="test_step",
            type="prompt",
            prompt="test/prompt.txt",
        )
        assert valid_step.prompt == "test/prompt.txt"

        # Invalid prompt step (missing prompt)
        with pytest.raises(ValidationError):
            WorkflowStepConfig(
                name="test_step",
                type="prompt",
            )

    def test_validation_step_validation(self):
        """Test validation of validation steps."""
        # Valid validation step
        valid_step = WorkflowStepConfig(
            name="test_step",
            type="validation",
            validators=["similarity", "structure"],
        )
        assert valid_step.validators == ["similarity", "structure"]

        # Invalid validation step (missing validators)
        with pytest.raises(ValidationError):
            WorkflowStepConfig(
                name="test_step",
                type="validation",
            )

    def test_output_step_validation(self):
        """Test validation of output steps."""
        # Valid output step
        valid_step = WorkflowStepConfig(
            name="test_step",
            type="output",
            formats=["html", "pdf"],
        )
        assert valid_step.formats == ["html", "pdf"]

        # Invalid output step (missing formats)
        with pytest.raises(ValidationError):
            WorkflowStepConfig(
                name="test_step",
                type="output",
            )


class TestAppConfig:
    """Tests for the AppConfig model."""

    def test_from_file(self):
        """Test loading configuration from a file."""
        # Create a temporary config file
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".yaml") as temp:
            yaml.dump(
                {
                    "llm": {
                        "default_provider": "test_provider",
                        "providers": {
                            "test_provider": {
                                "default_model": "test_model",
                                "models": {"test_model": {}},
                            }
                        },
                    }
                },
                temp,
            )

        try:
            # Load the configuration from the file
            config = AppConfig.from_file(temp.name)

            # Check if the configuration was loaded correctly
            assert config.llm.default_provider == "test_provider"
            assert "test_provider" in config.llm.providers
            assert config.llm.providers["test_provider"].default_model == "test_model"
        finally:
            # Clean up the temporary file
            os.unlink(temp.name)

    def test_default_values(self):
        """Test default values for optional fields."""
        config = AppConfig(
            llm=LLMConfig(
                default_provider="test_provider",
                providers={
                    "test_provider": LLMProviderConfig(
                        default_model="test_model",
                    )
                },
            )
        )

        # Check if default values are set
        assert config.system.persistence_dir == ".curriculum_curator"
        assert config.system.output_dir == "output"
        assert config.system.log_level == "INFO"
        assert config.prompts.base_path == "./prompts"