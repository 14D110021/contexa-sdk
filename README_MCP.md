# MCP Integration

The Contexa SDK provides comprehensive support for the [Model Context Protocol (MCP)](https://github.com/mctlab/model-context-protocol), an open standard for AI models to access external tools, data, and services.

## What is MCP?

MCP (Model Context Protocol) is a standardized protocol that enables AI models and agents to interact with external tools and services in a consistent way. It defines:

- How tools describe their capabilities (function specs)
- How agents make requests to tools
- How tools return structured responses
- Security and authentication mechanisms

## Key MCP Features in Contexa SDK

### Using Remote MCP Tools

Use any MCP-compatible tool with your Contexa agents:

```python
from contexa_sdk.core.tool import RemoteTool
from pydantic import BaseModel

# Define the schema for the tool input
class SearchInput(BaseModel):
    query: str

# Create a remote tool that connects to an MCP endpoint
search_tool = RemoteTool(
    endpoint_url="https://api.example.com/mcp/search",
    name="web_search",
    description="Search the web for information",
    schema=SearchInput
)

# Use it like any other Contexa tool
from contexa_sdk.core.agent import ContexaAgent
from contexa_sdk.core.model import ContexaModel

agent = ContexaAgent(
    name="Research Assistant",
    description="Helps with online research",
    model=ContexaModel(provider="openai", model_id="gpt-4o"),
    tools=[search_tool]
)

# Run the agent
result = await agent.run("Find information about climate change")
```

### Creating MCP-Compatible Tools

Convert your Python functions into MCP-compatible endpoints:

```python
from contexa_sdk.core.tool import ContexaTool
from contexa_sdk.deployment.mcp_server import MCPServer
from pydantic import BaseModel

# Define a tool
class WeatherInput(BaseModel):
    location: str
    unit: str = "celsius"

@ContexaTool.register(
    name="get_weather",
    description="Get current weather for a location"
)
async def get_weather(inp: WeatherInput) -> str:
    # Implementation logic
    return f"The weather in {inp.location} is 22°{inp.unit}"

# Create an MCP server with our tool
server = MCPServer(tools=[get_weather])

# Run the server
await server.start(host="0.0.0.0", port=8000)
```

This exposes an MCP-compatible endpoint at `http://localhost:8000/v1/tools/get_weather`.

### Tool Discovery

Discover available tools on an MCP server:

```python
from contexa_sdk.client.mcp import MCPClient

# Create an MCP client
client = MCPClient(base_url="https://api.example.com/mcp")

# Discover available tools
tools = await client.list_tools()

for tool in tools:
    print(f"Tool: {tool.name}")
    print(f"Description: {tool.description}")
    print(f"Schema: {tool.schema}")
    print("---")
```

### Agent as MCP Server

Expose your entire agent as an MCP-compatible service:

```python
from contexa_sdk.deployment.agent_mcp_server import AgentMCPServer

# Create an MCP server for your agent
server = AgentMCPServer(agent=my_agent)

# Start the server
await server.start(host="0.0.0.0", port=8000)
```

This allows other systems to interact with your agent through the MCP protocol.

## MCP Client

The SDK includes a client for interacting with MCP servers:

```python
from contexa_sdk.client.mcp import MCPClient

# Create an MCP client
client = MCPClient(
    base_url="https://api.example.com/mcp",
    api_key="your-api-key"  # Optional
)

# Call a tool
response = await client.call_tool(
    tool_name="web_search",
    inputs={"query": "latest AI research"}
)

print(response)
```

## MCP Authentication

The SDK supports various authentication methods for MCP:

```python
# API Key Authentication
client = MCPClient(
    base_url="https://api.example.com/mcp",
    api_key="your-api-key"
)

# Bearer Token Authentication
client = MCPClient(
    base_url="https://api.example.com/mcp",
    auth_token="your-bearer-token"
)

# Custom Headers
client = MCPClient(
    base_url="https://api.example.com/mcp",
    headers={"X-Custom-Auth": "value"}
)
```

## OpenAPI Integration

Convert OpenAPI specifications to MCP tools:

```python
from contexa_sdk.tools.openapi import create_mcp_tools_from_openapi

# Create MCP tools from an OpenAPI spec
tools = await create_mcp_tools_from_openapi(
    openapi_url="https://api.example.com/openapi.json",
    base_url="https://api.example.com",
    api_key="your-api-key"  # Optional
)

# Use these tools with an agent
agent = ContexaAgent(
    name="API Assistant",
    description="Helps interact with APIs",
    model=ContexaModel(provider="openai", model_id="gpt-4o"),
    tools=tools
)
```

## MCP Tool Registry

Register and discover MCP tools across your organization:

```python
from contexa_sdk.registry.mcp import MCPToolRegistry

# Create or connect to a registry
registry = MCPToolRegistry(
    url="https://registry.example.com",
    api_key="your-api-key"
)

# Register a tool
await registry.register_tool(
    name="weather_tool",
    description="Get weather information",
    endpoint_url="https://api.example.com/mcp/weather",
    schema=WeatherInput
)

# Discover tools
tools = await registry.search_tools(query="weather")

# Incorporate discovered tools into an agent
agent = ContexaAgent(
    name="Weather Assistant",
    description="Helps with weather queries",
    model=ContexaModel(provider="openai", model_id="gpt-4o"),
    tools=tools
)
```

## MCP Version Compatibility

The SDK supports multiple versions of the MCP protocol:

```python
# Specify MCP version for a server
server = MCPServer(
    tools=[get_weather],
    mcp_version="1.0"
)

# Specify MCP version for a client
client = MCPClient(
    base_url="https://api.example.com/mcp",
    mcp_version="1.0"
)
```

## Examples

For complete examples of MCP integration, see:
- [MCP Agent Example](examples/mcp_agent_example.py)
- [MCP Tool Server Example](examples/mcp_tool_server_example.py)
- [OpenAPI to MCP Example](examples/openapi_to_mcp_example.py) 