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