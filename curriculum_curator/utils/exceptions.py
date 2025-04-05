"""Exception hierarchy for Curriculum Curator."""


class CurriculumCuratorError(Exception):
    """Base exception for all curriculum curator errors."""

    pass


class PromptError(CurriculumCuratorError):
    """Exceptions related to prompt loading and rendering."""

    pass


class LLMRequestError(CurriculumCuratorError):
    """Exceptions related to LLM API requests."""

    pass


class WorkflowError(CurriculumCuratorError):
    """Exceptions related to workflow execution."""

    pass


class ValidationError(CurriculumCuratorError):
    """Exceptions related to content validation."""

    pass


class RemediationError(CurriculumCuratorError):
    """Exceptions related to content remediation."""

    pass


class OutputError(CurriculumCuratorError):
    """Exceptions related to output production."""

    pass


class ConfigurationError(CurriculumCuratorError):
    """Exceptions related to configuration loading or validation."""

    pass
