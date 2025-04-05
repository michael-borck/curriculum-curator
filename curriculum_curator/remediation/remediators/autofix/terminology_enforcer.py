"""Terminology enforcer for ensuring consistent terminology usage."""

import re
from typing import Any, Optional

from curriculum_curator.remediation.remediators.base import BaseRemediator


class TerminologyEnforcer(BaseRemediator):
    """Remediator that enforces consistent terminology.

    Replaces incorrect or inconsistent terminology with preferred terms.
    Uses a configured glossary or terminology map.

    Config options:
        terminology_map: Dictionary mapping incorrect terms to preferred terms
        case_sensitive: Whether to use case-sensitive matching
        whole_word_only: Whether to match only whole words
    """

    def __init__(self, config: Any):
        """Initialize the terminology enforcer.

        Args:
            config: Configuration for the remediator
        """
        super().__init__(config)
        self.terminology_map = getattr(config, "terminology_map", {})
        self.case_sensitive = getattr(config, "case_sensitive", False)
        self.whole_word_only = getattr(config, "whole_word_only", True)

    async def remediate(
        self, content: str, _issues: list[dict[str, Any]], _context: Optional[dict[str, Any]] = None
    ) -> dict[str, Any]:
        """Enforce terminology consistency in the content.

        Args:
            content: The content to remediate
            _issues: List of validation issues to address
            _context: Optional context with additional information

        Returns:
            dict: Remediation result
        """
        # TODO: Implement terminology enforcement logic

        # Placeholder implementation
        actions = []
        remediated_content = content

        # Apply terminology replacements
        for incorrect, preferred in self.terminology_map.items():
            if self.whole_word_only:
                pattern = r"\b" + re.escape(incorrect) + r"\b"
            else:
                pattern = re.escape(incorrect)

            flags = 0 if self.case_sensitive else re.IGNORECASE

            # Count occurrences
            matches = re.findall(pattern, content, flags)

            if matches:
                # Record the action
                actions.append(
                    {
                        "type": "terminology_correction",
                        "incorrect_term": incorrect,
                        "preferred_term": preferred,
                        "occurrences": len(matches),
                    }
                )

                # Make the replacements
                if self.case_sensitive:
                    remediated_content = re.sub(pattern, preferred, remediated_content)
                else:
                    # Preserve case where possible
                    for match in set(matches):
                        remediated_content = self._replace_preserving_case(
                            remediated_content, match, preferred
                        )

        return {
            "remediated_content": remediated_content,
            "remediation_actions": actions,
            "success": len(actions) > 0,
            "terms_corrected": sum(action["occurrences"] for action in actions),
        }

    def _replace_preserving_case(self, text: str, old: str, new: str) -> str:
        """Replace text while preserving the case pattern.

        Args:
            text: The text to modify
            old: The text to replace
            new: The replacement text

        Returns:
            str: Modified text
        """
        # Determine case pattern of old text
        if old.islower():
            replacement = new.lower()
        elif old.isupper():
            replacement = new.upper()
        elif old[0].isupper() and old[1:].islower():
            replacement = new[0].upper() + new[1:].lower()
        else:
            replacement = new

        # Create regex pattern that matches the old text case-insensitively
        pattern = re.escape(old)
        if self.whole_word_only:
            pattern = r"\b" + pattern + r"\b"

        # Replace with case-preserved new text
        return re.sub(pattern, lambda m: replacement, text, flags=re.IGNORECASE)

    def can_remediate_issues(self, issues: list[dict[str, Any]]) -> bool:
        """Check if this remediator can handle the given issues.

        Args:
            issues: List of validation issues

        Returns:
            bool: True if this remediator can handle the issues
        """
        # This remediator can be run proactively regardless of issues
        # But will specifically respond to terminology issues
        for issue in issues:
            if "terminology" in issue.get("message", "").lower():
                return True

            if issue.get("issue") == "terminology":
                return True

        # Return True if we have a terminology map, so this can run proactively
        return len(self.terminology_map) > 0
