"""TOTP setup, login challenge, recovery codes, and disable flow."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

import pyotp
import pytest
from fastapi.testclient import TestClient

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


PASSWORD = "Str0ng-Passw0rd!23"


@pytest.fixture
def client(test_db: Session):
    from app.api import deps
    from app.core import database as core_database
    from app.main import app

    def _override_get_db():
        yield test_db

    app.dependency_overrides[deps.get_db] = _override_get_db
    app.dependency_overrides[core_database.get_db] = _override_get_db
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c
    app.dependency_overrides.clear()


def _make_user(db: Session):
    from app.core.security import get_password_hash
    from app.models.user import User

    user = User(
        id=str(uuid.uuid4()),
        email="totp-user@example.com",
        password_hash=get_password_hash(PASSWORD),
        name="TOTP User",
        role="lecturer",
        is_verified=True,
        is_active=True,
    )
    db.add(user)
    db.commit()
    return user


def _login(client: TestClient):
    return client.post(
        "/api/auth/login",
        json={"email": "totp-user@example.com", "password": PASSWORD},
    )


def _bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _enable_totp(client: TestClient, token: str) -> tuple[str, list[str]]:
    setup = client.post("/api/auth/totp/setup", headers=_bearer(token))
    assert setup.status_code == 200, setup.text
    data = setup.json()
    code = pyotp.TOTP(data["secret"]).now()
    enabled = client.post(
        "/api/auth/totp/enable", headers=_bearer(token), json={"code": code}
    )
    assert enabled.status_code == 200, enabled.text
    return data["secret"], data["recoveryCodes"]


def test_totp_login_challenge_and_replay(client: TestClient, test_db: Session) -> None:
    _make_user(test_db)
    login = _login(client)
    assert login.status_code == 200
    token = login.json()["access_token"]

    secret, recovery = _enable_totp(client, token)
    assert len(recovery) == 10

    challenge = _login(client)
    assert challenge.status_code == 200
    body = challenge.json()
    assert body["mfaRequired"] is True
    assert body["access_token"] is None
    assert body["mfaToken"]

    code = pyotp.TOTP(secret).now()
    verified = client.post(
        "/api/auth/totp/verify",
        json={"mfaToken": body["mfaToken"], "code": code},
    )
    assert verified.status_code == 200, verified.text
    assert verified.json()["access_token"]

    # Same 30-second window must not be replayable.
    replay = client.post(
        "/api/auth/totp/verify",
        json={"mfaToken": body["mfaToken"], "code": code},
    )
    assert replay.status_code == 401


def test_totp_recovery_code_is_single_use(
    client: TestClient, test_db: Session
) -> None:
    _make_user(test_db)
    token = _login(client).json()["access_token"]
    _, recovery = _enable_totp(client, token)

    challenge = _login(client).json()
    used = client.post(
        "/api/auth/totp/verify",
        json={"mfaToken": challenge["mfaToken"], "code": recovery[0]},
    )
    assert used.status_code == 200

    status = client.get(
        "/api/auth/totp/status",
        headers=_bearer(used.json()["access_token"]),
    )
    assert status.json()["recoveryCodesRemaining"] == 9

    second = _login(client).json()
    reused = client.post(
        "/api/auth/totp/verify",
        json={"mfaToken": second["mfaToken"], "code": recovery[0]},
    )
    assert reused.status_code == 401


def test_totp_disable_requires_password_and_code(
    client: TestClient, test_db: Session
) -> None:
    _make_user(test_db)
    token = _login(client).json()["access_token"]
    _, recovery = _enable_totp(client, token)

    bad = client.post(
        "/api/auth/totp/disable",
        headers=_bearer(token),
        json={"password": "wrong", "code": recovery[0]},
    )
    assert bad.status_code == 400

    ok = client.post(
        "/api/auth/totp/disable",
        headers=_bearer(token),
        json={"password": PASSWORD, "code": recovery[1]},
    )
    assert ok.status_code == 200
    assert ok.json()["enabled"] is False
