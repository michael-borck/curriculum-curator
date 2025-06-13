"""Utility functions for loading workflow configurations."""

import glob
from pathlib import Path
from typing import Any, Optional, Union

import structlog
import yaml
from pydantic import ValidationError

from curriculum_curator.workflow.models import WorkflowConfig

logger = structlog.get_logger()


def load_workflow_config(yaml_path: str) -> Optional[WorkflowConfig]:
    """Load and validate a workflow configuration from a YAML file.

    Args:
        yaml_path (str): Path to the YAML configuration file

    Returns:
        Optional[WorkflowConfig]: The validated workflow configuration or None if invalid
    """
    try:
        with open(yaml_path) as f:
            raw_config = yaml.safe_load(f)

        # Validate with Pydantic
        workflow_config = WorkflowConfig(**raw_config)
        logger.info(
            "workflow_config_loaded",
            path=yaml_path,
            name=workflow_config.name,
            step_count=len(workflow_config.steps),
        )
        return workflow_config
    except ValidationError as e:
        logger.error("workflow_config_validation_error", path=yaml_path, error=str(e))
        return None
    except Exception as e:
        logger.error("workflow_config_load_error", path=yaml_path, error=str(e))
        return None


def find_workflow_configs(directory: str = "examples/workflows") -> dict[str, WorkflowConfig]:
    """Find and validate workflow configuration files in the specified directory.

    Args:
        directory (str): Directory to search for workflow configs

    Returns:
        dict: Dictionary of workflow name to validated configuration
    """
    workflows = {}

    # Ensure the directory exists
    path = Path(directory)
    if not path.exists():
        return workflows

    # Find all YAML files in the directory
    yaml_files = glob.glob(str(path / "*.yaml")) + glob.glob(str(path / "*.yml"))

    # Load and validate each file
    for yaml_file in yaml_files:
        config = load_workflow_config(yaml_file)
        if config:
            workflows[config.name] = config

    logger.info(
        "workflow_configs_discovered",
        directory=directory,
        count=len(workflows),
        workflows=list(workflows.keys()),
    )
    return workflows


def get_workflow_config(workflow_name: str) -> Optional[Union[WorkflowConfig, dict[str, Any]]]:
    """Get a workflow configuration by name.

    Args:
        workflow_name (str): Name of the workflow

    Returns:
        Optional[Union[WorkflowConfig, Dict[str, Any]]]: Workflow configuration or None if not found
    """
    # First, check for built-in examples directory
    workflows = find_workflow_configs()

    # If workflow not found, check current directory
    if workflow_name not in workflows:
        current_dir_workflows = find_workflow_configs("workflows")
        workflows.update(current_dir_workflows)

    workflow = workflows.get(workflow_name)

    # Return as dict for backward compatibility
    if workflow:
        return workflow.dict()

    return None
