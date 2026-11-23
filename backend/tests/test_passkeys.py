"""Passkey registration options and credential management."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

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


def _user_and_token(client: TestClient, test_db: Session) -> tuple[str, str]:
    from app.core.security import get_password_hash
    from app.models.user import User

    user = User(
        id=str(uuid.uuid4()),
        email="passkey-user@example.com",
        password_hash=get_password_hash(PASSWORD),
        name="Passkey User",
        role="lecturer",
        is_verified=True,
        is_active=True,
    )
    test_db.add(user)
    test_db.commit()
    login = client.post(
        "/api/auth/login",
        json={"email": user.email, "password": PASSWORD},
    )
    return user.id, login.json()["access_token"]


def test_registration_options_shape(client: TestClient, test_db: Session) -> None:
    _, token = _user_and_token(client, test_db)
    response = client.post(
        "/api/auth/passkeys/register/options",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["challengeToken"]
    assert data["options"]["challenge"]
    assert data["options"]["rp"]["id"] == "localhost"
    assert data["options"]["user"]["name"] == "passkey-user@example.com"


def test_login_options_are_discoverable(client: TestClient) -> None:
    response = client.post("/api/auth/passkeys/login/options")
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["challengeToken"]
    assert data["options"]["challenge"]
    assert data["options"].get("allowCredentials", []) == []


def test_list_and_delete_owned_passkey(client: TestClient, test_db: Session) -> None:
    from app.models.webauthn_credential import WebAuthnCredential

    user_id, token = _user_and_token(client, test_db)
    row = WebAuthnCredential(
        user_id=user_id,
        credential_id="credential-id",
        public_key="cHVibGljLWtleQ",
        sign_count=0,
        name="Laptop",
    )
    test_db.add(row)
    test_db.commit()

    headers = {"Authorization": f"Bearer {token}"}
    listed = client.get("/api/auth/passkeys", headers=headers)
    assert listed.status_code == 200
    assert listed.json()["passkeys"][0]["name"] == "Laptop"

    deleted = client.delete(f"/api/auth/passkeys/{row.id}", headers=headers)
    assert deleted.status_code == 200
    assert client.get("/api/auth/passkeys", headers=headers).json()["passkeys"] == []
