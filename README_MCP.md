# MCP Integration with Contexa SDK

This document describes how to use the Multi-Channel Protocol (MCP) integration features of the Contexa SDK. The Contexa SDK allows you to create and use agents that can communicate using the MCP protocol, enabling seamless integration with other MCP-compatible systems.

## Overview

The Contexa SDK provides full MCP support for agent-to-agent communication, allowing you to:

1. **Build MCP-compatible agent servers** - Package your Contexa agents as standalone servers following the MCP protocol
2. **Use remote MCP agents** - Connect to and interact with remote agents via the MCP protocol
3. **Register in MCP registries** - Make your agents discoverable through MCP registries
4. **Perform agent handoffs** - Transfer tasks between local and remote agents while preserving context

## Creating an MCP-compatible Agent Server

To create an MCP-compatible agent server, you can use the `build_agent` function with the `mcp_compatible` parameter set to `True`:

```python
from contexa_sdk.core import ContexaAgent
from contexa_sdk.deployment import build_agent, deploy_agent

# Create your agent
agent = ContexaAgent(...)

# Build the agent as an MCP-compatible server
agent_path = build_agent(
    agent=agent,
    output_dir="./build",
    version="0.1.0",
    mcp_compatible=True,  # Enable MCP compatibility
    mcp_version="1.0"     # Specify the MCP version to use
)

# Deploy the agent
deployment = deploy_agent(
    agent_path=agent_path,
    register_as_mcp=True  # Register in the MCP registry
)

# The agent is now available at the endpoint URL
print(f"MCP Agent endpoint: {deployment['endpoint_url']}")
```

## Using a Remote MCP Agent

To use a remote MCP agent, you can use the `RemoteAgent` class:

```python
import asyncio
from contexa_sdk.core import RemoteAgent

async def main():
    # Create a RemoteAgent from an endpoint URL
    agent = await RemoteAgent.from_endpoint("https://api.example.com/v0/mcp/my-agent")
    
    # Use the agent as if it were a local agent
    response = await agent.run("What's the weather like in San Francisco?")
    print(response)
    
    # You can also use the agent's tools
    # The tools are automatically discovered from the remote agent

if __name__ == "__main__":
    asyncio.run(main())
```

## Agent Handoffs

You can perform handoffs between local and remote agents:

```python
import asyncio
from contexa_sdk.core import ContexaAgent, RemoteAgent

async def main():
    # Create or load a local agent
    local_agent = ContexaAgent(...)
    
    # Create a remote agent
    remote_agent = await RemoteAgent.from_endpoint("https://api.example.com/v0/mcp/another-agent")
    
    # Perform a task with the local agent
    local_result = await local_agent.run("Find information about electric cars")
    
    # Hand off to the remote agent
    remote_result = await local_agent.handoff_to(
        target_agent=remote_agent,
        query="Based on that information, what are the best electric cars for families?",
        include_history=True  # Include the conversation history
    )
    
    print(remote_result)

if __name__ == "__main__":
    asyncio.run(main())
```

## MCP Registry Integration

The Contexa SDK supports registering your agents in MCP registries, making them discoverable by other systems:

```python
from contexa_sdk.deployment import list_mcp_agents

# List all MCP agents in your account
agents = list_mcp_agents()
for agent in agents:
    print(f"Agent: {agent['endpoint_id']}")
    print(f"URL: {agent['endpoint_url']}")
    print(f"MCP Version: {agent.get('mcp_version', '1.0')}")
    print()
```

## Full Example

See the `examples/mcp_agent_example.py` file for a complete working example of MCP integration with the Contexa SDK.

## Technical Details

### MCP Protocol Version

The Contexa SDK currently supports MCP version 1.0.

### MCP Endpoints

MCP-compatible agents expose the following endpoints:

- `/mcp/run` - Run the agent with a query
- `/mcp/handoff` - Receive a handoff from another agent
- `/mcp/tools` - Get the list of tools available to the agent
- `/mcp/metadata` - Get metadata about the agent

### OpenAPI Specification

Each MCP-compatible agent includes an OpenAPI specification at `/openapi.json` that documents the agent's capabilities and endpoints, with MCP-specific extensions.

## Future Enhancements

We plan to enhance the MCP integration in future releases with:

1. **MCP Tool Discovery** - Automatically discover and use tools from remote MCP agents
2. **Enhanced Registry Integration** - Improved integration with MCP registries
3. **Agent Orchestration** - Built-in support for orchestrating multiple MCP agents
4. **Authentication** - Enhanced authentication mechanisms for MCP endpoints 