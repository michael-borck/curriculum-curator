"""AUDIT.md Step 4 regression tests: user-supplied outbound URLs."""

from __future__ import annotations

import pytest

from app.core.config import settings
from app.services.llm_service import LLMService
from app.services.search_router import SearchRouter


@pytest.mark.asyncio
async def test_custom_api_base_rejects_loopback(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "LOCAL_MODE", False)
    with pytest.raises(ValueError):
        await LLMService._assert_safe_api_base("custom", "http://127.0.0.1:9000/v1")


@pytest.mark.asyncio
async def test_custom_api_base_allows_public(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "LOCAL_MODE", False)
    # A public literal address should pass (no network call is made).
    await LLMService._assert_safe_api_base("custom", "https://1.1.1.1/v1")


@pytest.mark.asyncio
async def test_ollama_api_base_unrestricted(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "LOCAL_MODE", False)
    await LLMService._assert_safe_api_base("ollama", "http://127.0.0.1:11434")


@pytest.mark.asyncio
async def test_local_mode_allows_private_custom_base(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "LOCAL_MODE", True)
    await LLMService._assert_safe_api_base("custom", "http://192.168.1.10:8080/v1")


@pytest.mark.asyncio
async def test_user_searxng_private_url_is_refused(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "LOCAL_MODE", False)

    called = False

    async def fake_search(*_args: object, **_kwargs: object) -> list[object]:
        nonlocal called
        called = True
        return []

    monkeypatch.setattr(
        "app.services.search_router.web_search_service.search", fake_search
    )

    results = await SearchRouter()._search_searxng(
        "test", 5, {"searxngUrl": "http://127.0.0.1:8080"}
    )
    assert results == []
    assert called is False
