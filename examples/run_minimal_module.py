#!/usr/bin/env python3
"""
Sample script to run a workflow from a config file.
"""

import asyncio
import sys
from pathlib import Path
import yaml

from curriculum_curator.core import CurriculumCurator
from curriculum_curator.config.utils import load_config

# Define initial context variables for the workflow
INITIAL_CONTEXT = {
    "course_title": "Introduction to Python Programming",
    "course_slug": "intro-python",
    "learning_objectives": [
        "Understand basic Python syntax and data structures",
        "Write simple Python programs using control flow statements",
        "Use functions and modules to organize code",
        "Work with files and handle exceptions"
    ],
    "num_modules": 4,
    "module_id": "module1"
}

async def main():
    """Run the workflow from a config file."""
    # Get the path to the config file
    base_config_path = Path("config.yaml")
    workflow_config_path = Path("examples/workflows/minimal_module.yaml")
    
    # Load the base configuration
    base_config = load_config(base_config_path)
    
    # Load the workflow configuration
    with open(workflow_config_path, 'r') as f:
        workflow_config = yaml.safe_load(f)
    
    # Add the workflow to the configuration
    if not hasattr(base_config, 'workflows'):
        base_config.workflows = {}
    
    # Add our workflow to the config
    base_config.workflows["minimal_educational_module"] = workflow_config
    
    # Initialize the curriculum curator
    curator = CurriculumCurator(base_config)
    
    # Define the workflow to run
    workflow_name = "minimal_educational_module"
    
    print(f"Running workflow from config: {workflow_name}")
    print(f"Workflow config file: {workflow_config_path}")
    print(f"Initial context: {INITIAL_CONTEXT}")
    
    # Run the workflow
    try:
        result = await curator.run_workflow(
            workflow_name=workflow_name,
            variables=INITIAL_CONTEXT
        )
        
        # Print the results
        print("\nWorkflow completed successfully!")
        print(f"Session ID: {result['session_id']}")
        
        # Print output files
        output_files = result["results"].get("generate_outputs", {})
        if output_files:
            print("\nOutput files:")
            for var_name, file_path in output_files.items():
                print(f"  - {var_name}: {file_path}")
        
        return 0
    except Exception as e:
        print(f"Error running workflow: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))