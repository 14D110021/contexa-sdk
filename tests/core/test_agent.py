import unittest
import asyncio
from unittest.mock import MagicMock, AsyncMock

from contexa_sdk.core.agent import ContexaAgent
from contexa_sdk.core.model import Model
from contexa_sdk.core.tool import Tool, ToolParameter
from contexa_sdk.core.memory import DefaultMemory, BaseMemory

# A simple mock model for testing
class MockModel(Model):
    name: str = "test_mock_model"
    description: str = "A mock model for testing purposes"

    async def generate(self, prompt: str, **kwargs) -> dict:
        # Simulate an API call delay
        await asyncio.sleep(0.01)
        if "error" in prompt.lower():
            raise Exception("Mock model error")
        return {"text": f"Mock response to: {prompt}"}

# A simple mock tool for testing
class MockTool(Tool):
    name: str = "mock_tool"
    description: str = "A mock tool for testing"
    parameters: list = [
        ToolParameter(name="param1", type="string", description="A test parameter")
    ]

    async def execute(self, param1: str, **kwargs) -> dict:
        await asyncio.sleep(0.01)
        if param1 == "error":
            raise Exception("Mock tool error")
        return {"result": f"Mock tool executed with {param1}"}

class TestContexaAgent(unittest.TestCase):

    def setUp(self):
        """Set up for test methods."""
        self.mock_model = MockModel()
        self.mock_tool = MockTool()
        self.mock_memory = DefaultMemory()
        
        self.agent = ContexaAgent(
            name="Test Agent",
            description="An agent for testing",
            model=self.mock_model,
            tools=[self.mock_tool],
            memory=self.mock_memory,
        )

    def test_agent_initialization(self):
        """Test if the agent is initialized correctly."""
        self.assertEqual(self.agent.name, "Test Agent")
        self.assertEqual(self.agent.description, "An agent for testing")
        self.assertIsInstance(self.agent.model, MockModel)
        self.assertEqual(len(self.agent.tools), 1)
        self.assertIsInstance(self.agent.tools[0], MockTool)
        self.assertIsInstance(self.agent.memory, DefaultMemory)

    def test_to_dict_and_from_dict_serialization(self):
        """Test agent serialization to and from dictionary."""
        agent_dict = self.agent.to_dict()
        
        expected_keys = ["name", "description", "model", "tools", "memory", "config"]
        for key in expected_keys:
            self.assertIn(key, agent_dict)
            
        self.assertEqual(agent_dict["name"], "Test Agent")
        self.assertEqual(agent_dict["model"]["class_name"], "MockModel")
        self.assertEqual(len(agent_dict["tools"]), 1)
        self.assertEqual(agent_dict["tools"][0]["class_name"], "MockTool")
        self.assertEqual(agent_dict["memory"]["class_name"], "DefaultMemory")

    def test_add_tool(self):
        """Test adding a tool to the agent."""
        initial_tool_count = len(self.agent.tools)
        new_tool = MockTool(name="new_mock_tool")
        self.agent.add_tool(new_tool)
        self.assertEqual(len(self.agent.tools), initial_tool_count + 1)
        self.assertIn(new_tool, self.agent.tools)

    def test_remove_tool(self):
        """Test removing a tool from the agent."""
        tool_to_remove = self.agent.tools[0]
        initial_tool_count = len(self.agent.tools)
        
        self.agent.remove_tool(tool_to_remove.name)
        self.assertEqual(len(self.agent.tools), initial_tool_count - 1)
        self.assertNotIn(tool_to_remove, self.agent.tools)

        with self.assertRaises(ValueError):
            self.agent.remove_tool("non_existent_tool")

    def test_get_tool(self):
        """Test getting a tool by its name."""
        tool_name = self.mock_tool.name
        retrieved_tool = self.agent.get_tool(tool_name)
        self.assertIsInstance(retrieved_tool, MockTool)
        self.assertEqual(retrieved_tool.name, tool_name)

        self.assertIsNone(self.agent.get_tool("non_existent_tool"))
        
    async def test_run_agent_with_mock_model_simple_prompt(self):
        """Test the agent's run method with a simple prompt and mock model."""
        prompt = "Hello, world!"
        expected_response_text = f"Mock response to: {prompt}"
        
        response = await self.agent.run(prompt)
        
        self.assertIsInstance(response, str)
        self.assertEqual(response, expected_response_text)
        
        history = self.agent.memory.get_history()
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0]["role"], "user")
        self.assertEqual(history[0]["content"], prompt)
        self.assertEqual(history[1]["role"], "assistant")
        self.assertEqual(history[1]["content"], expected_response_text)

    async def test_run_agent_with_context(self):
        """Test the agent's run method with additional context."""
        prompt = "Tell me a joke"
        context = {"user_mood": "happy", "previous_topic": "AI"}
        expected_response_text = f"Mock response to: {prompt}"
        
        response = await self.agent.run(prompt, context=context)
        self.assertEqual(response, expected_response_text)

    async def test_run_agent_model_error_handling(self):
        """Test error handling when the model's generate method raises an exception."""
        prompt_that_causes_error = "error in model"
        
        with self.assertRaises(Exception):
            await self.agent.run(prompt_that_causes_error)
            
        history = self.agent.memory.get_history()
        self.assertEqual(len(history), 1) 
        self.assertEqual(history[0]["role"], "user")
        self.assertEqual(history[0]["content"], prompt_that_causes_error)

if __name__ == '__main__':
    # This allows running the tests directly from this file
    unittest.main()
