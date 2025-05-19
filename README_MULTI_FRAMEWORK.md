# Multi-Framework Integration

Contexa SDK enables seamless integration between different agent frameworks, allowing you to:

1. **Write once, run anywhere**: Define tools, models, and agents once and use them in any supported framework
2. **Framework interoperability**: Share capabilities between frameworks without duplicating code
3. **Agent handoffs**: Transfer control between agents built on different frameworks while maintaining context

## Supported Frameworks

The SDK currently supports the following frameworks:

| Framework | Min Version | Adapter | Installation |
|-----------|-------------|---------|------------|
| LangChain | 0.1.0 | `langchain.py` | `pip install contexa-sdk[langchain]` |
| CrewAI | 0.110.0 | `crewai.py` | `pip install contexa-sdk[crewai]` |
| OpenAI Agents SDK | 0.4.0 | `openai.py` | `pip install contexa-sdk[openai]` |
| Google GenAI | 0.3.0 | `google/genai.py` | `pip install contexa-sdk[google-genai]` |
| Google ADK | 0.5.0 | `google/adk.py` | `pip install contexa-sdk[google-adk]` |

> **Note:** For detailed information about the Google adapters and when to use each one, see [Google Adapters Documentation](docs/google_adapters.md).

## Architecture

The multi-framework integration is built on the adapter pattern:

```
Contexa Core Objects → Adapters → Framework Native Objects
```

Each adapter implements the `BaseAdapter` interface, which provides methods to convert Contexa core objects to framework-specific objects:

```python
class BaseAdapter(ABC):
    def tool(self, t: ContexaTool) -> Any: ...
    def model(self, m: ContexaModel) -> Any: ...
    def agent(self, a: ContexaAgent) -> Any: ...
    def prompt(self, p: ContexaPrompt) -> Any: ...
```

All adapters implement a standardized return format for the `model()` method, providing consistent structure across frameworks:

```python
# Example standardized model conversion
def model(self, model: ContexaModel) -> Any:
    """Convert a Contexa model to a framework-specific model."""
    return {
        "model_name": model.model_name,
        "provider": model.provider,
        "config": model.config,
        # Framework-specific fields as needed
    }
```

This standardization enables seamless interoperability between different framework adapters.

## Using Adapters

### Converting Tools

```python
from contexa_sdk.core.tool import ContexaTool
from pydantic import BaseModel

# Define a Contexa tool
class SearchInput(BaseModel):
    query: str

@ContexaTool.register(
    name="web_search",
    description="Search the web and return text snippet"
)
async def web_search(inp: SearchInput) -> str:
    return f"Top hit for {inp.query}"

# Convert to framework-specific tools
from contexa_sdk.adapters import langchain, crewai, openai, google

# LangChain tool
lc_tool = langchain.tool(web_search)

# CrewAI tool
crew_tool = crewai.tool(web_search)

# OpenAI tool
oa_tool = openai.tool(web_search)

# Google ADK tool
google_tool = google.tool(web_search)
```

### Converting Models

```python
from contexa_sdk.core.model import ContexaModel

# Define a Contexa model
model = ContexaModel(provider="openai", model_id="gpt-4o")

# Convert to framework-specific models
lc_model = langchain.model(model)
crew_model = crewai.model(model)
oa_model = openai.model(model)
adk_model = google.model(model)
```

### Converting Agents

```python
from contexa_sdk.core.agent import ContexaAgent

# Define a Contexa agent
agent = ContexaAgent(
    name="My Assistant",
    description="A helpful assistant",
    model=ContexaModel(provider="openai", model_id="gpt-4o"),
    tools=[web_search]
)

# Convert to framework-specific agents
lc_agent = langchain.agent(agent)
crew_agent = crewai.agent(agent)
oa_agent = openai.agent(agent)
adk_agent = google.agent(agent)
```

## Agent Handoffs

Contexa SDK enables seamless handoffs between agents built on different frameworks. During a handoff, the conversation context is preserved, allowing agents to collaborate effectively.

```python
# First, define agents using different frameworks
from contexa_sdk.adapters import langchain, crewai
from contexa_sdk.core.agent import ContexaAgent

# LangChain-based research agent
research_agent = langchain.agent(ContexaAgent(
    name="Researcher",
    description="Researches topics and finds information",
    model=ContexaModel(provider="openai", model_id="gpt-4o"),
    tools=[web_search]
))

# CrewAI-based writing agent
writing_agent = crewai.agent(ContexaAgent(
    name="Writer",
    description="Writes content based on research",
    model=ContexaModel(provider="anthropic", model_id="claude-3-opus"),
    tools=[]
))

# Perform a handoff from the research agent to the writing agent
from contexa_sdk.runtime.handoff import handoff

# First, run the research agent
research_result = await research_agent.run("Research AI advancements in 2023")

# Then, hand off to the writing agent with the research result
final_result = await handoff(
    from_agent=research_agent,
    to_agent=writing_agent,
    message=f"Write a summary based on this research: {research_result}"
)
```

## Implementation Details

Each adapter maps Contexa objects to framework-specific objects:

| Adapter | Tool Mapping | Agent Mapping | Notes |
|---------|--------------|---------------|-------|
| LangChain | `langchain_core.tools.BaseTool` | `AgentExecutor` | Uses `@tool` decorator or `BaseTool` subclass |
| CrewAI | `crewai.Tool` | `Crew` | CrewAI treats any callable as a tool |
| OpenAI | `openai_agents.Tool` | `openai_agents.Agent` | Generates JSON schema for tools |
| Google ADK | `google.adk.Tool` | `google.adk.Agent` | Follows ADK's agent creation pattern |

For more details on the implementation of each adapter, see the source code in the `contexa_sdk/adapters/`