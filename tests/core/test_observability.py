import unittest
from unittest.mock import MagicMock, patch
import asyncio

from contexa_sdk.core.agent import ContexaAgent
from contexa_sdk.core.observability import Metrics, Logs, Traces, ObservabilityConfig
from contexa_sdk.core.model import Model
from contexa_sdk.core.memory import DefaultMemory

# Mock model for testing
class MockModel(Model):
    name: str = "mock_model"
    description: str = "A mock model for testing"

    async def generate(self, prompt: str, **kwargs) -> dict:
        await asyncio.sleep(0.01)
        return {"text": f"Response to: {prompt}"}

class TestObservability(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_model = MockModel()
        self.mock_memory = DefaultMemory()
        
        # Create mocked observability components
        self.mock_metrics = MagicMock(spec=Metrics)
        self.mock_logs = MagicMock(spec=Logs)
        self.mock_traces = MagicMock(spec=Traces)
        
        # Create observability config with mocked components
        self.observability_config = ObservabilityConfig(
            enabled=True,
            metrics=self.mock_metrics,
            logs=self.mock_logs,
            traces=self.mock_traces
        )
        
        # Create agent with mocked observability
        self.agent = ContexaAgent(
            name="Test Agent with Observability",
            description="An agent for testing observability",
            model=self.mock_model,
            memory=self.mock_memory,
            config={"observability": self.observability_config}
        )

    async def test_metrics_recorded_during_run(self):
        """Test that metrics are recorded during agent run."""
        prompt = "Test prompt"
        
        # Run the agent
        await self.agent.run(prompt)
        
        # Verify metrics were recorded
        self.mock_metrics.record_request.assert_called()
        self.mock_metrics.record_tokens.assert_called()
        self.mock_metrics.record_latency.assert_called()
    
    async def test_logs_recorded_during_run(self):
        """Test that logs are recorded during agent run."""
        prompt = "Test prompt"
        
        # Run the agent
        await self.agent.run(prompt)
        
        # Verify logs were recorded
        self.mock_logs.info.assert_called()
        
    async def test_traces_recorded_during_run(self):
        """Test that traces are recorded during agent run."""
        prompt = "Test prompt"
        
        # Run the agent
        await self.agent.run(prompt)
        
        # Verify traces were recorded
        self.mock_traces.start_span.assert_called()
        self.mock_traces.end_span.assert_called()
    
    @patch('contexa_sdk.core.observability.Metrics')
    @patch('contexa_sdk.core.observability.Logs')
    @patch('contexa_sdk.core.observability.Traces')
    async def test_default_observability_components(self, mock_traces_cls, mock_logs_cls, mock_metrics_cls):
        """Test that default observability components are created if not specified."""
        # Setup the mocks to return MagicMock instances
        mock_traces_cls.return_value = MagicMock()
        mock_logs_cls.return_value = MagicMock()
        mock_metrics_cls.return_value = MagicMock()
        
        # Create agent with observability enabled but no specific components
        agent = ContexaAgent(
            name="Test Agent",
            description="An agent for testing default observability",
            model=self.mock_model,
            memory=self.mock_memory,
            config={"observability": {"enabled": True}}
        )
        
        # Run the agent
        await agent.run("Test prompt")
        
        # Verify default components were created
        mock_traces_cls.assert_called_once()
        mock_logs_cls.assert_called_once()
        mock_metrics_cls.assert_called_once()

if __name__ == '__main__':
    unittest.main() 