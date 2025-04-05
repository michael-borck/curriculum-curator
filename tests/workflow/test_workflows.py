"""Unit tests for workflow configuration loading and discovery."""


from curriculum_curator.workflow.workflows import (
    find_workflow_configs,
    get_workflow_config,
    load_workflow_config,
)

VALID_WORKFLOW_YAML = """
name: test_yaml_workflow
description: A test workflow loaded from YAML
steps:
  - name: step1
    type: prompt
    prompt: test/prompt.txt
    output_variable: result1
  - name: step2
    type: validation
    content_variable: result1
    validators: ["readability"]
    output_variable: validation_issues
"""

INVALID_WORKFLOW_YAML = """
name: invalid_workflow
description: An invalid workflow missing required fields
steps:
  - name: step1
    type: prompt
    # Missing required prompt field
    output_variable: result1
"""

WORKFLOW_WITH_DEFAULTS_YAML = """
name: workflow_with_defaults
description: A workflow with defaults
defaults:
  llm_model_alias: default_model
  output_format: json
steps:
  - name: step1
    type: prompt
    prompt: test/prompt.txt
    output_variable: result1
  - name: step2
    type: prompt
    prompt: test/prompt2.txt
    output_variable: result2
    llm_model_alias: override_model  # Override default
"""


class TestWorkflowLoading:
    """Test cases for loading workflow configurations from YAML."""

    def test_load_valid_workflow(self, tmp_path):
        """Test loading a valid workflow configuration from YAML."""
        # Create a temporary workflow file
        workflow_path = tmp_path / "valid_workflow.yaml"
        workflow_path.write_text(VALID_WORKFLOW_YAML)

        # Load and validate the workflow
        workflow = load_workflow_config(workflow_path)

        assert workflow is not None
        assert workflow.name == "test_yaml_workflow"
        assert workflow.description == "A test workflow loaded from YAML"
        assert len(workflow.steps) == 2
        assert workflow.steps[0].type == "prompt"
        assert workflow.steps[1].type == "validation"

    def test_load_invalid_workflow(self, tmp_path):
        """Test loading an invalid workflow configuration from YAML."""
        # Create a temporary workflow file with errors
        workflow_path = tmp_path / "invalid_workflow.yaml"
        workflow_path.write_text(INVALID_WORKFLOW_YAML)

        # Load should return None for invalid configuration
        workflow = load_workflow_config(workflow_path)
        assert workflow is None

    def test_load_workflow_with_defaults(self, tmp_path):
        """Test loading a workflow with defaults from YAML."""
        # Create a temporary workflow file with defaults
        workflow_path = tmp_path / "workflow_with_defaults.yaml"
        workflow_path.write_text(WORKFLOW_WITH_DEFAULTS_YAML)

        # Load and validate the workflow
        workflow = load_workflow_config(workflow_path)

        assert workflow is not None
        assert workflow.name == "workflow_with_defaults"

        # Check that defaults are applied to step1
        step1 = workflow.steps[0]
        assert step1.llm_model_alias == "default_model"
        assert step1.output_format == "json"

        # Check that step2 overrides the default
        step2 = workflow.steps[1]
        assert step2.llm_model_alias == "override_model"
        assert step2.output_format == "json"  # This default should still apply


class TestWorkflowDiscovery:
    """Test cases for discovering workflow configurations."""

    def test_find_workflow_configs(self, tmp_path):
        """Test finding workflow configurations in a directory."""
        # Create test workflows in a temporary directory
        workflows_dir = tmp_path / "workflows"
        workflows_dir.mkdir()

        # Create some workflow files
        (workflows_dir / "workflow1.yaml").write_text(VALID_WORKFLOW_YAML)
        (workflows_dir / "workflow2.yaml").write_text(WORKFLOW_WITH_DEFAULTS_YAML)
        (workflows_dir / "invalid.yaml").write_text(INVALID_WORKFLOW_YAML)
        (workflows_dir / "not_yaml.txt").write_text("This is not a YAML file")

        # Find workflows in the directory
        workflows = find_workflow_configs(str(workflows_dir))

        # Should find the two valid workflows
        assert len(workflows) == 2
        assert "test_yaml_workflow" in workflows
        assert "workflow_with_defaults" in workflows
        assert "invalid_workflow" not in workflows

    def test_get_workflow_config(self, tmp_path, monkeypatch):
        """Test getting a workflow configuration by name."""
        # Create test workflows in temporary directories
        examples_dir = tmp_path / "examples" / "workflows"
        examples_dir.mkdir(parents=True)

        user_dir = tmp_path / "workflows"
        user_dir.mkdir()

        # Create workflow files in both directories
        (examples_dir / "example.yaml").write_text(VALID_WORKFLOW_YAML)
        (user_dir / "user.yaml").write_text(WORKFLOW_WITH_DEFAULTS_YAML)

        # Patch the default directories to use our test directories
        monkeypatch.setattr(
            "curriculum_curator.workflow.workflows.find_workflow_configs",
            lambda dir="": find_workflow_configs(
                str(examples_dir if dir == "examples/workflows" else user_dir)
            ),
        )

        # Get workflows by name
        example_workflow = get_workflow_config("test_yaml_workflow")
        user_workflow = get_workflow_config("workflow_with_defaults")

        # Check that correct workflows are found
        assert example_workflow is not None
        assert example_workflow["name"] == "test_yaml_workflow"

        assert user_workflow is not None
        assert user_workflow["name"] == "workflow_with_defaults"

        # Non-existent workflow should return None
        assert get_workflow_config("nonexistent") is None
