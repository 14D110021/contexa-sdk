"""Example demonstrating Cluster Agent Runtime functionality.

This example shows how to set up a simulated cluster with
a coordinator node and worker nodes to manage distributed agents.
"""

import asyncio
import logging
import os
import time
from typing import Dict, List, Optional, Any

from contexa_sdk.core.agent import ContexaAgent
from contexa_sdk.core.agent import AgentMemory
from contexa_sdk.core.model import ContexaModel
from contexa_sdk.core.tool import Tool, ToolParameter
from contexa_sdk.runtime import (
    AgentRuntimeConfig,
    ResourceLimits,
    FileStateProvider
)
from contexa_sdk.runtime.cluster_runtime import ClusterAgentRuntime


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
        """Execute the calculator operation."""
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
    
    def __init__(self, node_id: str = "unknown"):
        """Initialize the mock model."""
        super().__init__()
        self.response_delay = 0.5  # Simulate processing time
        self.node_id = node_id
    
    async def generate(
        self, prompt: str, **kwargs
    ) -> Dict[str, Any]:
        """Generate a response for the given prompt."""
        # Simulate processing time
        await asyncio.sleep(self.response_delay)
        
        # Generate a mock response that includes the node ID
        if "weather" in prompt.lower():
            return {"text": f"[Node {self.node_id}] It's sunny today with a high of 75°F."}
        elif "hello" in prompt.lower() or "hi" in prompt.lower():
            return {"text": f"[Node {self.node_id}] Hello! How can I assist you today?"}
        elif "calculator" in prompt.lower() or "math" in prompt.lower():
            return {"text": f"[Node {self.node_id}] I can help with math. Use the calculator tool."}
        elif "help" in prompt.lower():
            return {"text": f"[Node {self.node_id}] I'm a simple agent running on node {self.node_id}."}
        else:
            return {"text": f"[Node {self.node_id}] I'm not sure how to respond to that."}


async def setup_coordinator():
    """Set up the coordinator node."""
    # Create a temp directory for state persistence
    state_dir = os.path.join(os.path.dirname(__file__), "temp_state")
    os.makedirs(state_dir, exist_ok=True)
    
    # Create a state provider that persists to disk
    state_provider = FileStateProvider(state_dir)
    
    # Configure the runtime with resource limits
    config = AgentRuntimeConfig(
        max_agents=10,
        default_resource_limits=ResourceLimits(
            max_memory_mb=200,
            max_cpu_percent=50,
            max_requests_per_minute=30,
            max_tokens_per_minute=1000
        ),
        state_provider=state_provider,
        health_check_interval_seconds=10,
        additional_options={
            "state_save_interval_seconds": 30,
            "heartbeat_interval_seconds": 5,
            "node_check_interval_seconds": 10
        }
    )
    
    # Create the coordinator runtime
    coordinator = ClusterAgentRuntime(
        config=config,
        is_coordinator=True,
        node_id="coordinator-1",
        node_endpoint="http://localhost:8000"  # Simulated endpoint
    )
    
    # Start the coordinator
    await coordinator.start()
    logger.info("Coordinator node started")
    
    return coordinator


async def setup_worker(coordinator_endpoint: str, node_id: str):
    """Set up a worker node."""
    # Configure the runtime
    config = AgentRuntimeConfig(
        max_agents=5,
        default_resource_limits=ResourceLimits(
            max_memory_mb=100,
            max_cpu_percent=30,
            max_requests_per_minute=20,
            max_tokens_per_minute=500
        ),
        additional_options={
            "heartbeat_interval_seconds": 5
        }
    )
    
    # Create the worker runtime
    worker = ClusterAgentRuntime(
        config=config,
        coordinator_endpoint=coordinator_endpoint,
        node_id=node_id,
        node_endpoint=f"http://localhost:800{node_id[-1]}"  # Simulated endpoint
    )
    
    # Start the worker
    await worker.start()
    logger.info(f"Worker node {node_id} started")
    
    return worker


async def run_example():
    """Run the Cluster Agent Runtime example."""
    try:
        # Set up the coordinator node
        coordinator = await setup_coordinator()
        
        # Set up worker nodes
        worker1 = await setup_worker("http://localhost:8000", "worker-1")
        worker2 = await setup_worker("http://localhost:8000", "worker-2")
        
        # Create and register agents on the coordinator
        coordinator_agent = ContexaAgent(
            name="Coordinator Agent",
            description="Agent running on the coordinator node",
            model=MockModel(node_id="coordinator-1"),
            tools=[CalculatorTool()],
            memory=AgentMemory()
        )
        
        coordinator_agent_id = await coordinator.register_agent(coordinator_agent)
        logger.info(f"Registered coordinator agent with ID: {coordinator_agent_id}")
        
        # Create and register agents on worker nodes
        worker1_agent = ContexaAgent(
            name="Worker 1 Agent",
            description="Agent running on worker node 1",
            model=MockModel(node_id="worker-1"),
            tools=[CalculatorTool()],
            memory=AgentMemory()
        )
        
        worker1_agent_id = await worker1.register_agent(worker1_agent)
        logger.info(f"Registered worker 1 agent with ID: {worker1_agent_id}")
        
        worker2_agent = ContexaAgent(
            name="Worker 2 Agent",
            description="Agent running on worker node 2",
            model=MockModel(node_id="worker-2"),
            tools=[CalculatorTool()],
            memory=AgentMemory()
        )
        
        worker2_agent_id = await worker2.register_agent(worker2_agent)
        logger.info(f"Registered worker 2 agent with ID: {worker2_agent_id}")
        
        # Run queries on all agents
        queries = [
            "Hello there!",
            "What can you help me with?",
            "Tell me about yourself",
        ]
        
        # Run queries on the coordinator agent
        logger.info("Running queries on coordinator agent")
        for query in queries:
            response = await coordinator.run_agent(coordinator_agent_id, query)
            logger.info(f"Coordinator agent response: {response}")
            await asyncio.sleep(0.5)
        
        # Run queries on worker 1 agent
        logger.info("Running queries on worker 1 agent")
        for query in queries:
            response = await worker1.run_agent(worker1_agent_id, query)
            logger.info(f"Worker 1 agent response: {response}")
            await asyncio.sleep(0.5)
        
        # Run queries on worker 2 agent
        logger.info("Running queries on worker 2 agent")
        for query in queries:
            response = await worker2.run_agent(worker2_agent_id, query)
            logger.info(f"Worker 2 agent response: {response}")
            await asyncio.sleep(0.5)
        
        # Simulate using coordinator to access worker agents
        # In a real implementation, this would work through the coordinator API
        logger.info("Demonstrating cross-node communication (simulated)")
        logger.info("In a full implementation, the coordinator would route requests to workers")
        
        # Save agent states
        await coordinator.save_agent_state(coordinator_agent_id)
        await worker1.save_agent_state(worker1_agent_id)
        await worker2.save_agent_state(worker2_agent_id)
        logger.info("Saved all agent states")
        
        # Simulate node failure and recovery
        logger.info("Simulating node failure and recovery (conceptual only)")
        logger.info("In a full implementation, the coordinator would detect node failures")
        logger.info("and migrate agents to healthy nodes")
        
        # Stop all runtimes
        await worker2.stop()
        await worker1.stop()
        await coordinator.stop()
        logger.info("All nodes stopped")
        
    finally:
        # Clean up the temp directory (in a real application, you'd keep this)
        state_dir = os.path.join(os.path.dirname(__file__), "temp_state")
        import shutil
        if os.path.exists(state_dir):
            shutil.rmtree(state_dir)


if __name__ == "__main__":
    asyncio.run(run_example()) 