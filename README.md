# Contexa SDK

The Contexa SDK is a comprehensive framework for building, deploying, and managing AI agents. It provides a unified interface for working with different AI frameworks and enables seamless agent handoffs, multi-framework integration, observability, and robust runtime management.

## Key Features

### Core Agent System

- **Unified Agent Interface**: Abstract away underlying AI frameworks with a standardized agent interface
- **Tool Management**: Create, customize, and share tools between agents
- **Memory Systems**: Implement memory for context preservation and reasoning
- **Model Integration**: Connect to various AI models with a consistent API

### Multi-Framework Support

- **Framework Adapters**: Integrate with LangChain, CrewAI, OpenAI, and Google ADK
- **Cross-Framework Handoffs**: Seamlessly transfer control between agents built on different frameworks
- **Context Preservation**: Maintain conversation history and state during handoffs

### Agent Runtime

- **Lifecycle Management**: Control agent startup, execution, and shutdown
- **State Persistence**: Save and restore agent state for resilience
- **Resource Tracking**: Monitor and limit resource usage
- **Health Monitoring**: Detect and recover from failures

### Observability

- **Structured Logging**: Track agent operations with detailed logs
- **Metrics Collection**: Monitor performance and usage metrics
- **Tracing**: Follow request flows through multiple agents
- **OpenTelemetry Compatible**: Integrate with existing observability stacks

### MCP Integration

- **MCP Protocol Support**: Build and consume Model Context Protocol compatible services
- **Agent-as-MCP-Server**: Expose agents as MCP-compatible endpoints
- **Remote Agent Integration**: Invoke remote agents via the MCP protocol

## Installation

```bash
pip install contexa-sdk
```

## Quick Start

```python
import asyncio
from contexa_sdk.core.agent import ContexaAgent
from contexa_sdk.core.model import Model
from contexa_sdk.core.tool import Tool

# Define a simple model
class MyModel(Model):
    async def generate(self, prompt, **kwargs):
        return {"text": f"Response to: {prompt}"}

# Define a simple tool
class GreetingTool(Tool):
    name = "greeting"
    description = "Greet the user"
    
    async def execute(self, name="User", **kwargs):
        return {"message": f"Hello, {name}!"}

# Create an agent
agent = ContexaAgent(
    name="My Assistant",
    description="A helpful assistant",
    model=MyModel(),
    tools=[GreetingTool()]
)

# Run the agent
async def main():
    response = await agent.run("Can you greet me?")
    print(response)

asyncio.run(main())
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

- Basic agent usage
- Multi-framework handoffs
- Runtime management
- Observability setup
- MCP integration

## Contributing

Contributions are welcome! Please see our [Contributing Guide](CONTRIBUTING.md) for more information.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details. 