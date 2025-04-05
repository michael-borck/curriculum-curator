"""Tests for the ValidationManager."""

import pytest
from typing import Dict, Any
import os
import tempfile
import yaml

from curriculum_curator.validation.manager import ValidationManager
from curriculum_curator.config.models import AppConfig, ValidationConfig


@pytest.fixture
def sample_config():
    """Create a sample configuration with validation settings."""
    config_dict = {
        "system": {"persistence_dir": ".test_curator"},
        "llm": {
            "default_provider": "test_provider",
            "providers": {
                "test_provider": {
                    "default_model": "test_model",
                    "models": {"test_model": {}}
                }
            }
        },
        "validation": {
            "structure": {
                "article": {
                    "min_sections": 3,
                    "required_sections": ["Introduction", "Body", "Conclusion"]
                },
                "assessment": {
                    "min_sections": 2,
                    "required_sections": ["Questions", "Answers"]
                }
            },
            "readability": {
                "max_avg_sentence_length": 20,
                "min_flesch_reading_ease": 60.0
            }
        }
    }
    
    # Create a temporary config file
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".yaml") as temp:
        yaml.dump(config_dict, temp)
        temp_path = temp.name
    
    try:
        # Load as AppConfig
        config = AppConfig.model_validate(config_dict)
        yield config
    finally:
        # Clean up
        os.unlink(temp_path)


@pytest.fixture
def validation_manager(sample_config):
    """Create a ValidationManager instance with the sample config."""
    return ValidationManager(sample_config)


class TestValidationManager:
    """Tests for the ValidationManager class."""
    
    def test_init(self, validation_manager):
        """Test ValidationManager initialization."""
        assert validation_manager is not None
        assert len(validation_manager.validators) > 0
        assert "structure_article" in validation_manager.validators
        assert "structure_assessment" in validation_manager.validators
        assert "readability" in validation_manager.validators
    
    @pytest.mark.asyncio
    async def test_validate_structure(self, validation_manager):
        """Test validating content structure."""
        content = """
# Introduction

This is the introduction.

# Body

This is the main body of the article.

# Conclusion

This is the conclusion.
"""

        result = await validation_manager.validate(content, ["structure_article"])
        assert isinstance(result, list)
        assert len(result) == 0  # No issues because the structure is valid
    
    @pytest.mark.asyncio
    async def test_validate_invalid_structure(self, validation_manager):
        """Test validating content with invalid structure."""
        content = """
# Introduction

This is the introduction.

# Body

This is the main body of the article.
"""

        result = await validation_manager.validate(content, ["structure_article"])
        assert isinstance(result, list)
        assert len(result) > 0  # Should have issues because "Conclusion" is missing
    
    @pytest.mark.asyncio
    async def test_validate_multiple(self, validation_manager):
        """Test validating content with multiple validators."""
        content = """
# Introduction

This is the introduction.

# Body

This is the main body of the article.

# Conclusion

This is the conclusion.
"""

        result = await validation_manager.validate(content, ["structure_article", "readability"])
        assert isinstance(result, list)
        # May have issues depending on the readability implementation
        # (currently a stub that always passes)
    
    @pytest.mark.asyncio
    async def test_validate_with_context(self, validation_manager):
        """Test validating content with context."""
        content = """
# Questions

1. What is the capital of France?
2. What is the largest planet in our solar system?

# Answers

1. Paris
2. Jupiter
"""

        context = {
            "content_type": "assessment",
            "previous_sections": {
                "introduction": "This is an introduction to the test."
            }
        }

        result = await validation_manager.validate(content, ["structure_assessment"], context)
        assert isinstance(result, list)
        assert len(result) == 0  # No issues expected