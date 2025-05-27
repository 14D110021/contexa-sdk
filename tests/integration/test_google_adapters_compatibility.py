"""Integration tests for Google adapters cross-framework compatibility.

This module tests both Google GenAI and Google ADK adapters for compatibility
with other frameworks (LangChain, CrewAI, OpenAI) and with each other.
"""

import pytest
import unittest.mock as mock
import asyncio
from typing import Dict, Any

from contexa_sdk.core.model import ContexaModel
from contexa_sdk.core.agent import ContexaAgent
from contexa_sdk.core.tool import ContexaTool
from contexa_sdk.adapters import langchain, crewai, openai
from contexa_sdk.adapters.google import (
    # GenAI functions
    genai_tool, genai_model, genai_agent, genai_handoff,
    # ADK functions
    adk_tool, adk_model, adk_agent, adk_handoff,
    # Default exports (using GenAI implementations)
    tool, model, agent, handoff
)


class MockTool(ContexaTool):
    """Mock tool for testing."""
    
    def __init__(self, name="test_tool", description="Test tool description"):
        """Initialize the mock tool."""
        self.name = name
        self.description = description
        
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute the mock tool."""
        return {"result": f"Executed {self.name} with {kwargs}"}


@pytest.fixture
def test_tools():
    """Create test tools for conversion testing."""
    return {
        "basic": MockTool(name="basic_tool", description="A basic test tool"),
        "search": MockTool(name="search_tool", description="A search test tool"),
        "analyze": MockTool(name="analyze_tool", description="An analysis test tool")
    }


@pytest.fixture
def test_models():
    """Create test models for conversion testing."""
    return {
        "basic": ContexaModel(
            model_name="test-model",
            provider="test",
            config={"temperature": 0.7}
        ),
        "google": ContexaModel(
            model_name="gemini-pro",
            provider="google",
            config={"temperature": 0.8}
        )
    }


@pytest.fixture
def test_agents():
    """Create test agents for handoff testing."""
    # Create base Contexa agent
    base_agent = ContexaAgent(
        name="Base Agent",
        description="A test agent",
        model=ContexaModel(
            model_name="gemini-pro", 
            provider="google",
            config={"temperature": 0.7}
        ),
        tools=[MockTool()],
        system_prompt="You are a test assistant"
    )
    
    # Create framework-specific mock agents
    openai_agent = mock.MagicMock(name="openai_agent")
    langchain_agent = mock.MagicMock(name="langchain_agent")
    crewai_agent = mock.MagicMock(name="crewai_agent")
    genai_agent_mock = mock.MagicMock(name="genai_agent")
    adk_agent_mock = mock.MagicMock(name="adk_agent")
    
    # Mock required methods
    for agent_mock in [openai_agent, langchain_agent, crewai_agent, genai_agent_mock, adk_agent_mock]:
        agent_mock.run = mock.AsyncMock(return_value="Mock response")
    
    return {
        "base": base_agent,
        "openai": openai_agent,
        "langchain": langchain_agent,
        "crewai": crewai_agent,
        "genai": genai_agent_mock,
        "adk": adk_agent_mock
    }


@pytest.fixture
def mock_adapters(monkeypatch):
    """Mock all adapter handoff methods for testing."""
    def create_mock_handoff(adapter_name):
        async def mock_handoff(*args, **kwargs):
            query = kwargs.get("query", "")
            return f"{adapter_name} response to: {query}"
        return mock_handoff
    
    # Mock each adapter's handoff method
    monkeypatch.setattr("contexa_sdk.adapters.openai.handoff", create_mock_handoff("OpenAI"))
    monkeypatch.setattr("contexa_sdk.adapters.langchain.handoff", create_mock_handoff("LangChain"))
    monkeypatch.setattr("contexa_sdk.adapters.crewai.handoff", create_mock_handoff("CrewAI"))
    monkeypatch.setattr("contexa_sdk.adapters.google.genai_handoff", create_mock_handoff("Google GenAI"))
    monkeypatch.setattr("contexa_sdk.adapters.google.adk_handoff", create_mock_handoff("Google ADK"))


# ----- TOOL CONVERSION TESTS -----

def test_genai_tool_conversion(test_tools):
    """Test converting Contexa tools to Google GenAI tools."""
    for tool_name, tool in test_tools.items():
        # Mock the actual conversion to focus on interface
        with mock.patch("google.genai.types.FunctionDeclaration") as mock_func_decl:
            mock_func_decl.return_value = mock.MagicMock(name=f"genai_{tool_name}")
            
            # Convert tool using GenAI adapter
            result = genai_tool(tool)
            
            # Verify conversion was called correctly
            mock_func_decl.assert_called_once()
            assert result is not None


def test_adk_tool_conversion(test_tools):
    """Test converting Contexa tools to Google ADK tools."""
    for tool_name, tool in test_tools.items():
        # Mock the actual conversion to focus on interface
        with mock.patch("contexa_sdk.adapters.google.converter.convert_tool") as mock_convert:
            mock_convert.return_value = mock.MagicMock(name=f"adk_{tool_name}")
            
            # Convert tool using ADK adapter
            result = adk_tool(tool)
            
            # Verify conversion was called correctly
            mock_convert.assert_called_once_with(tool)
            assert result is not None


def test_default_tool_conversion(test_tools):
    """Test that default tool conversion uses GenAI implementation."""
    basic_tool = test_tools["basic"]
    
    # Mock both implementations to check which one is used
    with mock.patch("contexa_sdk.adapters.google.genai.tool") as mock_genai_tool:
        mock_genai_tool.return_value = mock.MagicMock(name="genai_result")
        
        with mock.patch("contexa_sdk.adapters.google.converter.convert_tool") as mock_adk_tool:
            mock_adk_tool.return_value = mock.MagicMock(name="adk_result")
            
            # Use default tool function
            result = tool(basic_tool)
            
            # Verify GenAI implementation was used
            mock_genai_tool.assert_called_once_with(basic_tool)
            mock_adk_tool.assert_not_called()


# ----- MODEL CONVERSION TESTS -----

def test_genai_model_conversion(test_models):
    """Test converting Contexa models to Google GenAI models."""
    for model_name, model_obj in test_models.items():
        # Mock the actual conversion to focus on interface
        with mock.patch("google.genai.GenerativeModel") as mock_genai_model:
            mock_genai_model.return_value = mock.MagicMock(name=f"genai_model_{model_name}")
            
            # Convert model using GenAI adapter
            result = genai_model(model_obj)
            
            # Verify conversion produced a result
            assert result is not None
            
            # If it's a Google model, verify specific settings
            if model_obj.provider == "google":
                assert "model" in result
                assert "config" in result


def test_adk_model_conversion(test_models):
    """Test converting Contexa models to Google ADK models."""
    for model_name, model_obj in test_models.items():
        # Mock the actual conversion to focus on interface
        with mock.patch("contexa_sdk.adapters.google.converter.convert_model") as mock_convert:
            mock_convert.return_value = mock.MagicMock(name=f"adk_model_{model_name}")
            
            # Convert model using ADK adapter
            result = adk_model(model_obj)
            
            # Verify conversion was called correctly
            mock_convert.assert_called_once_with(model_obj)
            assert result is not None


def test_default_model_conversion(test_models):
    """Test that default model conversion uses GenAI implementation."""
    google_model = test_models["google"]
    
    # Mock both implementations to check which one is used
    with mock.patch("contexa_sdk.adapters.google.genai.model") as mock_genai_model:
        mock_genai_model.return_value = mock.MagicMock(name="genai_model_result")
        
        with mock.patch("contexa_sdk.adapters.google.converter.convert_model") as mock_adk_model:
            mock_adk_model.return_value = mock.MagicMock(name="adk_model_result")
            
            # Use default model function
            result = model(google_model)
            
            # Verify GenAI implementation was used
            mock_genai_model.assert_called_once_with(google_model)
            mock_adk_model.assert_not_called()


# ----- AGENT CONVERSION TESTS -----

def test_genai_agent_conversion(test_agents):
    """Test converting Contexa agents to Google GenAI agents."""
    base_agent = test_agents["base"]
    
    # Mock GenAI model creation
    with mock.patch("contexa_sdk.adapters.google.genai.model") as mock_model_fn, \
         mock.patch("contexa_sdk.adapters.google.genai.tool") as mock_tool_fn:
        
        mock_model_fn.return_value = {"model": mock.MagicMock()}
        mock_tool_fn.return_value = mock.MagicMock()
        
        # Convert agent
        result = genai_agent(base_agent)
        
        # Verify agent has required attributes and methods
        assert hasattr(result, "run")
        assert callable(result.run)


def test_adk_agent_conversion(test_agents):
    """Test converting Contexa agents to Google ADK agents."""
    base_agent = test_agents["base"]
    
    # Mock ADK agent creation
    with mock.patch("contexa_sdk.adapters.google.adk.sync_adapt_agent") as mock_adapt_agent:
        mock_adapt_agent.return_value = mock.MagicMock()
        
        # Convert agent
        result = adk_agent(base_agent)
        
        # Verify ADK agent was created
        mock_adapt_agent.assert_called_once_with(base_agent)
        assert result is not None


def test_default_agent_conversion(test_agents):
    """Test that default agent conversion uses GenAI implementation."""
    base_agent = test_agents["base"]
    
    # Mock both implementations to check which one is used
    with mock.patch("contexa_sdk.adapters.google.genai.agent") as mock_genai_agent:
        mock_genai_agent.return_value = mock.MagicMock(name="genai_agent_result")
        
        with mock.patch("contexa_sdk.adapters.google.adk.sync_adapt_agent") as mock_adk_agent:
            mock_adk_agent.return_value = mock.MagicMock(name="adk_agent_result")
            
            # Use default agent function
            result = agent(base_agent)
            
            # Verify GenAI implementation was used
            mock_genai_agent.assert_called_once_with(base_agent)
            mock_adk_agent.assert_not_called()


# ----- HANDOFF TESTS -----

@pytest.mark.asyncio
async def test_genai_to_langchain_handoff(mock_adapters, test_agents):
    """Test handoff from Google GenAI to LangChain."""
    # Arrange
    with mock.patch("contexa_sdk.adapters.google.genai.agent") as mock_genai_agent_fn, \
         mock.patch("contexa_sdk.adapters.langchain.agent") as mock_lc_agent_fn:
        
        mock_genai_agent_fn.return_value = test_agents["genai"]
        mock_lc_agent_fn.return_value = test_agents["langchain"]
        
        source_agent = test_agents["base"]
        target_agent = test_agents["base"]  # Will be converted to LangChain
        query = "Test query from GenAI to LangChain"
        
        # Act
        result = await genai_handoff(
            source_agent=source_agent,
            target_agent=target_agent,
            query=query
        )
        
        # Assert
        assert "GenAI" in result
        assert query in result


@pytest.mark.asyncio
async def test_adk_to_crewai_handoff(mock_adapters, test_agents):
    """Test handoff from Google ADK to CrewAI."""
    # Arrange
    with mock.patch("contexa_sdk.adapters.google.adk.sync_adapt_agent") as mock_adk_agent_fn, \
         mock.patch("contexa_sdk.adapters.crewai.agent") as mock_crew_agent_fn:
        
        mock_adk_agent_fn.return_value = test_agents["adk"]
        mock_crew_agent_fn.return_value = test_agents["crewai"]
        
        source_agent = test_agents["base"]
        target_agent = test_agents["base"]  # Will be converted to CrewAI
        query = "Test query from ADK to CrewAI"
        
        # Act
        result = await adk_handoff(
            source_agent=source_agent,
            target_adk_agent=target_agent,
            query=query
        )
        
        # Assert
        assert "ADK" in result
        assert query in result


@pytest.mark.asyncio
async def test_openai_to_genai_handoff(mock_adapters, test_agents):
    """Test handoff from OpenAI to Google GenAI."""
    # Arrange
    with mock.patch("contexa_sdk.adapters.openai.agent") as mock_oa_agent_fn, \
         mock.patch("contexa_sdk.adapters.google.genai.agent") as mock_genai_agent_fn:
        
        mock_oa_agent_fn.return_value = test_agents["openai"]
        mock_genai_agent_fn.return_value = test_agents["genai"]
        
        source_agent = test_agents["base"]
        target_agent = test_agents["base"]  # Will be converted to GenAI
        query = "Test query from OpenAI to GenAI"
        
        # Act - using openai handoff that targets a GenAI agent
        with mock.patch("contexa_sdk.adapters.google.genai_handoff") as mock_genai_handoff_fn:
            mock_genai_handoff_fn.side_effect = lambda **kwargs: f"GenAI response to: {kwargs['query']}"
            
            result = await openai.handoff(
                source_agent=source_agent,
                target_agent=target_agent,
                query=query
            )
        
        # Assert
        assert "OpenAI" in result
        assert query in result


@pytest.mark.asyncio
async def test_langchain_to_adk_handoff(mock_adapters, test_agents):
    """Test handoff from LangChain to Google ADK."""
    # Arrange
    with mock.patch("contexa_sdk.adapters.langchain.agent") as mock_lc_agent_fn, \
         mock.patch("contexa_sdk.adapters.google.adk.sync_adapt_agent") as mock_adk_agent_fn:
        
        mock_lc_agent_fn.return_value = test_agents["langchain"]
        mock_adk_agent_fn.return_value = test_agents["adk"]
        
        source_agent = test_agents["base"]
        target_agent = test_agents["base"]  # Will be converted to ADK
        query = "Test query from LangChain to ADK"
        
        # Act - using langchain handoff that targets an ADK agent
        with mock.patch("contexa_sdk.adapters.google.adk_handoff") as mock_adk_handoff_fn:
            mock_adk_handoff_fn.side_effect = lambda **kwargs: f"ADK response to: {kwargs['query']}"
            
            result = await langchain.handoff(
                source_agent=source_agent,
                target_agent_executor=target_agent,
                query=query
            )
        
        # Assert
        assert "LangChain" in result
        assert query in result


@pytest.mark.asyncio
async def test_genai_to_adk_handoff(mock_adapters, test_agents):
    """Test handoff from Google GenAI to Google ADK."""
    # Arrange
    source_agent = test_agents["base"]
    target_agent = test_agents["base"] 
    query = "Test query from GenAI to ADK"
    
    # Mock the GenAI agent
    with mock.patch("contexa_sdk.adapters.google.genai.agent") as mock_genai_agent_fn:
        mock_genai_agent_fn.return_value = test_agents["genai"]
        
        # Mock the ADK agent and ADK handoff
        with mock.patch("contexa_sdk.adapters.google.adk.sync_adapt_agent") as mock_adk_agent_fn, \
             mock.patch("contexa_sdk.adapters.google.adk_handoff") as mock_adk_handoff_fn:
            
            mock_adk_agent_fn.return_value = test_agents["adk"]
            mock_adk_handoff_fn.side_effect = lambda **kwargs: f"ADK response to: {kwargs['query']}"
            
            # Act - Handoff from GenAI to ADK
            result = await genai_handoff(
                source_agent=source_agent,
                target_agent=target_agent,
                query=query
            )
            
            # Assert
            assert "GenAI" in result
            assert query in result


@pytest.mark.asyncio
async def test_adk_to_genai_handoff(mock_adapters, test_agents):
    """Test handoff from Google ADK to Google GenAI."""
    # Arrange
    source_agent = test_agents["base"]
    target_agent = test_agents["base"]
    query = "Test query from ADK to GenAI"
    
    # Mock the ADK agent
    with mock.patch("contexa_sdk.adapters.google.adk.sync_adapt_agent") as mock_adk_agent_fn:
        mock_adk_agent_fn.return_value = test_agents["adk"]
        
        # Mock the GenAI agent and GenAI handoff
        with mock.patch("contexa_sdk.adapters.google.genai.agent") as mock_genai_agent_fn, \
             mock.patch("contexa_sdk.adapters.google.genai_handoff") as mock_genai_handoff_fn:
            
            mock_genai_agent_fn.return_value = test_agents["genai"]
            mock_genai_handoff_fn.side_effect = lambda **kwargs: f"GenAI response to: {kwargs['query']}"
            
            # Act - Handoff from ADK to GenAI
            result = await adk_handoff(
                source_agent=source_agent,
                target_adk_agent=target_agent,
                query=query
            )
            
            # Assert
            assert "ADK" in result
            assert query in result


@pytest.mark.asyncio
async def test_default_handoff_uses_genai(mock_adapters, test_agents):
    """Test that default handoff uses the GenAI implementation."""
    source_agent = test_agents["base"]
    target_agent = test_agents["base"]
    query = "Default handoff test"
    
    # Mock both implementations to check which one is used
    with mock.patch("contexa_sdk.adapters.google.genai_handoff") as mock_genai_handoff:
        mock_genai_handoff.return_value = f"GenAI response to: {query}"
        
        with mock.patch("contexa_sdk.adapters.google.adk_handoff") as mock_adk_handoff:
            mock_adk_handoff.return_value = f"ADK response to: {query}"
            
            # Use default handoff function
            result = await handoff(
                source_agent=source_agent,
                target_agent=target_agent,
                query=query
            )
            
            # Verify GenAI implementation was used
            mock_genai_handoff.assert_called_once()
            mock_adk_handoff.assert_not_called()
            assert "GenAI" in result 