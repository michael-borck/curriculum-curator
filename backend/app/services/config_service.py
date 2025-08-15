"""
Configuration service for retrieving and caching system configurations
"""

import json
import os
from typing import Any, ClassVar

from sqlalchemy.orm import Session

from app.models import ConfigCategory, SystemConfig


class ConfigService:
    """Service for managing system configurations"""

    _cache: ClassVar[dict[str, Any]] = {}
    _initialized: ClassVar[bool] = False

    @classmethod
    def initialize(cls, db: Session) -> None:
        """Initialize configuration cache from database"""
        configs = db.query(SystemConfig).all()
        for config in configs:
            cls._cache[config.key] = cls._parse_value(config.value, config.value_type)
        cls._initialized = True

    @classmethod
    def get(cls, key: str, default: Any = None) -> Any:
        """
        Get configuration value by key

        Args:
            key: Configuration key
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        # First check environment variables (highest priority)
        env_key = key.upper().replace(".", "_")
        env_value = os.getenv(env_key)
        if env_value is not None:
            return env_value

        # Then check cache
        return cls._cache.get(key, default)

    @classmethod
    def get_bool(cls, key: str, default: bool = False) -> bool:
        """Get boolean configuration value"""
        value = cls.get(key, default)
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ["true", "1", "yes", "on"]
        return bool(value)

    @classmethod
    def get_int(cls, key: str, default: int = 0) -> int:
        """Get integer configuration value"""
        value = cls.get(key, default)
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    @classmethod
    def get_float(cls, key: str, default: float = 0.0) -> float:
        """Get float configuration value"""
        value = cls.get(key, default)
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    @classmethod
    def get_json(cls, key: str, default: dict | list | None = None) -> Any:
        """Get JSON configuration value"""
        value = cls.get(key, default)
        if isinstance(value, dict | list):
            return value
        if isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return default
        return default

    @classmethod
    def get_list(cls, key: str, default: list | None = None) -> list:
        """Get list configuration value (comma-separated or JSON)"""
        if default is None:
            default = []

        value = cls.get(key, default)
        if isinstance(value, list):
            return value
        if isinstance(value, str):
            # Try JSON first
            try:
                parsed = json.loads(value)
                if isinstance(parsed, list):
                    return parsed
            except json.JSONDecodeError:
                pass
            # Fall back to comma-separated
            return [v.strip() for v in value.split(",") if v.strip()]
        return default

    @classmethod
    def refresh(cls, db: Session, key: str | None = None) -> None:
        """
        Refresh configuration cache

        Args:
            db: Database session
            key: Optional specific key to refresh
        """
        if key:
            config = db.query(SystemConfig).filter(SystemConfig.key == key).first()
            if config:
                cls._cache[config.key] = cls._parse_value(config.value, config.value_type)
        else:
            cls.initialize(db)

    @classmethod
    def get_by_category(cls, category: ConfigCategory) -> dict[str, Any]:
        """Get all configurations in a category"""
        # This is a simple implementation - in production you'd track category in cache
        return {
            key: value
            for key, value in cls._cache.items()
            if key.startswith(category.value.lower())
        }

    @classmethod
    def _parse_value(cls, value: str, value_type: str) -> Any:  # noqa: PLR0911
        """Parse configuration value based on type"""
        if value_type == "boolean":
            return value.lower() in ["true", "1", "yes", "on"]
        if value_type == "integer":
            try:
                return int(value)
            except (TypeError, ValueError):
                return value
        elif value_type == "float":
            try:
                return float(value)
            except (TypeError, ValueError):
                return value
        elif value_type == "json":
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        else:
            return value

    # Convenience methods for common configurations

    @classmethod
    def get_password_min_length(cls) -> int:
        """Get minimum password length"""
        return cls.get_int("security.password_min_length", 8)

    @classmethod
    def get_password_requirements(cls) -> dict[str, bool]:
        """Get password requirements"""
        return {
            "uppercase": cls.get_bool("security.password_require_uppercase", True),
            "lowercase": cls.get_bool("security.password_require_lowercase", True),
            "numbers": cls.get_bool("security.password_require_numbers", True),
            "special": cls.get_bool("security.password_require_special", True),
        }

    @classmethod
    def get_max_login_attempts(cls) -> int:
        """Get maximum login attempts"""
        return cls.get_int("security.max_login_attempts", 5)

    @classmethod
    def get_lockout_duration_minutes(cls) -> int:
        """Get account lockout duration in minutes"""
        return cls.get_int("security.lockout_duration_minutes", 15)

    @classmethod
    def get_session_timeout_minutes(cls) -> int:
        """Get session timeout in minutes"""
        return cls.get_int("security.session_timeout_minutes", 30)

    @classmethod
    def is_user_registration_enabled(cls) -> bool:
        """Check if user registration is enabled"""
        return cls.get_bool("security.enable_user_registration", True)

    @classmethod
    def is_email_whitelist_enabled(cls) -> bool:
        """Check if email whitelist is enabled"""
        return cls.get_bool("security.enable_email_whitelist", True)

    @classmethod
    def get_smtp_settings(cls) -> dict[str, Any]:
        """Get SMTP settings for email"""
        return {
            "server": cls.get("email.smtp_server", "localhost"),
            "port": cls.get_int("email.smtp_port", 587),
            "username": cls.get("email.smtp_username"),
            "password": cls.get("email.smtp_password"),
            "use_tls": cls.get_bool("email.smtp_use_tls", True),
            "from_email": cls.get("email.from_address", "noreply@curriculum-curator.local"),
            "from_name": cls.get("email.from_name", "Curriculum Curator"),
        }

    @classmethod
    def get_llm_settings(cls, provider: str) -> dict[str, Any]:
        """Get LLM provider settings"""
        base_key = f"llm.{provider.lower()}"
        return {
            "api_key": cls.get(f"{base_key}_api_key"),
            "model": cls.get(f"{base_key}_model"),
            "temperature": cls.get_float(f"{base_key}_temperature", 0.7),
            "max_tokens": cls.get_int(f"{base_key}_max_tokens", 4096),
            "enabled": cls.get_bool(f"{base_key}_enabled", False),
        }

    @classmethod
    def get_export_settings(cls) -> dict[str, Any]:
        """Get export settings"""
        return {
            "quarto_path": cls.get("tools.quarto_path", "quarto"),
            "pandoc_path": cls.get("tools.pandoc_path", "pandoc"),
            "formats_enabled": cls.get_list("export.formats_enabled",
                                           ["pdf", "docx", "pptx", "html", "markdown"]),
            "max_export_size_mb": cls.get_int("export.max_size_mb", 100),
        }

    @classmethod
    def get_file_upload_settings(cls) -> dict[str, Any]:
        """Get file upload settings"""
        return {
            "enabled": cls.get_bool("features.enable_file_upload", True),
            "max_size_mb": cls.get_int("upload.max_file_size_mb", 10),
            "allowed_extensions": cls.get_list("upload.allowed_extensions",
                                             [".pdf", ".doc", ".docx", ".txt", ".md"]),
        }

    @classmethod
    def is_ai_enabled(cls) -> bool:
        """Check if AI features are enabled"""
        return cls.get_bool("features.enable_ai_features", True)

