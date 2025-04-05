from pathlib import Path

import frontmatter
import structlog

logger = structlog.get_logger()


class PromptRegistry:
    """Manages a collection of prompts with YAML front matter for metadata."""

    def __init__(self, base_path):
        """Initialize the prompt registry.

        Args:
            base_path (str or Path): Base directory containing prompt files
        """
        self.base_path = Path(base_path)
        self.prompt_cache = {}

        logger.info("prompt_registry_initialized", base_path=str(self.base_path))

    def get_prompt(self, prompt_path):
        """Get a prompt by its path relative to the base path.

        Args:
            prompt_path (str): Path to the prompt file, relative to base_path

        Returns:
            dict: Dictionary containing the prompt content and metadata

        Raises:
            FileNotFoundError: If the prompt file does not exist
        """
        # Check cache first
        if prompt_path in self.prompt_cache:
            logger.debug("prompt_cache_hit", prompt=prompt_path)
            return self.prompt_cache[prompt_path]

        # Load from file
        full_path = self.base_path / prompt_path
        if not full_path.exists():
            logger.error("prompt_not_found", prompt=prompt_path, full_path=str(full_path))
            raise FileNotFoundError(f"Prompt not found: {prompt_path}")

        try:
            prompt_data = frontmatter.load(full_path)
            self.prompt_cache[prompt_path] = {
                "content": prompt_data.content,
                "metadata": prompt_data.metadata,
            }

            logger.debug(
                "prompt_loaded", prompt=prompt_path, metadata_keys=list(prompt_data.metadata.keys())
            )

            return self.prompt_cache[prompt_path]

        except Exception as e:
            logger.exception("prompt_load_failed", prompt=prompt_path, error=str(e))
            raise

    def list_prompts(self, tag=None):
        """List all prompts, optionally filtered by tag.

        Args:
            tag (str, optional): Filter prompts by this tag

        Returns:
            list: List of prompt paths relative to the base path
        """
        prompts = []

        # Search for .txt and .md files
        for file_path in self.base_path.glob("**/*.txt"):
            relative_path = file_path.relative_to(self.base_path)
            if tag is None:
                prompts.append(str(relative_path))
            else:
                try:
                    prompt_data = self.get_prompt(str(relative_path))
                    if tag in prompt_data["metadata"].get("tags", []):
                        prompts.append(str(relative_path))
                except Exception:
                    continue

        # Also search for markdown files that might contain prompts
        for file_path in self.base_path.glob("**/*.md"):
            relative_path = file_path.relative_to(self.base_path)
            if tag is None:
                prompts.append(str(relative_path))
            else:
                try:
                    prompt_data = self.get_prompt(str(relative_path))
                    if tag in prompt_data["metadata"].get("tags", []):
                        prompts.append(str(relative_path))
                except Exception:
                    continue

        logger.info("prompts_listed", tag=tag, count=len(prompts))

        return sorted(prompts)

    def clear_cache(self):
        """Clear the prompt cache."""
        self.prompt_cache.clear()
        logger.debug("prompt_cache_cleared")

    def get_prompt_metadata(self, prompt_path):
        """Get only the metadata for a prompt without loading the full content.

        Args:
            prompt_path (str): Path to the prompt file, relative to base_path

        Returns:
            dict: Dictionary containing the prompt metadata

        Raises:
            FileNotFoundError: If the prompt file does not exist
        """
        # Check cache first
        if prompt_path in self.prompt_cache:
            return self.prompt_cache[prompt_path]["metadata"]

        # Load from file
        full_path = self.base_path / prompt_path
        if not full_path.exists():
            raise FileNotFoundError(f"Prompt not found: {prompt_path}")

        try:
            with open(full_path) as f:
                metadata = frontmatter.parse(f.read())[0]
            return metadata

        except Exception as e:
            logger.exception("prompt_metadata_load_failed", prompt=prompt_path, error=str(e))
            raise
