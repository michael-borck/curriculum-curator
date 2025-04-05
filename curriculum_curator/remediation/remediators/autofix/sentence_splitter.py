"""Sentence splitter for fixing readability issues by breaking down long sentences."""

import re
from typing import Any, Optional

from curriculum_curator.remediation.remediators.base import BaseRemediator


class SentenceSplitter(BaseRemediator):
    """Remediator that breaks long sentences into shorter ones.

    Improves readability by splitting long sentences at appropriate points,
    such as conjunctions or semicolons.

    Config options:
        max_sentence_length: Maximum allowed sentence length
        split_points: List of patterns where sentences can be split
    """

    def __init__(self, config: Any):
        """Initialize the sentence splitter.

        Args:
            config: Configuration for the remediator
        """
        super().__init__(config)
        self.max_sentence_length = getattr(config, "max_sentence_length", 25)
        self.split_points = getattr(
            config,
            "split_points",
            [
                r"\s+and\s+",
                r"\s+but\s+",
                r"\s+or\s+",
                r"\s+nor\s+",
                r"\s+yet\s+",
                r"\s+so\s+",
                r"\s+for\s+",
                r";",
            ],
        )

    async def remediate(
        self, content: str, _issues: list[dict[str, Any]], _context: Optional[dict[str, Any]] = None
    ) -> dict[str, Any]:
        """Break long sentences into shorter ones.

        Args:
            content: The content to remediate
            _issues: List of validation issues to address
            _context: Optional context with additional information

        Returns:
            dict: Remediation result
        """
        # TODO: Implement sentence splitting logic

        # Placeholder implementation
        actions = []
        remediated_content = content

        # Split text into sentences
        sentences = self._extract_sentences(content)

        # Find long sentences
        long_sentences = [
            sentence
            for sentence in sentences
            if self._count_words(sentence) > self.max_sentence_length
        ]

        # For each long sentence, try to split it
        for sentence in long_sentences:
            # Placeholder - in real implementation we would split the sentences
            actions.append(
                {
                    "type": "sentence_split",
                    "original": sentence,
                    "modified": sentence,  # Would be the split version
                    "word_count_before": self._count_words(sentence),
                    "word_count_after": self._count_words(sentence),  # Would be reduced
                }
            )

        return {
            "remediated_content": remediated_content,
            "remediation_actions": actions,
            "success": len(actions) > 0,
            "long_sentences_count": len(long_sentences),
            "sentences_split": len(actions),
        }

    def _extract_sentences(self, text: str) -> list[str]:
        """Extract sentences from text.

        Args:
            text: The text to extract sentences from

        Returns:
            list: List of sentences
        """
        # Simple sentence splitting - would be more sophisticated in real implementation
        return re.split(r"(?<=[.!?])\s+", text)

    def _count_words(self, text: str) -> int:
        """Count words in text.

        Args:
            text: The text to count words in

        Returns:
            int: Word count
        """
        return len(text.split())

    def can_remediate_issues(self, issues: list[dict[str, Any]]) -> bool:
        """Check if this remediator can handle the given issues.

        Args:
            issues: List of validation issues

        Returns:
            bool: True if this remediator can handle the issues
        """
        # Check if any issues are readability-related
        for issue in issues:
            if issue.get("validator") == "ReadabilityValidator":
                return True

            if issue.get("issue") == "sentence_length":
                return True

            if (
                "sentence" in issue.get("message", "").lower()
                and "long" in issue.get("message", "").lower()
            ):
                return True

        return False
