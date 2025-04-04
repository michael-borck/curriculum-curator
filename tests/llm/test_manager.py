import pytest
import os
import yaml
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

from curriculum_curator.llm.manager import LLMManager, LLMRequest
from curriculum_curator.utils.exceptions import LLMRequestError

# Sample configuration for testing
TEST_CONFIG = {
    "llm": {
        "default_provider": "test_provider",
        "aliases": {
            "test_alias": "test_provider/test_model"
        },
        "providers": {
            "test_provider": {
                "api_key": "test_api_key",
                "default_model": "test_model",
                "cost_per_1k_tokens": {
                    "input": 0.10,
                    "output": 0.20
                },
                "models": {
                    "test_model": {}
                }
            }
        }
    }
}


@pytest.fixture
def llm_manager():
    """Create an LLMManager instance with test configuration."""
    return LLMManager(TEST_CONFIG)


class TestLLMRequest:
    """Tests for the LLMRequest class."""

    def test_init(self):
        """Test LLMRequest initialization."""
        request = LLMRequest(
            prompt="Test prompt",
            provider="test_provider",
            model="test_model",
            workflow_id="test_workflow",
            step_name="test_step"
        )
        
        assert request.prompt == "Test prompt"
        assert request.provider == "test_provider"
        assert request.model == "test_model"
        assert request.workflow_id == "test_workflow"
        assert request.step_name == "test_step"
        assert request.status == "pending"
        assert request.error is None
        assert request.input_tokens is None
        assert request.output_tokens is None
        assert request.completion is None
        assert request.duration is None
        assert request.cost is None


class TestLLMManager:
    """Tests for the LLMManager class."""

    def test_init(self, llm_manager):
        """Test LLMManager initialization."""
        assert llm_manager.config == TEST_CONFIG
        assert llm_manager.history == []
        assert llm_manager.current_workflow_id is None
        assert llm_manager.current_step_name is None

    def test_resolve_model_alias_default(self, llm_manager):
        """Test resolving a model alias to default provider and model."""
        provider, model = llm_manager._resolve_model_alias()
        assert provider == "test_provider"
        assert model == "test_model"

    def test_resolve_model_alias_explicit(self, llm_manager):
        """Test resolving an explicit provider/model alias."""
        provider, model = llm_manager._resolve_model_alias("test_provider/test_model")
        assert provider == "test_provider"
        assert model == "test_model"

    def test_resolve_model_alias_named(self, llm_manager):
        """Test resolving a named alias."""
        provider, model = llm_manager._resolve_model_alias("test_alias")
        assert provider == "test_provider"
        assert model == "test_model"

    def test_resolve_model_alias_fallback(self, llm_manager):
        """Test resolving an unknown alias falls back to default."""
        provider, model = llm_manager._resolve_model_alias("unknown_alias")
        assert provider == "test_provider"
        assert model == "test_model"

    def test_calculate_cost(self, llm_manager):
        """Test cost calculation based on token counts."""
        request = LLMRequest(
            prompt="Test prompt",
            provider="test_provider",
            model="test_model"
        )
        request.input_tokens = 1000
        request.output_tokens = 500
        
        llm_manager._calculate_cost(request)
        
        # 1000 input tokens at $0.10 per 1k = $0.10
        # 500 output tokens at $0.20 per 1k = $0.10
        # Total: $0.20
        assert request.cost == 0.20

    @patch('litellm.acompletion')
    @pytest.mark.asyncio
    async def test_generate(self, mock_acompletion, llm_manager):
        """Test generating text from LLM."""
        # Configure the mock response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Test response"
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 5
        mock_acompletion.return_value = mock_response
        
        # Call the generate method
        result = await llm_manager.generate("Test prompt")
        
        # Verify the result
        assert result == "Test response"
        
        # Verify the mock was called correctly
        mock_acompletion.assert_called_once()
        call_args = mock_acompletion.call_args[1]
        assert call_args["model"] == "test_provider/test_model"
        assert call_args["messages"] == [{"role": "user", "content": "Test prompt"}]
        
        # Verify request object is added to history
        assert len(llm_manager.history) == 1
        request = llm_manager.history[0]
        assert request.status == "success"
        assert request.completion == "Test response"
        assert request.input_tokens == 10
        assert request.output_tokens == 5
        assert request.cost is not None
        assert request.duration is not None

    @patch('litellm.acompletion')
    @pytest.mark.asyncio
    async def test_generate_error(self, mock_acompletion, llm_manager):
        """Test error handling in generate method."""
        # Configure the mock to raise an exception
        mock_acompletion.side_effect = Exception("Test error")
        
        # Call the generate method with error handling
        with pytest.raises(LLMRequestError):
            await llm_manager.generate("Test prompt")
        
        # Verify request object is added to history with error status
        assert len(llm_manager.history) == 1
        request = llm_manager.history[0]
        assert request.status == "error"
        assert request.error == "Test error"

    def test_generate_usage_report(self, llm_manager):
        """Test generating usage reports."""
        # Add some mock requests to history
        request1 = LLMRequest(
            prompt="Test prompt 1",
            provider="test_provider",
            model="test_model",
            workflow_id="workflow1",
            step_name="step1"
        )
        request1.status = "success"
        request1.input_tokens = 100
        request1.output_tokens = 50
        request1.cost = 0.15
        request1.duration = 1.5
        
        request2 = LLMRequest(
            prompt="Test prompt 2",
            provider="test_provider",
            model="test_model",
            workflow_id="workflow1",
            step_name="step2"
        )
        request2.status = "success"
        request2.input_tokens = 200
        request2.output_tokens = 100
        request2.cost = 0.3
        request2.duration = 2.5
        
        llm_manager.history = [request1, request2]
        
        # Generate report for all workflow steps
        report = llm_manager.generate_usage_report(workflow_id="workflow1")
        
        # Verify report structure and totals
        assert "by_model" in report
        assert "totals" in report
        assert "timestamp" in report
        assert report["workflow_id"] == "workflow1"
        
        by_model = report["by_model"]
        assert "test_provider/test_model" in by_model
        assert by_model["test_provider/test_model"]["count"] == 2
        assert by_model["test_provider/test_model"]["input_tokens"] == 300
        assert by_model["test_provider/test_model"]["output_tokens"] == 150
        assert by_model["test_provider/test_model"]["cost"] == 0.45
        
        totals = report["totals"]
        assert totals["count"] == 2
        assert totals["input_tokens"] == 300
        assert totals["output_tokens"] == 150
        assert totals["cost"] == 0.45
        assert totals["errors"] == 0
        
        # Generate report filtered by step
        step_report = llm_manager.generate_usage_report(workflow_id="workflow1", step_name="step1")
        assert step_report["by_model"]["test_provider/test_model"]["count"] == 1
        assert step_report["by_model"]["test_provider/test_model"]["input_tokens"] == 100
        assert step_report["totals"]["count"] == 1