"""
Mock implementations for testing
"""

from typing import Any
from unittest.mock import AsyncMock, MagicMock


class MockLLMService:
    """Mock LLM service for testing"""

    def __init__(self):
        self.models = {}

    async def generate_content(
        self,
        content_type: str,
        pedagogy_style: str,
        context: dict[str, Any],
        stream: bool = False,
    ):
        """Mock content generation"""
        if stream:

            async def mock_stream():
                for word in ["This", "is", "a", "test", "response"]:
                    yield word + " "

            return mock_stream()
        else:

            async def mock_response():
                yield "This is a test response"

            return mock_response()

    def _build_pedagogy_prompt(self, style: str) -> str:
        return f"Mock pedagogy prompt for {style}"

    def _build_content_prompt(self, content_type: str, context: dict) -> str:
        return f"Mock content prompt for {content_type}"


# Create a mock instance
mock_llm_service = MockLLMService()
