# Contexa SDK
[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Version](https://img.shields.io/badge/version-0.1.0-green)](https://github.com/rupeshrajdev/contexa_sdk)

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
- LangChain (≥0.1.0)
- CrewAI (≥0.110.0)
- OpenAI Agents SDK (≥1.2.0)
- Google GenAI (≥0.3.0) - For simple Gemini model integrations
- Google ADK (≥0.5.0) - For advanced agent capabilities

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
- **Agent Visualization**: Generate interactive graphs of agent relationships, tools, and handoffs

### MCP Integration

- **MCP Protocol Support**: Build and consume Model Context Protocol compatible services
- **Agent-as-MCP-Server**: Expose agents as MCP-compatible endpoints
- **Remote Agent Integration**: Invoke remote agents via the MCP protocol

### NEW! Agent Orchestration

Our new orchestration module enables sophisticated multi-agent collaboration:

- **Agent Teams**: Organize agents into teams with defined roles and responsibilities
- **Structured Communication**: Direct message passing between agents with typed content
- **Task Handoffs**: Formal delegation of tasks between agents with validation
- **Shared Workspaces**: Collaborative environments for sharing artifacts with versioning
- **MCP-Compatible Agents**: Standardized agent interfaces based on the Model Context Protocol (MCP)
- **Capability-Based Discovery**: Find agents by their capabilities rather than identifiers
- **Streaming Handoffs**: Real-time progressive updates during long-running tasks
- **Unified Message Envelopes**: Structured communication format for all agent interactions

## Installation

```bash
# Install core SDK only
pip install contexa-sdk

# Install with specific framework support
pip install contexa-sdk[langchain]    # For LangChain support
pip install contexa-sdk[crewai]       # For CrewAI support
pip install contexa-sdk[openai]       # For OpenAI Agents SDK support
pip install contexa-sdk[viz]          # For agent visualization support

# Install with all framework support
pip install contexa-sdk[all]
```

### Google Adapter Installation

Contexa SDK provides Google GenAI integration for Gemini models:

```bash
# For Google GenAI (Gemini) support
pip install contexa-sdk[google-genai]

# Alternative installation
pip install contexa-sdk[google]
```

#### Google GenAI Adapter

**Google GenAI** (`google-genai`): 
- Direct integration with Google's Generative AI SDK
- Access to Gemini models (gemini-pro, gemini-pro-vision)
- Streamlined for question-answering and function-calling
- Lightweight dependency footprint: only requires `google-generativeai>=0.3.0`

Each adapter can be imported separately with specific prefixes:

```python
# Direct GenAI adapter imports
from contexa_sdk.adapters.google import (
    genai_tool, genai_model, genai_agent, genai_handoff
)

# Direct ADK adapter imports
from contexa_sdk.adapters.google import (
    adk_tool, adk_model, adk_agent, adk_handoff
)
```

For detailed migration guidance from the old Google adapter structure, see our [Google Adapter Migration Guide](docs/google_adapter_migration.md) and [Google Adapters Documentation](docs/google_adapters.md).

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

# Google GenAI (for simple Gemini model integration)
from contexa_sdk.adapters.google import genai_agent
genai_assistant = genai_agent(agent)
result = await genai_assistant.run("What's new in AI?")

# Google ADK (for advanced agent capabilities)
from contexa_sdk.adapters.google import adk_agent
adk_assistant = adk_agent(agent)
result = await adk_assistant.run("What's new in AI?")
```

### 4. Cross-Framework Integration

You can easily create workflows that combine agents from different frameworks:

```python
from contexa_sdk.runtime.handoff import handoff

# Create a GenAI agent for research
research_agent = genai_agent(ContexaAgent(
    name="Researcher",
    model=ContexaModel(provider="google", model_id="gemini-pro"),
    tools=[web_search]
))

# Create an ADK agent for analysis 
analysis_agent = adk_agent(ContexaAgent(
    name="Analyst",
    model=ContexaModel(provider="google", model_id="gemini-pro"),
    tools=[analysis_tool]
))

# Create a LangChain agent for report formatting
report_agent = langchain.agent(ContexaAgent(
    name="Reporter",
    model=ContexaModel(provider="openai", model_id="gpt-4o"),
    tools=[formatting_tool]
))

# Execute a multi-framework workflow
research_result = await research_agent.run("Research quantum computing advances")
analysis_result = await handoff(
    from_agent=research_agent,
    to_agent=analysis_agent,
    message=f"Analyze these findings: {research_result}"
)
final_report = await handoff(
    from_agent=analysis_agent,
    to_agent=report_agent,
    message=f"Format this analysis as a markdown report: {analysis_result}"
)
```

### 5. Using the New Orchestration Features

```python
from contexa_sdk.orchestration import AgentTeam, Message, Channel, TaskHandoff, SharedWorkspace

# Create a team of agents
research_team = AgentTeam(
    name="Research Team",
    expertise=["quantum computing", "medical research"]
)

# Add agents to the team
research_team.add_agent(researcher_agent, role="lead")
research_team.add_agent(assistant_researcher, role="specialist")
research_team.add_agent(validation_agent, role="validator")

# Set up communication channel
team_channel = Channel(name="research_channel")

# Send a message between agents
message = Message(
    sender_id="researcher_agent",
    recipient_id="validation_agent", 
    content="Please validate these findings",
    message_type="request"
)
team_channel.send(message)

# Create a shared workspace for collaboration
workspace = SharedWorkspace(name="Research Project")

# Add a document to the workspace
doc_id = workspace.add_artifact(
    name="Research Findings",
    content={"topic": "Quantum Computing", "findings": [...]},
    creator_id="researcher_agent"
)

# Execute a task handoff
handoff = TaskHandoff(
    sender=researcher_agent,
    recipient=validation_agent,
    task_description="Validate research findings",
    input_data={"doc_id": doc_id}
)
result = handoff.execute()
```

### 6. Deploy Your Agent

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
- [Agent Orchestration](docs/orchestration.md)
- [MCP-Compatible Agents](README_MCP_AGENTS.md)
- [New Developer Onboarding](ONBOARDING.md)
- [Framework Compatibility](FRAMEWORK_COMPATIBILITY.md)
- [Google Adapter Migration Guide](docs/google_adapter_migration.md)

## Examples

The `examples/` directory contains various examples demonstrating different features:

- [Basic Agent Usage](examples/search_agent.py)
- [Multi-Framework Integration](examples/multi_framework_integration.py)
- [Agent Handoff](examples/agent_handoff.py)
- [Runtime Management](examples/runtime_example.py)
- [Cluster Runtime](examples/cluster_runtime_example.py)
- [Observability Setup](examples/observability_example.py)
- [MCP Integration](examples/mcp_agent_example.py)
- [Orchestration Example](examples/orchestration_example.py)
- [Agent Visualization](examples/agent_visualization.py)
- [MCP-Compatible Handoffs](examples/mcp_handoff_example.py)
- [Google Adapter Comparison](examples/google_adapter_comparison.py)
- [Google Adapter Migration](examples/google_adapter_migration_example.py)

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