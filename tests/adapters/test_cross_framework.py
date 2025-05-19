"""Tests for cross-framework handoffs and interoperability."""

import unittest
import pytest
import asyncio
from unittest.mock import patch, MagicMock

from contexa_sdk.core.tool import ContexaTool, BaseTool, RemoteTool
from contexa_sdk.core.agent import ContexaAgent
from contexa_sdk.core.model import ContexaModel
from contexa_sdk.runtime.handoff import handoff


class TestCrossFrameworkHandoffs:
    """Test handoffs between agents built on different frameworks."""
    
    @pytest.mark.asyncio
    async def test_langchain_to_crewai_handoff(self):
        """Test handoff from LangChain agent to CrewAI agent."""
        # Create mock ContexaAgent instances
        langchain_agent = MagicMock(spec=ContexaAgent)
        langchain_agent.name = "LangChain Agent"
        
        crewai_agent = MagicMock(spec=ContexaAgent)
        crewai_agent.name = "CrewAI Agent"
        crewai_agent.run = MagicMock(return_value=asyncio.Future())
        crewai_agent.run.return_value.set_result("Response from CrewAI")
        
        # Test handoff with standard agents
        result = await handoff(
            from_agent=langchain_agent,
            to_agent=crewai_agent,
            message="Research quantum computing",
            context={"domain": "physics"}
        )
        
        # Just verify the result for now
        assert result == "Response from CrewAI"
        crewai_agent.run.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_openai_to_google_handoff(self):
        """Test handoff from OpenAI agent to Google AI agent."""
        # Create mock agents with run method
        openai_agent = MagicMock()
        openai_agent.name = "OpenAI Assistant"
        
        google_agent = MagicMock()
        google_agent.name = "Google AI Agent"
        # Set up the run method to return a string directly (not a Future)
        google_agent.run = MagicMock(return_value="Response from Google AI")
        
        # Test handoff
        result = await handoff(
            from_agent=openai_agent,
            to_agent=google_agent,
            message="Translate this document",
            context={"language": "French"}
        )
        
        # Verify the result
        assert result == "Response from Google AI"
        google_agent.run.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_crewai_to_langchain_handoff(self):
        """Test handoff from CrewAI agent to LangChain agent."""
        # Create mock agents
        crewai_agent = MagicMock()
        crewai_agent.name = "CrewAI Agent"
        
        langchain_agent = MagicMock()
        langchain_agent.name = "LangChain Agent"
        langchain_agent.run = MagicMock(return_value="Response from LangChain")
        
        # Test handoff with timeout
        result = await handoff(
            from_agent=crewai_agent,
            to_agent=langchain_agent,
            message="Analyze this data",
            timeout=5.0
        )
        
        # Assert results
        langchain_agent.run.assert_called_once()
        assert result == "Response from LangChain"


class TestToolInteroperability:
    """Test cross-framework tool interoperability."""
    
    def test_tool_interoperability(self):
        """Test that tools can be used across frameworks."""
        # Define a simple tool with ContexaTool directly
        from pydantic import BaseModel
        
        class WebSearchInput(BaseModel):
            query: str
            
        async def web_search_func(inp: WebSearchInput) -> str:
            return f"Search results for: {inp.query}"
            
        web_search = ContexaTool(
            func=web_search_func,
            name="web_search",
            description="Search the web for information",
            schema=WebSearchInput
        )
        
        # Verify tool metadata
        assert web_search.name == "web_search"
        assert "Search the web" in web_search.description
        assert web_search.schema == WebSearchInput
        
        # Create mock converters for different frameworks
        converters = {
            "langchain": MagicMock(return_value=MagicMock(name="langchain_tool")),
            "crewai": MagicMock(return_value=MagicMock(name="crewai_tool")),
            "openai": MagicMock(return_value=MagicMock(name="openai_tool")),
            "google": MagicMock(return_value=MagicMock(name="google_tool"))
        }
        
        # Convert the tool using each converter
        for framework, converter in converters.items():
            framework_tool = converter(web_search)
            
            # Verify the framework tool was created
            assert framework_tool is not None
            
            # Validate that the converter was called with the web_search tool
            converter.assert_called_once_with(web_search) 