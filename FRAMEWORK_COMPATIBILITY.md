# Framework Compatibility Guide

Contexa SDK is designed to be compatible with multiple agentic frameworks, allowing you to define agents, tools, and models once and deploy them to your framework of choice. This document outlines our compatibility with major AI agent frameworks and provides details on requirements and supported features.

## Supported Frameworks

Contexa SDK currently supports the following frameworks:

| Framework | Supported Version | Installation |
|-----------|-------------------|-------------|
| LangChain | 0.1.0+ | `pip install contexa-sdk[langchain]` |
| CrewAI | 0.110.0+ | `pip install contexa-sdk[crewai]` |
| OpenAI Agents SDK | 0.0.14+ | `pip install contexa-sdk[openai]` |
| Google ADK | 0.5.0+ | `pip install contexa-sdk[google]` |

## LangChain Integration

The Contexa SDK provides seamless integration with LangChain's latest modular architecture (v0.1.0+). Our adapter supports:

- Converting Contexa tools to LangChain tools
- Adapting Contexa models to LangChain chat models
- Creating LangChain agents from Contexa agents
- Converting Contexa prompts to LangChain prompt templates
- Supporting inter-agent handoffs via AgentExecutor

### Key Components

```python
from contexa_sdk.adapters import langchain

# Convert Contexa tool to LangChain tool
lc_tool = langchain.tool(contexa_tool)

# Convert Contexa model to LangChain chat model
lc_model = langchain.model(contexa_model)

# Convert Contexa agent to LangChain agent executor
lc_agent = langchain.agent(contexa_agent)
```

### Latest API Changes

LangChain v0.1.0+ introduced a modular architecture with separated components:
- `langchain-core`: Core abstractions like prompts and output parsers
- `langchain`: Main package with LLM integrations and agent runtimes
- `langchain-community`: Community-contributed integrations

Our adapter maintains compatibility with this structure, importing from the appropriate packages.

## CrewAI Integration

The CrewAI adapter supports the latest CrewAI paradigm (v0.110.0+), enabling multi-agent collaboration with our toolkit. Our adapter supports:

- Converting Contexa tools to CrewAI tools
- Adapting Contexa models to CrewAI-compatible model specifications
- Creating CrewAI agents and crews from Contexa agents
- Supporting inter-agent handoffs via CrewAI's delegation mechanism
- Compatibility with CrewAI's task-based workflow

### Key Components

```python
from contexa_sdk.adapters import crewai

# Convert Contexa tool to CrewAI tool
crew_tool = crewai.tool(contexa_tool)

# Convert Contexa model to CrewAI-compatible model
crew_model = crewai.model(contexa_model)

# Convert Contexa agent to CrewAI crew
crew = crewai.agent(contexa_agent)
```

### Latest API Changes

CrewAI v0.110.0+ introduced the `@tool` decorator pattern and improved agent delegation. Our adapter has been updated to use these features.

## OpenAI Agents SDK Integration

Our OpenAI Agents SDK integration supports the latest version of the library (v0.0.14+), which was rebranded from OpenAI Agents Python SDK to simply "agents". Our adapter provides:

- Converting Contexa tools to OpenAI `function_tool` decorated functions
- Adapting Contexa models to OpenAI model identifiers
- Creating OpenAI Agents with appropriate configuration
- Supporting agent handoffs via the Runner interface
- Compatibility with OpenAI's enhanced safety features

### Key Components

```python
from contexa_sdk.adapters import openai

# Convert Contexa tool to OpenAI function tool
openai_tool = openai.tool(contexa_tool)

# Convert Contexa model to OpenAI model identifier
openai_model = openai.model(contexa_model)

# Convert Contexa agent to OpenAI agent
openai_agent = openai.agent(contexa_agent)
```

### Latest API Changes

OpenAI Agents SDK was rebranded and its imports changed from `openai_agents` to `agents`. The primary way to create tools also changed to use the `@function_tool` decorator pattern. Our adapter has been updated to reflect these changes.

## Google ADK Integration

Our Google ADK integration provides compatibility with Google's Agent Development Kit (v0.5.0+), a code-first toolkit for building sophisticated AI agents. Our adapter supports:

- Converting Contexa tools to Google ADK agent tools
- Adapting Contexa models to Google ADK model configurations
- Creating Google ADK agents from Contexa agent definitions
- Supporting multi-agent composition via ADK's agent hierarchies
- Leveraging ADK's built-in evaluation and deployment capabilities

### Key Components

```python
from contexa_sdk.adapters import google

# Convert Contexa tool to Google ADK tool
google_tool = google.tool(contexa_tool)

# Convert Contexa model to Google ADK model configuration
google_model = google.model(contexa_model)

# Convert Contexa agent to Google ADK agent
google_agent = google.agent(contexa_agent)
```

### Latest API Changes

Google ADK continues to evolve rapidly with new features for agent development. Our adapter is designed to work with ADK's latest patterns, including their agent hierarchy model, tool system, and LLM integration.

## Handling Framework Updates

The Contexa SDK team monitors updates to all supported frameworks and maintains compatibility through regular updates to our adapters. When a framework introduces breaking changes, we aim to:

1. Update our adapters within 2 weeks of the release
2. Provide backward compatibility where possible
3. Document migration paths in our release notes

## Compatibility Testing

We maintain a comprehensive test suite in `tests/adapters/test_compatibility.py` that validates our adapters against the latest versions of each framework. These tests help ensure that our integration points remain functional as frameworks evolve.

## Requesting New Framework Support

If you'd like to see support for additional agentic frameworks, please [open an issue](https://github.com/your-repo/contexa-sdk/issues/new) with the framework name, key features, and your use case. We prioritize framework integrations based on community interest and framework maturity.

# Contexa SDK - Framework Compatibility Matrix

This document outlines the version compatibility between Contexa SDK and the various AI frameworks it supports.

## Version Compatibility

| Framework | Minimum Supported Version | Recommended Version | Notes |
|-----------|---------------------------|---------------------|-------|
| LangChain | 0.1.0 | 0.1.5+ | Requires langchain-openai for OpenAI integration |
| CrewAI | 0.110.0 | 0.112.0+ | Earlier versions may have agent registration issues |
| OpenAI SDK | 1.2.0 | 1.5.0+ | Required for function calling |
| OpenAI Agents SDK | 0.0.3 | 0.0.5+ | Still in preview/beta |
| Google GenAI | 0.3.0 | 0.3.1+ | For Gemini model access |
| Google ADK | 0.5.0 | 0.5.0+ | Agent Development Kit (newer product) |

## Feature Support Matrix

| Feature | LangChain | CrewAI | OpenAI | Google GenAI | Google ADK |
|---------|-----------|--------|--------|-------------|------------|
| Tool Conversions | ✅ | ✅ | ✅ | ✅ | ✅ |
| Model Conversions | ✅ | ✅ | ✅ | ✅ | ✅ |
| Agent Conversions | ✅ | ✅ | ✅ | ✅ | ✅ |
| Handoffs (outgoing) | ✅ | ✅ | ✅ | ✅ | ✅ |
| Handoffs (incoming) | ✅ | ✅ | ✅ | ✅ | ✅ |
| Streaming | ✅ | ✅ | ✅ | ✅ | ❌ |
| Multi-agent | ✅ | ✅ | ❌ | ❌ | ✅ |
| MCP Support | ✅ | ✅ | ✅ | ✅ | ✅ |

## Google Adapter Comparison

### Google GenAI vs. Google ADK

| Aspect | Google GenAI | Google ADK |
|--------|-------------|------------|
| Primary Use Case | Simple integration with Gemini models | Advanced agent capabilities and orchestration |
| Complexity | Lower | Higher |
| Required Package | google-generativeai | google-adk |
| Model Support | Gemini models | Multiple models with ADK wrapper |
| Function Calling | Basic | Advanced |
| Multi-agent Support | Limited | Extensive |
| Integration Ease | Easier, fewer components | More complex, more features |
| Development Status | Stable | Newer/evolving |

## Installation Requirements

For each framework, install the corresponding extras:

```bash
# LangChain support
pip install "contexa-sdk[langchain]"

# CrewAI support
pip install "contexa-sdk[crewai]"

# OpenAI support 
pip install "contexa-sdk[openai]"

# Google GenAI support (for Gemini models)
pip install "contexa-sdk[google-genai]"

# Google ADK support (for Agent Development Kit)
pip install "contexa-sdk[google-adk]"

# Support for both Google adapters
pip install "contexa-sdk[google]"

# All frameworks
pip install "contexa-sdk[all]"
```

## Recommendations

- **For new projects**: Start with LangChain for flexibility or OpenAI for simplicity
- **For Google developers**: 
  - Use GenAI adapter for simple Gemini model access
  - Use ADK adapter for complex agent development with Google's framework
- **For multi-agent systems**: CrewAI and Google ADK provide the most robust support
- **For performance**: OpenAI and Google GenAI adapters offer the fastest execution 