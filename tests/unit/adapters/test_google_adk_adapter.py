"""Unit tests for Google ADK adapter."""

import pytest
import sys
import unittest.mock as mock
from typing import Dict, Any

from contexa_sdk.core.model import ContexaModel
from contexa_sdk.adapters.google_adk import GoogleAIAdapter


@pytest.fixture
def patch_imports(monkeypatch, mock_google_adk):
    """Patch imports for Google ADK modules."""
    original_import = __import__
    
    def mock_import(name, *args, **kwargs):
        if name.startswith("google"):
            return mock_google_adk.get(name, original_import(name, *args, **kwargs))
        return original_import(name, *args, **kwargs)
    
    monkeypatch.setattr("builtins.__import__", mock_import)
    
    # Patch the specific imports used in the Google ADK adapter
    monkeypatch.setattr(
        "contexa_sdk.adapters.google_adk.genai", 
        mock_google_adk["google.genai"]
    )
    monkeypatch.setattr(
        "contexa_sdk.adapters.google_adk.adk", 
        mock_google_adk["google.adk"]
    )


class TestGoogleAIAdapter:
    """Test cases for GoogleAIAdapter."""
    
    def test_init(self):
        """Test adapter initialization."""
        adapter = GoogleAIAdapter()
        assert isinstance(adapter, GoogleAIAdapter)
    
    def test_model_with_google_model(self, patch_imports):
        """Test model conversion for Google model in the Google ADK adapter."""
        # Arrange
        adapter = GoogleAIAdapter()
        model = ContexaModel(
            model_name="gemini-pro",
            provider="google",
            config={
                "api_key": "test-key",
                "temperature": 0.7,
                "max_output_tokens": 500
            }
        )
        
        # Act
        result = adapter.model(model)
        
        # Assert
        assert isinstance(result, dict)
        assert "model_name" in result
        assert result["model_name"] == "gemini-pro"
        assert "provider" in result
        assert result["provider"] == "google"
        assert "client" in result  # Should have a client field for Google ADK
        assert "config" in result
        assert "temperature" in result["config"]
        assert result["config"]["temperature"] == 0.7
    
    def test_model_with_non_google_model(self, patch_imports):
        """Test model conversion for non-Google model in the Google ADK adapter."""
        # Arrange
        adapter = GoogleAIAdapter()
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
    
    def test_model_with_different_gemini_model(self, patch_imports):
        """Test model conversion for a different Gemini model in the Google ADK adapter."""
        # Arrange
        adapter = GoogleAIAdapter()
        model = ContexaModel(
            model_name="gemini-ultra",
            provider="google",
            config={
                "api_key": "test-key",
                "temperature": 0.5,
                "max_output_tokens": 1000
            }
        )
        
        # Act
        result = adapter.model(model)
        
        # Assert
        assert isinstance(result, dict)
        assert "model_name" in result
        assert result["model_name"] == "gemini-ultra"
        assert "provider" in result
        assert result["provider"] == "google"
        assert "client" in result
        assert "config" in result
        assert "temperature" in result["config"]
    
    def test_model_with_vertex_model(self, patch_imports):
        """Test model conversion for a Vertex AI model in the Google ADK adapter."""
        # Arrange
        adapter = GoogleAIAdapter()
        model = ContexaModel(
            model_name="gemini-pro",
            provider="vertex",
            config={
                "project": "test-project",
                "location": "us-central1",
                "temperature": 0.5
            }
        )
        
        # Act
        result = adapter.model(model)
        
        # Assert
        assert isinstance(result, dict)
        assert "model_name" in result
        assert result["model_name"] == "gemini-pro"
        assert "provider" in result
        assert result["provider"] == "vertex"
        assert "config" in result
        assert "project" in result["config"]
        assert result["config"]["project"] == "test-project"
    
    def test_model_with_no_api_key(self, patch_imports):
        """Test model conversion when no API key is provided."""
        # Arrange
        adapter = GoogleAIAdapter()
        model = ContexaModel(
            model_name="gemini-pro",
            provider="google",
            config={
                "temperature": 0.7
            }
        )
        
        # Act
        result = adapter.model(model)
        
        # Assert
        assert isinstance(result, dict)
        assert "model_name" in result
        assert "api_key" not in result["config"]
    
    def test_model_with_import_error(self, monkeypatch):
        """Test model conversion with Google ADK import error."""
        # Arrange
        adapter = GoogleAIAdapter()
        model = ContexaModel(
            model_name="gemini-pro",
            provider="google",
            config={"api_key": "test-key"}
        )
        
        # Make imports fail
        def mock_import_error(*args, **kwargs):
            raise ImportError("No module named 'google.adk'")
        
        monkeypatch.setattr("contexa_sdk.adapters.google_adk.adk", mock_import_error)
        
        # Act
        result = adapter.model(model)
        
        # Assert
        assert isinstance(result, dict)
        assert "model_name" in result
        assert result["model_name"] == "gemini-pro"
        assert "provider" in result
        assert "client" not in result or result["client"] is None
        assert "config" in result
    
    @pytest.mark.asyncio
    async def test_agent_with_model_dictionary(self, patch_imports):
        """Test agent conversion with the new model dictionary format."""
        # Arrange
        adapter = GoogleAIAdapter()
        
        # Mock the model method to return the standardized dictionary
        model_dict = {
            "model_name": "gemini-pro",
            "provider": "google",
            "client": mock.MagicMock(),
            "config": {"temperature": 0.7}
        }
        
        with mock.patch.object(adapter, 'model', return_value=model_dict):
            from contexa_sdk.core.agent import ContexaAgent
            from contexa_sdk.core.tool import ContexaTool
            from contexa_sdk.core.model import ContexaModel
            
            # Create a test model
            model = ContexaModel(
                model_name="gemini-pro",
                provider="google",
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
                # Act
                result = adapter.agent(agent)
                
                # Assert
                assert result is not None 