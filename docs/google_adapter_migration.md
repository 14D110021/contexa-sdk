# Migrating to the New Google Adapters Structure

This guide will help you migrate your code from the old Google adapter structure to the new, improved structure that properly separates Google GenAI and Google ADK implementations.

## Overview of Changes

The Google adapters have been restructured to:

1. Clearly separate Google GenAI (Gemini) and Google ADK implementations
2. Use explicit prefixed functions for better clarity (`genai_*` and `adk_*`)
3. Maintain backward compatibility through non-prefixed exports
4. Improve error handling and provide synchronous wrappers

## Step 1: Update Your Imports

### Old Imports

```python
# Old approach - mixed GenAI and ADK
from contexa_sdk.adapters import google
from contexa_sdk.adapters.google_adk import GoogleADKAdapter
```

### New Imports

```python
# For Google GenAI (Gemini) 
from contexa_sdk.adapters.google import genai_tool, genai_model, genai_agent

# For Google ADK
from contexa_sdk.adapters.google import adk_tool, adk_model, adk_agent

# For backward compatibility (uses GenAI by default)
from contexa_sdk.adapters.google import tool, model, agent
```

## Step 2: Update Your Function Calls

### Old Usage (Mixed GenAI and ADK)

```python
# Old approach - not clear which implementation is used
google_tool = google.tool(my_tool)
google_model = google.model(my_model)
google_agent = google.agent(my_agent)
```

### New Usage (Explicit GenAI or ADK)

```python
# For Google GenAI (Gemini)
genai_tool = genai_tool(my_tool)
genai_model = genai_model(my_model)
genai_agent = genai_agent(my_agent)

# For Google ADK
adk_tool = adk_tool(my_tool)
adk_model = adk_model(my_model)
adk_agent = adk_agent(my_agent)
```

## Step 3: Update Your Dependencies

### Old Dependencies

```bash
pip install contexa-sdk[google]  # Installed both, but usage was unclear
```

### New Dependencies

```bash
# For Google GenAI only
pip install contexa-sdk[google-genai]

# For Google ADK only
pip install contexa-sdk[google-adk]

# For both (same as before)
pip install contexa-sdk[google]
```

## Common Migration Patterns

### Scenario 1: You were using Gemini models with the Google adapter

If you were using the Google adapter primarily for accessing Gemini models:

```python
# Old code
from contexa_sdk.adapters import google

model = ContexaModel(provider="google", model_name="gemini-pro")
google_model = google.model(model)
```

Change to:

```python
# New code - explicit GenAI
from contexa_sdk.adapters.google import genai_model

model = ContexaModel(provider="google", model_name="gemini-pro")
google_model = genai_model(model)
```

### Scenario 2: You were using Google ADK functionality

If you were specifically using Google ADK features:

```python
# Old code
from contexa_sdk.adapters.google_adk import GoogleADKAdapter

adk_adapter = GoogleADKAdapter()
adk_tool = adk_adapter.tool(my_tool)
```

Change to:

```python
# New code - explicit ADK
from contexa_sdk.adapters.google import adk_tool

adk_tool = adk_tool(my_tool)
```

### Scenario 3: You want to maintain maximum backward compatibility

If you want to ensure your code works with minimal changes:

```python
# Old code
from contexa_sdk.adapters import google

google_agent = google.agent(my_agent)
```

This will continue to work, as the non-prefixed functions are preserved for backward compatibility. However, they now use the GenAI implementation by default.

## New Features

The restructured adapters include several improvements:

1. **Synchronous Wrappers**: All adapter functions now have synchronous equivalents (e.g., `adk_agent` is synchronous, and there's an underlying `async_adk_agent` that it calls)

2. **Better Error Handling**: More informative error messages with suggestions for fixing issues

3. **Support for Both Usage Patterns**: Both adapters now handle direct `ContexaTool` instances and decorated functions

4. **Mock Implementations for Testing**: Enhanced mock implementations that don't require dependencies

## Choosing the Right Adapter

- **Google GenAI** (`genai_*`): Use for direct access to Gemini models, simpler integration with basic function calling
- **Google ADK** (`adk_*`): Use for advanced agent features, complex reasoning, and Google's agent development ecosystem

For more details, see the [Google Adapters Documentation](docs/adapters/google_adapters.md) and try the [Google Adapter Comparison Example](examples/google_adapter_comparison.py).

## API Differences Between GenAI and ADK

Understanding the differences between the two implementations will help you choose the right adapter:

### GenAI Adapter (genai_*)

- **Purpose**: Direct integration with Google's Generative AI models (Gemini)
- **Main Package**: Requires `google-generativeai`
- **Key Features**:
  - Simpler API focused on model interaction
  - Direct access to Gemini model capabilities
  - Lighter weight with fewer dependencies
  - Better for straightforward question-answering and function-calling scenarios

### ADK Adapter (adk_*)

- **Purpose**: Integration with Google's Agent Development Kit for advanced agent capabilities
- **Main Package**: Requires `google-adk` 
- **Key Features**:
  - Advanced reasoning capabilities
  - Multi-step planning built-in
  - Task decomposition features
  - Integration with Google's agent ecosystem
  - Better for complex, multi-turn conversations and tasks

## Testing During Migration

Here are some tips for testing your code during the migration process:

1. **Incremental Testing**: Migrate one component at a time and test thoroughly before moving on to the next

2. **Create Test Cases**:
   ```python
   # Test both adapters with the same input
   async def test_adapters():
       # Create test data
       base_agent = ContexaAgent(...)
       
       # Test GenAI adapter
       genai_assistant = genai_agent(base_agent)
       genai_result = await genai_assistant.run("Test query")
       
       # Test ADK adapter
       adk_assistant = adk_agent(base_agent)
       adk_result = await adk_assistant.run("Test query")
       
       # Compare results
       print(f"GenAI: {genai_result}")
       print(f"ADK: {adk_result}")
   ```

3. **Mock Testing**: Use the built-in mock implementations for testing without dependencies
   ```python
   # Setting an environment variable to use mocks
   os.environ["CONTEXA_USE_MOCKS"] = "true"
   
   # Now adapters will use mock implementations
   mock_genai_assistant = genai_agent(base_agent)
   ```

## Troubleshooting Common Issues

### Import Errors

**Problem**: `ImportError: Cannot import name 'genai_tool' from 'contexa_sdk.adapters.google'`

**Solution**: Ensure you've updated to the latest Contexa SDK version with the new adapter structure:
```bash
pip install --upgrade contexa-sdk
```

### Dependency Errors

**Problem**: `ImportError: No module named 'google.generativeai'`

**Solution**: Install the correct dependencies:
```bash
pip install contexa-sdk[google-genai]  # For GenAI
pip install contexa-sdk[google-adk]    # For ADK
```

### Adapter Mismatch

**Problem**: Your code works with one adapter but not the other

**Solution**: Review the key differences and ensure you're using the appropriate adapter for your use case. Consider using the example in `examples/google_adapter_comparison.py` as a reference.

### Backward Compatibility Issues

**Problem**: Code that worked with the old structure now behaves differently

**Solution**: The non-prefixed functions (e.g., `google.tool()`) now use the GenAI implementation by default. If you were implicitly relying on ADK features, explicitly switch to the ADK adapter:
```python
# Old code (implicitly used GenAI in new structure)
from contexa_sdk.adapters import google
google_agent = google.agent(my_agent)

# New code (explicitly use ADK)
from contexa_sdk.adapters.google import adk_agent
adk_agent = adk_agent(my_agent)
```

## FAQ

### Q: Which adapter should I use by default?

A: If you're primarily using Gemini models for simple tasks, use the GenAI adapter (`genai_*`). If you need advanced agent capabilities like multi-step reasoning or complex task handling, use the ADK adapter (`adk_*`).

### Q: Will my existing code break?

A: The restructuring maintains backward compatibility, so non-prefixed imports like `from contexa_sdk.adapters import google` will continue to work. However, they now use the GenAI implementation by default.

### Q: Can I use both adapters in the same project?

A: Yes, you can use both adapters side by side for different parts of your application:
```python
from contexa_sdk.adapters.google import genai_agent, adk_agent

# Use GenAI for simple tasks
simple_assistant = genai_agent(simple_agent)

# Use ADK for complex tasks
complex_assistant = adk_agent(complex_agent)
```

### Q: Do I need to install both dependencies?

A: You only need to install the dependencies for the adapters you're using. If you're using both, you can install both with:
```bash
pip install contexa-sdk[google]
```

## Complete Migration Example

Here's a complete example showing migration from the old structure to the new:

### Old Code

```python
from contexa_sdk.core.agent import ContexaAgent
from contexa_sdk.core.model import ContexaModel
from contexa_sdk.core.tool import ContexaTool
from contexa_sdk.adapters import google

# Define a tool
@ContexaTool.register(
    name="fetch_data",
    description="Fetches data from a source"
)
async def fetch_data(source: str) -> str:
    return f"Data from {source}"

# Create an agent
agent = ContexaAgent(
    name="DataAgent",
    model=ContexaModel(provider="google", model_name="gemini-pro"),
    tools=[fetch_data]
)

# Convert to Google agent (unclear which implementation)
google_agent = google.agent(agent)

# Run the agent
async def run():
    response = await google_agent.run("Get data from database")
    print(response)
```

### New Code (Using GenAI)

```python
from contexa_sdk.core.agent import ContexaAgent
from contexa_sdk.core.model import ContexaModel
from contexa_sdk.core.tool import ContexaTool
from contexa_sdk.adapters.google import genai_agent  # Explicit import

# Define a tool
@ContexaTool.register(
    name="fetch_data",
    description="Fetches data from a source"
)
async def fetch_data(source: str) -> str:
    return f"Data from {source}"

# Create an agent
agent = ContexaAgent(
    name="DataAgent",
    model=ContexaModel(provider="google", model_name="gemini-pro"),
    tools=[fetch_data]
)

# Convert to Google GenAI agent (explicit)
genai_assistant = genai_agent(agent)

# Run the agent
async def run():
    response = await genai_assistant.run("Get data from database")
    print(response)
```

### New Code (Using ADK)

```python
from contexa_sdk.core.agent import ContexaAgent
from contexa_sdk.core.model import ContexaModel
from contexa_sdk.core.tool import ContexaTool
from contexa_sdk.adapters.google import adk_agent  # Explicit import

# Define a tool
@ContexaTool.register(
    name="fetch_data",
    description="Fetches data from a source"
)
async def fetch_data(source: str) -> str:
    return f"Data from {source}"

# Create an agent
agent = ContexaAgent(
    name="DataAgent",
    model=ContexaModel(provider="google", model_name="gemini-pro"),
    tools=[fetch_data]
)

# Convert to Google ADK agent (explicit)
adk_assistant = adk_agent(agent)

# Run the agent
async def run():
    response = await adk_assistant.run("Get data from database")
    print(response)
```

## Need Help?

If you encounter issues during migration, please:

1. Check the [documentation](docs/adapters/google_adapters.md)
2. Review the [example code](examples/google_adapter_comparison.py)
3. Open an issue on GitHub if problems persist 