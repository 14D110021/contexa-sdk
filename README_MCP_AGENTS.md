# MCP-Compatible Agent System

This document describes the MCP-Compatible Agent System in the Contexa SDK, which provides a standardized approach to agent communication and orchestration inspired by industry standards like IBM's Agent Communication Protocol (ACP) and aligned with Anthropic's Model Context Protocol (MCP) principles.

## Overview

The MCP-Compatible Agent System is a sophisticated framework for enabling interoperable, standardized communication between agents. It provides:

1. Standardized interfaces for agent-to-agent communication
2. Multiple communication patterns (sync, async, streaming)
3. Capability-based agent discovery
4. Agent lifecycle management
5. Seamless interoperability with existing Contexa agents

## Key Components

### MCPAgent

The `MCPAgent` class is the core building block that represents an MCP-compatible agent:

```python
from contexa_sdk.orchestration import MCPAgent, AgentState

agent = MCPAgent(
    agent_id="research-agent",
    name="Research Agent",
    description="Finds information on topics",
    version="1.0.0",
    capabilities=["research", "summarization"],
    accepts_streaming=False,
    produces_streaming=True,
    metadata={"specialty": "information gathering"}
)

# Define execution handler
def execution_handler(content):
    query = content.get("input_data", {}).get("query", "")
    return {"summary": f"Research summary for '{query}'"}

# Set handler and activate agent
agent.set_execution_handler(execution_handler)
agent.set_state(AgentState.ACTIVE)
```

### Agent Registry

The registry allows for dynamic discovery of agents based on their capabilities:

```python
from contexa_sdk.orchestration import registry

# Register the agent
registry.register(agent)

# Find agents by capability
research_agents = registry.find_by_capability("research")

# Get a specific agent
agent = registry.get_agent("research-agent")
```

### MCP Handoffs

The handoff system facilitates task delegation between agents:

```python
from contexa_sdk.orchestration import mcp_handoff

# Synchronous handoff
result = mcp_handoff(
    source_agent=agent1,
    target_agent=agent2,
    task_description="Analyze the research findings",
    input_data={"query": "quantum computing"}
)

# Streaming handoff
stream = mcp_handoff(
    source_agent=agent1,
    target_agent=agent2,
    task_description="Analyze with progress updates",
    input_data={"query": "neural networks"},
    streaming=True
)

# Process streaming updates
async for chunk in stream:
    print(f"Progress: {chunk.get('chunk', {}).get('progress', 0)}")
```

### Compatibility with Existing Agents

Easily adapt existing ContexaAgents to the MCP system:

```python
from contexa_sdk.orchestration import register_contexa_agent

# Convert existing agent
mcp_agent = register_contexa_agent(existing_agent)

# Now use it with MCP handoffs
result = mcp_handoff(
    source_agent=some_mcp_agent,
    target_agent=existing_agent,  # Automatically handles conversion
    task_description="Process data",
    input_data={"data": {...}}
)
```

## Communication Patterns

### Synchronous Request/Response

The simplest pattern is a direct request-response between agents:

```python
response = broker.send_message(message)
```

### Asynchronous Communication

For non-blocking operations:

```python
handoff_future = mcp_handoff(
    source_agent=agent1,
    target_agent=agent2,
    task_description="Long-running task",
    input_data={...},
    async_mode=True
)

# Continue with other work...

# Later, get the result
result = await handoff_future
```

### Streaming Data Flow

For real-time progressive updates:

```python
stream = mcp_handoff(
    source_agent=agent1,
    target_agent=agent2,
    task_description="Task with progress updates",
    input_data={...},
    streaming=True
)

async for chunk in stream:
    update_progress_bar(chunk.get("chunk", {}).get("progress", 0))
    display_partial_insight(chunk.get("chunk", {}).get("partial_insight", ""))
```

## Agent Lifecycle Management

The system supports proper lifecycle management through states:

```python
from contexa_sdk.orchestration import AgentState

# Initialize an agent
agent.set_state(AgentState.INITIALIZING)

# Activate the agent
agent.set_state(AgentState.ACTIVE)

# Mark as degraded (e.g., experiencing issues)
agent.set_state(AgentState.DEGRADED)

# Prepare for shutdown
agent.set_state(AgentState.RETIRING)

# Fully shut down
agent.set_state(AgentState.RETIRED)
```

## Error Handling

The system provides standardized error handling:

```python
try:
    result = mcp_handoff(...)
    if result.get("status") == "failed":
        print(f"Handoff failed: {result.get('error')}")
    else:
        process_success(result.get("result"))
except Exception as e:
    print(f"Exception during handoff: {str(e)}")
```

## Examples

For a complete working example, see [MCP-Compatible Handoffs](examples/mcp_handoff_example.py).

## Advanced Usage

### Adding State Change Callbacks

```python
def on_state_change(old_state, new_state):
    print(f"Agent state changed from {old_state} to {new_state}")
    if new_state == AgentState.DEGRADED:
        alert_monitoring_system()

agent.on_state_change(on_state_change)
```

### Custom Protocol Validation

```python
from pydantic import BaseModel

class ResearchProtocolInput(BaseModel):
    query: str
    max_results: int = 5

# Create protocol spec
protocol_id = "research-protocol-v1"

# Use in handoff
result = mcp_handoff(
    source_agent=agent1,
    target_agent=agent2,
    task_description="Research quantum computing",
    input_data={"query": "recent advances", "max_results": 3},
    protocol_id=protocol_id
)
```

## Integration with Other Frameworks

The MCP-Compatible Agent System is designed to work seamlessly with other agent frameworks, providing a standardized communication layer that can be adapted to different environments. This enables interoperability between agents built on different frameworks, creating a unified ecosystem for agent collaboration. 