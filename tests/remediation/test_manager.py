"""Tests for the RemediationManager."""

import pytest
from typing import Dict, Any, List
import os
import tempfile
import yaml

from curriculum_curator.remediation.manager import RemediationManager
from curriculum_curator.validation.manager import ValidationIssue
from curriculum_curator.config.models import AppConfig


@pytest.fixture
def sample_config():
    """Create a sample configuration with remediation settings."""
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
        "remediation": {
            "auto_fix": {
                "format_corrector": {
                    "enabled": True,
                    "aggressive": False
                },
                "sentence_splitter": {
                    "enabled": True,
                    "max_sentence_length": 20
                }
            },
            "rewrite": {
                "rephrasing_prompter": {
                    "enabled": True,
                    "llm_model_alias": "test_model"
                }
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
def remediation_manager(sample_config):
    """Create a RemediationManager instance with the sample config."""
    return RemediationManager(sample_config)


@pytest.fixture
def sample_validation_issues():
    """Create sample validation issues for testing remediation."""
    return [
        ValidationIssue(
            severity="warning",
            message="Sentences are too long",
            location="paragraph_1",
            remediation_type="auto_fix.sentence_splitter"
        ),
        ValidationIssue(
            severity="error",
            message="Content structure is inconsistent",
            location="document",
            remediation_type="auto_fix.format_corrector"
        ),
        ValidationIssue(
            severity="error",
            message="Technical language is too complex for target audience",
            location="section_3",
            remediation_type="rewrite.rephrasing_prompter"
        )
    ]


class TestRemediationManager:
    """Tests for the RemediationManager class."""
    
    def test_init(self, remediation_manager):
        """Test RemediationManager initialization."""
        assert remediation_manager is not None
        assert len(remediation_manager.remediators) > 0
        
        # Check that remediators were registered correctly
        assert "auto_fix.format_corrector" in remediation_manager.remediators
        assert "auto_fix.sentence_splitter" in remediation_manager.remediators
        assert "rewrite.rephrasing_prompter" in remediation_manager.remediators
    
    @pytest.mark.asyncio
    async def test_remediate_content(self, remediation_manager, sample_validation_issues):
        """Test remediating content based on validation issues."""
        content = """
        This is a very long sentence that exceeds the maximum allowed sentence length and should be split into smaller sentences by the sentence splitter remediator because it's hard to read.
        
        The structure of this document is inconsistent and needs to be fixed.
        
        This section contains complex technical language that needs to be simplified for the target audience.
        """
        
        result = await remediation_manager.remediate_content(content, sample_validation_issues)
        
        # Check the structure of the result
        assert isinstance(result, dict)
        assert "content" in result
        assert "actions" in result
        assert "stats" in result
        
        # The content should be different after remediation
        assert result["content"] != content
        
        # There should be an action for each issue
        assert len(result["actions"]) > 0
    
    @pytest.mark.asyncio
    async def test_remediate_with_specific_remediators(self, remediation_manager):
        """Test remediating content with specific remediators."""
        content = """
        This is a very long sentence that exceeds the maximum allowed sentence length and should be split into smaller sentences by the sentence splitter remediator because it's hard to read.
        """
        
        # Create a remediation configuration
        config = {
            "remediators": ["auto_fix.sentence_splitter"],
            "options": {
                "auto_fix.sentence_splitter": {
                    "max_sentence_length": 15
                }
            }
        }
        
        result = await remediation_manager.remediate_content(content, [], config)
        
        # Check the structure of the result
        assert isinstance(result, dict)
        assert "content" in result
        assert "actions" in result
        
        # The content should be different after remediation with the sentence splitter
        assert result["content"] != content
    
    @pytest.mark.asyncio
    async def test_get_appropriate_remediators(self, remediation_manager, sample_validation_issues):
        """Test getting appropriate remediators for issues."""
        remediators = remediation_manager.get_appropriate_remediators(sample_validation_issues)
        
        # Should include all remediator types from the issues
        assert "auto_fix.sentence_splitter" in remediators
        assert "auto_fix.format_corrector" in remediators
        assert "rewrite.rephrasing_prompter" in remediators
    
    @pytest.mark.asyncio
    async def test_no_remediation_needed(self, remediation_manager):
        """Test remediation when no issues are present."""
        content = "This is perfect content that needs no remediation."
        
        result = await remediation_manager.remediate_content(content, [])
        
        # Content should remain unchanged
        assert result["content"] == content
        assert len(result["actions"]) == 0