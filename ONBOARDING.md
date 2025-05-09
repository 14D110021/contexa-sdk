# Contexa SDK Onboarding Guide

This document is designed to help new developers understand the Contexa SDK codebase, particularly for those who might be a bit rusty with Python syntax and modern libraries.

## Table of Contents

- [Getting Started](#getting-started)
- [Understanding the Repository Structure](#understanding-the-repository-structure)
- [Recommended Reading Order](#recommended-reading-order)
- [Key Python Concepts Used](#key-python-concepts-used)
- [Setting Up a Development Environment](#setting-up-a-development-environment)
- [Running Your First Example](#running-your-first-example)
- [Contributing](#contributing)

## Getting Started

Before diving into the code, it's important to understand what Contexa SDK is trying to achieve: standardizing AI agent development across multiple frameworks. The SDK provides an abstraction layer that allows developers to define tools, models, and agents once and use them in different AI agent frameworks like LangChain, CrewAI, and OpenAI.

## Understanding the Repository Structure

The Contexa SDK repository is organized into these main directories:

- `contexa_sdk/`: Core SDK code
  - `core/`: Fundamental abstractions like Tool, Model, Agent
  - `adapters/`: Framework-specific adapters
  - `runtime/`: Agent execution and management
  - `observability/`: Monitoring and logging
  - `deployment/`: Packaging and deployment
  - `cli/`: Command-line interface

- `examples/`: Example applications
  - Basic examples showing simple concepts
  - Advanced examples demonstrating complex patterns

- Documentation files:
  - `README.md`: Overview and quickstart
  - `README_*.md`: Feature-specific documentation

## Recommended Reading Order

For developers new to the codebase, we recommend following this reading order:

### 1. Start with High-Level Documentation

1. **README.md** - For an overview of Contexa SDK's features and basic usage
2. **DOCUMENTATION_CHECKLIST.md** - To understand the documentation status
3. **README_MULTI_FRAMEWORK.md** - To understand how framework interoperability works
4. **README_MCP.md** - To learn about the Model Context Protocol integration

### 2. Explore Basic Examples

5. **examples/search_agent.py** - The simplest example
6. **examples/agent_handoff.py** - How agents communicate
7. **examples/multi_framework_integration.py** - Framework interoperability

### 3. Study Core Components

8. **contexa_sdk/core/tool.py** - Tools and their registration
9. **contexa_sdk/core/model.py** - Model abstraction
10. **contexa_sdk/core/agent.py** - Agent construction
11. **contexa_sdk/core/prompt.py** - Prompt management

### 4. Explore Advanced Examples

12. **examples/financial_analysis_agent.py** - LangChain integration
13. **examples/content_creation_crew.py** - CrewAI integration
14. **examples/customer_support_agent.py** - OpenAI function calling

### 5. Understand Framework Adapters

15. **contexa_sdk/adapters/base.py** - Base adapter functionality
16. **contexa_sdk/adapters/langchain.py** - LangChain conversion
17. **contexa_sdk/adapters/openai.py** - OpenAI conversion

### 6. Dive Into Runtime and Infrastructure

18. **contexa_sdk/runtime/** - Agent execution
19. **contexa_sdk/observability/** - Monitoring
20. **contexa_sdk/deployment/** - Deployment
21. **contexa_sdk/cli/** - CLI functionality

## Key Python Concepts Used

The Contexa SDK uses several modern Python features that you should be familiar with:

### Decorators

Decorators are used extensively for registering tools and other components:

```python
@ContexaTool.register(
    name="web_search",
    description="Search the web"
)
async def web_search(input_data: SearchInput) -> ToolOutput:
    # Function implementation here
```

### Async/Await Patterns

Most code uses asynchronous programming with `async def` and `await`:

```python
async def create_agent():
    # Async code here
    result = await model.generate(prompt)
```

### Type Hints

Type annotations are used throughout the codebase:

```python
def process_data(data: Dict[str, Any]) -> List[Result]:
    # Function implementation here
```

### Pydantic Models

Pydantic is used for data validation and settings management:

```python
class SearchInput(BaseModel):
    query: str = Field(description="Search query")
    max_results: int = Field(10, description="Maximum number of results")
```

### Context Managers

Context managers with `async with` are used for resource management:

```python
async with ClientSession() as session:
    # Use session here
```

## Setting Up a Development Environment

To work with the Contexa SDK, we recommend the following setup:

1. Create a Python virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install the SDK with all dependencies:
   ```bash
   pip install -e ".[all]"
   ```

3. Install development tools:
   ```bash
   pip install -e ".[dev]"
   ```

## Running Your First Example

Try running a simple example to verify your setup:

```bash
cd examples
python search_agent.py
```

If everything is set up correctly, you should see output from the search agent.

## Contributing

Once you're comfortable with the codebase, consider contributing to the project:

1. Find an issue to work on in the GitHub issue tracker
2. Create a new branch for your changes
3. Make changes and add tests if applicable
4. Ensure all tests pass: `pytest`
5. Submit a pull request

See [CONTRIBUTING.md](CONTRIBUTING.md) for more detailed guidelines.

## Additional Resources

If you need to refresh your Python knowledge:

- [Real Python Tutorials](https://realpython.com/)
- [Async IO in Python](https://realpython.com/async-io-python/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [Type Hints Cheat Sheet](https://mypy.readthedocs.io/en/stable/cheat_sheet_py3.html) 