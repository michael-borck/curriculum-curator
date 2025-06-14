"""Base remediator class for content remediation."""

from abc import ABC, abstractmethod
from typing import Any, Optional


class BaseRemediator(ABC):
    """Base class for all remediators.

    All remediators should inherit from this class and implement the remediate method.
    """

    def __init__(self, config: Any):
        """Initialize the remediator with configuration.

        Args:
            config: Configuration for the remediator, typically from AppConfig.remediation
        """
        self.config = config
        self.name = self.__class__.__name__

    @abstractmethod
    async def remediate(
        self, content: str, issues: list[dict[str, Any]], context: Optional[dict[str, Any]] = None
    ) -> dict[str, Any]:
        """Remediate the content based on validation issues.

        Args:
            content: The content to remediate
            issues: List of validation issues to address
            context: Optional context with additional information for remediation

        Returns:
            dict: Remediation result with at least 'remediated_content' and 'remediation_actions' fields
        """
        pass

    def can_remediate_issues(self, _issues: list[dict[str, Any]]) -> bool:
        """Check if this remediator can handle the given issues.

        Args:
            _issues: List of validation issues

        Returns:
            bool: True if this remediator can handle the issues
        """
        return False  # Base implementation assumes it can't handle any issues

    def get_remediation_summary(self, result: dict[str, Any]) -> str:
        """Get a human-readable summary of the remediation.

        Args:
            result: The result from the remediate method

        Returns:
            str: Human-readable summary
        """
        actions = result.get("remediation_actions", [])
        if not actions:
            return "No remediation actions performed"

        return f"{len(actions)} remediation actions performed"
