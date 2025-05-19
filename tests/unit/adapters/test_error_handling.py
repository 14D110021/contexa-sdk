"""Unit tests for adapter error handling."""

import pytest
import sys
import unittest.mock as mock
from typing import Dict, Any

from contexa_sdk.core.model import ContexaModel
from contexa_sdk.core.agent import ContexaAgent
from contexa_sdk.core.tool import ContexaTool
from contexa_sdk.adapters import openai, langchain, crewai, google


class TestAdapterErrorHandling:
    """Test error handling across all adapters."""
    
    def test_openai_missing_dependency(self, monkeypatch):
        """Test OpenAI adapter handling missing dependency."""
        # Mock the import to raise ImportError
        def mock_import(*args, **kwargs):
            if args[0] == "openai" or args[0] == "openai_agents":
                raise ImportError(f"No module named '{args[0]}'")
            return __import__(*args, **kwargs)
        
        monkeypatch.setattr("builtins.__import__", mock_import)
        
        # Create a model object
        model = ContexaModel(
            model_name="gpt-4o",
            provider="openai",
            config={"api_key": "test-key"}
        )
        
        # This should not raise an exception
        result = openai.model(model)
        
        # Verify result structure
        assert isinstance(result, dict)
        assert "model_name" in result
        assert result["model_name"] == "gpt-4o"
        
        # Create a tool
        tool = mock.MagicMock(spec=ContexaTool)
        tool.name = "test_tool"
        tool.description = "Test tool"
        
        # This should not raise an exception
        result = openai.tool(tool)
        assert result is not None
    
    def test_langchain_missing_dependency(self, monkeypatch):
        """Test LangChain adapter handling missing dependency."""
        # Mock the import to raise ImportError
        def mock_import(*args, **kwargs):
            if args[0].startswith("langchain"):
                raise ImportError(f"No module named '{args[0]}'")
            return __import__(*args, **kwargs)
        
        monkeypatch.setattr("builtins.__import__", mock_import)
        
        # Create a model object
        model = ContexaModel(
            model_name="gpt-4o",
            provider="openai",
            config={"api_key": "test-key"}
        )
        
        # This should not raise an exception
        result = langchain.model(model)
        
        # Verify result structure
        assert isinstance(result, dict)
        assert "model_name" in result
        assert result["model_name"] == "gpt-4o"
        
        # Create a tool
        tool = mock.MagicMock(spec=ContexaTool)
        tool.name = "test_tool"
        tool.description = "Test tool"
        
        # This should not raise an exception
        result = langchain.tool(tool)
        assert result is not None
    
    def test_crewai_missing_dependency(self, monkeypatch):
        """Test CrewAI adapter handling missing dependency."""
        # Mock the import to raise ImportError
        def mock_import(*args, **kwargs):
            if args[0] == "crewai":
                raise ImportError(f"No module named '{args[0]}'")
            return __import__(*args, **kwargs)
        
        monkeypatch.setattr("builtins.__import__", mock_import)
        
        # Create a model object
        model = ContexaModel(
            model_name="gpt-4o",
            provider="openai",
            config={"api_key": "test-key"}
        )
        
        # This should not raise an exception
        result = crewai.model(model)
        
        # Verify result structure
        assert isinstance(result, dict)
        assert "model_name" in result
        assert result["model_name"] == "gpt-4o"
        
        # Create a tool
        tool = mock.MagicMock(spec=ContexaTool)
        tool.name = "test_tool"
        tool.description = "Test tool"
        
        # This should not raise an exception
        result = crewai.tool(tool)
        assert result is not None
    
    def test_google_missing_dependency(self, monkeypatch):
        """Test Google ADK adapter handling missing dependency."""
        # Mock the import to raise ImportError
        def mock_import(*args, **kwargs):
            if args[0].startswith("google"):
                raise ImportError(f"No module named '{args[0]}'")
            return __import__(*args, **kwargs)
        
        monkeypatch.setattr("builtins.__import__", mock_import)
        
        # Create a model object
        model = ContexaModel(
            model_name="gemini-pro",
            provider="google",
            config={"api_key": "test-key"}
        )
        
        # This should not raise an exception
        result = google.model(model)
        
        # Verify result structure
        assert isinstance(result, dict)
        assert "model_name" in result
        assert result["model_name"] == "gemini-pro"
        
        # Create a tool
        tool = mock.MagicMock(spec=ContexaTool)
        tool.name = "test_tool"
        tool.description = "Test tool"
        
        # This should not raise an exception
        result = google.tool(tool)
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_openai_handoff_with_missing_dependency(self, monkeypatch):
        """Test OpenAI adapter handoff with missing dependency."""
        # Mock the import to raise ImportError
        def mock_import(*args, **kwargs):
            if args[0] == "openai" or args[0] == "openai_agents":
                raise ImportError(f"No module named '{args[0]}'")
            return __import__(*args, **kwargs)
        
        monkeypatch.setattr("builtins.__import__", mock_import)
        
        # Create mock agents
        source_agent = mock.MagicMock(spec=ContexaAgent)
        target_agent = mock.MagicMock()
        
        # This should raise a helpful exception rather than a cryptic one
        with pytest.raises(ImportError) as exc_info:
            await openai.handoff(
                source_agent=source_agent,
                target_agent=target_agent,
                query="Test query"
            )
        
        # Verify the error message is helpful
        assert "openai" in str(exc_info.value).lower()
        assert "install" in str(exc_info.value).lower() or "dependency" in str(exc_info.value).lower()
    
    def test_adapter_error_messages(self, monkeypatch):
        """Test that adapter errors include helpful installation instructions."""
        # Mock the import to raise ImportError
        def mock_import(*args, **kwargs):
            if args[0] == "crewai":
                raise ImportError(f"No module named '{args[0]}'")
            return __import__(*args, **kwargs)
        
        monkeypatch.setattr("builtins.__import__", mock_import)
        
        # Create a model object
        model = ContexaModel(
            model_name="gpt-4o",
            provider="openai",
            config={"api_key": "test-key"}
        )
        
        # Create a mock agent
        agent = mock.MagicMock(spec=ContexaAgent)
        agent.model = model
        
        # Agent should return a helpful error with installation instructions
        with pytest.raises(ImportError) as exc_info:
            crewai.agent(agent)
        
        # Verify the error message contains installation instructions
        error_message = str(exc_info.value).lower()
        assert "crewai" in error_message
        assert "install" in error_message
        assert "pip" in error_message 