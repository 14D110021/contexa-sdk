"""Unit tests for OpenAI adapter."""

import pytest
import sys
import unittest.mock as mock
from typing import Dict, Any

from contexa_sdk.core.model import ContexaModel
from contexa_sdk.adapters.openai import OpenAIAdapter


@pytest.fixture
def patch_imports(monkeypatch, mock_openai):
    """Patch imports for OpenAI modules."""
    original_import = __import__
    
    def mock_import(name, *args, **kwargs):
        if name == "openai" or name == "openai_agents":
            return mock_openai.get(name, original_import(name, *args, **kwargs))
        return original_import(name, *args, **kwargs)
    
    monkeypatch.setattr("builtins.__import__", mock_import)
    monkeypatch.setattr("contexa_sdk.adapters.openai.OpenAI", mock_openai["openai"])
    monkeypatch.setattr("contexa_sdk.adapters.openai.Agent", mock_openai["openai_agents"].Agent)
    monkeypatch.setattr("contexa_sdk.adapters.openai.Tool", mock_openai["openai_agents"].Tool)


class TestOpenAIAdapter:
    """Test cases for OpenAIAdapter."""
    
    def test_init(self):
        """Test adapter initialization."""
        adapter = OpenAIAdapter()
        assert isinstance(adapter, OpenAIAdapter)
    
    def test_model_with_openai_model(self, patch_imports):
        """Test model conversion for OpenAI model."""
        # Arrange
        adapter = OpenAIAdapter()
        model = ContexaModel(
            model_name="gpt-4o",
            provider="openai",
            config={
                "api_key": "test-key",
                "temperature": 0.7,
                "max_tokens": 500
            }
        )
        
        # Act
        result = adapter.model(model)
        
        # Assert
        assert isinstance(result, dict)
        assert "model_name" in result
        assert result["model_name"] == "gpt-4o"
        assert "provider" in result
        assert result["provider"] == "openai"
        assert "config" in result
        assert "temperature" in result["config"]
        assert result["config"]["temperature"] == 0.7
        assert "max_tokens" in result["config"]
        assert result["config"]["max_tokens"] == 500
    
    def test_model_with_anthropic_model(self, patch_imports):
        """Test model conversion for non-OpenAI model."""
        # Arrange
        adapter = OpenAIAdapter()
        model = ContexaModel(
            model_name="claude-3-opus",
            provider="anthropic",
            config={
                "api_key": "test-anthropic-key",
                "temperature": 0.5,
                "max_tokens": 1000
            }
        )
        
        # Act
        result = adapter.model(model)
        
        # Assert
        assert isinstance(result, dict)
        assert "model_name" in result
        assert result["model_name"] == "claude-3-opus"
        assert "provider" in result
        assert result["provider"] == "anthropic"
        assert "config" in result
        assert "temperature" in result["config"]
        assert result["config"]["temperature"] == 0.5
    
    def test_model_with_no_api_key(self, patch_imports):
        """Test model conversion when no API key is provided."""
        # Arrange
        adapter = OpenAIAdapter()
        model = ContexaModel(
            model_name="gpt-4o",
            provider="openai",
            config={
                "temperature": 0.7
            }
        )
        
        # Act
        result = adapter.model(model)
        
        # Assert
        assert isinstance(result, dict)
        assert "model_name" in result
        assert "client" not in result or result["client"] is None
        assert "config" in result
        assert "api_key" not in result["config"]
    
    def test_model_with_import_error(self, monkeypatch):
        """Test model conversion with OpenAI import error."""
        # Arrange
        adapter = OpenAIAdapter()
        model = ContexaModel(
            model_name="gpt-4o",
            provider="openai",
            config={"api_key": "test-key"}
        )
        
        # Make imports fail
        def mock_import_error(*args, **kwargs):
            raise ImportError("No module named 'openai'")
        
        monkeypatch.setattr("contexa_sdk.adapters.openai.OpenAI", mock_import_error)
        
        # Act
        result = adapter.model(model)
        
        # Assert
        assert isinstance(result, dict)
        assert "model_name" in result
        assert result["model_name"] == "gpt-4o"
        assert "client" not in result
        assert "config" in result
        
    @pytest.mark.asyncio
    async def test_agent_with_model_dictionary(self, patch_imports):
        """Test agent conversion with the new model dictionary format."""
        # Arrange
        adapter = OpenAIAdapter()
        model = ContexaModel(
            model_name="gpt-4o",
            provider="openai",
            config={"api_key": "test-key"}
        )
        
        # Mock the model method to return the standardized dictionary
        model_dict = {
            "model_name": "gpt-4o",
            "provider": "openai",
            "client": mock.MagicMock(),
            "config": {"temperature": 0.7}
        }
        
        with mock.patch.object(adapter, 'model', return_value=model_dict):
            from contexa_sdk.core.agent import ContexaAgent
            from contexa_sdk.core.tool import ContexaTool
            
            # Create a simple tool
            tool = mock.MagicMock(spec=ContexaTool)
            tool.name = "test_tool"
            tool.description = "A test tool"
            
            # Create a test agent
            agent = ContexaAgent(
                name="Test Agent",
                description="A test agent",
                model=model,
                tools=[tool],
                system_prompt="You are a helpful assistant"
            )
            
            # Also mock the tool method
            with mock.patch.object(adapter, 'tool', return_value=mock.MagicMock()):
                # Act
                result = adapter.agent(agent)
                
                # Assert
                assert result is not None
                # Additional assertions based on the expected structure of the OpenAI agent 