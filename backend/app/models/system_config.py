"""
System configuration model for storing application-wide settings
"""

import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import JSON, Boolean, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.user import GUID


class ConfigCategory(str, Enum):
    """Configuration categories"""

    LLM = "llm"
    TOOLS = "tools"
    EXPORT = "export"
    EMAIL = "email"
    SECURITY = "security"
    FEATURES = "features"


class SystemConfig(Base):
    """System-wide configuration settings"""

    __tablename__ = "system_config"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4, index=True)
    key = Column(String(100), unique=True, nullable=False, index=True)
    value = Column(JSON, nullable=False)
    category = Column(String(50), nullable=False, index=True)
    description = Column(Text, nullable=True)
    is_sensitive = Column(Boolean, default=False)  # For hiding sensitive values in UI

    # Audit fields
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by_id = Column(GUID(), ForeignKey("users.id"), nullable=True)

    # Relationships
    updated_by = relationship("User", foreign_keys=[updated_by_id])

    def __repr__(self):
        return f"<SystemConfig(key='{self.key}', category='{self.category}')>"

    @classmethod
    def get_default_configs(cls):
        """Get default system configurations"""
        return [
            # LLM Configuration
            {
                "key": "llm.provider",
                "value": "openai",
                "category": ConfigCategory.LLM,
                "description": "Default LLM provider (openai, anthropic, etc.)",
                "is_sensitive": False
            },
            {
                "key": "llm.model",
                "value": "gpt-4",
                "category": ConfigCategory.LLM,
                "description": "Default LLM model",
                "is_sensitive": False
            },
            {
                "key": "llm.api_url",
                "value": "https://api.openai.com/v1",
                "category": ConfigCategory.LLM,
                "description": "LLM API endpoint URL",
                "is_sensitive": False
            },
            {
                "key": "llm.api_key",
                "value": "",
                "category": ConfigCategory.LLM,
                "description": "System-wide LLM API key (users can override)",
                "is_sensitive": True
            },
            {
                "key": "llm.allow_user_keys",
                "value": True,
                "category": ConfigCategory.LLM,
                "description": "Allow users to bring their own API keys",
                "is_sensitive": False
            },

            # Tool Paths
            {
                "key": "tools.git_path",
                "value": "/usr/bin/git",
                "category": ConfigCategory.TOOLS,
                "description": "Path to Git executable",
                "is_sensitive": False
            },
            {
                "key": "tools.quarto_path",
                "value": "/usr/local/bin/quarto",
                "category": ConfigCategory.TOOLS,
                "description": "Path to Quarto executable",
                "is_sensitive": False
            },
            {
                "key": "tools.pandoc_path",
                "value": "/usr/bin/pandoc",
                "category": ConfigCategory.TOOLS,
                "description": "Path to Pandoc executable",
                "is_sensitive": False
            },

            # Export Settings
            {
                "key": "export.max_file_size",
                "value": 104857600,  # 100MB
                "category": ConfigCategory.EXPORT,
                "description": "Maximum file size for exports (bytes)",
                "is_sensitive": False
            },
            {
                "key": "export.allowed_formats",
                "value": ["pdf", "docx", "pptx", "html", "md", "tex"],
                "category": ConfigCategory.EXPORT,
                "description": "Allowed export formats",
                "is_sensitive": False
            },
            {
                "key": "export.temp_dir",
                "value": "/tmp/exports",
                "category": ConfigCategory.EXPORT,
                "description": "Temporary directory for export processing",
                "is_sensitive": False
            },

            # Email Settings
            {
                "key": "email.enabled",
                "value": False,
                "category": ConfigCategory.EMAIL,
                "description": "Enable email functionality",
                "is_sensitive": False
            },
            {
                "key": "email.from_address",
                "value": "noreply@curriculum-curator.local",
                "category": ConfigCategory.EMAIL,
                "description": "From email address",
                "is_sensitive": False
            },
            {
                "key": "email.smtp_host",
                "value": "",
                "category": ConfigCategory.EMAIL,
                "description": "SMTP server host",
                "is_sensitive": False
            },
            {
                "key": "email.smtp_port",
                "value": 587,
                "category": ConfigCategory.EMAIL,
                "description": "SMTP server port",
                "is_sensitive": False
            },
            {
                "key": "email.smtp_password",
                "value": "",
                "category": ConfigCategory.EMAIL,
                "description": "SMTP password",
                "is_sensitive": True
            },

            # Security Settings
            {
                "key": "security.session_timeout",
                "value": 1440,  # 24 hours in minutes
                "category": ConfigCategory.SECURITY,
                "description": "User session timeout (minutes)",
                "is_sensitive": False
            },
            {
                "key": "security.max_login_attempts",
                "value": 5,
                "category": ConfigCategory.SECURITY,
                "description": "Maximum login attempts before lockout",
                "is_sensitive": False
            },
            {
                "key": "security.lockout_duration",
                "value": 30,  # 30 minutes
                "category": ConfigCategory.SECURITY,
                "description": "Account lockout duration (minutes)",
                "is_sensitive": False
            },
            {
                "key": "security.require_email_verification",
                "value": True,
                "category": ConfigCategory.SECURITY,
                "description": "Require email verification for new users",
                "is_sensitive": False
            },

            # Feature Flags
            {
                "key": "features.ai_generation",
                "value": True,
                "category": ConfigCategory.FEATURES,
                "description": "Enable AI content generation",
                "is_sensitive": False
            },
            {
                "key": "features.file_upload",
                "value": True,
                "category": ConfigCategory.FEATURES,
                "description": "Enable file upload functionality",
                "is_sensitive": False
            },
            {
                "key": "features.export",
                "value": True,
                "category": ConfigCategory.FEATURES,
                "description": "Enable export functionality",
                "is_sensitive": False
            },
            {
                "key": "features.collaboration",
                "value": False,
                "category": ConfigCategory.FEATURES,
                "description": "Enable multi-user collaboration (future)",
                "is_sensitive": False
            }
        ]
