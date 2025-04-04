import pytest
import os
import yaml
import tempfile
from pathlib import Path


@pytest.fixture
def test_config():
    """Sample configuration for testing."""
    return {
        "system": {
            "persistence_dir": ".curriculum_curator",
            "output_dir": "output",
            "log_level": "INFO"
        },
        "llm": {
            "default_provider": "test_provider",
            "aliases": {
                "test_alias": "test_provider/test_model"
            },
            "providers": {
                "test_provider": {
                    "api_key": "test_api_key",
                    "default_model": "test_model",
                    "cost_per_1k_tokens": {
                        "input": 0.10,
                        "output": 0.20
                    },
                    "models": {
                        "test_model": {}
                    }
                }
            }
        },
        "prompts": {
            "base_path": "./prompts"
        },
        "validation": {
            "similarity": {
                "threshold": 0.85
            }
        },
        "workflows": {
            "test_workflow": {
                "description": "Test workflow",
                "steps": [
                    {
                        "name": "test_step",
                        "type": "prompt",
                        "prompt": "test/prompt.txt",
                        "output_variable": "test_output"
                    }
                ]
            }
        }
    }


@pytest.fixture
def temp_dir():
    """Creates a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def temp_prompts_dir(temp_dir):
    """Creates a temporary prompts directory with test prompt files."""
    prompts_dir = temp_dir / "prompts" / "test"
    prompts_dir.mkdir(parents=True, exist_ok=True)
    
    # Create a test prompt file
    prompt_file = prompts_dir / "prompt.txt"
    prompt_content = """---
description: Test prompt
requires:
  - test_var
tags:
  - test
version: 1.0
---
This is a test prompt with {test_var}."""
    
    prompt_file.write_text(prompt_content)
    
    return prompts_dir.parent  # Return the top-level prompts directory