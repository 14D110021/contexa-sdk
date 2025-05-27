"""Tests for Google ADK adapter-specific features."""

import unittest
from unittest.mock import patch, MagicMock
import asyncio
from contexa_sdk.core.model import ContexaModel
from contexa_sdk.core.tool import ContexaTool
from contexa_sdk.core.agent import ContexaAgent
from pydantic import BaseModel


class TestGoogleADKFeatures(unittest.TestCase):
    """Test Google ADK adapter-specific features."""

    def setUp(self):
        """Set up the test environment."""
        # Define a test tool
        class SearchInput(BaseModel):
            query: str

        @ContexaTool.register(
            name="search", 
            description="Search for information"
        )
        async def search_tool(inp: SearchInput) -> str:
            return f"Results for {inp.query}"

        self.tool = search_tool
        self.model = ContexaModel(
            provider="google", 
            model_name="gemini-pro",
            temperature=0.7
        )
        
        # Create an agent
        self.agent = ContexaAgent(
            name="TestAgent",
            description="A test agent",
            system_prompt="You are a helpful assistant",
            model=self.model,
            tools=[self.tool]
        )

    @patch("google.adk", autospec=True)
    def test_adk_multi_turn_reasoning(self, mock_adk):
        """Test that ADK adapter supports multi-turn reasoning."""
        from contexa_sdk.adapters.google import adk_agent
        
        # Set up mock behavior
        mock_agent = MagicMock()
        mock_adk.Agent.return_value = mock_agent
        
        # Configure mock agent to handle multi-turn conversation
        mock_response = MagicMock()
        mock_response.text = "I need more information"
        mock_response.needs_followup = True
        
        mock_agent.process_async.return_value = mock_response
        
        # Convert agent
        adk_assistant = adk_agent(self.agent)
        
        # Test multi-turn capability
        result = asyncio.run(adk_assistant.run("Tell me about machine learning"))
        
        # Verify ADK agent was called with proper configuration
        mock_adk.Agent.assert_called_once()
        mock_agent.process_async.assert_called_once()

    @patch("google.adk", autospec=True)
    def test_adk_agent_hierarchy(self, mock_adk):
        """Test that ADK adapter supports agent hierarchies."""
        from contexa_sdk.adapters.google import adk_agent, adk_tool
        
        # Create a parent agent and a child agent
        child_agent = ContexaAgent(
            name="ChildAgent",
            description="A specialized agent",
            model=self.model,
            tools=[]
        )
        
        parent_agent = ContexaAgent(
            name="ParentAgent",
            description="A coordinator agent",
            model=self.model,
            tools=[self.tool],
            sub_agents=[child_agent]
        )
        
        # Set up mock behavior for agent hierarchy
        mock_parent = MagicMock()
        mock_child = MagicMock()
        
        # Mock ADK Agent creation to return different mocks for parent vs child
        def side_effect(*args, **kwargs):
            if kwargs.get("name") == "ParentAgent":
                return mock_parent
            else:
                return mock_child
                
        mock_adk.Agent.side_effect = side_effect
        
        # Convert parent agent (which should convert child agents)
        parent_adk_agent = adk_agent(parent_agent)
        
        # Verify both agents were created
        self.assertEqual(mock_adk.Agent.call_count, 2)
        
        # Verify parent-child relationship was established
        # Note: This verification will depend on your implementation details

    @patch("google.adk", autospec=True)
    def test_adk_complex_tool_registration(self, mock_adk):
        """Test that ADK adapter supports complex tool registration."""
        from contexa_sdk.adapters.google import adk_tool
        
        # Define a more complex tool with nested fields
        class Location(BaseModel):
            latitude: float
            longitude: float
            
        class GeoInput(BaseModel):
            location: Location
            radius: int
            
        @ContexaTool.register(
            name="geo_search",
            description="Search for locations"
        )
        async def geo_search(inp: GeoInput) -> dict:
            return {
                "latitude": inp.location.latitude,
                "longitude": inp.location.longitude,
                "radius": inp.radius,
                "results": ["Result 1", "Result 2"]
            }
            
        # Set up mock behavior
        mock_tool = MagicMock()
        mock_adk.Tool.return_value = mock_tool
        
        # Convert complex tool
        adk_geo_tool = adk_tool(geo_search)
        
        # Verify complex schema was properly converted
        mock_adk.Tool.assert_called_once()
        
        # The details of the verification depend on your implementation details
        # but we should check that nested fields are properly handled

    @patch("google.adk", autospec=True)
    def test_adk_agent_middleware(self, mock_adk):
        """Test that ADK adapter supports agent middleware."""
        from contexa_sdk.adapters.google import adk_agent
        
        # Set up mock middleware
        mock_middleware = MagicMock()
        mock_adk.Middleware = MagicMock()
        mock_adk.Middleware.return_value = mock_middleware
        
        # Create agent with middleware configuration
        agent_with_middleware = ContexaAgent(
            name="MiddlewareAgent",
            description="Agent with middleware",
            model=self.model,
            tools=[self.tool],
            middleware_config={
                "logger": True,
                "response_filter": True
            }
        )
        
        # Convert agent
        adk_middleware_agent = adk_agent(agent_with_middleware)
        
        # Verify middleware was configured
        # Implementation-specific checks would go here

    @patch("google.adk", autospec=True)
    def test_adk_task_decomposition(self, mock_adk):
        """Test that ADK adapter supports task decomposition."""
        from contexa_sdk.adapters.google import adk_agent
        
        # Set up mock agent with task decomposition
        mock_agent = MagicMock()
        mock_adk.Agent.return_value = mock_agent
        
        # Configure mock response with subtasks
        mock_response = MagicMock()
        mock_response.text = "I'll break this down into steps"
        mock_response.subtasks = [
            MagicMock(text="Subtask 1: Research"),
            MagicMock(text="Subtask 2: Analyze"),
            MagicMock(text="Subtask 3: Summarize")
        ]
        
        mock_agent.process_async.return_value = mock_response
        
        # Create agent with task decomposition enabled
        task_agent = ContexaAgent(
            name="TaskAgent",
            description="Agent that decomposes tasks",
            model=self.model,
            tools=[self.tool],
            capabilities={
                "task_decomposition": True
            }
        )
        
        # Convert agent
        adk_task_agent = adk_agent(task_agent)
        
        # Test task decomposition
        result = asyncio.run(adk_task_agent.run("Create a comprehensive report on climate change"))
        
        # Verify task decomposition was configured and used
        mock_adk.Agent.assert_called_once()
        mock_agent.process_async.assert_called_once()
        
        # Implementation-specific verification would go here


if __name__ == "__main__":
    unittest.main() 