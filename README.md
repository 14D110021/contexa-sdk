# Contexa SDK

Contexa SDK is a powerful Python library for building AI agents that can communicate across different frameworks. The SDK provides a unified interface for integrating AI agents from LangChain, CrewAI, OpenAI, and Google Vertex AI.

## Features

- **Framework Agnostic Agents**: Build agents that work across LangChain, CrewAI, OpenAI, and Google AI
- **Agent Handoffs**: Enable agents to pass tasks to other specialized agents with context preservation
- **Multi-Channel Protocol (MCP) Support**: Package agents as MCP-compatible services
- **Comprehensive Observability**: Built-in logging, tracing, and metrics for monitoring agent performance
- **Centralized Resource Registry**: Manage tools, models, and agents through a unified interface

## Installation

```bash
pip install contexa-sdk
```

## Quick Start

```python
from contexa_sdk.core.agent import ContexaAgent
from contexa_sdk.core.model import ContexaModel
from contexa_sdk.core.tool import BaseTool

# Create a model
model = ContexaModel(model_name="gpt-4", provider="openai")

# Create a tool
@BaseTool.register
async def web_search(query: str):
    """Search the web for information."""
    # Implementation
    return {"result": f"Search results for: {query}"}

# Create an agent
agent = ContexaAgent(
    name="Research Agent",
    description="Searches the web for information",
    tools=[web_search],
    model=model
)

# Run the agent
response = await agent.run("What are the latest AI trends?")
```

## Multi-Framework Integration

```python
from contexa_sdk.adapters.langchain import convert_agent_to_langchain
from contexa_sdk.adapters.crewai import convert_agent_to_crewai
from contexa_sdk.adapters.openai import adapt_openai_assistant

# Convert a Contexa agent to a LangChain agent
langchain_agent = await convert_agent_to_langchain(agent)

# Import an OpenAI assistant into Contexa
openai_agent = await adapt_openai_assistant("asst_abc123")
```

## Documentation

For more detailed documentation, see:

- [Agent Handoffs](README_AGENT_HANDOFFS.md)
- [Multi-Framework Integration](README_MULTI_FRAMEWORK.md)
- [Observability](README_OBSERVABILITY.md)
- [MCP Protocol Support](README_MCP.md)

## Examples

The `examples` directory contains detailed examples for various use cases:

- `agent_handoff.py` - Demonstrates agent-to-agent handoffs
- `multi_framework_integration.py` - Shows integration across frameworks
- `observability_example.py` - Illustrates logging and metrics collection

## License

This project is licensed under the MIT License - see the LICENSE file for details. 