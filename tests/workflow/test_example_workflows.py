"""Tests for example workflow configurations."""

import pytest
from pathlib import Path

from curriculum_curator.workflow.workflows import load_workflow_config

class TestExampleWorkflows:
    """Test cases for example workflow configurations."""
    
    def test_minimal_module_workflow(self):
        """Test that the minimal module workflow configuration is valid."""
        # Find the examples workflow directory
        # Start from the current file's location and navigate to the repository root
        test_dir = Path(__file__).parent
        repo_root = test_dir.parent.parent
        
        # Try to locate the example workflow file
        workflow_path = repo_root / "examples" / "workflows" / "minimal_module.yaml"
        
        # Skip the test if the file doesn't exist (for CI environments)
        if not workflow_path.exists():
            pytest.skip(f"Example workflow file not found: {workflow_path}")
        
        # Load and validate the workflow
        workflow = load_workflow_config(workflow_path)
        
        # Assertions about the minimal workflow
        assert workflow is not None, "Workflow failed validation"
        assert workflow.name == "minimal_educational_module"
        assert "educational module" in workflow.description.lower()
        assert workflow.defaults is not None, "Workflow should have defaults"
        
        # Check defaults
        assert "llm_model_alias" in workflow.defaults
        assert "output_format" in workflow.defaults
        assert "validators" in workflow.defaults
        
        # Check steps
        assert len(workflow.steps) >= 7, "Should have at least 7 steps"
        
        # Count step types
        step_types = {}
        for step in workflow.steps:
            step_type = step.type
            step_types[step_type] = step_types.get(step_type, 0) + 1
        
        # Verify we have the expected step types
        assert step_types.get("prompt", 0) >= 4, "Should have at least 4 prompt steps"
        assert step_types.get("validation", 0) >= 1, "Should have at least 1 validation step"
        assert step_types.get("remediation", 0) >= 1, "Should have at least 1 remediation step"
        assert step_types.get("output", 0) >= 1, "Should have at least 1 output step"
        
        # Check for specific steps by name
        step_names = [step.name for step in workflow.steps]
        assert "course_overview" in step_names
        assert "module_outline" in step_names
        assert "lecture_content" in step_names
        assert "validate_lecture" in step_names
        assert "remediate_lecture" in step_names
        assert "generate_outputs" in step_names