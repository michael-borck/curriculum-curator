"""Translator for converting content between languages."""

from typing import Any, Optional

from curriculum_curator.remediation.remediators.base import BaseRemediator


class Translator(BaseRemediator):
    """Remediator that translates content between languages.

    Automatically translates content from source language to target language
    using either an external translation API or an LLM.

    Config options:
        target_language: Target language code (e.g., 'en', 'es', 'fr')
        source_language: Source language code, or 'auto' for auto-detection
        use_llm: Whether to use LLM for translation (vs. dedicated translation API)
        model_alias: LLM model to use if use_llm is True
        preserve_formatting: Whether to preserve Markdown formatting
    """

    def __init__(self, config: Any):
        """Initialize the translator.

        Args:
            config: Configuration for the remediator
        """
        super().__init__(config)
        self.target_language = getattr(config, "target_language", "en")
        self.source_language = getattr(config, "source_language", "auto")
        self.use_llm = getattr(config, "use_llm", True)
        self.model_alias = getattr(config, "model_alias", None)
        self.preserve_formatting = getattr(config, "preserve_formatting", True)

    async def remediate(
        self, content: str, issues: list[dict[str, Any]], _context: Optional[dict[str, Any]] = None
    ) -> dict[str, Any]:
        """Translate content to the target language.

        Args:
            content: The content to remediate
            issues: List of validation issues to address
            _context: Optional context with additional information

        Returns:
            dict: Remediation result
        """
        # Determine source language from issues or auto-detect
        source_language = self.source_language
        for issue in issues:
            if issue.get("validator", "").endswith("LanguageDetector"):
                source_language = issue.get("detected_language", source_language)
                break

        if source_language == self.target_language:
            return {
                "remediated_content": content,
                "remediation_actions": [],
                "success": True,
                "message": "Content already in target language",
            }

        # TODO: Implement translation
        # This would use a translation API or an LLM

        # Placeholder implementation
        translated_content = content  # In real implementation, this would be translated

        return {
            "remediated_content": translated_content,
            "remediation_actions": [
                {
                    "type": "translation",
                    "source_language": source_language,
                    "target_language": self.target_language,
                    "method": "llm" if self.use_llm else "api",
                }
            ],
            "success": True,
        }

    def can_remediate_issues(self, issues: list[dict[str, Any]]) -> bool:
        """Check if this remediator can handle the given issues.

        Args:
            issues: List of validation issues

        Returns:
            bool: True if this remediator can handle the issues
        """
        # Check for language-related issues
        for issue in issues:
            if issue.get("validator", "").endswith("LanguageDetector"):
                return True

            # Look for explicit language mentions in message
            message = issue.get("message", "").lower()
            if "language" in message and (
                "translate" in message or "conversion" in message or "wrong" in message
            ):
                return True

        return False
