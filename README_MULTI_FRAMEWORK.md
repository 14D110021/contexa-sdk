# Multi-Framework Integration in Contexa SDK

The Contexa SDK provides powerful capabilities for integrating AI agents across multiple frameworks, enabling you to build complex AI workflows that leverage the strengths of different ecosystems.

## Key Features

- **Framework Adapters**: Convert between Contexa and popular frameworks including LangChain, CrewAI, OpenAI, and Google Vertex AI
- **Bidirectional Conversion**: Both export Contexa agents to other frameworks and import external agents into Contexa
- **Context Preservation**: Maintain conversation history and context when switching between frameworks
- **Centralized Registry**: Use a unified interface to manage tools, models, and agents across frameworks
- **MCP Protocol Support**: Package agents as MCP servers for standard communication

## Supported Frameworks

| Framework | Import to Contexa | Export from Contexa |
|-----------|-------------------|---------------------|
| LangChain | ✅                | ✅                  |
| CrewAI    | ✅                | ✅                  |
| OpenAI    | ✅                | ✅                  |
| Google AI | ✅                | ✅                  |

## Using the Framework Adapters

### Converting a Contexa Agent to a Framework

```python
from contexa_sdk.adapters.langchain import convert_agent_to_langchain

# Create a Contexa agent
contexa_agent = ContexaAgent(
    name="Research Agent",
    description="Searches the web for information",
    tools=[web_search_tool],
    model=gpt4_model
)

# Convert to LangChain
langchain_agent = await convert_agent_to_langchain(contexa_agent)

# Use with LangChain's ecosystem
from langchain.agents import AgentExecutor
executor = AgentExecutor.from_agent_and_tools(
    agent=langchain_agent,
    tools=langchain_tools
)
```

### Importing a Framework Agent to Contexa

```python
from contexa_sdk.adapters.openai import adapt_openai_assistant

# Create a RemoteAgent that wraps an OpenAI Assistant
openai_assistant_id = "asst_abc123"
contexa_agent = await adapt_openai_assistant(openai_assistant_id)

# Use like any other Contexa agent
result = await contexa_agent.run("What are the latest trends in AI?")
```

## Multi-Framework Workflow Example

The SDK enables you to build workflows that span multiple frameworks, as demonstrated in the `multi_framework_integration.py` example:

```python
# Initial task for the research agent (LangChain)
research_result = await langchain_agent.run(initial_query)

# Hand off to analysis agent (CrewAI)
analysis_result = await crewai_agent.run(f"Analyze this data: {research_result}")

# Hand off to generation agent (OpenAI)
generation_result = await openai_agent.run(f"Generate content based on: {analysis_result}")

# Hand off to summary agent (Google AI)
summary_result = await google_agent.run(f"Summarize: {generation_result}")
```

## Resource Registry

The Contexa SDK provides a centralized registry for managing components across frameworks:

```python
from contexa_sdk.client import tools, models, agents

# Register tools, models, and agents
tools.register("web_search", my_search_tool)
models.register("gpt-4", my_gpt4_model)
agents.register("research_agent", my_research_agent)

# Retrieve them anywhere in your application
search_tool = tools.get("web_search")
gpt4_model = models.get("gpt-4")
research_agent = agents.get("research_agent")
```

## MCP Protocol Support

The SDK can package agents as Multi-Channel Protocol (MCP) servers:

```python
from contexa_sdk.deployment import build_mcp_agent_server

# Build an MCP-compatible agent server
artifact_path = build_mcp_agent_server(
    agent=my_agent,
    output_dir="./deployment",
    mcp_version="1.0"
)
```

This enables standardized communication between agents across different platforms and providers.

## Getting Started

To start using the multi-framework integration capabilities:

1. Install the Contexa SDK: `pip install contexa-sdk`
2. Install the frameworks you want to integrate with: `pip install langchain crewai openai google-cloud-aiplatform`
3. Import the appropriate adapters: `from contexa_sdk.adapters.langchain import ...`
4. See the examples directory for complete demonstrations

## Additional Documentation

- [Agent Handoffs](./README_AGENT_HANDOFFS.md)
- [Observability](./README_OBSERVABILITY.md)
- [MCP Protocol](./README_MCP.md) 