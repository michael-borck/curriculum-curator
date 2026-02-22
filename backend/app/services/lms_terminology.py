"""
LMS terminology mapping table.

Different LMS platforms use different labels for the same structural
concepts.  This module provides a central mapping so exports can
produce platform-appropriate names and imports can use platform-aware
keyword sets when classifying items.

Story 9.9 — mapping table.
Story 9.10 — wired into exports via ``target_lms`` query parameter.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class TargetLMS(str, Enum):
    """Supported LMS targets for export labelling."""

    GENERIC = "generic"
    CANVAS = "canvas"
    MOODLE = "moodle"
    BLACKBOARD = "blackboard"
    BRIGHTSPACE = "brightspace"


@dataclass(frozen=True)
class LMSTerminology:
    """Immutable label set for a single LMS platform."""

    lms: TargetLMS
    display_name: str
    module_label: str
    overview_label: str
    material_label: str
    assessment_label: str
    quiz_label: str
    # Keyword sets used by import classification
    assessment_terms: frozenset[str]
    material_terms: frozenset[str]


# Shared base keyword sets (generic superset)
_BASE_ASSESSMENT_TERMS = frozenset(
    {"quiz", "exam", "test", "assignment", "midterm", "final", "assessment"}
)
_BASE_MATERIAL_TERMS = frozenset(
    {
        "lecture",
        "reading",
        "video",
        "discussion",
        "activity",
        "handout",
        "case study",
        "notes",
        "page",
        "resource",
    }
)

LMS_TERMINOLOGY: dict[TargetLMS, LMSTerminology] = {
    TargetLMS.GENERIC: LMSTerminology(
        lms=TargetLMS.GENERIC,
        display_name="Generic",
        module_label="Week",
        overview_label="Overview",
        material_label="Materials",
        assessment_label="Assessments",
        quiz_label="Quizzes",
        assessment_terms=_BASE_ASSESSMENT_TERMS,
        material_terms=_BASE_MATERIAL_TERMS,
    ),
    TargetLMS.CANVAS: LMSTerminology(
        lms=TargetLMS.CANVAS,
        display_name="Canvas",
        module_label="Module",
        overview_label="Pages",
        material_label="Pages",
        assessment_label="Assignments",
        quiz_label="Quizzes",
        assessment_terms=_BASE_ASSESSMENT_TERMS | {"assignments"},
        material_terms=_BASE_MATERIAL_TERMS | {"pages", "modules"},
    ),
    TargetLMS.MOODLE: LMSTerminology(
        lms=TargetLMS.MOODLE,
        display_name="Moodle",
        module_label="Topic",
        overview_label="Resources",
        material_label="Resources",
        assessment_label="Activities",
        quiz_label="Quiz",
        assessment_terms=_BASE_ASSESSMENT_TERMS | {"activities"},
        material_terms=_BASE_MATERIAL_TERMS | {"resources", "topics"},
    ),
    TargetLMS.BLACKBOARD: LMSTerminology(
        lms=TargetLMS.BLACKBOARD,
        display_name="Blackboard",
        module_label="Content Area",
        overview_label="Items",
        material_label="Items",
        assessment_label="Assignments",
        quiz_label="Tests",
        assessment_terms=_BASE_ASSESSMENT_TERMS | {"tests"},
        material_terms=_BASE_MATERIAL_TERMS | {"items", "content area"},
    ),
    TargetLMS.BRIGHTSPACE: LMSTerminology(
        lms=TargetLMS.BRIGHTSPACE,
        display_name="Brightspace",
        module_label="Module",
        overview_label="Topics",
        material_label="Topics",
        assessment_label="Assignments",
        quiz_label="Quizzes",
        assessment_terms=_BASE_ASSESSMENT_TERMS | {"assignments"},
        material_terms=_BASE_MATERIAL_TERMS | {"topics", "modules"},
    ),
}


def get_terminology(lms: TargetLMS | None = None) -> LMSTerminology:
    """Return the terminology for the given LMS, defaulting to generic."""
    if lms is None:
        return LMS_TERMINOLOGY[TargetLMS.GENERIC]
    return LMS_TERMINOLOGY.get(lms, LMS_TERMINOLOGY[TargetLMS.GENERIC])


def detect_lms_to_target(source_lms: str | None) -> TargetLMS:
    """Convert a ``detect_source_lms()`` string to a ``TargetLMS`` enum value."""
    if source_lms is None:
        return TargetLMS.GENERIC
    try:
        return TargetLMS(source_lms.lower())
    except ValueError:
        return TargetLMS.GENERIC
