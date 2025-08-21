"""
Database models for Curriculum Curator
"""

# Authentication models
# Import models in dependency order
from .assessment_plan import AssessmentMode, AssessmentPlan, AssessmentType
from .chat import ChatMessage, ChatRole, ChatSession, ContextScope
from .chat_session import SessionStatus, WorkflowChatSession, WorkflowStage
from .content import Content, ContentCategory, ContentStatus, ContentType
from .content_version import ContentVersion
from .email_verification import EmailVerification
from .email_whitelist import EmailWhitelist

# Generation tracking
from .generation_history import GenerationHistory, GenerationType
from .learning_outcome import BloomLevel, OutcomeType, UnitLearningOutcome
from .llm_config import LLMConfiguration, TokenUsageLog
from .login_attempt import LoginAttempt, LoginAttemptType
from .material import Material, MaterialType
from .password_reset import PasswordReset
from .quiz_question import QuestionType, QuizQuestion
from .security_log import SecurityEventType, SecurityLog
from .system_config import ConfigCategory, SystemConfig
from .system_settings import SystemSettings

# Core academic models
from .unit import DifficultyLevel, PedagogyType, Semester, Unit, UnitStatus
from .unit_outline import UnitOutline, UnitStructureStatus
from .user import TeachingPhilosophy, User, UserRole

# Validation and search models
from .validation_result import ValidationResult, ValidationStatus
from .weekly_topic import WeeklyTopic, WeekType

# ruff: noqa: RUF022
__all__ = [
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
    # Materials
    "Material",
    "MaterialType",
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
]
