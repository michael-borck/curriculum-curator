import pytest
import frontmatter
from pathlib import Path

from curriculum_curator.prompt.registry import PromptRegistry


class TestPromptRegistry:
    """Tests for the PromptRegistry class."""

    def test_init(self, temp_prompts_dir):
        """Test PromptRegistry initialization."""
        registry = PromptRegistry(temp_prompts_dir)
        assert registry.base_path == temp_prompts_dir
        assert registry.prompt_cache == {}

    def test_get_prompt(self, temp_prompts_dir):
        """Test getting a prompt by path."""
        registry = PromptRegistry(temp_prompts_dir)
        prompt_data = registry.get_prompt("test/prompt.txt")
        
        assert "content" in prompt_data
        assert "metadata" in prompt_data
        assert prompt_data["content"] == "This is a test prompt with {test_var}."
        assert prompt_data["metadata"]["description"] == "Test prompt"
        assert prompt_data["metadata"]["requires"] == ["test_var"]
        assert prompt_data["metadata"]["tags"] == ["test"]
        # Handle float or string version - convert both to string for comparison
        assert str(prompt_data["metadata"]["version"]) == "1.0"

    def test_get_prompt_from_cache(self, temp_prompts_dir):
        """Test getting a prompt from cache."""
        registry = PromptRegistry(temp_prompts_dir)
        
        # First call should load from file
        prompt_data1 = registry.get_prompt("test/prompt.txt")
        
        # Modify the cache to verify it's being used
        registry.prompt_cache["test/prompt.txt"]["metadata"]["test_cache"] = True
        
        # Second call should load from cache
        prompt_data2 = registry.get_prompt("test/prompt.txt")
        
        assert "test_cache" in prompt_data2["metadata"]
        assert prompt_data2["metadata"]["test_cache"] is True

    def test_get_prompt_not_found(self, temp_prompts_dir):
        """Test handling of non-existent prompt files."""
        registry = PromptRegistry(temp_prompts_dir)
        
        with pytest.raises(FileNotFoundError):
            registry.get_prompt("nonexistent/prompt.txt")

    def test_list_prompts(self, temp_prompts_dir):
        """Test listing all prompts."""
        registry = PromptRegistry(temp_prompts_dir)
        prompts = registry.list_prompts()
        
        assert "test/prompt.txt" in prompts
        assert len(prompts) == 1

    def test_list_prompts_with_tag(self, temp_prompts_dir):
        """Test listing prompts filtered by tag."""
        registry = PromptRegistry(temp_prompts_dir)
        
        # Test with matching tag
        prompts = registry.list_prompts(tag="test")
        assert "test/prompt.txt" in prompts
        assert len(prompts) == 1
        
        # Test with non-matching tag
        prompts = registry.list_prompts(tag="nonexistent")
        assert len(prompts) == 0

    def test_clear_cache(self, temp_prompts_dir):
        """Test clearing the prompt cache."""
        registry = PromptRegistry(temp_prompts_dir)
        
        # Load a prompt to populate the cache
        registry.get_prompt("test/prompt.txt")
        assert "test/prompt.txt" in registry.prompt_cache
        
        # Clear the cache
        registry.clear_cache()
        assert registry.prompt_cache == {}

    def test_get_prompt_metadata(self, temp_prompts_dir):
        """Test getting only the metadata for a prompt."""
        registry = PromptRegistry(temp_prompts_dir)
        metadata = registry.get_prompt_metadata("test/prompt.txt")
        
        assert "description" in metadata
        assert metadata["description"] == "Test prompt"
        assert "requires" in metadata
        assert metadata["requires"] == ["test_var"]