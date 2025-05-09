# Agent Runtime

The Contexa Agent Runtime provides a robust infrastructure for managing the entire lifecycle of AI agents. It handles agent execution, state management, resource allocation, health monitoring, and recovery - enabling reliable and scalable agent deployments.

## Key Features

- **Lifecycle Management**: Control agent startup, execution, and shutdown
- **State Persistence**: Save and restore agent state for resilience  
- **Resource Tracking**: Monitor and limit resource usage
- **Health Monitoring**: Detect and recover from failures
- **Scaling**: Run agents across distributed environments
- **Event Bus**: Enable inter-agent communication

## Architecture

The agent runtime consists of several key components:

1. **Runtime Manager**: Coordinates agent execution and lifecycle events
2. **State Manager**: Handles agent state persistence and recovery
3. **Resource Manager**: Monitors and controls resource utilization
4. **Health Monitor**: Tracks agent health and triggers recovery actions
5. **Event Bus**: Facilitates communication between agents
6. **Cluster Manager**: Coordinates agent execution across multiple nodes

```
┌───────────────────────────────────────┐
│           Runtime Manager             │
├───────────┬───────────┬───────────────┤
│  State    │ Resource  │   Health      │
│  Manager  │ Manager   │   Monitor     │
├───────────┴───────────┴───────────────┤
│              Event Bus                │
├───────────────────────────────────────┤
│           Cluster Manager             │
└───────────────────────────────────────┘
```

## Basic Usage

### Single Agent Runtime

```python
from contexa_sdk.runtime.manager import RuntimeManager
from contexa_sdk.core.agent import ContexaAgent

# Create an agent
agent = ContexaAgent(
    name="Assistant",
    description="A helpful assistant",
    model=ContexaModel(provider="openai", model_id="gpt-4o"),
    tools=[web_search]
)

# Initialize runtime manager
runtime = RuntimeManager()

# Register agent with the runtime
agent_id = await runtime.register_agent(agent)

# Start the agent
await runtime.start_agent(agent_id)

# Run the agent
result = await runtime.run_agent(
    agent_id, 
    input="What are the latest AI advancements?"
)

# Stop the agent
await runtime.stop_agent(agent_id)
```

### Persistent State

The runtime can persist agent state, allowing agents to be stopped and resumed:

```python
# Save state
state_id = await runtime.save_state(agent_id)

# Stop agent
await runtime.stop_agent(agent_id)

# Later, restore the agent with its state
new_agent_id = await runtime.restore_agent(state_id)

# Continue the conversation
result = await runtime.run_agent(
    new_agent_id, 
    input="Tell me more about that last topic"
)
```

### Resource Management

Control and monitor resource usage:

```python
# Configure resource limits
from contexa_sdk.runtime.resources import ResourceLimits

limits = ResourceLimits(
    max_memory_mb=1024,
    max_tokens_per_minute=10000,
    max_concurrent_requests=5
)

# Register agent with resource limits
agent_id = await runtime.register_agent(agent, resource_limits=limits)

# Get current resource usage
usage = await runtime.get_resource_usage(agent_id)
print(f"Memory usage: {usage.memory_mb}MB")
print(f"Token usage: {usage.tokens_used_last_minute}/min")
```

## Event Bus

The event bus enables communication between agents:

```python
from contexa_sdk.runtime.events import EventBus, Event

# Create an event bus
event_bus = EventBus()

# Register event handlers
async def handle_search_event(event):
    query = event.data["query"]
    # Perform search
    result = await search_function(query)
    # Publish results
    await event_bus.publish(Event(
        type="search_result",
        data={"query": query, "result": result}
    ))

# Subscribe to events
await event_bus.subscribe("search_request", handle_search_event)

# Publish an event
await event_bus.publish(Event(
    type="search_request",
    data={"query": "latest AI research"}
))
```

## Distributed Runtime

For scaling across multiple nodes:

```python
from contexa_sdk.runtime.cluster import ClusterManager

# Initialize cluster manager
cluster = ClusterManager(
    discovery_url="redis://localhost:6379",
    node_id="node-1"
)

# Register with the cluster
await cluster.register()

# Start agent on the most available node
agent_id = await cluster.start_agent(agent)

# Run agent (automatically routes to the right node)
result = await cluster.run_agent(
    agent_id, 
    input="What's the weather today?"
)
```

## Health Monitoring

Monitor agent health and implement recovery:

```python
from contexa_sdk.runtime.health import HealthMonitor

# Create health monitor
health = HealthMonitor()

# Register health checks
async def check_model_availability():
    try:
        response = await model.generate("test")
        return True
    except Exception:
        return False

health.register_check("model_availability", check_model_availability)

# Configure auto-recovery
async def recover_model():
    # Implement recovery logic
    pass

health.register_recovery("model_availability", recover_model)

# Start health monitoring for an agent
await health.monitor_agent(agent_id, interval_seconds=60)
```

## Deployment

Deploy agents as standalone services:

```python
from contexa_sdk.deployment.service import AgentService

# Create a service from an agent
service = AgentService(agent)

# Start the service
await service.start(port=8000)
```

This exposes HTTP endpoints:
- `POST /run` - Run the agent
- `GET /health` - Check agent health
- `GET /status` - Get agent status

## Examples

For complete examples of the runtime system, see:
- [Basic Runtime Example](examples/runtime_example.py)
- [Cluster Runtime Example](examples/cluster_runtime_example.py)
- [MCP Agent Example](examples/mcp_agent_example.py) 