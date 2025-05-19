"""Tests for the Google adapters in Contexa SDK."""

import pytest
from contexa_sdk.core.model import ContexaModel
from contexa_sdk.core.tool import ContexaTool
from contexa_sdk.core.agent import ContexaAgent
from pydantic import BaseModel


def test_google_module_structure():
    """Test that the Google adapter module structure is correct."""
    # Import the main google module
    from contexa_sdk.adapters import google
    
    # Check for GenAI functions
    assert hasattr(google, 'genai_tool')
    assert hasattr(google, 'genai_model')
    assert hasattr(google, 'genai_agent')
    assert hasattr(google, 'genai_prompt')
    assert hasattr(google, 'genai_handoff')
    
    # Check for ADK functions
    assert hasattr(google, 'adk_tool')
    assert hasattr(google, 'adk_model')
    assert hasattr(google, 'adk_agent')
    assert hasattr(google, 'adk_prompt')
    assert hasattr(google, 'adk_handoff')
    
    # Check for backward compatibility default exports
    assert hasattr(google, 'tool')
    assert hasattr(google, 'model')
    assert hasattr(google, 'agent')
    assert hasattr(google, 'prompt')
    assert hasattr(google, 'handoff')


def test_google_genai_direct_imports():
    """Test importing directly from the GenAI module."""
    # Import directly from the genai module
    from contexa_sdk.adapters.google.genai import (
        tool, model, agent, prompt, handoff,
        GoogleGenAIAdapter, GOOGLE_SDK_AVAILABLE
    )
    
    # Verify functions exist and are callable
    assert callable(tool)
    assert callable(model)
    assert callable(agent)
    assert callable(prompt)
    assert callable(handoff)
    
    # Verify the adapter class
    assert hasattr(GoogleGenAIAdapter, 'tool')
    assert hasattr(GoogleGenAIAdapter, 'model')
    assert hasattr(GoogleGenAIAdapter, 'agent')


def test_google_adk_direct_imports():
    """Test importing directly from the ADK module."""
    # Import directly from the adk module
    from contexa_sdk.adapters.google.adk import (
        sync_adapt_agent, sync_adapt_adk_agent, sync_handoff,
        adk_manager
    )
    
    # Verify functions exist and are callable
    assert callable(sync_adapt_agent)
    assert callable(sync_adapt_adk_agent)
    assert callable(sync_handoff)
    
    # Verify the manager exists
    assert hasattr(adk_manager, 'contexa_to_adk')
    assert hasattr(adk_manager, 'adk_to_contexa')


@pytest.mark.asyncio
async def test_genai_test_model():
    """Test using test models with the GenAI adapter."""
    from contexa_sdk.adapters.google import genai_model
    
    # Create a test model
    test_model = ContexaModel(
        provider="test",
        model_name="test-model"
    )
    
    # This should work with our mock implementation
    model_data = genai_model(test_model)
    assert isinstance(model_data, dict)
    assert "model" in model_data
    
    # Create an error test model
    error_model = ContexaModel(
        provider="test",
        model_name="error_model"
    )
    
    # This should work but raise an error when used
    model_data = genai_model(error_model)
    assert isinstance(model_data, dict)
    assert "model" in model_data
    
    # Test that the error model raises a ValueError when used
    with pytest.raises(ValueError, match="This is a test error from the error_model"):
        await model_data["model"].generate_content_async("test")


@pytest.mark.asyncio
async def test_genai_tool_conversion():
    """Test converting a Contexa tool to a Google GenAI tool."""
    from contexa_sdk.adapters.google import genai_tool
    
    # Define a test tool with Pydantic input
    class SearchInput(BaseModel):
        query: str
        max_results: int = 5
    
    # Define the tool using the decorator
    @ContexaTool.register(
        name="web_search",
        description="Search the web for information"
    )
    async def web_search(inp: SearchInput) -> str:
        return f"Results for '{inp.query}' (max: {inp.max_results})"
    
    # Extract the actual tool instance from the decorated function
    tool_instance = getattr(web_search, "__contexa_tool__", None)
    assert tool_instance is not None, "The decorator did not attach the __contexa_tool__ attribute"
    
    # Convert the tool - using the tool instance, not the function
    google_tool = genai_tool(tool_instance)
    
    # Check basic properties
    assert hasattr(google_tool, "name")
    assert google_tool.name == "web_search"
    assert hasattr(google_tool, "description")
    assert google_tool.description == "Search the web for information"
    
    # Check the tool has parameters
    assert hasattr(google_tool, "parameters")


@pytest.mark.asyncio
async def test_genai_agent_conversion():
    """Test converting a Contexa agent to a Google GenAI agent."""
    from contexa_sdk.adapters.google import genai_agent
    
    # Create a simple test agent
    agent = ContexaAgent(
        name="Test Agent",
        description="A test agent",
        model=ContexaModel(provider="test", model_name="test-model"),
        tools=[]
    )
    
    # Convert the agent
    google_agent = genai_agent(agent)
    
    # Check basic properties
    assert hasattr(google_agent, "name")
    assert google_agent.name == "Test Agent"
    assert hasattr(google_agent, "run")
    assert callable(google_agent.run)
    assert hasattr(google_agent, "reset")
    assert callable(google_agent.reset)


def test_adk_sync_wrappers():
    """Test the synchronous wrappers for ADK functions."""
    from contexa_sdk.adapters.google import adk_agent, adk_model
    from contexa_sdk.adapters.google.adk import sync_adapt_agent
    import inspect
    
    # Both should be callable
    assert callable(adk_agent)
    assert callable(adk_model)
    
    # The exported adk_agent should be the same as sync_adapt_agent
    assert adk_agent is sync_adapt_agent
    
    # Check that these are synchronous functions (not coroutines)
    assert not inspect.iscoroutinefunction(adk_agent)
    assert not inspect.iscoroutinefunction(adk_model)


def test_converter_sync_functions():
    """Test the synchronous converter functions."""
    from contexa_sdk.adapters.google.converter import convert_tool, convert_model
    import inspect
    
    # These should be synchronous functions
    assert not inspect.iscoroutinefunction(convert_tool)
    assert not inspect.iscoroutinefunction(convert_model)
    
    # Create a test model
    model = ContexaModel(
        provider="google",
        model_name="gemini-pro"
    )
    
    # Try importing ADK to check if we should expect errors
    try:
        from google.adk import settings
        google_adk_available = True
    except ImportError:
        google_adk_available = False
        
    if not google_adk_available:
        # Should raise ImportError if ADK is not installed
        with pytest.raises(ImportError):
            convert_model(model)
    else:
        # Should return a dict with model configuration
        model_config = convert_model(model)
        assert isinstance(model_config, dict)
        assert "model" in model_config


def test_import_functions_type():
    """Test that all imported functions are callable."""
    from contexa_sdk.adapters.google import (
        genai_tool, genai_model, genai_agent, genai_prompt, genai_handoff,
        adk_tool, adk_model, adk_agent, adk_prompt, adk_handoff,
        tool, model, agent, prompt, handoff
    )
    
    # All functions should be callable
    assert callable(genai_tool)
    assert callable(genai_model)
    assert callable(genai_agent)
    assert callable(genai_prompt)
    assert callable(genai_handoff)
    
    assert callable(adk_tool)
    assert callable(adk_model)
    assert callable(adk_agent)
    assert callable(adk_prompt)
    assert callable(adk_handoff)
    
    assert callable(tool)
    assert callable(model)
    assert callable(agent)
    assert callable(prompt)
    assert callable(handoff)


@pytest.mark.asyncio
async def test_genai_function_or_tool():
    """Test that the GenAI adapter can handle both decorated functions and ContexaTool instances."""
    from contexa_sdk.adapters.google import genai_tool
    
    # Define a test tool with Pydantic input
    class SearchInput(BaseModel):
        query: str
    
    # 1. Test with a decorated function
    @ContexaTool.register(
        name="decorated_tool",
        description="Test decorated tool"
    )
    async def decorated_tool(inp: SearchInput) -> str:
        return f"Decorated tool result for '{inp.query}'"
    
    # 2. Test with a ContexaTool instance
    direct_tool = ContexaTool(
        func=lambda inp: f"Direct tool result for '{inp.query}'",
        name="direct_tool",
        description="Test direct tool",
        schema=SearchInput
    )
    
    # Both should work with genai_tool
    google_decorated = genai_tool(decorated_tool)
    google_direct = genai_tool(direct_tool)
    
    # Check both converted tools
    assert google_decorated.name == "decorated_tool"
    assert google_direct.name == "direct_tool" 