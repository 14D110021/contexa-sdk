"""Unit tests for LangChain adapter."""

import pytest
import sys
import unittest.mock as mock
from typing import Dict, Any

from contexa_sdk.core.model import ContexaModel
from contexa_sdk.adapters.langchain import LangChainAdapter


@pytest.fixture
def patch_imports(monkeypatch, mock_langchain):
    """Patch imports for LangChain modules."""
    original_import = __import__
    
    def mock_import(name, *args, **kwargs):
        if name.startswith("langchain"):
            module_name = name
            if "." in name:
                module_name = name.split(".")[0]
            return mock_langchain.get(name, original_import(name, *args, **kwargs))
        return original_import(name, *args, **kwargs)
    
    monkeypatch.setattr("builtins.__import__", mock_import)
    
    # Patch the specific imports used in the LangChain adapter
    monkeypatch.setattr(
        "contexa_sdk.adapters.langchain.BaseChatModel", 
        mock_langchain["langchain_core.language_models.chat_models"].BaseChatModel
    )
    monkeypatch.setattr(
        "contexa_sdk.adapters.langchain.AgentExecutor", 
        mock_langchain["langchain.agents"].AgentExecutor
    )
    monkeypatch.setattr(
        "contexa_sdk.adapters.langchain.Tool", 
        mock_langchain["langchain_core.tools"].Tool
    )


class TestLangChainAdapter:
    """Test cases for LangChainAdapter."""
    
    def test_init(self):
        """Test adapter initialization."""
        adapter = LangChainAdapter()
        assert isinstance(adapter, LangChainAdapter)
    
    def test_model_with_openai_model(self, patch_imports):
        """Test model conversion for OpenAI model in the LangChain adapter."""
        # Arrange
        adapter = LangChainAdapter()
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
        assert "langchain_model" in result
        assert "config" in result
        assert "temperature" in result["config"]
        assert result["config"]["temperature"] == 0.7
    
    def test_model_with_anthropic_model(self, patch_imports):
        """Test model conversion for Anthropic model in the LangChain adapter."""
        # Arrange
        adapter = LangChainAdapter()
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
        assert "langchain_model" in result
        assert "config" in result
        assert "temperature" in result["config"]
        assert result["config"]["temperature"] == 0.5
    
    def test_model_with_huggingface_model(self, patch_imports):
        """Test model conversion for HuggingFace model in the LangChain adapter."""
        # Arrange
        adapter = LangChainAdapter()
        model = ContexaModel(
            model_name="mistralai/Mistral-7B-v0.1",
            provider="huggingface",
            config={
                "api_key": "test-hf-key",
                "temperature": 0.8,
                "model_kwargs": {"device": "cuda"}
            }
        )
        
        # Act
        result = adapter.model(model)
        
        # Assert
        assert isinstance(result, dict)
        assert "model_name" in result
        assert result["model_name"] == "mistralai/Mistral-7B-v0.1"
        assert "provider" in result
        assert result["provider"] == "huggingface"
        assert "langchain_model" in result
        assert "config" in result
        assert "temperature" in result["config"]
        assert "model_kwargs" in result["config"]
    
    def test_model_with_import_error(self, monkeypatch):
        """Test model conversion with LangChain import error."""
        # Arrange
        adapter = LangChainAdapter()
        model = ContexaModel(
            model_name="gpt-4o",
            provider="openai",
            config={"api_key": "test-key"}
        )
        
        # Make imports fail
        def mock_import_error(*args, **kwargs):
            raise ImportError("No module named 'langchain'")
        
        monkeypatch.setattr("contexa_sdk.adapters.langchain.BaseChatModel", mock_import_error)
        
        # Act
        result = adapter.model(model)
        
        # Assert
        assert isinstance(result, dict)
        assert "model_name" in result
        assert result["model_name"] == "gpt-4o"
        assert "provider" in result
        assert "langchain_model" not in result or result["langchain_model"] is None
        assert "config" in result
    
    @pytest.mark.asyncio
    async def test_agent_with_model_dictionary(self, patch_imports):
        """Test agent conversion with the new model dictionary format."""
        # Arrange
        adapter = LangChainAdapter()
        
        # Mock the model method to return the standardized dictionary
        model_dict = {
            "model_name": "gpt-4o",
            "provider": "openai",
            "langchain_model": mock.MagicMock(),
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
                # Act
                result = adapter.agent(agent)
                
                # Assert
                assert result is not None 