"""
Canonical enums for the type system.

Three orthogonal dimensions:
- SessionFormat: what kind of teaching session (lecture, tutorial, lab, ...)
- ContentType: what artifact you're creating (slides, notes, worksheet, ...)
- PedagogyType: teaching philosophy — lives on Unit model (see unit.py)
"""

from enum import Enum


class SessionFormat(str, Enum):
    """What kind of teaching session a WeeklyMaterial represents."""

    LECTURE = "lecture"
    TUTORIAL = "tutorial"
    LAB = "lab"
    WORKSHOP = "workshop"
    SEMINAR = "seminar"
    INDEPENDENT = "independent"
    OTHER = "other"


class ContentType(str, Enum):
    """What artifact a Content item represents."""

    SLIDES = "slides"
    NOTES = "notes"
    WORKSHEET = "worksheet"
    HANDOUT = "handout"
    QUIZ = "quiz"
    CASE_STUDY = "case_study"
    READING = "reading"
    VIDEO = "video"
    DISCUSSION = "discussion"
    ACTIVITY = "activity"
    ASSIGNMENT = "assignment"
    RESOURCE = "resource"
