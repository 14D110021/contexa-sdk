import unittest
import asyncio
from unittest.mock import MagicMock, AsyncMock

from contexa_sdk.core.agent import ContexaAgent, AgentMemory
from contexa_sdk.core.model import ContexaModel, ModelResponse, ModelMessage
from contexa_sdk.core.tool import ContexaTool, BaseTool

# A simple mock model for testing
class MockModel(ContexaModel):
    def __init__(self):
        super().__init__(model_name="test_mock_model", provider="mock")

    async def generate(self, messages, **kwargs):
        # Simulate an API call delay
        await asyncio.sleep(0.01)
        prompt = messages[-1].content if messages else ""
        if "error" in prompt.lower():
            raise Exception("Mock model error")
        return ModelResponse(
            content=f"Mock response to: {prompt}",
            model="test_mock_model",
            usage={"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30}
        )

# A simple mock tool for testing
@ContexaTool.register(
    name="mock_tool",
    description="A mock tool for testing"
)
async def mock_tool_func(param1: str) -> str:
    await asyncio.sleep(0.01)
    if param1 == "error":
        raise Exception("Mock tool error")
    return f"Mock tool executed with {param1}"

class TestContexaAgent(unittest.TestCase):

    def setUp(self):
        """Set up for test methods."""
        self.mock_model = MockModel()
        self.mock_tool = mock_tool_func.__contexa_tool__
        self.mock_memory = AgentMemory()
        
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
        self.assertIsInstance(self.agent.tools[0], ContexaTool)
        self.assertIsInstance(self.agent.memory, AgentMemory)

    def test_to_dict_serialization(self):
        """Test agent serialization to dictionary."""
        agent_dict = self.agent.to_dict()
        
        # Check that basic keys are present
        self.assertIn("name", agent_dict)
        self.assertIn("description", agent_dict)
        self.assertIn("tools", agent_dict)
        self.assertIn("model", agent_dict)
        self.assertIn("memory", agent_dict)
            
        self.assertEqual(agent_dict["name"], "Test Agent")
        self.assertEqual(len(agent_dict["tools"]), 1)

    async def test_run_agent_with_mock_model_simple_prompt(self):
        """Test the agent's run method with a simple prompt and mock model."""
        prompt = "Hello, world!"
        expected_response_text = f"Mock response to: {prompt}"
        
        response = await self.agent.run(prompt)
        
        self.assertIsInstance(response, str)
        self.assertEqual(response, expected_response_text)
        
        # Check that messages were added to memory
        messages = self.agent.memory.get_messages()
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0].role, "user")
        self.assertEqual(messages[0].content, prompt)
        self.assertEqual(messages[1].role, "assistant")
        self.assertEqual(messages[1].content, expected_response_text)

    async def test_run_agent_with_context(self):
        """Test the agent's run method with additional context."""
        prompt = "Tell me a joke"
        expected_response_text = f"Mock response to: {prompt}"
        
        response = await self.agent.run(prompt)
        self.assertEqual(response, expected_response_text)

    async def test_run_agent_model_error_handling(self):
        """Test error handling when the model's generate method raises an exception."""
        prompt_that_causes_error = "error in model"
        
        with self.assertRaises(Exception):
            await self.agent.run(prompt_that_causes_error)
            
        # Check that user message was added even though generation failed
        messages = self.agent.memory.get_messages()
        self.assertEqual(len(messages), 1) 
        self.assertEqual(messages[0].role, "user")
        self.assertEqual(messages[0].content, prompt_that_causes_error)

    def test_tools_available(self):
        """Test that tools are available on the agent."""
        self.assertEqual(len(self.agent.tools), 1)
        self.assertEqual(self.agent.tools[0].name, "mock_tool")

    def test_memory_operations(self):
        """Test basic memory operations."""
        # Test adding a message
        self.agent.memory.add_message("user", "test message")
        messages = self.agent.memory.get_messages()
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].content, "test message")
        
        # Test clearing memory
        self.agent.memory.clear()
        messages = self.agent.memory.get_messages()
        self.assertEqual(len(messages), 0)

if __name__ == '__main__':
    # This allows running the tests directly from this file
    unittest.main()
