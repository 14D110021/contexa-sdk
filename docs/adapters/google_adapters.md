# Google Adapters for Contexa SDK

Contexa SDK provides two different Google adapters for integrating with Google's AI technologies:

1. **Google GenAI Adapter** - For working with Google's Generative AI SDK (Palm/Gemini)
2. **Google ADK Adapter** - For working with Google's Agent Development Kit (ADK)

## Installation Requirements

### Google GenAI Adapter

To use the Google GenAI adapter, you need to install the `google-generativeai` package:

```bash
pip install "contexa-sdk[google-genai]"
```

Or directly:

```bash
pip install google-generativeai
```

### Google ADK Adapter

To use the Google ADK adapter, you need to install the `google-adk` package:

```bash
pip install "contexa-sdk[google-adk]"
```

Or directly:

```bash
pip install google-adk
```

## Usage Examples

The adapters are accessed through the `contexa_sdk.adapters.google` module, which provides namespaced functions for each adapter type.

### Google GenAI Adapter

The GenAI adapter provides access to Google's Generative AI models (formerly PaLM, now Gemini):

```python
from contexa_sdk.adapters.google import genai_model, genai_tool, genai_agent, genai_handoff
from contexa_sdk.core.model import ContexaModel
from contexa_sdk.core.tool import ContexaTool
from contexa_sdk.core.agent import ContexaAgent

# Create a Contexa model
model = ContexaModel(
    provider="google",
    model_name="gemini-pro",
    config={"api_key": "your-api-key"}  # Optional, can use environment variables
)

# Convert to a Google GenAI model
google_model = genai_model(model)

# Define a tool
@ContexaTool.register(
    name="weather_tool",
    description="Get the weather for a location"
)
async def get_weather(location: str) -> str:
    return f"The weather in {location} is sunny."

# Convert to a Google GenAI tool
google_tool = genai_tool(get_weather)

# Create an agent with the model and tool
agent = ContexaAgent(
    name="Weather Assistant",
    description="An assistant that provides weather information",
    model=model,
    tools=[get_weather]
)

# Convert to a Google GenAI agent
google_agent = genai_agent(agent)

# Run the agent
result = await google_agent.run("What's the weather in New York?")
print(result)
```

### Google ADK Adapter

The ADK adapter provides access to Google's Agent Development Kit, a framework for building sophisticated AI agents:

```python
from contexa_sdk.adapters.google import adk_model, adk_tool, adk_agent, adk_handoff
from contexa_sdk.core.model import ContexaModel
from contexa_sdk.core.tool import ContexaTool
from contexa_sdk.core.agent import ContexaAgent

# Create a Contexa model
model = ContexaModel(
    provider="google",
    model_name="gemini-2.0-pro",  # ADK uses different model names
)

# Convert to an ADK model
adk_model_name = adk_model(model)

# Define a tool
@ContexaTool.register(
    name="search_tool",
    description="Search for information"
)
async def search(query: str) -> str:
    return f"Search results for {query}"

# Convert to an ADK tool
adk_search_tool = adk_tool(search)

# Create an agent with the model and tool
agent = ContexaAgent(
    name="Research Assistant",
    description="An assistant that performs research",
    model=model,
    tools=[search],
    system_prompt="You are a research assistant that helps find information."
)

# Convert to an ADK agent
research_agent = adk_agent(agent)

# Run the agent
result = await research_agent.run("Find information about climate change")
print(result)
```

### Cross-Framework Handoffs

You can perform handoffs between agents built with different frameworks:

```python
from contexa_sdk.runtime.handoff import handoff

# Perform a handoff from a GenAI agent to an ADK agent
result = await handoff(
    from_agent=genai_agent_instance,
    to_agent=adk_agent_instance,
    message="Continue researching this topic: climate change",
    context={"previous_findings": "Initial data about rising sea levels"}
)
```

## Default Functions

For backward compatibility, the module also exports default functions that use the Google GenAI adapter:

```python
from contexa_sdk.adapters.google import tool, model, agent, handoff
```

## Function Reference

### Google GenAI Functions

| Function | Description |
|----------|-------------|
| `genai_tool(tool)` | Converts a Contexa tool to a Google GenAI tool function |
| `genai_model(model)` | Converts a Contexa model to a Google GenAI model |
| `genai_agent(agent)` | Converts a Contexa agent to a Google GenAI agent wrapper |
| `genai_prompt(prompt)` | Converts a Contexa prompt to a format usable by Google GenAI |
| `genai_handoff(source_agent, target_agent, query, context, metadata)` | Handles handoff between a Contexa agent and a Google GenAI agent |

### Google ADK Functions

| Function | Description |
|----------|-------------|
| `adk_tool(tool)` | Converts a Contexa tool to a Google ADK tool |
| `adk_model(model)` | Converts a Contexa model to a Google ADK model name |
| `adk_agent(agent)` | Converts a Contexa agent to a Google ADK agent |
| `adk_prompt(prompt)` | Converts a Contexa prompt to a format usable by Google ADK |
| `adk_handoff(source_agent, target_agent, query, context, metadata)` | Handles handoff between a Contexa agent and a Google ADK agent | 