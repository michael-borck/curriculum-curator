#!/usr/bin/env python
"""Workflow Configuration Validator

This script validates workflow configuration files using the Pydantic models.
It provides detailed error messages for invalid configurations.

Usage:
    python -m curriculum_curator.tools.validate_workflow path/to/workflow.yaml
    python -m curriculum_curator.tools.validate_workflow --all
"""

import argparse
import sys
from pathlib import Path

from curriculum_curator.workflow.workflows import load_workflow_config


def validate_file(path: str) -> bool:
    """Validate a single workflow configuration file.

    Args:
        path (str): Path to the workflow YAML file

    Returns:
        bool: True if valid, False otherwise
    """
    print(f"Validating workflow configuration: {path}")

    try:
        with open(path) as f:
            config_content = f.read()

        # First just print the raw content for reference
        print("\nConfiguration content:")
        print("-" * 50)
        print(config_content)
        print("-" * 50)

        # Then validate it
        workflow_config = load_workflow_config(path)

        if workflow_config:
            print("\n✅ Configuration is valid!")
            print(f"  - Name: {workflow_config.name}")
            print(f"  - Description: {workflow_config.description}")
            print(f"  - Step count: {len(workflow_config.steps)}")

            # Print step types
            step_types = {}
            for step in workflow_config.steps:
                step_type = step.type
                step_types[step_type] = step_types.get(step_type, 0) + 1

            print("  - Step types:")
            for step_type, count in step_types.items():
                print(f"      - {step_type}: {count}")

            return True
        else:
            print("\n❌ Failed to validate configuration")
            return False

    except FileNotFoundError:
        print(f"\n❌ File not found: {path}")
        return False
    except Exception as e:
        print(f"\n❌ Error validating configuration: {e}")
        return False


def validate_all_workflows() -> list[str]:
    """Validate all discovered workflow configurations.

    Returns:
        List[str]: List of invalid workflow paths
    """
    invalid_paths = []

    # Check built-in examples
    examples_dir = Path("examples/workflows")
    if examples_dir.exists():
        print(f"\nValidating workflows in {examples_dir}:")
        yaml_files = list(examples_dir.glob("*.yaml")) + list(examples_dir.glob("*.yml"))
        for yaml_file in yaml_files:
            if not validate_file(str(yaml_file)):
                invalid_paths.append(str(yaml_file))

    # Check current directory workflows
    workflows_dir = Path("workflows")
    if workflows_dir.exists():
        print(f"\nValidating workflows in {workflows_dir}:")
        yaml_files = list(workflows_dir.glob("*.yaml")) + list(workflows_dir.glob("*.yml"))
        for yaml_file in yaml_files:
            if not validate_file(str(yaml_file)):
                invalid_paths.append(str(yaml_file))

    return invalid_paths


def main() -> int:
    """Main entry point for the validator."""
    parser = argparse.ArgumentParser(description="Validate workflow configuration files")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("file", nargs="?", help="Path to workflow configuration file")
    group.add_argument("--all", action="store_true", help="Validate all discovered workflows")

    args = parser.parse_args()

    if args.all:
        invalid_paths = validate_all_workflows()

        if invalid_paths:
            print(f"\n❌ Found {len(invalid_paths)} invalid workflow configurations:")
            for path in invalid_paths:
                print(f"  - {path}")
            return 1
        else:
            print("\n✅ All workflow configurations are valid!")
            return 0
    else:
        # Validate single file
        if validate_file(args.file):
            return 0
        else:
            return 1


if __name__ == "__main__":
    sys.exit(main())
