"""
Database models for Curriculum Curator
"""

# Authentication models
# Chat functionality
from .chat import ChatMessage, ChatRole, ChatSession, ContextScope
from .content import Content, ContentStatus, ContentType
from .content_version import ContentVersion
from .conversation import Conversation
from .course import Course, CourseModule, CourseStatus, ModuleType
from .course_search_result import CourseSearchResult
from .email_verification import EmailVerification
from .email_whitelist import EmailWhitelist

# Generation tracking
from .generation_history import GenerationHistory, GenerationType
from .login_attempt import LoginAttempt, LoginAttemptType
from .lrd import LRD, LRDStatus
from .material import Material, MaterialType
from .password_reset import PasswordReset
from .quiz_question import QuestionType, QuizQuestion
from .security_log import SecurityEventType, SecurityLog
from .system_config import ConfigCategory, SystemConfig
from .system_settings import SystemSettings
from .task_list import TaskList, TaskStatus

# Core academic models
from .unit import DifficultyLevel, PedagogyType, Semester, Unit, UnitStatus
from .unit_learning_outcome import BloomLevel, UnitLearningOutcome
from .user import TeachingPhilosophy, User, UserRole

# Validation and search models
from .validation_result import ValidationResult, ValidationStatus

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
    "Course",
    "CourseModule",
    "CourseStatus",
    "ModuleType",
    "LRD",
    "LRDStatus",
    "Material",
    "MaterialType",
    "TaskList",
    "TaskStatus",
    "Conversation",
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
    "ContentVersion",
    "QuizQuestion",
    "QuestionType",
    # Validation and search
    "ValidationResult",
    "ValidationStatus",
    "CourseSearchResult",
    # Chat functionality
    "ChatSession",
    "ChatMessage",
    "ChatRole",
    "ContextScope",
    # Generation tracking
    "GenerationHistory",
    "GenerationType",
    # Security
    "LoginAttempt",
    "LoginAttemptType",
    "SecurityLog",
    "SecurityEventType",
    # System Configuration
    "SystemConfig",
    "ConfigCategory",
]
