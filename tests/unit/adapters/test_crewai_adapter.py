"""Unit tests for CrewAI adapter."""

import pytest
import sys
import unittest.mock as mock
from typing import Dict, Any

from contexa_sdk.core.model import ContexaModel
from contexa_sdk.adapters.crewai import CrewAIAdapter


@pytest.fixture
def patch_imports(monkeypatch, mock_crewai):
    """Patch imports for CrewAI modules."""
    original_import = __import__
    
    def mock_import(name, *args, **kwargs):
        if name == "crewai":
            return mock_crewai.get(name, original_import(name, *args, **kwargs))
        return original_import(name, *args, **kwargs)
    
    monkeypatch.setattr("builtins.__import__", mock_import)
    monkeypatch.setattr("contexa_sdk.adapters.crewai.Agent", mock_crewai["crewai"].Agent)
    monkeypatch.setattr("contexa_sdk.adapters.crewai.Crew", mock_crewai["crewai"].Crew)
    monkeypatch.setattr("contexa_sdk.adapters.crewai.Tool", mock_crewai["crewai"].Tool)


class TestCrewAIAdapter:
    """Test cases for CrewAIAdapter."""
    
    def test_init(self):
        """Test adapter initialization."""
        adapter = CrewAIAdapter()
        assert isinstance(adapter, CrewAIAdapter)
    
    def test_model_with_openai_model(self, patch_imports):
        """Test model conversion for OpenAI model with CrewAI adapter."""
        # Arrange
        adapter = CrewAIAdapter()
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
        assert "crewai_model" in result
        assert result["crewai_model"] == "gpt-4o"
        assert "config" in result
        assert "temperature" in result["config"]
        assert result["config"]["temperature"] == 0.7
    
    def test_model_with_anthropic_model(self, patch_imports):
        """Test model conversion for Anthropic model with CrewAI adapter."""
        # Arrange
        adapter = CrewAIAdapter()
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
        assert "crewai_model" in result
        assert result["crewai_model"] == "claude-3-opus"
        assert "config" in result
        assert "temperature" in result["config"]
    
    def test_model_with_custom_model(self, patch_imports):
        """Test model conversion for custom model with CrewAI adapter."""
        # Arrange
        adapter = CrewAIAdapter()
        model = ContexaModel(
            model_name="custom-model",
            provider="custom",
            config={
                "api_key": "test-key",
                "temperature": 0.7,
                "endpoint": "https://custom-endpoint.com"
            }
        )
        
        # Act
        result = adapter.model(model)
        
        # Assert
        assert isinstance(result, dict)
        assert "model_name" in result
        assert result["model_name"] == "custom-model"
        assert "provider" in result
        assert result["provider"] == "custom"
        # For custom models, check if crewai_model is a callback or appropriate value
        assert "crewai_model" in result
        assert result["config"]["endpoint"] == "https://custom-endpoint.com"
    
    def test_model_with_import_error(self, monkeypatch):
        """Test model conversion with CrewAI import error."""
        # Arrange
        adapter = CrewAIAdapter()
        model = ContexaModel(
            model_name="gpt-4o",
            provider="openai",
            config={"api_key": "test-key"}
        )
        
        # Make imports fail
        def mock_import_error(*args, **kwargs):
            raise ImportError("No module named 'crewai'")
        
        monkeypatch.setattr("contexa_sdk.adapters.crewai.Agent", mock_import_error)
        
        # Act
        result = adapter.model(model)
        
        # Assert
        assert isinstance(result, dict)
        assert "model_name" in result
        assert result["model_name"] == "gpt-4o"
        assert "provider" in result
        assert "crewai_model" in result
        assert "config" in result
    
    @pytest.mark.asyncio
    async def test_agent_with_model_dictionary(self, patch_imports):
        """Test agent conversion with the new model dictionary format."""
        # Arrange
        adapter = CrewAIAdapter()
        
        # Mock the model method to return the standardized dictionary
        model_dict = {
            "model_name": "gpt-4o",
            "provider": "openai",
            "crewai_model": "gpt-4o",
            "config": {"temperature": 0.7}
        }
        
        with mock.patch.object(adapter, 'model', return_value=model_dict):
            from contexa_sdk.core.agent import ContexaAgent
            from contexa_sdk.core.tool import ContexaTool
            from contexa_sdk.core.model import ContexaModel
            
            # Create a test model
            model = ContexaModel(
                model_name="gpt-4o",
                provider="openai",
                config={"api_key": "test-key"}
            )
            
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
                # Act - Test both with and without crew wrapping
                result_with_crew = adapter.agent(agent)
                result_without_crew = adapter.agent(agent, wrap_in_crew=False)
                
                # Assert
                assert result_with_crew is not None
                assert result_without_crew is not None
                assert result_with_crew != result_without_crew  # Should be different objects 