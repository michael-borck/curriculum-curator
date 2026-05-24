"""Tests for llm_service.generate_structured_content (the strict + retry engine).

Covers the flexibility added for candidate #2 (system_prompt, inject_schema,
max_tokens, generic return) and the ADR-045 retry/validate contract.
"""

from collections.abc import Iterator
from contextlib import contextmanager
from unittest.mock import AsyncMock, Mock, patch

import pytest
from pydantic import BaseModel

from app.services.llm_service import LLMService


class _Sample(BaseModel):
    name: str
    count: int = 0


def _resp(content: str) -> Mock:
    r = Mock()
    r.choices = [Mock(message=Mock(content=content))]
    r.usage = None  # keep _log_usage from touching Mock attrs
    return r


@contextmanager
def _mocked_acompletion(
    *, return_value: Mock | None = None, side_effect: list[Mock] | None = None
) -> Iterator[AsyncMock]:
    """Patch acompletion + settings so _get_llm_config resolves to openai."""
    with (
        patch(
            "app.services.llm_service.acompletion", new_callable=AsyncMock
        ) as mock_acompletion,
        patch("app.services.llm_service.settings") as mock_settings,
    ):
        if side_effect is not None:
            mock_acompletion.side_effect = side_effect
        else:
            mock_acompletion.return_value = return_value
        mock_settings.OPENAI_API_KEY = "test-key"
        mock_settings.ANTHROPIC_API_KEY = None
        mock_settings.GEMINI_API_KEY = None
        mock_settings.DEFAULT_LLM_PROVIDER = "openai"
        mock_settings.DEFAULT_LLM_MODEL = "gpt-4"
        yield mock_acompletion


def _service() -> LLMService:
    service = LLMService()
    service.providers = {"openai": True}
    return service


def _db() -> Mock:
    db = Mock()
    db.query.return_value.filter.return_value.all.return_value = []
    return db


@pytest.mark.asyncio
async def test_returns_validated_model():
    with _mocked_acompletion(return_value=_resp('{"name": "widget", "count": 3}')):
        result, error = await _service().generate_structured_content(
            prompt="make a widget", response_model=_Sample, db=_db()
        )
    assert error is None
    assert isinstance(result, _Sample)
    assert result.name == "widget"
    assert result.count == 3


@pytest.mark.asyncio
async def test_custom_system_prompt_is_used():
    with _mocked_acompletion(return_value=_resp('{"name": "x"}')) as mock_acompletion:
        await _service().generate_structured_content(
            prompt="p",
            response_model=_Sample,
            db=_db(),
            system_prompt="HARDENED <user_data> defence",
        )
    messages = mock_acompletion.call_args.kwargs["messages"]
    assert messages[0]["role"] == "system"
    assert messages[0]["content"] == "HARDENED <user_data> defence"


@pytest.mark.asyncio
async def test_inject_schema_toggle():
    # inject_schema=False → the model's JSON schema is NOT appended to the prompt.
    with _mocked_acompletion(return_value=_resp('{"name": "x"}')) as mock_acompletion:
        await _service().generate_structured_content(
            prompt="PROMPT_BODY",
            response_model=_Sample,
            db=_db(),
            inject_schema=False,
        )
    user_msg = mock_acompletion.call_args.kwargs["messages"][1]["content"]
    assert user_msg == "PROMPT_BODY"
    assert "schema" not in user_msg.lower()

    # inject_schema=True (default) → schema instructions appended.
    with _mocked_acompletion(return_value=_resp('{"name": "x"}')) as mock_acompletion:
        await _service().generate_structured_content(
            prompt="PROMPT_BODY", response_model=_Sample, db=_db()
        )
    user_msg = mock_acompletion.call_args.kwargs["messages"][1]["content"]
    assert "PROMPT_BODY" in user_msg
    assert "schema" in user_msg.lower()


@pytest.mark.asyncio
async def test_max_tokens_passed_through():
    with _mocked_acompletion(return_value=_resp('{"name": "x"}')) as mock_acompletion:
        await _service().generate_structured_content(
            prompt="p", response_model=_Sample, db=_db(), max_tokens=4096
        )
    assert mock_acompletion.call_args.kwargs["max_tokens"] == 4096


@pytest.mark.asyncio
async def test_retries_on_bad_json_then_succeeds():
    side = [_resp("not json at all"), _resp('{"name": "recovered"}')]
    with _mocked_acompletion(side_effect=side) as mock_acompletion:
        result, error = await _service().generate_structured_content(
            prompt="p", response_model=_Sample, db=_db()
        )
    assert error is None
    assert result is not None
    assert result.name == "recovered"
    assert mock_acompletion.call_count == 2


@pytest.mark.asyncio
async def test_returns_error_after_persistent_bad_json():
    with _mocked_acompletion(return_value=_resp("still not json")) as mock_acompletion:
        result, error = await _service().generate_structured_content(
            prompt="p", response_model=_Sample, db=_db(), max_retries=3
        )
    assert result is None
    assert error is not None
    assert mock_acompletion.call_count == 3


@pytest.mark.asyncio
async def test_validation_error_retries():
    # First response is valid JSON but missing required 'name' → ValidationError,
    # then a complete one succeeds.
    side = [_resp('{"count": 5}'), _resp('{"name": "fixed", "count": 5}')]
    with _mocked_acompletion(side_effect=side) as mock_acompletion:
        result, error = await _service().generate_structured_content(
            prompt="p", response_model=_Sample, db=_db()
        )
    assert error is None
    assert result is not None
    assert result.name == "fixed"
    assert mock_acompletion.call_count == 2
