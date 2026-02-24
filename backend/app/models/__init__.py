"""
Database models for Curriculum Curator
"""

# Common types
# Authentication models
# Import models in dependency order
# New unit structure models
from .accreditation_mappings import (
    AoLCompetencyCode,
    AoLLevel,
    GraduateCapabilityCode,
    ULOGraduateCapabilityMapping,
    UnitAoLMapping,
)
from .assessment import (
    Assessment,
    AssessmentCategory,
    AssessmentStatus,
    SubmissionType,
)
from .assessment_plan import AssessmentMode, AssessmentPlan, AssessmentType
from .chat import ChatMessage, ChatRole, ChatSession, ContextScope
from .chat_session import SessionStatus, WorkflowChatSession, WorkflowStage
from .common import GUID
from .content import Content, ContentCategory, ContentStatus
from .content_version import ContentVersion
from .email_verification import EmailVerification
from .email_whitelist import EmailWhitelist
from .enums import ContentType, SessionFormat

# Generation tracking
from .generation_history import GenerationHistory, GenerationType
from .learning_design import DesignStatus, LearningDesign
from .learning_outcome import (
    AssessmentLearningOutcome,
    BloomLevel,
    OutcomeType,
    UnitLearningOutcome,
)
from .llm_config import LLMConfiguration, TokenUsageLog
from .local_learning_outcome import LocalLearningOutcome
from .login_attempt import LoginAttempt, LoginAttemptType
from .mappings import (
    assessment_material_links,
    assessment_ulo_mappings,
    material_ulo_mappings,
)
from .password_reset import PasswordReset
from .quiz_question import QuestionType, QuizQuestion
from .research_source import CitationStyle, ContentCitation, ResearchSource, SourceType
from .security_log import SecurityEventType, SecurityLog
from .system_config import ConfigCategory, SystemConfig
from .system_settings import SystemSettings
from .task_list import TaskList, TaskStatus

# Core academic models
from .unit import DifficultyLevel, PedagogyType, Semester, Unit, UnitStatus
from .unit_outline import UnitOutline, UnitStructureStatus
from .user import TeachingPhilosophy, User, UserRole

# Validation and search models
from .validation_result import ValidationResult, ValidationStatus
from .weekly_material import MaterialStatus, WeeklyMaterial
from .weekly_topic import WeeklyTopic, WeekType

# ruff: noqa: RUF022
__all__ = [
    # Common types
    "GUID",
    # Accreditation mappings
    "GraduateCapabilityCode",
    "AoLCompetencyCode",
    "AoLLevel",
    "ULOGraduateCapabilityMapping",
    "UnitAoLMapping",
    # Authentication
    "EmailVerification",
    "EmailWhitelist",
    "PasswordReset",
    "SystemSettings",
    "User",
    "UserRole",
    "TeachingPhilosophy",
    # Core academic
    "Unit",
    "UnitStatus",
    "Semester",
    "DifficultyLevel",
    "PedagogyType",
    "UnitLearningOutcome",
    "BloomLevel",
    "Content",
    "ContentType",
    "ContentStatus",
    "ContentCategory",
    "ContentVersion",
    "QuizQuestion",
    "QuestionType",
    # Validation and search
    "ValidationResult",
    "ValidationStatus",
    # Chat functionality
    "ChatSession",
    "ChatMessage",
    "ChatRole",
    "ContextScope",
    # Generation tracking
    "GenerationHistory",
    "GenerationType",
    # LLM Configuration
    "LLMConfiguration",
    "TokenUsageLog",
    # Local Learning Outcomes
    "LocalLearningOutcome",
    # Learning Designs and TaskList
    "LearningDesign",
    "DesignStatus",
    "TaskList",
    "TaskStatus",
    # Enums
    "SessionFormat",
    # Security
    "LoginAttempt",
    "LoginAttemptType",
    "SecurityLog",
    "SecurityEventType",
    # System Configuration
    "SystemConfig",
    "ConfigCategory",
    # New course structure models
    "UnitOutline",
    "UnitStructureStatus",
    "WeeklyTopic",
    "WeekType",
    "AssessmentPlan",
    "AssessmentType",
    "AssessmentMode",
    "OutcomeType",
    "WorkflowChatSession",
    "WorkflowStage",
    "SessionStatus",
    # New unit structure models
    "WeeklyMaterial",
    "MaterialStatus",
    "Assessment",
    "AssessmentCategory",
    "AssessmentStatus",
    "SubmissionType",
    "AssessmentLearningOutcome",
    "material_ulo_mappings",
    "assessment_ulo_mappings",
    "assessment_material_links",
    # Research sources and citations
    "ResearchSource",
    "ContentCitation",
    "SourceType",
    "CitationStyle",
]
