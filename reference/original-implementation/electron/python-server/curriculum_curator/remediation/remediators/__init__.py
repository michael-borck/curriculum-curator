"""Content remediators for fixing issues in educational content."""


# Import AutoFix remediators
from curriculum_curator.remediation.remediators.autofix.format_corrector import (
    FormatCorrector,
)
from curriculum_curator.remediation.remediators.autofix.sentence_splitter import (
    SentenceSplitter,
)
from curriculum_curator.remediation.remediators.autofix.terminology_enforcer import (
    TerminologyEnforcer,
)
from curriculum_curator.remediation.remediators.base import BaseRemediator

# Import Language remediators
from curriculum_curator.remediation.remediators.language.translator import Translator

# Import Rewrite remediators
from curriculum_curator.remediation.remediators.rewrite.rephrasing_prompter import (
    RephrasingPrompter,
)

# Import Workflow remediators
from curriculum_curator.remediation.remediators.workflow.flag_for_review import (
    FlagForReview,
)

# Registry of all available remediators
REMEDIATOR_REGISTRY: dict[str, type[BaseRemediator]] = {
    # AutoFix remediators
    "format_corrector": FormatCorrector,
    "sentence_splitter": SentenceSplitter,
    "terminology_enforcer": TerminologyEnforcer,
    # Rewrite remediators
    "rephrasing_prompter": RephrasingPrompter,
    # Workflow remediators
    "flag_for_review": FlagForReview,
    # Language remediators
    "translator": Translator,
}


def get_remediator(remediator_name: str, config):
    """Get a remediator instance by name.

    Args:
        remediator_name: Name of the remediator
        config: Configuration for the remediator

    Returns:
        BaseRemediator: Initialized remediator instance

    Raises:
        ValueError: If the remediator is not found or implemented
    """
    if remediator_name not in REMEDIATOR_REGISTRY:
        raise ValueError(
            f"Remediator '{remediator_name}' not found. Available remediators: {', '.join(REMEDIATOR_REGISTRY.keys())}"
        )

    remediator_class = REMEDIATOR_REGISTRY[remediator_name]
    if remediator_class is None:
        raise ValueError(f"Remediator '{remediator_name}' is not yet implemented")

    return remediator_class(config)
