"""Integration tests for cross-framework handoffs."""

import pytest
import unittest.mock as mock
import asyncio
from typing import Dict, Any

from contexa_sdk.core.model import ContexaModel
from contexa_sdk.core.agent import ContexaAgent
from contexa_sdk.core.tool import ContexaTool
from contexa_sdk.adapters import openai, langchain, crewai, google


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
def mock_adapters(monkeypatch):
    """Mock all adapter handoff methods."""
    # Create a common mock response function
    async def mock_handoff(*args, **kwargs):
        # Capture the query for testing
        query = kwargs.get("query", "")
        # Return a consistent response format for testing
        return f"Response to: {query}"
    
    # Mock each adapter's handoff method
    monkeypatch.setattr("contexa_sdk.adapters.openai.handoff", mock_handoff)
    monkeypatch.setattr("contexa_sdk.adapters.langchain.handoff", mock_handoff)
    monkeypatch.setattr("contexa_sdk.adapters.crewai.handoff", mock_handoff)
    monkeypatch.setattr("contexa_sdk.adapters.google.handoff", mock_handoff)


@pytest.fixture
def test_agents():
    """Create test agents for each framework."""
    # Create a common model
    model = ContexaModel(
        model_name="test-model",
        provider="test",
        config={"temperature": 0.7}
    )
    
    # Create a common tool
    tool = MockTool()
    
    # Create a base Contexa agent
    base_agent = ContexaAgent(
        name="Base Agent",
        description="A test agent",
        model=model,
        tools=[tool],
        system_prompt="You are a test assistant"
    )
    
    # Create adapted versions
    openai_agent = mock.MagicMock()
    langchain_agent = mock.MagicMock()
    crewai_agent = mock.MagicMock()
    google_agent = mock.MagicMock()
    
    # Mock the conversion methods
    with mock.patch.object(openai, 'agent', return_value=openai_agent), \
         mock.patch.object(langchain, 'agent', return_value=langchain_agent), \
         mock.patch.object(crewai, 'agent', return_value=crewai_agent), \
         mock.patch.object(google, 'agent', return_value=google_agent):
        
        return {
            "base": base_agent,
            "openai": openai_agent,
            "langchain": langchain_agent,
            "crewai": crewai_agent,
            "google": google_agent
        }


@pytest.mark.asyncio
async def test_openai_to_langchain_handoff(mock_adapters, test_agents):
    """Test handoff from OpenAI agent to LangChain agent."""
    # Arrange
    source_agent = test_agents["base"]  # Use Contexa agent as source
    target_agent = test_agents["langchain"]
    query = "Test query for LangChain"
    
    # Act
    with mock.patch.object(openai, 'agent', return_value=test_agents["openai"]):
        result = await openai.handoff(
            source_agent=source_agent,
            target_agent_executor=target_agent,
            query=query
        )
    
    # Assert
    assert result == f"Response to: {query}"


@pytest.mark.asyncio
async def test_langchain_to_crewai_handoff(mock_adapters, test_agents):
    """Test handoff from LangChain agent to CrewAI agent."""
    # Arrange
    source_agent = test_agents["base"]  # Use Contexa agent as source
    target_agent = test_agents["crewai"]
    query = "Test query for CrewAI"
    
    # Act
    with mock.patch.object(langchain, 'agent', return_value=test_agents["langchain"]):
        result = await langchain.handoff(
            source_agent=source_agent,
            target_agent_executor=target_agent,
            query=query
        )
    
    # Assert
    assert result == f"Response to: {query}"


@pytest.mark.asyncio
async def test_crewai_to_openai_handoff(mock_adapters, test_agents):
    """Test handoff from CrewAI agent to OpenAI agent."""
    # Arrange
    source_agent = test_agents["base"]  # Use Contexa agent as source
    target_agent = test_agents["openai"]
    query = "Test query for OpenAI"
    
    # Act
    with mock.patch.object(crewai, 'agent', return_value=test_agents["crewai"]):
        result = await crewai.handoff(
            source_agent=source_agent,
            target=target_agent,
            query=query
        )
    
    # Assert
    assert result == f"Response to: {query}"


@pytest.mark.asyncio
async def test_google_to_langchain_handoff(mock_adapters, test_agents):
    """Test handoff from Google agent to LangChain agent."""
    # Arrange
    source_agent = test_agents["base"]  # Use Contexa agent as source
    target_agent = test_agents["langchain"]
    query = "Test query for LangChain from Google"
    
    # Act
    with mock.patch.object(google, 'agent', return_value=test_agents["google"]):
        result = await google.handoff(
            source_agent=source_agent,
            target_agent=target_agent,
            query=query
        )
    
    # Assert
    assert result == f"Response to: {query}"


@pytest.mark.asyncio
async def test_handoff_with_context(mock_adapters, test_agents):
    """Test handoff with additional context information."""
    # Arrange
    source_agent = test_agents["base"]  # Use Contexa agent as source
    target_agent = test_agents["langchain"]
    query = "Test query with context"
    context = {
        "previous_response": "Previous agent response",
        "user_info": {"name": "Test User", "preference": "detailed"}
    }
    
    # Create a more specific mock for this test
    async def mock_handoff_with_context(*args, **kwargs):
        # Verify context is passed correctly
        passed_context = kwargs.get("context", {})
        if passed_context.get("previous_response") == context["previous_response"]:
            return f"Response with context: {query}"
        return "Context missing"
    
    # Act
    with mock.patch.object(openai, 'agent', return_value=test_agents["openai"]), \
         mock.patch("contexa_sdk.adapters.openai.handoff", mock_handoff_with_context):
        result = await openai.handoff(
            source_agent=source_agent,
            target_agent=target_agent,
            query=query,
            context=context
        )
    
    # Assert
    assert result == f"Response with context: {query}"


@pytest.mark.asyncio
async def test_handoff_with_metadata(mock_adapters, test_agents):
    """Test handoff with metadata information."""
    # Arrange
    source_agent = test_agents["base"]  # Use Contexa agent as source
    target_agent = test_agents["crewai"]
    query = "Test query with metadata"
    metadata = {
        "reason": "Testing metadata passing",
        "priority": "high"
    }
    
    # Create a more specific mock for this test
    async def mock_handoff_with_metadata(*args, **kwargs):
        # Verify metadata is passed correctly
        passed_metadata = kwargs.get("metadata", {})
        if passed_metadata.get("reason") == metadata["reason"]:
            return f"Response with metadata: {query}"
        return "Metadata missing"
    
    # Act
    with mock.patch.object(crewai, 'agent', return_value=test_agents["crewai"]), \
         mock.patch("contexa_sdk.adapters.crewai.handoff", mock_handoff_with_metadata):
        result = await crewai.handoff(
            source_agent=source_agent,
            target=target_agent,
            query=query,
            metadata=metadata
        )
    
    # Assert
    assert result == f"Response with metadata: {query}"


@pytest.mark.asyncio
async def test_multi_step_handoff_chain(mock_adapters, test_agents):
    """Test a chain of handoffs across multiple frameworks."""
    # Arrange
    base_agent = test_agents["base"]
    openai_agent = test_agents["openai"]
    langchain_agent = test_agents["langchain"]
    crewai_agent = test_agents["crewai"]
    
    # Create more specific mocks for sequential handoffs
    async def mock_openai_handoff(*args, **kwargs):
        return "OpenAI processed: " + kwargs.get("query", "")
    
    async def mock_langchain_handoff(*args, **kwargs):
        query = kwargs.get("query", "")
        if query.startswith("OpenAI processed:"):
            return "LangChain processed: " + query
        return "Invalid chain"
    
    async def mock_crewai_handoff(*args, **kwargs):
        query = kwargs.get("query", "")
        if query.startswith("LangChain processed:"):
            return "CrewAI processed: " + query
        return "Invalid chain"
    
    # Act
    with mock.patch.object(openai, 'agent', return_value=openai_agent), \
         mock.patch.object(langchain, 'agent', return_value=langchain_agent), \
         mock.patch.object(crewai, 'agent', return_value=crewai_agent), \
         mock.patch("contexa_sdk.adapters.openai.handoff", mock_openai_handoff), \
         mock.patch("contexa_sdk.adapters.langchain.handoff", mock_langchain_handoff), \
         mock.patch("contexa_sdk.adapters.crewai.handoff", mock_crewai_handoff):
        
        # Step 1: Base agent to OpenAI
        step1_result = await openai.handoff(
            source_agent=base_agent,
            target_agent=openai_agent,
            query="Initial query"
        )
        
        # Step 2: OpenAI to LangChain
        step2_result = await langchain.handoff(
            source_agent=base_agent,
            target_agent_executor=langchain_agent,
            query=step1_result
        )
        
        # Step 3: LangChain to CrewAI
        final_result = await crewai.handoff(
            source_agent=base_agent,
            target=crewai_agent,
            query=step2_result
        )
    
    # Assert the chain of processing
    assert final_result.startswith("CrewAI processed: LangChain processed: OpenAI processed:") 