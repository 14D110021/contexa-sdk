# Contexa SDK

**Contexa SDK** is a comprehensive framework for standardizing AI agent development, deployment, and interoperability across multiple frameworks. It provides a unified layer that enables agent components (tools, models, prompts, etc.) to be seamlessly converted between different agent frameworks like LangChain, CrewAI, OpenAI Agent SDK, and Google ADK.

## Mission

At Contexa, we're building a standardized "context layer" for AI agents. Our SDK allows any AI agent to easily access external tools, APIs, and data through a universal protocol (the open Model Context Protocol, or MCP). By standardizing the agent layer one component at a time, we enable:

- **Write Once, Run Anywhere**: Define your tools, models, and agents once and use them across any supported framework
- **Seamless Deployment**: Package and deploy your agents to versioned endpoints with a single command
- **Framework Interoperability**: Enable cross-framework agent handoffs and collaboration
- **Observability**: Monitor and trace agent activities with structured logging and metrics

## Core Features

### Unified Core Objects

- **Tools**: Define tools once and use them in any framework
- **Models**: Wrap any LLM/chat API with a consistent interface
- **Agents**: Build framework-agnostic agent definitions
- **Prompts**: Create reusable prompt templates

### Multi-Framework Adapters

Convert Contexa objects to native framework objects for:
- LangChain (≥0.1)
- CrewAI (≥0.110)
- OpenAI Agents SDK (≥0.4)
- Google ADK (≥0.3)

### Agent Runtime

- **Lifecycle Management**: Control agent startup, execution, and shutdown
- **State Persistence**: Save and restore agent state for resilience
- **Resource Tracking**: Monitor and limit resource usage
- **Health Monitoring**: Detect and recover from failures

### Observability

- **Structured Logging**: Track agent operations in detail
- **Metrics Collection**: Monitor performance and usage metrics
- **Tracing**: Follow request flows through multiple agents
- **OpenTelemetry Compatible**: Integrate with existing observability stacks

### MCP Integration

- **MCP Protocol Support**: Build and consume Model Context Protocol compatible services
- **Agent-as-MCP-Server**: Expose agents as MCP-compatible endpoints
- **Remote Agent Integration**: Invoke remote agents via the MCP protocol

## Installation

```bash
# Install core SDK
pip install contexa-sdk

# Install with specific framework support
pip install contexa-sdk[langchain]  # For LangChain support
pip install contexa-sdk[crewai]     # For CrewAI support
pip install contexa-sdk[openai]     # For OpenAI Agents SDK support
pip install contexa-sdk[google-adk] # For Google ADK support

# Install with all framework support
pip install contexa-sdk[all]
```

## Quick Start

### 1. Define a Tool

```python
from contexa_sdk.core.tool import ContexaTool
from pydantic import BaseModel

class SearchInput(BaseModel):
    query: str

@ContexaTool.register(
    name="web_search",
    description="Search the web and return text snippet"
)
async def web_search(inp: SearchInput) -> str:
    return f"Top hit for {inp.query}"
```

### 2. Create an Agent

```python
from contexa_sdk.core.agent import ContexaAgent
from contexa_sdk.core.model import ContexaModel

# Create an agent with our tool
agent = ContexaAgent(
    name="My Assistant",
    description="A helpful assistant",
    model=ContexaModel(provider="openai", model_id="gpt-4o"),
    tools=[web_search]
)
```

### 3. Use with Different Frameworks

```python
# LangChain
from contexa_sdk.adapters import langchain
lc_agent = langchain.agent(agent)
result = await lc_agent.invoke("What's new in AI?")

# CrewAI
from contexa_sdk.adapters import crewai
crew_agent = crewai.agent(agent)
result = await crew_agent.run("What's new in AI?")

# OpenAI
from contexa_sdk.adapters import openai
oa_agent = openai.agent(agent)
result = await oa_agent.execute("What's new in AI?")
```

### 4. Deploy Your Agent

```bash
# Build and deploy your agent
ctx build
ctx deploy

# Output: https://api.contexa.ai/v0/ctx/my-org/my-agent:8f3ad1
```

## Documentation

For more detailed documentation, see the following guides:

- [Core Concepts](docs/core_concepts.md)
- [Multi-Framework Integration](README_MULTI_FRAMEWORK.md)
- [Agent Runtime](README_RUNTIME.md)
- [Observability](README_OBSERVABILITY.md)
- [MCP Integration](README_MCP.md)

## Examples

The `examples/` directory contains various examples demonstrating different features:

- [Basic Agent Usage](examples/search_agent.py)
- [Multi-Framework Integration](examples/multi_framework_integration.py)
- [Agent Handoff](examples/agent_handoff.py)
- [Runtime Management](examples/runtime_example.py)
- [Cluster Runtime](examples/cluster_runtime_example.py)
- [Observability Setup](examples/observability_example.py)
- [MCP Integration](examples/mcp_agent_example.py)

### Advanced AI Agent Examples

We've included several complex AI agent examples that demonstrate the full capabilities of Contexa SDK across multiple frameworks:

- [Financial Analysis Agent (LangChain)](examples/financial_analysis_agent.py): A financial analysis agent that extracts data from PDF reports, calculates financial metrics, creates visualizations, and provides analysis.

- [Content Creation Pipeline (CrewAI)](examples/content_creation_crew.py): A multi-agent workflow for content creation including research, writing, editing, and SEO optimization, orchestrated using CrewAI.

- [Customer Support Agent (OpenAI)](examples/customer_support_agent.py): A comprehensive customer support agent that integrates with knowledge bases, ticket systems, and order tracking using OpenAI function calling.

These examples showcase:
- Framework-specific adaptations
- Advanced tool usage
- Multi-agent coordination
- Complex system integrations
- Real-world use cases

## Contributing

Contributions are welcome! Please see our [Contributing Guide](CONTRIBUTING.md) for more information.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details. 