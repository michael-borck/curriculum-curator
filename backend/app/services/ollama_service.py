"""
Ollama service for managing local AI models.

Wraps the Ollama HTTP API for status checking, model management,
and RAM-based model recommendations.
"""

import json
import logging
from collections.abc import AsyncGenerator
from typing import Any

import httpx
import psutil

from app.core.config import settings

logger = logging.getLogger(__name__)


class OllamaService:
    """Service for interacting with an Ollama instance."""

    def __init__(self, base_url: str | None = None) -> None:
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")

    def _client(self, timeout: float | None = 10.0) -> httpx.AsyncClient:
        return httpx.AsyncClient(base_url=self.base_url, timeout=timeout)

    async def check_status(self) -> bool:
        """Ping Ollama to see if it's reachable."""
        try:
            async with self._client(timeout=5.0) as client:
                resp = await client.get("/api/tags")
                return resp.status_code == 200
        except (httpx.ConnectError, httpx.TimeoutException):
            return False

    async def list_models(self) -> list[dict[str, Any]]:
        """Return the list of locally installed models."""
        try:
            async with self._client() as client:
                resp = await client.get("/api/tags")
                resp.raise_for_status()
                data = resp.json()
                return list(data.get("models", []))
        except (httpx.ConnectError, httpx.TimeoutException, httpx.HTTPStatusError):
            return []

    def recommend_model(self) -> dict[str, Any]:
        """Pick the best model based on available system RAM."""
        mem = psutil.virtual_memory()
        total_gb = mem.total / (1024**3)

        if total_gb < 8:
            model = "tinyllama"
            label = "TinyLlama (1.1B)"
            reason = f"Your system has {total_gb:.0f} GB RAM. TinyLlama is lightweight and runs well on low-memory systems."
        elif total_gb < 16:
            model = "llama3.2"
            label = "Llama 3.2 (3B)"
            reason = f"Your system has {total_gb:.0f} GB RAM. Llama 3.2 3B offers a good balance of quality and performance."
        else:
            model = "mistral"
            label = "Mistral (7B)"
            reason = f"Your system has {total_gb:.0f} GB RAM. Mistral 7B provides excellent quality for content generation."

        return {
            "recommended_model": model,
            "label": label,
            "reason": reason,
            "total_ram_gb": round(total_gb, 1),
            "available_ram_gb": round(mem.available / (1024**3), 1),
        }

    async def pull_model(self, model_name: str) -> AsyncGenerator[dict[str, Any], None]:
        """Stream model download progress from Ollama POST /api/pull."""
        async with (
            self._client(timeout=None) as client,
            client.stream(
                "POST",
                "/api/pull",
                json={"name": model_name, "stream": True},
            ) as resp,
        ):
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    yield data
                except json.JSONDecodeError:
                    continue

    async def delete_model(self, model_name: str) -> bool:
        """Delete a model from Ollama."""
        try:
            async with self._client() as client:
                resp = await client.request(
                    "DELETE", "/api/delete", json={"name": model_name}
                )
                return resp.status_code == 200
        except (httpx.ConnectError, httpx.TimeoutException):
            return False

    async def test_generation(
        self, model_name: str, prompt: str = "Say hello in one sentence."
    ) -> dict[str, Any]:
        """Run a quick generation test to verify a model works."""
        try:
            async with self._client(timeout=60.0) as client:
                resp = await client.post(
                    "/api/generate",
                    json={"model": model_name, "prompt": prompt, "stream": False},
                )
                resp.raise_for_status()
                data = resp.json()
                return {
                    "success": True,
                    "response": data.get("response", ""),
                    "model": model_name,
                }
        except (httpx.ConnectError, httpx.TimeoutException) as e:
            return {
                "success": False,
                "error": f"Connection failed: {e}",
                "model": model_name,
            }
        except httpx.HTTPStatusError as e:
            return {
                "success": False,
                "error": f"HTTP {e.response.status_code}: {e.response.text}",
                "model": model_name,
            }


ollama_service = OllamaService()
