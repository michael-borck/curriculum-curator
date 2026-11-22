"""AUDIT.md Step 2/9 regression tests: secrets and LLM config resolution."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from pydantic import ValidationError

if TYPE_CHECKING:
    from fastapi.testclient import TestClient
    from sqlalchemy.orm import Session

    from app.models.user import User

STRONG = "correct-horse-battery-staple-32plus-chars!"


class TestSecretKeyValidator:
    @pytest.mark.parametrize(
        "bad",
        [
            "dev-secret-key-change-in-production",
            "your-secret-key-change-this-in-production",
            "change-me-to-a-random-string",
            "ci-test-secret",
            "test-secret-key-for-testing",
            "short",
            "docker-dev-secret-key-abc123",
        ],
    )
    def test_rejects_known_and_short_secrets(self, bad: str) -> None:
        from app.core.config import Settings

        with pytest.raises(ValidationError):
            Settings(_env_file=None, SECRET_KEY=bad, DEBUG=False, TESTING=False)

    def test_rejects_default_even_in_debug(self) -> None:
        from app.core.config import Settings

        with pytest.raises(ValidationError):
            Settings(
                _env_file=None,
                SECRET_KEY="dev-secret-key-change-in-production",
                DEBUG=True,
                TESTING=False,
            )

    def test_accepts_strong_secret(self) -> None:
        from app.core.config import Settings

        s = Settings(_env_file=None, SECRET_KEY=STRONG, DEBUG=False, TESTING=False)
        assert s.SECRET_KEY == STRONG

    def test_testing_mode_exempt(self) -> None:
        from app.core.config import Settings

        s = Settings(_env_file=None, SECRET_KEY="x", TESTING=True)
        assert s.SECRET_KEY == "x"

    def test_local_mode_with_public_domain_rejected(self) -> None:
        from app.core.config import Settings

        with pytest.raises(ValidationError):
            Settings(
                _env_file=None,
                SECRET_KEY=STRONG,
                LOCAL_MODE=True,
                PUBLIC_DOMAIN="example.com",
                TESTING=False,
            )


class TestSecretCrypto:
    def test_roundtrip_and_not_plaintext(self) -> None:
        from app.core.secret_crypto import decrypt_secret, encrypt_secret

        enc = encrypt_secret("sk-live-1234567890")
        assert enc is not None
        assert "sk-live" not in enc
        assert decrypt_secret(enc) == "sk-live-1234567890"

    def test_legacy_plaintext_passthrough(self) -> None:
        from app.core.secret_crypto import decrypt_secret

        assert decrypt_secret("plain-old-key") == "plain-old-key"
        assert decrypt_secret(None) is None
        assert decrypt_secret("") is None


class TestLLMConfigStorageAndResolution:
    def test_created_key_stored_encrypted_and_used(
        self, client: TestClient, test_db: Session, test_user: User
    ) -> None:
        from app.core.secret_crypto import decrypt_secret
        from app.models.llm_config import LLMConfiguration

        resp = client.post(
            "/api/llm-config/configurations",
            json={
                "provider": "openai",
                "apiKey": "sk-user-secret-9999",
                "modelName": "gpt-4",
                "isDefault": True,
            },
        )
        assert resp.status_code == 200, resp.text

        row = test_db.query(LLMConfiguration).one()
        assert row.api_key != "sk-user-secret-9999"
        assert "sk-user-secret" not in (row.api_key or "")
        assert decrypt_secret(row.api_key) == "sk-user-secret-9999"

        from app.services.llm_service import LLMService

        db_user = test_db.query(type(test_user)).filter_by(id=test_user.id).one()
        _model, provider, api_key, _base = LLMService()._get_llm_config(db_user, test_db)
        assert provider == "openai"
        assert api_key == "sk-user-secret-9999"

    def test_kill_switch_blocks_user_keys(
        self, test_db: Session, test_user: User
    ) -> None:
        import uuid

        from app.core.secret_crypto import encrypt_secret
        from app.models.llm_config import LLMConfiguration
        from app.models.system_settings import SystemSettings
        from app.services.llm_service import LLMService

        test_db.add(
            LLMConfiguration(
                id=str(uuid.uuid4()),
                user_id=test_user.id,
                provider="openai",
                api_key=encrypt_secret("sk-blocked"),
                model_name="gpt-4",
                is_default=True,
                is_active=True,
            )
        )
        test_db.add(
            SystemSettings(
                id=str(uuid.uuid4()),
                key="allow_user_api_keys",
                value="false",
            )
        )
        test_db.commit()
        test_db.refresh(test_user)

        _m, _p, api_key, _b = LLMService()._get_llm_config(test_user, test_db)
        assert api_key != "sk-blocked"
