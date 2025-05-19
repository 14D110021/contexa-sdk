# Google Adapters for Contexa SDK

This document explains the two different Google adapters available in the Contexa SDK and how to use them effectively.

## Overview

Contexa SDK supports two different Google AI technologies:

1. **Google Generative AI SDK** (GenAI) - For working with Gemini models directly
2. **Google Agent Development Kit** (ADK) - For building agents using Google's ADK framework

Each technology has a dedicated adapter in the SDK that provides specialized functionality.

## Installation

```bash
# Install GenAI support
pip install contexa-sdk[google-genai]

# Install ADK support
pip install contexa-sdk[google-adk]

# Install both
pip install contexa-sdk[google]
```

## Google Generative AI SDK Adapter

The GenAI adapter (`contexa_sdk.adapters.google.genai`) allows you to convert Contexa objects to work with the Google Generative AI SDK (Gemini models).

### When to Use

- When you want to interact directly with Gemini models
- When you need to use advanced Gemini features like streaming
- When you have existing Contexa tools that you want to use with Gemini
- When you need a lighter-weight solution without the full ADK

### Example Usage

```python
from contexa_sdk.core.tool import ContexaTool
from contexa_sdk.core.model import ContexaModel
from contexa_sdk.core.agent import ContexaAgent
from pydantic import BaseModel

# Define a tool
class SearchInput(BaseModel):
    query: str

@ContexaTool.register(
    name="web_search",
    description="Search the web for information"
)
async def web_search(inp: SearchInput) -> str:
    return f"Results for '{inp.query}'"

# Create a model and agent
model = ContexaModel(provider="google", model_name="gemini-pro")
agent = ContexaAgent(
    name="Research Assistant",
    description="Helps with online research",
    model=model,
    tools=[web_search]
)

# Convert to Google GenAI
from contexa_sdk.adapters.google import genai_agent, genai_tool, genai_model

# Convert individual components
google_tool = genai_tool(web_search)
google_model = genai_model(model)

# Or convert the entire agent
google_agent = genai_agent(agent)

# Run the agent
result = await google_agent.run("Research quantum computing")
```

## Google Agent Development Kit Adapter

The ADK adapter (`contexa_sdk.adapters.google.adk`) allows you to convert Contexa objects to work with the Google Agent Development Kit.

### When to Use

- When you're building agents that need to integrate with Google's ADK ecosystem
- When you need advanced agent capabilities provided by the ADK
- When you're building Google Agent Builder applications
- When you need the full power of Google's agent platform

### Example Usage

```python
from contexa_sdk.core.tool import ContexaTool
from contexa_sdk.core.model import ContexaModel
from contexa_sdk.core.agent import ContexaAgent
from pydantic import BaseModel

# Define a tool
class SearchInput(BaseModel):
    query: str

@ContexaTool.register(
    name="web_search",
    description="Search the web for information"
)
async def web_search(inp: SearchInput) -> str:
    return f"Results for '{inp.query}'"

# Create a model and agent
model = ContexaModel(provider="google", model_name="gemini-pro")
agent = ContexaAgent(
    name="Research Assistant",
    description="Helps with online research",
    model=model,
    tools=[web_search]
)

# Convert to Google ADK
from contexa_sdk.adapters.google import adk_agent, adk_tool, adk_model

# Convert individual components
adk_tool_obj = adk_tool(web_search)
adk_model_obj = adk_model(model)

# Or convert the entire agent
adk_agent_obj = adk_agent(agent)

# Run the agent
result = adk_agent_obj.run("Research quantum computing")
```

## Adapter Differences

| Feature | GenAI Adapter | ADK Adapter |
|---------|---------------|-------------|
| Primary Technology | Google GenAI (Gemini) | Google ADK |
| Installation | `pip install contexa-sdk[google-genai]` | `pip install contexa-sdk[google-adk]` |
| Import Path | `contexa_sdk.adapters.google.genai` | `contexa_sdk.adapters.google.adk` |
| Function Prefix | `genai_*` | `adk_*` |
| Tool Support | Converts to FunctionDeclaration | Converts to ADK Tool |
| Model Support | Direct Gemini model access | Integration with ADK model system |
| Agent Creation | Lightweight wrapper | Full ADK agent instance |
| Streaming Support | Yes | Depends on ADK version |
| Complexity | Lower | Higher |

## Choosing the Right Adapter

### Use the GenAI Adapter When:

- You need direct access to Gemini models
- You want a simpler, lighter-weight solution
- You're not already in the ADK ecosystem
- You need the latest Gemini features

### Use the ADK Adapter When:

- You're already using Google's ADK
- You need advanced ADK-specific capabilities
- You're building for Google Agent Builder
- You need to integrate with other ADK components

## Backward Compatibility

For backward compatibility, the generic functions in `contexa_sdk.adapters.google` (without prefixes) use the GenAI implementations as defaults:

```python
from contexa_sdk.adapters.google import tool, model, agent

# These use the GenAI implementations by default
google_tool = tool(my_tool)
google_model = model(my_model)
google_agent = agent(my_agent)
```

## Testing Without Dependencies

Both adapters include mock implementations that allow tests to run without the actual Google dependencies installed. This makes it easier to develop and test your code without needing API keys or full dependency installations.

## Further Reading

- [Google GenAI SDK Documentation](https://cloud.google.com/python/docs/reference/generativeai/latest)
- [Google ADK Documentation](https://cloud.google.com/agent-builder/docs/overview)
- [Contexa SDK Multi-Framework Integration](../README_MULTI_FRAMEWORK.md) 