"""Base validator class for content validation."""

from abc import ABC, abstractmethod
from typing import Any, Optional


class BaseValidator(ABC):
    """Base class for all validators.

    All validators should inherit from this class and implement the validate method.
    """

    def __init__(self, config: Any):
        """Initialize the validator with configuration.

        Args:
            config: Configuration for the validator, typically from AppConfig.validation
        """
        self.config = config
        self.name = self.__class__.__name__

    @abstractmethod
    async def validate(
        self, content: str, context: Optional[dict[str, Any]] = None
    ) -> dict[str, Any]:
        """Validate the content and return a validation result.

        Args:
            content: The content to validate
            context: Optional context with additional information for validation

        Returns:
            dict: Validation result with at least a 'valid' boolean field and optional
                additional information about the validation
        """
        pass

    def get_remediation_hints(self, _validation_result: dict[str, Any]) -> dict[str, Any]:
        """Get hints for remediation based on validation result.

        This method can be overridden by validators to provide specific remediation hints
        when validation fails.

        Args:
            _validation_result: The result from the validate method

        Returns:
            dict: Hints for remediation
        """
        return {
            "can_remediate": False,
            "hints": ["No specific remediation hints available for this validator"],
        }
