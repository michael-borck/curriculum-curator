"""Tests for the Resend HTTP-API email provider (EMAIL_PROVIDER=resend)."""

import io
import json
import urllib.error

import pytest

from app.core.smtp_config import EmailProvider, SMTPConfig
from app.services.email_service import EmailService


def _resend_service() -> EmailService:
    svc = EmailService()
    svc.smtp_config = SMTPConfig(
        provider=EmailProvider.RESEND,
        resend_api_key="re_test_key",
        from_email="noreply@example.com",
        from_name="Curriculum Curator",
    )
    return svc


class TestResendConfig:
    def test_is_configured_with_key(self) -> None:
        cfg = SMTPConfig(
            provider=EmailProvider.RESEND,
            resend_api_key="re_x",
            from_email="a@b.com",
        )
        assert cfg.is_configured() is True

    def test_not_configured_without_key(self) -> None:
        cfg = SMTPConfig(provider=EmailProvider.RESEND, from_email="a@b.com")
        assert cfg.is_configured() is False

    def test_test_connection_reports_key_state(self) -> None:
        ok, _ = _resend_service().test_smtp_connection()
        assert ok is True


class TestResendSend:
    def test_send_success_builds_request(self, monkeypatch) -> None:  # type: ignore[no-untyped-def]
        captured: dict[str, object] = {}

        class _Resp:
            status = 200

            def __enter__(self):  # type: ignore[no-untyped-def]
                return self

            def __exit__(self, *_a):  # type: ignore[no-untyped-def]
                return False

        def fake_urlopen(req, timeout=None):  # type: ignore[no-untyped-def]
            captured["req"] = req
            return _Resp()

        monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)

        svc = _resend_service()
        ok = svc._send_resend_api(
            subject="Hi",
            recipient="user@example.com",
            html_body="<b>x</b>",
            text_body="x",
        )
        assert ok is True

        req = captured["req"]
        assert req.full_url == "https://api.resend.com/emails"  # type: ignore[attr-defined]
        assert req.get_header("Authorization") == "Bearer re_test_key"  # type: ignore[attr-defined]
        body = json.loads(req.data.decode())  # type: ignore[attr-defined]
        assert body["to"] == ["user@example.com"]
        assert body["subject"] == "Hi"
        assert body["html"] == "<b>x</b>"
        assert "noreply@example.com" in body["from"]

    def test_send_raises_with_resend_error_body(self, monkeypatch) -> None:  # type: ignore[no-untyped-def]
        def fake_urlopen(req, timeout=None):  # type: ignore[no-untyped-def]
            raise urllib.error.HTTPError(
                url="https://api.resend.com/emails",
                code=422,
                msg="Unprocessable",
                hdrs=None,  # type: ignore[arg-type]
                fp=io.BytesIO(b'{"message":"domain not verified"}'),
            )

        monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)

        svc = _resend_service()
        with pytest.raises(
            RuntimeError, match=r"Resend API error 422.*domain not verified"
        ):
            svc._send_resend_api(
                subject="Hi", recipient="u@e.com", html_body="x", text_body="x"
            )

    def test_deliver_routes_resend_to_api_not_smtp(self, monkeypatch) -> None:  # type: ignore[no-untyped-def]
        called: dict[str, bool] = {}
        svc = _resend_service()
        monkeypatch.setattr(
            svc, "_send_resend_api", lambda **_kw: called.setdefault("api", True)
        )
        monkeypatch.setattr(
            svc, "_send_raw", lambda **_kw: called.setdefault("smtp", True)
        )
        svc._deliver(subject="s", recipient="r@e.com", html_body="h", text_body="t")
        assert called == {"api": True}
