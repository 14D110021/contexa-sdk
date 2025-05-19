"""Tests for consistent error handling across framework adapters."""

import pytest
import asyncio
from unittest.mock import patch, MagicMock

from contexa_sdk.core.tool import ContexaTool
from contexa_sdk.core.agent import ContexaAgent
from contexa_sdk.core.model import ContexaModel


class TestAdapterErrorHandling:
    """Test error handling across different framework adapters."""
    
    @pytest.mark.parametrize("adapter_name", [
        "langchain",
        "crewai",
        "openai",
        "google_adk"
    ])
    def test_model_error_handling(self, adapter_name):
        """Test that model errors are handled consistently across adapters."""
        # Skip if adapter is not installed
        try:
            adapter_module = __import__(f"contexa_sdk.adapters.{adapter_name}", fromlist=["*"])
        except ImportError:
            pytest.skip(f"{adapter_name} adapter not installed")
        
        # Create a model with invalid configuration
        model = ContexaModel(
            provider="invalid_provider",
            model_name="invalid_model"
        )
        
        # Attempt to convert model and expect consistent error
        with pytest.raises(Exception) as excinfo:
            # Check if the adapter module has a model conversion function
            if not hasattr(adapter_module, "model"):
                pytest.skip(f"{adapter_name} adapter does not have 'model' function")
            adapter_module.model(model)
        
        # Verify error contains helpful information
        error_msg = str(excinfo.value).lower()
        assert "provider" in error_msg or "invalid" in error_msg
    
    @pytest.mark.parametrize("adapter_name", [
        "langchain",
        "crewai",
        "openai",
        "google_adk"
    ])
    def test_tool_validation(self, adapter_name):
        """Test that tool validation is consistent across adapters."""
        # Skip if adapter is not installed
        try:
            adapter_module = __import__(f"contexa_sdk.adapters.{adapter_name}", fromlist=["*"])
        except ImportError:
            pytest.skip(f"{adapter_name} adapter not installed")
        
        # Check if the adapter module has a tool conversion function
        if not hasattr(adapter_module, "tool"):
            pytest.skip(f"{adapter_name} adapter does not have 'tool' function")
            
        # Create an invalid tool (missing required attributes)
        invalid_tool = MagicMock(spec=ContexaTool)
        invalid_tool.name = None  # Missing name
        
        # Attempt to convert tool and expect consistent error
        with pytest.raises(Exception) as excinfo:
            adapter_module.tool(invalid_tool)
        
        # Verify error contains helpful information
        error_msg = str(excinfo.value).lower()
        assert "tool" in error_msg and ("name" in error_msg or "required" in error_msg)
    
    @pytest.mark.parametrize("adapter_name", [
        "langchain",
        "crewai",
        "openai",
        "google_adk"
    ])
    def test_agent_validation(self, adapter_name):
        """Test that agent validation is consistent across adapters."""
        # Skip if adapter is not installed
        try:
            adapter_module = __import__(f"contexa_sdk.adapters.{adapter_name}", fromlist=["*"])
        except ImportError:
            pytest.skip(f"{adapter_name} adapter not installed")
            
        # Check if the adapter module has an agent conversion function
        if not hasattr(adapter_module, "agent"):
            pytest.skip(f"{adapter_name} adapter does not have 'agent' function")
        
        # Create an agent with missing model
        invalid_agent = ContexaAgent(
            name="Test Agent",
            description="An agent for testing",
            model=None,  # Missing model
            tools=[]
        )
        
        # Attempt to convert agent and expect consistent error
        with pytest.raises(Exception) as excinfo:
            adapter_module.agent(invalid_agent)
        
        # Verify error contains helpful information
        error_msg = str(excinfo.value).lower()
        assert "agent" in error_msg and "model" in error_msg
    
    @pytest.mark.asyncio
    @pytest.mark.parametrize("adapter_name", [
        "langchain",
        "crewai",
        "openai",
        "google_adk"
    ])
    async def test_runtime_error_propagation(self, adapter_name):
        """Test that runtime errors are properly propagated from adapters."""
        # Skip if adapter is not installed
        try:
            adapter_module = __import__(f"contexa_sdk.adapters.{adapter_name}", fromlist=["*"])
        except ImportError:
            pytest.skip(f"{adapter_name} adapter not installed")
            
        # Check if the adapter module has a model conversion function
        if not hasattr(adapter_module, "model"):
            pytest.skip(f"{adapter_name} adapter does not have 'model' function")
        
        # Create a model that will raise an error during execution
        model = ContexaModel(provider="test", model_name="error_model")
        
        # Special case for Google ADK
        if adapter_name == "google_adk":
            # For Google ADK we need a custom test
            with pytest.raises(ValueError) as excinfo:
                adapted_model = adapter_module.model(model)
                # Try to generate with the model
                await adapted_model.generate([])
                
            # Verify error contains "test model error" 
            error_msg = str(excinfo.value).lower()
            assert "model" in error_msg and "error" in error_msg
            return
        
        with pytest.raises(Exception) as excinfo:
            adapted_model = adapter_module.model(model)
            # Try to generate with the model
            await adapted_model.generate([])
        
        # Verify error indicates it's a model issue
        error_msg = str(excinfo.value).lower()
        assert any(term in error_msg for term in ["provider", "model", "error"]) 