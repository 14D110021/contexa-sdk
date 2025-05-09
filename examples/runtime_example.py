"""Example demonstrating Agent Runtime functionality.

This example shows how to use the LocalAgentRuntime to manage
agent lifecycles, including starting, running, and monitoring
the health of agents.
"""

import asyncio
import logging
import os
import time
from typing import Dict, List, Optional, Any

from contexa_sdk.core.agent import ContexaAgent
from contexa_sdk.core.memory import DefaultMemory
from contexa_sdk.core.model import Model
from contexa_sdk.core.tool import Tool, ToolParameter
from contexa_sdk.runtime import (
    AgentRuntimeConfig,
    ResourceLimits,
    FileStateProvider
)
from contexa_sdk.runtime.local_runtime import LocalAgentRuntime


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


# Define a simple tool for the agent
class CalculatorTool(Tool):
    """Simple calculator tool for basic math operations."""
    
    name: str = "calculator"
    description: str = "Perform basic math operations like add, subtract, multiply, divide"
    
    parameters: List[ToolParameter] = [
        ToolParameter(
            name="operation",
            description="Math operation: add, subtract, multiply, divide",
            type="string",
            required=True
        ),
        ToolParameter(
            name="a",
            description="First number",
            type="number",
            required=True
        ),
        ToolParameter(
            name="b",
            description="Second number",
            type="number",
            required=True
        )
    ]
    
    async def execute(
        self, operation: str, a: float, b: float, **kwargs
    ) -> Dict[str, Any]:
        """Execute the calculator operation.
        
        Args:
            operation: The operation to perform (add, subtract, multiply, divide)
            a: First number
            b: Second number
            
        Returns:
            Dict with result of the operation
        """
        operation = operation.lower()
        
        if operation == "add":
            result = a + b
        elif operation == "subtract":
            result = a - b
        elif operation == "multiply":
            result = a * b
        elif operation == "divide":
            if b == 0:
                raise ValueError("Cannot divide by zero")
            result = a / b
        else:
            raise ValueError(f"Unknown operation: {operation}")
        
        return {"result": result}


# Create a mock model for the agent
class MockModel(Model):
    """Mock model implementation that returns predefined responses."""
    
    name: str = "mock-model"
    description: str = "Mock model for testing"
    
    def __init__(self):
        """Initialize the mock model."""
        super().__init__()
        self.response_delay = 0.5  # Simulate processing time
    
    async def generate(
        self, prompt: str, **kwargs
    ) -> Dict[str, Any]:
        """Generate a response for the given prompt.
        
        Args:
            prompt: The prompt to generate a response for
            
        Returns:
            Dict with the generated text
        """
        # Simulate processing time
        await asyncio.sleep(self.response_delay)
        
        # Generate a mock response
        if "weather" in prompt.lower():
            return {"text": "It's sunny today with a high of 75°F."}
        elif "hello" in prompt.lower() or "hi" in prompt.lower():
            return {"text": "Hello! How can I assist you today?"}
        elif "calculator" in prompt.lower() or "math" in prompt.lower():
            return {"text": "I can help with math. Use the calculator tool with 'operation', 'a', and 'b' parameters."}
        elif "help" in prompt.lower():
            return {"text": "I'm a simple agent. You can ask about the weather, say hello, or use the calculator tool."}
        else:
            return {"text": "I'm not sure how to respond to that. Try asking about the weather or using the calculator tool."}


async def run_example():
    """Run the Agent Runtime example."""
    # Create a temp directory for state persistence
    state_dir = os.path.join(os.path.dirname(__file__), "temp_state")
    os.makedirs(state_dir, exist_ok=True)
    
    try:
        # Create a state provider that persists to disk
        state_provider = FileStateProvider(state_dir)
        
        # Configure the runtime with resource limits
        config = AgentRuntimeConfig(
            max_agents=5,
            default_resource_limits=ResourceLimits(
                max_memory_mb=100,
                max_cpu_percent=50,
                max_requests_per_minute=30,
                max_tokens_per_minute=1000
            ),
            state_provider=state_provider,
            health_check_interval_seconds=10,
            additional_options={
                "state_save_interval_seconds": 30  # Save state every 30 seconds
            }
        )
        
        # Create the runtime
        runtime = LocalAgentRuntime(config=config)
        await runtime.start()
        logger.info("Runtime started")
        
        # Create an agent
        agent = ContexaAgent(
            name="Calculator Assistant",
            description="An assistant that can perform basic math operations",
            model=MockModel(),
            tools=[CalculatorTool()],
            memory=DefaultMemory()
        )
        
        # Register the agent with the runtime
        agent_id = await runtime.register_agent(agent)
        logger.info(f"Registered agent with ID: {agent_id}")
        
        # Run some queries
        queries = [
            "Hello there!",
            "Can you help me with some math?",
            "Calculate 5 + 3",
            "What's 10 multiplied by 7?",
            "Divide 100 by 5"
        ]
        
        for query in queries:
            logger.info(f"Sending query: {query}")
            response = await runtime.run_agent(agent_id, query)
            logger.info(f"Response: {response}")
            
            # Get resource usage
            usage = await runtime.get_resource_usage(agent_id)
            logger.info(f"Resource usage: Memory: {usage.memory_mb:.2f} MB, CPU: {usage.cpu_percent:.2f}%")
            
            # Check health
            health = await runtime.check_health(agent_id)
            logger.info(f"Agent health: {health['status']}")
            
            # Wait a bit between queries
            await asyncio.sleep(1)
        
        # Save agent state
        await runtime.save_agent_state(agent_id)
        logger.info("Saved agent state")
        
        # Stop the runtime
        await runtime.stop()
        logger.info("Runtime stopped")
        
    finally:
        # Clean up the temp directory (in a real application, you'd keep this)
        import shutil
        if os.path.exists(state_dir):
            shutil.rmtree(state_dir)


if __name__ == "__main__":
    asyncio.run(run_example()) 