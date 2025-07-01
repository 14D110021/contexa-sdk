import unittest
from unittest.mock import MagicMock, patch
import asyncio

from contexa_sdk.core.agent import ContexaAgent, AgentMemory
from contexa_sdk.core.model import ContexaModel, ModelResponse, ModelMessage
from contexa_sdk.observability.logger import get_logger, set_log_level, configure_logging, log_event

# Mock model for testing
class MockModel(ContexaModel):
    def __init__(self):
        super().__init__(model_name="mock_model", provider="mock")
    
    async def generate(self, messages, **kwargs):
        await asyncio.sleep(0.01)
        return ModelResponse(
            content=f"Response to: {messages[-1].content if messages else 'empty'}",
            model="mock_model",
            usage={"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30}
        )

class TestObservability(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_model = MockModel()
        self.mock_memory = AgentMemory()
        
        # Create agent with empty tools list
        self.agent = ContexaAgent(
            name="Test Agent with Observability",
            description="An agent for testing observability",
            model=self.mock_model,
            memory=self.mock_memory,
            tools=[]  # Empty tools list for testing
        )

    async def test_agent_run_with_logging(self):
        """Test that agent run works with logging enabled."""
        prompt = "Test prompt"
        
        # Run the agent
        result = await self.agent.run(prompt)
        
        # Basic test that agent ran successfully
        self.assertIsNotNone(result)
        self.assertIn("Response to:", result)
    
    def test_get_logger(self):
        """Test that get_logger creates a logger."""
        logger = get_logger('test_logger')
        self.assertIsNotNone(logger)
        self.assertEqual(logger.name, 'test_logger')
        
    def test_set_log_level(self):
        """Test setting log levels."""
        # Test string level
        set_log_level('DEBUG')
        
        # Test integer level
        import logging
        set_log_level(logging.INFO)
        
        # This should not raise an exception
        self.assertTrue(True)
    
    def test_configure_logging(self):
        """Test logging configuration."""
        # Test basic configuration
        configure_logging(level='INFO')
        
        # Test JSON configuration
        configure_logging(level='DEBUG', output_format='json')
        
        # Test structured logging
        configure_logging(level='INFO', structured=True)
        
        # This should not raise an exception
        self.assertTrue(True)
    
    def test_log_event(self):
        """Test structured event logging."""
        # Test simple event
        log_event('test_event')
        
        # Test event with data
        log_event('test_event_with_data', data={'key': 'value'})
        
        # This should not raise an exception
        self.assertTrue(True)

    async def test_default_observability_components(self):
        """Test that default observability components work."""
        # Create agent with standard configuration
        agent = ContexaAgent(
            name="Test Agent",
            description="An agent for testing default observability",
            model=self.mock_model,
            memory=self.mock_memory, tools=[]
        )
        
        # Run the agent
        result = await agent.run("Test prompt")
        
        # Verify agent ran successfully
        self.assertIsNotNone(result)
        self.assertIn("Response to:", result)

if __name__ == '__main__':
    unittest.main() 