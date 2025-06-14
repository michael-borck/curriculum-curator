"""Tests for the configuration utilities."""

import os
import tempfile

import pytest
import yaml

from curriculum_curator.config.utils import find_config_file, load_config


def test_find_config_file():
    """Test finding the configuration file."""
    # Create a temporary config file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".yaml") as temp:
        temp.write(b"test: config")
        temp_path = temp.name

    try:
        # Test finding the config file with a specific path
        assert find_config_file(temp_path) == temp_path

        # Test finding a non-existent file - explicitly pass a non-existent path
        non_existent_path = "/non_existent_path_that_should_not_exist.yaml"
        with pytest.raises(FileNotFoundError):
            find_config_file(non_existent_path)
    finally:
        # Clean up the temporary file
        os.unlink(temp_path)


def test_load_config():
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
        config = load_config(temp.name)

        # Check if the configuration was loaded correctly
        assert config.llm.default_provider == "test_provider"
        assert "test_provider" in config.llm.providers
        assert config.llm.providers["test_provider"].default_model == "test_model"
    finally:
        # Clean up the temporary file
        os.unlink(temp.name)


def test_load_config_error():
    """Test handling of errors when loading configuration."""
    # Create a temporary file with invalid YAML
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".yaml") as temp:
        temp.write("invalid: yaml: :")

    try:
        # Try to load the invalid configuration
        with pytest.raises(Exception):
            load_config(temp.name)
    finally:
        # Clean up the temporary file
        os.unlink(temp.name)
