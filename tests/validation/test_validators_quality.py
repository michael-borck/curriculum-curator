"""Tests for quality validators."""

import pytest
from types import SimpleNamespace

from curriculum_curator.validation.validators.quality.readability import ReadabilityValidator
from curriculum_curator.validation.validators.quality.structure import StructureValidator
from curriculum_curator.validation.validators.quality.similarity import SimilarityValidator


class TestStructureValidator:
    """Tests for structure validator."""
    
    @pytest.fixture
    def validator(self):
        """Create a structure validator with test configuration."""
        config = SimpleNamespace(
            min_sections=3,
            required_sections=["Introduction", "Content", "Summary"]
        )
        return StructureValidator(config)
    
    @pytest.mark.asyncio
    async def test_valid_structure(self, validator):
        """Test validation with valid structure."""
        content = """
# Introduction

This is the introduction.

# Main Content

This is the main content.

# Summary

This is the summary.

# Additional Information

This is additional information.
"""
        result = await validator.validate(content)
        assert result["valid"] is True
        assert len(result["sections_found"]) == 4
    
    @pytest.mark.asyncio
    async def test_missing_sections(self, validator):
        """Test validation with missing required sections."""
        content = """
# Introduction

This is the introduction.

# Main Content

This is the main content.

# Additional Information

This is additional information.
"""
        result = await validator.validate(content)
        assert result["valid"] is False
        assert "Summary" in result["issues"][0]["missing_sections"]
    
    @pytest.mark.asyncio
    async def test_too_few_sections(self, validator):
        """Test validation with too few sections."""
        content = """
# Introduction

This is the introduction.

# Main Content

This is the main content.
"""
        result = await validator.validate(content)
        assert result["valid"] is False
        assert len(result["sections_found"]) == 2
        assert result["issues"][0]["issue"] == "min_sections"


class TestReadabilityValidator:
    """Tests for readability validator."""
    
    @pytest.fixture
    def validator(self):
        """Create a readability validator with test configuration."""
        config = SimpleNamespace(
            max_avg_sentence_length=15,
            min_flesch_reading_ease=70.0
        )
        return ReadabilityValidator(config)
    
    @pytest.mark.asyncio
    async def test_readability_validation(self, validator):
        """Test readability validation."""
        # This is a placeholder test since the validator uses a stub implementation
        content = "This is a sample text. It has short sentences. The readability should be good."
        result = await validator.validate(content)
        
        # Since we're using stubs, we expect the validation to always pass
        assert result["valid"] is True
        assert "metrics" in result
    
    def test_get_remediation_hints(self, validator):
        """Test remediation hints for readability validation."""
        # Create a mock validation result with readability issues
        validation_result = {
            "valid": False,
            "issues": [
                {"issue": "sentence_length", "value": 25, "threshold": 15},
                {"issue": "reading_ease", "value": 50, "threshold": 70}
            ]
        }
        
        hints = validator.get_remediation_hints(validation_result)
        assert hints["can_remediate"] is True
        assert len(hints["hints"]) > 0
        
        # Valid result should have no remediation hints
        valid_result = {"valid": True}
        hints = validator.get_remediation_hints(valid_result)
        assert hints["can_remediate"] is False
        assert len(hints["hints"]) == 0


class TestSimilarityValidator:
    """Tests for similarity validator."""
    
    @pytest.fixture
    def validator(self):
        """Create a similarity validator with test configuration."""
        config = SimpleNamespace(
            threshold=0.85,
            model="all-MiniLM-L6-v2"
        )
        return SimilarityValidator(config)
    
    @pytest.mark.asyncio
    async def test_similarity_validation(self, validator):
        """Test similarity validation."""
        # This is a placeholder test since the validator uses a stub implementation
        content = "This is a sample text that should be unique."
        result = await validator.validate(content)
        
        # Since we're using stubs, we expect the validation to always pass
        assert result["valid"] is True