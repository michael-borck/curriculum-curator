"""Tests for the workflow builder."""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import yaml

from curriculum_curator.workflow.builder import WorkflowBuilder


class TestWorkflowBuilder:
    """Tests for the WorkflowBuilder class."""

    def test_init(self):
        """Test initialization of the workflow builder."""
        builder = WorkflowBuilder()

        # Check default workflow template
        assert builder.workflow["name"] == ""
        assert builder.workflow["description"] == ""
        assert builder.workflow["defaults"] == {}
        assert builder.workflow["steps"] == []

        # Check available components lists
        assert isinstance(builder.available_validators, list)
        assert isinstance(builder.available_remediators, list)

    def test_load_base(self):
        """Test loading a base workflow."""
        # Create a temporary workflow file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(
                {
                    "name": "test_workflow",
                    "description": "Test workflow",
                    "defaults": {"llm_model_alias": "test_model"},
                    "steps": [
                        {
                            "name": "generate_content",
                            "type": "prompt",
                            "prompt": "test/prompt.txt",
                            "output_variable": "content",
                        }
                    ],
                },
                f,
            )

        try:
            # Load the workflow
            builder = WorkflowBuilder()
            builder.load_base(f.name)

            # Check loaded workflow
            assert builder.workflow["name"] == "test_workflow"
            assert builder.workflow["description"] == "Test workflow"
            assert builder.workflow["defaults"] == {"llm_model_alias": "test_model"}
            assert len(builder.workflow["steps"]) == 1
            assert builder.workflow["steps"][0]["name"] == "generate_content"
        finally:
            os.unlink(f.name)

    def test_save(self):
        """Test saving a workflow."""
        builder = WorkflowBuilder()

        # Set up a workflow
        builder.workflow = {
            "name": "test_save",
            "description": "Test save workflow",
            "defaults": {},
            "steps": [
                {
                    "name": "generate_content",
                    "type": "prompt",
                    "prompt": "test/prompt.txt",
                    "output_variable": "content",
                }
            ],
        }

        # Create a temporary file to save to
        with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as f:
            pass

        try:
            # Mock validation to always succeed
            with patch.object(builder, "_validate_workflow", return_value=True):
                builder.save(Path(f.name))

                # Check the saved file
                with open(f.name) as saved_file:
                    saved_workflow = yaml.safe_load(saved_file)

                    assert saved_workflow["name"] == "test_save"
                    assert saved_workflow["description"] == "Test save workflow"
                    assert len(saved_workflow["steps"]) == 1
                    assert saved_workflow["steps"][0]["name"] == "generate_content"
        finally:
            os.unlink(f.name)

    def test_validate_workflow(self):
        """Test workflow validation."""
        builder = WorkflowBuilder()

        # Set up an invalid workflow (missing required fields)
        builder.workflow = {
            "name": "",  # Empty name is invalid
            "description": "Test validation",
            "defaults": {},
            "steps": [],  # Empty steps is invalid
        }

        # Check validation fails
        assert builder._validate_workflow() is False

        # Set up a valid workflow
        builder.workflow = {
            "name": "test_validation",
            "description": "Test validation",
            "defaults": {},
            "steps": [
                {
                    "name": "generate_content",
                    "type": "prompt",
                    "prompt": "test/prompt.txt",
                    "output_variable": "content",
                }
            ],
        }

        # Check validation succeeds
        assert builder._validate_workflow() is True
