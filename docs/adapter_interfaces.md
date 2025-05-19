# Adapter Interfaces

This document describes the standardized interfaces for framework adapters in Contexa SDK.

## Overview

Contexa SDK uses the adapter pattern to convert between Contexa core objects and framework-specific objects. Each adapter implements a consistent interface, allowing Contexa objects to be used across multiple agent frameworks.

## Base Adapter Interface

All adapters implement the `BaseAdapter` interface defined in `contexa_sdk/adapters/base.py`:

```python
class BaseAdapter(ABC):
    @abstractmethod
    def tool(self, tool: ContexaTool) -> Any:
        """Convert a Contexa tool to a framework-specific tool."""
        pass
        
    @abstractmethod
    def model(self, model: ContexaModel) -> Any:
        """Convert a Contexa model to a framework-specific model."""
        pass
        
    @abstractmethod
    def agent(self, agent: ContexaAgent) -> Any:
        """Convert a Contexa agent to a framework-specific agent."""
        pass
        
    @abstractmethod
    def prompt(self, prompt: ContexaPrompt) -> Any:
        """Convert a Contexa prompt to a framework-specific prompt."""
        pass
```

## Standardized Model Conversion

The `model()` method has been standardized to return a consistent structure across all adapters:

```python
def model(self, model: ContexaModel) -> Any:
    """Convert a Contexa model to a framework-specific model.
    
    Args:
        model: The Contexa model to convert
        
    Returns:
        A dictionary containing the model configuration with keys:
        - model_name: The model name
        - provider: The model provider (e.g., "openai", "anthropic")
        - config: Additional configuration parameters
        - client: (Optional) Framework-specific client object
    """
    # Implementation details...
```

This standard dictionary return format allows for consistent handling of model configuration across all adapters.

## Adapter-Specific Handoff Functions

Each adapter also provides a `handoff()` function at the module level:

```python
async def handoff(
    source_agent: ContexaAgent,
    target_agent_executor: Any,  # Framework-specific agent
    query: str,
    context: Optional[Dict[str, Any]] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> str:
    """Handle handoff from a Contexa agent to a framework-specific agent.
    
    Args:
        source_agent: The Contexa agent handing off the task
        target_agent_executor: The framework-specific agent receiving the task
        query: The query to send to the target agent
        context: Additional context to pass to the target agent
        metadata: Additional metadata for the handoff
        
    Returns:
        The response from the target agent
    """
    # Implementation details...
```

## Implemented Adapters

### OpenAI Adapter

The OpenAI adapter converts Contexa objects to OpenAI Agents SDK objects:

- **Tool**: Converts to `openai_agents.Tool`
- **Model**: Returns a standardized dictionary
- **Agent**: Converts to `openai_agents.Agent`
- **Handoff**: Supports handoffs to OpenAI Agents

Usage:
```python
from contexa_sdk.adapters import openai

# Convert a Contexa model
openai_model = openai.model(contexa_model)

# Convert a Contexa agent
openai_agent = openai.agent(contexa_agent)

# Handoff to an OpenAI agent
response = await openai.handoff(
    source_agent=contexa_agent,
    target_agent=openai_agent,
    query="Your query here"
)
```

### LangChain Adapter

The LangChain adapter converts Contexa objects to LangChain objects:

- **Tool**: Converts to `langchain_core.tools.Tool`
- **Model**: Returns a standardized dictionary with a `langchain_model` key
- **Agent**: Converts to `langchain.agents.AgentExecutor`
- **Handoff**: Supports handoffs to LangChain agents

Usage:
```python
from contexa_sdk.adapters import langchain

# Convert a Contexa model
lc_model = langchain.model(contexa_model)

# Convert a Contexa agent
lc_agent = langchain.agent(contexa_agent)

# Handoff to a LangChain agent
response = await langchain.handoff(
    source_agent=contexa_agent,
    target_agent_executor=lc_agent,
    query="Your query here"
)
```

### CrewAI Adapter

The CrewAI adapter converts Contexa objects to CrewAI objects:

- **Tool**: Converts to `crewai.Tool`
- **Model**: Returns a standardized dictionary with a `crewai_model` key
- **Agent**: Converts to `crewai.Agent` or `crewai.Crew` (configurable)
- **Handoff**: Supports handoffs to CrewAI agents/crews

Usage:
```python
from contexa_sdk.adapters import crewai

# Convert a Contexa model
crew_model = crewai.model(contexa_model)

# Convert a Contexa agent (with optional crew wrapping)
crew_agent = crewai.agent(contexa_agent, wrap_in_crew=True)

# Handoff to a CrewAI agent/crew
response = await crewai.handoff(
    source_agent=contexa_agent,
    target=crew_agent,
    query="Your query here"
)
```

### Google ADK Adapter

The Google ADK adapter converts Contexa objects to Google ADK objects:

- **Tool**: Converts to `google.adk.Tool`
- **Model**: Returns a standardized dictionary
- **Agent**: Converts to `google.adk.Agent`
- **Handoff**: Supports handoffs to Google ADK agents

Usage:
```python
from contexa_sdk.adapters import google

# Convert a Contexa model
google_model = google.model(contexa_model)

# Convert a Contexa agent
google_agent = google.agent(contexa_agent)

# Handoff to a Google ADK agent
response = await google.handoff(
    source_agent=contexa_agent,
    target_agent=google_agent,
    query="Your query here"
)
```

## Framework Version Compatibility

Each adapter specifies the minimum supported version of its corresponding framework:

- **LangChain**: ≥0.1.0
- **CrewAI**: ≥0.110.0
- **OpenAI Agents SDK**: ≥0.0.3 (part of openai-agents package)
- **Google ADK**: ≥0.5.0

## Error Handling

Adapters provide consistent error handling, including:

- Graceful handling of missing dependencies (with helpful installation instructions)
- Proper error messages for unsupported operations
- Validation of framework versions

## Extending with New Adapters

To create a new adapter for another framework:

1. Create a new module in `contexa_sdk/adapters/`
2. Implement the `BaseAdapter` interface
3. Return standardized structures from the `model()` method
4. Provide module-level functions for easy access
5. Implement proper error handling and validation 