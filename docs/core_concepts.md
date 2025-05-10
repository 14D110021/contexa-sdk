# Contexa SDK: Core Concepts

## Introduction

Contexa SDK is a framework-agnostic agent platform that provides a unified interface for building, deploying, and managing AI agents across multiple frameworks. It allows developers to define agents, tools, and models once, and then deploy them across different frameworks like LangChain, CrewAI, OpenAI Agents SDK, and Google GenAI.

## Key Components

### Agents

Agents are the central abstraction in Contexa SDK. An agent is an autonomous entity that:

- Receives inputs (queries, tasks, instructions)
- Uses a model for reasoning
- Employs tools to interact with the external world
- Produces outputs

```python
from contexa_sdk.core.agent import ContexaAgent
from contexa_sdk.core.model import ContexaModel
from contexa_sdk.core.tool import ContexaTool

# Create an agent
agent = ContexaAgent(
    name="CustomerSupportAgent",
    description="Helps customers with their inquiries",
    system_prompt="You are a helpful customer support agent...",
    model=ContexaModel(...),
    tools=[tool1, tool2, ...]
)
```

### Tools

Tools are functions that enable agents to interact with external systems, retrieve information, or perform actions. Each tool has:

- A name and description
- A set of parameters
- Logic for executing the function
- Return type information

```python
from contexa_sdk.core.tool import ContexaTool

# Define a tool as an async function
async def get_weather(location: str, unit: str = "celsius") -> str:
    """Get the current weather for a location"""
    # Implementation
    return f"The weather in {location} is sunny and 25°{unit}"

# Create a Contexa tool
weather_tool = ContexaTool(
    name="get_weather",
    description="Get current weather information",
    function=get_weather
)
```

### Models

Models represent language models that power agents. Contexa SDK supports various model providers:

```python
from contexa_sdk.core.model import ContexaModel

# Create a model configuration
model = ContexaModel(
    model_name="gpt-4o",
    provider="openai",
    temperature=0.7,
    max_tokens=1000
)
```

### Adapters

Adapters convert Contexa objects (agents, tools, models) to objects compatible with specific frameworks:

```python
# Convert a Contexa agent to an OpenAI agent
from contexa_sdk.adapters import openai

openai_agent = openai.agent(my_contexa_agent)
```

## Framework Integrations

Contexa SDK provides adapters for multiple frameworks:

### LangChain

```python
from contexa_sdk.adapters import langchain

# Convert Contexa objects to LangChain
langchain_tool = langchain.tool(my_contexa_tool)
langchain_agent = langchain.agent(my_contexa_agent)
```

### OpenAI Agents SDK

```python
from contexa_sdk.adapters import openai

# Convert Contexa objects to OpenAI Agents SDK
openai_tool = openai.tool(my_contexa_tool)
openai_agent = openai.agent(my_contexa_agent)
```

### CrewAI

```python
from contexa_sdk.adapters import crewai

# Convert Contexa objects to CrewAI
crewai_tool = crewai.tool(my_contexa_tool)
crewai_agent = crewai.agent(my_contexa_agent)
```

### Google GenAI

```python
from contexa_sdk.adapters import google

# Convert Contexa objects to Google GenAI
google_tool = google.tool(my_contexa_tool)
google_model = google.model(my_contexa_model)
```

## Runtime Environments

Contexa SDK supports different runtime environments for agent execution:

### Local Runtime

Run agents locally with process isolation:

```python
from contexa_sdk.runtime import LocalRuntime

runtime = LocalRuntime()
result = runtime.run_agent(agent, "What's the weather in Tokyo?")
```

### Cluster Runtime

Run agents in a distributed environment:

```python
from contexa_sdk.runtime import ClusterRuntime

runtime = ClusterRuntime(
    connection_string="redis://localhost:6379",
    worker_count=4
)
result = runtime.run_agent(agent, "What's the weather in Tokyo?")
```

## Observability

Contexa SDK provides comprehensive observability:

### Tracing

```python
from contexa_sdk.observability import Tracer

tracer = Tracer()
with tracer.start_span("agent_execution"):
    result = agent.run("What's the weather in Tokyo?")
```

### Metrics

```python
from contexa_sdk.observability import MetricsCollector

metrics = MetricsCollector()
metrics.record_latency("agent_execution", 120)  # 120ms
metrics.increment_counter("tool_calls", 1)
```

### Logging

```python
from contexa_sdk.observability import Logger

logger = Logger()
logger.info("Agent started execution")
logger.error("Tool execution failed", exc_info=True)
```

## Deployment

Contexa SDK supports various deployment options:

### Model Context Protocol (MCP)

Deploy agents as standardized MCP servers:

```python
from contexa_sdk.deployment import MCPGenerator

generator = MCPGenerator()
mcp_server_code = generator.generate(agent)
```

### Containerization

Package agents in containers for easy deployment:

```python
from contexa_sdk.deployment import Deployer

deployer = Deployer()
deployer.build_container(agent, "my-agent:latest")
deployer.deploy_to_kubernetes("my-agent:latest", replicas=3)
```

## Installation

Install the SDK with optional dependencies based on your framework needs:

```bash
# Core SDK
pip install contexa-sdk

# With framework support
pip install contexa-sdk[langchain]  # For LangChain support
pip install contexa-sdk[crewai]     # For CrewAI support
pip install contexa-sdk[openai]     # For OpenAI Agents SDK support
pip install contexa-sdk[google]     # For Google GenAI support

# All frameworks
pip install contexa-sdk[all]
``` 