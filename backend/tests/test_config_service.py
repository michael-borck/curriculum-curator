"""
Tests for Config service — env vars + DB cache.
"""

import os
import uuid

import pytest
from sqlalchemy.orm import Session

from app.models.system_config import ConfigCategory, SystemConfig
from app.services.config_service import ConfigService


@pytest.fixture(autouse=True)
def _reset_cache():
    """Reset the class-level cache before each test."""
    ConfigService._cache.clear()
    ConfigService._initialized = False
    yield
    ConfigService._cache.clear()
    ConfigService._initialized = False


def _insert_config(
    db: Session,
    key: str,
    value: str,
    value_type: str = "string",
    category: str = ConfigCategory.FEATURES.value,
) -> SystemConfig:
    config = SystemConfig(
        id=str(uuid.uuid4()),
        key=key,
        value=value,
        category=category,
        description=f"Test config: {key}",
    )
    # SystemConfig.value is JSON, but _parse_value expects a str for value_type parsing
    # The model stores value as JSON; for testing we set it and use value_type attribute
    db.add(config)
    db.commit()
    db.refresh(config)
    return config


# ─── INITIALIZE ──────────────────────────────────────────────


class TestInitialize:
    def test_initialize_empty_db(self, test_db: Session):
        ConfigService.initialize(test_db)
        assert ConfigService._initialized is True

    def test_initialize_loads_configs(self, test_db: Session):
        _insert_config(test_db, "app.name", "TestApp")
        ConfigService.initialize(test_db)
        assert ConfigService._cache["app.name"] == "TestApp"


# ─── GET ─────────────────────────────────────────────────────


class TestGet:
    def test_get_from_cache(self):
        ConfigService._cache["my.key"] = "cached_value"
        assert ConfigService.get("my.key") == "cached_value"

    def test_get_default(self):
        assert ConfigService.get("nonexistent", "fallback") == "fallback"

    def test_env_var_overrides_cache(self, monkeypatch: pytest.MonkeyPatch):
        ConfigService._cache["my.key"] = "cached"
        monkeypatch.setenv("MY_KEY", "from_env")
        assert ConfigService.get("my.key") == "from_env"


# ─── GET_BOOL ────────────────────────────────────────────────


class TestGetBool:
    def test_true_values(self):
        for val in ["true", "1", "yes", "on"]:
            ConfigService._cache["b"] = val
            assert ConfigService.get_bool("b") is True

    def test_false_values(self):
        for val in ["false", "0", "no", "off"]:
            ConfigService._cache["b"] = val
            assert ConfigService.get_bool("b") is False

    def test_bool_type(self):
        ConfigService._cache["b"] = True
        assert ConfigService.get_bool("b") is True

    def test_default(self):
        assert ConfigService.get_bool("missing", False) is False


# ─── GET_INT ─────────────────────────────────────────────────


class TestGetInt:
    def test_int_from_string(self):
        ConfigService._cache["i"] = "42"
        assert ConfigService.get_int("i") == 42

    def test_int_from_int(self):
        ConfigService._cache["i"] = 42
        assert ConfigService.get_int("i") == 42

    def test_invalid_returns_default(self):
        ConfigService._cache["i"] = "not_a_number"
        assert ConfigService.get_int("i", 99) == 99

    def test_missing_returns_default(self):
        assert ConfigService.get_int("missing", 10) == 10


# ─── GET_FLOAT ───────────────────────────────────────────────


class TestGetFloat:
    def test_float_from_string(self):
        ConfigService._cache["f"] = "3.14"
        assert ConfigService.get_float("f") == 3.14

    def test_invalid_returns_default(self):
        ConfigService._cache["f"] = "nan_text"
        assert ConfigService.get_float("f", 1.0) == 1.0


# ─── GET_JSON ────────────────────────────────────────────────


class TestGetJson:
    def test_json_from_string(self):
        ConfigService._cache["j"] = '{"a": 1}'
        result = ConfigService.get_json("j")
        assert result == {"a": 1}

    def test_json_dict_passthrough(self):
        ConfigService._cache["j"] = {"a": 1}
        assert ConfigService.get_json("j") == {"a": 1}

    def test_invalid_json_returns_default(self):
        ConfigService._cache["j"] = "not json"
        assert ConfigService.get_json("j", {"default": True}) == {"default": True}


# ─── GET_LIST ────────────────────────────────────────────────


class TestGetList:
    def test_list_passthrough(self):
        ConfigService._cache["l"] = ["a", "b"]
        assert ConfigService.get_list("l") == ["a", "b"]

    def test_json_list(self):
        ConfigService._cache["l"] = '["x", "y"]'
        assert ConfigService.get_list("l") == ["x", "y"]

    def test_comma_separated(self):
        ConfigService._cache["l"] = "a, b, c"
        assert ConfigService.get_list("l") == ["a", "b", "c"]

    def test_empty_default(self):
        assert ConfigService.get_list("missing") == []


# ─── REFRESH ─────────────────────────────────────────────────


class TestRefresh:
    def test_refresh_all_empty(self, test_db: Session):
        # refresh on empty DB calls initialize which succeeds
        ConfigService.refresh(test_db)
        assert ConfigService._initialized is True


# ─── GET_BY_CATEGORY ─────────────────────────────────────────


class TestGetByCategory:
    def test_get_by_category(self):
        ConfigService._cache["security.key1"] = "val1"
        ConfigService._cache["security.key2"] = "val2"
        ConfigService._cache["features.other"] = "val3"

        result = ConfigService.get_by_category(ConfigCategory.SECURITY)
        assert len(result) == 2
        assert "security.key1" in result


# ─── CONVENIENCE METHODS ─────────────────────────────────────


class TestConvenienceMethods:
    def test_password_min_length_default(self):
        assert ConfigService.get_password_min_length() == 8

    def test_password_min_length_custom(self):
        ConfigService._cache["security.password_min_length"] = 12
        assert ConfigService.get_password_min_length() == 12

    def test_password_requirements(self):
        result = ConfigService.get_password_requirements()
        assert "uppercase" in result
        assert "lowercase" in result
        assert "numbers" in result
        assert "special" in result

    def test_max_login_attempts_default(self):
        assert ConfigService.get_max_login_attempts() == 5

    def test_lockout_duration_default(self):
        assert ConfigService.get_lockout_duration_minutes() == 15

    def test_session_timeout_default(self):
        assert ConfigService.get_session_timeout_minutes() == 30

    def test_registration_enabled_default(self):
        assert ConfigService.is_user_registration_enabled() is True

    def test_email_whitelist_default(self):
        assert ConfigService.is_email_whitelist_enabled() is True

    def test_smtp_settings(self):
        result = ConfigService.get_smtp_settings()
        assert result["server"] == "localhost"
        assert result["port"] == 587

    def test_llm_settings(self):
        result = ConfigService.get_llm_settings("openai")
        assert result["temperature"] == 0.7
        assert result["max_tokens"] == 4096

    def test_export_settings(self):
        result = ConfigService.get_export_settings()
        assert "quarto_path" in result
        assert "formats_enabled" in result

    def test_file_upload_settings(self):
        result = ConfigService.get_file_upload_settings()
        assert result["enabled"] is True

    def test_ai_enabled_default(self):
        assert ConfigService.is_ai_enabled() is True


# ─── PARSE VALUE ─────────────────────────────────────────────


class TestParseValue:
    def test_parse_boolean(self):
        assert ConfigService._parse_value("true", "boolean") is True
        assert ConfigService._parse_value("false", "boolean") is False

    def test_parse_integer(self):
        assert ConfigService._parse_value("42", "integer") == 42

    def test_parse_integer_invalid(self):
        assert ConfigService._parse_value("abc", "integer") == "abc"

    def test_parse_float(self):
        assert ConfigService._parse_value("3.14", "float") == 3.14

    def test_parse_json(self):
        assert ConfigService._parse_value('{"a": 1}', "json") == {"a": 1}

    def test_parse_json_invalid(self):
        assert ConfigService._parse_value("not json", "json") == "not json"

    def test_parse_string(self):
        assert ConfigService._parse_value("hello", "string") == "hello"
