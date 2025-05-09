# Contexa SDK Agent Runtime

The Agent Runtime module provides infrastructure for managing AI agent lifecycles and execution environments. It handles agent coordination, resource allocation, state persistence, and health monitoring.

## Core Features

### Agent Lifecycle Management

- **Starting and stopping agents**: Provides methods to initialize and cleanly shut down agents
- **Pause and resume**: Allows suspending agent execution while retaining state
- **Registering and unregistering**: Manages agent registration with runtime environments

### State Persistence

- **Checkpointing and recovery**: Persists agent state to recover from failures
- **Conversation history**: Preserves memory and context between agent restarts
- **Custom state handling**: Supports agent-specific state formats with flexible serialization

### Resource Management

- **Resource tracking**: Monitors memory, CPU, and API token usage
- **Resource limits**: Enforces constraints on resource consumption
- **Scaling**: Adjusts resources based on workload (in cluster environments)

### Health Monitoring

- **Automated health checks**: Continuously monitors agent health status
- **Auto-recovery**: Attempts to restore agents experiencing issues
- **Diagnostics**: Provides insights into agent performance and errors

## Architecture

The Agent Runtime is designed with modular components:

```
runtime/
├── __init__.py             # Module exports
├── agent_runtime.py        # Core interfaces and abstract base classes
├── state_management.py     # State persistence interfaces and implementations
├── resource_tracking.py    # Resource usage monitoring
├── health_monitoring.py    # Health checks and recovery mechanisms
├── local_runtime.py        # Single-process runtime implementation
└── cluster_runtime.py      # Distributed runtime for multi-node deployments
```

## Usage Examples

### Basic Usage

```python
import asyncio
from contexa_sdk.core.agent import ContexaAgent
from contexa_sdk.runtime import AgentRuntimeConfig, FileStateProvider
from contexa_sdk.runtime.local_runtime import LocalAgentRuntime

async def main():
    # Configure the runtime
    config = AgentRuntimeConfig(
        state_provider=FileStateProvider("./agent_states"),
        health_check_interval_seconds=30
    )
    
    # Create and start the runtime
    runtime = LocalAgentRuntime(config=config)
    await runtime.start()
    
    # Register an agent
    agent = ContexaAgent(
        name="Assistant",
        description="A helpful assistant",
        model=my_model,
        tools=my_tools
    )
    agent_id = await runtime.register_agent(agent)
    
    # Run the agent
    response = await runtime.run_agent(agent_id, "Hello, how can you help me?")
    print(response)
    
    # Check agent health
    health = await runtime.check_health(agent_id)
    print(f"Agent health: {health['status']}")
    
    # Save agent state
    await runtime.save_agent_state(agent_id)
    
    # Stop the runtime
    await runtime.stop()

if __name__ == "__main__":
    asyncio.run(main())
```

### Using the Cluster Runtime

```python
from contexa_sdk.runtime.cluster_runtime import ClusterAgentRuntime

# Create a coordinator node
coordinator = ClusterAgentRuntime(
    is_coordinator=True,
    node_endpoint="http://localhost:8000"
)
await coordinator.start()

# Create a worker node
worker = ClusterAgentRuntime(
    coordinator_endpoint="http://localhost:8000",
    node_endpoint="http://localhost:8001"
)
await worker.start()

# Register an agent on the coordinator
agent_id = await coordinator.register_agent(my_agent)

# Run the agent (automatically routed to the appropriate node)
response = await coordinator.run_agent(agent_id, "Process this request")
```

## State Providers

The runtime supports different state persistence mechanisms:

- **InMemoryStateProvider**: Keeps state in memory (for testing or ephemeral agents)
- **FileStateProvider**: Persists state to the filesystem as JSON files
- Custom providers: Implement the `StateProvider` interface for your own storage backends

## Health Checks

Built-in health checks include:

- **ResourceHealthCheck**: Monitors resource usage against defined limits
- **ResponseTimeHealthCheck**: Tracks and analyzes agent response times
- Custom checks: Extend the `HealthCheck` base class for specialized monitoring

## Resource Tracking

The runtime tracks various resource metrics:

- Memory usage
- CPU utilization  
- Requests per minute
- Tokens per minute
- Concurrent requests

## Configuration

The `AgentRuntimeConfig` class allows customizing runtime behavior:

```python
config = AgentRuntimeConfig(
    max_agents=10,  # Maximum number of agents to support
    default_resource_limits=ResourceLimits(
        max_memory_mb=500,
        max_cpu_percent=80,
        max_requests_per_minute=100,
        max_tokens_per_minute=10000
    ),
    state_provider=my_state_provider,
    health_check_interval_seconds=60,
    additional_options={
        "state_save_interval_seconds": 300,
        "heartbeat_interval_seconds": 10,
    }
)
```

## Extending the Runtime

You can extend the runtime with custom functionality:

1. Implement custom state providers by extending `StateProvider`
2. Create custom health checks by extending `HealthCheck`
3. Build domain-specific runtimes by extending `AgentRuntime`

## Implementation Notes

- The runtime is designed to be async-first, using Python's asyncio
- Thread safety is ensured through appropriate locking mechanisms
- Error handling follows a centralized pattern for consistent recovery behavior 