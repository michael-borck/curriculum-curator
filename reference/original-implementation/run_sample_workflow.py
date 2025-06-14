#!/usr/bin/env python3
"""Sample script to run the minimal educational module workflow.
"""

import asyncio
import sys

from curriculum_curator.config.utils import load_config
from curriculum_curator.core import CurriculumCurator

# Define initial context variables for the workflow
INITIAL_CONTEXT = {
    "course_title": "Introduction to Python Programming",
    "course_slug": "intro-python",
    "learning_objectives": [
        "Understand basic Python syntax and data structures",
        "Write simple Python programs using control flow statements",
        "Use functions and modules to organize code",
        "Work with files and handle exceptions",
    ],
    "num_modules": 4,
    "module_id": "module1",
}


async def main():
    """Run the sample workflow."""
    # Load configuration
    config = load_config("config.yaml")

    # Initialize the curriculum curator
    curator = CurriculumCurator(config)

    # Define the workflow to run
    workflow_name = "minimal_educational_module"

    print(f"Running workflow: {workflow_name}")
    print(f"Initial context: {INITIAL_CONTEXT}")

    # Run the workflow
    try:
        result = await curator.run_workflow(workflow_name=workflow_name, variables=INITIAL_CONTEXT)

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
